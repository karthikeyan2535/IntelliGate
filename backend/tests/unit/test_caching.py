"""
Unit tests for Deterministic Exact-Match Response Caching.
Verifies SHA-256 fingerprint generation, tenant isolation, and cacheability evaluation.
"""
import pytest

from app.caching.cache_key import compute_cache_fingerprint
from app.caching.cache_manager import CacheManager


def test_cache_fingerprint_deterministic():
    messages = [{"role": "user", "content": "What is the speed of light?"}]
    fp1 = compute_cache_fingerprint(
        organization_id="org_12345",
        project_id="proj_abc",
        model="gpt-4o",
        messages=messages,
        temperature=0.0,
    )
    fp2 = compute_cache_fingerprint(
        organization_id="org_12345",
        project_id="proj_abc",
        model="gpt-4o",
        messages=messages,
        temperature=0.0,
    )
    assert fp1 == fp2
    assert fp1.startswith("cache:")


def test_tenant_isolation_in_cache_fingerprint():
    messages = [{"role": "user", "content": "Hello"}]
    fp_tenant_a = compute_cache_fingerprint(
        organization_id="tenant_a_123",
        project_id=None,
        model="gpt-4o",
        messages=messages,
    )
    fp_tenant_b = compute_cache_fingerprint(
        organization_id="tenant_b_456",
        project_id=None,
        model="gpt-4o",
        messages=messages,
    )
    # Cache keys MUST be different between tenants even with identical prompt
    assert fp_tenant_a != fp_tenant_b


def test_cacheable_criteria():
    req_deterministic = {"temperature": 0.0, "stream": False}
    resp_success = {"choices": [{"finish_reason": "stop"}]}
    assert CacheManager.is_cacheable(req_deterministic, resp_success) is True

    # Non-deterministic temperature > 0
    req_nondeterministic = {"temperature": 0.7, "stream": False}
    assert CacheManager.is_cacheable(req_nondeterministic, resp_success) is False

    # Streaming requests
    req_streaming = {"temperature": 0.0, "stream": True}
    assert CacheManager.is_cacheable(req_streaming, resp_success) is False

