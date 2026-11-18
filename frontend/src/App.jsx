import React, { useState } from 'react';
import {
  Activity, Terminal, Award, FileText, CheckCircle2,
  Copy, Check, ExternalLink, Cpu, ShieldCheck
} from 'lucide-react';
import OverviewView from './components/OverviewView';
import PlaygroundView from './components/PlaygroundView';
import ModelPerformanceView from './components/ModelPerformanceView';
import RequestHistoryView from './components/RequestHistoryView';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [copiedKey, setCopiedKey] = useState(false);

  const navItems = [
    { id: 'overview', label: 'Overview', icon: Activity },
    { id: 'playground', label: 'Playground', icon: Terminal },
    { id: 'performance', label: 'Model Benchmarks', icon: Award },
    { id: 'history', label: 'Audit Logs', icon: FileText },
  ];

  function copyApiKey() {
    navigator.clipboard.writeText('ig-playground-virtual-key-demo');
    setCopiedKey(true);
    setTimeout(() => setCopiedKey(false), 2000);
  }

  return (
    <div className="min-h-screen bg-app-bg text-ink-primary flex flex-col font-sans selection:bg-metric-blue selection:text-white">
      {/* Top Header */}
      <header className="border-b border-app-border bg-app-panel/95 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="h-14 flex items-center justify-between">
            {/* Identity */}
            <div className="flex items-center gap-3">
              <div className="w-7 h-7 rounded bg-metric-blue/15 border border-metric-blue/30 flex items-center justify-center text-metric-blue font-mono font-bold text-xs">
                IG
              </div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm tracking-tight text-ink-primary font-mono">
                  INTELLIGATE
                </span>
                <span className="text-ink-faint">/</span>
                <span className="text-xs text-ink-secondary hidden sm:inline">
                  Evaluation-Driven LLM Gateway
                </span>
              </div>
            </div>

            {/* Provider Connectivity Indicators */}
            <div className="hidden md:flex items-center gap-2 text-[11px] font-mono text-ink-muted">
              <span className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-app-subtle border border-app-border">
                <span className="w-1.5 h-1.5 rounded-full bg-metric-emerald" />
                <span className="text-ink-secondary">openai</span>
              </span>
              <span className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-app-subtle border border-app-border">
                <span className="w-1.5 h-1.5 rounded-full bg-metric-emerald" />
                <span className="text-ink-secondary">gemini</span>
              </span>
              <span className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-app-subtle border border-app-border">
                <span className="w-1.5 h-1.5 rounded-full bg-metric-emerald" />
                <span className="text-ink-secondary">groq</span>
              </span>
            </div>

            {/* Actions & Credentials */}
            <div className="flex items-center gap-2 text-xs">
              <button
                onClick={copyApiKey}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-app-subtle hover:bg-app-hover border border-app-border text-ink-secondary hover:text-ink-primary font-mono text-[11px] transition-colors cursor-pointer"
                title="Click to copy demo virtual API key"
              >
                {copiedKey ? (
                  <>
                    <Check className="w-3 h-3 text-metric-emerald" />
                    <span className="text-metric-emerald">copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3 h-3 text-ink-muted" />
                    <span>ig-demo-key</span>
                  </>
                )}
              </button>
              <a
                href="https://github.com/karthikeyan2535/IntelliGate"
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1 px-2.5 py-1 rounded bg-app-subtle hover:bg-app-hover border border-app-border text-ink-secondary hover:text-ink-primary text-[11px] font-mono transition-colors"
              >
                <span>GitHub</span>
                <ExternalLink className="w-3 h-3 text-ink-muted" />
              </a>
            </div>
          </div>

          {/* Navigation Bar */}
          <nav className="flex items-center gap-1 border-t border-app-border/40 -mb-[1px]">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`h-10 px-3.5 text-xs font-medium flex items-center gap-2 border-b-2 transition-colors cursor-pointer ${
                    isActive
                      ? 'border-metric-blue text-ink-primary bg-app-subtle/50'
                      : 'border-transparent text-ink-muted hover:text-ink-secondary hover:bg-app-subtle/20'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-metric-blue' : 'text-ink-muted'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'overview' && <OverviewView onNavigate={setActiveTab} />}
        {activeTab === 'playground' && <PlaygroundView />}
        {activeTab === 'performance' && <ModelPerformanceView />}
        {activeTab === 'history' && <RequestHistoryView />}
      </main>

      {/* Footer */}
      <footer className="border-t border-app-border bg-app-panel text-ink-muted text-[11px] py-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2 font-mono">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-metric-emerald" />
            <span>IntelliGate Core Gateway v1.0</span>
            <span className="text-ink-faint">|</span>
            <span>Port 8000 / 3000</span>
          </div>
          <div>
            <span>Dynamic Pareto Routing • Empirical Benchmark Calibration</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
