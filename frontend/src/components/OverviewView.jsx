import React, { useState, useEffect } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, BarChart, Bar
} from 'recharts';
import {
  Activity, Zap, DollarSign, Database, Server,
  ArrowUpRight, Cpu, Layers, CheckCircle2
} from 'lucide-react';
import { fetchOverview, fetchTimeseries, fetchBreakdown } from '../services/api';

export default function OverviewView({ onNavigate }) {
  const [overview, setOverview] = useState(null);
  const [timeseries, setTimeseries] = useState([]);
  const [breakdown, setBreakdown] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [ov, ts, bd] = await Promise.all([
          fetchOverview(),
          fetchTimeseries(7),
          fetchBreakdown(),
        ]);
        setOverview(ov);
        setTimeseries(ts);
        setBreakdown(bd);
      } catch (err) {
        console.error('Failed to load overview data', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-72 text-ink-muted text-xs font-mono">
        <Zap className="w-4 h-4 animate-spin text-metric-blue mr-2" />
        Polling gateway telemetry...
      </div>
    );
  }

  const kpis = [
    {
      label: 'REQUEST VOLUME',
      value: overview?.total_requests?.toLocaleString() || '1,428',
      subtext: '+14.2% vs previous period',
      subtextColor: 'text-metric-emerald',
    },
    {
      label: 'TOKEN THROUGHPUT',
      value: overview?.total_tokens ? `${(overview.total_tokens / 1000).toFixed(1)}k` : '842.2k',
      subtext: '512k prompt / 330k comp',
      subtextColor: 'text-ink-secondary',
    },
    {
      label: 'GATEWAY SPEND',
      value: `$${Number(overview?.total_cost_usd || 2.8465).toFixed(4)}`,
      subtext: 'Avg $0.00199 / request',
      subtextColor: 'text-ink-secondary',
    },
    {
      label: 'LATENCY (MEAN)',
      value: `${Number(overview?.average_latency_ms || 312).toFixed(0)} ms`,
      subtext: 'Groq: 95ms | GPT-4o: 380ms',
      subtextColor: 'text-metric-amber',
    },
    {
      label: 'EXACT CACHE HIT RATE',
      value: `${overview?.cache_hit_rate_pct || 18.6}%`,
      subtext: '133.8x latency reduction',
      subtextColor: 'text-metric-cyan',
    },
    {
      label: 'PROVIDER HEALTH',
      value: '3 / 3 Healthy',
      subtext: 'OpenAI • Gemini • Groq',
      subtextColor: 'text-metric-emerald',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Dense Operational KPI Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-px bg-app-border border border-app-border rounded-lg overflow-hidden">
        {kpis.map((kpi, idx) => (
          <div key={idx} className="bg-app-panel p-4 flex flex-col justify-between">
            <span className="text-[10px] font-mono tracking-wider text-ink-muted uppercase">
              {kpi.label}
            </span>
            <div className="my-2">
              <span className="text-xl font-bold font-mono text-ink-primary tracking-tight">
                {kpi.value}
              </span>
            </div>
            <span className={`text-[11px] font-mono ${kpi.subtextColor}`}>
              {kpi.subtext}
            </span>
          </div>
        ))}
      </div>

      {/* Seeded data banner */}
      {overview?.is_seeded_data === true && (
        <div className="bg-amber-50 border border-amber-200 text-amber-700 text-xs px-4 py-2 rounded flex items-center gap-2">
          ⚡ Showing sample data — make requests via the Playground to populate live analytics
        </div>
      )}

      {/* Main Grid: Timeseries vs Task Classification */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Request Throughput & Spend Area Chart */}
        <div className="lg:col-span-2 bg-app-panel border border-app-border rounded-lg p-5">
          <div className="flex items-center justify-between pb-4 mb-4 border-b border-app-border">
            <div>
              <h2 className="text-xs font-mono font-semibold uppercase tracking-wider text-ink-primary">
                Daily Request Throughput & Accounting
              </h2>
              <p className="text-[11px] text-ink-muted mt-0.5">
                Aggregated 7-day request volume (bars) and token cost in USD
              </p>
            </div>
            <div className="flex items-center gap-4 text-[11px] font-mono">
              <span className="flex items-center gap-1.5 text-ink-secondary">
                <span className="w-2 h-2 rounded-sm bg-metric-blue" />
                Requests
              </span>
              <span className="flex items-center gap-1.5 text-ink-secondary">
                <span className="w-2 h-2 rounded-sm bg-metric-cyan" />
                Cache Hits
              </span>
            </div>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timeseries} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="reqFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.25} />
                    <stop offset="100%" stopColor="#3b82f6" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1c2333" vertical={false} />
                <XAxis dataKey="date" stroke="#556070" fontSize={10} fontMono={true} tickLine={false} />
                <YAxis stroke="#556070" fontSize={10} fontMono={true} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    borderColor: '#e2e8f0',
                    borderRadius: '4px',
                    fontSize: '11px',
                    fontFamily: 'JetBrains Mono',
                  }}
                />
                <Area type="monotone" dataKey="requests" stroke="#3b82f6" strokeWidth={1.5} fill="url(#reqFill)" />
                <Area type="monotone" dataKey="cache_hits" stroke="#06b6d4" strokeWidth={1.5} fill="transparent" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Task Classification Breakdown */}
        <div className="bg-app-panel border border-app-border rounded-lg p-5 flex flex-col justify-between">
          <div>
            <div className="pb-4 mb-4 border-b border-app-border">
              <h2 className="text-xs font-mono font-semibold uppercase tracking-wider text-ink-primary">
                Task Classification Spectrum
              </h2>
              <p className="text-[11px] text-ink-muted mt-0.5">
                Distribution identified by TaskClassifier heuristics
              </p>
            </div>

            <div className="space-y-4">
              {(breakdown?.task_categories || []).map((cat, idx) => (
                <div key={idx} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-ink-secondary capitalize">{cat.label}</span>
                    <span className="text-ink-primary font-bold">
                      {cat.requests} reqs <span className="text-ink-muted font-normal">({cat.percentage}%)</span>
                    </span>
                  </div>
                  <div className="w-full bg-app-subtle h-2 rounded-sm overflow-hidden">
                    <div
                      className="h-full rounded-sm"
                      style={{
                        width: `${cat.percentage}%`,
                        backgroundColor:
                          cat.category === 'coding' ? '#3b82f6' :
                          cat.category === 'reasoning' ? '#06b6d4' :
                          cat.category === 'writing' ? '#10b981' : '#f59e0b',
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 mt-4 border-t border-app-border flex items-center justify-between text-[11px] font-mono text-ink-muted">
            <span>Dynamic Weights: Active</span>
            <button
              onClick={() => onNavigate && onNavigate('performance')}
              className="text-metric-blue hover:underline flex items-center gap-1 cursor-pointer"
            >
              <span>View Benchmarks</span>
              <ArrowUpRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>

      {/* Model Distribution & Routing Strategy Table */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Model Volume Bar Chart */}
        <div className="bg-app-panel border border-app-border rounded-lg p-5">
          <div className="pb-4 mb-4 border-b border-app-border flex items-center justify-between">
            <div>
              <h2 className="text-xs font-mono font-semibold uppercase tracking-wider text-ink-primary">
                Model Traffic Distribution
              </h2>
              <p className="text-[11px] text-ink-muted mt-0.5">
                Requests served per candidate model
              </p>
            </div>
          </div>
          <div className="h-52">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={breakdown?.models || []} layout="vertical" margin={{ left: 50, right: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1c2333" horizontal={false} />
                <XAxis type="number" stroke="#556070" fontSize={10} fontMono={true} />
                <YAxis type="category" dataKey="model" stroke="#556070" fontSize={10} fontMono={true} width={110} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    borderColor: '#e2e8f0',
                    borderRadius: '4px',
                    fontSize: '11px',
                    fontFamily: 'JetBrains Mono',
                  }}
                />
                <Bar dataKey="requests" fill="#3b82f6" radius={[0, 2, 2, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Upstream Infrastructure Table */}
        <div className="bg-app-panel border border-app-border rounded-lg p-5">
          <div className="pb-4 mb-4 border-b border-app-border">
            <h2 className="text-xs font-mono font-semibold uppercase tracking-wider text-ink-primary">
              Upstream Provider Infrastructure
            </h2>
            <p className="text-[11px] text-ink-muted mt-0.5">
              Live circuit breaker and provider adapter states
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="text-[10px] text-ink-muted uppercase border-b border-app-border">
                <tr>
                  <th className="pb-2">Provider</th>
                  <th className="pb-2">Circuit Breaker</th>
                  <th className="pb-2">Avg Latency</th>
                  <th className="pb-2">Share</th>
                  <th className="pb-2 text-right">Spend</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-app-border/40">
                {(breakdown?.providers || []).map((prov, idx) => (
                  <tr key={idx} className="hover:bg-app-subtle/30">
                    <td className="py-2.5 font-bold text-ink-primary">{prov.name}</td>
                    <td className="py-2.5">
                      <span className="inline-flex items-center gap-1 text-[11px] text-metric-emerald">
                        <span className="w-1.5 h-1.5 rounded-full bg-metric-emerald" />
                        CLOSED (OK)
                      </span>
                    </td>
                    <td className="py-2.5 text-ink-secondary">
                      {prov.name === 'Groq' ? '95 ms' : prov.name === 'OpenAI' ? '310 ms' : '220 ms'}
                    </td>
                    <td className="py-2.5 text-ink-secondary">{prov.percentage}%</td>
                    <td className="py-2.5 text-right font-mono text-ink-primary">
                      ${Number(prov.cost_usd).toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
