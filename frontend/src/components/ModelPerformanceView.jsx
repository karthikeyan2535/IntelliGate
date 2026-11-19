import React, { useState, useEffect } from 'react';
import {
  Award, RefreshCw, Play, CheckCircle2, AlertCircle,
  FileCode, Terminal, Search, ExternalLink, Layers,
  Clock, Check, X, Eye, BarChart2, RotateCcw
} from 'lucide-react';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid
} from 'recharts';
import {
  fetchModelProfiles, runEvaluationSuite, fetchEvaluationRuns, fetchEvaluationRunDetails, resetModelProfiles
} from '../services/api';

export default function ModelPerformanceView() {
  const [profiles, setProfiles] = useState([]);
  const [evalRuns, setEvalRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [evaluatingModel, setEvaluatingModel] = useState(null);
  const [evalResult, setEvalResult] = useState(null);
  const [evalError, setEvalError] = useState(null);
  const [filterProvider, setFilterProvider] = useState('all');
  const [selectedRun, setSelectedRun] = useState(null);
  const [loadingRunDetail, setLoadingRunDetail] = useState(false);

  useEffect(() => {
    loadAll();
  }, []);

  async function loadAll() {
    setLoading(true);
    try {
      const [profData, runData] = await Promise.all([
        fetchModelProfiles(),
        fetchEvaluationRuns(15)
      ]);
      setProfiles(profData || []);
      setEvalRuns(runData || []);
    } catch (err) {
      console.error('Failed to load performance data', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleResetBaselines() {
    try {
      await resetModelProfiles();
      await loadAll();
    } catch (err) {
      console.error('Failed to reset profiles', err);
    }
  }

  async function handleRunEval(modelId, provider) {
    setEvaluatingModel(modelId);
    setEvalError(null);
    setEvalResult(null);

    try {
      const result = await runEvaluationSuite(modelId, provider, 12);
      setEvalResult(result);
      await loadAll();
    } catch (err) {
      console.error('Evaluation run error', err);
      setEvalError(err.message || 'Evaluation run failed');
    } finally {
      setEvaluatingModel(null);
    }
  }

  async function handleInspectRun(runId) {
    setLoadingRunDetail(true);
    try {
      const details = await fetchEvaluationRunDetails(runId);
      setSelectedRun(details);
    } catch (err) {
      console.error('Failed to load run details', err);
    } finally {
      setLoadingRunDetail(false);
    }
  }

  const filtered = profiles.filter((p) => {
    if (filterProvider === 'all') return true;
    return p.provider?.toLowerCase() === filterProvider.toLowerCase();
  });

  const chartData = filtered.map((p) => ({
    name: p.display_name?.replace('OpenAI ', '').replace('Google ', '').replace('Groq ', '') || p.model_id,
    provider: p.provider,
    coding: Math.round((p.coding_quality || 0) * 100),
    reasoning: Math.round((p.reasoning_quality || 0) * 100),
    writing: Math.round((p.writing_quality || 0) * 100),
    latency: Math.round(p.avg_latency_ms || 200),
  }));

  return (
    <div className="space-y-6 font-sans">
      {/* Header & Controls */}
      <div className="bg-white border border-app-border rounded-lg p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
        <div>
          <h2 className="text-sm font-semibold text-ink-primary flex items-center gap-2">
            <Award className="w-4 h-4 text-metric-blue" />
            Model Capability Registry & Empirical Benchmarks
          </h2>
          <p className="text-xs text-ink-secondary mt-0.5">
            Empirical quality scores calibrated via deterministic unit assertions & syntax validation
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs">
          {/* Provider Filter */}
          <div className="inline-flex items-center bg-app-subtle p-0.5 rounded-md border border-app-border">
            {['all', 'openai', 'groq', 'gemini'].map((prov) => (
              <button
                key={prov}
                onClick={() => setFilterProvider(prov)}
                className={`px-2.5 py-1 rounded text-xs font-medium capitalize transition-colors cursor-pointer ${
                  filterProvider === prov
                    ? 'bg-white text-ink-primary shadow-xs'
                    : 'text-ink-secondary hover:text-ink-primary'
                }`}
              >
                {prov}
              </button>
            ))}
          </div>

          <button
            onClick={loadAll}
            className="px-2.5 py-1 bg-white hover:bg-app-subtle border border-app-border text-ink-secondary hover:text-ink-primary rounded-md flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5 text-ink-muted" />
            <span>Sync</span>
          </button>

          <button
            onClick={handleResetBaselines}
            title="Restore baseline calibrated empirical scores for all models"
            className="px-2.5 py-1 bg-white hover:bg-amber-50 border border-app-border text-ink-secondary hover:text-amber-800 rounded-md flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <RotateCcw className="w-3 h-3 text-ink-muted" />
            <span>Reset Baselines</span>
          </button>
        </div>
      </div>

      {/* Live Run Banner */}
      {evaluatingModel && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3.5 text-xs text-blue-700 flex items-center gap-2.5">
          <Terminal className="w-4 h-4 animate-spin flex-shrink-0" />
          <span>
            Executing deterministic benchmark test suite against <strong className="font-mono">{evaluatingModel}</strong>...
          </span>
        </div>
      )}

      {evalResult && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3.5 text-xs text-emerald-800 flex items-center justify-between gap-2.5">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-emerald-600" />
            <span>
              Evaluation completed: {evalResult.passed_prompts}/{evalResult.total_prompts} items passed for <strong className="font-mono">{evalResult.model_id}</strong>. Overall calibrated quality: {(evalResult.overall_quality_score * 100).toFixed(1)}%.
            </span>
          </div>
          <button
            onClick={() => setEvalResult(null)}
            className="text-xs text-emerald-700 hover:text-emerald-900 font-medium underline cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      )}

      {evalError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3.5 text-xs text-red-700 flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{evalError}</span>
        </div>
      )}

      {/* Capability Matrix Table */}
      <div className="bg-white border border-app-border rounded-lg overflow-hidden shadow-xs">
        <div className="p-3.5 border-b border-app-border flex items-center justify-between">
          <div className="text-xs font-semibold text-ink-primary flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-metric-blue" />
            <span>Empirical Capability Matrix</span>
          </div>
          <span className="text-xs text-ink-secondary">
            {filtered.length} active models registered
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-app-subtle/50 text-ink-secondary font-semibold text-[11px] border-b border-app-border">
              <tr>
                <th className="py-2.5 px-3">Model Identifier</th>
                <th className="py-2.5 px-2">Provider</th>
                <th className="py-2.5 px-2 text-center">Coding (Q_c)</th>
                <th className="py-2.5 px-2 text-center">Reasoning (Q_r)</th>
                <th className="py-2.5 px-2 text-center">Writing (Q_w)</th>
                <th className="py-2.5 px-2 text-center">General QA</th>
                <th className="py-2.5 px-2 text-center">P50 Latency</th>
                <th className="py-2.5 px-2 text-right">In / 1K</th>
                <th className="py-2.5 px-2 text-right">Out / 1K</th>
                <th className="py-2.5 px-2 text-center">Reliability</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-app-border/60">
              {filtered.map((p, idx) => (
                <tr key={idx} className="hover:bg-app-subtle/30 transition-colors">
                  <td className="py-2.5 px-3">
                    <div className="font-medium text-ink-primary">{p.display_name}</div>
                    <div className="text-[11px] text-ink-secondary font-mono">{p.model_id}</div>
                  </td>

                  <td className="py-2.5 px-2">
                    <span className="px-2 py-0.5 rounded bg-app-subtle border border-app-border text-[11px] capitalize text-ink-secondary">
                      {p.provider}
                    </span>
                  </td>

                  <td className="py-2.5 px-2 text-center font-mono text-[11px]">
                    <span className={`font-semibold ${
                      p.coding_quality >= 0.90 ? 'text-metric-emerald' :
                      p.coding_quality >= 0.80 ? 'text-metric-cyan' : 'text-ink-secondary'
                    }`}>
                      {(p.coding_quality * 100).toFixed(0)}%
                    </span>
                  </td>

                  <td className="py-2.5 px-2 text-center font-mono text-[11px]">
                    <span className={`font-semibold ${
                      p.reasoning_quality >= 0.90 ? 'text-metric-emerald' :
                      p.reasoning_quality >= 0.80 ? 'text-metric-cyan' : 'text-ink-secondary'
                    }`}>
                      {(p.reasoning_quality * 100).toFixed(0)}%
                    </span>
                  </td>

                  <td className="py-2.5 px-2 text-center font-mono text-[11px]">
                    <span className={`font-semibold ${
                      p.writing_quality >= 0.90 ? 'text-metric-emerald' :
                      p.writing_quality >= 0.80 ? 'text-metric-cyan' : 'text-ink-secondary'
                    }`}>
                      {(p.writing_quality * 100).toFixed(0)}%
                    </span>
                  </td>

                  <td className="py-2.5 px-2 text-center font-mono text-[11px]">
                    <span className={`font-semibold ${
                      p.general_qa_quality >= 0.90 ? 'text-metric-emerald' :
                      p.general_qa_quality >= 0.80 ? 'text-metric-cyan' : 'text-ink-secondary'
                    }`}>
                      {(p.general_qa_quality * 100).toFixed(0)}%
                    </span>
                  </td>

                  <td className="py-2.5 px-2 text-center font-mono text-[11px] text-metric-amber">
                    {p.avg_latency_ms ? `${Math.round(p.avg_latency_ms)} ms` : '—'}
                  </td>

                  <td className="py-2.5 px-2 text-right font-mono text-[11px] text-ink-primary">
                    ${Number(p.input_cost_per_1k || 0).toFixed(5)}
                  </td>

                  <td className="py-2.5 px-2 text-right font-mono text-[11px] text-ink-primary">
                    ${Number(p.output_cost_per_1k || 0).toFixed(5)}
                  </td>

                  <td className="py-2.5 px-2 text-center font-mono text-[11px] text-metric-emerald">
                    {((p.reliability || 0.99) * 100).toFixed(1)}%
                  </td>

                  <td className="py-2.5 px-3 text-right">
                    <button
                      onClick={() => handleRunEval(p.model_id, p.provider)}
                      disabled={evaluatingModel === p.model_id}
                      className="px-2.5 py-1 bg-white hover:bg-app-subtle border border-app-border text-ink-primary rounded-md inline-flex items-center gap-1.5 transition-colors cursor-pointer text-xs"
                    >
                      {evaluatingModel === p.model_id ? (
                        <Terminal className="w-3 h-3 animate-spin text-metric-blue" />
                      ) : (
                        <Play className="w-2.5 h-2.5 fill-current text-metric-blue" />
                      )}
                      <span>Run Eval</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Visual Quality Comparison Chart */}
      <div className="bg-white border border-app-border rounded-lg p-5 shadow-xs">
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-app-border">
          <div>
            <h2 className="text-sm font-semibold text-ink-primary flex items-center gap-1.5">
              <BarChart2 className="w-4 h-4 text-metric-blue" />
              <span>Comparative Quality Across Intent Domains</span>
            </h2>
            <p className="text-xs text-ink-secondary mt-0.5">
              Calibrated pass rates derived from deterministic evaluation benchmarks
            </p>
          </div>
          <span className="text-xs text-ink-secondary font-mono">
            Scale: 50% - 100%
          </span>
        </div>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#475569' }} interval={0} angle={-15} textAnchor="end" />
              <YAxis domain={[50, 100]} tick={{ fontSize: 11, fill: '#475569' }} unit="%" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #cbd5e1',
                  borderRadius: '6px',
                  fontSize: '11px',
                  boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.05)',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
              <Bar dataKey="coding" name="Coding Quality" fill="#2563eb" radius={[3, 3, 0, 0]} />
              <Bar dataKey="reasoning" name="Reasoning Quality" fill="#0891b2" radius={[3, 3, 0, 0]} />
              <Bar dataKey="writing" name="Writing Quality" fill="#059669" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Historical Benchmark Runs Table */}
      <div className="bg-white border border-app-border rounded-lg overflow-hidden shadow-xs">
        <div className="p-3.5 border-b border-app-border flex items-center justify-between">
          <div className="text-xs font-semibold text-ink-primary flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-metric-blue" />
            <span>Empirical Benchmark Execution History</span>
          </div>
          <span className="text-xs text-ink-secondary">
            {evalRuns.length} runs recorded
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-app-subtle/50 text-ink-secondary font-semibold text-[11px] border-b border-app-border">
              <tr>
                <th className="py-2.5 px-3">Run ID</th>
                <th className="py-2.5 px-2">Evaluated Model</th>
                <th className="py-2.5 px-2">Provider</th>
                <th className="py-2.5 px-2 text-center">Score</th>
                <th className="py-2.5 px-2 text-center">Passed Prompts</th>
                <th className="py-2.5 px-2 text-center">Avg Latency</th>
                <th className="py-2.5 px-2 text-center">Duration</th>
                <th className="py-2.5 px-2">Timestamp</th>
                <th className="py-2.5 px-3 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-app-border/60">
              {evalRuns.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-ink-secondary text-xs">
                    No benchmark runs recorded yet. Click "Run Eval" on any model above to execute deterministic suite.
                  </td>
                </tr>
              ) : (
                evalRuns.map((r, idx) => (
                  <tr key={idx} className="hover:bg-app-subtle/30 transition-colors">
                    <td className="py-2.5 px-3 font-mono text-ink-secondary text-[11px]">
                      {r.id ? r.id.slice(0, 8) : `run-${idx + 1}`}
                    </td>
                    <td className="py-2.5 px-2 font-medium text-ink-primary font-mono text-[11px]">
                      {r.model_id}
                    </td>
                    <td className="py-2.5 px-2 capitalize text-ink-secondary text-[11px]">
                      {r.provider_name}
                    </td>
                    <td className="py-2.5 px-2 text-center font-mono text-[11px]">
                      <span className="font-semibold text-metric-emerald">
                        {((r.overall_quality_score || 0) * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-2.5 px-2 text-center text-ink-secondary font-mono text-[11px]">
                      {r.passed_prompts} / {r.total_prompts}
                    </td>
                    <td className="py-2.5 px-2 text-center text-metric-amber font-mono text-[11px]">
                      {Math.round(r.avg_latency_ms || 0)} ms
                    </td>
                    <td className="py-2.5 px-2 text-center text-ink-secondary font-mono text-[11px]">
                      {(r.duration_seconds || 0).toFixed(1)}s
                    </td>
                    <td className="py-2.5 px-2 text-ink-secondary text-[11px]">
                      {r.created_at ? new Date(r.created_at).toLocaleTimeString() : 'Recent'}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      {r.id ? (
                        <button
                          onClick={() => handleInspectRun(r.id)}
                          className="px-2 py-0.5 bg-white hover:bg-app-subtle border border-app-border text-ink-primary rounded text-xs inline-flex items-center gap-1 transition-colors cursor-pointer"
                        >
                          <Eye className="w-3 h-3 text-metric-blue" />
                          <span>Inspect</span>
                        </button>
                      ) : (
                        <span className="text-ink-muted text-[11px]">Inline</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Detailed Run Inspector Modal */}
      {selectedRun && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white border border-app-border rounded-xl shadow-xl max-w-3xl w-full max-h-[85vh] flex flex-col text-xs overflow-hidden">
            {/* Modal Header */}
            <div className="p-4 border-b border-app-border flex items-center justify-between bg-app-subtle/50">
              <div className="flex items-center gap-2">
                <FileCode className="w-4 h-4 text-metric-blue" />
                <h3 className="font-semibold text-ink-primary text-xs">
                  Benchmark Run Inspector: {selectedRun.model_id} ({selectedRun.provider_name})
                </h3>
              </div>
              <button
                onClick={() => setSelectedRun(null)}
                className="p-1 rounded hover:bg-app-hover text-ink-muted hover:text-ink-primary transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Run Summary Ribbon */}
            <div className="p-3 bg-app-bg border-b border-app-border grid grid-cols-4 gap-2 text-center text-xs">
              <div>
                <span className="text-ink-secondary block text-[11px]">Quality Score</span>
                <span className="font-bold font-mono text-metric-emerald">
                  {((selectedRun.overall_quality_score || 0) * 100).toFixed(1)}%
                </span>
              </div>
              <div>
                <span className="text-ink-secondary block text-[11px]">Passed / Total</span>
                <span className="font-semibold font-mono text-ink-primary">
                  {selectedRun.passed_prompts} / {selectedRun.total_prompts}
                </span>
              </div>
              <div>
                <span className="text-ink-secondary block text-[11px]">Avg Latency</span>
                <span className="font-semibold font-mono text-metric-amber">
                  {Math.round(selectedRun.avg_latency_ms || 0)} ms
                </span>
              </div>
              <div>
                <span className="text-ink-secondary block text-[11px]">Total Duration</span>
                <span className="font-semibold font-mono text-ink-primary">
                  {(selectedRun.duration_seconds || 0).toFixed(2)}s
                </span>
              </div>
            </div>

            {/* Itemized Prompt Results */}
            <div className="p-4 overflow-y-auto space-y-3 flex-1">
              <div className="text-xs font-semibold text-ink-primary mb-2">
                Itemized Verification Details ({selectedRun.item_details?.length || 0} Test Items)
              </div>
              {selectedRun.item_details && selectedRun.item_details.length > 0 ? (
                selectedRun.item_details.map((item, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded-lg border text-xs ${
                      item.passed
                        ? 'border-emerald-200 bg-emerald-50/40'
                        : 'border-red-200 bg-red-50/40'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${item.passed ? 'bg-emerald-500' : 'bg-red-500'}`} />
                        <span className="font-semibold text-ink-primary">{item.item_id || `Item #${idx + 1}`}</span>
                        <span className="px-1.5 py-0.5 rounded bg-white border border-app-border text-[11px] capitalize text-ink-secondary">
                          {item.category} • {item.complexity}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-[11px] font-mono">
                        <span className="text-metric-amber">{item.latency_ms} ms</span>
                        <span className={`font-semibold ${item.passed ? 'text-emerald-700' : 'text-red-700'}`}>
                          {item.passed ? 'PASSED' : 'FAILED'}
                        </span>
                      </div>
                    </div>

                    {item.response_sample && (
                      <div className="mt-2 bg-white border border-app-border rounded p-2.5 text-xs text-ink-secondary font-mono whitespace-pre-wrap leading-relaxed">
                        {item.response_sample}
                      </div>
                    )}
                    {item.error && (
                      <div className="mt-1.5 text-red-700 text-xs font-mono">
                        Error: {item.error}
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="text-center py-6 text-ink-secondary">
                  No individual item logs saved for this run.
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-3 border-t border-app-border bg-app-subtle/30 flex justify-end">
              <button
                onClick={() => setSelectedRun(null)}
                className="px-3 py-1.5 bg-white hover:bg-app-subtle border border-app-border rounded-md text-ink-primary text-xs cursor-pointer shadow-xs"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Architectural Documentation Notes */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
        <div className="bg-white border border-app-border rounded-lg p-4 space-y-1.5 shadow-xs">
          <div className="text-ink-primary font-semibold">
            Deterministic Evaluation
          </div>
          <p className="text-xs text-ink-secondary leading-relaxed">
            Evaluates outputs through concrete regex parsing, Python AST validity, and required substring inclusion—eliminating subjective hallucination.
          </p>
        </div>

        <div className="bg-white border border-app-border rounded-lg p-4 space-y-1.5 shadow-xs">
          <div className="text-ink-primary font-semibold">
            Multi-Objective Pareto Routing
          </div>
          <p className="text-xs text-ink-secondary leading-relaxed">
            Dynamic complexity weights adapt trade-offs: w_q = 0.70 for complex reasoning/coding, while w_c = 0.45 for fast low-complexity Q&A.
          </p>
        </div>

        <div className="bg-white border border-app-border rounded-lg p-4 space-y-1.5 shadow-xs">
          <div className="text-ink-primary font-semibold">
            Live Feedback Loop
          </div>
          <p className="text-xs text-ink-secondary leading-relaxed">
            Completed benchmark suites immediately update the in-memory ProfileManager, instantly refining all future routing decisions.
          </p>
        </div>
      </div>
    </div>
  );
}
