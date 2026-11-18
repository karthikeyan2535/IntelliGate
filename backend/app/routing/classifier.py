"""
Task Classification and Complexity Estimation for Intelligent LLM Routing.
Analyzes prompt characteristics (code syntax, constraints, reasoning markers, structural depth)
to accurately categorize tasks into:
  - Categories: coding, reasoning, writing, general_qa
  - Complexity: simple, moderate, complex
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class TaskCategory(str, Enum):
    CODING = "coding"
    REASONING = "reasoning"
    WRITING = "writing"
    GENERAL_QA = "general_qa"


class ComplexityLevel(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


@dataclass
class ClassificationResult:
    category: TaskCategory
    complexity: ComplexityLevel
    confidence: float
    detected_features: list[str]
    explanation: str

    @property
    def signals(self) -> list[str]:
        return self.detected_features


# Keyword and syntax heuristics
CODING_PATTERNS = [
    r"```[a-zA-Z]*",
    r"\b(def |function |class |return |import |const |let |var |fn |func |pub |SELECT |FROM |WHERE |GROUP BY)\b",
    r"\b(debug|refactor|compile|runtime error|syntax error|algorithm|unit test|regex|sql query|api endpoint|dockerfile)\b",
    r"(\{|\}|\(\)|=>|===|!==|;|\[\])",
]

REASONING_PATTERNS = [
    r"\b(prove|derive|solve for|step-by-step|deduce|infer|calculate|probability|bayes|logic puzzle|contradiction)\b",
    r"\b(why does|analyze the trade-off|evaluate the consequence|what would happen if|root cause)\b",
    r"\b(\d+\s*[\+\-\*\/\^]\s*\d+|equation|theorem|hypothesis|p-value|matrix|differential)\b",
]

WRITING_PATTERNS = [
    r"\b(draft|write a (story|essay|poem|email|speech|blog post|article)|summarize|paraphrase|rewrite)\b",
    r"\b(tone of voice|compelling|creative writing|metaphor|rhyme|dialogue|in the style of)\b",
    r"\b(headline|copywriting|bullet points|executive summary|press release)\b",
]

COMPLEXITY_HIGH_INDICATORS = [
    r"\b(lock-free|concurrency|distributed system|consensus|byzantine|fault tolerance|protocol|inductive proof|formal proof|microservices|memory leak|deadlock|np-hard|dynamic programming)\b",
    r"\b(asymptot|o\(n\^|formal verification|security audit|vulnerability analysis|zero-day|cryptographic|safety and liveness)\b",
    r"\b(comprehensive|production-grade|end-to-end|in-depth analysis|multi-tier|architectural design|distributed consensus)\b",
]

COMPLEXITY_MODERATE_INDICATORS = [
    r"\b(async |await |fastapi|sqlalchemy|postgresql|docker|database|refactor|optimize|class |unit test|algorithm)\b",
    r"\b(step-by-step|logical proof|puzzle|contradiction|derive|calculate probability)\b",
]

CONSTRAINT_PATTERNS = [
    r"\b(must (be|include|not|have)|strictly|do not include|limit to|maximum of|json format only|valid yaml)\b",
    r"\b(without using|format as|schema:)\b",
]


class TaskClassifier:
    """Classifies user prompts into task categories and complexity levels."""

    @classmethod
    def classify(cls, prompt: str) -> ClassificationResult:
        if not prompt or not prompt.strip():
            return ClassificationResult(
                category=TaskCategory.GENERAL_QA,
                complexity=ComplexityLevel.SIMPLE,
                confidence=0.5,
                detected_features=["empty_or_minimal_prompt"],
                explanation="Minimal or empty prompt defaulted to general_qa.",
            )

        text = prompt.strip()
        lower = text.lower()
        features: list[str] = []

        # 1. Category Detection Scoring
        coding_score = 0.0
        reasoning_score = 0.0
        writing_score = 0.0

        for pat in CODING_PATTERNS:
            matches = len(re.findall(pat, text, re.IGNORECASE))
            if matches > 0:
                coding_score += matches * 1.5

        for pat in REASONING_PATTERNS:
            matches = len(re.findall(pat, lower))
            if matches > 0:
                reasoning_score += matches * 1.5

        for pat in WRITING_PATTERNS:
            matches = len(re.findall(pat, lower))
            if matches > 0:
                writing_score += matches * 1.5

        # Feature tracking
        if coding_score > 0:
            features.append(f"code_syntax_score:{coding_score:.1f}")
        if reasoning_score > 0:
            features.append(f"reasoning_cues_score:{reasoning_score:.1f}")
        if writing_score > 0:
            features.append(f"writing_cues_score:{writing_score:.1f}")

        # Determine winning category
        max_score = max(coding_score, reasoning_score, writing_score)
        if max_score < 1.0:
            category = TaskCategory.GENERAL_QA
            confidence = 0.75
        elif coding_score == max_score:
            category = TaskCategory.CODING
            confidence = min(0.98, 0.65 + (coding_score * 0.05))
        elif reasoning_score == max_score:
            category = TaskCategory.REASONING
            confidence = min(0.95, 0.65 + (reasoning_score * 0.05))
        else:
            category = TaskCategory.WRITING
            confidence = min(0.95, 0.65 + (writing_score * 0.05))

        # 2. Complexity Estimation (independent of simple token length!)
        complexity_score = 0.0

        # Technical depth indicators
        for pat in COMPLEXITY_HIGH_INDICATORS:
            found = re.findall(pat, lower)
            if found:
                complexity_score += 2.0 * len(found)
                features.append(f"high_complexity_term:{found[0]}")

        for pat in COMPLEXITY_MODERATE_INDICATORS:
            found = re.findall(pat, lower)
            if found:
                complexity_score += 1.2 * len(found)
                features.append(f"moderate_indicator:{found[0]}")

        # Constraint density
        constraint_count = sum(len(re.findall(pat, lower)) for pat in CONSTRAINT_PATTERNS)
        if constraint_count > 0:
            complexity_score += constraint_count * 1.0
            features.append(f"constraints_found:{constraint_count}")

        # Multi-question structure
        question_marks = text.count("?")
        if question_marks >= 3:
            complexity_score += 1.5
            features.append("multi_part_questions")

        # Code block presence adds baseline complexity
        if "```" in text or "def " in text or "class " in text:
            complexity_score += 1.2
            features.append("contains_executable_code")

        # Word count contribution (subtle modifier, not sole determinant)
        word_count = len(text.split())
        if word_count > 250:
            complexity_score += 1.5
        elif word_count < 25 and complexity_score == 0:
            complexity_score -= 1.0

        # Decide complexity level
        if complexity_score >= 3.0:
            complexity = ComplexityLevel.COMPLEX
        elif complexity_score >= 1.2:
            complexity = ComplexityLevel.MODERATE
        else:
            complexity = ComplexityLevel.SIMPLE

        explanation = (
            f"Classified as '{category.value}' ({complexity.value} complexity) "
            f"based on {', '.join(features) if features else 'direct informational phrasing'}."
        )

        return ClassificationResult(
            category=category,
            complexity=complexity,
            confidence=round(confidence, 2),
            detected_features=features,
            explanation=explanation,
        )
