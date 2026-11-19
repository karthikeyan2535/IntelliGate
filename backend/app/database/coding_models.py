"""
Coding-specific database models for IntelliGate.

Tables:
  - coding_problems
  - coding_test_cases
  - coding_submissions
  - coding_attempts
  - coding_benchmark_runs
  - coding_benchmark_results
  - coding_model_profiles
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class TaskType(str, enum.Enum):
    ALGORITHM_GENERATION = "algorithm_generation"
    DEBUGGING = "debugging"
    CODE_OPTIMIZATION = "code_optimization"
    CODE_REPAIR = "code_repair"
    TEST_CASE_GENERATION = "test_case_generation"
    CODE_EXPLANATION = "code_explanation"


class AlgorithmFamily(str, enum.Enum):
    ARRAYS_STRINGS = "arrays_strings"
    DYNAMIC_PROGRAMMING = "dynamic_programming"
    GRAPHS = "graphs"
    TREES_DATA_STRUCTURES = "trees_data_structures"
    GREEDY_BINARY_SEARCH = "greedy_binary_search"
    BACKTRACKING = "backtracking"
    NUMBER_THEORY = "number_theory"
    OTHER = "other"


class DifficultyLevel(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class SupportedLanguage(str, enum.Enum):
    CPP = "cpp"
    PYTHON = "python"
    JAVA = "java"


class ExecutionStatus(str, enum.Enum):
    PENDING = "pending"
    COMPILING = "compiling"
    RUNNING = "running"
    ACCEPTED = "accepted"
    WRONG_ANSWER = "wrong_answer"
    COMPILATION_ERROR = "compilation_error"
    RUNTIME_ERROR = "runtime_error"
    TIME_LIMIT_EXCEEDED = "time_limit_exceeded"
    MEMORY_LIMIT_EXCEEDED = "memory_limit_exceeded"
    EXECUTION_ERROR = "execution_error"
    INFRASTRUCTURE_ERROR = "infrastructure_error"


class RoutingMode(str, enum.Enum):
    INTELLIGENT = "intelligent"
    LOWEST_COST = "lowest_cost"
    DIRECT = "direct"
    BASELINE_STRONGEST = "baseline_strongest"
    BASELINE_CHEAPEST = "baseline_cheapest"
    BASELINE_STATIC = "baseline_static"


# ── CodingProblem ─────────────────────────────────────────────────────────────


class CodingProblem(Base):
    __tablename__ = "coding_problems"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(64), default="manual", nullable=False)  # manual / codeforces / leetcode / benchmark
    source_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    constraints: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    input_format: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_format: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    algorithm_category: Mapped[str] = mapped_column(String(64), default="other", nullable=False)
    difficulty: Mapped[str] = mapped_column(String(32), default="medium", nullable=False)
    time_limit_ms: Mapped[int] = mapped_column(Integer, default=2000, nullable=False)
    memory_limit_mb: Mapped[int] = mapped_column(Integer, default=256, nullable=False)
    is_benchmark: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    benchmark_split: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # calibration / test / None

    # Structured metadata extracted by analyzer
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    test_cases: Mapped[List["CodingTestCase"]] = relationship(
        "CodingTestCase", back_populates="problem", cascade="all, delete-orphan", order_by="CodingTestCase.id"
    )
    submissions: Mapped[List["CodingSubmission"]] = relationship(
        "CodingSubmission", back_populates="problem", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_coding_problems_category", "algorithm_category"),
        Index("ix_coding_problems_difficulty", "difficulty"),
        Index("ix_coding_problems_is_benchmark", "is_benchmark"),
    )


# ── CodingTestCase ────────────────────────────────────────────────────────────


class CodingTestCase(Base):
    __tablename__ = "coding_test_cases"

    problem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("coding_problems.id", ondelete="CASCADE"), nullable=False
    )
    input_data: Mapped[str] = mapped_column(Text, nullable=False)
    expected_output: Mapped[str] = mapped_column(Text, nullable=False)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    problem: Mapped["CodingProblem"] = relationship("CodingProblem", back_populates="test_cases")

    __table_args__ = (
        Index("ix_coding_test_cases_problem_id", "problem_id"),
    )


# ── CodingSubmission ──────────────────────────────────────────────────────────


class CodingSubmission(Base):
    __tablename__ = "coding_submissions"

    problem_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("coding_problems.id", ondelete="SET NULL"), nullable=True
    )
    language: Mapped[str] = mapped_column(String(32), default="python", nullable=False)
    routing_mode: Mapped[str] = mapped_column(String(32), default="intelligent", nullable=False)
    target_model: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)  # for direct mode
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    cost_budget_usd: Mapped[Optional[float]] = mapped_column(Float, default=0.05, nullable=True)
    latency_budget_ms: Mapped[Optional[int]] = mapped_column(Integer, default=30000, nullable=True)

    # Outcome
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    final_solution_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    initial_model: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    final_model: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    total_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passed_test_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_test_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Explainability trace
    trace_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    problem: Mapped[Optional["CodingProblem"]] = relationship("CodingProblem", back_populates="submissions")
    attempts: Mapped[List["CodingAttempt"]] = relationship(
        "CodingAttempt", back_populates="submission", cascade="all, delete-orphan", order_by="CodingAttempt.attempt_number"
    )

    __table_args__ = (
        Index("ix_coding_submissions_problem_id", "problem_id"),
        Index("ix_coding_submissions_status", "status"),
        Index("ix_coding_submissions_created_at", "created_at"),
    )


# ── CodingAttempt ─────────────────────────────────────────────────────────────


class CodingAttempt(Base):
    __tablename__ = "coding_attempts"

    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("coding_submissions.id", ondelete="CASCADE"), nullable=False
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    model_id: Mapped[str] = mapped_column(String(128), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    routing_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Generated Output
    generated_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    algorithm_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    complexity_estimate: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # Verification / Execution
    execution_status: Mapped[str] = mapped_column(String(64), default="pending", nullable=False)
    passed_tests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    compiler_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    runtime_stdout: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    runtime_stderr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    failed_cases_json: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # Economics & Latency
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    submission: Mapped["CodingSubmission"] = relationship("CodingSubmission", back_populates="attempts")

    __table_args__ = (
        Index("ix_coding_attempts_submission_id", "submission_id"),
        Index("ix_coding_attempts_model_id", "model_id"),
        Index("ix_coding_attempts_status", "execution_status"),
    )


# ── CodingBenchmarkRun ────────────────────────────────────────────────────────


class CodingBenchmarkRun(Base):
    __tablename__ = "coding_benchmark_runs"

    benchmark_suite: Mapped[str] = mapped_column(String(64), default="standard_100", nullable=False)
    model_id: Mapped[str] = mapped_column(String(128), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    split: Mapped[str] = mapped_column(String(32), default="calibration", nullable=False)  # calibration / test
    routing_strategy: Mapped[Optional[str]] = mapped_column(String(64), default="direct", nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)

    total_problems: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passed_problems: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pass_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    first_attempt_pass_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    cost_per_verified_solution: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    avg_latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Category performance breakdowns
    category_scores: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    results: Mapped[List["CodingBenchmarkResult"]] = relationship(
        "CodingBenchmarkResult", back_populates="run", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_coding_benchmark_runs_model_id", "model_id"),
        Index("ix_coding_benchmark_runs_split", "split"),
    )


# ── CodingBenchmarkResult ─────────────────────────────────────────────────────


class CodingBenchmarkResult(Base):
    __tablename__ = "coding_benchmark_results"

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("coding_benchmark_runs.id", ondelete="CASCADE"), nullable=False
    )
    problem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("coding_problems.id", ondelete="CASCADE"), nullable=False
    )
    algorithm_category: Mapped[str] = mapped_column(String(64), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(32), nullable=False)
    attempts_needed: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    final_status: Mapped[str] = mapped_column(String(64), nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    test_cases_passed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_test_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    generated_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    run: Mapped["CodingBenchmarkRun"] = relationship("CodingBenchmarkRun", back_populates="results")
    problem: Mapped["CodingProblem"] = relationship("CodingProblem")

    __table_args__ = (
        Index("ix_coding_benchmark_results_run_id", "run_id"),
        Index("ix_coding_benchmark_results_passed", "passed"),
    )


# ── CodingModelProfile ────────────────────────────────────────────────────────


class CodingModelProfile(Base):
    """
    Empirically measured coding performance profile for a model, broken down by category & difficulty.
    """
    __tablename__ = "coding_model_profiles"

    model_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)

    overall_pass_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    first_attempt_pass_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    compilation_failure_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    runtime_failure_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Category pass rates (measured empirically)
    arrays_strings_pass_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    dynamic_programming_pass_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    graphs_pass_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    trees_data_structures_pass_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    greedy_binary_search_pass_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    debugging_repair_pass_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Difficulty pass rates
    easy_pass_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    medium_pass_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    hard_pass_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Cost & Speed
    avg_latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    avg_cost_per_attempt: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    input_cost_per_1k: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    output_cost_per_1k: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    sample_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_evaluated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_coding_model_profiles_model_id", "model_id"),
    )
