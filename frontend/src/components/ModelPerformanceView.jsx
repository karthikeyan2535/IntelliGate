import React, { useState, useEffect } from 'react';
import {
  Award, RefreshCw, Play, CheckCircle2, AlertCircle,
  FileCode, Terminal, Search, ExternalLink, Layers
} from 'lucide-react';
import { fetchModelProfiles, runEvaluationSuite } from '../services/api';

export default function ModelPerformanceView() {
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [evaluatingModel, setEvaluatingModel] = useState(null);
  const [evalResult, setEvalResult] = useState(null);
  const [evalError, setEvalError] = useState(null);
  const [filterProvider, setFilterProvider] = useState('all');

  useEffect(() => {
    loadProfiles();
  }, []);

  async function loadProfiles() {
    setLoading(true);
    try {
      const data = await fetchModelProfiles();
      setProfiles(data);
    } catch (err) {
      console.error('Failed to load profiles', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleRunEval(modelId, provider) {
    setEvaluatingModel(modelId);
    setEvalError(null);
    setEvalResult(null);

    try {
      const result = await runEvaluationSuite(modelId, provider, 12);
      setEvalResult(result);
      await loadProfiles();
    } catch (err) {
      console.error('Evaluation run error', err);
      setEvalError(err.message || 'Evaluation run failed');
    } finally {
      setEvaluatingModel(null);
    }
  }

  const filtered = profiles.filter((p) => {
    if (filterProvider === 'all') return true;
    return p.provider?.toLowerCase() === filterProvider.toLowerCase();
  });

  return (
    <div className="space-y-5">
      {/* Action Header & Provider Filter */}
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
                    ? 'bg-app-subtle text-ink-primary'
                    : 'text-ink-muted hover:text-ink-secondary'
                }`}
              >
                {prov}
              </button>
            ))}
          </div>

          <button
            onClick={loadProfiles}
            className="px-2.5 py-1 bg-app-subtle hover:bg-app-hover border border-app-border text-ink-secondary hover:text-ink-primary rounded flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Sync</span>
          </button>
        </div>
      </div>

      {/* Live Run Banner */}
      {evaluatingModel && (
        <div className="bg-metric-blue/10 border border-metric-blue/30 rounded-lg p-3 text-xs font-mono text-metric-blue flex items-center gap-2.5">
          <Terminal className="w-4 h-4 animate-spin flex-shrink-0" />
          <span>
            Executing deterministic benchmark test suite against <strong className="text-white">{evaluatingModel}</strong>...
          </span>
        </div>
      )}

      {evalResult && (
        <div className="bg-metric-emerald/10 border border-metric-emerald/30 rounded-lg p-3 text-xs font-mono text-metric-emerald flex items-center justify-between gap-2.5">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
            <span>
              Evaluation passed: {evalResult.passed_prompts}/{evalResult.total_prompts} items for <strong className="text-white">{evalResult.model_id}</strong>. Overall quality calibrated to {(evalResult.overall_quality_score * 100).toFixed(1)}%.
            </span>
          </div>
          <button
            onClick={() => setEvalResult(null)}
            className="text-[10px] uppercase text-ink-muted hover:text-white underline"
          >
            Close
          </button>
        </div>
      )}

      {evalError && (
        <div className="bg-metric-rose/10 border border-metric-rose/30 rounded-lg p-3 text-xs font-mono text-metric-rose flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{evalError}</span>
        </div>
      )}

      {/* Main Capability Matrix Table */}
      <div className="bg-app-panel border border-app-border rounded-lg overflow-hidden font-mono text-xs">
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
                    {p.avg_latency_ms?.toFixed(0) || 200} ms
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
            Dynamic complexity weights adapt trade-offs: $w_q = 0.60$ for complex reasoning/coding, while $w_c = 0.45$ for fast low-complexity Q&A.
          </p>
        </div>

        <div className="bg-app-panel border border-app-border rounded-lg p-3.5 space-y-1">
          <div className="text-ink-primary font-bold text-[11px] uppercase tracking-wider">
            Live Feedback Loop
          </div>
          <p className="text-[11px] text-ink-muted leading-relaxed">
            Completed benchmark suites immediately mutate the in-memory <code>ProfileManager</code>, instantly refining all future routing decisions.
          </p>
        </div>
      </div>
    </div>
  );
}
