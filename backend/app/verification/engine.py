"""
Verification & Escalation Engine.
Orchestrates end-to-end coding problem verification lifecycle:
1. Problem Analysis & Structured Metadata
2. Initial Routing Decision
3. Code Generation
4. Sandboxed Compilation & Test Execution
5. Verification & Failure Diagnostics
6. Bounded Escalation / Repair Loop
7. Immutable Trace & Cost Accounting
"""
from __future__ import annotations

import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import select

from app.analysis.coding_analyzer import coding_analyzer
from app.analysis.model_profiles import coding_profile_manager
from app.routing.coding_router import coding_router
from app.generation.code_generator import code_generator
from app.execution.sandbox import sandbox_executor, ExecutionResult
from app.database.base import AsyncSessionLocal
from app.database.coding_models import CodingSubmission, CodingAttempt, CodingProblem, CodingTestCase


class VerificationEngine:
    """
    Manages complete problem execution, verification, and escalation lifecycle.
    """

    async def execute_problem(
        self,
        problem_id: Optional[str],
        title: str,
        statement: str,
        test_cases: List[Dict[str, str]],  # [{"input": "...", "expected": "..."}]
        language: str = "python",
        routing_mode: str = "intelligent",
        target_model: Optional[str] = None,
        max_attempts: int = 3,
        cost_budget_usd: Optional[float] = 0.05,
        latency_budget_ms: Optional[int] = 30000,
        constraints: Optional[str] = "",
        input_format: Optional[str] = "",
        output_format: Optional[str] = "",
        is_leetcode_style: bool = False,
    ) -> Dict[str, Any]:
        trace_stages = []
        start_time = datetime.datetime.now(datetime.timezone.utc)

        # ── Step 1: Problem Analysis ──────────────────────────────────────────
        analysis = coding_analyzer.analyze(title, statement, constraints)
        trace_stages.append({
            "stage": "problem_analysis",
            "status": "completed",
            "details": f"Classified task as '{analysis.task_type}' in domain '{analysis.algorithm_family}' (Difficulty: {analysis.difficulty}).",
            "metadata": analysis.model_dump(),
        })

        # Save submission to DB
        submission = CodingSubmission(
            problem_id=problem_id if problem_id else None,
            language=language,
            routing_mode=routing_mode,
            target_model=target_model,
            max_attempts=max_attempts,
            cost_budget_usd=cost_budget_usd,
            latency_budget_ms=latency_budget_ms,
            status="running",
            total_test_cases=len(test_cases),
        )

        async with AsyncSessionLocal() as session:
            session.add(submission)
            await session.commit()
            await session.refresh(submission)
            submission_id = submission.id

        total_cost = 0.0
        total_latency = 0
        attempts_data: List[Dict[str, Any]] = []
        excluded_models: List[str] = []

        final_status = "wrong_answer"
        final_solution_code = None
        initial_model = None
        current_code = None
        failure_feedback = None

        # ── Step 2: Bounded Generation, Execution, & Escalation Loop ──────────
        for attempt_num in range(1, max_attempts + 1):
            # Budget check
            if cost_budget_usd is not None and total_cost >= cost_budget_usd:
                trace_stages.append({
                    "stage": f"attempt_{attempt_num}_halted",
                    "status": "stopped",
                    "details": f"Stopping condition reached: Cumulative inference cost ${total_cost:.5f} reached budget ${cost_budget_usd:.5f}.",
                })
                break

            # A. Select model (Route / Escalate)
            routing_res = await coding_router.select_model(
                algorithm_category=analysis.algorithm_family,
                difficulty=analysis.difficulty,
                routing_mode=routing_mode,
                target_model=target_model,
                cost_budget_usd=cost_budget_usd - total_cost if cost_budget_usd else None,
                latency_budget_ms=latency_budget_ms - total_latency if latency_budget_ms else None,
                excluded_models=excluded_models,
            )

            if attempt_num == 1:
                initial_model = routing_res.selected_model

            trace_stages.append({
                "stage": f"attempt_{attempt_num}_routing",
                "status": "completed",
                "model": routing_res.selected_model,
                "provider": routing_res.provider_name,
                "reason": routing_res.decision_reason,
                "applied_weights": routing_res.applied_weights,
                "rankings": [
                    {
                        "rank": c.rank,
                        "model_id": c.model_id,
                        "quality": c.category_quality,
                        "cost": c.cost_usd,
                        "latency": c.latency_ms,
                        "utility": c.utility_score,
                    }
                    for c in routing_res.candidate_rankings[:4]
                ],
            })

            # B. Generate Code
            try:
                gen_res = await code_generator.generate(
                    model_id=routing_res.selected_model,
                    provider_name=routing_res.provider_name,
                    language=language,
                    title=title,
                    statement=statement,
                    constraints=constraints,
                    input_format=input_format,
                    output_format=output_format,
                    sample_cases=test_cases[:3],
                    previous_code=current_code,
                    failure_diagnostics=failure_feedback,
                    is_leetcode_style=is_leetcode_style,
                )
            except Exception as gen_err:
                # If provider failed (e.g. quota or timeout), escalate to another provider without penalty
                trace_stages.append({
                    "stage": f"attempt_{attempt_num}_generation_error",
                    "status": "provider_error",
                    "details": f"Provider error from {routing_res.selected_model}: {str(gen_err)}. Escalating to next candidate.",
                })
                excluded_models.append(routing_res.selected_model)
                continue

            current_code = gen_res.code
            total_cost += gen_res.cost_usd
            total_latency += gen_res.latency_ms

            # C. Sandboxed Execution & Verification
            exec_res: ExecutionResult = await sandbox_executor.execute(
                language=language,
                code=current_code,
                test_cases=test_cases,
                timeout_sec=3.0,
                is_leetcode_style=is_leetcode_style,
            )

            total_latency += exec_res.peak_latency_ms
            attempt_passed = exec_res.status == "accepted"

            # Record attempt
            attempt_dict = {
                "attempt_number": attempt_num,
                "model_id": routing_res.selected_model,
                "provider_name": routing_res.provider_name,
                "routing_reason": routing_res.decision_reason,
                "generated_code": current_code,
                "algorithm_explanation": gen_res.explanation,
                "complexity_estimate": f"{gen_res.time_complexity} time, {gen_res.space_complexity} space",
                "execution_status": exec_res.status,
                "passed_tests": exec_res.passed_count,
                "total_tests": exec_res.total_count,
                "compiler_output": exec_res.compilation_output,
                "runtime_stdout": exec_res.runtime_stdout,
                "runtime_stderr": exec_res.runtime_stderr,
                "error_message": exec_res.error_message,
                "prompt_tokens": gen_res.prompt_tokens,
                "completion_tokens": gen_res.completion_tokens,
                "cost_usd": gen_res.cost_usd,
                "latency_ms": gen_res.latency_ms + exec_res.peak_latency_ms,
                "failed_cases": [
                    {
                        "case": r.test_case_index,
                        "status": r.status,
                        "input": r.input_data,
                        "expected": r.expected_output,
                        "actual": r.actual_output,
                        "error": r.error_message,
                    }
                    for r in exec_res.results if not r.passed
                ],
            }
            attempts_data.append(attempt_dict)

            # Persist attempt to database
            async with AsyncSessionLocal() as session:
                attempt_db = CodingAttempt(
                    submission_id=submission_id,
                    attempt_number=attempt_num,
                    model_id=routing_res.selected_model,
                    provider_name=routing_res.provider_name,
                    routing_reason=routing_res.decision_reason,
                    generated_code=current_code,
                    algorithm_explanation=gen_res.explanation,
                    complexity_estimate=attempt_dict["complexity_estimate"],
                    execution_status=exec_res.status,
                    passed_tests=exec_res.passed_count,
                    total_tests=exec_res.total_count,
                    compiler_output=exec_res.compilation_output,
                    runtime_stdout=exec_res.runtime_stdout,
                    runtime_stderr=exec_res.runtime_stderr,
                    error_message=exec_res.error_message,
                    failed_cases_json=attempt_dict["failed_cases"],
                    prompt_tokens=gen_res.prompt_tokens,
                    completion_tokens=gen_res.completion_tokens,
                    total_tokens=gen_res.total_tokens,
                    cost_usd=gen_res.cost_usd,
                    latency_ms=attempt_dict["latency_ms"],
                )
                session.add(attempt_db)
                await session.commit()

            trace_stages.append({
                "stage": f"attempt_{attempt_num}_verification",
                "status": exec_res.status,
                "passed_tests": f"{exec_res.passed_count}/{exec_res.total_count}",
                "latency_ms": attempt_dict["latency_ms"],
                "cost_usd": gen_res.cost_usd,
            })

            # Check if accepted
            if attempt_passed:
                final_status = "accepted"
                final_solution_code = current_code
                trace_stages.append({
                    "stage": "solution_verified",
                    "status": "accepted",
                    "details": f"Solution verified! Passed all {exec_res.total_count} test cases on attempt {attempt_num} using {routing_res.selected_model}.",
                })
                break
            else:
                # Failure analysis & prepare escalation feedback
                if exec_res.status == "compilation_error":
                    failure_feedback = f"Compilation Error:\n{exec_res.compilation_output}"
                elif exec_res.status == "time_limit_exceeded":
                    failure_feedback = "Time Limit Exceeded: The solution timed out (>3.0s). Algorithmic optimization required."
                elif exec_res.status == "runtime_error":
                    failure_feedback = f"Runtime Error:\n{exec_res.runtime_stderr or exec_res.error_message}"
                else:
                    first_fail = next((r for r in exec_res.results if not r.passed), None)
                    if first_fail:
                        failure_feedback = (
                            f"Wrong Answer on Test Case #{first_fail.test_case_index}:\n"
                            f"Input: {first_fail.input_data}\n"
                            f"Expected: {first_fail.expected_output}\n"
                            f"Actual: {first_fail.actual_output}"
                        )
                    else:
                        failure_feedback = "Wrong Answer on test cases."

                # Exclude failed model to ensure escalation to a stronger/different model
                excluded_models.append(routing_res.selected_model)
                trace_stages.append({
                    "stage": f"attempt_{attempt_num}_escalation_decision",
                    "status": "escalating",
                    "diagnostics": failure_feedback,
                    "action": f"Failed model '{routing_res.selected_model}' excluded. Escalating to next best candidate with failure diagnostics.",
                })

        # Update final submission record in database
        async with AsyncSessionLocal() as session:
            stmt = select(CodingSubmission).where(CodingSubmission.id == submission_id)
            res = await session.execute(stmt)
            sub_rec = res.scalar_one()

            sub_rec.status = final_status
            sub_rec.final_solution_code = final_solution_code or current_code
            sub_rec.initial_model = initial_model
            sub_rec.final_model = attempts_data[-1]["model_id"] if attempts_data else None
            sub_rec.total_attempts = len(attempts_data)
            sub_rec.passed_test_cases = attempts_data[-1]["passed_tests"] if attempts_data else 0
            sub_rec.total_test_cases = len(test_cases)
            sub_rec.total_cost_usd = round(total_cost, 6)
            sub_rec.total_latency_ms = total_latency
            sub_rec.trace_json = {"stages": trace_stages}
            await session.commit()

        return {
            "submission_id": str(submission_id),
            "status": final_status,
            "final_solution_code": final_solution_code or current_code,
            "initial_model": initial_model,
            "final_model": attempts_data[-1]["model_id"] if attempts_data else None,
            "total_attempts": len(attempts_data),
            "passed_test_cases": attempts_data[-1]["passed_tests"] if attempts_data else 0,
            "total_test_cases": len(test_cases),
            "total_cost_usd": round(total_cost, 6),
            "total_latency_ms": total_latency,
            "attempts": attempts_data,
            "trace": trace_stages,
            "analysis": analysis.model_dump(),
        }


verification_engine = VerificationEngine()
