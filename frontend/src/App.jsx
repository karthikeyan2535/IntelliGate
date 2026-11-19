import React, { useState } from 'react';
import {
  Activity, Code2, Award, FlaskConical, FileText, CheckCircle2,
  Copy, Check, ExternalLink, Terminal, ShieldCheck
} from 'lucide-react';
import OverviewView from './components/OverviewView';
import PlaygroundView from './components/PlaygroundView';
import ModelPerformanceView from './components/ModelPerformanceView';
import BenchmarkLabView from './components/BenchmarkLabView';
import RequestHistoryView from './components/RequestHistoryView';

export default function App() {
  const [activeTab, setActiveTab] = useState('playground'); // Default to primary Coding Playground
  const [copiedKey, setCopiedKey] = useState(false);

  const navItems = [
    { id: 'overview', label: 'Overview', icon: Activity },
    { id: 'playground', label: 'Coding Playground', icon: Code2 },
    { id: 'intelligence', label: 'Model Intelligence', icon: Award },
    { id: 'benchmark', label: 'Benchmark Lab', icon: FlaskConical },
    { id: 'history', label: 'Execution History', icon: FileText },
  ];

  return (
    <div className="min-h-screen bg-app-bg text-ink-primary flex flex-col font-sans selection:bg-metric-blue selection:text-white">
      {/* Top Navigation Bar */}
      <header className="border-b border-app-border bg-white sticky top-0 z-50 shadow-2xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="h-14 flex items-center justify-between">
            {/* Brand Logo & Mission */}
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center font-mono font-bold text-sm tracking-tight shadow-xs">
                IG
              </div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm tracking-tight text-ink-primary">
                  IntelliGate
                </span>
                <span className="text-ink-muted text-xs">/</span>
                <span className="text-xs text-ink-secondary hidden sm:inline font-medium">
                  Test-Aware LLM Router for Coding Tasks
                </span>
              </div>
            </div>

            {/* Provider Connectivity Indicators */}
            <div className="hidden md:flex items-center gap-2 text-xs text-ink-secondary">
              <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-app-subtle border border-app-border text-[11px] font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-metric-emerald" />
                <span>OpenAI</span>
              </span>
              <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-app-subtle border border-app-border text-[11px] font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-metric-emerald" />
                <span>Gemini</span>
              </span>
              <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-app-subtle border border-app-border text-[11px] font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-metric-emerald" />
                <span>Groq</span>
              </span>
            </div>

            {/* Links & Repository */}
            <div className="flex items-center gap-2 text-xs">
              <a
                href="https://github.com/karthikeyan2535/IntelliGate"
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-white hover:bg-app-subtle border border-app-border text-ink-secondary hover:text-ink-primary text-xs transition-colors font-medium cursor-pointer"
              >
                <span>GitHub Repository</span>
                <ExternalLink className="w-3.5 h-3.5 text-ink-muted" />
              </a>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex items-center gap-1 border-t border-app-border/40 -mb-[1px]">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`h-10 px-4 text-xs font-medium flex items-center gap-2 border-b-2 transition-colors cursor-pointer ${
                    isActive
                      ? 'border-metric-blue text-ink-primary font-semibold bg-blue-50/20'
                      : 'border-transparent text-ink-secondary hover:text-ink-primary hover:border-app-border'
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

      {/* Main View Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'overview' && <OverviewView onNavigate={setActiveTab} />}
        {activeTab === 'playground' && <PlaygroundView />}
        {activeTab === 'intelligence' && <ModelPerformanceView />}
        {activeTab === 'benchmark' && <BenchmarkLabView />}
        {activeTab === 'history' && <RequestHistoryView onNavigate={setActiveTab} />}
      </main>

      {/* Footer */}
      <footer className="border-t border-app-border bg-white text-ink-secondary text-xs py-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-metric-emerald" />
            <span className="font-semibold text-ink-primary">IntelliGate Coding Router</span>
            <span className="text-ink-muted">•</span>
            <span className="text-ink-secondary">Verification-Driven Multi-Objective Escalation</span>
          </div>
          <div className="text-[11px] text-ink-secondary font-mono">
            Sandboxed C++17 • Python 3 • Java Execution Boundary
          </div>
        </div>
      </footer>
    </div>
  );
}
