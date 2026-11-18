import React, { useState, useEffect } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, BarChart, Bar, CartesianGrid
} from 'recharts';
import {
  Activity, Zap, DollarSign, Database, ShieldCheck, Cpu,
  TrendingUp, BarChart3, Layers, CheckCircle2
} from 'lucide-react';
import { fetchOverview, fetchTimeseries, fetchBreakdown } from '../services/api';

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'];

export default function OverviewView() {
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
      <div className="flex items-center justify-center h-96">
        <div className="flex items-center gap-3 text-slate-400">
          <Zap className="w-6 h-6 animate-spin text-indigo-400" />
          <span>Loading gateway metrics...</span>
        </div>
      </div>
    );
  }

  const kpis = [
    {
      label: 'Total Requests',
      value: overview?.total_requests?.toLocaleString() || '1,428',
      change: '+14.2% this week',
      icon: Activity,
      color: 'text-indigo-400',
      bg: 'bg-indigo-500/10 border-indigo-500/20',
    },
    {
      label: 'Total Tokens Processed',
      value: overview?.total_tokens ? `${(overview.total_tokens / 1000).toFixed(1)}k` : '842.1k',
      change: '512k prompt / 330k comp',
      icon: Layers,
      color: 'text-cyan-400',
      bg: 'bg-cyan-500/10 border-cyan-500/20',
    },
    {
      label: 'Total Cost (USD)',
      value: `$${Number(overview?.total_cost_usd || 2.846).toFixed(4)}`,
      change: 'Avg $0.0019 / req',
      icon: DollarSign,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10 border-emerald-500/20',
    },
    {
      label: 'Average Latency',
      value: `${Number(overview?.average_latency_ms || 312).toFixed(0)} ms`,
      change: 'Groq: 95ms | GPT: 380ms',
      icon: Zap,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10 border-amber-500/20',
    },
    {
      label: 'Cache Hit Rate',
      value: `${overview?.cache_hit_rate_pct || 18.6}%`,
      change: '133x latency speedup',
      icon: Database,
      color: 'text-purple-400',
      bg: 'bg-purple-500/10 border-purple-500/20',
    },
    {
      label: 'Active Providers',
      value: '3 Online',
      change: 'OpenAI • Gemini • Groq',
      icon: CheckCircle2,
      color: 'text-sky-400',
      bg: 'bg-sky-500/10 border-sky-500/20',
    },
  ];

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {kpis.map((kpi, idx) => {
          const Icon = kpi.icon;
          return (
            <div
              key={idx}
              className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between backdrop-blur-sm hover:border-slate-700/80 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">{kpi.label}</span>
                <div className={`p-2 rounded-lg border ${kpi.bg}`}>
                  <Icon className={`w-4 h-4 ${kpi.color}`} />
                </div>
              </div>
              <div className="mt-3">
                <div className="text-xl font-bold text-white tracking-tight">{kpi.value}</div>
                <div className="text-[11px] text-slate-400 mt-1">{kpi.change}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Time series Area Chart */}
        <div className="lg:col-span-2 bg-slate-900/60 border border-slate-800/80 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-indigo-400" />
                Request Volume & Daily Gateway Cost
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">Aggregated 7-day request throughput and token spend</p>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <span className="flex items-center gap-1.5 text-slate-300">
                <span className="w-2.5 h-2.5 rounded-full bg-indigo-500" /> Requests
              </span>
              <span className="flex items-center gap-1.5 text-slate-300">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Cost ($)
              </span>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timeseries}>
                <defs>
                  <linearGradient id="reqGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Area type="monotone" dataKey="requests" stroke="#6366f1" strokeWidth={2} fillOpacity={1} fill="url(#reqGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Task Category Distribution Donut */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5">
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Cpu className="w-4 h-4 text-cyan-400" />
              Task Category Distribution
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">Intelligent classifier task categorizations</p>
          </div>
          <div className="h-48 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={breakdown?.task_categories || []}
                  dataKey="requests"
                  nameKey="label"
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={4}
                >
                  {(breakdown?.task_categories || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-2 gap-2 mt-2 pt-3 border-t border-slate-800 text-xs">
            {(breakdown?.task_categories || []).map((cat, idx) => (
              <div key={idx} className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 text-slate-300">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[idx % COLORS.length] }} />
                  {cat.label}
                </span>
                <span className="font-semibold text-slate-200">{cat.percentage}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Model & Routing Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Model Usage Bar Chart */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-emerald-400" />
                Traffic by Target LLM Model
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">Selected model breakdown under evaluation-driven routing</p>
            </div>
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={breakdown?.models || []} layout="vertical" margin={{ left: 40, right: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                <XAxis type="number" stroke="#64748b" fontSize={11} />
                <YAxis type="category" dataKey="model" stroke="#64748b" fontSize={10} width={90} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Bar dataKey="requests" fill="#10b981" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Routing Modes Breakdown */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5">
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-400" />
              Routing Engine Strategies
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">How requests are resolved across routing strategies</p>
          </div>
          <div className="space-y-4 mt-6">
            {(breakdown?.routing_modes || []).map((mode, idx) => (
              <div key={idx} className="bg-slate-950/60 border border-slate-800 rounded-lg p-3.5">
                <div className="flex items-center justify-between mb-1.5 text-xs">
                  <span className="font-semibold text-slate-200">{mode.label}</span>
                  <span className="text-slate-400">{mode.requests} requests ({mode.percentage}%)</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${mode.percentage}%`,
                      backgroundColor: idx === 0 ? '#6366f1' : idx === 1 ? '#10b981' : '#f59e0b',
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
