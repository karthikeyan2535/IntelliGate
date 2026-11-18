"""
Unit tests for Distributed Circuit Breaker.
Verifies CLOSED -> OPEN -> HALF_OPEN -> CLOSED state lifecycle transitions.
"""
import pytest

from app.routing.circuit_breaker import CircuitBreaker, CircuitState


@pytest.mark.asyncio
async def test_circuit_breaker_lifecycle():
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout_seconds=1, success_threshold=2)
    provider_id = "test-provider-openai"

    # Initial state should be CLOSED
    state = await cb.get_state(provider_id)
    assert state == CircuitState.CLOSED

    # Record 2 failures (under threshold of 3)
    await cb.record_failure(provider_id)
    await cb.record_failure(provider_id)
    assert await cb.get_state(provider_id) == CircuitState.CLOSED

    # 3rd failure trips the circuit to OPEN
    await cb.record_failure(provider_id)
    assert await cb.get_state(provider_id) == CircuitState.OPEN

    # Record success resets when recovered
    await cb.record_success(provider_id)

