"""
Unit tests for the Intelligent Routing Engine, Task Classifier, and Evaluation Profiles.
Verifies multi-objective utility scoring, complexity adaptation, and fallback chains.
"""
import pytest
from app.routing.classifier import ComplexityLevel, TaskCategory, TaskClassifier
from app.routing.engine import RoutingEngine, get_routing_engine
from app.evaluation.profiles import ProfileManager, ModelPerformanceProfile
from decimal import Decimal


def test_classifier_coding_detection():
    prompt = "Write an async Python function using FastAPI to query PostgreSQL using SQLAlchemy 2.0."
    res = TaskClassifier.classify(prompt)
    assert res.category == TaskCategory.CODING
    assert res.complexity in [ComplexityLevel.MODERATE, ComplexityLevel.COMPLEX]
    assert any("code_syntax" in s or "fastapi" in s.lower() for s in res.detected_features)


def test_classifier_reasoning_detection():
    prompt = (
        "Alice has 3 brothers, and each brother has 2 sisters. "
        "How many sisters does Alice have? Provide step-by-step logical proof."
    )
    res = TaskClassifier.classify(prompt)
    assert res.category == TaskCategory.REASONING
    assert res.complexity in [ComplexityLevel.MODERATE, ComplexityLevel.COMPLEX]


def test_classifier_writing_detection():
    prompt = "Draft an engaging newsletter summarizing recent advances in generative AI and agents."
    res = TaskClassifier.classify(prompt)
    assert res.category == TaskCategory.WRITING


def test_classifier_simple_qa_detection():
    prompt = "What is the capital of France?"
    res = TaskClassifier.classify(prompt)
    assert res.category == TaskCategory.GENERAL_QA
    assert res.complexity == ComplexityLevel.SIMPLE


@pytest.mark.asyncio
async def test_intelligent_routing_complex_task():
    engine = RoutingEngine()
    prompt = (
        "Design a distributed consensus protocol with Byzantine Fault Tolerance. "
        "Prove safety and liveness conditions with a formal inductive proof."
    )
    decision = await engine.route(prompt=prompt, routing_mode="intelligent")
    
    assert decision.mode == "intelligent"
    assert decision.complexity == "complex"
    assert decision.selected_model in ["gpt-4o", "llama-3.3-70b-versatile", "gemini-1.5-pro"]
    assert len(decision.fallback_candidates) >= 1
    assert "Intelligent Routing" in decision.reason
    assert len(decision.candidate_scores) > 0
    # Top ranked candidate should match selected_model
    assert decision.candidate_scores[0].model_id == decision.selected_model


@pytest.mark.asyncio
async def test_intelligent_routing_simple_task():
    engine = RoutingEngine()
    prompt = "Hello, what is 2 + 2?"
    decision = await engine.route(prompt=prompt, routing_mode="intelligent")
    
    assert decision.mode == "intelligent"
    assert decision.complexity == "simple"
    # For simple tasks, high speed / low cost models win
    assert decision.selected_model in ["llama-3.1-8b-instant", "gemini-1.5-flash", "gpt-4o-mini"]


@pytest.mark.asyncio
async def test_lowest_cost_routing_mode():
    engine = RoutingEngine()
    prompt = "Explain quantum computing in three sentences."
    decision = await engine.route(prompt=prompt, routing_mode="lowest_cost")
    
    assert decision.mode == "lowest_cost"
    # Should pick the cheapest token model in registry (e.g. llama-3.1-8b or gemini-1.5-flash)
    cheapest = sorted(ProfileManager.get_all(), key=lambda p: float(p.input_cost_per_1k))[0]
    assert decision.selected_model == cheapest.model_id
    assert "Lowest-cost mode" in decision.reason


@pytest.mark.asyncio
async def test_direct_routing_mode():
    engine = RoutingEngine()
    prompt = "Translate this word to French."
    decision = await engine.route(prompt=prompt, requested_model="gpt-4o", routing_mode="direct")
    
    assert decision.mode == "direct"
    assert decision.selected_model == "gpt-4o"
    assert "Direct model requested" in decision.reason


def test_profile_manager_empirical_update():
    # Verify profile manager dynamically stores updated benchmark metrics
    ProfileManager.update_profile(
        model_id="gpt-4o-mini",
        coding_score=0.88,
        reasoning_score=0.86,
        latency_ms=175.0,
    )
    prof = ProfileManager.get("gpt-4o-mini")
    assert prof is not None
    assert prof.coding_quality == 0.88
    assert prof.reasoning_quality == 0.86
    assert prof.avg_latency_ms == 175.0
