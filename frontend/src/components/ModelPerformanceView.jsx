import React, { useState, useEffect } from 'react';
import {
  Award, RefreshCw, Play, CheckCircle2, AlertCircle,
  FileCode, Terminal, Search, ExternalLink, Layers,
  Clock, Check, X, Eye, BarChart2
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

  // Prepare chart data for Quality vs Latency/Cost comparison
  const chartData = filtered.map((p) => ({
    name: p.display_name?.replace('OpenAI ', '').replace('Google ', '').replace('Groq ', '') || p.model_id,
    provider: p.provider,
    coding: Math.round((p.coding_quality || 0) * 100),
    reasoning: Math.round((p.reasoning_quality || 0) * 100),
    writing: Math.round((p.writing_quality || 0) * 100),
    latency: Math.round(p.avg_latency_ms || 200),
    cost_in_1k: (p.input_cost_per_1k || 0) * 1000, // scaled for display
  }));

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="bg-app-panel border border-app-border rounded-lg p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono">
        <div>
          <h2 className="text-xs font-mono font-semibold uppercase tracking-wider text-ink-primary flex items-center gap-2">
            <Award className="w-4 h-4 text-metric-blue" />
            Model Capability Registry & Empirical Benchmark Matrix
          </h2>
          <p className="text-[11px] text-ink-muted mt-0.5">
            Empirical quality scores calibrated from deterministic unit tests & structured output assertions
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Provider Filter */}
          <div className="flex items-center gap-1 bg-app-bg p-1 rounded border border-app-border text-[11px]">
            {['all', 'openai', 'groq', 'gemini'].map((prov) => (
              <button
                key={prov}
                onClick={() => setFilterProvider(prov)}
                className={`px-2 py-0.5 rounded uppercase font-semibold transition-colors cursor-pointer ${
                  filterProvider === prov
                    ? 'bg-app-subtle text-ink-primary shadow-sm'
                    : 'text-ink-muted hover:text-ink-secondary'
                }`}
              >
                {prov}
              </button>
            ))}
          </div>

          <button
            onClick={loadAll}
            className="px-2.5 py-1 bg-app-subtle hover:bg-app-hover border border-app-border text-ink-secondary hover:text-ink-primary rounded flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Sync</span>
          </button>

          <button
            onClick={handleResetBaselines}
            title="Restore baseline calibrated empirical scores for all models"
            className="px-2.5 py-1 bg-app-subtle hover:bg-metric-amber/15 border border-app-border text-ink-secondary hover:text-metric-amber rounded flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <span>Reset Baselines</span>
          </button>
        </div>
      </div>

      {/* Live Run Banner */}
      {evaluatingModel && (
        <div className="bg-metric-blue/10 border border-metric-blue/30 rounded-lg p-3 text-xs font-mono text-metric-blue flex items-center gap-2.5">
          <Terminal className="w-4 h-4 animate-spin flex-shrink-0" />
          <span>
            Executing deterministic benchmark test suite against <strong>{evaluatingModel}</strong>...
          </span>
        </div>
      )}

      {evalResult && (
        <div className="bg-metric-emerald/10 border border-metric-emerald/30 rounded-lg p-3 text-xs font-mono text-metric-emerald flex items-center justify-between gap-2.5">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
            <span>
              Evaluation passed: {evalResult.passed_prompts}/{evalResult.total_prompts} items for <strong>{evalResult.model_id}</strong>. Quality score calibrated to {(evalResult.overall_quality_score * 100).toFixed(1)}%. ProfileManager updated.
            </span>
          </div>
          <button
            onClick={() => setEvalResult(null)}
            className="text-[10px] uppercase text-ink-muted hover:text-ink-primary underline cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      )}

      {evalError && (
        <div className="bg-metric-rose/10 border border-metric-rose/30 rounded-lg p-3 text-xs font-mono text-metric-rose flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{evalError}</span>
        </div>
      )}

      {/* Capability Matrix Table */}
      <div className="bg-app-panel border border-app-border rounded-lg overflow-hidden font-mono text-xs">
        <div className="p-3 bg-app-subtle/40 border-b border-app-border flex items-center justify-between">
          <div className="text-[11px] font-semibold text-ink-primary uppercase tracking-wider flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-metric-blue" />
            Empirical Model Capability Profiles
          </div>
          <span className="text-[10px] text-ink-muted">
            {filtered.length} active models registered
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-app-subtle/70 text-ink-muted uppercase tracking-wider text-[10px] border-b border-app-border">
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
                <th className="py-2.5 px-3 text-right">Benchmark Suite</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-app-border/40">
              {filtered.map((p, idx) => (
                <tr key={idx} className="hover:bg-app-subtle/25 transition-colors">
                  <td className="py-2.5 px-3 font-semibold text-ink-primary">
                    <div>{p.display_name}</div>
                    <div className="text-[10px] text-ink-muted font-normal">{p.model_id}</div>
                  </td>

                  <td className="py-2.5 px-2">
                    <span className="px-1.5 py-0.5 rounded bg-app-bg border border-app-border text-[10px] uppercase text-ink-secondary">
                      {p.provider}
                    </span>
                  </td>

                  <td className="py-2.5 px-2 text-center">
                    <span className={`px-1.5 py-0.5 rounded text-[11px] font-bold ${
                      p.coding_quality >= 0.90 ? 'text-metric-emerald' :
                      p.coding_quality >= 0.80 ? 'text-metric-cyan' : 'text-ink-secondary'
                    }`}>
                      {(p.coding_quality * 100).toFixed(0)}%
                    </span>
                  </td>

                  <td className="py-2.5 px-2 text-center">
                    <span className={`px-1.5 py-0.5 rounded text-[11px] font-bold ${
                      p.reasoning_quality >= 0.90 ? 'text-metric-emerald' :
                      p.reasoning_quality >= 0.80 ? 'text-metric-cyan' : 'text-ink-secondary'
                    }`}>
                      {(p.reasoning_quality * 100).toFixed(0)}%
                    </span>
                  </td>

                  <td className="py-2.5 px-2 text-center">
                    <span className={`px-1.5 py-0.5 rounded text-[11px] font-bold ${
                      p.writing_quality >= 0.90 ? 'text-metric-emerald' :
                      p.writing_quality >= 0.80 ? 'text-metric-cyan' : 'text-ink-secondary'
                    }`}>
                      {(p.writing_quality * 100).toFixed(0)}%
                    </span>
                  </td>

                  <td className="py-2.5 px-2 text-center">
                    <span className={`px-1.5 py-0.5 rounded text-[11px] font-bold ${
                      p.general_qa_quality >= 0.90 ? 'text-metric-emerald' :
                      p.general_qa_quality >= 0.80 ? 'text-metric-cyan' : 'text-ink-secondary'
                    }`}>
                      {(p.general_qa_quality * 100).toFixed(0)}%
                    </span>
                  </td>

                  <td className="py-2.5 px-2 text-center text-metric-amber">
                    {p.avg_latency_ms ? `${Math.round(p.avg_latency_ms)} ms` : '—'}
                  </td>

                  <td className="py-2.5 px-2 text-right text-ink-primary">
                    ${Number(p.input_cost_per_1k || 0).toFixed(5)}
                  </td>

                  <td className="py-2.5 px-2 text-right text-ink-primary">
                    ${Number(p.output_cost_per_1k || 0).toFixed(5)}
                  </td>

                  <td className="py-2.5 px-2 text-center text-metric-emerald">
                    {((p.reliability || 0.99) * 100).toFixed(1)}%
                  </td>

                  <td className="py-2.5 px-3 text-right">
                    <button
                      onClick={() => handleRunEval(p.model_id, p.provider)}
                      disabled={evaluatingModel === p.model_id}
                      className="px-2.5 py-1 bg-app-subtle hover:bg-app-hover border border-app-border text-ink-primary rounded inline-flex items-center gap-1.5 transition-colors cursor-pointer text-[11px]"
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
      <div className="bg-app-panel border border-app-border rounded-lg p-4 font-mono text-xs">
        <div className="flex items-center justify-between mb-3">
          <div className="text-[11px] font-semibold text-ink-primary uppercase tracking-wider flex items-center gap-1.5">
            <BarChart2 className="w-3.5 h-3.5 text-metric-blue" />
            Quality Profile Comparison Across Task Categories (%)
          </div>
          <span className="text-[10px] text-ink-muted">
            Higher is better • Deterministically scored
          </span>
        </div>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748b' }} interval={0} angle={-15} textAnchor="end" />
              <YAxis domain={[50, 100]} tick={{ fontSize: 10, fill: '#64748b' }} unit="%" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #cbd5e1',
                  borderRadius: '6px',
                  fontSize: '11px',
                  fontFamily: 'monospace',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
              <Bar dataKey="coding" name="Coding Quality" fill="#3b82f6" radius={[3, 3, 0, 0]} />
              <Bar dataKey="reasoning" name="Reasoning Quality" fill="#8b5cf6" radius={[3, 3, 0, 0]} />
              <Bar dataKey="writing" name="Writing Quality" fill="#10b981" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Historical Benchmark Runs Table */}
      <div className="bg-app-panel border border-app-border rounded-lg overflow-hidden font-mono text-xs">
        <div className="p-3 bg-app-subtle/40 border-b border-app-border flex items-center justify-between">
          <div className="text-[11px] font-semibold text-ink-primary uppercase tracking-wider flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-metric-blue" />
            Empirical Benchmark Execution History
          </div>
          <span className="text-[10px] text-ink-muted">
            {evalRuns.length} runs recorded in persistent store
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-app-subtle/70 text-ink-muted uppercase tracking-wider text-[10px] border-b border-app-border">
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
            <tbody className="divide-y divide-app-border/40">
              {evalRuns.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-ink-muted">
                    No benchmark runs recorded yet. Click "Run Eval" on any model above to execute deterministic suite.
                  </td>
                </tr>
              ) : (
                evalRuns.map((r, idx) => (
                  <tr key={idx} className="hover:bg-app-subtle/25 transition-colors">
                    <td className="py-2.5 px-3 text-ink-muted text-[10px]">
                      {r.id ? r.id.slice(0, 8) + '...' : `run-${idx + 1}`}
                    </td>
                    <td className="py-2.5 px-2 font-semibold text-ink-primary">
                      {r.model_id}
                    </td>
                    <td className="py-2.5 px-2 uppercase text-ink-secondary text-[10px]">
                      {r.provider_name}
                    </td>
                    <td className="py-2.5 px-2 text-center">
                      <span className="px-1.5 py-0.5 rounded text-[11px] font-bold text-metric-emerald bg-metric-emerald/10 border border-metric-emerald/20">
                        {((r.overall_quality_score || 0) * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-2.5 px-2 text-center text-ink-secondary">
                      {r.passed_prompts} / {r.total_prompts}
                    </td>
                    <td className="py-2.5 px-2 text-center text-metric-amber">
                      {Math.round(r.avg_latency_ms || 0)} ms
                    </td>
                    <td className="py-2.5 px-2 text-center text-ink-muted">
                      {(r.duration_seconds || 0).toFixed(1)}s
                    </td>
                    <td className="py-2.5 px-2 text-ink-muted text-[10px]">
                      {r.created_at ? new Date(r.created_at).toLocaleTimeString() : 'Recent'}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      {r.id ? (
                        <button
                          onClick={() => handleInspectRun(r.id)}
                          className="px-2 py-0.5 bg-app-subtle hover:bg-app-hover border border-app-border text-ink-primary rounded inline-flex items-center gap-1 transition-colors cursor-pointer text-[10px]"
                        >
                          <Eye className="w-3 h-3 text-metric-blue" />
                          <span>Inspect</span>
                        </button>
                      ) : (
                        <span className="text-ink-faint text-[10px]">Inline</span>
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
          <div className="bg-app-panel border border-app-border rounded-xl shadow-2xl max-w-3xl w-full max-h-[85vh] flex flex-col font-mono text-xs overflow-hidden">
            {/* Modal Header */}
            <div className="p-4 border-b border-app-border flex items-center justify-between bg-app-subtle/50">
              <div className="flex items-center gap-2">
                <FileCode className="w-4 h-4 text-metric-blue" />
                <h3 className="font-semibold text-ink-primary text-xs uppercase tracking-wider">
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
            <div className="p-3 bg-app-bg border-b border-app-border grid grid-cols-4 gap-2 text-center text-[11px]">
              <div>
                <span className="text-ink-muted block text-[10px]">Score</span>
                <span className="font-bold text-metric-emerald">
                  {((selectedRun.overall_quality_score || 0) * 100).toFixed(1)}%
                </span>
              </div>
              <div>
                <span className="text-ink-muted block text-[10px]">Passed / Total</span>
                <span className="font-semibold text-ink-primary">
                  {selectedRun.passed_prompts} / {selectedRun.total_prompts}
                </span>
              </div>
              <div>
                <span className="text-ink-muted block text-[10px]">Avg Latency</span>
                <span className="font-semibold text-metric-amber">
                  {Math.round(selectedRun.avg_latency_ms || 0)} ms
                </span>
              </div>
              <div>
                <span className="text-ink-muted block text-[10px]">Duration</span>
                <span className="font-semibold text-ink-primary">
                  {(selectedRun.duration_seconds || 0).toFixed(2)}s
                </span>
              </div>
            </div>

            {/* Itemized Prompt Results */}
            <div className="p-4 overflow-y-auto space-y-3 flex-1">
              <div className="text-[11px] font-semibold text-ink-primary uppercase tracking-wider mb-2">
                Itemized Verification Details ({selectedRun.item_details?.length || 0} Test Items)
              </div>
              {selectedRun.item_details && selectedRun.item_details.length > 0 ? (
                selectedRun.item_details.map((item, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded-lg border text-xs ${
                      item.passed
                        ? 'border-metric-emerald/30 bg-metric-emerald/5'
                        : 'border-metric-rose/30 bg-metric-rose/5'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${item.passed ? 'bg-metric-emerald' : 'bg-metric-rose'}`} />
                        <span className="font-bold text-ink-primary">{item.item_id || `Item #${idx + 1}`}</span>
                        <span className="px-1.5 py-0.2 rounded bg-app-bg border border-app-border text-[10px] uppercase text-ink-secondary">
                          {item.category} • {item.complexity}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-[10px]">
                        <span className="text-metric-amber">{item.latency_ms} ms</span>
                        <span className={`font-bold uppercase ${item.passed ? 'text-metric-emerald' : 'text-metric-rose'}`}>
                          {item.passed ? 'PASSED' : 'FAILED'}
                        </span>
                      </div>
                    </div>

                    {item.response_sample && (
                      <div className="mt-2 bg-app-panel border border-app-border rounded p-2 text-[11px] text-ink-secondary font-mono whitespace-pre-wrap">
                        {item.response_sample}
                      </div>
                    )}
                    {item.error && (
                      <div className="mt-1 text-metric-rose text-[10px]">
                        Error: {item.error}
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="text-center py-6 text-ink-muted">
                  No individual item logs saved for this run.
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-3 border-t border-app-border bg-app-subtle/30 flex justify-end">
              <button
                onClick={() => setSelectedRun(null)}
                className="px-3 py-1 bg-app-panel hover:bg-app-hover border border-app-border rounded text-ink-primary text-xs cursor-pointer"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Architectural Documentation Notes */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
        <div className="bg-app-panel border border-app-border rounded-lg p-3.5 space-y-1">
          <div className="text-ink-primary font-bold text-[11px] uppercase tracking-wider">
            Deterministic Evaluation
          </div>
          <p className="text-[11px] text-ink-muted leading-relaxed">
            Evaluates outputs through concrete regex parsing, Python AST validity, and required substring inclusion—eliminating subjective hallucination.
          </p>
        </div>

        <div className="bg-app-panel border border-app-border rounded-lg p-3.5 space-y-1">
          <div className="text-ink-primary font-bold text-[11px] uppercase tracking-wider">
            Multi-Objective Pareto Routing
          </div>
          <p className="text-[11px] text-ink-muted leading-relaxed">
            Dynamic complexity weights adapt trade-offs: w_q = 0.60 for complex reasoning/coding, while w_c = 0.45 for fast low-complexity Q&A.
          </p>
        </div>

        <div className="bg-app-panel border border-app-border rounded-lg p-3.5 space-y-1">
          <div className="text-ink-primary font-bold text-[11px] uppercase tracking-wider">
            Live Feedback Loop
          </div>
          <p className="text-[11px] text-ink-muted leading-relaxed">
            Completed benchmark suites immediately mutate the in-memory ProfileManager, instantly refining all future routing decisions.
          </p>
        </div>
      </div>
    </div>
  );
}
