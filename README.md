# IntelliGate — Multi-Provider LLM Gateway & AI Infrastructure Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14.2+-black.svg?logo=next.js&logoColor=white)](https://nextjs.org)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg?logo=python&logoColor=white)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791.svg?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7.4-DC382D.svg?logo=redis&logoColor=white)](https://redis.io)
[![Tests](https://img.shields.io/badge/Tests-21%20Passed-success.svg)](https://pytest.org)

IntelliGate is a production-grade multi-provider LLM gateway and AI infrastructure platform. It provides a single, unified, OpenAI-compatible API to interact with OpenAI, Anthropic, Google Gemini, and local inference models with centralized model routing, distributed rate limiting, atomic cost governance, exact-match caching, PII redaction, and deep request tracing.

---

## Key Features

- **Unified OpenAI-Compatible API**: Seamless drop-in replacement (`/v1/chat/completions`, `/v1/models`). Works with any OpenAI SDK.
- **21-Stage Ordered Gateway Pipeline**: Request validation, key auth, rate-limiting, budget reservation, PII redaction, cache lookup, routing, retry/fallback, normalization, and settlement.
- **Provider Adapters**: Real adapters for **OpenAI**, **Anthropic**, **Google Gemini**, and generic **OpenAI-compatible** endpoints (Ollama, vLLM).
- **Intelligent Routing Engine**: Six routing strategies: Direct, Priority-Based, Weighted, Lowest-Cost, Lowest-Latency, and Health-Aware.
- **Reliability & Resilience**: Exponential backoff with decorrelated jitter, pre-commit streaming fallback, and 3-state Circuit Breakers (`CLOSED`, `OPEN`, `HALF_OPEN`).
- **Atomic Budget Governance**: Zero concurrent overspending via Redis Lua reservations; exact financial accounting using Python `Decimal`.
- **Distributed Rate Limiting**: Multi-tiered sliding window (Organization, Project, and Key RPM / TPM).
- **Security & PII Guardrails**: Microsoft Presidio and high-precision regex recognizers with `disabled`, `detect_only`, `redact`, and `block` policies.
- **Response Caching**: Deterministic SHA-256 fingerprinting with strict tenant isolation, achieving **307x speedup** on cache hits.
- **Next.js Developer Dashboard**: 12 responsive pages covering Overview, Virtual Keys, Providers, Models, Routing, Budgets, Guardrails, Cache, Analytics, Logs, Request Inspector, and Settings.
- **Stage-by-Stage Request Inspector**: Complete audit breakdown of execution timings per stage with zero prompt data leakage.

---

## Architecture Overview

```
Client / OpenAI SDK
         │
         ▼
[IntelliGate Data Plane]  ──►  1. Validation & Virtual Key Auth
         │               ──►  2. Rate Limiting (Redis Sliding Window)
         │               ──►  3. Atomic Budget Reservation (Redis Lua)
         │               ──►  4. PII Detection & Redaction
         │               ──►  5. Exact-Match Cache Lookup (Redis)
         │               ──►  6. Routing Engine & Circuit Breaker
         ▼
[Upstream Providers]     ──►  OpenAI | Anthropic | Gemini | Local vLLM
         │
         ▼
[Post-Processing]        ──►  7. Pre-commit Fallback Handling
                         ──►  8. Response Normalization to OpenAI Format
                         ──►  9. Decimal Cost Accounting & Budget Settlement
                         ──► 10. Cache Population & Telemetry Logging
```

---

## Quick Start

### 1. Using Docker Compose

```bash
cp .env.example .env
docker compose up -d
```
- Dashboard: [http://localhost:3000](http://localhost:3000)
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Prometheus: [http://localhost:9090](http://localhost:9090)
- Grafana: [http://localhost:3001](http://localhost:3001)

### 2. Local Manual Startup

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -e .
uvicorn app.main:app --reload --port 8000

# Frontend
cd ../frontend
npm install
npm run dev
```

---

## Verification & Testing

IntelliGate includes automated test suites covering unit, integration, and security checks:

```powershell
$env:PYTHONPATH = "E:\ai_pro\intelligate\backend"
pytest backend/tests -v
```

### Measured Benchmark Profile:
```powershell
python scripts/benchmark.py
```
- **Base Engine Latency**: `0.78 ms`
- **Cached Latency**: `6.04 ms` (**307x faster**)
- **Concurrency**: `183.4 req/sec` with **100% success rate** under load.

