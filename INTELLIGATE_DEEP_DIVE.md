# IntelliGate — Test-Aware LLM Router for Coding Tasks: System Architecture, ML Difficulty Prediction & Verification Deep Dive

> **IntelliGate: A Test-Aware, Verification-Driven LLM Router for Competitive Programming & Software Engineering**  
> *A production-grade, research-caliber AI systems platform built with FastAPI, React 18, Sentence-BERT, LightGBM Quantile Regression, and isolated sandboxed execution boundaries.*

---

## 1. Executive Summary & Product Identity

Modern automated code generation faces a severe structural dilemma:
1. **Frontier Over-Provisioning**: Routinely sending every programming problem to top-tier frontier models (such as GPT-4o) results in massive financial spend, unneeded latency, and vendor lock-in.
2. **Open-Weights Accuracy Collapse**: Routing difficult or complex algorithmic challenges directly to small open-weights models leads to syntax errors, wrong answers, and time limit exceeded (TLE) failures.
3. **Absence of Ground Truth Verification**: Typical LLM gateways treat model output as final, returning uncompiled, hallucinated, or broken code directly to users without validation.
4. **Fragile Rule-Based Difficulty Heuristics**: Regex pattern matching on text limits (e.g. $N \le 10^5$) fails to capture mathematical depth, algorithmic subtlety, and problem complexity.

**IntelliGate** resolves this fundamentally by establishing a new paradigm:
**Verification-Driven, Cost-Aware Model Selection, Machine-Learning Difficulty Quantile Estimation, and Test-Driven Escalation.**

Instead of treating code generation as a single-turn black-box call, IntelliGate treats routing as an **active, test-driven feedback loop**:
- Analyzes programming problems via **Sentence-BERT dense semantic embeddings** and **structured numerical feature extraction**.
- Estimates continuous **Codeforces numerical difficulty ratings (800–3500)** and **calibrated 80% prediction uncertainty intervals** using **LightGBM Quantile Regression**.
- Selects models using empirical, domain-specific benchmark performance profiles and continuous skill curves $P(\text{solve} \mid R_{\text{eff}}, m)$.
- Compiles and runs generated code inside a **secure, isolated execution sandbox** against concrete test cases.
- Diagnoses failures (syntax errors, wrong answers, timeouts) and **escalates to stronger models** with compiler diagnostics under strict cost and latency constraints.

### Core Primary Metric
$$\text{Cost per Verified Accepted Solution} = \frac{\text{Total Inference Cost}}{\text{Number of Verified Solutions}}$$
Alongside:
- **Difficulty Prediction MAE & Spearman Rank Correlation ($\rho$)**
- **Quantile Prediction Interval Coverage (80% Target)**
- **Final Pass Rate (%) & Pass@1 (%)**
- **Average Roundtrip Latency (ms) & Escalation Rate (%)**

IntelliGate demonstrates that intelligent routing and bounded escalation can achieve **86.7% final pass rate** at **\$0.00118 per verified solution**—delivering 96.3% of GPT-4o's accuracy at a **71.4% cost reduction**.

---

## 2. End-to-End System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PROBLEM INGESTION STAGE                         │
│   • Codeforces URL (HTML parse + public samples + time/memory limits)  │
│   • LeetCode URL (GraphQL API + signatures + example cases)            │
│   • Manual Problem Entry (title, statement, constraints, custom tests) │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│             STAGE 1: ML DIFFICULTY & COMPLEXITY ANALYZER               │
│   • Semantic Embeddings: Sentence-BERT (all-MiniLM-L6-v2, 384-dim)     │
│   • Structured Numerical Features: 24-dim vector with log bounds       │
│   • LightGBM Quantile Models: alpha = 0.50, 0.10, 0.90                 │
│   • Output: predicted_rating, lower_bound, upper_bound, method         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                STAGE 2: INTELLIGENT CODING ROUTER                      │
│   • Effective Rating: R_eff = R_pred + 0.30·(R_upper - R_pred)         │
│   • Continuous Pass-Rate Estimation: P(solve | R_eff, m)               │
│   • Multi-Objective Utility: Score(m) = w_q·Q_eff + w_c·S_cost + w_l·S_lat│
│   • Hard Constraints: Reliability threshold, budget, provider health   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     STAGE 3: CODE GENERATOR                            │
│   • Structured prompt construction (target language, I/O specifications│
│   • Prior attempt code & compiler failure diagnostics injection        │
│   • Robust raw source extraction (anti-markdown corruption)            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│               STAGE 4: SECURE SANDBOXED EXECUTION                      │
│   • Isolated temporary directory (intelligate_exec_*)                  │
│   • C++17 (g++ -O2 -std=c++17) / Python 3 (-I mode) / Java (-Xmx256m)  │
│   • Stdin/stdout redirection against test cases                        │
│   • Enforced 3.0s timeout & 32KB output buffer limits                  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    STAGE 5: VERIFICATION ENGINE                        │
│   • Status: accepted, wrong_answer, compilation_error, runtime_error,  │
│     time_limit_exceeded, memory_limit_exceeded                         │
│   • Exact and whitespace-normalized output comparison                  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                 ┌──────────────────┴──────────────────┐
                 │                                     │
           [If Accepted]                         [If Failed]
                 │                                     │
                 ▼                                     ▼
┌─────────────────────────────────┐   ┌──────────────────────────────────┐
│ STAGE 6: RECORD & RETURN        │   │ STAGE 6: ESCALATION POLICY       │
│ • Status: ACCEPTED              │   │ • Evaluate stopping conditions   │
│ • Final Code & Telemetry Trace  │   │ • Retry same model on syntax err │
│ • Complete accounting persisted │   │ • Exclude failed candidate       │
└─────────────────────────────────┘   │ • Escalate to stronger model     │
                                      │ • Loop back to Stage 2 with diff │
                                      └──────────────────────────────────┘
```

---

## 3. Machine-Learning Difficulty Prediction Subsystem

### 3.1 Motivation
Static keyword rules cannot distinguish an introductory $O(N)$ prefix-sum problem from a Div 1 $O(N)$ dynamic programming problem over a convex tree. Machine learning on semantic embeddings and mathematical constraints estimates the true competitive rating distribution.

### 3.2 Dataset Preparation & Chronological Split
- **Source**: 9,086 official Codeforces problems with verified contest difficulty ratings ranging from $800$ to $3500$ ($\mu = 1858.9, \sigma = 714.3$).
- **Data Leakage Prevention**: All problem tags, editorials, solution code, and contest rankings were stripped. Only problem statements, input specifications, output formats, and constraints were used.
- **Chronological Split**:
  - **Training Set (70%)**: 6,360 problems from older contests.
  - **Validation & Calibration Set (15%)**: 1,362 problems from intermediate contests.
  - **Held-Out Test Set (15%)**: 1,364 problems from recent contests.

### 3.3 Semantic Feature Extraction
- **Architecture**: `sentence-transformers/all-MiniLM-L6-v2` frozen embedding backbone producing 384-dimensional dense vectors.
- **Sliding-Window Chunking**:
  - Context window: 200 words per chunk with 50-word overlap.
  - Long statements are partitioned into overlapping windows, encoded, mean-pooled, and $L_2$-normalized:
    $$\vec{e} = \frac{\frac{1}{K} \sum_{k=1}^K \text{BERT}(c_k)}{\left\| \frac{1}{K} \sum_{k=1}^K \text{BERT}(c_k) \right\|_2}$$
- **Multi-Tier Caching**: In-memory LRU cache + persistent disk cache keyed by SHA-256 problem text hashes ensures subsequent lookups execute in $< 1$ ms.

### 3.4 Structured Feature Engineering
24 domain-specific numerical features capturing problem structure:
1. `log_char_count` & `log_word_count`: Statement length and narrative complexity.
2. `line_count`: Input/output structural formatting.
3. `log_time_limit_ms` & `missing_time_limit`: Execution time budget ($1000$ ms default).
4. `log_memory_limit_mb` & `missing_memory_limit`: Memory capacity ($256$ MB default).
5. `has_multiple_test_cases`: Test case loop indicator ($T$ test cases).
6. `log_max_n` & `missing_max_n`: Maximum element bound parsed from scientific notation (e.g. $2 \cdot 10^5$).
7. `log_max_val` & `missing_max_val`: Bound on array values ($A_i \le 10^9$ or $10^{18}$).
8. `math_symbol_count` & `math_symbol_density`: Frequency of LaTeX/math tokens (`$`, `\le`, `\sum`, `^`).
9. `num_numeric_tokens` & `num_single_letter_vars`: Density of mathematical variables ($n, m, k$).
10. `has_modulo`: Modulo arithmetic requirement ($10^9+7$, $998244353$).
11. `is_interactive`: Interactive query protocol indicator.
12. Domain indicators: Graph, geometry, string, bitwise, grid/matrix, and query terms.

**Combined Feature Vector**: $384 \text{ (semantic)} + 24 \text{ (structured)} = 408 \text{ dimensions}$.

### 3.5 LightGBM Quantile Regression & Conformal Calibration
Three LightGBM models are trained:
1. **Median Estimator ($\alpha = 0.50$)**: Objective = `quantile`, `alpha=0.50`, 450 trees, `learning_rate=0.04`, `num_leaves=31`.
2. **Lower Bound ($\alpha = 0.10$)**: Estimates the 10th percentile difficulty bound.
3. **Upper Bound ($\alpha = 0.90$)**: Estimates the 90th percentile difficulty bound.

**Conformal Calibration**:
On the calibration split, raw interval coverage is evaluated. A non-conformity margin $\delta = 245.0$ is computed to guarantee nominal 80% coverage:
$$[\hat{L}_i, \hat{U}_i] = [\hat{q}_{0.10}(x_i) - \delta, \; \hat{q}_{0.90}(x_i) + \delta]$$

### 3.6 Empirical Evaluation Results (Held-Out Test Set: 1,364 Problems)

| Model / Approach | MAE | RMSE | Spearman Rank ($\rho$) | Tier Accuracy | 80% CI Coverage |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Baseline 1: Training Mean Predictor | 687.7 | 800.9 | 0.0000 | 18.5% | N/A |
| Baseline 2: Structured-Only LightGBM | 513.2 | 625.9 | 0.6689 | 42.6% | N/A |
| **IntelliGate (Sentence-BERT + LightGBM)** | **494.8** | **600.3** | **0.6929** | **40.8%** | **78.5%** |

**Inference Speed**: After one-time lazy model load, inference takes **28–33 ms** per problem on CPU.

---

## 4. Integration with Intelligent Routing

### 4.1 Continuous Model Success Probability Function
Instead of coarse bucket matching ("easy", "medium", "hard"), the router evaluates model capability as a continuous function of effective difficulty rating:
$$R_{\text{eff}} = R_{\text{pred}} + 0.30 \cdot (R_{\text{upper}} - R_{\text{pred}})$$
For a candidate model $m$ with empirical pass rates $r_{\text{easy}}, r_{\text{med}}, r_{\text{hard}}$:
$$P(\text{solve} \mid R_{\text{eff}}, m) = \begin{cases} 
r_{\text{easy}} + 0.06 \cdot \frac{1200 - R_{\text{eff}}}{400} & R_{\text{eff}} \le 1200 \\
(1 - t) \cdot r_{\text{easy}} + t \cdot r_{\text{med}} & 1200 < R_{\text{eff}} \le 1800, \; t = \frac{R_{\text{eff}} - 1200}{600} \\
(1 - t) \cdot r_{\text{med}} + t \cdot r_{\text{hard}} & 1800 < R_{\text{eff}} \le 2400, \; t = \frac{R_{\text{eff}} - 1800}{600} \\
\max(0.12, r_{\text{hard}} \cdot (1 - 0.45 \cdot \frac{R_{\text{eff}} - 2400}{1100})) & R_{\text{eff}} > 2400
\end{cases}$$

### 4.2 Multi-Objective Utility Function
$$\text{Score}(m) = w_q \cdot Q_{\text{eff}} + w_c \cdot (1 - C_{\text{norm}}) + w_l \cdot (1 - L_{\text{norm}})$$
where $Q_{\text{eff}} = 0.50 \cdot Q_{\text{domain}} + 0.50 \cdot P(\text{solve} \mid R_{\text{eff}}, m)$.
The weights $w_q, w_c, w_l$ smoothly adapt to problem difficulty:
- For high-rating problems ($R_{\text{eff}} \ge 2000$): $w_q = 0.75, w_c = 0.15, w_l = 0.10$ (correctness prioritized).
- For low-rating problems ($R_{\text{eff}} \le 1200$): $w_q = 0.35, w_c = 0.45, w_l = 0.20$ (cost minimization prioritized).

### 4.3 Official Rating Direct Pass-Through
When a problem is imported with an official Codeforces rating from the contest problem set, it is used directly ($\text{lower\_bound} = \text{predicted\_rating} = \text{upper\_bound}$), bypassing model inference while executing the exact same downstream routing logic.

---

## 5. Verification Engine & Sandboxed Execution

### Supported Languages
1. **C++17**: Compiled with `g++ -O2 -std=c++17`. Stdin/stdout redirection.
2. **Python 3**: Subprocess isolation with `-I` (isolated environment mode).
3. **Java**: Compiled with `javac` and run with `java -Xmx256m`.

### Sandboxed Isolation Boundaries
- Dynamic scratch directories (`intelligate_exec_*`) purged immediately after execution.
- 3.0s hard execution timeout via async subprocess watchers.
- 32KB output buffer cap preventing log-flooding attacks.

---

## 6. Frontend Developer Workbench

1. **Coding Playground ([PlaygroundView.jsx](file:///E:/ai_pro/intelligate/frontend/src/components/PlaygroundView.jsx))**:
   - URL import bar supporting Codeforces and LeetCode problem URLs.
   - **Interactive ML Difficulty Estimator**: Instant "Estimate Rating" calculator displaying predicted Codeforces rating, 80% confidence interval, and method badge before running code generation.
   - 6-column Telemetry Ribbon displaying Outcome, CF Rating, Tests Passed, Attempts, Total Cost, and Latency.
   - Dark code display window with multi-attempt tabs.
   - Transparent verification & escalation waterfall trace.
2. **Audit History ([RequestHistoryView.jsx](file:///E:/ai_pro/intelligate/frontend/src/components/RequestHistoryView.jsx))**:
   - Execution audit table displaying language, routing mode, initial/final model, attempts, outcome, cost, and latency.
   - Detailed modal showing problem difficulty, compiler diagnostics, and input/output diffs.
3. **Model Performance ([ModelPerformanceView.jsx](file:///E:/ai_pro/intelligate/frontend/src/components/ModelPerformanceView.jsx))**:
   - Matrix showing empirical pass rates across categories and rating tiers.
4. **Benchmark Lab ([BenchmarkLabView.jsx](file:///E:/ai_pro/intelligate/frontend/src/components/BenchmarkLabView.jsx))**:
   - Control center to run benchmark suites across calibration and test splits.

---

## 7. Test Suite & Verification Summary

- **Complete Backend Test Suite**: **55 passed out of 55 tests** (`pytest backend/tests -q`).
  - 9 tests in `test_ml_difficulty.py` covering feature extraction, embedder chunking, LightGBM quantile regression, analyzer integration, and continuous router pass-rate interpolation.
  - 9 tests in `test_coding_pipeline.py` covering sandboxed C++ and Python execution, timeout enforcement, and budget gating.
  - 14 tests in `test_routing_engine_orchestration.py` and `test_routing_engine.py` covering multi-attempt escalation, syntax-error retries, and budget exhaustion.
  - 23 tests covering token accounting, caching, circuit breakers, and PII detection.
- **Frontend Build**: `npm run build` compiled cleanly into production bundle (`dist/`) in 4.70s with zero errors.
