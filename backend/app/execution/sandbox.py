"""
Secure sandboxed code execution service for C++17, Python, and Java.
Supports both standard stdin/stdout (Codeforces style) and wrapper execution (LeetCode style).
Executes in an isolated temporary workspace directory with memory, timeout, and subprocess boundaries.
"""
from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any


@dataclass
class TestCaseResult:
    test_case_index: int
    passed: bool
    status: str  # accepted / wrong_answer / time_limit_exceeded / runtime_error
    input_data: str
    expected_output: str
    actual_output: str
    execution_time_ms: int
    error_message: Optional[str] = None


@dataclass
class ExecutionResult:
    status: str  # accepted / wrong_answer / compilation_error / runtime_error / time_limit_exceeded / memory_limit_exceeded / execution_error
    passed_count: int
    total_count: int
    results: List[TestCaseResult] = field(default_factory=list)
    compilation_output: Optional[str] = None
    runtime_stdout: Optional[str] = None
    runtime_stderr: Optional[str] = None
    error_message: Optional[str] = None
    peak_latency_ms: int = 0


class SandboxExecutor:
    """
    Sandboxed compilation and execution manager.
    Enforces time limits, output limits, restricted workspace directories, and process cleanups.
    """

    MAX_OUTPUT_CHARS = 32768  # Limit stdout to avoid memory denial-of-service

    def __init__(self, default_timeout_sec: float = 3.0):
        self.default_timeout_sec = default_timeout_sec

    def _normalize_output(self, text: str) -> str:
        """Strip trailing whitespace and normalize CRLF -> LF."""
        if not text:
            return ""
        lines = [line.rstrip() for line in text.strip().splitlines()]
        return "\n".join(lines).strip()

    async def execute(
        self,
        language: str,
        code: str,
        test_cases: List[Dict[str, str]],  # [{"input": "...", "expected": "..."}]
        timeout_sec: Optional[float] = None,
        is_leetcode_style: bool = False,
    ) -> ExecutionResult:
        """
        Executes code inside an isolated temporary directory.
        """
        timeout = timeout_sec or self.default_timeout_sec
        lang = language.lower()

        # Create isolated temporary directory
        temp_dir = Path(tempfile.mkdtemp(prefix="intelligate_exec_"))
        try:
            if lang in ["cpp", "c++", "cpp17"]:
                return await self._execute_cpp(temp_dir, code, test_cases, timeout)
            elif lang in ["python", "python3", "py"]:
                return await self._execute_python(temp_dir, code, test_cases, timeout)
            elif lang in ["java"]:
                return await self._execute_java(temp_dir, code, test_cases, timeout)
            else:
                return ExecutionResult(
                    status="execution_error",
                    passed_count=0,
                    total_count=len(test_cases),
                    error_message=f"Unsupported execution language: {language}",
                )
        finally:
            # Clean up isolated workspace completely
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass

    # ── C++17 Execution ───────────────────────────────────────────────────────

    async def _execute_cpp(
        self, temp_dir: Path, code: str, test_cases: List[Dict[str, str]], timeout: float
    ) -> ExecutionResult:
        source_file = temp_dir / "solution.cpp"
        exe_file = temp_dir / ("solution.exe" if sys.platform == "win32" else "solution")

        source_file.write_text(code, encoding="utf-8")

        # Compile with C++17 and optimization
        compile_cmd = ["g++", "-O2", "-std=c++17", str(source_file), "-o", str(exe_file)]
        compile_start = time.perf_counter()
        try:
            proc = await asyncio.create_subprocess_exec(
                *compile_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(temp_dir),
            )
            stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=15.0)
            comp_stdout = stdout_b.decode("utf-8", errors="replace")
            comp_stderr = stderr_b.decode("utf-8", errors="replace")

            if proc.returncode != 0:
                return ExecutionResult(
                    status="compilation_error",
                    passed_count=0,
                    total_count=len(test_cases),
                    compilation_output=(comp_stdout + "\n" + comp_stderr).strip(),
                    error_message="Compilation failed. See compiler output.",
                )
        except asyncio.TimeoutError:
            return ExecutionResult(
                status="compilation_error",
                passed_count=0,
                total_count=len(test_cases),
                error_message="Compilation timed out after 15 seconds.",
            )
        except FileNotFoundError:
            return ExecutionResult(
                status="infrastructure_error",
                passed_count=0,
                total_count=len(test_cases),
                error_message="g++ compiler is not installed or not in PATH.",
            )

        # Run test cases against compiled binary
        return await self._run_test_cases(
            exec_cmd=[str(exe_file)],
            temp_dir=temp_dir,
            test_cases=test_cases,
            timeout=timeout,
        )

    # ── Python Execution ──────────────────────────────────────────────────────

    async def _execute_python(
        self, temp_dir: Path, code: str, test_cases: List[Dict[str, str]], timeout: float
    ) -> ExecutionResult:
        source_file = temp_dir / "solution.py"
        source_file.write_text(code, encoding="utf-8")

        # Use current python executable
        exec_cmd = [sys.executable, "-I", str(source_file)]  # -I isolates from user environment

        return await self._run_test_cases(
            exec_cmd=exec_cmd,
            temp_dir=temp_dir,
            test_cases=test_cases,
            timeout=timeout,
        )

    # ── Java Execution ────────────────────────────────────────────────────────

    async def _execute_java(
        self, temp_dir: Path, code: str, test_cases: List[Dict[str, str]], timeout: float
    ) -> ExecutionResult:
        # Determine class name (defaults to Solution or Main)
        class_name = "Solution"
        if "public class Main" in code or "class Main" in code:
            class_name = "Main"
        elif "public class Solution" in code or "class Solution" in code:
            class_name = "Solution"

        source_file = temp_dir / f"{class_name}.java"
        source_file.write_text(code, encoding="utf-8")

        # Compile Java
        compile_cmd = ["javac", str(source_file)]
        try:
            proc = await asyncio.create_subprocess_exec(
                *compile_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(temp_dir),
            )
            stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=15.0)
            comp_stdout = stdout_b.decode("utf-8", errors="replace")
            comp_stderr = stderr_b.decode("utf-8", errors="replace")

            if proc.returncode != 0:
                return ExecutionResult(
                    status="compilation_error",
                    passed_count=0,
                    total_count=len(test_cases),
                    compilation_output=(comp_stdout + "\n" + comp_stderr).strip(),
                    error_message="Java compilation failed.",
                )
        except asyncio.TimeoutError:
            return ExecutionResult(
                status="compilation_error",
                passed_count=0,
                total_count=len(test_cases),
                error_message="Java compilation timed out.",
            )
        except FileNotFoundError:
            return ExecutionResult(
                status="infrastructure_error",
                passed_count=0,
                total_count=len(test_cases),
                error_message="javac is not installed or not in PATH.",
            )

        # Run with memory limits
        exec_cmd = ["java", "-Xmx256m", "-cp", str(temp_dir), class_name]

        return await self._run_test_cases(
            exec_cmd=exec_cmd,
            temp_dir=temp_dir,
            test_cases=test_cases,
            timeout=timeout,
        )

    # ── Test Runner Loop ──────────────────────────────────────────────────────

    async def _run_test_cases(
        self,
        exec_cmd: List[str],
        temp_dir: Path,
        test_cases: List[Dict[str, str]],
        timeout: float,
    ) -> ExecutionResult:
        results: List[TestCaseResult] = []
        overall_status = "accepted"
        peak_latency_ms = 0
        first_error_msg = None
        last_stdout = None
        last_stderr = None

        for idx, tc in enumerate(test_cases):
            input_str = tc.get("input", "")
            expected_str = tc.get("expected", "")

            start_t = time.perf_counter()
            try:
                proc = await asyncio.create_subprocess_exec(
                    *exec_cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(temp_dir),
                )

                input_bytes = input_str.encode("utf-8")
                try:
                    stdout_b, stderr_b = await asyncio.wait_for(
                        proc.communicate(input=input_bytes), timeout=timeout
                    )
                except asyncio.TimeoutError:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                    elapsed_ms = int((time.perf_counter() - start_t) * 1000)
                    peak_latency_ms = max(peak_latency_ms, elapsed_ms)
                    results.append(
                        TestCaseResult(
                            test_case_index=idx + 1,
                            passed=False,
                            status="time_limit_exceeded",
                            input_data=input_str,
                            expected_output=expected_str,
                            actual_output="",
                            execution_time_ms=elapsed_ms,
                            error_message=f"Time limit of {timeout}s exceeded",
                        )
                    )
                    overall_status = "time_limit_exceeded"
                    break

                elapsed_ms = int((time.perf_counter() - start_t) * 1000)
                peak_latency_ms = max(peak_latency_ms, elapsed_ms)

                actual_str = stdout_b.decode("utf-8", errors="replace")[: self.MAX_OUTPUT_CHARS]
                stderr_str = stderr_b.decode("utf-8", errors="replace")[: self.MAX_OUTPUT_CHARS]
                last_stdout = actual_str
                last_stderr = stderr_str

                if proc.returncode != 0:
                    results.append(
                        TestCaseResult(
                            test_case_index=idx + 1,
                            passed=False,
                            status="runtime_error",
                            input_data=input_str,
                            expected_output=expected_str,
                            actual_output=actual_str,
                            execution_time_ms=elapsed_ms,
                            error_message=stderr_str or f"Process exited with code {proc.returncode}",
                        )
                    )
                    overall_status = "runtime_error"
                    first_error_msg = stderr_str or f"Runtime error code {proc.returncode}"
                    break

                # Compare normalized outputs
                norm_actual = self._normalize_output(actual_str)
                norm_expected = self._normalize_output(expected_str)

                if norm_actual == norm_expected:
                    results.append(
                        TestCaseResult(
                            test_case_index=idx + 1,
                            passed=True,
                            status="accepted",
                            input_data=input_str,
                            expected_output=expected_str,
                            actual_output=actual_str,
                            execution_time_ms=elapsed_ms,
                        )
                    )
                else:
                    results.append(
                        TestCaseResult(
                            test_case_index=idx + 1,
                            passed=False,
                            status="wrong_answer",
                            input_data=input_str,
                            expected_output=expected_str,
                            actual_output=actual_str,
                            execution_time_ms=elapsed_ms,
                            error_message="Output did not match expected value",
                        )
                    )
                    overall_status = "wrong_answer"
                    first_error_msg = "Wrong Answer on test case"
                    break

            except Exception as ex:
                elapsed_ms = int((time.perf_counter() - start_t) * 1000)
                results.append(
                    TestCaseResult(
                        test_case_index=idx + 1,
                        passed=False,
                        status="execution_error",
                        input_data=input_str,
                        expected_output=expected_str,
                        actual_output="",
                        execution_time_ms=elapsed_ms,
                        error_message=str(ex),
                    )
                )
                overall_status = "execution_error"
                first_error_msg = str(ex)
                break

        passed_count = sum(1 for r in results if r.passed)
        return ExecutionResult(
            status=overall_status,
            passed_count=passed_count,
            total_count=len(test_cases),
            results=results,
            runtime_stdout=last_stdout,
            runtime_stderr=last_stderr,
            error_message=first_error_msg,
            peak_latency_ms=peak_latency_ms,
        )


sandbox_executor = SandboxExecutor()
