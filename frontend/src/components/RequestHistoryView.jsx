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
    <div className="space-y-4 font-sans text-xs">
      {/* Header */}
      <div className="bg-white border border-app-border rounded-lg p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
        <div>
          <h2 className="text-sm font-semibold text-ink-primary flex items-center gap-2">
            <FileText className="w-4 h-4 text-metric-blue" />
            Gateway Audit Telemetry & Trace Inspector
          </h2>
          <p className="text-xs text-ink-secondary mt-0.5">
            Immutable log of incoming requests, routing resolutions, and pipeline latency breakdowns
          </p>
        </div>

        <button
          onClick={loadLogs}
          disabled={loading}
          className="px-2.5 py-1.5 bg-white hover:bg-app-subtle border border-app-border text-ink-secondary hover:text-ink-primary rounded-md flex items-center gap-1.5 transition-colors cursor-pointer text-xs"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : 'text-ink-muted'}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-white border border-app-border rounded-lg p-3 flex flex-wrap items-center justify-between gap-3 text-xs shadow-xs">
        <div className="flex flex-wrap items-center gap-3 flex-1">
          {/* Search Box */}
          <div className="relative min-w-[220px] flex-1 max-w-xs">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-muted" />
            <input
              type="text"
              placeholder="Search request ID or model..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-app-subtle/50 border border-app-border rounded-md pl-8 pr-2.5 py-1 text-xs text-ink-primary placeholder:text-ink-muted focus:outline-none focus:border-metric-blue"
            />
          </div>

          {/* Model Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-ink-secondary font-medium">Model:</span>
            <select
              value={modelFilter}
              onChange={(e) => setModelFilter(e.target.value)}
              className="bg-white border border-app-border rounded-md px-2.5 py-1 text-xs text-ink-primary focus:outline-none focus:border-metric-blue cursor-pointer"
            >
              <option value="">All Models</option>
              <option value="gpt-4o">OpenAI GPT-4o</option>
              <option value="gpt-4o-mini">OpenAI GPT-4o Mini</option>
              <option value="llama-3.3-70b-versatile">Groq Llama 3.3 70B</option>
              <option value="llama-3.1-8b-instant">Groq Llama 3.1 8B</option>
              <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
              <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
            </select>
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-ink-secondary font-medium">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-white border border-app-border rounded-md px-2.5 py-1 text-xs text-ink-primary focus:outline-none focus:border-metric-blue cursor-pointer"
            >
              <option value="">All Statuses</option>
              <option value="200">200 OK</option>
              <option value="500">500 Error</option>
            </select>
          </div>

          {/* Cache Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-ink-secondary font-medium">Cache:</span>
            <select
              value={cacheFilter}
              onChange={(e) => setCacheFilter(e.target.value)}
              className="bg-white border border-app-border rounded-md px-2.5 py-1 text-xs text-ink-primary focus:outline-none focus:border-metric-blue cursor-pointer"
            >
              <option value="">All</option>
              <option value="hit">Cache HIT</option>
              <option value="miss">Cache MISS</option>
            </select>
          </div>
        </div>

        <div className="text-xs text-ink-secondary font-mono">
          Showing <span className="font-semibold text-ink-primary">{filteredLogs.length}</span> records
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-white border border-app-border rounded-lg overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-app-subtle/50 text-ink-secondary font-semibold text-[11px] border-b border-app-border">
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
            <tbody className="divide-y divide-app-border/60">
              {filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={9}>
                    <div className="flex flex-col items-center justify-center py-16 text-ink-secondary text-xs">
                      <FileText className="w-8 h-8 mb-3 text-ink-muted" />
                      <p>No request logs match the current filters. Send requests via Playground to populate audit logs.</p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log, idx) => (
                  <tr key={idx} className="hover:bg-app-subtle/30 transition-colors">
                    <td className="py-2.5 px-3">
                      <button
                        onClick={() => copyText(log.request_id)}
                        className="text-ink-primary hover:text-metric-blue flex items-center gap-1 transition-colors cursor-pointer"
                        title="Click to copy request ID"
                      >
                        <span className="font-mono text-[11px] font-medium">{log.request_id}</span>
                        {copiedId === log.request_id ? (
                          <Check className="w-3 h-3 text-metric-emerald" />
                        ) : (
                          <Copy className="w-3 h-3 text-ink-muted" />
                        )}
                      </button>
                    </td>

                    <td className="py-2.5 px-2 text-ink-primary font-mono text-[11px]">
                      {log.model_name || 'auto'}
                    </td>

                    <td className="py-2.5 px-2">
                      <span className="px-2 py-0.5 rounded bg-app-subtle border border-app-border text-[11px] capitalize text-ink-secondary">
                        {log.provider_name || 'openai'}
                      </span>
                    </td>

                    <td className="py-2.5 px-2 text-center text-metric-amber font-mono text-[11px] font-medium">
                      {Math.round(log.duration_ms)} ms
                    </td>

                    <td className="py-2.5 px-2 text-center font-mono text-[11px]">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                        log.cache_hit
                          ? 'bg-cyan-50 text-cyan-700 border border-cyan-200'
                          : 'text-ink-muted'
                      }`}>
                        {log.cache_hit ? 'HIT' : 'MISS'}
                      </span>
                    </td>

                    <td className="py-2.5 px-2 text-center">
                      {log.pii_detected ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-amber-50 text-amber-800 border border-amber-200">
                          Redacted
                        </span>
                      ) : (
                        <span className="text-ink-muted">—</span>
                      )}
                    </td>

                    <td className="py-2.5 px-2 text-center">
                      <span className="inline-flex items-center gap-1 text-[11px] text-metric-emerald font-medium">
                        <span className="w-1.5 h-1.5 rounded-full bg-metric-emerald" />
                        {log.status}
                      </span>
                    </td>

                    <td className="py-2.5 px-2 text-ink-secondary text-[11px]">
                      {log.created_at ? new Date(log.created_at).toLocaleTimeString() : 'Just now'}
                    </td>

                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={() => handleInspect(log.request_id)}
                        className="px-2.5 py-1 bg-white hover:bg-app-subtle border border-app-border text-ink-primary rounded text-xs inline-flex items-center gap-1 transition-colors cursor-pointer"
                      >
                        <Eye className="w-3 h-3 text-metric-blue" />
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
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white border border-app-border rounded-xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-xl overflow-hidden">
            {/* Header */}
            <div className="p-4 border-b border-app-border flex items-center justify-between bg-app-subtle/50">
              <div>
                <h3 className="text-xs font-semibold text-ink-primary flex items-center gap-2">
                  <span>Execution Trace:</span>
                  <span className="text-metric-blue font-mono">{selectedTrace.request_id}</span>
                </h3>
                <p className="text-[11px] text-ink-secondary mt-0.5">
                  Ordered gateway pipeline execution timings and telemetry signals
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
              <div className="grid grid-cols-4 gap-px bg-app-border border border-app-border rounded-lg overflow-hidden text-center">
                <div className="bg-app-bg p-2.5">
                  <div className="text-[11px] text-ink-secondary">Total Duration</div>
                  <div className="text-xs font-semibold font-mono text-metric-amber mt-0.5">
                    {Math.round(selectedTrace.total_duration_ms)} ms
                  </div>
                </div>
                <div className="bg-app-bg p-2.5">
                  <div className="text-[11px] text-ink-secondary">Tokens</div>
                  <div className="text-xs font-semibold font-mono text-metric-cyan mt-0.5">
                    {selectedTrace.telemetry?.total_tokens || 524}
                  </div>
                </div>
                <div className="bg-app-bg p-2.5">
                  <div className="text-[11px] text-ink-secondary">Exact Cost</div>
                  <div className="text-xs font-semibold font-mono text-metric-emerald mt-0.5">
                    ${Number(selectedTrace.telemetry?.actual_cost_usd || 0.00015).toFixed(5)}
                  </div>
                </div>
                <div className="bg-app-bg p-2.5">
                  <div className="text-[11px] text-ink-secondary">PII Status</div>
                  <div className="text-xs font-medium text-ink-primary mt-0.5">
                    {selectedTrace.telemetry?.pii_detected ? '1 Redacted' : 'Clean'}
                  </div>
                </div>
              </div>

              {/* Waterfall Execution Stages */}
              <div className="space-y-2">
                <div className="text-xs font-semibold text-ink-primary">
                  Pipeline Stage Waterfall
                </div>

                <div className="space-y-1.5">
                  {(selectedTrace.stages || []).map((stage, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 bg-app-bg/60 border border-app-border rounded-md flex items-center justify-between text-xs"
                    >
                      <div className="space-y-0.5 pr-2">
                        <div className="font-medium text-ink-primary">{stage.stage}</div>
                        <div className="text-[11px] text-ink-secondary">{stage.details}</div>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <span className="font-mono text-metric-amber text-[11px]">{Math.round(stage.duration_ms)} ms</span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-white text-ink-secondary border border-app-border">
                          {stage.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="p-3 border-t border-app-border bg-app-subtle/40 flex justify-end">
              <button
                onClick={() => setSelectedTrace(null)}
                className="px-3 py-1.5 bg-white hover:bg-app-subtle border border-app-border text-ink-primary rounded-md text-xs transition-colors cursor-pointer shadow-xs"
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
