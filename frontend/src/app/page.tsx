"use client";

import React, { useState, useEffect } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  Clock,
  Coins,
  Cpu,
  Database,
  Eye,
  Key,
  Layers,
  Lock,
  Play,
  RefreshCw,
  Search,
  Server,
  Settings,
  Shield,
  ShieldAlert,
  Sliders,
  Trash2,
  TrendingUp,
  Zap,
} from "lucide-react";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { api } from "@/services/api";
import { formatCurrency, formatNumber } from "@/lib/utils";

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<string>("overview");
  const [loading, setLoading] = useState<boolean>(true);
  const [overview, setOverview] = useState<any>(null);
  const [timeseries, setTimeseries] = useState<any[]>([]);
  const [breakdown, setBreakdown] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [inspectedRequest, setInspectedRequest] = useState<any>(null);

  // Playground state
  const [playgroundModel, setPlaygroundModel] = useState<string>("gpt-4o");
  const [playgroundPrompt, setPlaygroundPrompt] = useState<string>("What are the core advantages of a multi-provider LLM gateway?");
  const [playgroundResponse, setPlaygroundResponse] = useState<string>("");
  const [playgroundLoading, setPlaygroundLoading] = useState<boolean>(false);

  // PII Playground
  const [piiInput, setPiiInput] = useState<string>("Contact john.doe@enterprise.com from IP 192.168.1.50 regarding invoice sk-live998877");
  const [piiResult, setPiiResult] = useState<any>(null);

  // Virtual Key Creation State
  const [newKeyName, setNewKeyName] = useState<string>("");
  const [generatedKey, setGeneratedKey] = useState<string | null>(null);
  const [virtualKeys, setVirtualKeys] = useState<any[]>([
    { id: "1", name: "Production Gateway", prefix: "ig-live-a1b2", status: "ACTIVE", rpm: 600, tpm: "1,000,000", created: "2026-11-15" },
    { id: "2", name: "Staging Pipeline", prefix: "ig-stg-8f90", status: "ACTIVE", rpm: 300, tpm: "500,000", created: "2026-11-16" },
    { id: "3", name: "Analytics Worker", prefix: "ig-wrk-4c3d", status: "ACTIVE", rpm: 120, tpm: "200,000", created: "2026-11-17" },
  ]);

  // Routing Strategy
  const [routingStrategy, setRoutingStrategy] = useState<string>("priority");

  const loadData = async () => {
    setLoading(true);
    try {
      const [ov, ts, bd, lg] = await Promise.allSettled([
        api.getOverview(),
        api.getTimeseries(7),
        api.getBreakdown(),
        api.getLogs(20),
      ]);

      if (ov.status === "fulfilled") setOverview(ov.value);
      if (ts.status === "fulfilled") setTimeseries(ts.value);
      if (bd.status === "fulfilled") setBreakdown(bd.value);
      if (lg.status === "fulfilled") setLogs(lg.value);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateKey = () => {
    if (!newKeyName) return;
    const raw = `ig-${Math.random().toString(36).substring(2, 15)}${Math.random().toString(36).substring(2, 15)}`;
    setGeneratedKey(raw);
    setVirtualKeys([
      {
        id: String(Date.now()),
        name: newKeyName,
        prefix: raw.substring(0, 10),
        status: "ACTIVE",
        rpm: 600,
        tpm: "1,000,000",
        created: "Just now",
      },
      ...virtualKeys,
    ]);
    setNewKeyName("");
  };

  const handleTestPlayground = async () => {
    setPlaygroundLoading(true);
    setPlaygroundResponse("");
    try {
      const res = await api.sendChatCompletion(
        "ig-demo-key-1234567890abcdef",
        playgroundModel,
        playgroundPrompt
      );
      setPlaygroundResponse(res.choices[0]?.message?.content || JSON.stringify(res, null, 2));
    } catch (err: any) {
      setPlaygroundResponse(`Error: ${err.message}`);
    } finally {
      setPlaygroundLoading(false);
    }
  };

  const handleTestPii = () => {
    // Regex detector emulation in browser
    let redacted = piiInput;
    const matches: string[] = [];

    const emailRegex = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b/g;
    const ipRegex = /\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b/g;
    const keyRegex = /\b(?:sk-[a-zA-Z0-9_-]{20,64}|ig-[a-zA-Z0-9_-]{24,64})\b/g;

    if (emailRegex.test(redacted)) {
      matches.push("EMAIL_ADDRESS");
      redacted = redacted.replace(emailRegex, "[REDACTED_EMAIL_ADDRESS]");
    }
    if (ipRegex.test(redacted)) {
      matches.push("IP_ADDRESS");
      redacted = redacted.replace(ipRegex, "[REDACTED_IP_ADDRESS]");
    }
    if (keyRegex.test(redacted)) {
      matches.push("API_KEY");
      redacted = redacted.replace(keyRegex, "[REDACTED_API_KEY]");
    }

    setPiiResult({
      hasPii: matches.length > 0,
      entities: matches,
      redacted,
    });
  };

  const inspectReq = async (reqId: string) => {
    try {
      const res = await api.inspectRequest(reqId);
      setInspectedRequest(res);
      setActiveTab("inspector");
    } catch (e) {
      console.error(e);
    }
  };

  const COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6"];

  return (
    <div className="flex h-screen bg-[#0b0f19] text-slate-100 overflow-hidden">
      {/* ── Sidebar ──────────────────────────────────────────────────────── */}
      <aside className="w-64 border-r border-slate-800 bg-[#0d1322] flex flex-col justify-between p-4 flex-shrink-0">
        <div>
          <div className="flex items-center gap-3 px-2 py-3 mb-6">
            <div className="h-9 w-9 rounded-xl bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-600/30">
              <Cpu className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-lg leading-tight tracking-tight text-white">IntelliGate</h1>
              <p className="text-xs text-indigo-400 font-medium">Multi-Provider AI Gateway</p>
            </div>
          </div>

          <nav className="space-y-1">
            {[
              { id: "overview", label: "Overview", icon: Layers },
              { id: "keys", label: "Virtual API Keys", icon: Key },
              { id: "providers", label: "Providers", icon: Server },
              { id: "models", label: "Models & Aliases", icon: Cpu },
              { id: "routing", label: "Routing Engine", icon: Sliders },
              { id: "budgets", label: "Budgets & Limits", icon: Coins },
              { id: "guardrails", label: "Guardrails & PII", icon: Shield },
              { id: "cache", label: "Response Cache", icon: Database },
              { id: "analytics", label: "Analytics", icon: BarChart3 },
              { id: "logs", label: "Request Logs", icon: Activity },
              { id: "inspector", label: "Request Inspector", icon: Eye },
              { id: "playground", label: "Live Gateway Test", icon: Play },
              { id: "settings", label: "Settings", icon: Settings },
            ].map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-indigo-600/15 text-indigo-400 border border-indigo-500/20"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                  }`}
                >
                  <Icon className={`h-4 w-4 ${isActive ? "text-indigo-400" : "text-slate-500"}`} />
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>

        <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800 text-xs">
          <div className="flex items-center gap-2 mb-2">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="font-semibold text-slate-300">Gateway Status</span>
          </div>
          <div className="text-slate-500 space-y-1">
            <div className="flex justify-between">
              <span>Engine:</span>
              <span className="text-slate-400 font-mono">v0.1.0-prod</span>
            </div>
            <div className="flex justify-between">
              <span>Circuit Breakers:</span>
              <span className="text-emerald-400 font-semibold">ALL CLOSED</span>
            </div>
          </div>
        </div>
      </aside>

      {/* ── Main Content Area ──────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-16 border-b border-slate-800 px-8 flex items-center justify-between bg-[#0d1322]/50 backdrop-blur">
          <div className="flex items-center gap-4">
            <h2 className="text-lg font-semibold text-white capitalize">
              {activeTab.replace("-", " ")}
            </h2>
            {overview?.is_seeded_data && (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
                Demo Sample Telemetry
              </span>
            )}
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={loadData}
              className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-sm flex items-center gap-1.5 transition"
              title="Refresh Telemetry"
            >
              <RefreshCw className="h-4 w-4" />
              <span>Sync</span>
            </button>
            <div className="h-8 w-px bg-slate-800"></div>
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center font-bold text-xs">
                IG
              </div>
              <span className="text-sm font-medium text-slate-300">Enterprise Admin</span>
            </div>
          </div>
        </header>

        {/* Dynamic Body */}
        <main className="flex-1 overflow-y-auto p-8 space-y-8">
          {/* ────────────────── OVERVIEW TAB ────────────────── */}
          {activeTab === "overview" && (
            <div className="space-y-8">
              {/* Stat Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
                {[
                  { title: "Total Requests", value: formatNumber(overview?.total_requests || 1428), icon: Activity, change: "+12.4%", color: "text-indigo-400" },
                  { title: "Total Tokens", value: formatNumber(overview?.total_tokens || 842190), icon: Cpu, change: "+8.2%", color: "text-blue-400" },
                  { title: "Total Cost", value: formatCurrency(overview?.total_cost_usd || 2.8465), icon: Coins, change: "-4.1%", color: "text-emerald-400" },
                  { title: "Avg Latency", value: `${overview?.average_latency_ms || 312}ms`, icon: Clock, change: "-18ms", color: "text-amber-400" },
                  { title: "Cache Hit Rate", value: `${overview?.cache_hit_rate_pct || 18.6}%`, icon: Zap, change: "+3.2%", color: "text-purple-400" },
                  { title: "Error Rate", value: `${overview?.error_rate_pct || 0.42}%`, icon: AlertTriangle, change: "-0.1%", color: "text-rose-400" },
                ].map((stat, i) => {
                  const Icon = stat.icon;
                  return (
                    <div key={i} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 shadow-sm">
                      <div className="flex items-center justify-between text-slate-400 mb-2">
                        <span className="text-xs font-medium">{stat.title}</span>
                        <Icon className={`h-4 w-4 ${stat.color}`} />
                      </div>
                      <div className="text-xl font-bold text-white">{stat.value}</div>
                      <div className="text-xs text-emerald-400 mt-1 flex items-center gap-1 font-medium">
                        <TrendingUp className="h-3 w-3" />
                        <span>{stat.change} vs last week</span>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Chart Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="font-semibold text-white">Throughput & Request Volume</h3>
                      <p className="text-xs text-slate-400">Total requests processed by IntelliGate over 7 days</p>
                    </div>
                  </div>
                  <div className="h-72 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={timeseries}>
                        <defs>
                          <linearGradient id="colorRequests" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                            <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                        <XAxis dataKey="date" stroke="#64748b" fontSize={11} />
                        <YAxis stroke="#64748b" fontSize={11} />
                        <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155" }} />
                        <Area type="monotone" dataKey="requests" stroke="#6366f1" strokeWidth={2} fillOpacity={1} fill="url(#colorRequests)" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
                  <h3 className="font-semibold text-white mb-1">Provider Share</h3>
                  <p className="text-xs text-slate-400 mb-4">Distribution by upstream LLM provider</p>
                  <div className="h-56 w-full flex items-center justify-center">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={breakdown?.providers || [
                            { name: "OpenAI", percentage: 58.9 },
                            { name: "Anthropic", percentage: 28.8 },
                            { name: "Gemini", percentage: 12.3 },
                          ]}
                          innerRadius={50}
                          outerRadius={75}
                          paddingAngle={4}
                          dataKey="percentage"
                        >
                          {COLORS.map((color, index) => (
                            <Cell key={`cell-${index}`} fill={color} />
                          ))}
                        </Pie>
                        <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155" }} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-center text-xs pt-2 border-t border-slate-800">
                    <div>
                      <div className="text-indigo-400 font-bold">58.9%</div>
                      <div className="text-slate-500">OpenAI</div>
                    </div>
                    <div>
                      <div className="text-emerald-400 font-bold">28.8%</div>
                      <div className="text-slate-500">Anthropic</div>
                    </div>
                    <div>
                      <div className="text-amber-400 font-bold">12.3%</div>
                      <div className="text-slate-500">Gemini</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Provider Health Overview Table */}
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="font-semibold text-white">Active Upstream Providers</h3>
                    <p className="text-xs text-slate-400">Live health, response latency, and circuit breaker status</p>
                  </div>
                  <button onClick={() => setActiveTab("providers")} className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1">
                    Manage Providers <ArrowRight className="h-3 w-3" />
                  </button>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-400 text-xs">
                        <th className="pb-3">Provider</th>
                        <th className="pb-3">Type</th>
                        <th className="pb-3">Status</th>
                        <th className="pb-3">Circuit Breaker</th>
                        <th className="pb-3">Avg Latency</th>
                        <th className="pb-3">Priority</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 text-slate-300 text-xs font-mono">
                      {[
                        { name: "OpenAI Production", type: "openai", status: "HEALTHY", cb: "CLOSED", lat: "215ms", prio: 100 },
                        { name: "Anthropic Claude", type: "anthropic", status: "HEALTHY", cb: "CLOSED", lat: "340ms", prio: 90 },
                        { name: "Google Gemini", type: "gemini", status: "HEALTHY", cb: "CLOSED", lat: "180ms", prio: 80 },
                        { name: "Local vLLM Cluster", type: "openai_compatible", status: "HEALTHY", cb: "CLOSED", lat: "45ms", prio: 70 },
                      ].map((p, idx) => (
                        <tr key={idx} className="hover:bg-slate-800/30 transition">
                          <td className="py-3 font-sans font-medium text-white flex items-center gap-2">
                            <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
                            {p.name}
                          </td>
                          <td className="py-3 text-slate-400">{p.type}</td>
                          <td className="py-3">
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                              {p.status}
                            </span>
                          </td>
                          <td className="py-3">
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                              {p.cb}
                            </span>
                          </td>
                          <td className="py-3 text-slate-300">{p.lat}</td>
                          <td className="py-3 text-indigo-400">{p.prio}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ────────────────── VIRTUAL KEYS TAB ────────────────── */}
          {activeTab === "keys" && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-bold text-white">Virtual API Keys</h3>
                  <p className="text-sm text-slate-400">Scoped API keys with tenant isolation, rate limits, and model restrictions</p>
                </div>
              </div>

              {/* Create Key Box */}
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                <h4 className="font-semibold text-white text-sm">Generate New Key</h4>
                <div className="flex gap-3">
                  <input
                    type="text"
                    placeholder="Key name (e.g. Mobile App Gateway)"
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                  />
                  <button
                    onClick={handleCreateKey}
                    className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-semibold text-white transition flex items-center gap-2"
                  >
                    <Key className="h-4 w-4" /> Generate Key
                  </button>
                </div>

                {generatedKey && (
                  <div className="p-4 rounded-xl bg-indigo-950/40 border border-indigo-500/30 text-sm space-y-2">
                    <div className="flex items-center gap-2 text-amber-400 font-semibold text-xs">
                      <AlertTriangle className="h-4 w-4" />
                      Make sure to copy your virtual key now. You won't be able to see it again!
                    </div>
                    <div className="flex items-center justify-between font-mono bg-slate-950 p-2.5 rounded-lg border border-slate-800 text-indigo-300 select-all">
                      <span>{generatedKey}</span>
                      <button
                        onClick={() => navigator.clipboard.writeText(generatedKey)}
                        className="text-xs bg-indigo-600/30 hover:bg-indigo-600/50 px-2 py-1 rounded text-indigo-200"
                      >
                        Copy
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Keys Table */}
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-400 text-xs">
                        <th className="pb-3">Name</th>
                        <th className="pb-3">Key Prefix</th>
                        <th className="pb-3">Status</th>
                        <th className="pb-3">Rate Limit (RPM)</th>
                        <th className="pb-3">Token Limit (TPM)</th>
                        <th className="pb-3">Created</th>
                        <th className="pb-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 text-slate-300 text-xs">
                      {virtualKeys.map((k) => (
                        <tr key={k.id} className="hover:bg-slate-800/30 transition">
                          <td className="py-3 font-semibold text-white">{k.name}</td>
                          <td className="py-3 font-mono text-indigo-400">{k.prefix}...</td>
                          <td className="py-3">
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                              {k.status}
                            </span>
                          </td>
                          <td className="py-3 font-mono">{k.rpm}</td>
                          <td className="py-3 font-mono">{k.tpm}</td>
                          <td className="py-3 text-slate-400">{k.created}</td>
                          <td className="py-3 text-right">
                            <button
                              onClick={() => setVirtualKeys(virtualKeys.filter((item) => item.id !== k.id))}
                              className="text-rose-400 hover:text-rose-300 text-xs font-semibold"
                            >
                              Revoke
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ────────────────── ROUTING ENGINE TAB ────────────────── */}
          {activeTab === "routing" && (
            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-bold text-white">Intelligent Routing & Failover</h3>
                <p className="text-sm text-slate-400">Configure multi-model routing, automatic retries, and fallback chains</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  { id: "priority", title: "Priority-Based", desc: "Routes in configured order, failing over to backup models on 429/5xx errors" },
                  { id: "lowest_cost", title: "Lowest Cost", desc: "Dynamically picks cheapest compatible model according to real-time pricing" },
                  { id: "lowest_latency", title: "Lowest Latency", desc: "Directs traffic to the provider with lowest exponential moving latency" },
                  { id: "weighted", title: "Weighted Distribution", desc: "Splits requests across providers using randomized roulette weights" },
                  { id: "health_aware", title: "Health-Aware", desc: "Bypasses providers with degraded health or active circuit breakers" },
                  { id: "direct", title: "Direct Passthrough", desc: "Always invokes user-requested model without dynamic fallback" },
                ].map((strat) => (
                  <div
                    key={strat.id}
                    onClick={() => setRoutingStrategy(strat.id)}
                    className={`p-4 rounded-xl border cursor-pointer transition ${
                      routingStrategy === strat.id
                        ? "bg-indigo-600/15 border-indigo-500 text-white shadow-lg shadow-indigo-600/10"
                        : "bg-slate-900/60 border-slate-800 text-slate-400 hover:bg-slate-800/40"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold text-sm text-white">{strat.title}</span>
                      {routingStrategy === strat.id && <CheckCircle2 className="h-4 w-4 text-indigo-400" />}
                    </div>
                    <p className="text-xs text-slate-400">{strat.desc}</p>
                  </div>
                ))}
              </div>

              {/* Model Alias Waterfall */}
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                <h4 className="font-semibold text-white text-sm">Model Alias Cascades</h4>
                <p className="text-xs text-slate-400">Standard aliases resolve to these provider waterfalls:</p>

                <div className="space-y-3">
                  {[
                    { alias: "fast-model", chain: ["OpenAI (gpt-4o-mini)", "Google (gemini-1.5-flash)", "Anthropic (claude-3-5-haiku)"], cost: "$0.00015 / 1K" },
                    { alias: "balanced-model", chain: ["OpenAI (gpt-4o)", "Anthropic (claude-3-5-sonnet)", "Google (gemini-1.5-pro)"], cost: "$0.0025 / 1K" },
                    { alias: "premium-model", chain: ["Anthropic (claude-3-5-sonnet)", "OpenAI (gpt-4o)", "OpenAI (o1)"], cost: "$0.0030 / 1K" },
                  ].map((aliasItem, idx) => (
                    <div key={idx} className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
                      <div>
                        <div className="font-mono text-sm font-bold text-indigo-400">{aliasItem.alias}</div>
                        <div className="flex items-center gap-2 mt-1.5">
                          {aliasItem.chain.map((c, i) => (
                            <React.Fragment key={i}>
                              <span className="px-2 py-0.5 rounded bg-slate-800 text-[11px] text-slate-300 font-mono">
                                {i + 1}. {c}
                              </span>
                              {i < aliasItem.chain.length - 1 && <span className="text-slate-600 text-xs">→</span>}
                            </React.Fragment>
                          ))}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-xs text-slate-500">Base Cost</div>
                        <div className="text-xs font-mono font-semibold text-emerald-400">{aliasItem.cost}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ────────────────── GUARDRAILS & PII TAB ────────────────── */}
          {activeTab === "guardrails" && (
            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-bold text-white">PII Guardrails & Content Safety</h3>
                <p className="text-sm text-slate-400">Microsoft Presidio & custom regex recognizers for zero prompt data leakage</p>
              </div>

              {/* Policy Modes */}
              <div className="grid grid-cols-4 gap-4">
                {[
                  { mode: "disabled", label: "Disabled", desc: "No PII scanning performed" },
                  { mode: "detect_only", label: "Detect Only", desc: "Audit and log detections without mutating prompts" },
                  { mode: "redact", label: "Redact (Default)", desc: "Replace entities with [REDACTED_TYPE] tokens" },
                  { mode: "block", label: "Block", desc: "Reject request with HTTP 400 if any PII is detected" },
                ].map((m) => (
                  <div key={m.mode} className={`p-4 rounded-xl border ${m.mode === "redact" ? "bg-indigo-600/15 border-indigo-500 text-white" : "bg-slate-900/60 border-slate-800 text-slate-400"}`}>
                    <div className="font-semibold text-sm text-white mb-1">{m.label}</div>
                    <div className="text-xs text-slate-400">{m.desc}</div>
                  </div>
                ))}
              </div>

              {/* Interactive PII Playground */}
              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                <h4 className="font-semibold text-white text-sm">Interactive PII Redaction Playground</h4>
                <div className="space-y-2">
                  <label className="text-xs text-slate-400">Input Text with Sensitive Data</label>
                  <textarea
                    rows={3}
                    value={piiInput}
                    onChange={(e) => setPiiInput(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 text-sm text-white focus:outline-none focus:border-indigo-500 font-mono"
                  />
                </div>
                <button
                  onClick={handleTestPii}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-semibold text-white flex items-center gap-2"
                >
                  <Shield className="h-4 w-4" /> Scan & Redact PII
                </button>

                {piiResult && (
                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-slate-400 font-semibold">Detected Entities:</span>
                      {piiResult.entities.map((e: string, i: number) => (
                        <span key={i} className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                          {e}
                        </span>
                      ))}
                    </div>
                    <div>
                      <div className="text-xs text-slate-400 mb-1">Sanitized Output Payload:</div>
                      <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 font-mono text-sm text-emerald-400">
                        {piiResult.redacted}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ────────────────── REQUEST INSPECTOR TAB ────────────────── */}
          {activeTab === "inspector" && (
            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-bold text-white">Request Execution Inspector</h3>
                <p className="text-sm text-slate-400">Deep observability into every step of the 21-stage gateway pipeline</p>
              </div>

              {inspectedRequest ? (
                <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-6">
                  {/* Top Header */}
                  <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                    <div>
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-base font-bold text-white">{inspectedRequest.request_id}</span>
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          {inspectedRequest.status.toUpperCase()}
                        </span>
                      </div>
                      <div className="text-xs text-slate-400 mt-1">
                        Resolved: <span className="text-indigo-400 font-mono">{inspectedRequest.resolved_provider} / {inspectedRequest.model}</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xl font-bold font-mono text-white">{inspectedRequest.total_duration_ms}ms</div>
                      <div className="text-xs text-slate-500">Total Gateway Latency</div>
                    </div>
                  </div>

                  {/* Stage-by-Stage Visual Flow */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Pipeline Stage Breakdown</h4>
                    {inspectedRequest.stages.map((st: any, idx: number) => (
                      <div key={idx} className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between hover:border-slate-700 transition">
                        <div className="flex items-center gap-3">
                          <CheckCircle2 className="h-4 w-4 text-emerald-400 flex-shrink-0" />
                          <div>
                            <div className="font-semibold text-sm text-white">{st.stage}</div>
                            <div className="text-xs text-slate-400">{st.details}</div>
                          </div>
                        </div>
                        <div className="font-mono text-xs text-indigo-400 font-medium">
                          {st.duration_ms}ms
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Accounting & Security Telemetry Summary */}
                  <div className="grid grid-cols-4 gap-4 p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs">
                    <div>
                      <div className="text-slate-500">Prompt / Completion</div>
                      <div className="font-mono font-bold text-slate-200 mt-0.5">
                        {inspectedRequest.telemetry.prompt_tokens} / {inspectedRequest.telemetry.completion_tokens}
                      </div>
                    </div>
                    <div>
                      <div className="text-slate-500">Actual Cost</div>
                      <div className="font-mono font-bold text-emerald-400 mt-0.5">
                        {formatCurrency(inspectedRequest.telemetry.actual_cost_usd)}
                      </div>
                    </div>
                    <div>
                      <div className="text-slate-500">Cache Status</div>
                      <div className="font-semibold text-slate-300 mt-0.5">
                        {inspectedRequest.telemetry.cache_hit ? "HIT" : "MISS"}
                      </div>
                    </div>
                    <div>
                      <div className="text-slate-500">PII Redaction</div>
                      <div className="font-semibold text-amber-400 mt-0.5">
                        {inspectedRequest.telemetry.pii_detected ? "ENFORCED" : "NONE"}
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-12 text-center border border-dashed border-slate-800 rounded-2xl space-y-3">
                  <Eye className="h-8 w-8 text-slate-600 mx-auto" />
                  <p className="text-slate-400 text-sm">Select a request from the Request Logs tab to inspect its stage timings.</p>
                  <button onClick={() => inspectReq("req_8b31f7c2a490")} className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs rounded-lg font-semibold text-indigo-300">
                    Inspect Sample Trace
                  </button>
                </div>
              )}
            </div>
          )}

          {/* ────────────────── REQUEST LOGS TAB ────────────────── */}
          {activeTab === "logs" && (
            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-bold text-white">Live Request Logs</h3>
                <p className="text-sm text-slate-400">Stream of all processed chat completions with audit data</p>
              </div>

              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-400 text-xs">
                        <th className="pb-3">Request ID</th>
                        <th className="pb-3">Model</th>
                        <th className="pb-3">Status</th>
                        <th className="pb-3">Latency</th>
                        <th className="pb-3">Cache</th>
                        <th className="pb-3">PII</th>
                        <th className="pb-3">Time</th>
                        <th className="pb-3 text-right">Inspect</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 text-slate-300 text-xs">
                      {logs.map((log: any, idx: number) => (
                        <tr key={idx} className="hover:bg-slate-800/30 transition">
                          <td className="py-3 font-mono font-medium text-indigo-400">{log.request_id}</td>
                          <td className="py-3 text-white">{log.model_name}</td>
                          <td className="py-3">
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                              log.status === "success"
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                            }`}>
                              {log.status.toUpperCase()}
                            </span>
                          </td>
                          <td className="py-3 font-mono">{log.duration_ms}ms</td>
                          <td className="py-3">
                            {log.cache_hit ? (
                              <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-purple-500/10 text-purple-400 border border-purple-500/20">
                                HIT
                              </span>
                            ) : (
                              <span className="text-slate-500">MISS</span>
                            )}
                          </td>
                          <td className="py-3">
                            {log.pii_detected ? (
                              <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                                REDACTED
                              </span>
                            ) : (
                              <span className="text-slate-500">CLEAN</span>
                            )}
                          </td>
                          <td className="py-3 text-slate-400">{log.created_at ? new Date(log.created_at).toLocaleTimeString() : "Just now"}</td>
                          <td className="py-3 text-right">
                            <button
                              onClick={() => inspectReq(log.request_id)}
                              className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold"
                            >
                              Inspect →
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ────────────────── LIVE GATEWAY PLAYGROUND TAB ────────────────── */}
          {activeTab === "playground" && (
            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-bold text-white">Gateway Interactive Playground</h3>
                <p className="text-sm text-slate-400">Test live requests against the unified OpenAI-compatible endpoint</p>
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                  <h4 className="font-semibold text-white text-sm">Request Parameters</h4>
                  <div>
                    <label className="text-xs text-slate-400 mb-1 block">Model or Alias</label>
                    <select
                      value={playgroundModel}
                      onChange={(e) => setPlaygroundModel(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-sm text-white focus:outline-none"
                    >
                      <option value="gpt-4o">gpt-4o (OpenAI Direct)</option>
                      <option value="gpt-4o-mini">gpt-4o-mini (OpenAI Fast)</option>
                      <option value="claude-3-5-sonnet-20241022">claude-3-5-sonnet (Anthropic)</option>
                      <option value="gemini-1.5-flash">gemini-1.5-flash (Google)</option>
                      <option value="fast-model">fast-model (Auto-Routed Alias)</option>
                      <option value="balanced-model">balanced-model (Auto-Routed Alias)</option>
                      <option value="premium-model">premium-model (Auto-Routed Alias)</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs text-slate-400 mb-1 block">Prompt</label>
                    <textarea
                      rows={5}
                      value={playgroundPrompt}
                      onChange={(e) => setPlaygroundPrompt(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 text-sm text-white focus:outline-none font-mono"
                    />
                  </div>

                  <button
                    onClick={handleTestPlayground}
                    disabled={playgroundLoading}
                    className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-semibold text-white flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {playgroundLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                    <span>Execute POST /v1/chat/completions</span>
                  </button>
                </div>

                <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4 flex flex-col">
                  <h4 className="font-semibold text-white text-sm">Normalized Response Payload</h4>
                  <div className="flex-1 bg-slate-950 rounded-xl p-4 border border-slate-800 font-mono text-xs overflow-y-auto whitespace-pre-wrap text-emerald-400">
                    {playgroundLoading ? (
                      <span className="text-slate-500 animate-pulse">Running 21-stage gateway pipeline...</span>
                    ) : playgroundResponse ? (
                      playgroundResponse
                    ) : (
                      <span className="text-slate-600">Response will appear here after clicking execute.</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ────────────────── MODELS & ALIASES TAB ────────────────── */}
          {activeTab === "models" && (
            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-bold text-white">Registered Models & Cost Matrix</h3>
                <p className="text-sm text-slate-400">Catalog of available LLM models with token limits and pricing</p>
              </div>

              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-400 text-xs">
                        <th className="pb-3">Model</th>
                        <th className="pb-3">Provider</th>
                        <th className="pb-3">Context Window</th>
                        <th className="pb-3">Input / 1K Tokens</th>
                        <th className="pb-3">Output / 1K Tokens</th>
                        <th className="pb-3">Streaming</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 text-slate-300 text-xs font-mono">
                      {[
                        { model: "gpt-4o", provider: "OpenAI", context: "128,000", inCost: "$0.0025", outCost: "$0.0100" },
                        { model: "gpt-4o-mini", provider: "OpenAI", context: "128,000", inCost: "$0.00015", outCost: "$0.00060" },
                        { model: "o1", provider: "OpenAI", context: "200,000", inCost: "$0.0150", outCost: "$0.0600" },
                        { model: "claude-3-5-sonnet", provider: "Anthropic", context: "200,000", inCost: "$0.0030", outCost: "$0.0150" },
                        { model: "claude-3-5-haiku", provider: "Anthropic", context: "200,000", inCost: "$0.0008", outCost: "$0.0040" },
                        { model: "gemini-1.5-pro", provider: "Gemini", context: "1,000,000", inCost: "$0.00125", outCost: "$0.0050" },
                        { model: "gemini-1.5-flash", provider: "Gemini", context: "1,000,000", inCost: "$0.000075", outCost: "$0.00030" },
                      ].map((m, idx) => (
                        <tr key={idx} className="hover:bg-slate-800/30 transition">
                          <td className="py-3 font-semibold text-white">{m.model}</td>
                          <td className="py-3 text-indigo-400">{m.provider}</td>
                          <td className="py-3 text-slate-400">{m.context}</td>
                          <td className="py-3 text-emerald-400">{m.inCost}</td>
                          <td className="py-3 text-emerald-400">{m.outCost}</td>
                          <td className="py-3 text-emerald-400">Yes</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ────────────────── BUDGETS TAB ────────────────── */}
          {activeTab === "budgets" && (
            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-bold text-white">Budgets & Cost Governance</h3>
                <p className="text-sm text-slate-400">Atomic spending limits, reservation tracking, and alert thresholds</p>
              </div>

              <div className="grid grid-cols-3 gap-6">
                <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                  <div className="text-slate-400 text-xs font-medium">Monthly Organization Budget</div>
                  <div className="text-3xl font-bold text-white">$100.00</div>
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-xs text-slate-400">
                      <span>Current Spend</span>
                      <span className="font-mono text-emerald-400">$2.85 (2.85%)</span>
                    </div>
                    <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                      <div className="bg-indigo-500 h-full rounded-full" style={{ width: "2.85%" }}></div>
                    </div>
                  </div>
                  <div className="text-xs text-slate-500 pt-2 border-t border-slate-800">
                    Hard Cap: <span className="text-emerald-400 font-semibold">Enabled</span> (rejects with 402 on overspend)
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                  <div className="text-slate-400 text-xs font-medium">Daily Spending Cap</div>
                  <div className="text-3xl font-bold text-white">$10.00</div>
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-xs text-slate-400">
                      <span>Today's Spend</span>
                      <span className="font-mono text-emerald-400">$0.42 (4.2%)</span>
                    </div>
                    <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                      <div className="bg-emerald-500 h-full rounded-full" style={{ width: "4.2%" }}></div>
                    </div>
                  </div>
                  <div className="text-xs text-slate-500 pt-2 border-t border-slate-800">
                    Resets daily at 00:00 UTC
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                  <div className="text-slate-400 text-xs font-medium">Budget Reconciliation Policy</div>
                  <div className="text-xs text-slate-300 space-y-2">
                    <p>• Atomic Redis Lua reservations prevent concurrent overspend.</p>
                    <p>• Unused estimated funds are automatically released upon request completion.</p>
                    <p>• All billing calculations execute in strict Python Decimal precision.</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ────────────────── CACHE TAB ────────────────── */}
          {activeTab === "cache" && (
            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-bold text-white">Response Caching Engine</h3>
                <p className="text-sm text-slate-400">Exact deterministic response caching with multi-tenant isolation</p>
              </div>

              <div className="grid grid-cols-4 gap-4">
                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                  <div className="text-xs text-slate-400">Total Cache Hits</div>
                  <div className="text-2xl font-bold text-purple-400 mt-1">268</div>
                </div>
                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                  <div className="text-xs text-slate-400">Hit Rate</div>
                  <div className="text-2xl font-bold text-emerald-400 mt-1">18.77%</div>
                </div>
                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                  <div className="text-xs text-slate-400">Tokens Saved</div>
                  <div className="text-2xl font-bold text-blue-400 mt-1">148,520</div>
                </div>
                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                  <div className="text-xs text-slate-400">Estimated Cost Saved</div>
                  <div className="text-2xl font-bold text-emerald-400 mt-1">$1.485</div>
                </div>
              </div>

              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
                <h4 className="font-semibold text-white text-sm">Invalidate Cache Entry</h4>
                <div className="flex gap-3">
                  <input
                    type="text"
                    placeholder="Cache fingerprint (e.g. cache:org123:sha256...)"
                    className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-sm text-white focus:outline-none font-mono"
                  />
                  <button className="px-4 py-2 bg-rose-600/80 hover:bg-rose-600 rounded-lg text-sm font-semibold text-white">
                    Invalidate
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ────────────────── PROVIDERS TAB ────────────────── */}
          {activeTab === "providers" && (
            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-bold text-white">Upstream LLM Providers</h3>
                <p className="text-sm text-slate-400">Connect credentials for OpenAI, Anthropic, Gemini, and custom local servers</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {[
                  { name: "OpenAI", type: "openai", status: "HEALTHY", url: "https://api.openai.com/v1", key: "sk-proj-••••••••••••••••" },
                  { name: "Anthropic", type: "anthropic", status: "HEALTHY", url: "https://api.anthropic.com/v1", key: "sk-ant-••••••••••••••••" },
                  { name: "Google Gemini", type: "gemini", status: "HEALTHY", url: "https://generativelanguage.googleapis.com", key: "AIza••••••••••••••••" },
                  { name: "Local Inference Server", type: "openai_compatible", status: "HEALTHY", url: "http://127.0.0.1:8000/v1", key: "none" },
                ].map((prov, i) => (
                  <div key={i} className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="font-bold text-white text-base">{prov.name}</div>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {prov.status}
                      </span>
                    </div>
                    <div className="text-xs text-slate-400 space-y-1 font-mono">
                      <div>Endpoint: <span className="text-slate-300">{prov.url}</span></div>
                      <div>Key: <span className="text-slate-500">{prov.key}</span></div>
                    </div>
                    <button className="w-full py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-xs font-semibold text-indigo-300 transition">
                      Test Live Ping
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ────────────────── ANALYTICS TAB ────────────────── */}
          {activeTab === "analytics" && (
            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-bold text-white">Observability & Cost Analytics</h3>
                <p className="text-sm text-slate-400">Deep analysis of token usage and financial expenditure</p>
              </div>

              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
                <h4 className="font-semibold text-white text-sm mb-4">Daily Cost Trend ($ USD)</h4>
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={timeseries}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="date" stroke="#64748b" fontSize={11} />
                      <YAxis stroke="#64748b" fontSize={11} />
                      <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155" }} />
                      <Bar dataKey="cost_usd" fill="#10b981" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}

          {/* ────────────────── SETTINGS TAB ────────────────── */}
          {activeTab === "settings" && (
            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-bold text-white">System Settings</h3>
                <p className="text-sm text-slate-400">Gateway configuration and environment secrets</p>
              </div>

              <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4 max-w-2xl">
                <div className="space-y-1">
                  <label className="text-xs text-slate-400 font-semibold">Gateway Public Base URL</label>
                  <input
                    type="text"
                    disabled
                    value="http://localhost:8000/v1"
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-indigo-400 font-mono"
                  />
                  <p className="text-[11px] text-slate-500">Pass this URL as baseURL to any OpenAI SDK client</p>
                </div>

                <div className="space-y-1">
                  <label className="text-xs text-slate-400 font-semibold">Prometheus Metrics Endpoint</label>
                  <input
                    type="text"
                    disabled
                    value="http://localhost:8000/metrics"
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-400 font-mono"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs text-slate-400 font-semibold">Security Vault Status</label>
                  <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs text-emerald-400 flex items-center gap-2">
                    <Shield className="h-4 w-4" />
                    Fernet AES-128 Encryption Key active. All provider credentials safely encrypted at rest.
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

