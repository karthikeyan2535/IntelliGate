"""
Code Generation Service.
Constructs structured prompts with clear format guidelines, invokes LLM providers,
and reliably extracts pure compilable source code without Markdown corruption.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from app.providers.base import ProviderMessage, ProviderRequest
from app.providers.registry import provider_registry


@dataclass
class GenerationResult:
    code: str
    explanation: str
    time_complexity: str
    space_complexity: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    latency_ms: int
    model_id: str
    provider_name: str


class CodeGenerator:
    """
    Constructs language-specific coding prompts and ensures strict code extraction.
    """

    PRICING_PER_1K: Dict[str, Dict[str, float]] = {
        "llama-3.3-70b-versatile": {"input": 0.00059, "output": 0.00079},
        "llama-3.1-8b-instant": {"input": 0.00005, "output": 0.00008},
        "gemini-1.5-flash": {"input": 0.000075, "output": 0.00030},
        "gemini-1.5-pro": {"input": 0.00125, "output": 0.00500},
        "gpt-4o": {"input": 0.00250, "output": 0.01000},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.00060},
    }

    async def generate(
        self,
        model_id: str,
        provider_name: str,
        language: str,
        title: str,
        statement: str,
        constraints: Optional[str] = "",
        input_format: Optional[str] = "",
        output_format: Optional[str] = "",
        sample_cases: Optional[List[Dict[str, str]]] = None,
        previous_code: Optional[str] = None,
        failure_diagnostics: Optional[str] = None,
        is_leetcode_style: bool = False,
    ) -> GenerationResult:
        provider = provider_registry.get(provider_name)

        system_prompt = (
            f"You are a competitive programming specialist writing high-performance, bug-free {language.upper()} code. "
            "You MUST produce a complete, fully compilable solution that reads from standard input (stdin) "
            "and writes to standard output (stdout), unless instructed otherwise.\n"
            "Format your reply EXACTLY using this markdown layout:\n"
            "```" + language.lower() + "\n<YOUR_CODE_HERE>\n```\n"
            "### Explanation\n<Short explanation>\n"
            "### Complexity\n- Time Complexity: <e.g. O(n log n)>\n- Space Complexity: <e.g. O(1)>\n"
        )

        user_content = f"Problem Title: {title}\n\nProblem Statement:\n{statement}\n\n"
        if constraints:
            user_content += f"Constraints:\n{constraints}\n\n"
        if input_format:
            user_content += f"Input Format:\n{input_format}\n\n"
        if output_format:
            user_content += f"Output Format:\n{output_format}\n\n"

        if sample_cases:
            user_content += "Sample Examples:\n"
            for idx, c in enumerate(sample_cases[:3]):
                user_content += f"Example {idx+1}:\nInput:\n{c.get('input', '')}\nExpected Output:\n{c.get('expected', '')}\n"

        if previous_code and failure_diagnostics:
            user_content += (
                f"\n--- PREVIOUS ATTEMPT FAILED ---\n"
                f"Your previous solution failed verification with the following diagnostics:\n"
                f"{failure_diagnostics}\n\n"
                f"Previous Code:\n```{language.lower()}\n{previous_code}\n```\n\n"
                f"Carefully analyze this failure (e.g. off-by-one, integer overflow, TLE, or bad logic) "
                f"and provide the corrected, working {language.upper()} solution."
            )

        messages = [
            ProviderMessage(role="system", content=system_prompt),
            ProviderMessage(role="user", content=user_content),
        ]

        req = ProviderRequest(
            model=model_id,
            messages=messages,
            temperature=0.2,  # Low temperature for coding precision
            max_tokens=2048,
        )

        start_t = time.perf_counter()
        resp = await provider.chat_completion(req)
        latency_ms = int((time.perf_counter() - start_t) * 1000)

        raw_text = resp.content or ""
        code, explanation, time_comp, space_comp = self._extract_code_and_meta(raw_text, language)

        p_tok = resp.usage.prompt_tokens if resp.usage else int(len(user_content) / 4)
        c_tok = resp.usage.completion_tokens if resp.usage else int(len(raw_text) / 4)
        tot_tok = resp.usage.total_tokens if resp.usage else (p_tok + c_tok)

        # Calculate exact cost
        rates = self.PRICING_PER_1K.get(model_id, {"input": 0.0005, "output": 0.001})
        cost = (p_tok / 1000.0 * rates["input"]) + (c_tok / 1000.0 * rates["output"])

        return GenerationResult(
            code=code,
            explanation=explanation,
            time_complexity=time_comp,
            space_complexity=space_comp,
            prompt_tokens=p_tok,
            completion_tokens=c_tok,
            total_tokens=tot_tok,
            cost_usd=round(cost, 6),
            latency_ms=latency_ms,
            model_id=model_id,
            provider_name=provider_name,
        )

    def _extract_code_and_meta(self, raw_text: str, language: str) -> tuple[str, str, str, str]:
        # Regex match for code block ```language ... ```
        pattern = re.compile(rf"```(?:{language}|cpp|python|py|java|c\+\+)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
        match = pattern.search(raw_text)
        if match:
            code = match.group(1).strip()
        else:
            # Fallback to any triple-backtick block
            fb_match = re.search(r"```.*?\n(.*?)```", raw_text, re.DOTALL)
            code = fb_match.group(1).strip() if fb_match else raw_text.strip()

        # Extract explanation
        explanation = "Generated optimal algorithmic solution."
        exp_match = re.search(r"### Explanation\s*\n(.*?)(?:###|$)", raw_text, re.DOTALL)
        if exp_match:
            explanation = exp_match.group(1).strip()

        # Extract time complexity
        time_comp = "O(n)"
        tc_match = re.search(r"Time Complexity:\s*([^\n]+)", raw_text, re.IGNORECASE)
        if tc_match:
            time_comp = tc_match.group(1).strip()

        # Extract space complexity
        space_comp = "O(1)"
        sc_match = re.search(r"Space Complexity:\s*([^\n]+)", raw_text, re.IGNORECASE)
        if sc_match:
            space_comp = sc_match.group(1).strip()

        return code, explanation, time_comp, space_comp


code_generator = CodeGenerator()
