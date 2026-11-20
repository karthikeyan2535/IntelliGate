"""
Coding Problem Analyzer.
Analyzes problem statements, constraints, and requirements to determine:
- Task type (algorithm generation, debugging, code repair, etc.)
- Algorithm family (arrays_strings, dynamic_programming, graphs, trees_data_structures, etc.)
- ML-Predicted Difficulty (Sentence-BERT embeddings + Structured Features + LightGBM Quantile Regression)
- Calibrated uncertainty bounds [lower_bound, upper_bound]
- Complexity expectations
- Edge cases
"""
from __future__ import annotations

import re
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from app.analysis.ml_difficulty.predictor import difficulty_predictor, DifficultyPrediction


class CodingProblemAnalysis(BaseModel):
    task_type: str = "algorithm_generation"
    algorithm_family: str = "other"
    difficulty: str = "medium"
    expected_time_complexity: str = "O(n)"
    expected_space_complexity: str = "O(1)"
    edge_cases: list[str] = Field(default_factory=list)
    confidence: float = 0.88
    reasoning: str = ""
    # ML-predicted Codeforces rating & uncertainty interval
    predicted_rating: Optional[int] = Field(None, description="Estimated Codeforces difficulty rating (800 - 3500)")
    lower_bound: Optional[int] = Field(None, description="Calibrated lower uncertainty bound (alpha = 0.10)")
    upper_bound: Optional[int] = Field(None, description="Calibrated upper uncertainty bound (alpha = 0.90)")
    confidence_width: Optional[int] = Field(None, description="Uncertainty interval width (upper_bound - lower_bound)")
    prediction_method: str = Field("sentence_bert_lightgbm", description="Method used for difficulty estimation")
    official_rating: Optional[int] = Field(None, description="Official rating if available from problem source")


class CodingProblemAnalyzer:
    """
    Dedicated analyzer combining fast semantic categorization with ML-driven
    difficulty quantile regression.
    """

    # Keyword patterns for algorithm families
    PATTERNS = {
        "dynamic_programming": [
            r"\bdp\b", r"\bdynamic programming\b", r"\bsubproblem\b", r"\bmemoiz\w*",
            r"\bknapsack\b", r"\blongest common\b", r"\blongest increasing\b", r"\boptimal substructure\b",
            r"\bcoin change\b", r"\bmaximum subarray\b", r"\bmin cost\b", r"\bgrid paths\b"
        ],
        "graphs": [
            r"\bgraph\b", r"\bbfs\b", r"\bdfs\b", r"\bbreadth-first\b", r"\bdepth-first\b",
            r"\bdijkstra\b", r"\bshortest path\b", r"\btopological sort\b", r"\bconnected component\b",
            r"\bbipartite\b", r"\bcycle detection\b", r"\badjacency\b", r"\bvertex\b", r"\bvertices\b", r"\bedges\b"
        ],
        "trees_data_structures": [
            r"\btree\b", r"\bbinary tree\b", r"\bbst\b", r"\btrie\b", r"\bheap\b", r"\bpriority queue\b",
            r"\bsegment tree\b", r"\bfenwick\b", r"\bunion-find\b", r"\bdisjoint set\b", r"\bstack\b",
            r"\bmonotonic stack\b", r"\bqueue\b", r"\blinked list\b"
        ],
        "greedy_binary_search": [
            r"\bgreedy\b", r"\bbinary search\b", r"\bbisect\b", r"\binterval scheduling\b",
            r"\bmonotonically\b", r"\btwo pointers\b", r"\bsliding window\b", r"\bprefix sum\b"
        ],
        "arrays_strings": [
            r"\barray\b", r"\bstring\b", r"\bsubstring\b", r"\bsubarray\b", r"\bpalindrome\b",
            r"\banagram\b", r"\bhash table\b", r"\bhashmap\b", r"\bmatrix\b", r"\brotate\b"
        ],
        "backtracking": [
            r"\bbacktrack\w*", r"\bpermutation\w*", r"\bcombination\w*", r"\bn-queens\b", r"\bsudoku\b"
        ],
        "number_theory": [
            r"\bprime\b", r"\bgcd\b", r"\blcm\b", r"\bmodulo\b", r"\bcombinatorics\b", r"\bfactorial\b"
        ]
    }

    def analyze(
        self,
        title: str,
        statement: str,
        constraints: Optional[str] = "",
        input_format: Optional[str] = "",
        output_format: Optional[str] = "",
        official_rating: Optional[int] = None,
        time_limit_ms: Optional[int] = None,
        memory_limit_mb: Optional[int] = None,
    ) -> CodingProblemAnalysis:
        full_text = f"{title}\n{statement}\n{constraints or ''}\n{input_format or ''}\n{output_format or ''}".lower()

        # 1. Determine task type
        task_type = "algorithm_generation"
        if any(w in full_text for w in ["fix the bug", "debug", "error in code", "compiler error"]):
            task_type = "debugging"
        elif any(w in full_text for w in ["optimize", "reduce time limit", "tle fix"]):
            task_type = "code_optimization"
        elif any(w in full_text for w in ["generate test", "adversarial case"]):
            task_type = "test_case_generation"

        # 2. Score algorithm families
        scores: Dict[str, int] = {k: 0 for k in self.PATTERNS}
        matched_keywords: Dict[str, list[str]] = {k: [] for k in self.PATTERNS}

        for family, pattern_list in self.PATTERNS.items():
            for pat in pattern_list:
                matches = re.findall(pat, full_text)
                if matches:
                    scores[family] += len(matches) * 2
                    matched_keywords[family].extend(matches)

        sorted_families = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_family, top_score = sorted_families[0]
        if top_score == 0:
            best_family = "arrays_strings" if any(w in full_text for w in ["array", "list", "string", "character"]) else "other"

        # 3. Machine-Learning Difficulty & Quantile Uncertainty Prediction
        if official_rating and 800 <= official_rating <= 3500:
            pred_rating = official_rating
            lower_bound = official_rating
            upper_bound = official_rating
            confidence_width = 0
            prediction_method = "official_codeforces"
            difficulty = difficulty_predictor._tier_from_rating(official_rating)
        else:
            ml_pred: DifficultyPrediction = difficulty_predictor.predict(
                title=title,
                statement=statement,
                constraints=constraints or "",
                input_format=input_format or "",
                output_format=output_format or "",
                time_limit_ms=time_limit_ms,
                memory_limit_mb=memory_limit_mb,
            )
            pred_rating = ml_pred.predicted_rating
            lower_bound = ml_pred.lower_bound
            upper_bound = ml_pred.upper_bound
            confidence_width = ml_pred.confidence_width
            prediction_method = ml_pred.prediction_method
            difficulty = ml_pred.difficulty_tier

        # 4. Complexity expectations
        expected_time = "O(n)"
        expected_space = "O(1)"

        if pred_rating >= 2100:
            expected_time = "O(n log n)" or "O(n sqrt(n))"
            expected_space = "O(n)"
        elif pred_rating >= 1600:
            expected_time = "O(n log n)" if best_family in ["greedy_binary_search", "trees_data_structures", "graphs"] else "O(n)"
            expected_space = "O(n)" if best_family in ["dynamic_programming", "graphs"] else "O(1)"
        else:
            expected_time = "O(n)"
            expected_space = "O(1)"

        # 5. Common edge cases based on family
        edge_cases = ["Empty input / n = 0", "Single element / n = 1"]
        if best_family == "graphs":
            edge_cases.extend(["Disconnected graph", "Self-loops or multi-edges", "Cycle presence"])
        elif best_family == "dynamic_programming":
            edge_cases.extend(["Zero capacity / base case", "All negative weights", "Large target value"])
        elif best_family == "trees_data_structures":
            edge_cases.extend(["Skewed / linear tree", "Root-only tree", "Duplicate node values"])
        elif best_family == "greedy_binary_search":
            edge_cases.extend(["Element not found", "All elements identical", "Boundaries at ends"])

        reasoning = (
            f"Classified under '{best_family}' ({len(matched_keywords.get(best_family, []))} indicators). "
            f"Difficulty evaluated via {prediction_method}: CF rating {pred_rating} "
            f"[{lower_bound} - {upper_bound}] (width: {confidence_width})."
        )

        return CodingProblemAnalysis(
            task_type=task_type,
            algorithm_family=best_family,
            difficulty=difficulty,
            expected_time_complexity=expected_time,
            expected_space_complexity=expected_space,
            edge_cases=edge_cases,
            confidence=0.88 if top_score > 0 else 0.70,
            reasoning=reasoning,
            predicted_rating=pred_rating,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            confidence_width=confidence_width,
            prediction_method=prediction_method,
            official_rating=official_rating,
        )


coding_analyzer = CodingProblemAnalyzer()
