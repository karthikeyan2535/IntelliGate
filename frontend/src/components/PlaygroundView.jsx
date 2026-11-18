import React, { useState } from 'react';
import {
  Terminal, Play, Copy, Check, AlertCircle, CheckCircle2,
  Cpu, ArrowRight, CornerDownLeft, Info
} from 'lucide-react';
import { executePlaygroundChat } from '../services/api';

const PRESET_VECTORS = [
  {
    tag: 'CODING',
    label: 'FastAPI + SQLAlchemy 2.0',
    prompt: 'Write an async Python function using FastAPI to query PostgreSQL using SQLAlchemy 2.0 with connection pooling, retries, and comprehensive error handling.',
  },
  {
    tag: 'REASONING',
    label: 'Formal Logic Puzzle',
    prompt: 'Alice has 3 brothers, and each brother has 2 sisters. How many sisters does Alice have? Provide step-by-step logical deduction and proof.',
  },
  {
    tag: 'WRITING',
    label: 'Architecture Announcement',
    prompt: 'Draft an engineering blog post announcing IntelliGate: an evaluation-driven LLM gateway that uses multi-objective Pareto optimization instead of static routing rules.',
  },
  {
    tag: 'QA',
    label: 'Direct Fact Lookup',
    prompt: 'What is the speed of light in vacuum in meters per second, and in what year was it fixed by international agreement?',
  },
];

export default function PlaygroundView() {
  const [prompt, setPrompt] = useState(PRESET_VECTORS[0].prompt);
  const [routingMode, setRoutingMode] = useState('intelligent');
  const [selectedModel, setSelectedModel] = useState('auto');
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(600);

  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  const [copiedText, setCopiedText] = useState(false);

  async function handleSend() {
    if (!prompt.trim() || loading) return;
    setLoading(true);
    setError(null);
    setResponse(null);

    const startTime = performance.now();
    try {
      const data = await executePlaygroundChat({
        prompt,
        routingMode,
        model: routingMode === 'direct' ? selectedModel : 'auto',
        temperature,
        maxTokens,
      });
      const clientLat = Math.round(performance.now() - startTime);
      setResponse({
        ...data,
        client_latency_ms: clientLat,
      });
    } catch (err) {
      console.error('Playground execution error', err);
      setError(err.message || 'Execution failed');
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSend();
    }
  }

  function copyOutput() {
    const text = response?.choices?.[0]?.message?.content || '';
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedText(true);
    setTimeout(() => setCopiedText(false), 2000);
  }

  const decision = response?.routing_decision;

  return (
    <div className="space-y-4">
      {/* Configuration & Preset Ribbon */}
      <div className="bg-app-panel border border-app-border rounded-lg p-3.5 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
        {/* Strategy Selector */}
        <div className="flex items-center gap-1.5 bg-app-bg p-1 rounded border border-app-border">
          <button
            onClick={() => { setRoutingMode('intelligent'); setSelectedModel('auto'); }}
            className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-colors cursor-pointer ${
              routingMode === 'intelligent'
                ? 'bg-metric-blue text-white'
                : 'text-ink-muted hover:text-ink-secondary'
            }`}
          >
            INTELLIGENT ROUTER
          </button>
          <button
            onClick={() => { setRoutingMode('lowest_cost'); setSelectedModel('auto'); }}
            className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-colors cursor-pointer ${
              routingMode === 'lowest_cost'
                ? 'bg-metric-emerald text-white'
                : 'text-ink-muted hover:text-ink-secondary'
            }`}
          >
            LOWEST COST
          </button>
          <button
            onClick={() => { setRoutingMode('direct'); setSelectedModel('gpt-4o'); }}
            className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-colors cursor-pointer ${
              routingMode === 'direct'
                ? 'bg-ink-faint text-ink-primary'
                : 'text-ink-muted hover:text-ink-secondary'
            }`}
          >
            DIRECT PINNED
          </button>
        </div>

        {/* Model Dropdown (when direct) */}
        {routingMode === 'direct' && (
          <div className="flex items-center gap-2">
            <span className="text-ink-muted text-[11px]">TARGET:</span>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="bg-app-bg border border-app-border text-ink-primary rounded px-2.5 py-1 text-xs focus:outline-none focus:border-metric-blue font-mono"
            >
              <option value="gpt-4o">openai / gpt-4o (Frontier)</option>
              <option value="llama-3.3-70b-versatile">groq / llama-3.3-70b (LPU Fast)</option>
              <option value="gpt-4o-mini">openai / gpt-4o-mini</option>
              <option value="gemini-1.5-flash">gemini / gemini-1.5-flash</option>
              <option value="llama-3.1-8b-instant">groq / llama-3.1-8b (Ultra-fast)</option>
              <option value="gemini-1.5-pro">gemini / gemini-1.5-pro</option>
            </select>
          </div>
        )}

        {/* Sliders */}
        <div className="flex items-center gap-4 text-[11px]">
          <div className="flex items-center gap-2">
            <span className="text-ink-muted">TEMP:</span>
            <input
              type="range"
              min="0.0"
              max="1.0"
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
              className="w-16 accent-metric-blue"
            />
            <span className="text-ink-primary w-6 text-right">{temperature}</span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-ink-muted">MAX_TOKENS:</span>
            <input
              type="number"
              min="50"
              max="2000"
              step="50"
              value={maxTokens}
              onChange={(e) => setMaxTokens(parseInt(e.target.value, 10))}
              className="w-16 bg-app-bg border border-app-border text-ink-primary rounded px-2 py-0.5 text-xs text-right focus:outline-none"
            />
          </div>
        </div>

        {/* Preset Vectors */}
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] text-ink-muted uppercase mr-1">Vectors:</span>
          {PRESET_VECTORS.map((v, idx) => (
            <button
              key={idx}
              onClick={() => setPrompt(v.prompt)}
              className="px-2 py-0.5 bg-app-subtle hover:bg-app-hover border border-app-border text-[10px] rounded text-ink-secondary hover:text-ink-primary transition-colors cursor-pointer"
              title={v.prompt}
            >
              {v.tag}
            </button>
          ))}
        </div>
      </div>

      {/* Main Split Workbench */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Left: Prompt Input Terminal */}
        <div className="bg-app-panel border border-app-border rounded-lg flex flex-col justify-between">
          <div className="p-4">
            <div className="flex items-center justify-between pb-2.5 mb-2.5 border-b border-app-border text-xs font-mono">
              <span className="text-ink-muted uppercase tracking-wider text-[11px] font-semibold">
                Request Prompt Buffer
              </span>
              <span className="text-ink-faint text-[11px]">
                {prompt.length} chars • ~{Math.ceil(prompt.length / 4)} tokens
              </span>
            </div>

            <textarea
              rows={14}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter instruction, question, or code context..."
              className="w-full bg-app-bg border border-app-border rounded p-3 text-xs text-ink-primary font-mono focus:outline-none focus:border-metric-blue resize-none leading-relaxed"
            />
          </div>

          <div className="p-3 bg-app-subtle/40 border-t border-app-border flex items-center justify-between text-xs font-mono">
            <span className="text-[11px] text-ink-muted flex items-center gap-1">
              <span>Press</span>
              <kbd className="px-1.5 py-0.5 bg-app-bg border border-app-border rounded text-[10px] text-ink-secondary">
                Ctrl+Enter
              </kbd>
              <span>to send</span>
            </span>

            <button
              onClick={handleSend}
              disabled={loading || !prompt.trim()}
              className="px-4 py-1.5 bg-metric-blue hover:bg-blue-600 disabled:opacity-40 text-white font-semibold text-xs rounded inline-flex items-center gap-2 transition-colors cursor-pointer"
            >
              {loading ? (
                <>
                  <Terminal className="w-3.5 h-3.5 animate-spin" />
                  <span>Evaluating & Executing...</span>
                </>
              ) : (
                <>
                  <Play className="w-3 h-3 fill-current" />
                  <span>Execute Pipeline</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right: Response Output & Decision Matrix */}
        <div className="space-y-4">
          {error && (
            <div className="bg-metric-rose/10 border border-metric-rose/30 rounded-lg p-3 text-xs font-mono text-metric-rose flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-bold">Execution Error:</span> {error}
              </div>
            </div>
          )}

          {/* Telemetry Strip */}
          {response && (
            <div className="grid grid-cols-4 gap-px bg-app-border border border-app-border rounded-lg overflow-hidden font-mono text-center">
              <div className="bg-app-panel p-2">
                <div className="text-[10px] text-ink-muted">RESOLVED MODEL</div>
                <div className="text-xs font-bold text-ink-primary truncate mt-0.5">
                  {response.model || 'auto'}
                </div>
              </div>
              <div className="bg-app-panel p-2">
                <div className="text-[10px] text-ink-muted">ROUNDTRIP</div>
                <div className="text-xs font-bold text-metric-amber mt-0.5">
                  {response.client_latency_ms || 240} ms
                </div>
              </div>
              <div className="bg-app-panel p-2">
                <div className="text-[10px] text-ink-muted">TOKENS</div>
                <div className="text-xs font-bold text-metric-cyan mt-0.5">
                  {response.usage?.total_tokens || 0}
                </div>
              </div>
              <div className="bg-app-panel p-2">
                <div className="text-[10px] text-ink-muted">EXACT CACHE</div>
                <div className={`text-xs font-bold mt-0.5 ${
                  response.cache_status === 'HIT' ? 'text-metric-emerald' : 'text-ink-secondary'
                }`}>
                  {response.cache_status || 'MISS'}
                </div>
              </div>
            </div>
          )}

          {/* Response Text Box */}
          <div className="bg-app-panel border border-app-border rounded-lg p-4">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-app-border text-xs font-mono">
              <span className="text-ink-muted uppercase tracking-wider text-[11px] font-semibold flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-metric-emerald" />
                Assistant Output Stream
              </span>

              {response?.choices?.[0]?.message?.content && (
                <button
                  onClick={copyOutput}
                  className="text-[11px] text-ink-muted hover:text-ink-primary flex items-center gap-1 transition-colors cursor-pointer"
                >
                  {copiedText ? (
                    <>
                      <Check className="w-3 h-3 text-metric-emerald" />
                      <span className="text-metric-emerald">copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3 h-3" />
                      <span>copy</span>
                    </>
                  )}
                </button>
              )}
            </div>

            <div className="bg-app-bg border border-app-border rounded p-3 min-h-[140px] max-h-[220px] overflow-y-auto text-xs font-mono text-ink-primary whitespace-pre-wrap leading-relaxed">
              {loading ? (
                <div className="flex items-center justify-center h-28 text-ink-muted gap-2">
                  <Terminal className="w-4 h-4 animate-spin text-metric-blue" />
                  <span>Computing Pareto weights across candidate models...</span>
                </div>
              ) : response?.choices?.[0]?.message?.content ? (
                response.choices[0].message.content
              ) : (
                <span className="text-ink-faint">
                  Execute a prompt above to see gateway response and routing breakdown...
                </span>
              )}
            </div>
          </div>

          {/* Transparent Routing Decision Matrix */}
          {decision && (
            <div className="bg-app-panel border border-app-border rounded-lg p-4 font-mono text-xs space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-app-border">
                <div className="flex items-center gap-2">
                  <span className="text-ink-primary font-bold uppercase tracking-wider text-[11px]">
                    ROUTING DECISION TELEMETRY
                  </span>
                  <span className="px-1.5 py-0.5 bg-app-subtle border border-app-border rounded text-[10px] text-metric-blue uppercase">
                    {decision.mode}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-1.5 py-0.5 rounded bg-app-subtle border border-app-border text-[10px] text-metric-cyan uppercase">
                    CATEGORY: {decision.task_category}
                  </span>
                  <span className="px-1.5 py-0.5 rounded bg-app-subtle border border-app-border text-[10px] text-metric-amber uppercase">
                    COMPLEXITY: {decision.complexity}
                  </span>
                </div>
              </div>

              {/* Justification Text */}
              <div className="p-2.5 bg-app-bg border border-app-border rounded text-[11px] text-ink-secondary leading-relaxed">
                {decision.reason}
              </div>

              {/* Candidate Utility Score Table */}
              {decision.candidate_scores?.length > 0 && (
                <div className="space-y-1.5 pt-1">
                  <div className="text-[10px] font-semibold text-ink-muted uppercase tracking-wider">
                    Candidate Evaluation Ranking & Multi-Objective Scores
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-[11px]">
                      <thead className="text-[10px] text-ink-muted border-b border-app-border">
                        <tr>
                          <th className="pb-1.5">Rank</th>
                          <th className="pb-1.5">Candidate Model</th>
                          <th className="pb-1.5 text-center">Quality (Q)</th>
                          <th className="pb-1.5 text-center">Cost Score</th>
                          <th className="pb-1.5 text-center">Latency</th>
                          <th className="pb-1.5 text-right font-bold">Composite Utility</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-app-border/40">
                        {decision.candidate_scores.slice(0, 4).map((c, idx) => (
                          <tr
                            key={idx}
                            className={idx === 0 ? 'text-ink-primary font-semibold' : 'text-ink-muted'}
                          >
                            <td className="py-1.5">
                              <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
                                idx === 0 ? 'bg-metric-blue text-white' : 'bg-app-subtle text-ink-muted'
                              }`}>
                                #{c.rank}
                              </span>
                            </td>
                            <td className="py-1.5">
                              {c.model_id} <span className="text-[10px] text-ink-faint uppercase">({c.provider})</span>
                            </td>
                            <td className="py-1.5 text-center text-metric-cyan">
                              {Number(c.quality_score).toFixed(2)}
                            </td>
                            <td className="py-1.5 text-center">
                              {Number(c.cost_score).toFixed(2)}
                            </td>
                            <td className="py-1.5 text-center text-metric-amber">
                              {c.latency_ms} ms
                            </td>
                            <td className="py-1.5 text-right font-bold text-metric-emerald font-mono">
                              {c.overall_score}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
