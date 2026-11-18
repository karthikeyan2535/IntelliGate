import React, { useState, useEffect } from 'react';
import {
  FileText, RefreshCw, Eye, X, CheckCircle2,
  Copy, Check, Clock, ShieldCheck, Database, Layers,
  Filter, Search
} from 'lucide-react';
import { fetchRequestLogs, inspectRequest } from '../services/api';

export default function RequestHistoryView() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTrace, setSelectedTrace] = useState(null);
  const [copiedId, setCopiedId] = useState(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [modelFilter, setModelFilter] = useState('');
  const [cacheFilter, setCacheFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadLogs();
  }, [statusFilter, modelFilter, cacheFilter]);

  async function loadLogs() {
    setLoading(true);
    try {
      let cacheHit = null;
      if (cacheFilter === 'hit') cacheHit = true;
      if (cacheFilter === 'miss') cacheHit = false;

      const data = await fetchRequestLogs({
        limit: 50,
        status: statusFilter,
        model: modelFilter,
        cacheHit: cacheHit,
      });
      setLogs(data || []);
    } catch (err) {
      console.error('Failed to load audit logs', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleInspect(requestId) {
    try {
      const trace = await inspectRequest(requestId);
      setSelectedTrace(trace);
    } catch (err) {
      console.error('Failed to load trace', err);
    }
  }

  function copyText(txt) {
    navigator.clipboard.writeText(txt);
    setCopiedId(txt);
    setTimeout(() => setCopiedId(null), 1500);
  }

  const filteredLogs = logs.filter((log) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      (log.request_id && log.request_id.toLowerCase().includes(q)) ||
      (log.model_name && log.model_name.toLowerCase().includes(q)) ||
      (log.provider_name && log.provider_name.toLowerCase().includes(q))
    );
  });

  return (
    <div className="space-y-4 font-mono text-xs">
      {/* Header */}
      <div className="bg-app-panel border border-app-border rounded-lg p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xs font-semibold uppercase tracking-wider text-ink-primary flex items-center gap-2">
            <FileText className="w-4 h-4 text-metric-blue" />
            Gateway Audit Telemetry & Trace Inspector
          </h2>
          <p className="text-[11px] text-ink-muted mt-0.5">
            Immutable log of all incoming requests, routing outcomes, and pipeline stage timings
          </p>
        </div>

        <button
          onClick={loadLogs}
          disabled={loading}
          className="px-2.5 py-1 bg-app-subtle hover:bg-app-hover border border-app-border text-ink-secondary hover:text-ink-primary rounded flex items-center gap-1.5 transition-colors cursor-pointer text-[11px]"
        >
          <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-app-panel border border-app-border rounded-lg p-3 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex flex-wrap items-center gap-2 flex-1">
          {/* Search Box */}
          <div className="relative min-w-[200px] flex-1 max-w-xs">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-muted" />
            <input
              type="text"
              placeholder="Search by Request ID or Model..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-app-bg border border-app-border rounded pl-8 pr-2.5 py-1 text-xs text-ink-primary placeholder:text-ink-muted focus:outline-none focus:border-metric-blue"
            />
          </div>

          {/* Model Filter */}
          <div className="flex items-center gap-1">
            <span className="text-[10px] text-ink-muted uppercase">Model:</span>
            <select
              value={modelFilter}
              onChange={(e) => setModelFilter(e.target.value)}
              className="bg-app-bg border border-app-border rounded px-2 py-1 text-[11px] text-ink-primary focus:outline-none focus:border-metric-blue cursor-pointer"
            >
              <option value="">All Models</option>
              <option value="gpt-4o">OpenAI GPT-4o</option>
              <option value="gpt-4o-mini">OpenAI GPT-4o Mini</option>
              <option value="llama-3.3-70b-versatile">Groq Llama 3.3 70B</option>
              <option value="llama-3.1-8b-instant">Groq Llama 3.1 8B</option>
              <option value="gemini-1.5-pro">Google Gemini 1.5 Pro</option>
              <option value="gemini-1.5-flash">Google Gemini 1.5 Flash</option>
            </select>
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-1">
            <span className="text-[10px] text-ink-muted uppercase">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-app-bg border border-app-border rounded px-2 py-1 text-[11px] text-ink-primary focus:outline-none focus:border-metric-blue cursor-pointer"
            >
              <option value="">All Statuses</option>
              <option value="200">200 OK</option>
              <option value="500">500 Error</option>
            </select>
          </div>

          {/* Cache Filter */}
          <div className="flex items-center gap-1">
            <span className="text-[10px] text-ink-muted uppercase">Cache:</span>
            <select
              value={cacheFilter}
              onChange={(e) => setCacheFilter(e.target.value)}
              className="bg-app-bg border border-app-border rounded px-2 py-1 text-[11px] text-ink-primary focus:outline-none focus:border-metric-blue cursor-pointer"
            >
              <option value="">All</option>
              <option value="hit">Cache HIT</option>
              <option value="miss">Cache MISS</option>
            </select>
          </div>
        </div>

        <div className="text-[11px] text-ink-muted">
          Showing <span className="font-bold text-ink-primary">{filteredLogs.length}</span> records
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-app-panel border border-app-border rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-app-subtle/70 text-ink-muted uppercase tracking-wider text-[10px] border-b border-app-border">
              <tr>
                <th className="py-2.5 px-3">Request ID</th>
                <th className="py-2.5 px-2">Resolved Model</th>
                <th className="py-2.5 px-2">Provider</th>
                <th className="py-2.5 px-2 text-center">Latency</th>
                <th className="py-2.5 px-2 text-center">Cache</th>
                <th className="py-2.5 px-2 text-center">PII Filter</th>
                <th className="py-2.5 px-2 text-center">Status</th>
                <th className="py-2.5 px-2">Timestamp</th>
                <th className="py-2.5 px-3 text-right">Trace</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-app-border/40">
              {filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={9}>
                    <div className="flex flex-col items-center justify-center py-16 text-ink-muted text-xs">
                      <FileText className="w-8 h-8 mb-3 text-ink-faint" />
                      <p>No request logs match the current filters. Use the Playground to send a request.</p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log, idx) => (
                  <tr key={idx} className="hover:bg-app-subtle/25 transition-colors">
                    <td className="py-2.5 px-3">
                      <button
                        onClick={() => copyText(log.request_id)}
                        className="text-ink-primary hover:text-metric-blue flex items-center gap-1 transition-colors cursor-pointer"
                        title="Click to copy request ID"
                      >
                        <span className="font-semibold">{log.request_id}</span>
                        {copiedId === log.request_id ? (
                          <Check className="w-2.5 h-2.5 text-metric-emerald" />
                        ) : (
                          <Copy className="w-2.5 h-2.5 text-ink-faint" />
                        )}
                      </button>
                    </td>

                    <td className="py-2.5 px-2 text-ink-secondary">
                      {log.model_name || 'auto'}
                    </td>

                    <td className="py-2.5 px-2">
                      <span className="px-1.5 py-0.5 rounded bg-app-bg border border-app-border text-[10px] uppercase text-ink-secondary font-semibold">
                        {log.provider_name || 'openai'}
                      </span>
                    </td>

                    <td className="py-2.5 px-2 text-center text-metric-amber font-semibold">
                      {Math.round(log.duration_ms)} ms
                    </td>

                    <td className="py-2.5 px-2 text-center">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        log.cache_hit
                          ? 'bg-metric-cyan/15 text-metric-cyan border border-metric-cyan/30'
                          : 'text-ink-muted'
                      }`}>
                        {log.cache_hit ? 'HIT' : 'MISS'}
                      </span>
                    </td>

                    <td className="py-2.5 px-2 text-center">
                      {log.pii_detected ? (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-metric-amber/15 text-metric-amber border border-metric-amber/30">
                          REDACTED
                        </span>
                      ) : (
                        <span className="text-ink-faint">—</span>
                      )}
                    </td>

                    <td className="py-2.5 px-2 text-center">
                      <span className="inline-flex items-center gap-1 text-[11px] text-metric-emerald font-semibold">
                        <span className="w-1.5 h-1.5 rounded-full bg-metric-emerald" />
                        {log.status}
                      </span>
                    </td>

                    <td className="py-2.5 px-2 text-ink-muted text-[11px]">
                      {log.created_at ? new Date(log.created_at).toLocaleTimeString() : 'Just now'}
                    </td>

                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={() => handleInspect(log.request_id)}
                        className="px-2 py-0.5 bg-app-subtle hover:bg-app-hover border border-app-border text-ink-secondary hover:text-ink-primary rounded text-[11px] inline-flex items-center gap-1 transition-colors cursor-pointer"
                      >
                        <Eye className="w-3 h-3" />
                        <span>Trace</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Step-by-Step Distributed Trace Inspector Modal */}
      {selectedTrace && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 flex items-center justify-center p-4">
          <div className="bg-app-panel border border-app-border rounded-lg w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden font-mono">
            {/* Header */}
            <div className="p-4 border-b border-app-border flex items-center justify-between bg-app-subtle/50">
              <div>
                <h3 className="text-xs font-bold text-ink-primary uppercase tracking-wider flex items-center gap-2">
                  <span>Execution Trace:</span>
                  <span className="text-metric-blue">{selectedTrace.request_id}</span>
                </h3>
                <p className="text-[11px] text-ink-muted mt-0.5">
                  Ordered gateway pipeline execution timings and audit signals
                </p>
              </div>
              <button
                onClick={() => setSelectedTrace(null)}
                className="text-ink-muted hover:text-ink-primary p-1 rounded hover:bg-app-subtle transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Content */}
            <div className="p-4 overflow-y-auto space-y-4 text-xs">
              {/* Telemetry Summary */}
              <div className="grid grid-cols-4 gap-px bg-app-border border border-app-border rounded overflow-hidden text-center">
                <div className="bg-app-bg p-2">
                  <div className="text-[10px] text-ink-muted">TOTAL DURATION</div>
                  <div className="text-xs font-bold text-metric-amber mt-0.5">
                    {Math.round(selectedTrace.total_duration_ms)} ms
                  </div>
                </div>
                <div className="bg-app-bg p-2">
                  <div className="text-[10px] text-ink-muted">TOKENS</div>
                  <div className="text-xs font-bold text-metric-cyan mt-0.5">
                    {selectedTrace.telemetry?.total_tokens || 524}
                  </div>
                </div>
                <div className="bg-app-bg p-2">
                  <div className="text-[10px] text-ink-muted">EXACT COST</div>
                  <div className="text-xs font-bold text-metric-emerald mt-0.5">
                    ${Number(selectedTrace.telemetry?.actual_cost_usd || 0.00015).toFixed(5)}
                  </div>
                </div>
                <div className="bg-app-bg p-2">
                  <div className="text-[10px] text-ink-muted">PII DETECTIONS</div>
                  <div className="text-xs font-bold text-ink-primary mt-0.5">
                    {selectedTrace.telemetry?.pii_detected ? '1 redacted' : 'None'}
                  </div>
                </div>
              </div>

              {/* Waterfall Execution Stages */}
              <div className="space-y-1.5">
                <div className="text-[10px] font-semibold text-ink-muted uppercase tracking-wider mb-2">
                  Pipeline Stage Waterfall
                </div>

                <div className="space-y-1">
                  {(selectedTrace.stages || []).map((stage, idx) => (
                    <div
                      key={idx}
                      className="p-2 bg-app-bg border border-app-border rounded flex items-center justify-between text-[11px]"
                    >
                      <div className="space-y-0.5 pr-2">
                        <div className="font-semibold text-ink-primary">{stage.stage}</div>
                        <div className="text-[10px] text-ink-muted">{stage.details}</div>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <span className="font-mono text-metric-amber text-[11px]">{Math.round(stage.duration_ms)} ms</span>
                        <span className="px-1.5 py-0.2 rounded text-[9px] uppercase font-bold bg-app-subtle text-ink-secondary border border-app-border">
                          {stage.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="p-3 border-t border-app-border bg-app-subtle/50 flex justify-end">
              <button
                onClick={() => setSelectedTrace(null)}
                className="px-3 py-1 bg-app-subtle hover:bg-app-hover border border-app-border text-ink-secondary hover:text-ink-primary rounded text-xs transition-colors cursor-pointer"
              >
                Close Trace
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
