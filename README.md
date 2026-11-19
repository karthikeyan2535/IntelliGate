# IntelliGate: A Test-Aware LLM Router for Coding Tasks

IntelliGate is a verification-driven, multi-provider LLM routing platform designed specifically for competitive programming and software engineering tasks. It analyzes programming problems, selects models using empirical benchmark performance profiles, generates source code, verifies solutions through sandboxed execution, and escalates failed attempts to stronger models under configurable cost and latency constraints.

---

## 1. Core Technical Contribution & Identity

Unlike generic LLM API gateways or basic chat assistants, IntelliGate's core technical contribution is:
**Verification-Driven, Cost-Aware Model Selection and Escalation.**

### Primary Evaluation Metric
$$\text{Cost per Verified Accepted Solution} = \frac{\text{Total Inference Cost}}{\text{Number of Verified Solutions}}$$
Alongside:
- **Final Pass Rate (%)**
- **First-Attempt Pass Rate (Pass@1 %)**
- **Average Latency (ms)**
- **Escalation Rate (%)**

IntelliGate proves that task-specific routing combined with test-driven repair can achieve competitive accuracy comparable to frontier models (e.g., GPT-4o) at a **71% lower inference cost** (\$0.00118 vs \$0.00412 per verified solution).

---

## 2. Architecture & Pipeline Lifecycle

```
[ Problem Input ] -> [ Problem Analyzer ] -> [ Intelligent Router ]
  (CF/LC/Manual)        (Family & Bounds)       (Utility Optimization)
                                                          |
                                                    v
[ Trace & Audit ] <- [ Verification Engine ] <- [ Sandboxed Sandbox ] <- [ Code Generator ]
 (Attempts & Cost)     (Test Validation)       (C++17 / Python / Java)    (Structured Prompt)
                               |
                        (If Failed) -> [ Escalation Engine ] (Feedback to Next Model)
```

1. **Problem Ingestion**: Accepts manual input, structured test cases, or direct Codeforces / LeetCode problem URLs.
2. **Problem Analyzer**: Classifies task into algorithm families (`dynamic_programming`, `graphs`, `arrays_strings`, `trees_data_structures`, `greedy_binary_search`, `debugging_repair`) and estimates bounds.
3. **Intelligent Router**: Applies multi-objective utility scoring based on empirical category pass-rates, normalized cost, and latency budgets.
4. **Code Generation**: Prompts selected model with strict output schemas, ensuring raw source extraction without Markdown corruption.
5. **Secure Sandbox Execution**: Compiles (g++ / javac) and executes in an isolated temporary workspace with standard I/O redirection, enforcing 3.0s timeouts and memory limits.
6. **Verification Engine**: Classifies results (`accepted`, `wrong_answer`, `compilation_error`, `runtime_error`, `time_limit_exceeded`).
7. **Bounded Escalation**: If verification fails, feeds compiler diagnostics or failing inputs to the next eligible model, continuing until solved or budget exhausted.

---

## 3. Comparative Evaluation (Held-Out Benchmark Experiment)

On the **30-problem held-out test split** across all algorithmic domains, IntelliGate was evaluated against three baseline routing policies:

| Strategy | Final Pass Rate | First-Attempt (Pass@1) | Cost / Verified Sol. | Avg Cost / Problem | Avg Latency | Escalation Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **IntelliGate (Intelligent + Escalation)** | **86.7%** | **73.3%** | **$0.00118** | **$0.00102** | **380 ms** | **26.7%** |
| Baseline 1: Always Strongest (GPT-4o) | 90.0% | 83.3% | $0.00412 | $0.00371 | 680 ms | 10.0% |
| Baseline 2: Always Cheapest (Llama 8B) | 53.3% | 43.3% | $0.00032 | $0.00017 | 115 ms | 46.7% |
| Baseline 3: Static Category-Based | 76.7% | 66.7% | $0.00175 | $0.00134 | 410 ms | 20.0% |

**Key Finding:** IntelliGate achieves 96.3% of GPT-4o's accuracy (86.7% vs 90.0%) while cutting inference spend by **71.4%**.

---

## 4. Supported Languages & Sandbox Boundaries

- **C++17**: Compiled with `g++ -O2 -std=c++17`. Stdin/stdout redirection.
- **Python 3**: Executed in isolated subprocess with `-I` (isolated environment mode).
- **Java**: Compiled with `javac` and run with `java -Xmx256m`.

### Security & Isolation Boundaries
- Subprocess execution in dynamic isolated temporary directories (`intelligate_exec_*`).
- Absolute deletion of scratch workspaces upon completion.
- Configurable process timeouts (default 3.0 seconds) preventing runaway CPU loops.
- Capped output buffer (`MAX_OUTPUT_CHARS = 32768`) preventing memory exhaustion attacks.

---

## 5. Technology Stack

- **Frontend**: React 18, Vite, Tailwind CSS, Recharts, Lucide Icons (Pure JavaScript, no TypeScript).
- **Backend**: FastAPI, Pydantic 2.0, SQLAlchemy 2.0 (async), SQLite (aiosqlite) / PostgreSQL, Pytest.
- **Providers**: OpenAI (`gpt-4o`, `gpt-4o-mini`), Google Gemini (`gemini-1.5-flash`, `gemini-1.5-pro`), Groq (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`).

---

## 6. Local Quickstart

### Backend Setup
```bash
cd backend
python -m venv venv
# On Windows: venv\Scripts\Activate.ps1
# On Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 3000
```

- **Frontend Dashboard**: `http://localhost:3000`
- **Backend API & Swagger Docs**: `http://localhost:8000/docs`

### Running the Test Suite
```bash
cd backend
pytest tests -v
```
*(All 39 unit and integration tests passing).*
