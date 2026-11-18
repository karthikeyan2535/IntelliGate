"""
Intelligent Routing Engine for IntelliGate.
Supports Direct, Priority, Weighted, Lowest-Cost, Lowest-Latency, and Health-Aware routing strategies.
Resolves model aliases (fast-model, balanced-model, premium-model) and generates fallback chains.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Optional
import structlog

from app.routing.circuit_breaker import CircuitState, get_circuit_breaker
from app.routing.health_monitor import get_health_monitor
from app.accounting.pricing import CostCalculator

logger = structlog.get_logger(__name__)

# Standard model alias mappings
MODEL_ALIASES: dict[str, list[dict[str, str]]] = {
    "fast-model": [
        {"provider": "openai", "model": "gpt-4o-mini", "priority": 100, "weight": 50},
        {"provider": "gemini", "model": "gemini-1.5-flash", "priority": 90, "weight": 30},
        {"provider": "anthropic", "model": "claude-3-5-haiku-20241022", "priority": 80, "weight": 20},
    ],
    "balanced-model": [
        {"provider": "openai", "model": "gpt-4o", "priority": 100, "weight": 50},
        {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022", "priority": 90, "weight": 30},
        {"provider": "gemini", "model": "gemini-1.5-pro", "priority": 80, "weight": 20},
    ],
    "premium-model": [
        {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022", "priority": 100, "weight": 40},
        {"provider": "openai", "model": "gpt-4o", "priority": 90, "weight": 40},
        {"provider": "openai", "model": "o1", "priority": 80, "weight": 20},
    ],
}


@dataclass
class RouteCandidate:
    provider_name: str
    model_name: str
    priority: int = 100
    weight: int = 1
    estimated_cost_per_1k: Decimal = Decimal("0.001")
    avg_latency_ms: float = 200.0
    is_healthy: bool = True


class RoutingEngine:
    """Selects optimal provider/model combination based on active policy and operational health."""

    def __init__(self):
        self.circuit_breaker = get_circuit_breaker()
        self.health_monitor = get_health_monitor()

    def resolve_model_alias(self, requested_model: str) -> list[dict[str, Any]]:
        """Resolves alias like 'fast-model' to candidate list or returns single-element list."""
        clean_name = requested_model.strip().lower()
        if clean_name in MODEL_ALIASES:
            return MODEL_ALIASES[clean_name]

        # Check provider prefix (e.g. 'openai/gpt-4o' or 'anthropic/claude-3-5-sonnet')
        if "/" in requested_model:
            parts = requested_model.split("/", 1)
            return [{"provider": parts[0].strip().lower(), "model": parts[1].strip()}]

        # Direct model name inference
        if "claude" in clean_name:
            return [{"provider": "anthropic", "model": requested_model}]
        elif "gemini" in clean_name:
            return [{"provider": "gemini", "model": requested_model}]
        elif "mistral" in clean_name:
            return [{"provider": "mistral", "model": requested_model}]
        else:
            return [{"provider": "openai", "model": requested_model}]

    async def select_route_candidates(
        self,
        requested_model: str,
        strategy: str = "priority",
        fallback_enabled: bool = True,
    ) -> list[RouteCandidate]:
        """
        Builds an ordered sequence of eligible provider route candidates.
        Discards candidates whose circuit breaker is OPEN.
        """
        raw_candidates = self.resolve_model_alias(requested_model)
        candidates: list[RouteCandidate] = []

        for item in raw_candidates:
            prov_name = item.get("provider", "openai")
            mod_name = item.get("model", requested_model)
            prio = int(item.get("priority", 100))
            wt = int(item.get("weight", 1))

            # Circuit breaker check
            cb_state = await self.circuit_breaker.get_state(prov_name)
            if cb_state == CircuitState.OPEN:
                logger.warning("Omitting candidate due to OPEN circuit breaker", provider=prov_name)
                continue

            # Health data
            health = await self.health_monitor.get_health_snapshot(prov_name)

            # Pricing estimate
            rates = CostCalculator.get_rates(prov_name, mod_name)
            cost_rate = rates.get("input", Decimal("0.001"))

            candidates.append(RouteCandidate(
                provider_name=prov_name,
                model_name=mod_name,
                priority=prio,
                weight=wt,
                estimated_cost_per_1k=cost_rate,
                avg_latency_ms=health.avg_latency_ms,
                is_healthy=health.is_healthy,
            ))

        if not candidates:
            # Fallback emergency candidate if all circuits were OPEN
            prov_fallback = raw_candidates[0].get("provider", "openai")
            candidates.append(RouteCandidate(
                provider_name=prov_fallback,
                model_name=raw_candidates[0].get("model", requested_model),
            ))

        # Apply strategy ordering
        strat = strategy.lower()
        if strat == "lowest_cost":
            candidates.sort(key=lambda c: c.estimated_cost_per_1k)
        elif strat == "lowest_latency":
            candidates.sort(key=lambda c: (not c.is_healthy, c.avg_latency_ms))
        elif strat == "weighted" and len(candidates) > 1:
            # Reorder with primary chosen by roulette wheel weight
            weights = [max(1, c.weight) for c in candidates]
            chosen = random.choices(candidates, weights=weights, k=1)[0]
            candidates.remove(chosen)
            candidates.insert(0, chosen)
        elif strat == "health_aware":
            candidates.sort(key=lambda c: (not c.is_healthy, -c.priority))
        else:
            # Default: priority (higher priority first)
            candidates.sort(key=lambda c: -c.priority)

        return candidates if fallback_enabled else candidates[:1]


_routing_engine: Optional[RoutingEngine] = None


def get_routing_engine() -> RoutingEngine:
    global _routing_engine
    if _routing_engine is None:
        _routing_engine = RoutingEngine()
    return _routing_engine

