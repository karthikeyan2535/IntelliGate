"""
Structured Feature Extractor for Competitive Programming Problems.

Extracts numerical, structural, and syntactic features from problem statements,
constraints, time/memory limits, and input/output formats without relying on
explicit tags or editorials.
"""
from __future__ import annotations

import math
import re
from typing import Dict, List, Optional, Tuple, Any


class StructuredFeatureExtractor:
    """
    Extracts a fixed-dimensional vector of numerical features with proper
    logarithmic transformations, missing-value indicators, and domain-specific
    structural signals.
    """

    FEATURE_NAMES = [
        "log_char_count",
        "log_word_count",
        "line_count",
        "log_time_limit_ms",
        "missing_time_limit",
        "log_memory_limit_mb",
        "missing_memory_limit",
        "has_multiple_test_cases",
        "log_max_n",
        "missing_max_n",
        "log_max_val",
        "missing_max_val",
        "math_symbol_count",
        "math_symbol_density",
        "num_numeric_tokens",
        "num_single_letter_vars",
        "has_modulo",
        "is_interactive",
        "is_graph_problem",
        "is_geometry_problem",
        "is_string_problem",
        "is_bitwise_problem",
        "has_grid_matrix",
        "has_queries",
    ]

    def __init__(self):
        # Precompile common regex patterns
        self._n_pattern = re.compile(
            r"(?:(?:[1-9]\d*)\s*[\u2264<=]\s*)?[nN]\s*[\u2264<=]\s*([1-9]\d*(?:\s*[\*x\u00d7\u00b7]\s*10\^?\d+)?|10\^?\d+|[0-9]+)"
        )
        self._ten_power_pattern = re.compile(r"10\^(\d+)")
        self._sci_mult_pattern = re.compile(r"(\d+)\s*[\*x\u00d7\u00b7]\s*10\^?(\d+)")
        self._val_pattern = re.compile(
            r"(?:a_?i|arr\[i\]|val|cost|weight|w_?i|x_?i|y_?i|c_?i)\s*[\u2264<=]\s*([1-9]\d*(?:\s*[\*x\u00d7\u00b7]\s*10\^?\d+|10\^?\d+|[0-9]+)?)"
        )
        self._modulo_pattern = re.compile(
            r"(?:modulo|mod(?:ulo)?\s*(?:by)?|10\^9\s*\+\s*7|998\s*244\s*353|1000000007|998244353)",
            re.IGNORECASE
        )
        self._interactive_pattern = re.compile(
            r"(?:interactive|standard output\s*,\s*flush|fflush|stdout\.flush|\bquery\b|\bqueries\b.{0,30}\bask\b)",
            re.IGNORECASE
        )
        self._graph_pattern = re.compile(
            r"\b(?:vertex|vertices|edge|edges|graph|tree|adjacency|bipartite|dag|cycle|path|undirected|directed)\b",
            re.IGNORECASE
        )
        self._geometry_pattern = re.compile(
            r"\b(?:coordinate|coordinates|point|points|polygon|euclidean|distance|angle|convex hull|segment)\b",
            re.IGNORECASE
        )
        self._string_pattern = re.compile(
            r"\b(?:substring|subsequence|prefix|suffix|palindrome|alphabet|character|characters|anagram|lexicograph\w*)\b",
            re.IGNORECASE
        )
        self._bitwise_pattern = re.compile(
            r"\b(?:xor|bitwise|binary representation|bit\s*shift|\u2295|\bbit\b|\bbits\b)\b",
            re.IGNORECASE
        )
        self._grid_pattern = re.compile(
            r"\b(?:grid|matrix|row|rows|column|columns|cell|cells|chessboard|table)\b",
            re.IGNORECASE
        )
        self._queries_pattern = re.compile(
            r"(?:[1-9]\d*\s*[\u2264<=]\s*)?[qQ]\s*[\u2264<=]\s*(?:10\^?\d+|[0-9]+)|\bqueries\b",
            re.IGNORECASE
        )
        self._test_cases_pattern = re.compile(
            r"(?:first line contains.*?t(?:est)?\s*cases?|[1-9]\d*\s*[\u2264<=]\s*t\s*[\u2264<=]\s*\d+|each test contains|test cases? consists? of)",
            re.IGNORECASE
        )

    def _parse_bound_value(self, text: str) -> Optional[float]:
        """Parses mathematical bounds like '10^5', '2 * 10^5', '100000', '10^9'."""
        if not text:
            return None
        text = text.replace(",", "").replace(" ", "").strip()

        # Scientific multiplication e.g. 2*10^5 or 2x10^5
        m_mult = self._sci_mult_pattern.search(text)
        if m_mult:
            coeff = float(m_mult.group(1))
            power = float(m_mult.group(2))
            return coeff * (10 ** power)

        # 10^k
        m_pow = self._ten_power_pattern.search(text)
        if m_pow:
            return 10 ** float(m_pow.group(1))

        # Plain integer
        m_int = re.search(r"\d+", text)
        if m_int:
            try:
                return float(m_int.group(0))
            except ValueError:
                return None
        return None

    def extract_features(
        self,
        statement: str,
        constraints: Optional[str] = "",
        time_limit_ms: Optional[int] = None,
        memory_limit_mb: Optional[int] = None,
        input_format: Optional[str] = "",
        output_format: Optional[str] = "",
    ) -> Dict[str, float]:
        """
        Extract structured numerical features as a dictionary.
        """
        full_text = f"{statement}\n{constraints or ''}\n{input_format or ''}\n{output_format or ''}"
        chars = len(full_text)
        words = len(full_text.split())
        lines = len(full_text.splitlines())

        # Log statement length & word count
        log_char_count = math.log10(max(chars, 1))
        log_word_count = math.log10(max(words, 1))

        # Time & Memory limits
        if time_limit_ms and time_limit_ms > 0:
            log_time_limit_ms = math.log10(time_limit_ms)
            missing_time_limit = 0.0
        else:
            # Try to regex parse e.g. "time limit per test: 2.0 seconds"
            tl_m = re.search(r"time limit.*?(\d+(?:\.\d+)?)\s*(?:sec(?:onds?)?|s\b)", full_text, re.IGNORECASE)
            if tl_m:
                ms = float(tl_m.group(1)) * 1000.0
                log_time_limit_ms = math.log10(max(ms, 100.0))
                missing_time_limit = 0.0
            else:
                log_time_limit_ms = math.log10(1000.0)  # default 1000ms
                missing_time_limit = 1.0

        if memory_limit_mb and memory_limit_mb > 0:
            log_memory_limit_mb = math.log10(memory_limit_mb)
            missing_memory_limit = 0.0
        else:
            ml_m = re.search(r"memory limit.*?(\d+)\s*(?:mega?bytes?|mb\b)", full_text, re.IGNORECASE)
            if ml_m:
                mb = float(ml_m.group(1))
                log_memory_limit_mb = math.log10(max(mb, 16.0))
                missing_memory_limit = 0.0
            else:
                log_memory_limit_mb = math.log10(256.0)  # default 256MB
                missing_memory_limit = 1.0

        # Multiple test cases
        has_multiple_test_cases = 1.0 if bool(self._test_cases_pattern.search(full_text)) else 0.0

        # Maximum N constraint
        n_match = self._n_pattern.search(full_text)
        parsed_n = None
        if n_match:
            parsed_n = self._parse_bound_value(n_match.group(1))
        if parsed_n is None or parsed_n < 50:
            # Fallback search for 10^5, 2*10^5, 10^9
            if "2*10^5" in full_text or "2·10^5" in full_text or "2 * 10^5" in full_text or "200000" in full_text:
                parsed_n = 200000.0
            elif "10^5" in full_text or "100000" in full_text:
                parsed_n = 100000.0
            elif "10^6" in full_text:
                parsed_n = 1000000.0

        if parsed_n and parsed_n > 0:
            log_max_n = math.log10(parsed_n)
            missing_max_n = 0.0
        else:
            log_max_n = 4.0  # default 10^4
            missing_max_n = 1.0

        # Maximum value constraint (e.g. A_i <= 10^9 or 10^18)
        val_match = self._val_pattern.search(full_text)
        parsed_val = None
        if val_match:
            parsed_val = self._parse_bound_value(val_match.group(1))
        if parsed_val is None:
            if "10^18" in full_text:
                parsed_val = 1e18
            elif "10^9" in full_text or "1000000000" in full_text:
                parsed_val = 1e9

        if parsed_val and parsed_val > 0:
            log_max_val = math.log10(parsed_val)
            missing_max_val = 0.0
        else:
            log_max_val = 9.0  # default 10^9
            missing_max_val = 1.0

        # Math symbols & expressions
        math_chars = sum(full_text.count(ch) for ch in ["$", "\\", "_", "^", "{", "}", "\u2264", "\u2265", "\u2260", "\u00d7", "\u2295"])
        math_density = math_chars / max(chars, 1)

        # Numeric tokens and variables
        num_numeric_tokens = len(re.findall(r"\b\d+\b", full_text))
        single_letter_vars = len(re.findall(r"\b[a-zA-Z]\b", full_text))

        # Modulo & Interactive
        has_modulo = 1.0 if bool(self._modulo_pattern.search(full_text)) else 0.0
        is_interactive = 1.0 if bool(self._interactive_pattern.search(full_text)) else 0.0

        # Algorithm domain indicators
        is_graph_problem = min(len(self._graph_pattern.findall(full_text)), 10) / 10.0
        is_geometry_problem = min(len(self._geometry_pattern.findall(full_text)), 10) / 10.0
        is_string_problem = min(len(self._string_pattern.findall(full_text)), 10) / 10.0
        is_bitwise_problem = min(len(self._bitwise_pattern.findall(full_text)), 10) / 10.0
        has_grid_matrix = min(len(self._grid_pattern.findall(full_text)), 10) / 10.0
        has_queries = 1.0 if bool(self._queries_pattern.search(full_text)) else 0.0

        return {
            "log_char_count": log_char_count,
            "log_word_count": log_word_count,
            "line_count": min(lines / 100.0, 5.0),
            "log_time_limit_ms": log_time_limit_ms,
            "missing_time_limit": missing_time_limit,
            "log_memory_limit_mb": log_memory_limit_mb,
            "missing_memory_limit": missing_memory_limit,
            "has_multiple_test_cases": has_multiple_test_cases,
            "log_max_n": log_max_n,
            "missing_max_n": missing_max_n,
            "log_max_val": log_max_val,
            "missing_max_val": missing_max_val,
            "math_symbol_count": math.log10(max(math_chars, 1)),
            "math_symbol_density": min(math_density * 10.0, 5.0),
            "num_numeric_tokens": min(num_numeric_tokens / 50.0, 5.0),
            "num_single_letter_vars": min(single_letter_vars / 50.0, 5.0),
            "has_modulo": has_modulo,
            "is_interactive": is_interactive,
            "is_graph_problem": is_graph_problem,
            "is_geometry_problem": is_geometry_problem,
            "is_string_problem": is_string_problem,
            "is_bitwise_problem": is_bitwise_problem,
            "has_grid_matrix": has_grid_matrix,
            "has_queries": has_queries,
        }

    def extract_vector(
        self,
        statement: str,
        constraints: Optional[str] = "",
        time_limit_ms: Optional[int] = None,
        memory_limit_mb: Optional[int] = None,
        input_format: Optional[str] = "",
        output_format: Optional[str] = "",
    ) -> List[float]:
        """
        Extract ordered numerical feature list matching FEATURE_NAMES.
        """
        feat_dict = self.extract_features(
            statement=statement,
            constraints=constraints,
            time_limit_ms=time_limit_ms,
            memory_limit_mb=memory_limit_mb,
            input_format=input_format,
            output_format=output_format,
        )
        return [feat_dict[k] for k in self.FEATURE_NAMES]


structured_feature_extractor = StructuredFeatureExtractor()
