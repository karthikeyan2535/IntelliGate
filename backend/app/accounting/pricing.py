"""
Versioned pricing matrix and cost calculation subsystem for IntelliGate.
Uses Python Decimal for exact financial calculations without floating point errors.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)

# Rates per 1,000 tokens (USD)
# Updated with current provider pricing tables
PRICING_TABLE: dict[str, dict[str, dict[str, Decimal]]] = {
    "openai": {
        "gpt-4o": {
            "input": Decimal("0.0025"),
            "output": Decimal("0.0100"),
            "cached_input": Decimal("0.00125"),
        },
        "gpt-4o-mini": {
            "input": Decimal("0.00015"),
            "output": Decimal("0.00060"),
            "cached_input": Decimal("0.000075"),
        },
        "gpt-4-turbo": {
            "input": Decimal("0.0100"),
            "output": Decimal("0.0300"),
        },
        "o1": {
            "input": Decimal("0.0150"),
            "output": Decimal("0.0600"),
        },
        "o3-mini": {
            "input": Decimal("0.0011"),
            "output": Decimal("0.0044"),
        },
    },
    "anthropic": {
        "claude-3-5-sonnet-20241022": {
            "input": Decimal("0.0030"),
            "output": Decimal("0.0150"),
            "cached_input": Decimal("0.0003"),
        },
        "claude-3-5-haiku-20241022": {
            "input": Decimal("0.0008"),
            "output": Decimal("0.0040"),
            "cached_input": Decimal("0.00008"),
        },
        "claude-3-opus-20240229": {
            "input": Decimal("0.0150"),
            "output": Decimal("0.0750"),
        },
    },
    "gemini": {
        "gemini-1.5-pro": {
            "input": Decimal("0.00125"),
            "output": Decimal("0.0050"),
            "cached_input": Decimal("0.0003125"),
        },
        "gemini-1.5-flash": {
            "input": Decimal("0.000075"),
            "output": Decimal("0.00030"),
            "cached_input": Decimal("0.00001875"),
        },
        "gemini-2.0-flash": {
            "input": Decimal("0.00010"),
            "output": Decimal("0.00040"),
        },
    },
    "mistral": {
        "mistral-large-latest": {
            "input": Decimal("0.0020"),
            "output": Decimal("0.0060"),
        },
        "mistral-small-latest": {
            "input": Decimal("0.0002"),
            "output": Decimal("0.0006"),
        },
    },
    "default": {
        "default": {
            "input": Decimal("0.0015"),
            "output": Decimal("0.0045"),
        }
    },
}


@dataclass
class CostBreakdown:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    input_cost_usd: Decimal
    output_cost_usd: Decimal
    total_cost_usd: Decimal
    is_estimated: bool = False


class CostCalculator:
    """Calculates exact financial cost for completions using versioned pricing tables."""

    @classmethod
    def get_rates(cls, provider: str, model: str) -> dict[str, Decimal]:
        prov_key = provider.lower()
        if prov_key in PRICING_TABLE:
            models = PRICING_TABLE[prov_key]
            # Exact match
            if model in models:
                return models[model]
            # Partial match (e.g. gpt-4o-2024-08-06 matches gpt-4o)
            for m_key, rates in models.items():
                if m_key in model or model in m_key:
                    return rates

        # Generic fallback
        return PRICING_TABLE["default"]["default"]

    @classmethod
    def calculate_cost(
        cls,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cached_tokens: int = 0,
        custom_input_cost_per_1k: Optional[Decimal] = None,
        custom_output_cost_per_1k: Optional[Decimal] = None,
    ) -> CostBreakdown:
        rates = cls.get_rates(provider, model)

        input_rate = custom_input_cost_per_1k or rates.get("input", Decimal("0.001"))
        output_rate = custom_output_cost_per_1k or rates.get("output", Decimal("0.002"))
        cached_rate = rates.get("cached_input", input_rate * Decimal("0.5"))

        uncached_prompt = max(0, prompt_tokens - cached_tokens)
        input_cost = (
            (Decimal(uncached_prompt) * input_rate / Decimal(1000)) +
            (Decimal(cached_tokens) * cached_rate / Decimal(1000))
        )
        output_cost = Decimal(completion_tokens) * output_rate / Decimal(1000)

        total_cost = (input_cost + output_cost).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)

        return CostBreakdown(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            input_cost_usd=input_cost.quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP),
            output_cost_usd=output_cost.quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP),
            total_cost_usd=total_cost,
            is_estimated=False,
        )

    @classmethod
    def estimate_max_cost(
        cls,
        provider: str,
        model: str,
        estimated_prompt_tokens: int,
        max_output_tokens: Optional[int] = None,
    ) -> Decimal:
        """Conservative upper bound estimate for budget reservation before execution."""
        max_out = max_output_tokens if max_output_tokens and max_output_tokens > 0 else 2048
        # Cap excessive max output token requests to realistic upper bound for reservation
        max_out = min(max_out, 8192)
        breakdown = cls.calculate_cost(
            provider=provider,
            model=model,
            prompt_tokens=estimated_prompt_tokens,
            completion_tokens=max_out,
        )
        return breakdown.total_cost_usd

