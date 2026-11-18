# IntelliGate — Evaluation-Driven Multi-Provider LLM Gateway

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-6.0-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg?logo=python&logoColor=white)](https://python.org)
[![Groq](https://img.shields.io/badge/Groq-LPU%20Inference-F05A28.svg)](https://groq.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-API-412991.svg?logo=openai&logoColor=white)](https://openai.com)
[![Gemini](https://img.shields.io/badge/Google-Gemini%20API-4285F4.svg?logo=google&logoColor=white)](https://ai.google.dev)
[![Tests](https://img.shields.io/badge/Tests-30%20Passed%20(100%25)-success.svg)](https://pytest.org)

**IntelliGate** is an evaluation-driven, production-grade LLM Gateway and Routing Platform designed for AI engineering environments. It provides a drop-in OpenAI-compatible API (`POST /v1/chat/completions`, `GET /v1/models`) that routes incoming requests across **OpenAI**, **Google Gemini**, and **Groq** based on empirical benchmark capability and operational metrics rather than hardcoded heuristics.

---

## 🌟 Architecture & Core Concept

Unlike conventional gateways that rely on static priority lists or random fallbacks, IntelliGate executes a multi-stage routing pipeline powered by closed-loop empirical evaluations:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Incoming Client Request                         │
│             (OpenAI Chat Completion Protocol or UI Playground)         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 Task Classifier & Complexity Estimator                 │
│  - Categories: Coding, Reasoning, Writing, General Q&A                 │
│  - Complexity: Simple, Moderate, Complex (depth & constraint based)    │
│  - Manual Overrides: Optional x-override-category / complexity headers │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     Hard Eligibility & Quality Gate                    │
│  - Context Window check (Required Tokens <= Model Window)              │
│  - Circuit Breaker check (State != OPEN)                               │
│  - Quality Gating: Q_task(m) >= Q_min(complexity)                     │
│    • Complex: 0.88   • Moderate: 0.80   • Simple: 0.70                │
│  * Failing models appended to Rejected Candidates Log with reason      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     Linear Multi-Objective Utility                     │
│       U(m) = w_q · Q(m) + w_c · C(m) + w_l · L(m) + w_r · R(m)         │
│  - Quality Q(m): Empirical score on detected category                  │
│  - Cost C(m): Natural log-scaled inverted token pricing                │
│  - Latency L(m): Min-max inverted P50 response time                   │
│  - Reliability R(m): Operational success rate                          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 Provider Invocation & Audit Recording                  │
│  - Resilient adapter execution (OpenAI / Groq / Gemini)                │
│  - Exact financial accounting (Decimal-precision token cost)          │
│  - Async persistence to PostgreSQL audit log & trace inspector         │
│  - Non-blocking empirical feedback loop into ProfileManager            │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📐 Mathematical Routing Engine

### 1. Task-Specific Quality Gating
Before scoring candidates, IntelliGate enforces hard quality thresholds to guarantee task suitability:

$$\text{Threshold}(c) = \begin{cases} 
0.88 & \text{if } c = \text{Complex} \\ 
0.80 & \text{if } c = \text{Moderate} \\ 
0.70 & \text{if } c = \text{Simple} 
\end{cases}$$

Models with $Q_{\text{task}}(m) < \text{Threshold}(c)$ are eliminated and logged into `rejected_candidates` with explicit rationales (e.g., `Quality 0.82 < 0.88 threshold for complex coding`).

### 2. Normalized Linear Utility Scoring
Every eligible candidate is evaluated via a transparent linear utility function:

$$U(m) = w_q \cdot Q_{\text{task}}(m) + w_c \cdot C(m) + w_l \cdot L(m) + w_r \cdot R(m)$$

#### Dynamic Complexity Weights
The weights dynamically adapt to the cognitive demands of the task:

| Complexity | Quality Weight ($w_q$) | Cost Weight ($w_c$) | Latency Weight ($w_l$) | Reliability Weight ($w_r$) |
| :--- | :---: | :---: | :---: | :---: |
| **Complex** | `0.60` | `0.15` | `0.15` | `0.10` |
| **Moderate** | `0.40` | `0.30` | `0.20` | `0.10` |
| **Simple** | `0.20` | `0.45` | `0.25` | `0.10` |

#### Feature Normalization
- **Cost Normalization** (Log-scaled to balance orders of magnitude without utility skew):
  $$C(m) = 1 - \frac{\ln(1 + \text{Cost}(m)) - \ln(1 + C_{min})}{\ln(1 + C_{max}) - \ln(1 + C_{min})}$$
- **Latency Normalization** (Min-max linear inversion):
  $$L(m) = 1 - \frac{\text{Latency}(m) - L_{min}}{L_{max} - L_{min}}$$

---

## 🔬 Benchmark Framework & Live Feedback Loop

IntelliGate includes a deterministic 24-prompt benchmark suite spanning:
1. **Code Synthesis**: Python AST parseability, algorithm correctness, exception handling.
2. **Formal Reasoning**: Step-by-step logic puzzles, mathematical induction, constraint validation.
3. **Structured Writing**: Tone matching, format adherence, Markdown compliance.
4. **General Q&A**: Factual extraction, deterministic entity verification.

### Closed-Loop Architecture
When you trigger **Run Eval** in the UI:
1. The model is executed against deterministic test prompts at `temperature=0.0`.
2. Structured output assertions and regex patterns grade pass/fail without subjective bias.
3. Pass rates and latencies are recorded in PostgreSQL (`EvaluationRecord`).
4. The measured scores **immediately mutate the in-memory `ProfileManager`**, recalibrating subsequent live routing choices in real time.

---

## 💻 Developer Workbench Dashboard

Built as a lightweight, clean developer workbench (Linear/Datadog aesthetic) with pure JavaScript, React 18, Vite, Tailwind CSS, and Recharts:

- **1. Overview**: Real-time KPI ribbons, request volume trends, task category distribution pie chart, and live DB-backed model request breakdown.
- **2. Interactive Playground**:
  - Live prompt editor with configurable System Prompt, User Prompt, Temperature, and Max Tokens.
  - Manual override selectors for Task Category and Complexity.
  - Telemetry ribbon displaying `RESOLVED MODEL`, `ROUNDTRIP LATENCY`, `TOKEN BREAKDOWN`, `CACHE STATUS`, and `EXACT COST ($USD)`.
  - Transparent Decision Card displaying applied weights, candidate rankings with `$/1K` pricing, and a **Rejected Candidates Log** with exact exclusion reasons.
- **3. Model Performance**:
  - Empirical model capability matrix with category quality scores ($Q_c, Q_r, Q_w, Q_{qa}$), P50 latency, and pricing.
  - Interactive Recharts bar chart comparing model quality across domains.
  - Empirical benchmark run history with a detailed **Run Inspector Modal** displaying itemized test results and outputs.
- **4. Request History**:
  - Searchable, filterable audit log (by Model, Status, and Cache Hit/Miss).
  - Step-by-step Distributed Trace Inspector displaying pipeline stage durations and security redactions.

---

## 🚀 Quick Start

### Option A: Local Development Setup

#### 1. Backend
```bash
# Clone the repository
git clone https://github.com/karthikeyan2535/IntelliGate.git
cd IntelliGate/backend

# Create virtual environment & install dependencies
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt

# Configure environment keys (.env in repo root or backend)
# Set OPENAI_API_KEY, GEMINI_API_KEY, GROQ_API_KEY

# Run unit & integration test suite
pytest tests -v

# Start FastAPI server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend
```bash
cd ../frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev -- --host 0.0.0.0
# Access dashboard at http://localhost:3000
```

### Option B: Docker Compose
```bash
# Run full stack with PostgreSQL, Redis, Prometheus & Grafana
docker compose up -d --build

# Backend: http://localhost:8000
# Frontend Dashboard: http://localhost:3000
# Health Check: http://localhost:8000/health
```

---

## 📡 OpenAI-Compatible API Usage

IntelliGate accepts standard OpenAI SDK requests:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="ig-playground-virtual-key-demo",
)

# Intelligent evaluation-driven routing
response = client.chat.completions.create(
    model="intelligent",  # or "lowest_cost", "gpt-4o", "llama-3.3-70b-versatile"
    messages=[
        {"role": "system", "content": "You are an expert algorithms engineer."},
        {"role": "user", "content": "Implement an LRU Cache in Python with O(1) get and put."}
    ],
    temperature=0.2,
    max_tokens=600,
)

print(response.choices[0].message.content)
```

### Inspecting Routing Headers
Every response from IntelliGate includes audit headers:
```http
X-IntelliGate-Request-ID: 7a9e2f41-0b3c-4d5e-8f1a-9c2b3d4e5f60
X-IntelliGate-Provider: groq
X-IntelliGate-Model: llama-3.3-70b-versatile
X-IntelliGate-Task-Category: coding
X-IntelliGate-Complexity: complex
X-IntelliGate-Routing-Mode: intelligent
X-IntelliGate-Cost-USD: 0.000185
X-IntelliGate-Cache: MISS
```

---

## 🧪 Verification & Test Suite

All 30 unit and integration tests verify the pipeline, routing algebra, circuit breakers, security filters, and financial accounting:

```bash
pytest backend/tests -v
```

Test Results:
- `test_models_endpoint_authorized` & `test_models_endpoint_unauthorized`: PASSED
- `test_chat_completions_non_streaming`: PASSED
- `test_chat_completions_pii_redaction`: PASSED
- `test_token_counter_exact` & `test_cost_calculator_exact_decimal`: PASSED
- `test_caching_deterministic_fingerprint`: PASSED
- `test_circuit_breaker_lifecycle`: PASSED
- `test_classifier_detection`: (Coding, Reasoning, Writing, General Q&A) PASSED
- `test_intelligent_routing_complex_task` & `test_simple_task`: PASSED
- `test_profile_manager_empirical_update`: PASSED
- `test_pii_guardrails`: (Email, API Key, IP Address Redaction) PASSED

---

## 📄 License
MIT License. Built for production LLM operations and AI engineering intern portfolio presentation.
