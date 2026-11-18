# IntelliGate — Evaluation-Driven Intelligent LLM Gateway

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-6.0-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg?logo=python&logoColor=white)](https://python.org)
[![Groq](https://img.shields.io/badge/Groq-LPU%20Inference-F05A28.svg)](https://groq.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-API-412991.svg?logo=openai&logoColor=white)](https://openai.com)
[![Gemini](https://img.shields.io/badge/Google-Gemini%20API-4285F4.svg?logo=google&logoColor=white)](https://ai.google.dev)
[![Tests](https://img.shields.io/badge/Tests-30%20Passed%20(100%25)-success.svg)](https://pytest.org)

**IntelliGate** is an evaluation-driven, production-ready Multi-Provider LLM Gateway designed for AI engineering environments. It provides a drop-in OpenAI-compatible API (`/v1/chat/completions`, `/v1/models`) that routes requests across **OpenAI**, **Google Gemini**, and **Groq**, driven by empirical benchmark performance rather than static rules.

---

## 🌟 Core Technical Differentiator: Evaluation-Driven Intelligent Routing

Most gateways route using naive hardcoded priority lists or round-robin balancing. IntelliGate treats routing as a **multi-objective optimization problem** calibrated by **live empirical benchmarks**:

```
Incoming Request
      │
      ▼
[Task Classifier & Complexity Estimator]
      ├── Categories: Coding | Reasoning | Writing | General Q&A
      └── Complexity: Simple | Moderate | Complex
      │
      ▼
[Capability Filter] ─── Check context window, circuit breaker state, availability
      │
      ▼
[Multi-Objective Utility Engine]
      └── Utility Score = (w_q · Quality) + (w_c · NormCost) + (w_l · NormLatency) + (w_r · Reliability)
      │   * Dynamic weights adapt to task complexity (e.g. 60% quality weight for complex logic)
      │
      ▼
[Optimal Model Execution + Fallback Chain]
      └── Returns OpenAI-compatible response + Transparent Routing Explanation
```

---

## 🚀 Key Features

### 1. Unified Multi-Provider Abstraction
- Standard drop-in OpenAI compatibility (`POST /v1/chat/completions`, `GET /v1/models`).
- Connects directly to **OpenAI** (`gpt-4o`, `gpt-4o-mini`), **Google Gemini** (`gemini-1.5-pro`, `gemini-1.5-flash`), and **Groq** (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`).
- Configured via clean environment variables (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`).
- Streaming response support with pre-commit fallback guarantee.

### 2. Intelligent Routing & Task Classification
- **Syntax and Semantics Analysis**: Analyzes prompt AST patterns, code block indicators, multi-part constraints, and technical markers to classify tasks into `coding`, `reasoning`, `writing`, and `general_qa`.
- **Constraint-Driven Complexity**: Distinguishes simple queries from deep algorithms independently of token count.
- **Three Routing Modes**:
  - `intelligent`: Optimizes quality-cost-latency Pareto frontier with dynamic complexity weights.
  - `lowest_cost`: Directs traffic to the cheapest qualified token provider.
  - `direct`: Pins execution to an explicitly requested model while maintaining gateway auditability.
- **Transparent Decision Reasoning**: Every response includes an understandable explanation of why a model was chosen along with candidate rankings.

### 3. Empirical Model Evaluation Framework
- **Curated 24-Prompt Benchmark Suite**: Spans code synthesis, formal inductive proofs, long-form creative writing, and factual lookups.
- **Deterministic & Pattern Verification**: Evaluates regex patterns, syntax validity, and expected key concepts without subjective hallucinations.
- **Live Profile Calibration**: Benchmark runs immediately update in-memory profiles, feeding directly back into the live routing engine.

### 4. High-Performance Reliability & Governance
- **Exact-Match Response Caching**: Deterministic SHA-256 fingerprinting with tenant isolation, delivering **133x latency speedup** on cache hits.
- **Resilient Circuit Breaker**: 3-state protection (`CLOSED`, `OPEN`, `HALF_OPEN`) preventing cascading failures.
- **High-Precision Financial Accounting**: Exact token tracking and decimal cost calculations using Python `Decimal`.
- **Zero-Data-Leakage PII Guardrails**: Pre-request scanning and automated redaction for emails, SSNs, API keys, and IP addresses.

### 5. Modern Vite + React Dashboard
- Built with **React 18 + Vite + Tailwind CSS + Recharts** (pure JavaScript).
- **Overview**: Real-time KPI ribbons, request volume trends, task category distribution (PieChart), and model breakdown.
- **LLM Playground**: Interactive prompt execution with instant response rendering and detailed **Routing Explanation Cards** showing candidate score breakdowns.
- **Model Performance**: Empirical benchmark score matrix across all models with one-click live evaluation triggers.
- **Request History**: Deep audit trail with execution trace modal showing pipeline timings per stage.

---

## 📊 Benchmark & Performance Profile

Results from `scripts/benchmark.py` running automated load testing:

| Metric | Measured Result |
| :--- | :--- |
| **Base Engine Latency (`/health`)** | **1.16 ms / req** |
| **Full Pipeline Cold Latency** | ~2.0 s (Model invocation + PII + Routing) |
| **Cached Request (Exact Match HIT)** | **14.97 ms (133.8x speedup)** |
| **Concurrent Pipeline Throughput** | **53.1 req / sec** (50 concurrent requests, 100% success) |
| **PII Multi-Entity Redaction Overhead**| **0.366 ms / payload** |
| **Intelligent Routing Decision Latency**| **0.382 ms** (Classification: 0.173 ms) |

---

## 🛠️ Quick Start

### 1. Prerequisites
- Python 3.12 or 3.13
- Node.js 18+ and npm
- PostgreSQL and Redis (optional; gateway gracefully uses SQLite/in-memory fallback for local dev)

### 2. Backend Setup
```bash
# Clone the repository
git clone https://github.com/karthikeyan2535/IntelliGate.git
cd IntelliGate/backend

# Create virtual environment & install dependencies
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt

# Configure environment keys
cp ../.env.example ../.env
# Edit .env with your OPENAI_API_KEY, GEMINI_API_KEY, and GROQ_API_KEY

# Run test suite
pytest tests -v

# Start FastAPI gateway
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup
```bash
cd ../frontend

# Install dependencies and start Vite dev server
npm install
npm run dev
# Dashboard opens at http://localhost:3000
```

---

## 📡 OpenAI-Compatible API Usage

You can use the official `openai` Python SDK or `curl` directly:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="ig-playground-virtual-key-demo",
)

# Intelligent evaluation-driven routing
response = client.chat.completions.create(
    model="intelligent",  # or "gpt-4o", "lowest_cost", "llama-3.3-70b-versatile"
    messages=[
        {"role": "user", "content": "Write an async Python function to parse JSON with error handling."}
    ],
    temperature=0.7,
)

print("Assistant:", response.choices[0].message.content)
```

Response headers returned by IntelliGate:
```http
X-IntelliGate-Request-ID: req_a1b2c3d4e5f6
X-IntelliGate-Provider: groq
X-IntelliGate-Model: llama-3.3-70b-versatile
X-IntelliGate-Task-Category: coding
X-IntelliGate-Complexity: complex
X-IntelliGate-Routing-Mode: intelligent
X-IntelliGate-Cost-USD: 0.000182
X-IntelliGate-Cache: MISS
```

---

## 🧪 Test Suite

Run the complete test suite verifying classification, multi-objective utility scoring, circuit breakers, caching, and financial accounting:

```bash
pytest backend/tests -v
```

Output:
```
============================= 30 passed in 4.33s ==============================
```

---

## 📜 License
MIT License. Built for production LLM operations and AI engineering intern portfolio presentation.
