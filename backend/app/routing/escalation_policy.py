"""
Escalation Policy for test-aware coding routing.

Decides whether to:
- Stop (if solution passes or stopping condition met)
- Retry with current model (e.g. compilation error or repairable output)
- Escalate to a stronger or different model (e.g. wrong answer, TLE, or repeated failure)

Tracks attempt history, token and cost budgets, and produces structured diagnostics.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional


class EscalationAction(str, Enum):
    STOP_ACCEPTED = "stop_accepted"
    STOP_BUDGET_EXCEEDED = "stop_budget_exceeded"
    STOP_MAX_ATTEMPTS = "stop_max_attempts"
    STOP_TIMEOUT = "stop_timeout"
    STOP_NO_CANDIDATE = "stop_no_candidate"
    RETRY_SAME_MODEL = "retry_same_model"
    ESCALATE_NEXT_MODEL = "escalate_next_model"


@dataclass(frozen=True)
class AttemptRecord:
    attempt_number: int
    model_id: str
    provider_name: str
    code: str
    status: str  # accepted, compilation_error, wrong_answer, runtime_error, time_limit_exceeded, infrastructure_error
    passed_tests: int
    total_tests: int
    cost_usd: float
    latency_ms: float
    diagnostics: Optional[str] = None
    compiler_output: Optional[str] = None
    runtime_stderr: Optional[str] = None


@dataclass(frozen=True)
class EscalationDecision:
    action: EscalationAction
    target_model_id: Optional[str]
    target_provider: Optional[str]
    reason: str
    repair_prompt_feedback: Optional[str] = None
    excluded_models: List[str] = field(default_factory=list)


class EscalationPolicy:
    """
    Decides the next action when a generated coding solution fails or passes.
    Enforces maximum attempts, cumulative cost limits, and latency budgets.
    """

    def __init__(
        self,
        max_attempts: int = 3,
        max_cost_usd: float = 0.05,
        max_latency_ms: float = 30000.0,
        allow_same_model_retry_on_compilation_error: bool = True,
    ):
        self.max_attempts = max_attempts
        self.max_cost_usd = max_cost_usd
        self.max_latency_ms = max_latency_ms
        self.allow_same_model_retry_on_compilation_error = allow_same_model_retry_on_compilation_error

    def evaluate(
        self,
        attempts: List[AttemptRecord],
        candidate_models: List[Dict[str, Any]],  # candidate models from router or profiles
    ) -> EscalationDecision:
        if not attempts:
            raise ValueError("EscalationPolicy requires at least one attempt to evaluate.")

        last_attempt = attempts[-1]
        cumulative_cost = sum(a.cost_usd for a in attempts)
        cumulative_latency = sum(a.latency_ms for a in attempts)

        # 1. Stop if solution accepted
        if last_attempt.status == "accepted" and last_attempt.passed_tests == last_attempt.total_tests:
            return EscalationDecision(
                action=EscalationAction.STOP_ACCEPTED,
                target_model_id=None,
                target_provider=None,
                reason=f"Solution accepted on attempt {last_attempt.attempt_number} using {last_attempt.model_id}.",
            )

        # 2. Check stopping conditions: Maximum attempts
        if len(attempts) >= self.max_attempts:
            return EscalationDecision(
                action=EscalationAction.STOP_MAX_ATTEMPTS,
                target_model_id=None,
                target_provider=None,
                reason=f"Stopping condition reached: Maximum attempts ({self.max_attempts}) exhausted.",
            )

        # 3. Check stopping conditions: Cost budget
        if cumulative_cost >= self.max_cost_usd:
            return EscalationDecision(
                action=EscalationAction.STOP_BUDGET_EXCEEDED,
                target_model_id=None,
                target_provider=None,
                reason=f"Stopping condition reached: Cumulative cost ${cumulative_cost:.5f} exceeded budget ${self.max_cost_usd:.5f}.",
            )

        # 4. Check stopping conditions: Latency budget
        if cumulative_latency >= self.max_latency_ms:
            return EscalationDecision(
                action=EscalationAction.STOP_TIMEOUT,
                target_model_id=None,
                target_provider=None,
                reason=f"Stopping condition reached: Cumulative latency {cumulative_latency:.0f}ms exceeded budget {self.max_latency_ms:.0f}ms.",
            )

        # 5. Build structured feedback based on failure mode
        feedback = self._build_diagnostics(last_attempt)

        # 6. Decide whether to retry same model or escalate
        # A single compilation error can optionally be retried on the same model with compiler output
        already_retried_same = (
            len(attempts) >= 2 and attempts[-1].model_id == attempts[-2].model_id
        )
        if (
            self.allow_same_model_retry_on_compilation_error
            and last_attempt.status == "compilation_error"
            and not already_retried_same
        ):
            return EscalationDecision(
                action=EscalationAction.RETRY_SAME_MODEL,
                target_model_id=last_attempt.model_id,
                target_provider=last_attempt.provider_name,
                reason=f"Compilation error on {last_attempt.model_id}. Retrying with compiler diagnostic output.",
                repair_prompt_feedback=feedback,
            )

        # 7. Escalate to the next eligible candidate
        attempted_model_ids = {a.model_id for a in attempts}
        eligible_candidates = [
            m for m in candidate_models
            if m["model_id"] not in attempted_model_ids
            and m.get("avg_cost_per_attempt", 0.0) <= (self.max_cost_usd - cumulative_cost)
        ]

        if not eligible_candidates:
            # If no new model within budget remains, check if any remaining model exists
            remaining_unattempted = [m for m in candidate_models if m["model_id"] not in attempted_model_ids]
            if not remaining_unattempted:
                return EscalationDecision(
                    action=EscalationAction.STOP_NO_CANDIDATE,
                    target_model_id=None,
                    target_provider=None,
                    reason="Stopping condition reached: All eligible candidate models have been exhausted.",
                )
            # Budget exhausted for stronger models
            return EscalationDecision(
                action=EscalationAction.STOP_BUDGET_EXCEEDED,
                target_model_id=None,
                target_provider=None,
                reason=f"Stopping condition reached: Remaining budget ${self.max_cost_usd - cumulative_cost:.5f} cannot afford remaining candidates.",
            )

        # Select next candidate (highest utility or capability in candidate list)
        next_model = eligible_candidates[0]
        return EscalationDecision(
            action=EscalationAction.ESCALATE_NEXT_MODEL,
            target_model_id=next_model["model_id"],
            target_provider=next_model.get("provider_name", "openai"),
            reason=f"Failure ({last_attempt.status}) on {last_attempt.model_id}. Escalating to {next_model['model_id']}.",
            repair_prompt_feedback=feedback,
            excluded_models=list(attempted_model_ids),
        )

    def _build_diagnostics(self, attempt: AttemptRecord) -> str:
        if attempt.status == "compilation_error":
            return f"Compiler Error Output:\n{attempt.compiler_output or attempt.diagnostics or 'Syntax/compilation failed'}"
        elif attempt.status == "time_limit_exceeded":
            return "Time Limit Exceeded: The solution timed out (>3.0s). Algorithmic optimization to lower time complexity is required."
        elif attempt.status == "runtime_error":
            return f"Runtime Error:\n{attempt.runtime_stderr or attempt.diagnostics or 'Exception occurred during execution'}"
        elif attempt.status == "wrong_answer":
            return f"Wrong Answer on test cases ({attempt.passed_tests}/{attempt.total_tests} passed).\nDetails:\n{attempt.diagnostics or 'Output differed from expected'}"
        return attempt.diagnostics or f"Execution failed with status: {attempt.status}"

