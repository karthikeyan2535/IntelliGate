"""
Structured JSON logging with structlog.
Provides request-ID injection and PII-safe processors.
"""
from __future__ import annotations

import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any

import structlog
from structlog.types import EventDict, Processor

# Context variable for request-scoped request ID
_request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    return _request_id_ctx.get() or str(uuid.uuid4())


def set_request_id(request_id: str) -> None:
    _request_id_ctx.set(request_id)


# ── PII-safe processors ───────────────────────────────────────────────────────

_REDACT_KEYS = frozenset(
    {
        "password",
        "api_key",
        "secret",
        "token",
        "credential",
        "authorization",
        "access_token",
        "refresh_token",
        "private_key",
        "secret_key",
        "fernet_key",
    }
)


def _redact_pii(logger: Any, method: str, event_dict: EventDict) -> EventDict:
    """Replace sensitive values with [REDACTED]."""
    for key in list(event_dict.keys()):
        if any(sensitive in key.lower() for sensitive in _redact_pii_keywords()):
            event_dict[key] = "[REDACTED]"
    return event_dict


def _redact_pii_keywords() -> frozenset[str]:
    return _REDACT_KEYS


def _add_request_id(logger: Any, method: str, event_dict: EventDict) -> EventDict:
    rid = _request_id_ctx.get()
    if rid:
        event_dict["request_id"] = rid
    return event_dict


# ── Shared processors ─────────────────────────────────────────────────────────

_SHARED_PROCESSORS: list[Processor] = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    structlog.processors.TimeStamper(fmt="iso"),
    _add_request_id,
    _redact_pii,
    structlog.processors.StackInfoRenderer(),
]


def configure_logging(log_level: str = "INFO", json_logs: bool = True) -> None:
    """Configure structlog + stdlib logging. Call once at startup."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    if json_logs:
        renderer: Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *_SHARED_PROCESSORS,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=_SHARED_PROCESSORS,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    # Quiet noisy libraries
    for noisy in ("uvicorn.access", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str = __name__) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
