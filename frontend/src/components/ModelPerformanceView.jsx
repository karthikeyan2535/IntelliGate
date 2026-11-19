import React, { useState, useEffect } from 'react';
import {
  Award, RefreshCw, Layers, RotateCcw, BarChart2,
  TrendingUp, Clock, DollarSign, CheckCircle2, ShieldCheck
} from 'lucide-react';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid
} from 'recharts';
import { fetchCodingModelProfiles, resetCodingBaselines } from '../services/api';

export default function ModelPerformanceView() {
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterCategory, setFilterCategory] = useState('all');

  useEffect(() => {
    loadProfiles();
  }, []);

  async function loadProfiles() {
    setLoading(true);
    try {
      const data = await fetchCodingModelProfiles();
      setProfiles(data || []);
    } catch (err) {
      console.error('Failed to load coding model profiles', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleResetBaselines() {
    try {
      await resetCodingBaselines();
      await loadProfiles();
    } catch (err) {
      console.error('Failed to reset baselines', err);
    }
  }

  const chartData = profiles.map((p) => ({
    name: p.display_name.replace(' (Versatile)', '').replace(' (Instant)', '').replace(' (Frontier)', ''),
    overall: Math.round(p.overall_pass_rate * 100),
    dp: Math.round(p.dynamic_programming_pass_rate * 100),
    graphs: Math.round(p.graphs_pass_rate * 100),
    arrays: Math.round(p.arrays_strings_pass_rate * 100),
    trees: Math.round(p.trees_data_structures_pass_rate * 100),
    cost_1k: (p.output_cost_per_1k * 1000).toFixed(4),
    latency: Math.round(p.avg_latency_ms),
  }));

  return (
    <div className="space-y-6 font-sans">
      {/* Header & Controls */}
      <div className="bg-white border border-app-border rounded-lg p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
        <div>
          <h2 className="text-sm font-semibold text-ink-primary flex items-center gap-2">
            <Award className="w-4 h-4 text-metric-blue" />
            Model Intelligence & Subdomain Capability Profiles
          </h2>
          <p className="text-xs text-ink-secondary mt-0.5">
            Empirically calibrated coding accuracy measured across 100 benchmark programming problems
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <button
            onClick={loadProfiles}
            className="px-2.5 py-1 bg-white hover:bg-app-subtle border border-app-border text-ink-secondary hover:text-ink-primary rounded-md flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5 text-ink-muted" />
            <span>Sync</span>
          </button>

          <button
            onClick={handleResetBaselines}
            title="Restore baseline calibrated empirical scores for all models"
            className="px-2.5 py-1 bg-white hover:bg-amber-50 border border-app-border text-ink-secondary hover:text-amber-800 rounded-md flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <RotateCcw className="w-3 h-3 text-ink-muted" />
            <span>Reset Baselines</span>
          </button>
        </div>
      </div>

      {/* Primary Capability Profiles Table */}
      <div className="bg-white border border-app-border rounded-lg overflow-hidden shadow-xs">
        <div className="p-3.5 border-b border-app-border flex items-center justify-between">
          <div className="text-xs font-semibold text-ink-primary flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-metric-blue" />
            <span>Coding Accuracy by Algorithm Category</span>
          </div>
          <span className="text-xs text-ink-secondary">
            {profiles.length} active models evaluated
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-app-subtle/50 text-ink-secondary font-semibold text-[11px] border-b border-app-border">
              <tr>
                <th className="py-2.5 px-3">Model</th>
                <th className="py-2.5 px-2">Provider</th>
                <th className="py-2.5 px-2 text-center">Overall</th>
                <th className="py-2.5 px-2 text-center">Arrays & Strings</th>
                <th className="py-2.5 px-2 text-center">Dynamic Prog.</th>
                <th className="py-2.5 px-2 text-center">Graphs</th>
                <th className="py-2.5 px-2 text-center">Trees & DS</th>
                <th className="py-2.5 px-2 text-center">Hard Problems</th>
                <th className="py-2.5 px-2 text-center">P50 Latency</th>
                <th className="py-2.5 px-2 text-right">Cost / Call</th>
                <th className="py-2.5 px-3 text-right">Samples</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-app-border/60">
              {profiles.map((p, idx) => (
                <tr key={idx} className="hover:bg-app-subtle/30 transition-colors">
                  <td className="py-2.5 px-3 font-medium text-ink-primary">
                    <div>{p.display_name}</div>
                    <div className="text-[10px] text-ink-muted font-mono">{p.model_id}</div>
                  </td>
                  <td className="py-2.5 px-2">
                    <span className="px-2 py-0.5 rounded bg-app-subtle border border-app-border text-[11px] capitalize text-ink-secondary font-medium">
                      {p.provider_name}
                    </span>
                  </td>
                  <td className="py-2.5 px-2 text-center font-mono text-xs">
                    <span className="font-bold text-metric-emerald">
                      {(p.overall_pass_rate * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="py-2.5 px-2 text-center font-mono text-xs">
                    {(p.arrays_strings_pass_rate * 100).toFixed(0)}%
                  </td>
                  <td className="py-2.5 px-2 text-center font-mono text-xs">
                    {(p.dynamic_programming_pass_rate * 100).toFixed(0)}%
                  </td>
                  <td className="py-2.5 px-2 text-center font-mono text-xs">
                    {(p.graphs_pass_rate * 100).toFixed(0)}%
                  </td>
                  <td className="py-2.5 px-2 text-center font-mono text-xs">
                    {(p.trees_data_structures_pass_rate * 100).toFixed(0)}%
                  </td>
                  <td className="py-2.5 px-2 text-center font-mono text-xs text-metric-amber font-semibold">
                    {(p.hard_pass_rate * 100).toFixed(0)}%
                  </td>
                  <td className="py-2.5 px-2 text-center font-mono text-xs text-ink-secondary">
                    {Math.round(p.avg_latency_ms)} ms
                  </td>
                  <td className="py-2.5 px-2 text-right font-mono text-xs text-metric-emerald font-semibold">
                    ${p.avg_cost_per_attempt.toFixed(5)}
                  </td>
                  <td className="py-2.5 px-3 text-right font-mono text-xs text-ink-secondary">
                    {p.sample_count}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Comparative Multi-Bar Quality Chart */}
      <div className="bg-white border border-app-border rounded-lg p-5 shadow-xs">
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-app-border">
          <div>
            <h2 className="text-sm font-semibold text-ink-primary flex items-center gap-1.5">
              <BarChart2 className="w-4 h-4 text-metric-blue" />
              <span>Category Accuracy Comparison Across Active Models (%)</span>
            </h2>
            <p className="text-xs text-ink-secondary mt-0.5">
              Empirical pass rates across key algorithmic subdomains
            </p>
          </div>
          <span className="text-xs text-ink-secondary font-mono">
            Benchmark calibration split
          </span>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#475569' }} interval={0} angle={-15} textAnchor="end" />
              <YAxis domain={[30, 100]} tick={{ fontSize: 11, fill: '#475569' }} unit="%" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #cbd5e1',
                  borderRadius: '6px',
                  fontSize: '11px',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
              <Bar dataKey="overall" name="Overall Pass" fill="#2563eb" radius={[3, 3, 0, 0]} />
              <Bar dataKey="dp" name="Dynamic Prog." fill="#0891b2" radius={[3, 3, 0, 0]} />
              <Bar dataKey="graphs" name="Graphs" fill="#059669" radius={[3, 3, 0, 0]} />
              <Bar dataKey="arrays" name="Arrays/Strings" fill="#d97706" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
