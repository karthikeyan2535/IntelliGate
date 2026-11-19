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
      <header className="border-b border-app-border bg-white sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="h-14 flex items-center justify-between">
            {/* Identity */}
            <div className="flex items-center gap-3">
              <div className="w-7 h-7 rounded bg-blue-50 border border-blue-200/80 flex items-center justify-center text-blue-600 font-mono font-bold text-xs tracking-tight shadow-xs">
                IG
              </div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-sm tracking-tight text-ink-primary">
                  IntelliGate
                </span>
                <span className="text-ink-muted text-xs hidden sm:inline">/</span>
                <span className="text-xs text-ink-secondary hidden sm:inline">
                  Evaluation-Driven LLM Gateway
                </span>
              </div>
            </div>

            {/* Provider Connectivity Indicators */}
            <div className="hidden md:flex items-center gap-2 text-xs text-ink-secondary">
              <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-app-subtle/80 border border-app-border text-[11px]">
                <span className="w-1.5 h-1.5 rounded-full bg-metric-emerald" />
                <span>OpenAI</span>
              </span>
              <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-app-subtle/80 border border-app-border text-[11px]">
                <span className="w-1.5 h-1.5 rounded-full bg-metric-emerald" />
                <span>Gemini</span>
              </span>
              <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-app-subtle/80 border border-app-border text-[11px]">
                <span className="w-1.5 h-1.5 rounded-full bg-metric-emerald" />
                <span>Groq</span>
              </span>
            </div>

            {/* Actions & Credentials */}
            <div className="flex items-center gap-2 text-xs">
              <button
                onClick={copyApiKey}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-white hover:bg-app-subtle border border-app-border text-ink-secondary hover:text-ink-primary text-xs transition-colors cursor-pointer"
                title="Click to copy demo virtual API key"
              >
                {copiedKey ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-metric-emerald" />
                    <span className="text-metric-emerald font-medium">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5 text-ink-muted" />
                    <span className="font-mono text-[11px]">ig-demo-key</span>
                  </>
                )}
              </button>
              <a
                href="https://github.com/karthikeyan2535/IntelliGate"
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1 px-2.5 py-1 rounded-md bg-white hover:bg-app-subtle border border-app-border text-ink-secondary hover:text-ink-primary text-xs transition-colors"
              >
                <span>GitHub</span>
                <ExternalLink className="w-3.5 h-3.5 text-ink-muted" />
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
                      ? 'border-metric-blue text-ink-primary font-semibold'
                      : 'border-transparent text-ink-muted hover:text-ink-secondary hover:border-app-border'
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
      <footer className="border-t border-app-border bg-white text-ink-muted text-xs py-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-metric-emerald" />
            <span className="font-medium text-ink-secondary">IntelliGate Core Gateway v1.0</span>
            <span className="text-ink-muted">•</span>
            <span className="font-mono text-[11px]">Port 8000 / 3000</span>
          </div>
          <div className="text-[11px] text-ink-secondary">
            Multi-Objective Pareto Routing • Empirical Benchmark Calibration
          </div>
        </div>
      </footer>
    </div>
  );
}
