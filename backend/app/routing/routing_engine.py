"""
Bounded orchestration of model routing, generation, verification, and escalation.

The provider and sandbox are injected. This module does NOT execute arbitrary code directly.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from time import monotonic
from typing import Dict, Any, List, Optional, Protocol

from .coding_router import CodingRouter
from .escalation_policy import AttemptRecord, EscalationPolicy, EscalationAction, EscalationDecision


@dataclass(frozen=True)
class SolveRequest:
    problem: str
    algorithm_category: str
    difficulty: str
    language: str = "cpp17"
    routing_mode: str = "intelligent"
    target_model: Optional[str] = None
    max_attempts: int = 3
    max_cost_usd: float = 0.05
    max_latency_ms: float = 30000.0
    title: str = "Coding Task"
    constraints: Optional[str] = ""
    input_format: Optional[str] = ""
    output_format: Optional[str] = ""
    test_cases: List[Dict[str, str]] = field(default_factory=list)


@dataclass(frozen=True)
class GenerationResult:
    code: str
    cost_usd: float
    latency_ms: float
    explanation: Optional[str] = None
    time_complexity: Optional[str] = None
    space_complexity: Optional[str] = None


@dataclass(frozen=True)
class VerificationResult:
    status: str  # accepted, wrong_answer, compilation_error, runtime_error, time_limit_exceeded, infrastructure_error
    passed_tests: int
    total_tests: int
    execution_time_ms: float
    compiler_output: Optional[str] = None
    runtime_stdout: Optional[str] = None
    runtime_stderr: Optional[str] = None
    error_message: Optional[str] = None
    failed_cases: List[Dict[str, Any]] = field(default_factory=list)


class CodeGeneratorProtocol(Protocol):
    async def generate_code(
        self,
        model_id: str,
        provider_name: str,
        language: str,
        problem: str,
        previous_code: Optional[str] = None,
        feedback: Optional[str] = None,
        constraints: Optional[str] = "",
        sample_cases: Optional[List[Dict[str, str]]] = None,
    ) -> GenerationResult:
        ...


class SandboxVerifierProtocol(Protocol):
    async def verify_code(
        self,
        language: str,
        code: str,
        test_cases: List[Dict[str, str]],
        timeout_sec: float = 3.0,
    ) -> VerificationResult:
        ...


@dataclass
class SolveResponse:
    status: str
    final_code: Optional[str]
    initial_model: Optional[str]
    final_model: Optional[str]
    total_attempts: int
    passed_tests: int
    total_tests: int
    total_cost_usd: float
    total_latency_ms: float
    attempts: List[AttemptRecord]
    trace: List[Dict[str, Any]]


class RoutingEngine:
    """
    Coordinates model routing, generation, sandboxed verification, and escalation.
    Enforces maximum attempts, cumulative inference budget, and latency bounds.
    """

    def __init__(
        self,
        router: CodingRouter,
        escalation_policy: Optional[EscalationPolicy] = None,
        generator: Optional[CodeGeneratorProtocol] = None,
        verifier: Optional[SandboxVerifierProtocol] = None,
    ):
        self.router = router
        self.escalation_policy = escalation_policy or EscalationPolicy()
        self.generator = generator
        self.verifier = verifier

    async def solve(
        self,
        request: SolveRequest,
        generator: Optional[CodeGeneratorProtocol] = None,
        verifier: Optional[SandboxVerifierProtocol] = None,
    ) -> SolveResponse:
        active_gen = generator or self.generator
        active_ver = verifier or self.verifier

        if active_gen is None or active_ver is None:
            raise ValueError("RoutingEngine requires both a CodeGenerator and SandboxVerifier.")

        policy = EscalationPolicy(
            max_attempts=request.max_attempts,
            max_cost_usd=request.max_cost_usd,
            max_latency_ms=request.max_latency_ms,
        )

        trace: List[Dict[str, Any]] = []
        attempts: List[AttemptRecord] = []
        excluded_models: List[str] = []

        total_cost = 0.0
        total_latency = 0.0
        initial_model: Optional[str] = None
        current_code: Optional[str] = None
        feedback: Optional[str] = None
        target_model_override = request.target_model

        start_time = monotonic()

        for attempt_num in range(1, request.max_attempts + 1):
            remaining_cost = max(request.max_cost_usd - total_cost, 0.0)
            remaining_latency = max(request.max_latency_ms - total_latency, 0.0)

            # Check latency boundary before calling provider
            if (monotonic() - start_time) * 1000.0 >= request.max_latency_ms:
                trace.append({
                    "stage": f"attempt_{attempt_num}_timeout",
                    "status": "stopped",
                    "details": f"Latency budget ({request.max_latency_ms}ms) reached.",
                })
                break

            # 1. Routing Decision
            routing_res = await self.router.select_model(
                algorithm_category=request.algorithm_category,
                difficulty=request.difficulty,
                routing_mode=request.routing_mode,
                target_model=target_model_override,
                cost_budget_usd=remaining_cost,
                latency_budget_ms=int(remaining_latency),
                excluded_models=excluded_models,
            )

            selected_model = routing_res.selected_model
            provider_name = routing_res.provider_name

            if attempt_num == 1:
                initial_model = selected_model

            trace.append({
                "stage": f"attempt_{attempt_num}_routing",
                "status": "completed",
                "model": selected_model,
                "provider": provider_name,
                "reason": routing_res.decision_reason,
            })

            # 2. Code Generation
            gen_start = monotonic()
            try:
                gen_res = await active_gen.generate_code(
                    model_id=selected_model,
                    provider_name=provider_name,
                    language=request.language,
                    problem=request.problem,
                    previous_code=current_code,
                    feedback=feedback,
                    constraints=request.constraints,
                    sample_cases=request.test_cases,
                )
            except Exception as e:
                # If generation fails due to provider error, exclude model and escalate
                trace.append({
                    "stage": f"attempt_{attempt_num}_generation_error",
                    "status": "provider_error",
                    "details": f"Provider error on {selected_model}: {str(e)}",
                })
                excluded_models.append(selected_model)
                target_model_override = None
                continue

            current_code = gen_res.code
            step_cost = gen_res.cost_usd
            step_latency = gen_res.latency_ms or ((monotonic() - gen_start) * 1000.0)

            total_cost += step_cost
            total_latency += step_latency

            # 3. Sandboxed Verification
            ver_res = await active_ver.verify_code(
                language=request.language,
                code=current_code,
                test_cases=request.test_cases,
            )

            total_latency += ver_res.execution_time_ms

            # Create attempt record
            diag_str = ver_res.error_message
            if ver_res.status == "wrong_answer" and ver_res.failed_cases:
                first = ver_res.failed_cases[0]
                diag_str = f"Wrong Answer on input {first.get('input')!r}. Expected {first.get('expected')!r}, got {first.get('actual')!r}"

            record = AttemptRecord(
                attempt_number=attempt_num,
                model_id=selected_model,
                provider_name=provider_name,
                code=current_code,
                status=ver_res.status,
                passed_tests=ver_res.passed_tests,
                total_tests=ver_res.total_tests,
                cost_usd=step_cost,
                latency_ms=step_latency + ver_res.execution_time_ms,
                diagnostics=diag_str,
                compiler_output=ver_res.compiler_output,
                runtime_stderr=ver_res.runtime_stderr,
            )
            attempts.append(record)

            trace.append({
                "stage": f"attempt_{attempt_num}_verification",
                "status": ver_res.status,
                "passed_tests": f"{ver_res.passed_tests}/{ver_res.total_tests}",
                "cost_usd": step_cost,
            })

            # 4. Evaluate Escalation Policy
            # Prepare candidates for policy
            candidates = [
                {"model_id": c.model_id, "provider_name": c.provider_name, "avg_cost_per_attempt": c.cost_usd}
                for c in routing_res.candidate_rankings
            ] if routing_res.candidate_rankings else [{"model_id": selected_model, "avg_cost_per_attempt": step_cost}]

            decision: EscalationDecision = policy.evaluate(attempts, candidates)

            trace.append({
                "stage": f"attempt_{attempt_num}_escalation",
                "action": decision.action.value,
                "reason": decision.reason,
            })

            if decision.action in (
                EscalationAction.STOP_ACCEPTED,
                EscalationAction.STOP_BUDGET_EXCEEDED,
                EscalationAction.STOP_MAX_ATTEMPTS,
                EscalationAction.STOP_TIMEOUT,
                EscalationAction.STOP_NO_CANDIDATE,
            ):
                break

            # Setup next attempt state
            feedback = decision.repair_prompt_feedback
            if decision.action == EscalationAction.RETRY_SAME_MODEL:
                target_model_override = decision.target_model_id
            elif decision.action == EscalationAction.ESCALATE_NEXT_MODEL:
                target_model_override = decision.target_model_id
                excluded_models.append(selected_model)

        final_status = attempts[-1].status if attempts else "no_attempts"
        final_code = attempts[-1].code if attempts else None
        final_model = attempts[-1].model_id if attempts else None
        passed_tests = attempts[-1].passed_tests if attempts else 0
        total_tests = attempts[-1].total_tests if attempts else len(request.test_cases)

        return SolveResponse(
            status=final_status,
            final_code=final_code,
            initial_model=initial_model,
            final_model=final_model,
            total_attempts=len(attempts),
            passed_tests=passed_tests,
            total_tests=total_tests,
            total_cost_usd=round(total_cost, 6),
            total_latency_ms=round(total_latency, 1),
            attempts=attempts,
            trace=trace,
        )

