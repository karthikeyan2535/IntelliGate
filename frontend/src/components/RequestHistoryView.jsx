import React, { useState, useEffect } from 'react';
import {
  FileText, RefreshCw, Eye, X, CheckCircle2,
  Copy, Check, Clock, ShieldAlert, Terminal, Layers
} from 'lucide-react';
import { fetchCodingSubmissions, fetchCodingSubmissionDetails } from '../services/api';

export default function RequestHistoryView({ onNavigate }) {
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSub, setSelectedSub] = useState(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [copiedId, setCopiedId] = useState(null);

  useEffect(() => {
    loadSubmissions();
  }, []);

  async function loadSubmissions() {
    setLoading(true);
    try {
      const data = await fetchCodingSubmissions(50);
      setSubmissions(data || []);
    } catch (err) {
      console.error('Failed to load submissions', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleInspect(id) {
    setLoadingDetails(true);
    try {
      const details = await fetchCodingSubmissionDetails(id);
      setSelectedSub(details);
    } catch (err) {
      console.error('Failed to load submission details', err);
    } finally {
      setLoadingDetails(false);
    }
  }

  function copyId(id) {
    navigator.clipboard.writeText(id);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 1500);
  }

  return (
    <div className="space-y-4 font-sans text-xs">
      {/* Header */}
      <div className="bg-white border border-app-border rounded-lg p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
        <div>
          <h2 className="text-sm font-semibold text-ink-primary flex items-center gap-2">
            <FileText className="w-4 h-4 text-metric-blue" />
            Execution History & Verification Audit Logs
          </h2>
          <p className="text-xs text-ink-secondary mt-0.5">
            Immutable log of all programming problem executions, compiler diagnostics, and escalation decisions
          </p>
        </div>

        <button
          onClick={loadSubmissions}
          disabled={loading}
          className="px-2.5 py-1.5 bg-white hover:bg-app-subtle border border-app-border text-ink-secondary hover:text-ink-primary rounded-md flex items-center gap-1.5 transition-colors cursor-pointer text-xs"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : 'text-ink-muted'}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Submissions Table */}
      <div className="bg-white border border-app-border rounded-lg overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-app-subtle/50 text-ink-secondary font-semibold text-[11px] border-b border-app-border">
              <tr>
                <th className="py-2.5 px-3">Submission ID</th>
                <th className="py-2.5 px-2">Language</th>
                <th className="py-2.5 px-2">Routing Mode</th>
                <th className="py-2.5 px-2">Initial Model</th>
                <th className="py-2.5 px-2">Final Model</th>
                <th className="py-2.5 px-2 text-center">Attempts</th>
                <th className="py-2.5 px-2 text-center">Outcome</th>
                <th className="py-2.5 px-2 text-right">Cost</th>
                <th className="py-2.5 px-2 text-center">Latency</th>
                <th className="py-2.5 px-2">Timestamp</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-app-border/60">
              {submissions.length === 0 ? (
                <tr>
                  <td colSpan={11}>
                    <div className="flex flex-col items-center justify-center py-16 text-ink-secondary text-xs">
                      <FileText className="w-8 h-8 mb-3 text-ink-muted" />
                      <p>No coding executions recorded yet. Submit a problem in the Coding Playground.</p>
                    </div>
                  </td>
                </tr>
              ) : (
                submissions.map((sub, idx) => (
                  <tr key={idx} className="hover:bg-app-subtle/30 transition-colors">
                    <td className="py-2.5 px-3">
                      <button
                        onClick={() => copyId(sub.id)}
                        className="text-ink-primary hover:text-metric-blue flex items-center gap-1 font-mono text-[11px] cursor-pointer"
                        title="Copy submission ID"
                      >
                        <span>{sub.id.slice(0, 8)}...</span>
                        {copiedId === sub.id ? (
                          <Check className="w-3 h-3 text-metric-emerald" />
                        ) : (
                          <Copy className="w-3 h-3 text-ink-muted" />
                        )}
                      </button>
                    </td>

                    <td className="py-2.5 px-2 capitalize font-medium text-ink-secondary">
                      {sub.language}
                    </td>

                    <td className="py-2.5 px-2 capitalize text-ink-secondary">
                      {sub.routing_mode.replace('_', ' ')}
                    </td>

                    <td className="py-2.5 px-2 font-mono text-[11px] text-ink-secondary">
                      {sub.initial_model || '—'}
                    </td>

                    <td className="py-2.5 px-2 font-mono text-[11px] font-medium text-ink-primary">
                      {sub.final_model || '—'}
                    </td>

                    <td className="py-2.5 px-2 text-center font-mono text-xs font-semibold text-metric-blue">
                      {sub.total_attempts}
                    </td>

                    <td className="py-2.5 px-2 text-center">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        sub.status === 'accepted'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-red-50 text-red-700 border border-red-200'
                      }`}>
                        {sub.status}
                      </span>
                    </td>

                    <td className="py-2.5 px-2 text-right font-mono text-xs text-metric-emerald font-semibold">
                      ${sub.total_cost_usd.toFixed(5)}
                    </td>

                    <td className="py-2.5 px-2 text-center font-mono text-xs text-metric-amber">
                      {sub.total_latency_ms} ms
                    </td>

                    <td className="py-2.5 px-2 text-ink-secondary text-[11px]">
                      {sub.created_at ? new Date(sub.created_at).toLocaleTimeString() : 'Recent'}
                    </td>

                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={() => handleInspect(sub.id)}
                        className="px-2.5 py-1 bg-white hover:bg-app-subtle border border-app-border text-ink-primary rounded text-xs inline-flex items-center gap-1 transition-colors cursor-pointer"
                      >
                        <Eye className="w-3 h-3 text-metric-blue" />
                        <span>Inspect</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Execution Trace & Attempt Details Modal */}
      {selectedSub && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white border border-app-border rounded-xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-xl overflow-hidden font-sans">
            {/* Header */}
            <div className="p-4 border-b border-app-border flex items-center justify-between bg-app-subtle/50">
              <div>
                <h3 className="text-xs font-semibold text-ink-primary flex items-center gap-2">
                  <span>Execution Audit Details:</span>
                  <span className="text-metric-blue font-mono">{selectedSub.id}</span>
                </h3>
                <p className="text-[11px] text-ink-secondary mt-0.5">
                  Language: {selectedSub.language.toUpperCase()} • Mode: {selectedSub.routing_mode} • Status: {selectedSub.status.toUpperCase()}
                </p>
              </div>
              <button
                onClick={() => setSelectedSub(null)}
                className="text-ink-muted hover:text-ink-primary p-1 rounded hover:bg-app-subtle transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-4 overflow-y-auto space-y-4 text-xs">
              {/* Summary Stats */}
              <div className="grid grid-cols-4 gap-px bg-app-border border border-app-border rounded-lg overflow-hidden text-center">
                <div className="bg-app-bg p-2.5">
                  <span className="text-[10px] text-ink-secondary block">Attempts</span>
                  <span className="text-xs font-bold font-mono text-metric-blue mt-0.5 block">
                    {selectedSub.total_attempts}
                  </span>
                </div>
                <div className="bg-app-bg p-2.5">
                  <span className="text-[10px] text-ink-secondary block">Tests Passed</span>
                  <span className="text-xs font-bold font-mono text-ink-primary mt-0.5 block">
                    {selectedSub.passed_test_cases} / {selectedSub.total_test_cases}
                  </span>
                </div>
                <div className="bg-app-bg p-2.5">
                  <span className="text-[10px] text-ink-secondary block">Total Cost</span>
                  <span className="text-xs font-bold font-mono text-metric-emerald mt-0.5 block">
                    ${selectedSub.total_cost_usd.toFixed(5)}
                  </span>
                </div>
                <div className="bg-app-bg p-2.5">
                  <span className="text-[10px] text-ink-secondary block">Latency</span>
                  <span className="text-xs font-bold font-mono text-metric-amber mt-0.5 block">
                    {selectedSub.total_latency_ms} ms
                  </span>
                </div>
              </div>

              {/* Attempts Breakdown */}
              <div className="space-y-2">
                <span className="text-xs font-semibold text-ink-primary block">
                  Model Generation Attempts ({selectedSub.attempts?.length || 0})
                </span>
                {selectedSub.attempts?.map((att, idx) => (
                  <div key={idx} className="p-3 bg-app-subtle/40 border border-app-border rounded-md space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-ink-primary">Attempt #{att.attempt_number}</span>
                        <span className="font-mono text-[11px] text-ink-secondary">({att.model_id} - {att.provider_name})</span>
                      </div>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        att.execution_status === 'accepted' ? 'text-emerald-700 bg-emerald-50' : 'text-red-700 bg-red-50'
                      }`}>
                        {att.execution_status}
                      </span>
                    </div>

                    {att.routing_reason && (
                      <p className="text-[11px] text-ink-secondary border-l-2 border-blue-500 pl-2">
                        {att.routing_reason}
                      </p>
                    )}

                    {att.generated_code && (
                      <pre className="bg-slate-950 text-slate-100 p-2.5 rounded font-mono text-[11px] max-h-36 overflow-y-auto leading-relaxed">
                        {att.generated_code}
                      </pre>
                    )}

                    {att.error_message && (
                      <p className="text-xs text-red-700 font-mono">
                        Error: {att.error_message}
                      </p>
                    )}
                  </div>
                ))}
              </div>

              {/* Pipeline Waterfall Trace */}
              {selectedSub.trace?.length > 0 && (
                <div className="space-y-1.5 pt-2 border-t border-app-border">
                  <span className="text-xs font-semibold text-ink-primary block">
                    Pipeline Waterfall Trace
                  </span>
                  <div className="space-y-1">
                    {selectedSub.trace.map((st, idx) => (
                      <div key={idx} className="p-2 bg-app-subtle/30 border border-app-border rounded flex items-center justify-between text-[11px]">
                        <span className="font-medium text-ink-primary capitalize">{st.stage.replace(/_/g, ' ')}</span>
                        <span className="text-ink-secondary font-mono">{st.status}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-3 border-t border-app-border bg-app-subtle/40 flex justify-end">
              <button
                onClick={() => setSelectedSub(null)}
                className="px-3 py-1.5 bg-white hover:bg-app-subtle border border-app-border text-ink-primary rounded-md text-xs cursor-pointer shadow-xs"
              >
                Close Audit View
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
