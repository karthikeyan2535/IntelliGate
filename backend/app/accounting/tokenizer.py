"""
Token counter with tiktoken support and fast fallback heuristics.
"""
from __future__ import annotations

import re
from typing import Any, Union
import structlog

logger = structlog.get_logger(__name__)

_ENCODER_CACHE: dict[str, Any] = {}


class TokenCounter:
    """High-throughput token counter for request sizing and cost forecasting."""

    @classmethod
    def get_encoder(cls, model: str) -> Any:
        if model in _ENCODER_CACHE:
            return _ENCODER_CACHE[model]
        try:
            import tiktoken
            if "gpt-4o" in model or "o1" in model or "o3" in model:
                enc = tiktoken.get_encoding("o200k_base")
            elif "gpt-3.5" in model:
                enc = tiktoken.get_encoding("cl100k_base")
            elif "claude" in model or "gemini" in model:
                # Approximation using cl100k_base which correlates strongly with BPE
                enc = tiktoken.get_encoding("cl100k_base")
            else:
                enc = tiktoken.get_encoding("cl100k_base")
            _ENCODER_CACHE[model] = enc
            return enc
        except Exception as exc:
            logger.debug("tiktoken not available, using heuristic fallback", error=str(exc))
            return None

    @classmethod
    def count_text(cls, text: str, model: str = "gpt-4o") -> int:
        if not text:
            return 0
        enc = cls.get_encoder(model)
        if enc is not None:
            try:
                return len(enc.encode(text))
            except Exception:
                pass
        # Robust heuristic fallback: ~4 characters per token for English/code
        # + split words to handle spaces and punctuation
        words = re.findall(r"\w+|[^\w\s]", text, re.UNICODE)
        return max(1, int(len(words) * 1.3))

    @classmethod
    def count_messages(cls, messages: list[dict[str, Any]], model: str = "gpt-4o") -> int:
        """
        Count tokens in ChatML / OpenAI message format, including per-message framing overhead.
        """
        num_tokens = 0
        # OpenAI Chat format overhead: ~3 tokens per message for role/content wrapper
        tokens_per_message = 3
        tokens_per_name = 1

        for msg in messages:
            num_tokens += tokens_per_message
            content = msg.get("content")
            if isinstance(content, str):
                num_tokens += cls.count_text(content, model)
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        num_tokens += cls.count_text(part.get("text", ""), model)
            if "name" in msg:
                num_tokens += tokens_per_name

        num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
        return num_tokens

