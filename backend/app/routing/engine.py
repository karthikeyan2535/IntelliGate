"""
Evaluation-Driven Intelligent Routing Engine for IntelliGate.
Analyzes task requirements and complexity, filters models based on capability profiles,
and computes multi-objective utility scores using empirical benchmark quality, cost, latency, and reliability.
Returns optimal model selection with transparent, human-readable routing explanations.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Optional
import structlog

from app.evaluation.profiles import ModelPerformanceProfile, ProfileManager
from app.routing.classifier import ClassificationResult, ComplexityLevel, TaskCategory, TaskClassifier
from app.routing.circuit_breaker import CircuitState, get_circuit_breaker
from app.routing.health_monitor import get_health_monitor

logger = structlog.get_logger(__name__)


@dataclass
class CandidateScore:
    model_id: str
    provider: str
    overall_score: float
    quality_score: float
    cost_score: float
    latency_score: float
    reliability_score: float
    cost_per_1k: float
    latency_ms: float
    rank: int = 1


@dataclass
class RouteCandidate:
    provider_name: str
    model_name: str
    priority: int = 1
    weight: float = 1.0


@dataclass
class RoutingDecision:
    mode: str  # "intelligent", "lowest_cost", "direct"
    task_category: str
    complexity: str
    selected_model: str
    selected_provider: str
    fallback_candidates: list[tuple[str, str]]  # list of (provider, model)
    reason: str
    candidate_scores: list[CandidateScore] = field(default_factory=list)


class RoutingEngine:
    """Evaluation-driven intelligent model selection engine."""

    def __init__(self):
        self.circuit_breaker = get_circuit_breaker()
        self.health_monitor = get_health_monitor()

    async def route(
        self,
        prompt: str,
        requested_model: Optional[str] = None,
        routing_mode: str = "intelligent",
        max_tokens_needed: Optional[int] = None,
    ) -> RoutingDecision:
        """
        Executes routing decision:
        1. Classifies task category & complexity.
        2. Filters eligible models.
        3. Ranks candidates via multi-objective utility scoring.
        4. Selects optimal model and builds fallback chain.
        """
        # 1. Direct Routing Mode (if explicitly requested and not set to intelligent/auto)
        clean_model = (requested_model or "").strip().lower()
        if routing_mode == "direct" or (
            clean_model
            and clean_model not in {"auto", "intelligent", "fast-model", "balanced-model", "premium-model"}
            and routing_mode != "intelligent"
            and routing_mode != "lowest_cost"
        ):
            return self._handle_direct_routing(requested_model or "gpt-4o")

        # 2. Task Classification & Complexity Estimation
        classification = TaskClassifier.classify(prompt)
        category_str = classification.category.value
        complexity_str = classification.complexity.value

        # 3. Filter Eligible Models
        all_profiles = ProfileManager.get_all()
        eligible: list[ModelPerformanceProfile] = []

        for p in all_profiles:
            # Check context window
            if max_tokens_needed and p.context_window < max_tokens_needed:
                continue
            # Check circuit breaker
            cb_state = await self.circuit_breaker.get_state(p.provider)
            if cb_state == CircuitState.OPEN:
                logger.warning("Omitting candidate due to OPEN circuit breaker", provider=p.provider)
                continue
            eligible.append(p)

        if not eligible:
            eligible = all_profiles  # Emergency fallback

        # 4. Routing Mode Selection: Lowest-Cost Mode
        if routing_mode == "lowest_cost" or clean_model == "fast-model":
            return self._handle_lowest_cost_routing(eligible, classification)

        # 5. Intelligent Routing Mode (Evaluation-Driven Multi-Objective Optimization)
        return self._handle_intelligent_routing(eligible, classification)

    async def select_route_candidates(
        self,
        requested_model: str,
        strategy: str = "intelligent",
        prompt: str = "",
    ) -> list[RouteCandidate]:
        """Convenience method returning candidates list from a routing decision."""
        decision = await self.route(prompt=prompt, requested_model=requested_model, routing_mode=strategy)
        candidates = [
            RouteCandidate(
                provider_name=decision.selected_provider,
                model_name=decision.selected_model,
                priority=1,
            )
        ]
        for idx, (prov, mod) in enumerate(decision.fallback_candidates):
            candidates.append(
                RouteCandidate(
                    provider_name=prov,
                    model_name=mod,
                    priority=idx + 2,
                )
            )
        return candidates

    def _handle_direct_routing(self, model_name: str) -> RoutingDecision:
        profile = ProfileManager.get(model_name)
        prov = profile.provider if profile else ("gemini" if "gemini" in model_name else "openai")
        mod = profile.model_id if profile else model_name

        return RoutingDecision(
            mode="direct",
            task_category="unspecified",
            complexity="unspecified",
            selected_model=mod,
            selected_provider=prov,
            fallback_candidates=[("groq", "llama-3.3-70b-versatile"), ("openai", "gpt-4o-mini")],
            reason=f"Direct model requested: '{model_name}'. Bypassing intelligent evaluation ranking.",
        )

    def _handle_lowest_cost_routing(
        self,
        profiles: list[ModelPerformanceProfile],
        classification: ClassificationResult,
    ) -> RoutingDecision:
        # Sort by total blended token cost (input + output)
        sorted_by_cost = sorted(
            profiles,
            key=lambda p: float(p.input_cost_per_1k + p.output_cost_per_1k),
        )
        winner = sorted_by_cost[0]
        fallbacks = [(p.provider, p.model_id) for p in sorted_by_cost[1:3]]

        reason = (
            f"Lowest-cost mode selected {winner.display_name} "
            f"(${float(winner.input_cost_per_1k):.6f}/1K input tokens) for {classification.complexity.value} "
            f"{classification.category.value} task."
        )

        scores = [
            CandidateScore(
                model_id=p.model_id,
                provider=p.provider,
                overall_score=round(1.0 - (idx * 0.1), 3),
                quality_score=p.get_quality_for_category(classification.category.value),
                cost_score=1.0,
                latency_score=0.9,
                reliability_score=p.reliability,
                cost_per_1k=float(p.input_cost_per_1k),
                latency_ms=p.avg_latency_ms,
                rank=idx + 1,
            )
            for idx, p in enumerate(sorted_by_cost)
        ]

        return RoutingDecision(
            mode="lowest_cost",
            task_category=classification.category.value,
            complexity=classification.complexity.value,
            selected_model=winner.model_id,
            selected_provider=winner.provider,
            fallback_candidates=fallbacks,
            reason=reason,
            candidate_scores=scores,
        )

    def _handle_intelligent_routing(
        self,
        profiles: list[ModelPerformanceProfile],
        classification: ClassificationResult,
    ) -> RoutingDecision:
        category = classification.category.value
        complexity = classification.complexity

        # Dynamic weight configuration based on task complexity
        if complexity == ComplexityLevel.COMPLEX:
            # Complex tasks (e.g. complex algorithms, advanced proofs): Quality is paramount!
            w_quality = 0.60
            w_cost = 0.20
            w_latency = 0.15
            w_reliability = 0.05
        elif complexity == ComplexityLevel.SIMPLE:
            # Simple tasks (e.g. quick Q&A, formatting): Cost & speed are prioritized!
            w_quality = 0.30
            w_cost = 0.45
            w_latency = 0.20
            w_reliability = 0.05
        else:
            # Moderate complexity: Balanced trade-off
            w_quality = 0.45
            w_cost = 0.35
            w_latency = 0.15
            w_reliability = 0.05

        # Normalize metrics across eligible candidate pool
        costs = [float(p.input_cost_per_1k) for p in profiles]
        latencies = [p.avg_latency_ms for p in profiles]

        min_cost, max_cost = min(costs), max(costs)
        min_lat, max_lat = min(latencies), max(latencies)

        scored_candidates: list[CandidateScore] = []

        for p in profiles:
            quality = p.get_quality_for_category(category)

            # Cost score (inverted: 1.0 = cheapest, 0.0 = most expensive)
            p_cost = float(p.input_cost_per_1k)
            cost_norm = (max_cost - p_cost) / (max_cost - min_cost) if max_cost > min_cost else 1.0

            # Latency score (inverted: 1.0 = fastest, 0.0 = slowest)
            p_lat = p.avg_latency_ms
            lat_norm = (max_lat - p_lat) / (max_lat - min_lat) if max_lat > min_lat else 1.0

            # Multi-objective utility function
            overall = (
                (w_quality * quality) +
                (w_cost * cost_norm) +
                (w_latency * lat_norm) +
                (w_reliability * p.reliability)
            )

            scored_candidates.append(CandidateScore(
                model_id=p.model_id,
                provider=p.provider,
                overall_score=round(overall, 4),
                quality_score=round(quality, 3),
                cost_score=round(cost_norm, 3),
                latency_score=round(lat_norm, 3),
                reliability_score=p.reliability,
                cost_per_1k=p_cost,
                latency_ms=p_lat,
            ))

        # Sort candidates by overall score descending
        scored_candidates.sort(key=lambda s: s.overall_score, reverse=True)
        for idx, s in enumerate(scored_candidates):
            s.rank = idx + 1

        winner_score = scored_candidates[0]
        winner_prof = ProfileManager.get(winner_score.model_id)

        fallbacks = [(s.provider, s.model_id) for s in scored_candidates[1:3]]

        reason = (
            f"Selected {winner_prof.display_name if winner_prof else winner_score.model_id} "
            f"via Intelligent Routing for {complexity.value} {category}. "
            f"Benchmark quality score of {winner_score.quality_score:.2f} and {winner_score.latency_ms:.0f}ms latency "
            f"yielded highest composite utility ({winner_score.overall_score:.3f}) under {complexity.value} complexity weighting."
        )

        return RoutingDecision(
            mode="intelligent",
            task_category=category,
            complexity=complexity.value,
            selected_model=winner_score.model_id,
            selected_provider=winner_score.provider,
            fallback_candidates=fallbacks,
            reason=reason,
            candidate_scores=scored_candidates,
        )


_routing_engine: Optional[RoutingEngine] = None


def get_routing_engine() -> RoutingEngine:
    global _routing_engine
    if _routing_engine is None:
        _routing_engine = RoutingEngine()
    return _routing_engine
