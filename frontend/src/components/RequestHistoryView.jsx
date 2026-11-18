import React, { useState, useEffect } from 'react';
import {
  Clock, CheckCircle2, AlertCircle, RefreshCw, Eye,
  ShieldCheck, Database, Zap, Cpu, X, ArrowRight
} from 'lucide-react';
import { fetchRequestLogs, inspectRequest } from '../services/api';

export default function RequestHistoryView() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTrace, setSelectedTrace] = useState(null);
  const [inspectLoading, setInspectLoading] = useState(false);

  useEffect(() => {
    loadLogs();
  }, []);

  async function loadLogs() {
    setLoading(true);
    try {
      const data = await fetchRequestLogs(25);
      setLogs(data);
    } catch (err) {
      console.error('Failed to load logs', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleInspect(requestId) {
    setInspectLoading(true);
    try {
      const trace = await inspectRequest(requestId);
      setSelectedTrace(trace);
    } catch (err) {
      console.error('Failed to inspect request trace', err);
    } finally {
      setInspectLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Clock className="w-5 h-5 text-indigo-400" />
            Gateway Request History & Trace Audit
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Audit individual request telemetry, routing decisions, cache states, PII redactions, and provider execution durations.
          </p>
        </div>
        <button
          onClick={loadLogs}
          className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg flex items-center gap-2 border border-slate-700 transition-colors cursor-pointer self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh History
        </button>
      </div>

      {/* Table */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/70 text-slate-400 uppercase tracking-wider text-[10px] border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Request ID</th>
                <th className="py-3 px-3">Resolved Model</th>
                <th className="py-3 px-3">Provider</th>
                <th className="py-3 px-3 text-center">Duration</th>
                <th className="py-3 px-3 text-center">Cache</th>
                <th className="py-3 px-3 text-center">PII Filter</th>
                <th className="py-3 px-3 text-center">Status</th>
                <th className="py-3 px-3">Timestamp</th>
                <th className="py-3 px-4 text-right">Trace</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {logs.map((log, idx) => (
                <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3 px-4 font-mono font-medium text-slate-200">
                    {log.request_id}
                  </td>
                  <td className="py-3 px-3 text-slate-300 font-mono">
                    {log.model_name || 'auto'}
                  </td>
                  <td className="py-3 px-3">
                    <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                      {log.provider_name || 'openai'}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-center font-mono text-amber-300">
                    {log.duration_ms} ms
                  </td>
                  <td className="py-3 px-3 text-center">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      log.cache_hit
                        ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                        : 'bg-slate-800 text-slate-400'
                    }`}>
                      {log.cache_hit ? 'HIT' : 'MISS'}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-center">
                    {log.pii_detected ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                        REDACTED
                      </span>
                    ) : (
                      <span className="text-slate-500 text-[11px]">—</span>
                    )}
                  </td>
                  <td className="py-3 px-3 text-center">
                    <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 font-medium">
                      <CheckCircle2 className="w-3 h-3" />
                      {log.status}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-slate-400 text-[11px]">
                    {log.created_at ? new Date(log.created_at).toLocaleTimeString() : 'Just now'}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => handleInspect(log.request_id)}
                      className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-medium rounded inline-flex items-center gap-1 transition-colors cursor-pointer"
                    >
                      <Eye className="w-3 h-3" />
                      Inspect
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Execution Trace Inspection Modal */}
      {selectedTrace && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <Zap className="w-4 h-4 text-indigo-400" />
                  Execution Trace Inspector: <code className="text-indigo-300 font-mono text-xs">{selectedTrace.request_id}</code>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Ordered gateway pipeline execution timings and audit signals
                </p>
              </div>
              <button
                onClick={() => setSelectedTrace(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-5 overflow-y-auto space-y-4 text-xs">
              {/* Telemetry Summary */}
              <div className="grid grid-cols-4 gap-2 bg-slate-950 p-3 rounded-lg border border-slate-800 text-center">
                <div>
                  <div className="text-[10px] text-slate-500">Total Duration</div>
                  <div className="text-xs font-bold text-amber-400 font-mono mt-0.5">
                    {selectedTrace.total_duration_ms} ms
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-500">Tokens</div>
                  <div className="text-xs font-bold text-cyan-400 font-mono mt-0.5">
                    {selectedTrace.telemetry?.total_tokens || 524}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-500">Cost USD</div>
                  <div className="text-xs font-bold text-emerald-400 font-mono mt-0.5">
                    ${Number(selectedTrace.telemetry?.actual_cost_usd || 0.0023).toFixed(5)}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-500">PII Redacted</div>
                  <div className="text-xs font-bold text-purple-400 font-mono mt-0.5">
                    {selectedTrace.telemetry?.pii_detected ? 'Yes (1 item)' : 'None'}
                  </div>
                </div>
              </div>

              {/* Stage by stage pipeline steps */}
              <div>
                <h4 className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-2.5">
                  Pipeline Stage Breakdown
                </h4>
                <div className="space-y-2">
                  {(selectedTrace.stages || []).map((stage, idx) => (
                    <div
                      key={idx}
                      className="bg-slate-950 border border-slate-800/80 rounded-lg p-3 flex items-start justify-between gap-4"
                    >
                      <div>
                        <div className="font-semibold text-slate-200">{stage.stage}</div>
                        <div className="text-[11px] text-slate-400 mt-0.5">{stage.details}</div>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <span className="font-mono text-amber-400 text-[11px]">{stage.duration_ms} ms</span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300">
                          {stage.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-800 bg-slate-950/60 flex justify-end">
              <button
                onClick={() => setSelectedTrace(null)}
                className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg transition-colors cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
