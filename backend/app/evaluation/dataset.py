"""
Benchmark Evaluation Dataset for IntelliGate.
Contains curated benchmark prompts across Coding, Reasoning, Writing, and General Q&A
with deterministic verification rules and expected answers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class BenchmarkItem:
    id: str
    category: str  # coding, reasoning, writing, general_qa
    complexity: str  # simple, moderate, complex
    prompt: str
    expected_contains: list[str]
    validator_type: str  # "substring", "regex", "json_valid", "length_check"
    regex_pattern: Optional[str] = None


BENCHMARK_DATASET: list[BenchmarkItem] = [
    # ── CODING ─────────────────────────────────────────────────────────────
    BenchmarkItem(
        id="code_01",
        category="coding",
        complexity="simple",
        prompt="Write a Python function named `is_palindrome` that takes a string and returns True if it's a palindrome.",
        expected_contains=["def is_palindrome", "return"],
        validator_type="substring",
    ),
    BenchmarkItem(
        id="code_02",
        category="coding",
        complexity="moderate",
        prompt="Write a Python function `binary_search(arr, target)` that returns the index of target in sorted arr, or -1 if not found. Include comments.",
        expected_contains=["def binary_search", "while", "return -1"],
        validator_type="substring",
    ),
    BenchmarkItem(
        id="code_03",
        category="coding",
        complexity="complex",
        prompt="Implement an asynchronous LRU Cache in Python using an OrderedDict and asyncio.Lock. Class must have `get(key)` and `set(key, value, ttl)` methods.",
        expected_contains=["class LRUCache", "async def get", "async def set", "Lock"],
        validator_type="substring",
    ),
    BenchmarkItem(
        id="code_04",
        category="coding",
        complexity="simple",
        prompt="Write a SQL query to select customer_id and total amount spent from an orders table where status is 'completed', grouped by customer_id.",
        expected_contains=["SELECT", "FROM", "WHERE", "GROUP BY"],
        validator_type="substring",
    ),
    BenchmarkItem(
        id="code_05",
        category="coding",
        complexity="moderate",
        prompt="Write a regular expression that validates standard international E.164 phone numbers (e.g., +14155552671). Output only the regex pattern.",
        expected_contains=["^\\+?[1-9]\\d{1,14}$"],
        validator_type="regex",
        regex_pattern=r"(\^\\[\+]?|^\+)",
    ),
    BenchmarkItem(
        id="code_06",
        category="coding",
        complexity="complex",
        prompt="Write a Rust function that safely swaps two elements in a mutable slice using pointer arithmetic or safe indexing, handling out-of-bounds errors gracefully.",
        expected_contains=["fn swap", "Option", "Result"],
        validator_type="substring",
    ),

    # ── REASONING ──────────────────────────────────────────────────────────
    BenchmarkItem(
        id="reason_01",
        category="reasoning",
        complexity="simple",
        prompt="A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. How much does the ball cost? Answer with just the number.",
        expected_contains=["0.05", "5 cents"],
        validator_type="substring",
    ),
    BenchmarkItem(
        id="reason_02",
        category="reasoning",
        complexity="moderate",
        prompt="If all Bloops are Razzies, and some Razzies are Lizzies, are all Bloops necessarily Lizzies? Answer Yes or No and briefly justify.",
        expected_contains=["No"],
        validator_type="substring",
    ),
    BenchmarkItem(
        id="reason_03",
        category="reasoning",
        complexity="complex",
        prompt="Three prisoners are told that each has either a red or blue hat. There are 3 red hats and 2 blue hats. All 3 can see the others' hats. Prisoner 1 says 'I do not know'. Prisoner 2 says 'I do not know'. What color hat does Prisoner 3 have? Deduce step by step.",
        expected_contains=["red"],
        validator_type="substring",
    ),
    BenchmarkItem(
        id="reason_04",
        category="reasoning",
        complexity="simple",
        prompt="What is the derivative of f(x) = 3x^2 + 5x - 7? Give the exact formula.",
        expected_contains=["6x + 5"],
        validator_type="substring",
    ),
    BenchmarkItem(
        id="reason_05",
        category="reasoning",
        complexity="moderate",
        prompt="A car travels 60 miles at 30 mph, and then returns 60 miles at 60 mph. What is its average speed for the entire round trip?",
        expected_contains=["40", "40 mph"],
        validator_type="substring",
    ),
    BenchmarkItem(
        id="reason_06",
        category="reasoning",
        complexity="complex",
        prompt="Evaluate the CAP theorem trade-offs in a distributed banking ledger. Explain why linearizable consistency cannot be guaranteed during network partitions.",
        expected_contains=["partition", "consistency", "availability", "split-brain"],
        validator_type="substring",
    ),

    # ── WRITING ────────────────────────────────────────────────────────────
    BenchmarkItem(
        id="write_01",
        category="writing",
        complexity="simple",
        prompt="Write a professional one-paragraph email declining a job offer politely while keeping the door open for future collaboration.",
        expected_contains=["thank you", "offer", "future", "opportunity"],
        validator_type="substring",
    ),
    BenchmarkItem(
        id="write_02",
        category="writing",
        complexity="moderate",
        prompt="Draft an executive summary of an incident post-mortem explaining a 15-minute database outage caused by connection pool exhaustion.",
        expected_contains=["Root Cause", "Action Items", "Impact", "Mitigation"],
        validator_type="substring",
    ),
    BenchmarkItem(
        id="write_03",
        category="writing",
        complexity="complex",
        prompt="Write a compelling, metaphorical introduction for a technical book comparing microservice orchestration to conducting a symphony orchestra.",
        expected_contains=["orchestra", "conductor", "harmony", "tempo"],
        validator_type="substring",
    ),
    BenchmarkItem(
        id="write_04",
        category="writing",
        complexity="simple",
        prompt="Rewrite this sentence to be concise and active voice: 'The decision was made by the engineering leadership committee that deployments should be halted.'",
        expected_contains=["Engineering leadership", "halted"],
        validator_type="substring",
    ),
    BenchmarkItem(
        id="write_05",
        category="writing",
        complexity="moderate",
        prompt="Generate 3 distinct marketing taglines for a developer tool that automates Kubernetes cluster optimization.",
        expected_contains=["Kubernetes", "automate"],
        validator_type="substring",
    ),
    BenchmarkItem(
        id="write_06",
        category="writing",
        complexity="complex",
        prompt="Draft a clear RFC (Request for Comments) abstract proposing an immutable event-sourcing architecture for an order fulfillment platform.",
        expected_contains=["RFC", "Abstract", "Event-Sourcing", "State", "Idempotency"],
        validator_type="substring",
    ),

    # ── GENERAL Q&A ────────────────────────────────────────────────────────
    BenchmarkItem(
        id="qa_01",
        category="general_qa",
        complexity="simple",
        prompt="What is the capital of Australia? Answer with just the city name.",
        expected_contains=["Canberra"],
        validator_type="substring",
    ),
    BenchmarkItem(
        id="qa_02",
        category="general_qa",
        complexity="simple",
        prompt="What is the difference between TCP and UDP in two concise sentences?",
        expected_contains=["TCP", "UDP", "connection"],
        validator_type="substring",
    ),
    BenchmarkItem(
        id="qa_03",
        category="general_qa",
        complexity="moderate",
        prompt="Explain the difference between symmetric and asymmetric encryption, mentioning one practical example of each.",
        expected_contains=["AES", "RSA", "public key", "private key"],
        validator_type="substring",
    ),
    BenchmarkItem(
        id="qa_04",
        category="general_qa",
        complexity="moderate",
        prompt="What causes the seasons on Earth? Answer in 3 bullet points.",
        expected_contains=["tilt", "axis", "orbit"],
        validator_type="substring",
    ),
    BenchmarkItem(
        id="qa_05",
        category="general_qa",
        complexity="complex",
        prompt="Explain how zero-knowledge proofs work using an intuitive conceptual analogy (such as the Ali Baba cave or colored balls), then state their primary cryptographic property.",
        expected_contains=["prover", "verifier", "knowledge", "soundness"],
        validator_type="substring",
    ),
    BenchmarkItem(
        id="qa_06",
        category="general_qa",
        complexity="simple",
        prompt="What is the speed of light in a vacuum in meters per second? Give the exact or rounded scientific figure.",
        expected_contains=["299,792,458", "3 x 10^8", "300,000"],
        validator_type="substring",
    ),
]
