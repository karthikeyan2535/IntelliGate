import React, { useState, useEffect } from 'react';
import {
  Award, Zap, DollarSign, Clock, ShieldCheck, Play,
  CheckCircle2, AlertCircle, RefreshCw, Database, FileText
} from 'lucide-react';
import { fetchModelProfiles, runEvaluationSuite } from '../services/api';

export default function ModelPerformanceView() {
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [evaluatingModel, setEvaluatingModel] = useState(null);
  const [evalResult, setEvalResult] = useState(null);
  const [evalError, setEvalError] = useState(null);

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
      // Reload profiles to show dynamically updated scores
      await loadProfiles();
    } catch (err) {
      console.error('Evaluation run failed', err);
      setEvalError(err.message || 'Evaluation failed');
    } finally {
      setEvaluatingModel(null);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Award className="w-5 h-5 text-indigo-400" />
            Empirical Model Performance & Evaluation Matrix
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Real benchmark scores across Coding, Reasoning, Writing, and QA. These live profiles directly calibrate the Intelligent Routing Engine's multi-objective utility functions.
          </p>
        </div>
        <button
          onClick={loadProfiles}
          className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg flex items-center gap-2 border border-slate-700 transition-colors cursor-pointer self-start md:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh Profiles
        </button>
      </div>

      {/* Live Evaluation Run Feedback Banner */}
      {evaluatingModel && (
        <div className="bg-indigo-500/10 border border-indigo-500/30 rounded-xl p-4 flex items-center gap-3 text-xs text-indigo-300">
          <Zap className="w-5 h-5 animate-spin text-indigo-400" />
          <div>
            <span className="font-semibold">Executing Benchmark Evaluation Suite:</span> Running 12 multi-category benchmark prompts through <strong className="font-mono">{evaluatingModel}</strong>...
          </div>
        </div>
      )}

      {evalResult && (
        <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-emerald-300">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
            <div>
              <span className="font-semibold">Evaluation Run Succeeded:</span> Evaluated {evalResult.passed_prompts}/{evalResult.total_prompts} items for <span className="font-mono font-bold">{evalResult.model_id}</span>.
              Score updated to <strong>{(evalResult.overall_quality_score * 100).toFixed(1)}%</strong> in active router profile.
            </div>
          </div>
          <button
            onClick={() => setEvalResult(null)}
            className="text-[11px] underline text-emerald-400 hover:text-emerald-300"
          >
            Dismiss
          </button>
        </div>
      )}

      {evalError && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-center gap-3 text-xs text-red-300">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
          <div>
            <span className="font-semibold">Evaluation Error:</span> {evalError}
          </div>
        </div>
      )}

      {/* Capability & Benchmark Profiles Table */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl overflow-hidden">
        <div className="p-4 border-b border-slate-800">
          <h3 className="text-sm font-semibold text-white">Registered Model Profiles</h3>
          <p className="text-xs text-slate-400 mt-0.5">Category quality scores calibrated from deterministic tests & structured validators</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/70 text-slate-400 uppercase tracking-wider text-[10px] border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Model & Provider</th>
                <th className="py-3 px-3 text-center">Coding</th>
                <th className="py-3 px-3 text-center">Reasoning</th>
                <th className="py-3 px-3 text-center">Writing</th>
                <th className="py-3 px-3 text-center">General Q&A</th>
                <th className="py-3 px-3 text-center">Avg Latency</th>
                <th className="py-3 px-3 text-center">Cost / 1K</th>
                <th className="py-3 px-3 text-center">Reliability</th>
                <th className="py-3 px-4 text-right">Run Evaluation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {profiles.map((p, idx) => (
                <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3 px-4">
                    <div className="font-semibold text-white flex items-center gap-1.5">
                      {p.display_name}
                      <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                        {p.provider}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 font-mono mt-0.5 truncate max-w-xs">
                      {p.model_id}
                    </div>
                  </td>

                  {/* Benchmark Quality Scores with color bars */}
                  <td className="py-3 px-3 text-center font-mono">
                    <span className={`px-2 py-0.5 rounded font-bold ${
                      p.coding_quality >= 0.90 ? 'bg-indigo-500/20 text-indigo-300' :
                      p.coding_quality >= 0.80 ? 'bg-sky-500/20 text-sky-300' : 'bg-slate-800 text-slate-400'
                    }`}>
                      {(p.coding_quality * 100).toFixed(0)}%
                    </span>
                  </td>

                  <td className="py-3 px-3 text-center font-mono">
                    <span className={`px-2 py-0.5 rounded font-bold ${
                      p.reasoning_quality >= 0.90 ? 'bg-indigo-500/20 text-indigo-300' :
                      p.reasoning_quality >= 0.80 ? 'bg-sky-500/20 text-sky-300' : 'bg-slate-800 text-slate-400'
                    }`}>
                      {(p.reasoning_quality * 100).toFixed(0)}%
                    </span>
                  </td>

                  <td className="py-3 px-3 text-center font-mono">
                    <span className={`px-2 py-0.5 rounded font-bold ${
                      p.writing_quality >= 0.90 ? 'bg-indigo-500/20 text-indigo-300' :
                      p.writing_quality >= 0.80 ? 'bg-sky-500/20 text-sky-300' : 'bg-slate-800 text-slate-400'
                    }`}>
                      {(p.writing_quality * 100).toFixed(0)}%
                    </span>
                  </td>

                  <td className="py-3 px-3 text-center font-mono">
                    <span className={`px-2 py-0.5 rounded font-bold ${
                      p.general_qa_quality >= 0.90 ? 'bg-indigo-500/20 text-indigo-300' :
                      p.general_qa_quality >= 0.80 ? 'bg-sky-500/20 text-sky-300' : 'bg-slate-800 text-slate-400'
                    }`}>
                      {(p.general_qa_quality * 100).toFixed(0)}%
                    </span>
                  </td>

                  <td className="py-3 px-3 text-center font-mono text-amber-300">
                    {p.avg_latency_ms?.toFixed(0) || 200} ms
                  </td>

                  <td className="py-3 px-3 text-center font-mono text-emerald-400">
                    ${Number(p.input_cost_per_1k || 0.001).toFixed(5)}
                  </td>

                  <td className="py-3 px-3 text-center font-mono text-purple-300">
                    {((p.reliability || 0.99) * 100).toFixed(1)}%
                  </td>

                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => handleRunEval(p.model_id, p.provider)}
                      disabled={evaluatingModel === p.model_id}
                      className="px-3 py-1 bg-indigo-600/80 hover:bg-indigo-600 disabled:opacity-50 text-white font-medium rounded-md inline-flex items-center gap-1.5 transition-colors cursor-pointer"
                    >
                      {evaluatingModel === p.model_id ? (
                        <Zap className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Play className="w-3.5 h-3.5 fill-current" />
                      )}
                      <span>Evaluate</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Benchmark Methodology Details */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4">
          <div className="flex items-center gap-2 text-indigo-400 font-semibold mb-1">
            <FileText className="w-4 h-4" />
            24 Curated Benchmark Prompts
          </div>
          <p className="text-slate-400 leading-relaxed">
            Covers synthetic unit tests, algorithmic proofs, long-form creative writing, and factual queries.
          </p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4">
          <div className="flex items-center gap-2 text-emerald-400 font-semibold mb-1">
            <CheckCircle2 className="w-4 h-4" />
            Deterministic Validation
          </div>
          <p className="text-slate-400 leading-relaxed">
            Tests syntax correctness, regex pattern matching, and expected semantic entity inclusion without hallucinated scores.
          </p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4">
          <div className="flex items-center gap-2 text-amber-400 font-semibold mb-1">
            <Zap className="w-4 h-4" />
            Dynamic Router Feedback Loop
          </div>
          <p className="text-slate-400 leading-relaxed">
            Benchmark results immediately update in-memory profiles, altering future multi-objective routing decisions.
          </p>
        </div>
      </div>
    </div>
  );
}
