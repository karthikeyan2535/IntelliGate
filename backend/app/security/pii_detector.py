"""
PII Detection, Redaction, and Policy Enforcement subsystem for IntelliGate.
Supports Microsoft Presidio when available, supplemented with high-precision pattern recognizers
for API keys, cloud tokens, SSNs, Credit Cards, IPv4/IPv6, and Email addresses.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional
import structlog

from app.core.metrics import PII_DETECTIONS_TOTAL

logger = structlog.get_logger(__name__)


class PIIPolicyAction(str, Enum):
    DISABLED = "disabled"
    DETECT_ONLY = "detect_only"
    REDACT = "redact"
    BLOCK = "block"


@dataclass
class PIIEntityMatch:
    entity_type: str
    start: int
    end: int
    text: str
    score: float


@dataclass
class PIIScanResult:
    has_pii: bool
    entities: list[PIIEntityMatch]
    redacted_text: str
    blocked: bool = False
    details: str = ""


# High-precision regular expressions for common and security-sensitive PII
REGEX_PATTERNS = {
    "API_KEY": re.compile(r"\b(?:sk-[a-zA-Z0-9_-]{20,64}|ig-[a-zA-Z0-9_-]{24,64}|ghp_[a-zA-Z0-9]{36}|AIza[0-9A-Za-z-_]{35})\b"),
    "EMAIL_ADDRESS": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"),
    "PHONE_NUMBER": re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "IP_ADDRESS": re.compile(r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"),
    "CREDIT_CARD": re.compile(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b"),
    "US_SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
}


class PIIDetector:
    """Enterprise-grade PII detector and redactor."""

    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold
        self._presidio_analyzer = None
        self._presidio_anonymizer = None
        self._init_presidio()

    def _init_presidio(self):
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine
            self._presidio_analyzer = AnalyzerEngine()
            self._presidio_anonymizer = AnonymizerEngine()
            logger.info("Presidio Analyzer & Anonymizer initialized successfully")
        except Exception as exc:
            logger.debug("Presidio not fully available, falling back to regex recognizers", reason=str(exc))

    def detect_entities(self, text: str) -> list[PIIEntityMatch]:
        if not text:
            return []

        matches: list[PIIEntityMatch] = []
        occupied_spans: list[tuple[int, int]] = []

        # 1. First run regex recognizers (for high-confidence credentials and PII)
        for entity_type, pattern in REGEX_PATTERNS.items():
            for m in pattern.finditer(text):
                start, end = m.span()
                matched_text = m.group(0)
                matches.append(PIIEntityMatch(
                    entity_type=entity_type,
                    start=start,
                    end=end,
                    text=matched_text,
                    score=0.98,
                ))
                occupied_spans.append((start, end))

        # 2. Run Presidio analyzer if installed
        if self._presidio_analyzer is not None:
            try:
                results = self._presidio_analyzer.analyze(
                    text=text,
                    language="en",
                    score_threshold=self.threshold,
                )
                for res in results:
                    # Avoid overlapping matches with higher-confidence regex
                    overlaps = any(s <= res.start < e or s < res.end <= e for s, e in occupied_spans)
                    if not overlaps:
                        matches.append(PIIEntityMatch(
                            entity_type=res.entity_type,
                            start=res.start,
                            end=res.end,
                            text=text[res.start:res.end],
                            score=res.score,
                        ))
            except Exception as exc:
                logger.debug("Presidio analysis pass encountered exception", error=str(exc))

        # Sort matches by start position in ascending order
        matches.sort(key=lambda x: x.start)
        return matches

    def redact_text(self, text: str, matches: list[PIIEntityMatch]) -> str:
        """Replace detected PII spans with [REDACTED_<ENTITY_TYPE>] placeholders."""
        if not matches or not text:
            return text

        # Replace backwards from end of string so indices remain valid
        result = list(text)
        sorted_matches = sorted(matches, key=lambda m: m.start, reverse=True)
        for m in sorted_matches:
            placeholder = f"[REDACTED_{m.entity_type}]"
            result[m.start:m.end] = list(placeholder)

        return "".join(result)

    def scan_and_enforce(
        self,
        text: str,
        action: PIIPolicyAction = PIIPolicyAction.REDACT,
    ) -> PIIScanResult:
        """
        Executes PII detection and enforces the configured policy action:
        - DISABLED: pass-through unchanged
        - DETECT_ONLY: scan and log, return original text
        - REDACT: replace PII with placeholders
        - BLOCK: reject request if any PII is detected
        """
        if action == PIIPolicyAction.DISABLED or not text:
            return PIIScanResult(has_pii=False, entities=[], redacted_text=text)

        matches = self.detect_entities(text)
        has_pii = len(matches) > 0

        if has_pii:
            for m in matches:
                PII_DETECTIONS_TOTAL.labels(entity_type=m.entity_type).inc()

            logger.info("PII detected in payload", count=len(matches), types=[m.entity_type for m in matches])

        if action == PIIPolicyAction.BLOCK and has_pii:
            return PIIScanResult(
                has_pii=True,
                entities=matches,
                redacted_text=text,
                blocked=True,
                details=f"Request blocked due to detected PII entities: {', '.join({m.entity_type for m in matches})}",
            )

        if action == PIIPolicyAction.REDACT and has_pii:
            redacted = self.redact_text(text, matches)
            return PIIScanResult(
                has_pii=True,
                entities=matches,
                redacted_text=redacted,
                blocked=False,
            )

        # DETECT_ONLY
        return PIIScanResult(
            has_pii=has_pii,
            entities=matches,
            redacted_text=text,
            blocked=False,
        )


_default_detector: Optional[PIIDetector] = None


def get_pii_detector() -> PIIDetector:
    global _default_detector
    if _default_detector is None:
        _default_detector = PIIDetector()
    return _default_detector

