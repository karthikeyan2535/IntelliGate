"""
Provider registry for IntelliGate.

Maintains a singleton map of provider_id → BaseProvider instances.
Providers are registered at startup and can be invalidated when credentials change.
"""
from __future__ import annotations

import threading
from typing import TYPE_CHECKING

import structlog

from app.providers.base import BaseProvider, ProviderError

if TYPE_CHECKING:
    pass

logger = structlog.get_logger(__name__)


class ProviderRegistry:
    """
    Thread-safe registry that maps provider_id → BaseProvider instance.

    Provider IDs are arbitrary strings (e.g. a DB UUID, "openai-prod",
    "anthropic-eu").  The same provider type can be registered multiple
    times with different IDs (and different credentials).
    """

    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, provider_id: str, provider: BaseProvider) -> None:
        """Register (or replace) a provider by ID."""
        with self._lock:
            self._providers[provider_id] = provider
        logger.info(
            "provider_registry.registered",
            provider_id=provider_id,
            provider_type=provider.provider_type,
        )

    def unregister(self, provider_id: str) -> None:
        """Remove a provider from the registry (e.g. when creds are deleted)."""
        with self._lock:
            removed = self._providers.pop(provider_id, None)
        if removed:
            logger.info(
                "provider_registry.unregistered",
                provider_id=provider_id,
                provider_type=removed.provider_type,
            )

    def invalidate(self, provider_id: str) -> None:
        """Alias for unregister — signals that cached credentials are stale."""
        self.unregister(provider_id)

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get(self, provider_id: str) -> BaseProvider:
        """Return the provider for the given ID or raise ProviderError."""
        with self._lock:
            provider = self._providers.get(provider_id)
        if provider is None:
            raise ProviderError(
                f"Provider '{provider_id}' not found in registry",
                status_code=503,
                error_code="provider_not_found",
                retryable=False,
            )
        return provider

    def get_or_none(self, provider_id: str) -> BaseProvider | None:
        """Return the provider or None if not registered."""
        with self._lock:
            return self._providers.get(provider_id)

    def all_providers(self) -> dict[str, BaseProvider]:
        """Return a snapshot of all registered providers."""
        with self._lock:
            return dict(self._providers)

    def registered_ids(self) -> list[str]:
        """Return all registered provider IDs."""
        with self._lock:
            return list(self._providers.keys())

    def __len__(self) -> int:
        with self._lock:
            return len(self._providers)

    def __contains__(self, provider_id: str) -> bool:
        with self._lock:
            return provider_id in self._providers


# Global singleton — import this in startup code to register providers
provider_registry = ProviderRegistry()
