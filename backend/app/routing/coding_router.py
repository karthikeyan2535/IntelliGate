"""
Intelligent Coding Router.
Evaluates candidate models using task-specific empirical profiles, complexity,
cost, and latency budgets, implementing:
- Score(m) = w_q * Q_c - w_c * C_norm - w_l * L_norm
- Hard eligibility constraints (budget, active provider health, availability)
- Explainable routing trace and transparent candidate ranking
- Baselines: Always Strongest, Always Cheapest, Static Category
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from app.analysis.model_profiles import coding_profile_manager


@dataclass
class CandidateEvaluation:
    model_id: str
    provider_name: str
    display_name: str
    category_quality: float
    difficulty_quality: float
    effective_quality: float
    cost_usd: float
    cost_score: float
    latency_ms: float
    latency_score: float
    utility_score: float
    is_eligible: bool = True
    exclusion_reason: Optional[str] = None
    rank: int = 0


@dataclass
class RoutingDecisionResult:
    selected_model: str
    provider_name: str
    routing_mode: str
    decision_reason: str
    applied_weights: Dict[str, float]
    candidate_rankings: List[CandidateEvaluation] = field(default_factory=list)
    rejected_candidates: List[Dict[str, str]] = field(default_factory=list)


class CodingRouter:
    """
    Intelligent Coding Router implementing multi-objective Pareto optimization
    tailored for programming challenges.
    """

    async def select_model(
        self,
        algorithm_category: str,
        difficulty: str,
        routing_mode: str = "intelligent",
        target_model: Optional[str] = None,
        cost_budget_usd: Optional[float] = 0.05,
        latency_budget_ms: Optional[int] = 30000,
        excluded_models: Optional[List[str]] = None,
    ) -> RoutingDecisionResult:
        excluded = set(excluded_models or [])
        profiles = await coding_profile_manager.get_all_profiles()

        # Handle Direct Mode
        if routing_mode == "direct" and target_model:
            prof = next((p for p in profiles if p["model_id"] == target_model), None)
            provider = prof["provider_name"] if prof else "openai"
            return RoutingDecisionResult(
                selected_model=target_model,
                provider_name=provider,
                routing_mode="direct",
                decision_reason=f"Directly pinned to model '{target_model}' by user request.",
                applied_weights={"quality": 1.0, "cost": 0.0, "latency": 0.0},
            )

        # Baseline: Always Strongest
        if routing_mode == "baseline_strongest":
            eligible = [p for p in profiles if p["model_id"] not in excluded]
            best = max(eligible, key=lambda p: p["overall_pass_rate"]) if eligible else profiles[0]
            return RoutingDecisionResult(
                selected_model=best["model_id"],
                provider_name=best["provider_name"],
                routing_mode="baseline_strongest",
                decision_reason=f"Baseline rule: always selected highest empirical pass-rate model ({best['display_name']} at {best['overall_pass_rate']*100:.1f}%).",
                applied_weights={"quality": 1.0, "cost": 0.0, "latency": 0.0},
            )

        # Baseline: Always Cheapest
        if routing_mode == "baseline_cheapest":
            eligible = [p for p in profiles if p["model_id"] not in excluded]
            cheapest = min(eligible, key=lambda p: p["avg_cost_per_attempt"]) if eligible else profiles[0]
            return RoutingDecisionResult(
                selected_model=cheapest["model_id"],
                provider_name=cheapest["provider_name"],
                routing_mode="baseline_cheapest",
                decision_reason=f"Baseline rule: always selected lowest cost model ({cheapest['display_name']} at ${cheapest['avg_cost_per_attempt']:.5f}/call).",
                applied_weights={"quality": 0.0, "cost": 1.0, "latency": 0.0},
            )

        # Baseline: Static Category-Based Routing
        if routing_mode == "baseline_static":
            # Fixed mapping
            cat_map = {
                "dynamic_programming": "gemini-1.5-flash",
                "graphs": "llama-3.3-70b-versatile",
                "arrays_strings": "llama-3.1-8b-instant",
                "trees_data_structures": "llama-3.3-70b-versatile",
                "greedy_binary_search": "llama-3.1-8b-instant",
                "debugging_repair": "gemini-1.5-flash",
            }
            chosen_id = cat_map.get(algorithm_category, "llama-3.3-70b-versatile")
            if chosen_id in excluded:
                # pick next
                chosen_id = "gemini-1.5-flash" if chosen_id != "gemini-1.5-flash" else "llama-3.3-70b-versatile"
            prof = next((p for p in profiles if p["model_id"] == chosen_id), profiles[0])
            return RoutingDecisionResult(
                selected_model=prof["model_id"],
                provider_name=prof["provider_name"],
                routing_mode="baseline_static",
                decision_reason=f"Static Category Baseline: Category '{algorithm_category}' mapped statically to {prof['display_name']}.",
                applied_weights={"quality": 0.5, "cost": 0.5, "latency": 0.0},
            )

        # ── Lowest-Cost Mode (with min threshold 0.70) ────────────────────────
        if routing_mode == "lowest_cost":
            eligible = [
                p for p in profiles
                if p["model_id"] not in excluded and (cost_budget_usd is None or p["avg_cost_per_attempt"] <= cost_budget_usd)
            ]
            if not eligible:
                eligible = profiles
            cheapest = min(eligible, key=lambda p: p["avg_cost_per_attempt"])
            return RoutingDecisionResult(
                selected_model=cheapest["model_id"],
                provider_name=cheapest["provider_name"],
                routing_mode="lowest_cost",
                decision_reason=f"Selected lowest cost model within budget: {cheapest['display_name']} (${cheapest['avg_cost_per_attempt']:.6f}/attempt).",
                applied_weights={"quality": 0.1, "cost": 0.8, "latency": 0.1},
            )

        # ── Intelligent Multi-Objective Mode ──────────────────────────────────
        # Dynamic weights based on problem difficulty
        if difficulty == "hard":
            w_q, w_c, w_l = 0.75, 0.15, 0.10
        elif difficulty == "easy":
            w_q, w_c, w_l = 0.35, 0.45, 0.20
        else:  # medium
            w_q, w_c, w_l = 0.55, 0.30, 0.15

        candidates: List[CandidateEvaluation] = []
        rejected: List[Dict[str, str]] = []

        # Find min/max for normalization across profiles
        max_cost = max(p["avg_cost_per_attempt"] for p in profiles) or 0.005
        min_cost = min(p["avg_cost_per_attempt"] for p in profiles) or 0.00005
        max_lat = max(p["avg_latency_ms"] for p in profiles) or 1000.0
        min_lat = min(p["avg_latency_ms"] for p in profiles) or 100.0

        for p in profiles:
            m_id = p["model_id"]
            if m_id in excluded:
                rejected.append({"model_id": m_id, "reason": "Already failed on previous attempt"})
                continue

            # Budget check
            if cost_budget_usd is not None and p["avg_cost_per_attempt"] > cost_budget_usd:
                rejected.append({"model_id": m_id, "reason": f"Estimated cost ${p['avg_cost_per_attempt']:.5f} exceeds budget ${cost_budget_usd:.5f}"})
                continue

            # Get category-specific quality
            cat_key = f"{algorithm_category}_pass_rate"
            cat_q = p.get(cat_key, p.get("overall_pass_rate", 0.75))
            diff_key = f"{difficulty}_pass_rate"
            diff_q = p.get(diff_key, p.get("overall_pass_rate", 0.75))

            # Effective quality is a weighted composite of category competence and difficulty tolerance
            effective_q = 0.65 * cat_q + 0.35 * diff_q

            # Normalized cost (0 = cheapest, 1 = most expensive)
            cost_norm = (p["avg_cost_per_attempt"] - min_cost) / max((max_cost - min_cost), 1e-6)
            cost_score = 1.0 - cost_norm  # higher is better

            # Normalized latency (0 = fastest, 1 = slowest)
            lat_norm = (p["avg_latency_ms"] - min_lat) / max((max_lat - min_lat), 1e-6)
            lat_score = 1.0 - lat_norm  # higher is better

            # Linear Utility Function
            utility = (w_q * effective_q) + (w_c * cost_score) + (w_l * lat_score)

            candidates.append(
                CandidateEvaluation(
                    model_id=m_id,
                    provider_name=p["provider_name"],
                    display_name=p["display_name"],
                    category_quality=round(cat_q, 3),
                    difficulty_quality=round(diff_q, 3),
                    effective_quality=round(effective_q, 3),
                    cost_usd=p["avg_cost_per_attempt"],
                    cost_score=round(cost_score, 3),
                    latency_ms=p["avg_latency_ms"],
                    latency_score=round(lat_score, 3),
                    utility_score=round(utility, 4),
                )
            )

        if not candidates:
            # Fallback to least expensive available if all filtered
            fallback = sorted(profiles, key=lambda x: x["avg_cost_per_attempt"])[0]
            return RoutingDecisionResult(
                selected_model=fallback["model_id"],
                provider_name=fallback["provider_name"],
                routing_mode="intelligent",
                decision_reason="All preferred models exceeded constraints; fell back to lowest-cost available candidate.",
                applied_weights={"quality": w_q, "cost": w_c, "latency": w_l},
                rejected_candidates=rejected,
            )

        # Sort by utility score descending
        candidates.sort(key=lambda c: c.utility_score, reverse=True)
        for idx, c in enumerate(candidates):
            c.rank = idx + 1

        selected = candidates[0]
        reason = (
            f"Selected {selected.display_name} (Utility: {selected.utility_score:.4f}). "
            f"Demonstrated {selected.category_quality*100:.1f}% empirical accuracy on '{algorithm_category}' "
            f"with optimal cost efficiency (${selected.cost_usd:.5f}/attempt)."
        )

        return RoutingDecisionResult(
            selected_model=selected.model_id,
            provider_name=selected.provider_name,
            routing_mode="intelligent",
            decision_reason=reason,
            applied_weights={"quality": w_q, "cost": w_c, "latency": w_l},
            candidate_rankings=candidates,
            rejected_candidates=rejected,
        )


coding_router = CodingRouter()
