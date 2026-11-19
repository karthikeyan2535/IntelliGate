"""
Adapters connecting CodeGenerator and SandboxExecutor to the RoutingEngine protocols.
"""
from __future__ import annotations

from typing import Dict, Any, List, Optional
from app.generation.code_generator import code_generator, GenerationResult as InternalGenResult
from app.execution.sandbox import sandbox_executor, ExecutionResult as InternalExecResult
from app.routing.routing_engine import GenerationResult, VerificationResult, CodeGeneratorProtocol, SandboxVerifierProtocol


class AppCodeGeneratorAdapter:
    """
    Implements CodeGeneratorProtocol using IntelliGate's core CodeGenerator service.
    """

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
        res: InternalGenResult = await code_generator.generate(
            model_id=model_id,
            provider_name=provider_name,
            language=language,
            title="Coding Problem",
            statement=problem,
            constraints=constraints,
            sample_cases=sample_cases,
            previous_code=previous_code,
            failure_diagnostics=feedback,
        )
        return GenerationResult(
            code=res.code,
            cost_usd=res.cost_usd,
            latency_ms=res.latency_ms,
            explanation=res.explanation,
            time_complexity=res.time_complexity,
            space_complexity=res.space_complexity,
        )


class AppSandboxVerifierAdapter:
    """
    Implements SandboxVerifierProtocol using IntelliGate's isolated SandboxExecutor.
    """

    async def verify_code(
        self,
        language: str,
        code: str,
        test_cases: List[Dict[str, str]],
        timeout_sec: float = 3.0,
    ) -> VerificationResult:
        res: InternalExecResult = await sandbox_executor.execute(
            language=language,
            code=code,
            test_cases=test_cases,
            timeout_sec=timeout_sec,
        )
        failed_cases = []
        for r in res.results:
            if not r.passed:
                failed_cases.append({
                    "test_case_index": r.test_case_index,
                    "input": r.input_data,
                    "expected": r.expected_output,
                    "actual": r.actual_output,
                    "error": r.error_message,
                })

        return VerificationResult(
            status=res.status,
            passed_tests=res.passed_count,
            total_tests=res.total_count,
            execution_time_ms=res.peak_latency_ms,
            compiler_output=res.compilation_output,
            runtime_stdout=res.runtime_stdout,
            runtime_stderr=res.runtime_stderr,
            error_message=res.error_message,
            failed_cases=failed_cases,
        )


app_code_generator_adapter = AppCodeGeneratorAdapter()
app_sandbox_verifier_adapter = AppSandboxVerifierAdapter()

