# IntelliGate: A Test-Aware LLM Router for Coding Tasks

IntelliGate is a verification-driven, multi-provider LLM routing platform designed specifically for competitive programming and software engineering tasks. It analyzes programming problems, predicts continuous Codeforces difficulty ratings using Sentence-BERT embeddings and LightGBM quantile regression, selects models using empirical benchmark performance profiles, generates source code, verifies solutions through sandboxed execution, and escalates failed attempts to stronger models under configurable cost and latency constraints.

---

## 1. Core Technical Contribution & Identity

Unlike generic LLM API gateways or basic chat assistants, IntelliGate's core technical contribution is:
**Verification-Driven, Cost-Aware Model Selection, Machine-Learning Difficulty Quantile Estimation, and Test-Driven Escalation.**

### Primary Evaluation Metric
$$\text{Cost per Verified Accepted Solution} = \frac{\text{Total Inference Cost}}{\text{Number of Verified Solutions}}$$
Alongside:
- **Difficulty Prediction MAE & Spearman Rank Correlation ($\rho$)**
- **Quantile Prediction Interval Coverage (80% Nominal Target)**
- **Final Pass Rate (%) & Pass@1 (%)**
- **Average Latency (ms) & Escalation Rate (%)**

IntelliGate proves that semantic difficulty estimation combined with test-driven repair achieves competitive correctness comparable to frontier models (e.g., GPT-4o) at a **71% lower inference cost** ($0.00118 vs $0.00412 per verified solution).

---

## 2. Architecture & Pipeline Lifecycle

```
[ Problem Input ] ──> [ Sentence-BERT (384d) + Structured Features (24d) ]
  (CF/LC/Manual)                                │
                                                ▼
[ Intelligent Router ] <── [ LightGBM Quantile Prediction: Rating + 80% CI ]
  (Utility Optimization)
        │
        ▼
[ Code Generator ] ──> [ Secure Sandbox ] ──> [ Verification Engine ] ──> [ Solution Accepted ]
  (Structured Prompt)    (C++17 / Py / Java)     (Test Output Audit)
                                                        │ (If Failed)
                                                        ▼
                                              [ Escalation Engine ] (Failure Diagnostics -> Stronger Model)
```

1. **Problem Ingestion**: Accepts manual input, structured test cases, or direct Codeforces / LeetCode problem URLs.
2. **Machine-Learning Difficulty Estimation**:
   - **Semantic Features**: 384-dimensional dense semantic embeddings using frozen `sentence-transformers/all-MiniLM-L6-v2` with sliding-window chunking (200 words, 50-word overlap) and mean pooling.
   - **Structured Features**: 24 numerical constraint features including $\log_{10}(N)$, time/memory limits, math symbol density, modulo arithmetic indicators, and missing-value flags.
   - **LightGBM Quantile Models**: Estimates numerical rating (Median $\alpha=0.50$) and calibrated uncertainty bounds (Lower $\alpha=0.10$, Upper $\alpha=0.90$).
3. **Intelligent Router**: Evaluates candidate models via continuous probability estimation $P(\text{solve} \mid R_{\text{eff}}, m)$ and multi-objective Pareto scoring with risk-adjusted uncertainty weighting.
4. **Code Generation**: Prompts selected model with strict output schemas, ensuring raw source extraction without Markdown corruption.
5. **Secure Sandbox Execution**: Compiles (`g++` / `javac`) and executes in an isolated temporary workspace with standard I/O redirection, enforcing 3.0s timeouts and memory limits.
6. **Verification Engine**: Classifies results (`accepted`, `wrong_answer`, `compilation_error`, `runtime_error`, `time_limit_exceeded`).
7. **Bounded Escalation**: If verification fails, feeds compiler diagnostics or failing inputs to the next eligible model, continuing until solved or budget exhausted.

---

## 3. Machine-Learning Difficulty Prediction Benchmark

Trained and evaluated on **9,086 official Codeforces problems** chronologically split by contest into Training (6,360 problems), Validation/Calibration (1,362 problems), and Held-Out Test (1,364 problems):

| Model / Strategy | MAE | RMSE | Spearman Rho ($\rho$) | Tier Accuracy | 80% CI Coverage | Avg Interval Width |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **IntelliGate (Sentence-BERT + LightGBM)** | **494.8** | **600.3** | **0.6929** | **40.8%** | **78.5%** | **1759.4** |
| Baseline 2: Structured-Only LightGBM | 513.2 | 625.9 | 0.6689 | 42.6% | N/A | N/A |
| Baseline 1: Training Mean Predictor | 687.7 | 800.9 | 0.0000 | 18.5% | N/A | N/A |

### Output Contract
```json
{
  "predicted_rating": 1754,
  "lower_bound": 800,
  "upper_bound": 2508,
  "confidence_width": 1708,
  "difficulty_tier": "medium",
  "prediction_method": "sentence_bert_lightgbm"
}
```

---

## 4. End-to-End Routing Performance (Held-Out Benchmark Experiment)

On the **30-problem held-out test split** across all algorithmic domains, IntelliGate was evaluated against three baseline routing policies:

| Strategy | Final Pass Rate | First-Attempt (Pass@1) | Cost / Verified Sol. | Avg Cost / Problem | Avg Latency | Escalation Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **IntelliGate (Intelligent + Escalation)** | **86.7%** | **73.3%** | **$0.00118** | **$0.00102** | **380 ms** | **26.7%** |
| Baseline 1: Always Strongest (GPT-4o) | 90.0% | 83.3% | $0.00412 | $0.00371 | 680 ms | 10.0% |
| Baseline 2: Always Cheapest (Llama 8B) | 53.3% | 43.3% | $0.00032 | $0.00017 | 115 ms | 46.7% |
| Baseline 3: Static Category-Based | 76.7% | 66.7% | $0.00175 | $0.00134 | 410 ms | 20.0% |

**Key Finding:** IntelliGate achieves 96.3% of GPT-4o's accuracy (86.7% vs 90.0%) while cutting inference spend by **71.4%**.

---

## 5. Supported Languages & Sandbox Boundaries

- **C++17**: Compiled with `g++ -O2 -std=c++17`. Stdin/stdout redirection.
- **Python 3**: Executed in isolated subprocess with `-I` (isolated environment mode).
- **Java**: Compiled with `javac` and run with `java -Xmx256m`.

### Security & Isolation Boundaries
- Subprocess execution in dynamic isolated temporary directories (`intelligate_exec_*`).
- Absolute deletion of scratch workspaces upon completion.
- Configurable process timeouts (default 3.0 seconds) preventing runaway CPU loops.
- Capped output buffer (`MAX_OUTPUT_CHARS = 32768`) preventing memory exhaustion attacks.

---

## 6. Technology Stack

- **Machine Learning**: `lightgbm 4.7.0`, `sentence-transformers 6.3.0` (`all-MiniLM-L6-v2`), `torch 2.15.0`, `scikit-learn 1.9.1`, `pandas 3.1.1`, `numpy 2.5.5`.
- **Backend**: FastAPI, Pydantic 2.0, SQLAlchemy 2.0 (async), SQLite (aiosqlite) / PostgreSQL, Pytest.
- **Frontend**: React 18, Vite, Tailwind CSS, Recharts, Lucide Icons (Pure JavaScript, no TypeScript).
- **Providers**: OpenAI (`gpt-4o`, `gpt-4o-mini`), Google Gemini (`gemini-1.5-flash`, `gemini-1.5-pro`), Groq (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`).

---

## 7. Local Quickstart

### Backend Setup
```bash
cd backend
python -m venv venv
# On Windows: venv\Scripts\Activate.ps1
# On Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Run Model Evaluation
```bash
python app/analysis/ml_difficulty/evaluate.py
```

### Run Full Test Suite
```bash
pytest tests -v
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 3000
```
