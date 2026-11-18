"""
Provider registry for IntelliGate.

Maintains a singleton map of provider_id → BaseProvider instances.
Automatically discovers credentials from environment variables.
"""
from __future__ import annotations

import os
import threading
from typing import Optional

import structlog

from app.providers.base import BaseProvider, ProviderError

logger = structlog.get_logger(__name__)


class ProviderRegistry:
    """Thread-safe registry that maps provider_id → BaseProvider instance."""

    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}
        self._lock = threading.Lock()
        self._initialized = False

    def register(self, provider_id: str, provider: BaseProvider) -> None:
        with self._lock:
            self._providers[provider_id.lower()] = provider
        logger.info(
            "provider_registry.registered",
            provider_id=provider_id,
            provider_type=provider.provider_type,
        )

    def unregister(self, provider_id: str) -> None:
        with self._lock:
            self._providers.pop(provider_id.lower(), None)

    def invalidate(self, provider_id: str) -> None:
        self.unregister(provider_id)

    def get(self, provider_id: str) -> BaseProvider:
        prov = self.get_or_none(provider_id)
        if prov is None:
            raise ProviderError(
                f"Provider '{provider_id}' not found in registry",
                status_code=503,
                error_code="provider_not_found",
                retryable=False,
            )
        return prov

    def get_or_none(self, provider_id: str) -> BaseProvider | None:
        self.ensure_initialized()
        with self._lock:
            return self._providers.get(provider_id.lower())

    def all_providers(self) -> dict[str, BaseProvider]:
        self.ensure_initialized()
        with self._lock:
            return dict(self._providers)

    def ensure_initialized(self) -> None:
        if self._initialized:
            return
        with self._lock:
            if self._initialized:
                return
            self._initialize_from_env()
            self._initialized = True

    def _initialize_from_env(self) -> None:
        """Autodiscover providers from standard environment variables."""
        try:
            from pathlib import Path
            from dotenv import load_dotenv
            load_dotenv()
            # Also check workspace root and backend folder
            for p in [Path(__file__).resolve().parents[2] / ".env", Path(__file__).resolve().parents[3] / ".env"]:
                if p.exists():
                    load_dotenv(p)
        except Exception:
            pass

        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and len(openai_key.strip()) > 5:
            from app.providers.openai_provider import OpenAIProvider
            self._providers["openai"] = OpenAIProvider(api_key=openai_key.strip())
            logger.info("Initialized OpenAI provider from environment")

        # Gemini
        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if gemini_key and len(gemini_key.strip()) > 5:
            from app.providers.gemini_provider import GeminiProvider
            self._providers["gemini"] = GeminiProvider(api_key=gemini_key.strip())
            logger.info("Initialized Gemini provider from environment")

        # Groq
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key and len(groq_key.strip()) > 5:
            from app.providers.groq_provider import GroqProvider
            self._providers["groq"] = GroqProvider(api_key=groq_key.strip())
            logger.info("Initialized Groq provider from environment")


provider_registry = ProviderRegistry()
