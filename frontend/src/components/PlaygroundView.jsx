import React, { useState } from 'react';
import {
  Terminal, Play, Copy, Check, AlertCircle, CheckCircle2,
  Cpu, ArrowRight, CornerDownLeft, Info, RotateCcw, ChevronDown, ChevronRight, Sliders, ShieldAlert
} from 'lucide-react';
import { executePlaygroundChat } from '../services/api';

const PRESET_VECTORS = [
  {
    tag: 'Coding',
    label: 'FastAPI + SQLAlchemy 2.0',
    prompt: 'Write an async Python function using FastAPI to query PostgreSQL using SQLAlchemy 2.0 with connection pooling, retries, and comprehensive error handling.',
  },
  {
    tag: 'Reasoning',
    label: 'Formal Logic Puzzle',
    prompt: 'Alice has 3 brothers, and each brother has 2 sisters. How many sisters does Alice have? Provide step-by-step logical deduction and proof.',
  },
  {
    tag: 'Writing',
    label: 'Architecture Announcement',
    prompt: 'Draft an engineering blog post announcing IntelliGate: an evaluation-driven LLM gateway that uses multi-objective Pareto optimization instead of static routing rules.',
  },
  {
    tag: 'General QA',
    label: 'Direct Fact Lookup',
    prompt: 'What is the speed of light in vacuum in meters per second, and in what year was it fixed by international agreement?',
  },
];

export default function PlaygroundView() {
  const [systemPrompt, setSystemPrompt] = useState('You are an expert AI assistant that follows technical instructions with high precision.');
  const [showSystemPrompt, setShowSystemPrompt] = useState(false);
  const [prompt, setPrompt] = useState(PRESET_VECTORS[0].prompt);
  const [routingMode, setRoutingMode] = useState('intelligent');
  const [selectedModel, setSelectedModel] = useState('auto');
  const [overrideCategory, setOverrideCategory] = useState('auto');
  const [overrideComplexity, setOverrideComplexity] = useState('auto');
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
        systemPrompt: showSystemPrompt ? systemPrompt : '',
        prompt,
        routingMode,
        model: routingMode === 'direct' ? selectedModel : 'auto',
        temperature,
        maxTokens,
        overrideCategory,
        overrideComplexity,
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

  function handleReset() {
    setPrompt('');
    setSystemPrompt('You are an expert AI assistant that follows technical instructions with high precision.');
    setResponse(null);
    setError(null);
    setOverrideCategory('auto');
    setOverrideComplexity('auto');
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
    <div className="space-y-5 font-sans">
      {/* Primary Configuration Toolbar */}
      <div className="bg-white border border-app-border rounded-lg p-4 space-y-3.5 shadow-xs">
        {/* Top Controls Row */}
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
          {/* Strategy Mode Segmented Control */}
          <div className="inline-flex items-center bg-app-subtle p-0.5 rounded-md border border-app-border text-xs">
            <button
              onClick={() => { setRoutingMode('intelligent'); setSelectedModel('auto'); }}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-colors cursor-pointer ${
                routingMode === 'intelligent'
                  ? 'bg-white text-ink-primary shadow-xs'
                  : 'text-ink-secondary hover:text-ink-primary'
              }`}
            >
              Intelligent Router
            </button>
            <button
              onClick={() => { setRoutingMode('lowest_cost'); setSelectedModel('auto'); }}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-colors cursor-pointer ${
                routingMode === 'lowest_cost'
                  ? 'bg-white text-ink-primary shadow-xs'
                  : 'text-ink-secondary hover:text-ink-primary'
              }`}
            >
              Lowest Cost
            </button>
            <button
              onClick={() => { setRoutingMode('direct'); setSelectedModel('gpt-4o'); }}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-colors cursor-pointer ${
                routingMode === 'direct'
                  ? 'bg-white text-ink-primary shadow-xs'
                  : 'text-ink-secondary hover:text-ink-primary'
              }`}
            >
              Direct Model
            </button>
          </div>

          {/* Model Dropdown (when direct) */}
          {routingMode === 'direct' && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-ink-secondary font-medium">Model:</span>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="bg-white border border-app-border text-ink-primary rounded-md px-2.5 py-1 text-xs focus:outline-none focus:border-metric-blue"
              >
                <option value="gpt-4o">OpenAI GPT-4o (Frontier)</option>
                <option value="llama-3.3-70b-versatile">Groq Llama 3.3 70B (Fast)</option>
                <option value="gpt-4o-mini">OpenAI GPT-4o Mini</option>
                <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
                <option value="llama-3.1-8b-instant">Groq Llama 3.1 8B (Instant)</option>
                <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
              </select>
            </div>
          )}

          {/* Sliders */}
          <div className="flex items-center gap-5 text-xs text-ink-secondary">
            <div className="flex items-center gap-2">
              <span className="font-medium">Temperature:</span>
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="w-16 accent-metric-blue cursor-pointer"
              />
              <span className="font-mono text-ink-primary w-6 text-right font-medium">{temperature}</span>
            </div>

            <div className="flex items-center gap-2">
              <span className="font-medium">Max Tokens:</span>
              <input
                type="number"
                min="50"
                max="2000"
                step="50"
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value, 10))}
                className="w-16 bg-white border border-app-border text-ink-primary rounded-md px-2 py-0.5 text-xs text-right focus:outline-none font-mono"
              />
            </div>
          </div>

          {/* Preset Vectors */}
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-ink-secondary font-medium mr-0.5">Presets:</span>
            {PRESET_VECTORS.map((v, idx) => (
              <button
                key={idx}
                onClick={() => setPrompt(v.prompt)}
                className="px-2 py-1 bg-app-subtle hover:bg-slate-200/70 border border-app-border text-xs rounded text-ink-secondary hover:text-ink-primary transition-colors cursor-pointer"
                title={v.prompt}
              >
                {v.tag}
              </button>
            ))}
          </div>
        </div>

        {/* Secondary Row: Manual Category & Complexity Overrides */}
        <div className="pt-3 border-t border-app-border/70 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-4">
            {/* Category Override */}
            <div className="flex items-center gap-2">
              <span className="text-ink-secondary font-medium">Domain:</span>
              <select
                value={overrideCategory}
                onChange={(e) => setOverrideCategory(e.target.value)}
                className={`bg-white border text-xs rounded-md px-2 py-1 focus:outline-none ${
                  overrideCategory !== 'auto'
                    ? 'border-metric-cyan text-metric-cyan font-medium'
                    : 'border-app-border text-ink-secondary'
                }`}
              >
                <option value="auto">Auto-detect (Heuristic)</option>
                <option value="coding">Coding</option>
                <option value="reasoning">Reasoning</option>
                <option value="writing">Writing</option>
                <option value="general_qa">General Q&A</option>
              </select>
            </div>

            {/* Complexity Override */}
            <div className="flex items-center gap-2">
              <span className="text-ink-secondary font-medium">Complexity:</span>
              <select
                value={overrideComplexity}
                onChange={(e) => setOverrideComplexity(e.target.value)}
                className={`bg-white border text-xs rounded-md px-2 py-1 focus:outline-none ${
                  overrideComplexity !== 'auto'
                    ? 'border-metric-amber text-metric-amber font-medium'
                    : 'border-app-border text-ink-secondary'
                }`}
              >
                <option value="auto">Auto-estimate</option>
                <option value="simple">Simple</option>
                <option value="moderate">Moderate</option>
                <option value="complex">Complex</option>
              </select>
            </div>
          </div>

          {/* System Prompt Toggle & Reset */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowSystemPrompt(!showSystemPrompt)}
              className="text-ink-secondary hover:text-ink-primary flex items-center gap-1 text-xs cursor-pointer"
            >
              {showSystemPrompt ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
              <span>System Prompt</span>
            </button>
            <button
              onClick={handleReset}
              className="px-2 py-1 bg-white hover:bg-app-subtle border border-app-border text-ink-secondary hover:text-ink-primary rounded-md flex items-center gap-1 text-xs cursor-pointer transition-colors"
              title="Reset prompt and parameters"
            >
              <RotateCcw className="w-3 h-3 text-ink-muted" />
              <span>Reset</span>
            </button>
          </div>
        </div>

        {/* Expandable System Prompt Field */}
        {showSystemPrompt && (
          <div className="pt-3 border-t border-app-border/70">
            <label className="block text-xs font-medium text-ink-secondary mb-1">System Instructions</label>
            <textarea
              rows={2}
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              placeholder="System prompt context (e.g. persona, formatting guidelines)..."
              className="w-full bg-app-bg border border-app-border rounded-md p-2.5 text-xs text-ink-primary font-mono focus:outline-none focus:border-metric-blue resize-none leading-relaxed"
            />
          </div>
        )}
      </div>

      {/* Main Split Workbench */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Left: Prompt Input Buffer */}
        <div className="bg-white border border-app-border rounded-lg flex flex-col justify-between shadow-xs">
          <div className="p-4">
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-app-border text-xs">
              <span className="font-semibold text-ink-primary">
                Prompt Input
              </span>
              <span className="text-xs text-ink-secondary font-mono">
                {prompt.length} chars • ~{Math.ceil(prompt.length / 4)} tokens
              </span>
            </div>

            <textarea
              rows={13}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter instruction, question, or code context..."
              className="w-full bg-app-bg/50 border border-app-border rounded-md p-3 text-xs text-ink-primary font-mono focus:outline-none focus:border-metric-blue resize-none leading-relaxed"
            />
          </div>

          <div className="p-3 bg-app-subtle/50 border-t border-app-border flex items-center justify-between text-xs">
            <span className="text-xs text-ink-secondary flex items-center gap-1.5">
              <span>Press</span>
              <kbd className="px-1.5 py-0.5 bg-white border border-app-border rounded text-[11px] font-mono text-ink-primary shadow-2xs">
                Ctrl+Enter
              </kbd>
              <span>to run</span>
            </span>

            <button
              onClick={handleSend}
              disabled={loading || !prompt.trim()}
              className="px-4 py-2 bg-metric-blue hover:bg-blue-600 disabled:opacity-40 text-white font-medium text-xs rounded-md inline-flex items-center gap-2 transition-colors cursor-pointer shadow-xs"
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
            <div className="bg-red-50 border border-red-200 rounded-lg p-3.5 text-xs text-red-700 flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold">Execution Error:</span> {error}
              </div>
            </div>
          )}

          {/* Telemetry Strip */}
          {response && (
            <div className="grid grid-cols-5 gap-px bg-app-border border border-app-border rounded-lg overflow-hidden text-center shadow-xs">
              <div className="bg-white p-2.5">
                <div className="text-[11px] text-ink-secondary font-medium">Resolved Model</div>
                <div className="text-xs font-semibold font-mono text-ink-primary truncate mt-0.5">
                  {response.model || 'auto'}
                </div>
              </div>
              <div className="bg-white p-2.5">
                <div className="text-[11px] text-ink-secondary font-medium">Roundtrip</div>
                <div className="text-xs font-semibold font-mono text-metric-amber mt-0.5">
                  {response.client_latency_ms || 240} ms
                </div>
              </div>
              <div className="bg-white p-2.5">
                <div className="text-[11px] text-ink-secondary font-medium">Tokens</div>
                <div className="text-xs font-semibold font-mono text-metric-cyan mt-0.5">
                  {response.usage?.total_tokens || 0}
                </div>
              </div>
              <div className="bg-white p-2.5">
                <div className="text-[11px] text-ink-secondary font-medium">Cache</div>
                <div className={`text-xs font-semibold font-mono mt-0.5 ${
                  response.cache_status === 'HIT' ? 'text-metric-emerald' : 'text-ink-secondary'
                }`}>
                  {response.cache_status || 'MISS'}
                </div>
              </div>
              <div className="bg-white p-2.5">
                <div className="text-[11px] text-ink-secondary font-medium">Cost USD</div>
                <div className="text-xs font-semibold font-mono text-metric-emerald mt-0.5">
                  {response.cost_usd != null ? `$${Number(response.cost_usd).toFixed(6)}` : '—'}
                </div>
              </div>
            </div>
          )}

          {/* Response Text Box */}
          <div className="bg-white border border-app-border rounded-lg p-4 shadow-xs">
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-app-border text-xs">
              <span className="font-semibold text-ink-primary flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-metric-emerald" />
                Assistant Output
              </span>

              {response?.choices?.[0]?.message?.content && (
                <button
                  onClick={copyOutput}
                  className="text-xs text-ink-secondary hover:text-ink-primary flex items-center gap-1 transition-colors cursor-pointer"
                >
                  {copiedText ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-metric-emerald" />
                      <span className="text-metric-emerald font-medium">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5 text-ink-muted" />
                      <span>Copy</span>
                    </>
                  )}
                </button>
              )}
            </div>

            <div className="bg-app-bg/50 border border-app-border rounded-md p-3 min-h-[140px] max-h-[220px] overflow-y-auto text-xs font-mono text-ink-primary whitespace-pre-wrap leading-relaxed">
              {loading ? (
                <div className="flex items-center justify-center h-28 text-ink-secondary gap-2 font-sans">
                  <Terminal className="w-4 h-4 animate-spin text-metric-blue" />
                  <span>Evaluating Pareto utility across candidate models...</span>
                </div>
              ) : response?.choices?.[0]?.message?.content ? (
                response.choices[0].message.content
              ) : (
                <span className="text-ink-muted font-sans">
                  Execute a prompt above to view model output and routing rationale.
                </span>
              )}
            </div>
          </div>

          {/* Transparent Routing Decision Matrix */}
          {decision && (
            <div className="bg-white border border-app-border rounded-lg p-4 text-xs space-y-3.5 shadow-xs">
              <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-app-border">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-ink-primary">
                    Routing Decision Rationale
                  </span>
                  <span className="px-2 py-0.5 bg-blue-50 border border-blue-200 text-blue-700 rounded text-[11px] font-medium">
                    {decision.mode}
                  </span>
                  {decision.is_overridden && (
                    <span className="px-2 py-0.5 bg-amber-50 border border-amber-200 text-amber-800 rounded text-[11px] font-medium">
                      Manual Override
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <span className="px-2 py-0.5 rounded bg-app-subtle border border-app-border text-ink-secondary capitalize">
                    {decision.task_category}
                  </span>
                  <span className="px-2 py-0.5 rounded bg-app-subtle border border-app-border text-ink-secondary capitalize">
                    {decision.complexity}
                  </span>
                </div>
              </div>

              {/* Justification Text */}
              <div className="p-3 bg-app-bg border border-app-border rounded-md text-xs text-ink-secondary leading-relaxed border-l-4 border-metric-blue">
                {decision.reason}
              </div>

              {/* Applied Weights Strip */}
              {decision.applied_weights && Object.keys(decision.applied_weights).length > 0 && (
                <div className="flex items-center gap-3 text-xs text-ink-secondary bg-app-subtle/60 px-3 py-2 rounded-md border border-app-border">
                  <span className="font-medium text-ink-primary">Applied Weights:</span>
                  {Object.entries(decision.applied_weights).map(([k, w]) => (
                    <span key={k}>
                      {k}: <strong className="font-mono text-ink-primary font-semibold">{(w * 100).toFixed(0)}%</strong>
                    </span>
                  ))}
                </div>
              )}

              {/* Candidate Utility Score Table */}
              {decision.candidate_scores?.length > 0 && (
                <div className="space-y-2 pt-1">
                  <div className="text-xs font-semibold text-ink-primary">
                    Candidate Model Ranking (Multi-Objective Utility)
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="text-[11px] font-semibold text-ink-secondary border-b border-app-border">
                        <tr>
                          <th className="pb-2">Rank</th>
                          <th className="pb-2">Model</th>
                          <th className="pb-2 text-center">Quality (Q)</th>
                          <th className="pb-2 text-center">Cost Score</th>
                          <th className="pb-2 text-center">Latency</th>
                          <th className="pb-2 text-center">$/1K</th>
                          <th className="pb-2 text-right">Utility</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-app-border/60">
                        {decision.candidate_scores.map((c, idx) => (
                          <tr
                            key={idx}
                            className={idx === 0 ? 'bg-blue-50/50 font-medium' : 'hover:bg-app-subtle/30'}
                          >
                            <td className="py-2">
                              <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold font-mono ${
                                idx === 0 ? 'bg-blue-600 text-white' : 'bg-app-subtle text-ink-secondary'
                              }`}>
                                #{c.rank}
                              </span>
                            </td>
                            <td className="py-2 font-mono text-[11px]">
                              {c.model_id} <span className="text-[10px] text-ink-muted">({c.provider})</span>
                            </td>
                            <td className="py-2 text-center font-mono text-[11px] text-metric-cyan">
                              {Number(c.quality_score).toFixed(2)}
                            </td>
                            <td className="py-2 text-center font-mono text-[11px]">
                              {Number(c.cost_score).toFixed(2)}
                            </td>
                            <td className="py-2 text-center font-mono text-[11px] text-metric-amber">
                              {c.latency_ms} ms
                            </td>
                            <td className="py-2 text-center font-mono text-[11px] text-ink-secondary">
                              {c.cost_per_1k != null ? `$${Number(c.cost_per_1k).toFixed(5)}` : '—'}
                            </td>
                            <td className="py-2 text-right font-mono text-xs font-semibold text-metric-emerald">
                              {c.overall_score}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Rejected Candidates & Reasons */}
              {decision.rejected_candidates?.length > 0 && (
                <div className="space-y-2 pt-2.5 border-t border-app-border">
                  <div className="text-xs font-semibold text-ink-primary flex items-center gap-1.5">
                    <ShieldAlert className="w-3.5 h-3.5 text-metric-amber" />
                    <span>Candidate Exclusions</span>
                  </div>
                  <div className="space-y-1.5">
                    {decision.rejected_candidates.slice(0, 5).map((r, idx) => (
                      <div key={idx} className="flex items-start justify-between text-xs bg-app-subtle/40 px-2.5 py-1.5 rounded-md border border-app-border/80">
                        <span className="font-mono text-[11px] text-ink-primary font-medium">{r.model_id}:</span>
                        <span className="text-ink-secondary text-right max-w-[70%]">{r.reason}</span>
                      </div>
                    ))}
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
