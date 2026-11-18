# IntelliGate System Architecture

IntelliGate is an enterprise-grade multi-provider LLM gateway and AI infrastructure platform designed as a modular monolith adhering to high-throughput, low-latency, and multi-tenant isolation principles.

---

## 1. Architectural Planes

```
                     ┌────────────────────────────────────────┐
                     │          Clients & Applications        │
                     └───────────────────┬────────────────────┘
                                         │ (OpenAI SDK / HTTP)
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           A. DATA PLANE (Gateway Pipeline)                      │
│                                                                                 │
│   [1. Validation]  ──►  [2. Key Auth]  ──►  [3. Model Perms]  ──►  [4. Rate Lim] │
│                                                                           │     │
│   [8. Route Eval]  ◄──  [7. Exact Cache] ◄── [6. PII Redact] ◄── [5. Budget Res]│
│         │                                                                       │
│         ▼                                                                       │
│   [9. Provider Invocation] ──► [10. Failover/Retry] ──► [11. Normalization]     │
│                                                                   │             │
│   [14. Cache Store]  ◄──  [13. Telemetry Event]  ◄──  [12. Cost Reconcile]      │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
        ┌────────────────────────────────┴────────────────────────────────┐
        ▼                                                                 ▼
┌─────────────────────────────────┐           ┌───────────────────────────────────┐
│     B. CONTROL PLANE            │           │     C. OBSERVABILITY PLANE        │
│                                 │           │                                   │
│ • Virtual API Key Management    │           │ • OpenTelemetry Traces            │
│ • Upstream Provider Vault       │           │ • Prometheus Metrics (/metrics)   │
│ • Dynamic Routing Engine        │           │ • Grafana Dashboards              │
│ • Organization & Project RBAC   │           │ • Stage-by-Stage Request Inspector│
│ • Budget & Rate Limit Policies  │           │ • Structured JSON Audit Logs      │
└─────────────────────────────────┘           └───────────────────────────────────┘
```

---

## 2. The 21-Stage Ordered Pipeline

Every incoming chat completion request traverses an ordered sequence of stages:

1. **Request Validation**: Validates message payload against the OpenAI ChatML specification using Pydantic v2.
2. **Virtual Key Authentication**: Resolves `ig-...` bearer token against HMAC-SHA256 hash in database.
3. **Tenant & Project Resolution**: Scopes all operations strictly to the authenticated organization and project.
4. **Model Permission Check**: Ensures virtual key is authorized to access the requested model or alias.
5. **Rate-Limit Enforcement**: Sliding-window Redis Lua script checks RPM and TPM limits across Key, Project, and Org tiers.
6. **Token Quota Sizing**: Estimates input tokens with tiktoken/BPE before provider invocation.
7. **Atomic Budget Reservation**: Pre-allocates estimated upper-bound cost in Redis to guarantee no concurrent budget overspend.
8. **PII Detection & Redaction**: Scans prompts for Emails, SSNs, Credit Cards, IPs, and API keys with Presidio/Regex.
9. **Exact-Match Cache Lookup**: Computes canonical SHA-256 fingerprint; on HIT, settles budget to $0 and returns immediately in ~6ms.
10. **Model Alias Resolution**: Translates aliases (`fast-model`, `balanced-model`, `premium-model`) into prioritized candidate tuples.
11. **Routing Policy Evaluation**: Orders candidates via Priority, Lowest-Cost, Lowest-Latency, Weighted, or Health-Aware strategies.
12. **Circuit Breaker Check**: Bypasses any upstream provider whose circuit is in the `OPEN` state.
13. **Provider Invocation**: Dispatches request via HTTPX Async Client to OpenAI, Anthropic, Gemini, or custom endpoints.
14. **Exponential Retry**: Re-attempts transient failures (429, 500, 502, 503, 504, timeouts) with decorrelated jitter.
15. **Pre-Commit Streaming Fallback**: If streaming candidate fails before first chunk is delivered, seamlessly switches to fallback.
16. **Response Normalization**: Translates proprietary provider schemas into the standard OpenAI format.
17. **Post-Execution PII Inspection**: Optional sanitization on completion text.
18. **Precise Cost Calculation**: Calculates financial cost using Python Decimal arithmetic without floating-point error.
19. **Atomic Budget Settlement**: Commits actual cost and releases unused reserved funds atomically.
20. **Telemetry & Audit Persistence**: Records duration, stage timings, tokens, cost, and cache flags.
21. **Cache Population**: Writes deterministic completions to Redis with tenant-scoped isolation.

