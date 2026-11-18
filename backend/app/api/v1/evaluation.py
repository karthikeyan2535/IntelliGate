"""
Evaluation and Benchmark APIs for IntelliGate.
Exposes empirical model performance profiles, evaluation suite runners,
historical benchmark runs, and prompt classification inspection.
"""
from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import get_db
from app.database.models import EvaluationRecord
from app.evaluation.dataset import BENCHMARK_DATASET
from app.evaluation.evaluator import BenchmarkEvaluator, EvaluationRunResult
from app.evaluation.profiles import ModelPerformanceProfile, ProfileManager
from app.routing.classifier import TaskClassifier

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/evaluation", tags=["Model Evaluation & Benchmarking"])


class ClassifyRequest(BaseModel):
    prompt: str


class EvaluationRunRequest(BaseModel):
    model_id: Optional[str] = "gpt-4o-mini"
    provider: Optional[str] = None
    max_items: Optional[int] = 12


@router.get("/profiles", summary="Get empirical model performance profiles")
async def get_performance_profiles() -> List[Dict[str, Any]]:
    """
    Returns active performance profiles across models, including
    category benchmark scores, latency, reliability, and pricing.
    """
    profiles = ProfileManager.get_all()
    return [
        {
            "model_id": p.model_id,
            "provider": p.provider,
            "display_name": p.display_name,
            "context_window": p.context_window,
            "input_cost_per_1k": float(p.input_cost_per_1k),
            "output_cost_per_1k": float(p.output_cost_per_1k),
            "coding_quality": p.coding_quality,
            "reasoning_quality": p.reasoning_quality,
            "writing_quality": p.writing_quality,
            "general_qa_quality": p.general_qa_quality,
            "avg_latency_ms": p.avg_latency_ms,
            "reliability": p.reliability,
            "supported_categories": p.supported_categories,
            "description": p.description,
        }
        for p in profiles
    ]


@router.get("/benchmark-items", summary="List curated benchmark dataset items")
async def list_benchmark_items() -> List[Dict[str, Any]]:
    """
    Returns the benchmark dataset used for empirical calibration.
    """
    return [
        {
            "id": item.id,
            "category": item.category,
            "complexity": item.complexity,
            "prompt": item.prompt,
            "validator_type": item.validator_type,
            "expected_contains": item.expected_contains,
        }
        for item in BENCHMARK_DATASET
    ]


@router.post("/run", summary="Trigger benchmark evaluation suite")
async def run_benchmark_evaluation(
    request: EvaluationRunRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Executes benchmark evaluation on the specified model, evaluates deterministic criteria,
    updates the active routing performance profile in real time, and persists the run to the database.
    """
    model_id = request.model_id or "gpt-4o-mini"
    try:
        result: EvaluationRunResult = await BenchmarkEvaluator.evaluate_model(
            model_id=model_id,
            provider_name=request.provider,
            max_items=request.max_items,
        )

        # Persist to database if table exists
        rec_id = None
        try:
            record = EvaluationRecord(
                model_id=result.model_id,
                provider_name=result.provider,
                total_prompts=result.total_prompts,
                passed_prompts=result.passed_prompts,
                overall_quality_score=result.overall_quality_score,
                category_scores=result.category_scores,
                avg_latency_ms=result.avg_latency_ms,
                total_tokens_used=result.total_tokens_used,
                duration_seconds=result.duration_seconds,
                item_details=result.item_details,
            )
            db.add(record)
            await db.commit()
            await db.refresh(record)
            rec_id = str(record.id)
        except Exception as db_err:
            logger.warning("Could not persist evaluation record to DB", error=str(db_err))

        return {
            "status": "success",
            "run_id": rec_id,
            "model_id": result.model_id,
            "provider": result.provider,
            "total_prompts": result.total_prompts,
            "passed_prompts": result.passed_prompts,
            "overall_quality_score": result.overall_quality_score,
            "category_scores": result.category_scores,
            "avg_latency_ms": result.avg_latency_ms,
            "total_tokens_used": result.total_tokens_used,
            "duration_seconds": result.duration_seconds,
            "item_details": result.item_details,
        }
    except Exception as exc:
        logger.error("Benchmark evaluation run failed", model=model_id, error=str(exc))
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(exc)}")


@router.get("/runs", summary="List historical benchmark evaluation runs")
async def list_evaluation_runs(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    Returns historical benchmark execution runs from the database.
    """
    try:
        stmt = select(EvaluationRecord).order_by(EvaluationRecord.created_at.desc()).limit(limit)
        res = await db.execute(stmt)
        records = res.scalars().all()
        if records:
            return [
                {
                    "id": str(r.id),
                    "model_id": r.model_id,
                    "provider_name": r.provider_name,
                    "total_prompts": r.total_prompts,
                    "passed_prompts": r.passed_prompts,
                    "overall_quality_score": r.overall_quality_score,
                    "category_scores": r.category_scores or {},
                    "avg_latency_ms": r.avg_latency_ms,
                    "total_tokens_used": r.total_tokens_used,
                    "duration_seconds": r.duration_seconds,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in records
            ]
    except Exception:
        pass
    return []


@router.get("/runs/{run_id}", summary="Get detailed evaluation run inspection")
async def get_evaluation_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Returns itemized prompt evaluation details for an evaluation run.
    """
    try:
        u_id = uuid.UUID(run_id)
        stmt = select(EvaluationRecord).where(EvaluationRecord.id == u_id)
        res = await db.execute(stmt)
        record = res.scalar_one_or_none()
        if record:
            return {
                "id": str(record.id),
                "model_id": record.model_id,
                "provider_name": record.provider_name,
                "total_prompts": record.total_prompts,
                "passed_prompts": record.passed_prompts,
                "overall_quality_score": record.overall_quality_score,
                "category_scores": record.category_scores or {},
                "avg_latency_ms": record.avg_latency_ms,
                "total_tokens_used": record.total_tokens_used,
                "duration_seconds": record.duration_seconds,
                "item_details": record.item_details or [],
                "created_at": record.created_at.isoformat() if record.created_at else None,
            }
    except Exception:
        pass
    raise HTTPException(status_code=404, detail="Evaluation run not found")


@router.post("/classify", summary="Test prompt classification and complexity scoring")
async def classify_prompt(
    request: ClassifyRequest,
) -> Dict[str, Any]:
    """
    Simulates the Task Classifier and Complexity Estimator for any prompt.
    """
    res = TaskClassifier.classify(request.prompt)
    return {
        "category": res.category.value,
        "complexity": res.complexity.value,
        "signals": res.signals,
        "confidence": res.confidence,
        "prompt_length": len(request.prompt),
    }


