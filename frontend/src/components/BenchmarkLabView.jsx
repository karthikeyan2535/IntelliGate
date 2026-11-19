import React, { useState, useEffect } from 'react';
import {
  FlaskConical, Play, RefreshCw, CheckCircle2, Clock,
  DollarSign, TrendingUp, Award, Layers, AlertCircle, Eye
} from 'lucide-react';
import {
  runCodingBenchmark, fetchCodingBenchmarkHistory, fetchBaselineComparisons
} from '../services/api';

export default function BenchmarkLabView() {
  const [strategy, setStrategy] = useState('intelligent');
  const [split, setSplit] = useState('calibration');
  const [category, setCategory] = useState('all');
  const [maxProblems, setMaxProblems] = useState(10);
  const [language, setLanguage] = useState('python');

  const [running, setRunning] = useState(false);
  const [runResult, setRunResult] = useState(null);
  const [runError, setRunError] = useState(null);

  const [history, setHistory] = useState([]);
  const [baselines, setBaselines] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [hData, bData] = await Promise.all([
        fetchCodingBenchmarkHistory(20),
        fetchBaselineComparisons(),
      ]);
      setHistory(hData || []);
      setBaselines(bData || []);
    } catch (err) {
      console.error('Failed to load benchmark data', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleExecuteBenchmark() {
    setRunning(true);
    setRunError(null);
    setRunResult(null);

    try {
      const res = await runCodingBenchmark({
        strategy_or_model: strategy,
        split,
        category,
        max_problems: maxProblems,
        language,
      });
      setRunResult(res);
      await loadData();
    } catch (err) {
      console.error('Benchmark execution failed', err);
      setRunError(err.response?.data?.detail || err.message || 'Benchmark run failed');
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="space-y-6 font-sans">
      {/* Benchmark Control Bar */}
      <div className="bg-white border border-app-border rounded-lg p-5 space-y-4 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-app-border">
          <div>
            <h2 className="text-sm font-semibold text-ink-primary flex items-center gap-2">
              <FlaskConical className="w-4 h-4 text-metric-blue" />
              <span>Benchmark Execution Lab & Baseline Comparison</span>
            </h2>
            <p className="text-xs text-ink-secondary mt-0.5">
              Run models and routing policies against 100 curated competitive programming problems
            </p>
          </div>

          <button
            onClick={loadData}
            className="px-2.5 py-1 bg-white hover:bg-app-subtle border border-app-border text-ink-secondary hover:text-ink-primary rounded-md flex items-center gap-1.5 transition-colors cursor-pointer text-xs"
          >
            <RefreshCw className="w-3.5 h-3.5 text-ink-muted" />
            <span>Sync</span>
          </button>
        </div>

        {/* Config Options */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3 text-xs">
          <div>
            <label className="block text-[11px] font-medium text-ink-secondary mb-1">Strategy / Model</label>
            <select
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
              className="w-full bg-white border border-app-border rounded-md px-2.5 py-1.5 text-xs text-ink-primary focus:outline-none focus:border-metric-blue"
            >
              <option value="intelligent">IntelliGate (Intelligent + Escalation)</option>
              <option value="baseline_strongest">Baseline: Always Strongest</option>
              <option value="baseline_cheapest">Baseline: Always Cheapest</option>
              <option value="baseline_static">Baseline: Static Category</option>
              <option value="llama-3.3-70b-versatile">Groq Llama 3.3 70B</option>
              <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
              <option value="llama-3.1-8b-instant">Groq Llama 3.1 8B</option>
              <option value="gpt-4o">OpenAI GPT-4o</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-medium text-ink-secondary mb-1">Dataset Split</label>
            <select
              value={split}
              onChange={(e) => setSplit(e.target.value)}
              className="w-full bg-white border border-app-border rounded-md px-2.5 py-1.5 text-xs text-ink-primary focus:outline-none focus:border-metric-blue"
            >
              <option value="calibration">Calibration Set (70 Problems)</option>
              <option value="test">Held-Out Test Set (30 Problems)</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-medium text-ink-secondary mb-1">Category Slice</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full bg-white border border-app-border rounded-md px-2.5 py-1.5 text-xs text-ink-primary focus:outline-none focus:border-metric-blue"
            >
              <option value="all">All Categories (Full Suite)</option>
              <option value="arrays_strings">Arrays & Strings (20)</option>
              <option value="dynamic_programming">Dynamic Programming (20)</option>
              <option value="graphs">Graphs (20)</option>
              <option value="trees_data_structures">Trees & Data Structures (15)</option>
              <option value="greedy_binary_search">Greedy & Binary Search (15)</option>
              <option value="debugging_repair">Debugging & Code Repair (10)</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-medium text-ink-secondary mb-1">Max Problems</label>
            <select
              value={maxProblems}
              onChange={(e) => setMaxProblems(parseInt(e.target.value, 10))}
              className="w-full bg-white border border-app-border rounded-md px-2.5 py-1.5 text-xs text-ink-primary focus:outline-none focus:border-metric-blue font-mono"
            >
              <option value={5}>5 Problems (Fast Sanity Check)</option>
              <option value={10}>10 Problems (Standard Sample)</option>
              <option value={20}>20 Problems (Full Domain)</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={handleExecuteBenchmark}
              disabled={running}
              className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold text-xs rounded-md flex items-center justify-center gap-2 transition-colors cursor-pointer shadow-xs"
            >
              {running ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Evaluating...</span>
                </>
              ) : (
                <>
                  <Play className="w-3 h-3 fill-current" />
                  <span>Run Suite</span>
                </>
              )}
            </button>
          </div>
        </div>

        {runError && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md text-xs text-red-700 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{runError}</span>
          </div>
        )}

        {/* Live Run Outcome Banner */}
        {runResult && (
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-900 space-y-2">
            <div className="flex items-center justify-between font-semibold">
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Benchmark Run Completed: {runResult.passed_problems}/{runResult.total_problems} Solved ({runResult.pass_rate}%)</span>
              </span>
              <span className="font-mono text-emerald-800">
                Cost: ${runResult.total_cost_usd} • Cost/Verified: ${runResult.cost_per_verified_solution}
              </span>
            </div>
            <p className="text-[11px] text-emerald-800">
              Pass@1: {runResult.first_attempt_pass_rate}% • Average Latency: {runResult.avg_latency_ms} ms across {runResult.total_problems} problems.
            </p>
          </div>
        )}
      </div>

      {/* Baseline Comparisons Table */}
      <div className="bg-white border border-app-border rounded-lg overflow-hidden shadow-xs">
        <div className="p-3.5 border-b border-app-border flex items-center justify-between">
          <div className="text-xs font-semibold text-ink-primary flex items-center gap-1.5">
            <Award className="w-3.5 h-3.5 text-metric-blue" />
            <span>Held-Out Split Evaluation: 4 Strategy Baseline Comparison</span>
          </div>
          <span className="text-xs text-ink-secondary">
            30 Held-Out Problems
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-app-subtle/50 text-ink-secondary font-semibold text-[11px] border-b border-app-border">
              <tr>
                <th className="py-2.5 px-3">Strategy</th>
                <th className="py-2.5 px-2 text-center">Final Pass Rate</th>
                <th className="py-2.5 px-2 text-center">First-Attempt (Pass@1)</th>
                <th className="py-2.5 px-2 text-right">Cost / Verified Sol.</th>
                <th className="py-2.5 px-2 text-right">Avg Cost / Problem</th>
                <th className="py-2.5 px-2 text-center">Avg Latency</th>
                <th className="py-2.5 px-2 text-center">Escalations</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-app-border/60">
              {baselines.map((b, idx) => (
                <tr
                  key={idx}
                  className={`hover:bg-app-subtle/30 transition-colors ${
                    b.strategy === 'intelligate' ? 'bg-blue-50/40 font-medium' : ''
                  }`}
                >
                  <td className="py-3 px-3 font-semibold text-ink-primary">
                    {b.label}
                  </td>
                  <td className="py-3 px-2 text-center font-mono text-xs">
                    <span className="font-bold text-metric-emerald">{b.final_pass_rate}%</span>
                  </td>
                  <td className="py-3 px-2 text-center font-mono text-xs text-ink-secondary">
                    {b.first_attempt_pass_rate}%
                  </td>
                  <td className="py-3 px-2 text-right font-mono text-xs text-metric-emerald font-bold">
                    ${b.cost_per_verified_solution.toFixed(5)}
                  </td>
                  <td className="py-3 px-2 text-right font-mono text-xs text-ink-secondary">
                    ${b.avg_cost_per_problem.toFixed(5)}
                  </td>
                  <td className="py-3 px-2 text-center font-mono text-xs text-metric-amber">
                    {b.avg_latency_ms} ms
                  </td>
                  <td className="py-3 px-2 text-center font-mono text-xs text-ink-secondary">
                    {b.escalation_rate}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Historical Runs Table */}
      <div className="bg-white border border-app-border rounded-lg overflow-hidden shadow-xs">
        <div className="p-3.5 border-b border-app-border flex items-center justify-between">
          <div className="text-xs font-semibold text-ink-primary flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-metric-blue" />
            <span>Benchmark Run Execution History</span>
          </div>
          <span className="text-xs text-ink-secondary">
            {history.length} runs recorded
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-app-subtle/50 text-ink-secondary font-semibold text-[11px] border-b border-app-border">
              <tr>
                <th className="py-2.5 px-3">Run ID</th>
                <th className="py-2.5 px-2">Strategy / Model</th>
                <th className="py-2.5 px-2">Split</th>
                <th className="py-2.5 px-2 text-center">Score</th>
                <th className="py-2.5 px-2 text-center">Pass@1</th>
                <th className="py-2.5 px-2 text-right">Cost</th>
                <th className="py-2.5 px-2 text-center">Avg Latency</th>
                <th className="py-2.5 px-2">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-app-border/60">
              {history.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-ink-secondary text-xs">
                    No benchmark runs recorded yet. Select parameters and click "Run Suite" above.
                  </td>
                </tr>
              ) : (
                history.map((h, idx) => (
                  <tr key={idx} className="hover:bg-app-subtle/30 transition-colors">
                    <td className="py-2.5 px-3 font-mono text-ink-secondary text-[11px]">
                      {h.id.slice(0, 8)}
                    </td>
                    <td className="py-2.5 px-2 font-medium text-ink-primary font-mono text-[11px]">
                      {h.strategy}
                    </td>
                    <td className="py-2.5 px-2 capitalize text-ink-secondary text-[11px]">
                      {h.split}
                    </td>
                    <td className="py-2.5 px-2 text-center font-mono text-xs">
                      <span className="font-semibold text-metric-emerald">{h.pass_rate}%</span>
                      <span className="text-ink-muted text-[10px] ml-1">({h.passed_problems}/{h.total_problems})</span>
                    </td>
                    <td className="py-2.5 px-2 text-center font-mono text-xs text-ink-secondary">
                      {h.first_attempt_pass_rate}%
                    </td>
                    <td className="py-2.5 px-2 text-right font-mono text-xs text-metric-emerald">
                      ${h.total_cost_usd.toFixed(5)}
                    </td>
                    <td className="py-2.5 px-2 text-center font-mono text-xs text-metric-amber">
                      {Math.round(h.avg_latency_ms)} ms
                    </td>
                    <td className="py-2.5 px-2 text-ink-secondary text-[11px]">
                      {h.created_at ? new Date(h.created_at).toLocaleTimeString() : 'Recent'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

