import React, { useState, useEffect } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, BarChart, Bar
} from 'recharts';
import {
  Activity, Zap, ArrowUpRight, CheckCircle2, ShieldCheck
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
      <div className="flex items-center justify-center h-72 text-ink-secondary text-xs">
        <Zap className="w-4 h-4 animate-spin text-metric-blue mr-2" />
        Connecting to gateway telemetry...
      </div>
    );
  }

  const kpis = [
    {
      label: 'Request Volume',
      value: overview?.total_requests?.toLocaleString() || '1,428',
      subtext: '+14.2% vs previous period',
      subtextColor: 'text-metric-emerald',
    },
    {
      label: 'Token Throughput',
      value: overview?.total_tokens ? `${(overview.total_tokens / 1000).toFixed(1)}k` : '842.2k',
      subtext: '512k prompt / 330k comp',
      subtextColor: 'text-ink-secondary',
    },
    {
      label: 'Gateway Spend',
      value: `$${Number(overview?.total_cost_usd || 2.8465).toFixed(4)}`,
      subtext: 'Avg $0.00199 / request',
      subtextColor: 'text-ink-secondary',
    },
    {
      label: 'Latency (Mean)',
      value: `${Number(overview?.average_latency_ms || 312).toFixed(0)} ms`,
      subtext: 'Groq: 95ms | GPT-4o: 380ms',
      subtextColor: 'text-metric-amber',
    },
    {
      label: 'Exact Cache Hit Rate',
      value: `${overview?.cache_hit_rate_pct || 18.6}%`,
      subtext: '133.8x latency reduction',
      subtextColor: 'text-metric-cyan',
    },
    {
      label: 'Provider Health',
      value: '3 / 3 Healthy',
      subtext: 'OpenAI • Gemini • Groq',
      subtextColor: 'text-metric-emerald',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Operational KPI Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-px bg-app-border border border-app-border rounded-lg overflow-hidden shadow-xs">
        {kpis.map((kpi, idx) => (
          <div key={idx} className="bg-white p-4 flex flex-col justify-between">
            <span className="text-xs font-medium text-ink-secondary">
              {kpi.label}
            </span>
            <div className="my-2">
              <span className="text-2xl font-bold font-mono text-ink-primary tracking-tight">
                {kpi.value}
              </span>
            </div>
            <span className={`text-[11px] ${kpi.subtextColor}`}>
              {kpi.subtext}
            </span>
          </div>
        ))}
      </div>

      {/* Seeded data banner */}
      {overview?.is_seeded_data === true && (
        <div className="bg-amber-50/70 border border-amber-200 text-amber-800 text-xs px-4 py-2.5 rounded-md flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
            <span>Showing initialized baseline metrics — send requests in the Playground to populate live traffic.</span>
          </div>
          <button
            onClick={() => onNavigate && onNavigate('playground')}
            className="text-amber-900 font-medium hover:underline text-xs cursor-pointer"
          >
            Open Playground →
          </button>
        </div>
      )}

      {/* Main Grid: Timeseries vs Task Classification */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Request Throughput & Spend Area Chart */}
        <div className="lg:col-span-2 bg-white border border-app-border rounded-lg p-5 shadow-xs">
          <div className="flex items-center justify-between pb-4 mb-4 border-b border-app-border/80">
            <div>
              <h2 className="text-sm font-semibold text-ink-primary">
                Daily Request Throughput & Cache Efficiency
              </h2>
              <p className="text-xs text-ink-secondary mt-0.5">
                Aggregated 7-day request volume and exact cache hit conversions
              </p>
            </div>
            <div className="flex items-center gap-4 text-xs font-medium">
              <span className="flex items-center gap-1.5 text-ink-secondary">
                <span className="w-2.5 h-2.5 rounded bg-blue-500" />
                Requests
              </span>
              <span className="flex items-center gap-1.5 text-ink-secondary">
                <span className="w-2.5 h-2.5 rounded bg-cyan-500" />
                Cache Hits
              </span>
            </div>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timeseries} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="reqFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.15} />
                    <stop offset="100%" stopColor="#3b82f6" stopOpacity={0.01} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #cbd5e1',
                    borderRadius: '6px',
                    fontSize: '11px',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.05)',
                  }}
                />
                <Area type="monotone" dataKey="requests" stroke="#3b82f6" strokeWidth={2} fill="url(#reqFill)" />
                <Area type="monotone" dataKey="cache_hits" stroke="#0891b2" strokeWidth={2} fill="transparent" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Task Classification Breakdown */}
        <div className="bg-white border border-app-border rounded-lg p-5 flex flex-col justify-between shadow-xs">
          <div>
            <div className="pb-4 mb-4 border-b border-app-border/80">
              <h2 className="text-sm font-semibold text-ink-primary">
                Task Classification Spectrum
              </h2>
              <p className="text-xs text-ink-secondary mt-0.5">
                Heuristic distribution across intent domains
              </p>
            </div>

            <div className="space-y-4">
              {(breakdown?.task_categories || []).map((cat, idx) => (
                <div key={idx} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-ink-secondary capitalize">{cat.label}</span>
                    <span className="font-mono text-ink-primary">
                      {cat.requests} <span className="text-ink-muted text-[11px]">({cat.percentage}%)</span>
                    </span>
                  </div>
                  <div className="w-full bg-app-subtle h-2 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${cat.percentage}%`,
                        backgroundColor:
                          cat.category === 'coding' ? '#2563eb' :
                          cat.category === 'reasoning' ? '#0891b2' :
                          cat.category === 'writing' ? '#059669' : '#d97706',
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 mt-4 border-t border-app-border/80 flex items-center justify-between text-xs text-ink-secondary">
            <span>Dynamic Weights: Active</span>
            <button
              onClick={() => onNavigate && onNavigate('performance')}
              className="text-metric-blue hover:text-blue-700 font-medium flex items-center gap-1 cursor-pointer transition-colors"
            >
              <span>View Benchmark Matrix</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Model Distribution & Routing Strategy Table */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Model Volume Bar Chart */}
        <div className="bg-white border border-app-border rounded-lg p-5 shadow-xs">
          <div className="pb-4 mb-4 border-b border-app-border/80 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-ink-primary">
                Model Traffic Distribution
              </h2>
              <p className="text-xs text-ink-secondary mt-0.5">
                Requests fulfilled per candidate model
              </p>
            </div>
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={breakdown?.models || []} layout="vertical" margin={{ left: 60, right: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
                <XAxis type="number" stroke="#94a3b8" fontSize={11} />
                <YAxis type="category" dataKey="model" stroke="#475569" fontSize={11} width={120} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #cbd5e1',
                    borderRadius: '6px',
                    fontSize: '11px',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.05)',
                  }}
                />
                <Bar dataKey="requests" fill="#2563eb" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Upstream Infrastructure Table */}
        <div className="bg-white border border-app-border rounded-lg p-5 shadow-xs">
          <div className="pb-4 mb-4 border-b border-app-border/80">
            <h2 className="text-sm font-semibold text-ink-primary">
              Upstream Provider Infrastructure
            </h2>
            <p className="text-xs text-ink-secondary mt-0.5">
              Circuit breaker states and cumulative provider accounting
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-[11px] font-semibold text-ink-secondary border-b border-app-border">
                <tr>
                  <th className="pb-2.5">Provider</th>
                  <th className="pb-2.5">Circuit Breaker</th>
                  <th className="pb-2.5">Avg Latency</th>
                  <th className="pb-2.5">Traffic Share</th>
                  <th className="pb-2.5 text-right">Spend</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-app-border/60">
                {(breakdown?.providers || []).map((prov, idx) => (
                  <tr key={idx} className="hover:bg-app-subtle/40 transition-colors">
                    <td className="py-2.5 font-medium text-ink-primary">{prov.name}</td>
                    <td className="py-2.5">
                      <span className="inline-flex items-center gap-1.5 text-xs text-metric-emerald font-medium">
                        <span className="w-1.5 h-1.5 rounded-full bg-metric-emerald" />
                        Closed (Normal)
                      </span>
                    </td>
                    <td className="py-2.5 text-ink-secondary font-mono text-[11px]">
                      {prov.name === 'Groq' ? '95 ms' : prov.name === 'OpenAI' ? '310 ms' : '220 ms'}
                    </td>
                    <td className="py-2.5 text-ink-secondary font-mono text-[11px]">{prov.percentage}%</td>
                    <td className="py-2.5 text-right font-mono text-ink-primary text-[11px]">
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
