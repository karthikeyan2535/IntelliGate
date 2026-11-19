"""
Coding Problem Analyzer.
Analyzes problem statements, constraints, and requirements to determine:
- Task type (algorithm generation, debugging, code repair, etc.)
- Algorithm family (arrays_strings, dynamic_programming, graphs, trees_data_structures, etc.)
- Estimated difficulty (easy, medium, hard)
- Complexity expectations
- Edge cases
"""
from __future__ import annotations

import re
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class CodingProblemAnalysis(BaseModel):
    task_type: str = "algorithm_generation"
    algorithm_family: str = "other"
    difficulty: str = "medium"
    expected_time_complexity: str = "O(n)"
    expected_space_complexity: str = "O(1)"
    edge_cases: list[str] = Field(default_factory=list)
    confidence: float = 0.85
    reasoning: str = ""


class CodingProblemAnalyzer:
    """
    Dedicated analyzer combining fast deterministic heuristic pattern matching
    with structured classification.
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

    def analyze(self, title: str, statement: str, constraints: Optional[str] = "") -> CodingProblemAnalysis:
        full_text = f"{title}\n{statement}\n{constraints or ''}".lower()

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

        # Pick best category or fallback to arrays_strings / other
        sorted_families = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_family, top_score = sorted_families[0]
        if top_score == 0:
            best_family = "arrays_strings" if any(w in full_text for w in ["array", "list", "string", "character"]) else "other"

        # 3. Estimate difficulty from constraint bounds
        difficulty = "medium"
        n_match = re.search(r"n\s*<=?\s*(\d[\d,^e]*)", full_text)
        expected_time = "O(n)"
        expected_space = "O(1)"

        if "10^5" in full_text or "100000" in full_text or "200000" in full_text:
            expected_time = "O(n log n)" if best_family in ["greedy_binary_search", "trees_data_structures"] else "O(n)"
            difficulty = "medium"
        elif "10^9" in full_text or "1000000000" in full_text:
            expected_time = "O(log n)" or "O(sqrt(n))"
            difficulty = "hard"
        elif "n <= 20" in full_text or "n <= 15" in full_text:
            expected_time = "O(2^n)"
            difficulty = "hard"
            best_family = "backtracking" if scores["backtracking"] > 0 else best_family
        elif any(w in full_text for w in ["simple", "sum of", "find maximum", "return true if"]):
            difficulty = "easy"

        # Common edge cases based on family
        edge_cases = ["Empty input / n = 0", "Single element / n = 1"]
        if best_family == "graphs":
            edge_cases.extend(["Disconnected graph", "Self-loops or multi-edges", "Cycle presence"])
        elif best_family == "dynamic_programming":
            edge_cases.extend(["Zero capacity / base case", "All negative weights", "Large target value"])
        elif best_family == "trees_data_structures":
            edge_cases.extend(["Skewed / linear tree", "Root-only tree", "Duplicate node values"])
        elif best_family == "greedy_binary_search":
            edge_cases.extend(["Element not found", "All elements identical", "Boundaries at ends"])

        return CodingProblemAnalysis(
            task_type=task_type,
            algorithm_family=best_family,
            difficulty=difficulty,
            expected_time_complexity=expected_time,
            expected_space_complexity=expected_space,
            edge_cases=edge_cases,
            confidence=0.88 if top_score > 0 else 0.65,
            reasoning=f"Matched {len(matched_keywords.get(best_family, []))} indicators for {best_family}. Difficulty estimated from constraints.",
        )


coding_analyzer = CodingProblemAnalyzer()
