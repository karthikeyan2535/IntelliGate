# IntelliGate Performance Benchmarks & Empirical Profile

The benchmark suite (`scripts/benchmark.py`) measures gateway overhead, cache acceleration, concurrent request throughput, and PII inspection latency.

---

## 1. Measured Empirical Results

| Metric | Result | Target Specification | Status |
|---|---|---|---|
| **Base Engine Latency (`/health`)** | **0.78 ms** | < 2.0 ms | **EXCEEDED** |
| **Cold Request (Full 21 Stages)** | **1855.80 ms** | Dependent on model | **VERIFIED** |
| **Cached Request (Exact Match HIT)** | **6.04 ms** | < 15.0 ms | **EXCEEDED** |
| **Cache Speedup Ratio** | **307.1x** | > 10x | **EXCEEDED** |
| **Concurrency Load (50 parallel)** | **183.4 req/sec** | > 100 req/sec | **EXCEEDED** |
| **Mean Concurrency Latency** | **5.45 ms** | < 20.0 ms | **EXCEEDED** |
| **PII Multi-Entity Sanitization** | **0.071 ms / payload** | < 1.0 ms | **EXCEEDED** |
| **Success Rate under Load** | **100% (50/50)** | 100% | **PASSED** |

---

## 2. Benchmark Script Execution

To reproduce the benchmark locally:

```powershell
$env:PYTHONPATH = "E:\ai_pro\intelligate\backend"
python E:\ai_pro\intelligate\scripts\benchmark.py
```

### Output:
```
=================================================================
      INTELLIGATE GATEWAY BENCHMARK & LOAD PROFILE REPORT     
=================================================================
[1] Base Engine Latency (/health):           0.78 ms / req
[2] Cold Request (Full 21 Stages):           1855.80 ms (Cache MISS)
[3] Cached Request (Exact Match HIT):         6.04 ms (307.1x speedup)
[4] Executing 50 concurrent pipeline requests...
    • Success Rate:                           50/50 (100%)
    • Total Wall Clock Time:                  0.27 s
    • Concurrency Throughput:                 183.4 req/sec
    • Mean Latency under Concurrency:         5.45 ms
[5] PII Multi-Entity Scan & Redact Overhead:  0.071 ms / payload
=================================================================
                  BENCHMARK COMPLETE - ALL PASSED             
=================================================================
```

