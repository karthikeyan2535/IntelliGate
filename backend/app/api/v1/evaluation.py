"""
Evaluation and Benchmark APIs for IntelliGate.
Exposes empirical model performance profiles, evaluation suite runners,
and prompt classification inspection.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel
import structlog
from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.auth import get_current_user
from app.database.models import User
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
async def get_performance_profiles(
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
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
async def list_benchmark_items(
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
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
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Executes benchmark evaluation on the specified model, evaluates deterministic criteria,
    and updates the active routing performance profile in real time.
    """
    model_id = request.model_id or "gpt-4o-mini"
    try:
        result: EvaluationRunResult = await BenchmarkEvaluator.evaluate_model(
            model_id=model_id,
            provider_name=request.provider,
            max_items=request.max_items,
        )
        return {
            "status": "success",
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


@router.post("/classify", summary="Test prompt classification and complexity scoring")
async def classify_prompt(
    request: ClassifyRequest,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Simulates the Task Classifier and Complexity Estimator for any prompt.
    """
    res = TaskClassifier.classify(request.prompt)
    return {
        "category": res.category.value,
        "complexity": res.complexity.value,
        "signals": res.signals,
        "prompt_length": len(request.prompt),
    }

