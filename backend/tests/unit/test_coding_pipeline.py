"""
Unit tests for Coding-focused IntelliGate:
- Coding problem analysis (task type, algorithm family, difficulty)
- Sandbox code execution (C++17, Python)
- Intelligent coding router scoring & constraints
- URL importer parsing & fallback handling
"""
import pytest
from app.analysis.coding_analyzer import coding_analyzer
from app.execution.sandbox import sandbox_executor
from app.routing.coding_router import coding_router


def test_analyzer_algorithm_families():
    # DP test
    dp_text = "Find minimum coins to make up amount W using dynamic programming memoization."
    res_dp = coding_analyzer.analyze("Coin Change", dp_text, "1 <= W <= 10000")
    assert res_dp.algorithm_family == "dynamic_programming"

    # Graphs test
    graph_text = "Find shortest path from source 0 to all vertices in directed graph using Dijkstra."
    res_graph = coding_analyzer.analyze("Shortest Path", graph_text, "V <= 1000, E <= 5000")
    assert res_graph.algorithm_family == "graphs"

    # Trees test
    tree_text = "Return preorder and inorder traversal of binary tree with maximum depth."
    res_tree = coding_analyzer.analyze("Tree Traversal", tree_text, "N <= 1000")
    assert res_tree.algorithm_family == "trees_data_structures"


def test_analyzer_difficulty_bounds():
    hard_text = "Solve puzzle for n <= 20 with backtracking."
    res_hard = coding_analyzer.analyze("N Queens", hard_text, "n <= 20")
    assert res_hard.difficulty == "hard"
    assert res_hard.algorithm_family == "backtracking"


@pytest.mark.asyncio
async def test_sandbox_python_execution():
    code = """
import sys
data = sys.stdin.read().split()
if data:
    print(int(data[0]) * int(data[1]))
"""
    test_cases = [{"input": "6 7\n", "expected": "42\n"}]
    res = await sandbox_executor.execute("python", code, test_cases)
    assert res.status == "accepted"
    assert res.passed_count == 1
    assert res.total_count == 1


@pytest.mark.asyncio
async def test_sandbox_python_wrong_answer():
    code = "print(10)"
    test_cases = [{"input": "1\n", "expected": "42\n"}]
    res = await sandbox_executor.execute("python", code, test_cases)
    assert res.status == "wrong_answer"
    assert res.passed_count == 0


@pytest.mark.asyncio
async def test_sandbox_timeout_enforcement():
    code = """
import time
time.sleep(5)
print('done')
"""
    test_cases = [{"input": "1\n", "expected": "done\n"}]
    res = await sandbox_executor.execute("python", code, test_cases, timeout_sec=0.5)
    assert res.status == "time_limit_exceeded"
    assert res.passed_count == 0


@pytest.mark.asyncio
async def test_sandbox_cpp_compilation_and_execution():
    code = """
#include <iostream>
using namespace std;
int main() {
    int a, b;
    if (cin >> a >> b) {
        cout << (a + b) << endl;
    }
    return 0;
}
"""
    test_cases = [{"input": "15 25\n", "expected": "40\n"}]
    res = await sandbox_executor.execute("cpp", code, test_cases)
    assert res.status == "accepted"
    assert res.passed_count == 1


@pytest.mark.asyncio
async def test_sandbox_cpp_compilation_error():
    bad_code = "int main() { syntax error }"
    test_cases = [{"input": "1\n", "expected": "1\n"}]
    res = await sandbox_executor.execute("cpp", bad_code, test_cases)
    assert res.status == "compilation_error"
    assert "error" in res.compilation_output.lower()


@pytest.mark.asyncio
async def test_intelligent_coding_router_modes():
    # Direct mode
    res_direct = await coding_router.select_model(
        algorithm_category="graphs",
        difficulty="medium",
        routing_mode="direct",
        target_model="llama-3.3-70b-versatile",
    )
    assert res_direct.selected_model == "llama-3.3-70b-versatile"
    assert res_direct.routing_mode == "direct"

    # Intelligent mode
    res_intel = await coding_router.select_model(
        algorithm_category="dynamic_programming",
        difficulty="hard",
        routing_mode="intelligent",
    )
    assert res_intel.selected_model is not None
    assert len(res_intel.candidate_rankings) > 0
    assert res_intel.candidate_rankings[0].rank == 1

    # Lowest cost mode
    res_cheap = await coding_router.select_model(
        algorithm_category="arrays_strings",
        difficulty="easy",
        routing_mode="lowest_cost",
    )
    assert res_cheap.selected_model == "llama-3.1-8b-instant"


@pytest.mark.asyncio
async def test_router_budget_enforcement():
    # Very small budget should filter expensive models
    res = await coding_router.select_model(
        algorithm_category="graphs",
        difficulty="hard",
        routing_mode="intelligent",
        cost_budget_usd=0.0001,
    )
    # Most expensive models like gpt-4o ($0.00350) should be excluded
    for rej in res.rejected_candidates:
        if rej["model_id"] == "gpt-4o":
            assert "exceeds budget" in rej["reason"]

