import React, { useState } from 'react';
import {
  Play, Plus, Trash2, Link as LinkIcon, AlertCircle, CheckCircle2,
  Copy, Check, RotateCcw, Terminal, ArrowRight, ShieldAlert,
  Clock, DollarSign, Layers, ChevronDown, ChevronRight, FileCode
} from 'lucide-react';
import { submitCodingProblem, importCodingProblem } from '../services/api';

const PRESET_CODING_PROBLEMS = [
  {
    title: 'Two Sum Sorted Array',
    statement: 'Given a 1-indexed array of integers numbers that is already sorted in non-decreasing order, find two numbers such that they add up to a specific target number.\n\nInput format:\nFirst line contains N and Target.\nSecond line contains N sorted integers.\n\nOutput format:\nPrint the 1-based indices space-separated.',
    constraints: '2 <= N <= 30000, -1000 <= numbers[i] <= 1000',
    test_cases: [
      { input: '3 9\n2 7 11\n', expected: '1 2\n' },
      { input: '4 6\n2 3 4 5\n', expected: '1 3\n' },
    ],
    language: 'python',
  },
  {
    title: 'Climbing Stairs Dynamic Programming',
    statement: 'You are climbing a staircase. It takes n steps to reach the top. Each time you can either climb 1 or 2 steps. In how many distinct ways can you climb to the top?\n\nInput format:\nA single integer n.\n\nOutput format:\nPrint the total distinct ways.',
    constraints: '1 <= n <= 45',
    test_cases: [
      { input: '2\n', expected: '2\n' },
      { input: '3\n', expected: '3\n' },
      { input: '5\n', expected: '8\n' },
    ],
    language: 'cpp',
  },
  {
    title: 'Valid Palindrome (Alphanumeric)',
    statement: 'A phrase is a palindrome if, after converting all uppercase letters into lowercase letters and removing all non-alphanumeric characters, it reads the same forward and backward.\n\nInput format:\nA single line of string.\n\nOutput format:\nPrint "true" if it is a palindrome, or "false" otherwise.',
    constraints: '1 <= length <= 200000',
    test_cases: [
      { input: 'A man, a plan, a canal: Panama\n', expected: 'true\n' },
      { input: 'race a car\n', expected: 'false\n' },
    ],
    language: 'python',
  },
];

export default function PlaygroundView() {
  const [urlInput, setUrlInput] = useState('');
  const [importing, setImporting] = useState(false);
  const [importError, setImportError] = useState(null);

  const [title, setTitle] = useState(PRESET_CODING_PROBLEMS[0].title);
  const [statement, setStatement] = useState(PRESET_CODING_PROBLEMS[0].statement);
  const [constraints, setConstraints] = useState(PRESET_CODING_PROBLEMS[0].constraints);
  const [language, setLanguage] = useState(PRESET_CODING_PROBLEMS[0].language);

  const [testCases, setTestCases] = useState(PRESET_CODING_PROBLEMS[0].test_cases);

  // Router configuration
  const [routingMode, setRoutingMode] = useState('intelligent');
  const [targetModel, setTargetModel] = useState('gpt-4o');
  const [maxAttempts, setMaxAttempts] = useState(3);
  const [costBudget, setCostBudget] = useState(0.05);

  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [copiedCode, setCopiedCode] = useState(false);
  const [selectedAttemptIdx, setSelectedAttemptIdx] = useState(0);

  // Handle URL import
  async function handleImportUrl() {
    if (!urlInput.trim() || importing) return;
    setImporting(true);
    setImportError(null);
    try {
      const data = await importCodingProblem(urlInput.trim());
      setTitle(data.title || 'Imported Problem');
      setStatement(data.statement || '');
      setConstraints(data.constraints || '');
      if (data.sample_test_cases?.length) {
        setTestCases(data.sample_test_cases);
      }
      setUrlInput('');
    } catch (err) {
      setImportError(err.response?.data?.detail || err.message || 'Failed to import problem from URL');
    } finally {
      setImporting(false);
    }
  }

  // Handle pipeline execution
  async function handleExecute() {
    if (!statement.trim() || testCases.length === 0 || running) return;
    setRunning(true);
    setError(null);
    setResult(null);

    try {
      const res = await submitCodingProblem({
        title: title || 'Custom Problem',
        statement,
        constraints,
        language,
        routing_mode: routingMode,
        target_model: routingMode === 'direct' ? targetModel : null,
        max_attempts: maxAttempts,
        cost_budget_usd: costBudget,
        test_cases: testCases.map((tc) => ({
          input: tc.input.endsWith('\n') ? tc.input : tc.input + '\n',
          expected: tc.expected.endsWith('\n') ? tc.expected : tc.expected + '\n',
          is_sample: true,
        })),
      });
      setResult(res);
      setSelectedAttemptIdx(res.attempts ? res.attempts.length - 1 : 0);
    } catch (err) {
      console.error('Execution error', err);
      setError(err.response?.data?.detail || err.message || 'Submission failed');
    } finally {
      setRunning(false);
    }
  }

  function addTestCase() {
    setTestCases([...testCases, { input: '', expected: '' }]);
  }

  function removeTestCase(idx) {
    setTestCases(testCases.filter((_, i) => i !== idx));
  }

  function updateTestCase(idx, field, val) {
    const updated = [...testCases];
    updated[idx][field] = val;
    setTestCases(updated);
  }

  function copySolution() {
    const code = result?.final_solution_code || '';
    if (!code) return;
    navigator.clipboard.writeText(code);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  }

  const currentAttempt = result?.attempts?.[selectedAttemptIdx];

  return (
    <div className="space-y-6 font-sans">
      {/* Top Problem Ingestion & Presets Bar */}
      <div className="bg-white border border-app-border rounded-lg p-4 space-y-3 shadow-xs">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
          {/* URL Import */}
          <div className="flex items-center gap-2 w-full sm:w-auto flex-1 max-w-xl">
            <div className="relative flex-1">
              <LinkIcon className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-muted" />
              <input
                type="text"
                placeholder="Import problem URL (Codeforces or LeetCode)..."
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleImportUrl()}
                className="w-full bg-app-subtle/50 border border-app-border rounded-md pl-8 pr-2.5 py-1.5 text-xs text-ink-primary focus:outline-none focus:border-metric-blue"
              />
            </div>
            <button
              onClick={handleImportUrl}
              disabled={importing || !urlInput.trim()}
              className="px-3 py-1.5 bg-white hover:bg-app-subtle border border-app-border text-ink-primary rounded-md font-medium text-xs transition-colors cursor-pointer disabled:opacity-50 flex items-center gap-1.5 shadow-2xs"
            >
              {importing ? <Terminal className="w-3 h-3 animate-spin text-metric-blue" /> : <LinkIcon className="w-3 h-3" />}
              <span>Import URL</span>
            </button>
          </div>

          {/* Quick Presets */}
          <div className="flex items-center gap-1.5 self-start sm:self-auto">
            <span className="text-ink-secondary text-xs font-medium mr-1">Presets:</span>
            {PRESET_CODING_PROBLEMS.map((p, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setTitle(p.title);
                  setStatement(p.statement);
                  setConstraints(p.constraints);
                  setTestCases(p.test_cases);
                  setLanguage(p.language);
                }}
                className="px-2.5 py-1 bg-app-subtle hover:bg-slate-200/70 border border-app-border text-xs rounded-md text-ink-secondary hover:text-ink-primary transition-colors cursor-pointer"
              >
                {p.title.split(' ')[0]}
              </button>
            ))}
          </div>
        </div>

        {importError && (
          <div className="p-2.5 bg-red-50 border border-red-200 rounded-md text-xs text-red-700 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{importError}</span>
          </div>
        )}
      </div>

      {/* Main Split Workbench */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Problem Definition & Test Cases */}
        <div className="space-y-4">
          <div className="bg-white border border-app-border rounded-lg p-4 space-y-3 shadow-xs">
            <div className="flex items-center justify-between pb-2 border-b border-app-border">
              <span className="text-xs font-semibold text-ink-primary">Problem Definition</span>
              <span className="text-[11px] text-ink-muted">Manual or Imported</span>
            </div>

            <div>
              <label className="block text-[11px] font-medium text-ink-secondary mb-1">Problem Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Subarray Sum Equals K"
                className="w-full bg-app-subtle/30 border border-app-border rounded-md px-3 py-1.5 text-xs text-ink-primary font-medium focus:outline-none focus:border-metric-blue"
              />
            </div>

            <div>
              <label className="block text-[11px] font-medium text-ink-secondary mb-1">Problem Statement</label>
              <textarea
                rows={7}
                value={statement}
                onChange={(e) => setStatement(e.target.value)}
                placeholder="Enter problem requirements, input/output formats..."
                className="w-full bg-app-subtle/30 border border-app-border rounded-md p-3 text-xs text-ink-primary font-mono focus:outline-none focus:border-metric-blue resize-none leading-relaxed"
              />
            </div>

            <div>
              <label className="block text-[11px] font-medium text-ink-secondary mb-1">Constraints & Bounds</label>
              <input
                type="text"
                value={constraints}
                onChange={(e) => setConstraints(e.target.value)}
                placeholder="e.g. 1 <= N <= 10^5, Time limit: 2.0s"
                className="w-full bg-app-subtle/30 border border-app-border rounded-md px-3 py-1.5 text-xs text-ink-primary font-mono focus:outline-none focus:border-metric-blue"
              />
            </div>
          </div>

          {/* Test Cases Editor */}
          <div className="bg-white border border-app-border rounded-lg p-4 space-y-3 shadow-xs">
            <div className="flex items-center justify-between pb-2 border-b border-app-border">
              <div>
                <span className="text-xs font-semibold text-ink-primary">Verification Test Cases</span>
                <p className="text-[11px] text-ink-secondary">Executed in sandbox against compiled code</p>
              </div>
              <button
                onClick={addTestCase}
                className="px-2.5 py-1 bg-white hover:bg-app-subtle border border-app-border text-ink-primary rounded-md text-xs font-medium flex items-center gap-1 cursor-pointer shadow-2xs"
              >
                <Plus className="w-3 h-3 text-metric-blue" />
                <span>Add Test</span>
              </button>
            </div>

            <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
              {testCases.map((tc, idx) => (
                <div key={idx} className="p-3 bg-app-subtle/40 border border-app-border rounded-md space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-ink-secondary font-mono text-[11px]">
                      Test Case #{idx + 1}
                    </span>
                    {testCases.length > 1 && (
                      <button
                        onClick={() => removeTestCase(idx)}
                        className="text-red-500 hover:text-red-700 cursor-pointer p-0.5"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <span className="text-[10px] text-ink-muted uppercase block mb-0.5">Input (stdin)</span>
                      <textarea
                        rows={2}
                        value={tc.input}
                        onChange={(e) => updateTestCase(idx, 'input', e.target.value)}
                        placeholder="e.g. 3 9\n2 7 11\n"
                        className="w-full bg-white border border-app-border rounded p-1.5 font-mono text-[11px] text-ink-primary focus:outline-none resize-none"
                      />
                    </div>
                    <div>
                      <span className="text-[10px] text-ink-muted uppercase block mb-0.5">Expected (stdout)</span>
                      <textarea
                        rows={2}
                        value={tc.expected}
                        onChange={(e) => updateTestCase(idx, 'expected', e.target.value)}
                        placeholder="e.g. 1 2\n"
                        className="w-full bg-white border border-app-border rounded p-1.5 font-mono text-[11px] text-ink-primary focus:outline-none resize-none"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Configuration & Submit Bar */}
          <div className="bg-white border border-app-border rounded-lg p-4 space-y-3.5 shadow-xs">
            <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
              {/* Target Language */}
              <div className="flex items-center gap-1.5">
                <span className="font-semibold text-ink-secondary">Language:</span>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="bg-white border border-app-border rounded-md px-2.5 py-1 text-xs text-ink-primary font-medium focus:outline-none focus:border-metric-blue cursor-pointer"
                >
                  <option value="python">Python 3.13</option>
                  <option value="cpp">C++17 (g++)</option>
                  <option value="java">Java 25 (OpenJDK)</option>
                </select>
              </div>

              {/* Routing Strategy */}
              <div className="inline-flex items-center bg-app-subtle p-0.5 rounded-md border border-app-border text-xs">
                <button
                  onClick={() => setRoutingMode('intelligent')}
                  className={`px-3 py-1 rounded text-xs font-semibold transition-colors cursor-pointer ${
                    routingMode === 'intelligent'
                      ? 'bg-white text-ink-primary shadow-xs'
                      : 'text-ink-secondary hover:text-ink-primary'
                  }`}
                >
                  Intelligent Router
                </button>
                <button
                  onClick={() => setRoutingMode('lowest_cost')}
                  className={`px-3 py-1 rounded text-xs font-semibold transition-colors cursor-pointer ${
                    routingMode === 'lowest_cost'
                      ? 'bg-white text-ink-primary shadow-xs'
                      : 'text-ink-secondary hover:text-ink-primary'
                  }`}
                >
                  Lowest Cost
                </button>
                <button
                  onClick={() => setRoutingMode('direct')}
                  className={`px-3 py-1 rounded text-xs font-semibold transition-colors cursor-pointer ${
                    routingMode === 'direct'
                      ? 'bg-white text-ink-primary shadow-xs'
                      : 'text-ink-secondary hover:text-ink-primary'
                  }`}
                >
                  Direct Model
                </button>
              </div>

              {/* Direct Model Selection */}
              {routingMode === 'direct' && (
                <div className="flex items-center gap-1.5">
                  <span className="font-semibold text-ink-secondary">Model:</span>
                  <select
                    value={targetModel}
                    onChange={(e) => setTargetModel(e.target.value)}
                    className="bg-white border border-app-border rounded-md px-2 py-1 text-xs text-ink-primary font-mono focus:outline-none focus:border-metric-blue cursor-pointer"
                  >
                    <option value="llama-3.3-70b-versatile">llama-3.3-70b-versatile</option>
                    <option value="gemini-1.5-flash">gemini-1.5-flash</option>
                    <option value="llama-3.1-8b-instant">llama-3.1-8b-instant</option>
                    <option value="gpt-4o">gpt-4o</option>
                    <option value="gpt-4o-mini">gpt-4o-mini</option>
                  </select>
                </div>
              )}
            </div>

            {/* Attempts & Budget */}
            <div className="pt-2 border-t border-app-border/80 flex flex-wrap items-center justify-between gap-3 text-xs text-ink-secondary">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-1.5">
                  <span>Max Attempts:</span>
                  <select
                    value={maxAttempts}
                    onChange={(e) => setMaxAttempts(parseInt(e.target.value, 10))}
                    className="bg-white border border-app-border rounded px-2 py-0.5 text-xs text-ink-primary font-mono"
                  >
                    <option value={1}>1 (No retry)</option>
                    <option value={2}>2 attempts</option>
                    <option value={3}>3 attempts (Recommended)</option>
                    <option value={4}>4 attempts</option>
                  </select>
                </div>

                <div className="flex items-center gap-1.5">
                  <span>Budget Cap:</span>
                  <span className="font-mono text-ink-primary font-medium">${costBudget}</span>
                </div>
              </div>

              <button
                onClick={handleExecute}
                disabled={running || !statement.trim()}
                className="px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white font-semibold text-xs rounded-md inline-flex items-center gap-2 transition-colors cursor-pointer shadow-xs"
              >
                {running ? (
                  <>
                    <Terminal className="w-3.5 h-3.5 animate-spin" />
                    <span>Routing & Verifying...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3 h-3 fill-current" />
                    <span>Run Verification Pipeline</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Execution Output, Trace & Escalation */}
        <div className="space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-xs text-red-700 flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold">Pipeline Execution Error:</span> {error}
              </div>
            </div>
          )}

          {/* Telemetry Summary Ribbon */}
          {result && (
            <div className="grid grid-cols-5 gap-px bg-app-border border border-app-border rounded-lg overflow-hidden text-center shadow-xs">
              <div className="bg-white p-2.5">
                <span className="text-[10px] text-ink-secondary uppercase block font-medium">Outcome</span>
                <span className={`text-xs font-bold mt-0.5 block ${
                  result.status === 'accepted' ? 'text-metric-emerald' : 'text-metric-rose'
                }`}>
                  {result.status === 'accepted' ? 'ACCEPTED' : result.status.toUpperCase()}
                </span>
              </div>
              <div className="bg-white p-2.5">
                <span className="text-[10px] text-ink-secondary uppercase block font-medium">Tests Passed</span>
                <span className="text-xs font-bold font-mono text-ink-primary mt-0.5 block">
                  {result.passed_test_cases} / {result.total_test_cases}
                </span>
              </div>
              <div className="bg-white p-2.5">
                <span className="text-[10px] text-ink-secondary uppercase block font-medium">Attempts</span>
                <span className="text-xs font-bold font-mono text-metric-blue mt-0.5 block">
                  {result.total_attempts} of {maxAttempts}
                </span>
              </div>
              <div className="bg-white p-2.5">
                <span className="text-[10px] text-ink-secondary uppercase block font-medium">Total Cost</span>
                <span className="text-xs font-bold font-mono text-metric-emerald mt-0.5 block">
                  ${result.total_cost_usd.toFixed(5)}
                </span>
              </div>
              <div className="bg-white p-2.5">
                <span className="text-[10px] text-ink-secondary uppercase block font-medium">Latency</span>
                <span className="text-xs font-bold font-mono text-metric-amber mt-0.5 block">
                  {result.total_latency_ms} ms
                </span>
              </div>
            </div>
          )}

          {/* Generated Code Window with Attempt Selector */}
          <div className="bg-white border border-app-border rounded-lg p-4 space-y-3 shadow-xs">
            <div className="flex items-center justify-between pb-2.5 border-b border-app-border">
              <div className="flex items-center gap-2">
                <FileCode className="w-4 h-4 text-metric-blue" />
                <span className="text-xs font-semibold text-ink-primary">Generated Solution</span>
                {result?.attempts && (
                  <div className="flex items-center gap-1 ml-2">
                    {result.attempts.map((att, idx) => (
                      <button
                        key={idx}
                        onClick={() => setSelectedAttemptIdx(idx)}
                        className={`px-2 py-0.5 rounded text-[10px] font-mono font-medium transition-colors cursor-pointer ${
                          selectedAttemptIdx === idx
                            ? 'bg-blue-600 text-white'
                            : 'bg-app-subtle text-ink-secondary hover:bg-slate-200'
                        }`}
                      >
                        Attempt {att.attempt_number}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {result?.final_solution_code && (
                <button
                  onClick={copySolution}
                  className="text-xs text-ink-secondary hover:text-ink-primary flex items-center gap-1 cursor-pointer transition-colors"
                >
                  {copiedCode ? <Check className="w-3.5 h-3.5 text-metric-emerald" /> : <Copy className="w-3.5 h-3.5 text-ink-muted" />}
                  <span>{copiedCode ? 'Copied' : 'Copy'}</span>
                </button>
              )}
            </div>

            <div className="bg-slate-950 text-slate-100 rounded-md p-3.5 font-mono text-xs overflow-x-auto min-h-[160px] max-h-[260px] leading-relaxed">
              {running ? (
                <div className="flex items-center justify-center h-32 text-slate-400 gap-2 font-sans text-xs">
                  <Terminal className="w-4 h-4 animate-spin text-blue-400" />
                  <span>Evaluating benchmark profiles & generating solution...</span>
                </div>
              ) : currentAttempt?.generated_code ? (
                <pre>{currentAttempt.generated_code}</pre>
              ) : (
                <span className="text-slate-500 font-sans text-xs">
                  Click "Run Verification Pipeline" to generate and sandbox-verify code.
                </span>
              )}
            </div>

            {currentAttempt && (
              <div className="p-2.5 bg-app-subtle/50 border border-app-border rounded-md text-xs space-y-1">
                <div className="flex items-center justify-between text-ink-secondary">
                  <span>Model: <strong className="font-mono text-ink-primary">{currentAttempt.model_id}</strong> ({currentAttempt.provider_name})</span>
                  <span>Execution: <strong className={currentAttempt.execution_status === 'accepted' ? 'text-metric-emerald' : 'text-metric-rose'}>{currentAttempt.execution_status.toUpperCase()}</strong></span>
                </div>
                {currentAttempt.algorithm_explanation && (
                  <p className="text-[11px] text-ink-secondary pt-1 border-t border-app-border/40">
                    {currentAttempt.algorithm_explanation}
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Transparent Routing & Escalation Trace */}
          {result?.trace && (
            <div className="bg-white border border-app-border rounded-lg p-4 space-y-3 shadow-xs">
              <div className="flex items-center justify-between pb-2 border-b border-app-border">
                <span className="text-xs font-semibold text-ink-primary flex items-center gap-1.5">
                  <ShieldAlert className="w-3.5 h-3.5 text-metric-blue" />
                  <span>Verification & Escalation Trace</span>
                </span>
                <span className="text-[11px] text-ink-secondary font-mono">
                  {result.trace.length} stages recorded
                </span>
              </div>

              <div className="space-y-2 max-h-64 overflow-y-auto text-xs pr-1">
                {result.trace.map((st, idx) => (
                  <div key={idx} className="p-2.5 bg-app-subtle/40 border border-app-border rounded-md space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-ink-primary text-xs capitalize">
                        {st.stage.replace(/_/g, ' ')}
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                        st.status === 'accepted' || st.status === 'completed'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : st.status === 'escalating'
                          ? 'bg-amber-50 text-amber-800 border border-amber-200'
                          : 'bg-red-50 text-red-700 border border-red-200'
                      }`}>
                        {st.status}
                      </span>
                    </div>

                    {st.details && <p className="text-[11px] text-ink-secondary">{st.details}</p>}
                    {st.reason && <p className="text-[11px] text-ink-secondary border-l-2 border-blue-500 pl-2 mt-1">{st.reason}</p>}
                    {st.action && <p className="text-[11px] text-amber-800 font-medium">{st.action}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
