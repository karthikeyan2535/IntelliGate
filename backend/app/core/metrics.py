"""
Prometheus metrics definitions for IntelliGate.
All counters, histograms, and gauges are defined here.
"""
from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram, Info

# ── App info ──────────────────────────────────────────────────────────────────
APP_INFO = Info(
    "intelligate_app",
    "IntelliGate application information",
)

# ── HTTP request metrics ───────────────────────────────────────────────────────
HTTP_REQUESTS_TOTAL = Counter(
    "intelligate_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "intelligate_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
)

HTTP_REQUESTS_IN_FLIGHT = Gauge(
    "intelligate_http_requests_in_flight",
    "HTTP requests currently being processed",
)

# ── Gateway / LLM request metrics ─────────────────────────────────────────────
GATEWAY_REQUESTS_TOTAL = Counter(
    "intelligate_gateway_requests_total",
    "Total LLM gateway requests",
    ["provider", "model", "status"],
)

GATEWAY_REQUEST_DURATION_SECONDS = Histogram(
    "intelligate_gateway_request_duration_seconds",
    "LLM gateway request duration in seconds",
    ["provider", "model"],
    buckets=[0.1, 0.25, 0.5, 1, 2, 5, 10, 30, 60, 120],
)

GATEWAY_TOKENS_TOTAL = Counter(
    "intelligate_gateway_tokens_total",
    "Total tokens processed",
    ["provider", "model", "type"],  # type: prompt | completion
)

GATEWAY_COST_USD_TOTAL = Counter(
    "intelligate_gateway_cost_usd_total",
    "Total cost in USD",
    ["provider", "model", "org_id"],
)

GATEWAY_STREAM_CHUNKS_TOTAL = Counter(
    "intelligate_gateway_stream_chunks_total",
    "Total streaming chunks received",
    ["provider", "model"],
)

# ── Provider health metrics ───────────────────────────────────────────────────
PROVIDER_HEALTH_STATUS = Gauge(
    "intelligate_provider_health_status",
    "Provider health status (1=healthy, 0=unhealthy)",
    ["provider", "region"],
)

PROVIDER_ERRORS_TOTAL = Counter(
    "intelligate_provider_errors_total",
    "Total provider errors",
    ["provider", "model", "error_type"],
)

PROVIDER_LATENCY_P99 = Histogram(
    "intelligate_provider_latency_p99_seconds",
    "Provider latency (p99) in seconds",
    ["provider"],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60],
)

# ── Cache metrics ─────────────────────────────────────────────────────────────
CACHE_HITS_TOTAL = Counter(
    "intelligate_cache_hits_total",
    "Cache hits",
    ["cache_type"],
)

CACHE_MISSES_TOTAL = Counter(
    "intelligate_cache_misses_total",
    "Cache misses",
    ["cache_type"],
)

# ── Rate limiting metrics ─────────────────────────────────────────────────────
RATE_LIMIT_HITS_TOTAL = Counter(
    "intelligate_rate_limit_hits_total",
    "Rate limit hits",
    ["key_id", "limit_type"],
)

# ── Budget metrics ────────────────────────────────────────────────────────────
BUDGET_USAGE_USD = Gauge(
    "intelligate_budget_usage_usd",
    "Current budget usage in USD",
    ["org_id", "policy_id"],
)

BUDGET_LIMIT_USD = Gauge(
    "intelligate_budget_limit_usd",
    "Budget limit in USD",
    ["org_id", "policy_id"],
)

# ── Auth metrics ──────────────────────────────────────────────────────────────
AUTH_ATTEMPTS_TOTAL = Counter(
    "intelligate_auth_attempts_total",
    "Authentication attempts",
    ["method", "status"],
)

# ── Active connections ────────────────────────────────────────────────────────
ACTIVE_STREAMING_CONNECTIONS = Gauge(
    "intelligate_active_streaming_connections",
    "Active streaming connections",
)


# ── Pipeline & Gateway standard metric aliases ────────────────────────────────
LLM_REQUEST_TOTAL = Counter(
    "intelligate_llm_requests_total",
    "LLM requests total",
    ["provider", "model", "status"],
)
LLM_REQUEST_DURATION_SECONDS = Histogram(
    "intelligate_llm_request_duration_seconds",
    "LLM request duration in seconds",
    ["provider", "model"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30],
)
LLM_TOKENS_TOTAL = Counter(
    "intelligate_llm_tokens_total",
    "LLM tokens total",
    ["provider", "model", "type"],
)
LLM_COST_TOTAL = Counter(
    "intelligate_llm_cost_usd_total",
    "Estimated LLM cost in USD total",
    ["provider", "model"],
)
RATE_LIMIT_REJECTIONS_TOTAL = Counter(
    "intelligate_rate_limit_rejections_total",
    "Rate limit rejections total",
)
BUDGET_REJECTIONS_TOTAL = Counter(
    "intelligate_budget_rejections_total",
    "Budget rejections total",
)
PII_DETECTIONS_TOTAL = Counter(
    "intelligate_pii_detections_total",
    "PII entities detected total",
    ["entity_type"],
)
CIRCUIT_BREAKER_STATE = Gauge(
    "intelligate_circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=half_open, 2=open)",
    ["provider"],
)
PROVIDER_HEALTH = Gauge(
    "intelligate_provider_health",
    "Provider health score (1=healthy, 0=unhealthy)",
    ["provider"],
)
