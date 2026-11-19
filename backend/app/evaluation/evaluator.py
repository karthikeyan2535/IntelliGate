"""
Model Evaluation Engine for IntelliGate.
Executes benchmark datasets across models, validates outputs deterministically,
computes quality scores, measures latency, and generates task-specific profiles
that directly calibrate the Intelligent Routing Engine.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any, Optional
import structlog

from app.evaluation.dataset import BENCHMARK_DATASET, BenchmarkItem
from app.evaluation.profiles import ProfileManager
from app.providers.base import BaseProvider, ProviderMessage, ProviderRequest
from app.providers.registry import provider_registry

logger = structlog.get_logger(__name__)


@dataclass
class EvaluationRunResult:
    model_id: str
    provider: str
    total_prompts: int
    passed_prompts: int
    overall_quality_score: float
    category_scores: dict[str, float]
    avg_latency_ms: float
    total_tokens_used: int
    duration_seconds: float
    item_details: list[dict[str, Any]]


class BenchmarkEvaluator:
    """Executes automated benchmark evaluation suites against LLM models."""

    @classmethod
    async def evaluate_model(
        cls,
        model_id: str,
        provider_name: Optional[str] = None,
        max_items: Optional[int] = None,
    ) -> EvaluationRunResult:
        """
        Runs the benchmark dataset through the specified model and computes empirical scores.
        """
        profile = ProfileManager.get(model_id)
        prov_name = provider_name or (profile.provider if profile else "openai")

        # Resolve provider adapter
        provider: Optional[BaseProvider] = provider_registry.get_or_none(prov_name)
        if not provider:
            # Fallback to mock provider in test environment
            from tests.mocks import MockLLMProvider
            provider = MockLLMProvider()

        # If subset requested, sample evenly across all categories (coding, reasoning, writing, general_qa)
        if max_items and max_items < len(BENCHMARK_DATASET):
            by_cat: dict[str, list] = {"coding": [], "reasoning": [], "writing": [], "general_qa": []}
            for item in BENCHMARK_DATASET:
                by_cat.setdefault(item.category, []).append(item)
            
            per_cat = max(1, max_items // len(by_cat))
            balanced: list = []
            for cat_items in by_cat.values():
                balanced.extend(cat_items[:per_cat])
            if len(balanced) < max_items:
                remaining = [it for it in BENCHMARK_DATASET if it not in balanced]
                balanced.extend(remaining[:max_items - len(balanced)])
            dataset = balanced[:max_items]
        else:
            dataset = BENCHMARK_DATASET

        total_items = len(dataset)
        passed_count = 0
        total_latency_ms = 0.0
        total_tokens = 0

        category_stats: dict[str, dict[str, int]] = {
            "coding": {"passed": 0, "total": 0},
            "reasoning": {"passed": 0, "total": 0},
            "writing": {"passed": 0, "total": 0},
            "general_qa": {"passed": 0, "total": 0},
        }

        item_results: list[dict[str, Any]] = []
        run_start = time.perf_counter()

        for item in dataset:
            cat = item.category
            category_stats[cat]["total"] += 1

            p_req = ProviderRequest(
                model=model_id,
                messages=[ProviderMessage(role="user", content=item.prompt)],
                temperature=0.0,  # deterministic temperature for benchmarking
                max_tokens=300,
            )

            t0 = time.perf_counter()
            error_msg: Optional[str] = None
            passed = False
            response_content = ""

            try:
                resp = await provider.chat_completion(p_req)
                elapsed_ms = (time.perf_counter() - t0) * 1000
                total_latency_ms += elapsed_ms
                response_content = resp.content or ""
                if resp.usage:
                    total_tokens += resp.usage.total_tokens

                # Validate response against benchmark item rules
                passed = cls._validate_response(item, response_content)
            except Exception as exc:
                elapsed_ms = (time.perf_counter() - t0) * 1000
                error_msg = str(exc)

            if passed:
                passed_count += 1
                category_stats[cat]["passed"] += 1

            item_results.append({
                "item_id": item.id,
                "category": item.category,
                "complexity": item.complexity,
                "passed": passed,
                "latency_ms": round(elapsed_ms, 1),
                "error": error_msg,
                "response_sample": response_content[:100] + ("..." if len(response_content) > 100 else ""),
            })

        duration_sec = time.perf_counter() - run_start

        # Detect if all requests failed strictly due to upstream credit, billing or auth errors
        billing_errors = [
            it["error"] for it in item_results
            if it.get("error") and any(w in it["error"].lower() for w in ["credit", "quota", "billing", "unauthorized", "api_key", "exceeded"])
        ]
        if len(billing_errors) == total_items:
            # Do NOT overwrite existing capability profile with zeros when API key has no credits
            raise ValueError(
                f"Evaluation failed: Provider '{prov_name}' rejected all requests ({billing_errors[0]}). Existing model capability profile preserved."
            )

        overall_score = round(passed_count / total_items, 3) if total_items > 0 else 0.0
        avg_lat = round(total_latency_ms / total_items, 1) if total_items > 0 else 0.0

        cat_scores: dict[str, Optional[float]] = {}
        for cat, stats in category_stats.items():
            tot = stats["total"]
            pas = stats["passed"]
            # Only update score if category was actually tested in this run
            cat_scores[cat] = round(pas / tot, 3) if tot > 0 else None

        # Feed the measured scores directly back into the ProfileManager!
        ProfileManager.update_profile(
            model_id=model_id,
            coding_score=cat_scores.get("coding"),
            reasoning_score=cat_scores.get("reasoning"),
            writing_score=cat_scores.get("writing"),
            qa_score=cat_scores.get("general_qa"),
            latency_ms=avg_lat if avg_lat > 0 else None,
        )

        logger.info(
            "Completed benchmark evaluation",
            model=model_id,
            overall_score=overall_score,
            passed=f"{passed_count}/{total_items}",
            avg_latency_ms=avg_lat,
        )

        return EvaluationRunResult(
            model_id=model_id,
            provider=prov_name,
            total_prompts=total_items,
            passed_prompts=passed_count,
            overall_quality_score=overall_score,
            category_scores=cat_scores,
            avg_latency_ms=avg_lat,
            total_tokens_used=total_tokens,
            duration_seconds=round(duration_sec, 2),
            item_details=item_results,
        )

    @staticmethod
    def _validate_response(item: BenchmarkItem, response: str) -> bool:
        if not response or not response.strip():
            return False

        lower = response.lower()

        if item.validator_type == "regex" and item.regex_pattern:
            return bool(re.search(item.regex_pattern, response, re.IGNORECASE))

        # Substring verification: check that required key elements or answers appear
        matches = [kw.lower() in lower for kw in item.expected_contains]
        # At least one key indicator or majority matches
        return any(matches)

