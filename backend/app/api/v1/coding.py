"""
Coding-Specific API Endpoints for IntelliGate:
- Problems: Import from URL, Manual Creation, List & Get Problem
- Submissions: Submit Problem, Run Pipeline, Inspect Trace & Attempts
- Models: Empirical Capability Profiles & Baselines Reset
- Benchmarks: Run Benchmarks, Historical Runs, Baseline Comparison
- Analytics: Overview & Cost-Per-Verified-Solution Metrics
"""
from __future__ import annotations

import uuid
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func, desc

from app.database.base import AsyncSessionLocal
from app.database.coding_models import (
    CodingProblem, CodingTestCase, CodingSubmission, CodingAttempt,
    CodingBenchmarkRun, CodingModelProfile
)
from app.ingestion.importer import problem_importer
from app.analysis.coding_analyzer import coding_analyzer
from app.analysis.model_profiles import coding_profile_manager
from app.verification.engine import verification_engine
from app.benchmark.runner import coding_benchmark_runner


router = APIRouter(prefix="/coding", tags=["Coding Router"])


# ── Pydantic Request & Response Schemas ────────────────────────────────────────


class ImportProblemRequest(BaseModel):
    url: str = Field(..., description="Supported Codeforces or LeetCode problem URL")


class ManualTestCase(BaseModel):
    input: str
    expected: str
    is_sample: bool = True


class CreateProblemRequest(BaseModel):
    title: str
    statement: str
    constraints: Optional[str] = None
    input_format: Optional[str] = None
    output_format: Optional[str] = None
    algorithm_category: Optional[str] = "other"
    difficulty: Optional[str] = "medium"
    test_cases: List[ManualTestCase] = Field(default_factory=list)


class SubmitProblemRequest(BaseModel):
    problem_id: Optional[str] = None
    title: str = "Custom Problem"
    statement: str
    test_cases: List[ManualTestCase]
    language: str = "python"  # python, cpp, java
    routing_mode: str = "intelligent"  # intelligent, lowest_cost, direct, baseline_*
    target_model: Optional[str] = None
    max_attempts: int = 3
    cost_budget_usd: Optional[float] = 0.05
    latency_budget_ms: Optional[int] = 30000
    constraints: Optional[str] = ""
    input_format: Optional[str] = ""
    output_format: Optional[str] = ""


class BenchmarkRunRequest(BaseModel):
    strategy_or_model: str = "intelligent"
    split: str = "calibration"  # calibration or test
    max_problems: int = 15
    category: Optional[str] = "all"
    language: str = "python"


# ── Problem Ingestion Endpoints ───────────────────────────────────────────────


@router.post("/problems/import", summary="Import a problem from Codeforces or LeetCode")
async def import_problem(req: ImportProblemRequest) -> Dict[str, Any]:
    try:
        data = await problem_importer.import_from_url(req.url)
        # Analyze category and difficulty automatically
        analysis = coding_analyzer.analyze(data.title, data.statement, data.constraints)

        # Store in database
        async with AsyncSessionLocal() as session:
            prob = CodingProblem(
                title=data.title,
                source=data.source,
                source_url=data.source_url,
                statement=data.statement,
                constraints=data.constraints,
                input_format=data.input_format,
                output_format=data.output_format,
                algorithm_category=analysis.algorithm_family,
                difficulty=data.estimated_difficulty or analysis.difficulty,
                time_limit_ms=data.time_limit_ms,
                memory_limit_mb=data.memory_limit_mb,
                metadata_json={"analysis": analysis.model_dump()},
            )
            session.add(prob)
            await session.commit()
            await session.refresh(prob)

            # Store test cases
            for tc in data.sample_test_cases:
                t_obj = CodingTestCase(
                    problem_id=prob.id,
                    input_data=tc.get("input", ""),
                    expected_output=tc.get("expected", ""),
                    is_sample=True,
                )
                session.add(t_obj)
            await session.commit()

            return {
                "problem_id": str(prob.id),
                "title": data.title,
                "statement": data.statement,
                "constraints": data.constraints,
                "input_format": data.input_format,
                "output_format": data.output_format,
                "algorithm_category": analysis.algorithm_family,
                "difficulty": prob.difficulty,
                "sample_test_cases": data.sample_test_cases,
                "source": data.source,
                "source_url": data.source_url,
                "is_leetcode_style": data.is_leetcode_style,
                "function_signature": data.function_signature,
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/problems", summary="Manually create a coding problem")
async def create_problem(req: CreateProblemRequest) -> Dict[str, Any]:
    analysis = coding_analyzer.analyze(req.title, req.statement, req.constraints)
    cat = req.algorithm_category if req.algorithm_category != "other" else analysis.algorithm_family

    async with AsyncSessionLocal() as session:
        prob = CodingProblem(
            title=req.title,
            source="manual",
            statement=req.statement,
            constraints=req.constraints,
            input_format=req.input_format,
            output_format=req.output_format,
            algorithm_category=cat,
            difficulty=req.difficulty or analysis.difficulty,
            metadata_json={"analysis": analysis.model_dump()},
        )
        session.add(prob)
        await session.commit()
        await session.refresh(prob)

        for tc in req.test_cases:
            t_obj = CodingTestCase(
                problem_id=prob.id,
                input_data=tc.input,
                expected_output=tc.expected,
                is_sample=tc.is_sample,
            )
            session.add(t_obj)
        await session.commit()

        return {
            "problem_id": str(prob.id),
            "title": prob.title,
            "algorithm_category": prob.algorithm_category,
            "difficulty": prob.difficulty,
            "analysis": analysis.model_dump(),
        }


@router.get("/problems", summary="List coding problems")
async def list_problems(
    limit: int = 50,
    category: Optional[str] = None,
    is_benchmark: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    async with AsyncSessionLocal() as session:
        stmt = select(CodingProblem).order_by(desc(CodingProblem.created_at)).limit(limit)
        if category and category != "all":
            stmt = stmt.where(CodingProblem.algorithm_category == category)
        if is_benchmark is not None:
            stmt = stmt.where(CodingProblem.is_benchmark == is_benchmark)

        res = await session.execute(stmt)
        problems = res.scalars().all()

        out = []
        for p in problems:
            out.append({
                "id": str(p.id),
                "title": p.title,
                "source": p.source,
                "algorithm_category": p.algorithm_category,
                "difficulty": p.difficulty,
                "is_benchmark": p.is_benchmark,
                "benchmark_split": p.benchmark_split,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            })
        return out


@router.get("/problems/{problem_id}", summary="Get problem details and test cases")
async def get_problem(problem_id: str) -> Dict[str, Any]:
    try:
        p_uuid = uuid.UUID(problem_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid problem UUID format")

    async with AsyncSessionLocal() as session:
        stmt = select(CodingProblem).where(CodingProblem.id == p_uuid)
        res = await session.execute(stmt)
        p = res.scalar_one_or_none()
        if not p:
            raise HTTPException(status_code=404, detail="Problem not found")

        # Get test cases
        tc_stmt = select(CodingTestCase).where(CodingTestCase.problem_id == p_uuid)
        tc_res = await session.execute(tc_stmt)
        tcs = tc_res.scalars().all()

        return {
            "id": str(p.id),
            "title": p.title,
            "source": p.source,
            "source_url": p.source_url,
            "statement": p.statement,
            "constraints": p.constraints,
            "input_format": p.input_format,
            "output_format": p.output_format,
            "algorithm_category": p.algorithm_category,
            "difficulty": p.difficulty,
            "time_limit_ms": p.time_limit_ms,
            "memory_limit_mb": p.memory_limit_mb,
            "test_cases": [
                {"input": tc.input_data, "expected": tc.expected_output, "is_sample": tc.is_sample}
                for tc in tcs
            ],
        }


# ── Submission & Execution Pipeline Endpoints ─────────────────────────────────


@router.post("/submissions", summary="Submit a problem to IntelliGate routing pipeline")
async def submit_problem(req: SubmitProblemRequest) -> Dict[str, Any]:
    try:
        test_case_dicts = [{"input": tc.input, "expected": tc.expected} for tc in req.test_cases]
        if not test_case_dicts:
            raise HTTPException(status_code=400, detail="At least one test case is required.")

        result = await verification_engine.execute_problem(
            problem_id=req.problem_id,
            title=req.title,
            statement=req.statement,
            test_cases=test_case_dicts,
            language=req.language,
            routing_mode=req.routing_mode,
            target_model=req.target_model,
            max_attempts=req.max_attempts,
            cost_budget_usd=req.cost_budget_usd,
            latency_budget_ms=req.latency_budget_ms,
            constraints=req.constraints,
            input_format=req.input_format,
            output_format=req.output_format,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/submissions", summary="List historical submissions")
async def list_submissions(limit: int = 50) -> List[Dict[str, Any]]:
    async with AsyncSessionLocal() as session:
        stmt = (
            select(CodingSubmission)
            .order_by(desc(CodingSubmission.created_at))
            .limit(limit)
        )
        res = await session.execute(stmt)
        subs = res.scalars().all()

        out = []
        for s in subs:
            out.append({
                "id": str(s.id),
                "problem_id": str(s.problem_id) if s.problem_id else None,
                "language": s.language,
                "routing_mode": s.routing_mode,
                "status": s.status,
                "initial_model": s.initial_model,
                "final_model": s.final_model,
                "total_attempts": s.total_attempts,
                "passed_test_cases": s.passed_test_cases,
                "total_test_cases": s.total_test_cases,
                "total_cost_usd": s.total_cost_usd,
                "total_latency_ms": s.total_latency_ms,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            })
        return out


@router.get("/submissions/{submission_id}", summary="Get submission details, trace, and attempts")
async def get_submission(submission_id: str) -> Dict[str, Any]:
    try:
        s_uuid = uuid.UUID(submission_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid submission UUID format")

    async with AsyncSessionLocal() as session:
        stmt = select(CodingSubmission).where(CodingSubmission.id == s_uuid)
        res = await session.execute(stmt)
        s = res.scalar_one_or_none()
        if not s:
            raise HTTPException(status_code=404, detail="Submission not found")

        # Get attempts
        att_stmt = (
            select(CodingAttempt)
            .where(CodingAttempt.submission_id == s_uuid)
            .order_by(CodingAttempt.attempt_number)
        )
        att_res = await session.execute(att_stmt)
        attempts = att_res.scalars().all()

        return {
            "id": str(s.id),
            "problem_id": str(s.problem_id) if s.problem_id else None,
            "language": s.language,
            "routing_mode": s.routing_mode,
            "status": s.status,
            "final_solution_code": s.final_solution_code,
            "initial_model": s.initial_model,
            "final_model": s.final_model,
            "total_attempts": s.total_attempts,
            "passed_test_cases": s.passed_test_cases,
            "total_test_cases": s.total_test_cases,
            "total_cost_usd": s.total_cost_usd,
            "total_latency_ms": s.total_latency_ms,
            "trace": s.trace_json.get("stages", []) if s.trace_json else [],
            "attempts": [
                {
                    "attempt_number": a.attempt_number,
                    "model_id": a.model_id,
                    "provider_name": a.provider_name,
                    "routing_reason": a.routing_reason,
                    "generated_code": a.generated_code,
                    "algorithm_explanation": a.algorithm_explanation,
                    "complexity_estimate": a.complexity_estimate,
                    "execution_status": a.execution_status,
                    "passed_tests": a.passed_tests,
                    "total_tests": a.total_tests,
                    "compiler_output": a.compiler_output,
                    "runtime_stdout": a.runtime_stdout,
                    "runtime_stderr": a.runtime_stderr,
                    "error_message": a.error_message,
                    "failed_cases": a.failed_cases_json or [],
                    "cost_usd": a.cost_usd,
                    "latency_ms": a.latency_ms,
                }
                for a in attempts
            ],
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }


# ── Model Capability Profiles Endpoints ───────────────────────────────────────


@router.get("/models/performance", summary="List empirical coding profiles for all models")
async def list_model_profiles() -> List[Dict[str, Any]]:
    return await coding_profile_manager.get_all_profiles()


@router.post("/models/performance/reset", summary="Reset model profiles to calibrated baselines")
async def reset_model_profiles() -> Dict[str, str]:
    await coding_profile_manager.reset_baselines()
    return {"status": "ok", "message": "Calibrated empirical coding profiles restored successfully."}


# ── Benchmark Evaluation Endpoints ───────────────────────────────────────────


@router.post("/benchmarks/run", summary="Run a benchmark suite")
async def run_benchmark(req: BenchmarkRunRequest) -> Dict[str, Any]:
    try:
        res = await coding_benchmark_runner.run_benchmark_suite(
            strategy_or_model=req.strategy_or_model,
            split=req.split,
            max_problems=req.max_problems,
            category=req.category,
            language=req.language,
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/benchmarks/history", summary="List historical benchmark evaluation runs")
async def list_benchmark_runs(limit: int = 20) -> List[Dict[str, Any]]:
    async with AsyncSessionLocal() as session:
        stmt = (
            select(CodingBenchmarkRun)
            .order_by(desc(CodingBenchmarkRun.created_at))
            .limit(limit)
        )
        res = await session.execute(stmt)
        runs = res.scalars().all()

        return [
            {
                "id": str(r.id),
                "suite": r.benchmark_suite,
                "strategy": r.routing_strategy,
                "model_id": r.model_id,
                "split": r.split,
                "status": r.status,
                "total_problems": r.total_problems,
                "passed_problems": r.passed_problems,
                "pass_rate": round(r.pass_rate * 100, 1),
                "first_attempt_pass_rate": round(r.first_attempt_pass_rate * 100, 1),
                "total_cost_usd": r.total_cost_usd,
                "cost_per_verified_solution": r.cost_per_verified_solution,
                "avg_latency_ms": r.avg_latency_ms,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in runs
        ]


@router.get("/benchmarks/compare", summary="Compare 4 routing strategies on held-out evaluation")
async def compare_routing_strategies() -> List[Dict[str, Any]]:
    return await coding_benchmark_runner.get_baseline_comparison()


# ── High-Level Analytics & Cost Accounting ────────────────────────────────────


@router.get("/analytics/overview", summary="Get coding-specific system analytics")
async def get_coding_analytics() -> Dict[str, Any]:
    async with AsyncSessionLocal() as session:
        # Total submissions
        total_sub_res = await session.execute(select(func.count(CodingSubmission.id)))
        total_submissions = total_sub_res.scalar_one()

        # Accepted submissions
        accepted_res = await session.execute(
            select(func.count(CodingSubmission.id)).where(CodingSubmission.status == "accepted")
        )
        accepted_submissions = accepted_res.scalar_one()

        # First attempt accepted
        first_pass_res = await session.execute(
            select(func.count(CodingSubmission.id)).where(
                CodingSubmission.status == "accepted",
                CodingSubmission.total_attempts == 1,
            )
        )
        first_attempt_accepted = first_pass_res.scalar_one()

        # Total spend
        cost_res = await session.execute(select(func.sum(CodingSubmission.total_cost_usd)))
        total_cost = cost_res.scalar_one() or 0.0

        # Avg latency
        lat_res = await session.execute(select(func.avg(CodingSubmission.total_latency_ms)))
        avg_latency = lat_res.scalar_one() or 0.0

        # Benchmark count
        bm_res = await session.execute(select(func.count(CodingBenchmarkRun.id)))
        benchmark_runs_count = bm_res.scalar_one()

        # Model usage breakdown
        model_stmt = (
            select(CodingAttempt.model_id, func.count(CodingAttempt.id))
            .group_by(CodingAttempt.model_id)
        )
        model_res = await session.execute(model_stmt)
        model_breakdown = [{"model": row[0], "attempts": row[1]} for row in model_res.all()]

        final_pass_rate = (accepted_submissions / total_submissions * 100) if total_submissions > 0 else 0.0
        first_pass_rate = (first_attempt_accepted / total_submissions * 100) if total_submissions > 0 else 0.0
        cost_per_verified = (total_cost / accepted_submissions) if accepted_submissions > 0 else 0.0

        return {
            "total_problems_processed": total_submissions,
            "verified_solutions": accepted_submissions,
            "final_pass_rate": round(final_pass_rate, 1),
            "first_attempt_pass_rate": round(first_pass_rate, 1),
            "total_spend_usd": round(total_cost, 5),
            "cost_per_verified_solution": round(cost_per_verified, 5),
            "avg_latency_ms": round(avg_latency, 1),
            "benchmark_runs_count": benchmark_runs_count,
            "model_usage": model_breakdown,
        }

