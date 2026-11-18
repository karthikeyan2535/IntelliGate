import React, { useState } from 'react';
import {
  Send, Sparkles, Zap, DollarSign, Database, Clock,
  Cpu, Award, ShieldAlert, ChevronRight, CheckCircle2,
  AlertCircle, ArrowRight
} from 'lucide-react';
import { executePlaygroundChat } from '../services/api';

const SAMPLE_PROMPTS = [
  {
    label: '⚡ Complex Coding',
    category: 'coding',
    prompt: 'Write an async Python function using FastAPI to query PostgreSQL using SQLAlchemy 2.0 with connection pooling, retries, and comprehensive error handling.',
  },
  {
    label: '🧠 Logical Reasoning',
    category: 'reasoning',
    prompt: 'Alice has 3 brothers, and each brother has 2 sisters. How many sisters does Alice have? Provide step-by-step logical deduction and proof.',
  },
  {
    label: '✍️ Creative Writing',
    category: 'writing',
    prompt: 'Draft an engaging technical launch announcement for IntelliGate, highlighting its evaluation-driven intelligent routing over brute-force infrastructure.',
  },
  {
    label: '💬 Fast Q&A',
    category: 'general_qa',
    prompt: 'What is the speed of light in meters per second and who first measured it accurately?',
  },
];

export default function PlaygroundView() {
  const [prompt, setPrompt] = useState(SAMPLE_PROMPTS[0].prompt);
  const [routingMode, setRoutingMode] = useState('intelligent');
  const [selectedModel, setSelectedModel] = useState('auto');
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(600);

  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);

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
      console.error('Playground error', err);
      setError(err.message || 'Execution failed');
    } finally {
      setLoading(false);
    }
  }

  const routingDecision = response?.routing_decision;

  return (
    <div className="space-y-6">
      {/* Top Header & Strategy Controls */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-indigo-400" />
              IntelliGate LLM Playground
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Experience evaluation-driven intelligent routing. Every request is classified and matched to optimal models based on empirical benchmarks.
            </p>
          </div>

          {/* Routing Mode Selector */}
          <div className="flex items-center gap-2 bg-slate-950 p-1.5 rounded-lg border border-slate-800">
            <button
              onClick={() => { setRoutingMode('intelligent'); setSelectedModel('auto'); }}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                routingMode === 'intelligent'
                  ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-500/20'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              🎯 Intelligent Routing
            </button>
            <button
              onClick={() => { setRoutingMode('lowest_cost'); setSelectedModel('auto'); }}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                routingMode === 'lowest_cost'
                  ? 'bg-emerald-600 text-white shadow-sm shadow-emerald-500/20'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              💰 Lowest Cost
            </button>
            <button
              onClick={() => { setRoutingMode('direct'); setSelectedModel('gpt-4o'); }}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                routingMode === 'direct'
                  ? 'bg-purple-600 text-white shadow-sm shadow-purple-500/20'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              📌 Direct Model
            </button>
          </div>
        </div>

        {/* Model Dropdown (when direct mode active) & Parameters */}
        <div className="flex flex-wrap items-center gap-4 pt-4 text-xs">
          {routingMode === 'direct' && (
            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-medium">Select Model:</span>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:border-indigo-500"
              >
                <option value="gpt-4o">OpenAI GPT-4o (Frontier)</option>
                <option value="gpt-4o-mini">OpenAI GPT-4o Mini (Fast)</option>
                <option value="llama-3.3-70b-versatile">Groq Llama 3.3 70B (Ultra-fast)</option>
                <option value="llama-3.1-8b-instant">Groq Llama 3.1 8B (Extreme Speed)</option>
                <option value="gemini-1.5-flash">Google Gemini 1.5 Flash (1M Context)</option>
                <option value="gemini-1.5-pro">Google Gemini 1.5 Pro</option>
              </select>
            </div>
          )}

          <div className="flex items-center gap-2">
            <span className="text-slate-400 font-medium">Temperature:</span>
            <input
              type="range"
              min="0.0"
              max="1.0"
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
              className="w-20 accent-indigo-500"
            />
            <span className="text-slate-300 font-mono">{temperature}</span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-slate-400 font-medium">Max Tokens:</span>
            <input
              type="number"
              min="50"
              max="2000"
              step="50"
              value={maxTokens}
              onChange={(e) => setMaxTokens(parseInt(e.target.value, 10))}
              className="w-20 bg-slate-950 border border-slate-800 text-slate-200 rounded px-2 py-1 text-xs focus:outline-none"
            />
          </div>

          {/* Quick preset buttons */}
          <div className="ml-auto flex items-center gap-2">
            <span className="text-slate-500 text-[11px] hidden sm:inline">Sample Prompts:</span>
            {SAMPLE_PROMPTS.map((sample, idx) => (
              <button
                key={idx}
                onClick={() => setPrompt(sample.prompt)}
                className="text-[11px] px-2.5 py-1 bg-slate-800/80 hover:bg-slate-700 text-slate-300 rounded-md transition-colors"
              >
                {sample.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Grid: Input Prompt Pane vs Output & Routing Pane */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Prompt Input */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                User Prompt Input
              </label>
              <span className="text-[11px] text-slate-500 font-mono">
                {prompt.length} chars • ~{Math.ceil(prompt.length / 4)} tokens
              </span>
            </div>
            <textarea
              rows={12}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Enter your prompt here..."
              className="w-full bg-slate-950/80 border border-slate-800 rounded-lg p-3.5 text-sm text-slate-200 font-mono focus:outline-none focus:border-indigo-500/80 transition-colors resize-none placeholder:text-slate-600"
            />
          </div>

          <div className="mt-4 flex items-center justify-between pt-3 border-t border-slate-800/80">
            <div className="text-xs text-slate-400 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Direct pipeline endpoint: <code className="text-slate-300 font-mono">/v1/chat/completions</code>
            </div>
            <button
              onClick={handleSend}
              disabled={loading || !prompt.trim()}
              className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg flex items-center gap-2 shadow-lg shadow-indigo-600/20 transition-all cursor-pointer"
            >
              {loading ? (
                <>
                  <Zap className="w-4 h-4 animate-spin text-white" />
                  Routing & Synthesizing...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  Execute Request
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right: Response Output & Routing Breakdown */}
        <div className="space-y-4">
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 text-xs text-red-400 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold">Execution Failed:</span> {error}
              </div>
            </div>
          )}

          {/* Real-time KPI Ribbon */}
          {response && (
            <div className="grid grid-cols-4 gap-2 bg-slate-900/60 border border-slate-800/80 rounded-xl p-3 text-center">
              <div>
                <div className="text-[10px] text-slate-400 font-medium">Model Used</div>
                <div className="text-xs font-bold text-white font-mono truncate mt-0.5">
                  {response.model || 'Unknown'}
                </div>
              </div>
              <div>
                <div className="text-[10px] text-slate-400 font-medium">Latency</div>
                <div className="text-xs font-bold text-amber-400 font-mono mt-0.5">
                  {response.client_latency_ms || 240} ms
                </div>
              </div>
              <div>
                <div className="text-[10px] text-slate-400 font-medium">Tokens</div>
                <div className="text-xs font-bold text-cyan-400 font-mono mt-0.5">
                  {response.usage?.total_tokens || 0}
                </div>
              </div>
              <div>
                <div className="text-[10px] text-slate-400 font-medium">Cache Status</div>
                <div className="text-xs font-bold text-purple-400 font-mono mt-0.5">
                  {response.cache_status || 'MISS'}
                </div>
              </div>
            </div>
          )}

          {/* Model Response Card */}
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5">
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                Gateway Normalized Response
              </label>
              {response?.cost_usd && (
                <span className="text-[11px] font-mono text-emerald-400">
                  Cost: ${Number(response.cost_usd).toFixed(6)}
                </span>
              )}
            </div>
            <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-3.5 min-h-[140px] max-h-[220px] overflow-y-auto text-xs text-slate-200 font-mono whitespace-pre-wrap">
              {loading ? (
                <div className="flex items-center justify-center h-28 text-slate-500 gap-2">
                  <Zap className="w-4 h-4 animate-spin text-indigo-400" />
                  <span>Evaluating candidate models across benchmarks...</span>
                </div>
              ) : response?.choices?.[0]?.message?.content ? (
                response.choices[0].message.content
              ) : (
                <span className="text-slate-600">Response will appear here after clicking Execute Request...</span>
              )}
            </div>
          </div>

          {/* Transparent Routing Decision Card */}
          {routingDecision && (
            <div className="bg-slate-900/90 border border-indigo-500/30 rounded-xl p-5 shadow-lg shadow-indigo-950/20">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="p-1 rounded bg-indigo-500/20 text-indigo-300 text-xs font-semibold flex items-center gap-1">
                    <Sparkles className="w-3.5 h-3.5" />
                    Routing Decision Explanation
                  </span>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700 capitalize font-medium">
                    {routingDecision.mode} Mode
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-medium uppercase">
                    {routingDecision.task_category}
                  </span>
                  <span className="text-[11px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-medium uppercase">
                    {routingDecision.complexity}
                  </span>
                </div>
              </div>

              {/* Decision reason */}
              <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
                {routingDecision.reason}
              </p>

              {/* Candidate Scoring Breakdown */}
              {routingDecision.candidate_scores?.length > 0 && (
                <div className="mt-4 pt-3 border-t border-slate-800">
                  <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                    Evaluation Matrix & Candidate Utility Ranking
                  </div>
                  <div className="space-y-2">
                    {routingDecision.candidate_scores.slice(0, 4).map((c, idx) => (
                      <div
                        key={idx}
                        className={`p-2.5 rounded-lg border text-xs flex items-center justify-between ${
                          idx === 0
                            ? 'bg-indigo-950/40 border-indigo-500/40 text-white'
                            : 'bg-slate-950/40 border-slate-800 text-slate-400'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                            idx === 0 ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400'
                          }`}>
                            #{c.rank}
                          </span>
                          <div>
                            <span className="font-semibold font-mono text-slate-200">{c.model_id}</span>
                            <span className="text-[10px] text-slate-500 ml-1.5 uppercase">({c.provider})</span>
                          </div>
                        </div>

                        <div className="flex items-center gap-4 text-[11px]">
                          <span title="Empirical benchmark score for this category">
                            Quality: <strong className="text-indigo-300">{Number(c.quality_score).toFixed(2)}</strong>
                          </span>
                          <span title="Average latency under evaluation">
                            Latency: <strong className="text-amber-300">{c.latency_ms}ms</strong>
                          </span>
                          <span title="Normalized Composite Utility Score">
                            Score: <strong className="text-emerald-400 font-mono font-bold">{c.overall_score}</strong>
                          </span>
                        </div>
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
