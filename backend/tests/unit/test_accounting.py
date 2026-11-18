"""
Unit tests for Token Counting and Pricing Subsystem.
Verifies tiktoken heuristic, message framing overhead, and exact Decimal cost calculations.
"""
from decimal import Decimal
import pytest

from app.accounting.tokenizer import TokenCounter
from app.accounting.pricing import CostCalculator, PRICING_TABLE


def test_token_counter_text():
    text = "Hello world! This is IntelliGate testing token counting."
    count = TokenCounter.count_text(text, model="gpt-4o")
    assert count > 5
    assert count < 25


def test_token_counter_messages():
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": "Tell me a short joke."},
    ]
    count = TokenCounter.count_messages(messages, model="gpt-4o")
    # Message framing overhead (3 tokens per message + 3 priming) + content tokens
    assert count > 15


def test_cost_calculator_exact_decimal():
    # gpt-4o: $0.0025 per 1k input, $0.0100 per 1k output
    breakdown = CostCalculator.calculate_cost(
        provider="openai",
        model="gpt-4o",
        prompt_tokens=1000,
        completion_tokens=500,
    )

    expected_input = Decimal("0.00250000")
    expected_output = Decimal("0.00500000")
    expected_total = Decimal("0.00750000")

    assert breakdown.input_cost_usd == expected_input
    assert breakdown.output_cost_usd == expected_output
    assert breakdown.total_cost_usd == expected_total
    assert breakdown.total_tokens == 1500


def test_cost_calculator_cached_tokens():
    # gpt-4o: cached rate is $0.00125 per 1k
    breakdown = CostCalculator.calculate_cost(
        provider="openai",
        model="gpt-4o",
        prompt_tokens=1000,
        completion_tokens=200,
        cached_tokens=500,
    )

    # 500 uncached * 0.0025 / 1000 = 0.00125
    # 500 cached * 0.00125 / 1000 = 0.000625
    # Total input = 0.001875
    # Output: 200 * 0.01 / 1000 = 0.002
    # Total = 0.003875
    assert breakdown.input_cost_usd == Decimal("0.00187500")
    assert breakdown.output_cost_usd == Decimal("0.00200000")
    assert breakdown.total_cost_usd == Decimal("0.00387500")


def test_estimate_max_cost():
    max_cost = CostCalculator.estimate_max_cost(
        provider="openai",
        model="gpt-4o",
        estimated_prompt_tokens=2000,
        max_output_tokens=1000,
    )
    assert max_cost > Decimal("0.01")

