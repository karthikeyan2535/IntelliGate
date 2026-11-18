/**
 * IntelliGate Frontend API Client.
 * Connects directly to IntelliGate backend endpoints.
 */

const API_BASE = '/api/v1';
const GATEWAY_BASE = '/v1';
const DEMO_KEY = 'ig-playground-virtual-key-demo';

export async function fetchOverview() {
  try {
    const res = await fetch(`${API_BASE}/analytics/overview`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('Overview fallback to default demo data', err);
    return {
      total_requests: 1428,
      total_tokens: 842190,
      total_cost_usd: 2.8465,
      average_latency_ms: 312.4,
      error_rate_pct: 0.42,
      cache_hit_rate_pct: 18.6,
      active_providers: 3,
    };
  }
}

export async function fetchTimeseries(days = 7) {
  try {
    const res = await fetch(`${API_BASE}/analytics/timeseries?days=${days}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    return [
      { date: 'Day 1', requests: 180, cost_usd: 0.32, cache_hits: 34 },
      { date: 'Day 2', requests: 220, cost_usd: 0.41, cache_hits: 45 },
      { date: 'Day 3', requests: 280, cost_usd: 0.55, cache_hits: 58 },
      { date: 'Day 4', requests: 250, cost_usd: 0.48, cache_hits: 50 },
      { date: 'Day 5', requests: 310, cost_usd: 0.62, cache_hits: 65 },
      { date: 'Day 6', requests: 360, cost_usd: 0.74, cache_hits: 78 },
      { date: 'Today', requests: 420, cost_usd: 0.82, cache_hits: 92 },
    ];
  }
}

export async function fetchBreakdown() {
  try {
    const res = await fetch(`${API_BASE}/analytics/breakdown`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    return {
      providers: [
        { name: 'OpenAI', requests: 842, cost_usd: 1.642, percentage: 48.5 },
        { name: 'Groq', requests: 490, cost_usd: 0.284, percentage: 28.2 },
        { name: 'Google Gemini', requests: 404, cost_usd: 0.320, percentage: 23.3 },
      ],
      task_categories: [
        { category: 'coding', label: 'Coding', requests: 580, percentage: 33.4 },
        { category: 'reasoning', label: 'Reasoning', requests: 460, percentage: 26.5 },
        { category: 'writing', label: 'Writing', requests: 396, percentage: 22.8 },
        { category: 'general_qa', label: 'General Q&A', requests: 300, percentage: 17.3 },
      ],
      routing_modes: [
        { mode: 'intelligent', label: 'Intelligent Routing', requests: 1210, percentage: 69.7 },
        { mode: 'lowest_cost', label: 'Lowest Cost', requests: 360, percentage: 20.7 },
        { mode: 'direct', label: 'Direct Model', requests: 166, percentage: 9.6 },
      ],
    };
  }
}

export async function fetchModelProfiles() {
  try {
    const res = await fetch(`${API_BASE}/evaluation/profiles`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    return [
      {
        model_id: 'gpt-4o',
        display_name: 'OpenAI GPT-4o',
        provider: 'openai',
        coding_quality: 0.96,
        reasoning_quality: 0.95,
        writing_quality: 0.94,
        general_qa_quality: 0.97,
        avg_latency_ms: 380.0,
        input_cost_per_1k: 0.0025,
        output_cost_per_1k: 0.0100,
        reliability: 0.995,
        description: 'Flagship frontier model with highest reasoning and synthesis benchmark scores.',
      },
      {
        model_id: 'llama-3.3-70b-versatile',
        display_name: 'Groq Llama 3.3 70B',
        provider: 'groq',
        coding_quality: 0.90,
        reasoning_quality: 0.89,
        writing_quality: 0.92,
        general_qa_quality: 0.94,
        avg_latency_ms: 95.0,
        input_cost_per_1k: 0.00059,
        output_cost_per_1k: 0.00079,
        reliability: 0.992,
        description: 'Near-frontier open model running on Groq LPUs with extreme throughput.',
      },
      {
        model_id: 'gpt-4o-mini',
        display_name: 'OpenAI GPT-4o Mini',
        provider: 'openai',
        coding_quality: 0.84,
        reasoning_quality: 0.82,
        writing_quality: 0.88,
        general_qa_quality: 0.91,
        avg_latency_ms: 190.0,
        input_cost_per_1k: 0.00015,
        output_cost_per_1k: 0.00060,
        reliability: 0.998,
        description: 'High-speed, cost-efficient model ideal for simple-to-moderate tasks.',
      },
      {
        model_id: 'gemini-1.5-flash',
        display_name: 'Google Gemini 1.5 Flash',
        provider: 'gemini',
        coding_quality: 0.82,
        reasoning_quality: 0.80,
        writing_quality: 0.87,
        general_qa_quality: 0.90,
        avg_latency_ms: 160.0,
        input_cost_per_1k: 0.000075,
        output_cost_per_1k: 0.00030,
        reliability: 0.994,
        description: 'Ultra-fast, lowest cost per token with massive 1M context window.',
      },
      {
        model_id: 'llama-3.1-8b-instant',
        display_name: 'Groq Llama 3.1 8B',
        provider: 'groq',
        coding_quality: 0.76,
        reasoning_quality: 0.75,
        writing_quality: 0.83,
        general_qa_quality: 0.86,
        avg_latency_ms: 45.0,
        input_cost_per_1k: 0.00005,
        output_cost_per_1k: 0.00008,
        reliability: 0.996,
        description: 'Instantaneous ~40ms response latency for low-complexity Q&A and writing.',
      },
    ];
  }
}

export async function runEvaluationSuite(modelId, provider, maxItems = 12) {
  const res = await fetch(`${API_BASE}/evaluation/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model_id: modelId, provider, max_items: maxItems }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Evaluation request failed' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return await res.json();
}

export async function executePlaygroundChat({
  systemPrompt = '',
  prompt,
  routingMode,
  model,
  temperature = 0.7,
  maxTokens = 800,
  overrideCategory = null,
  overrideComplexity = null,
}) {
  const messages = [];
  if (systemPrompt && systemPrompt.trim()) {
    messages.push({ role: 'system', content: systemPrompt.trim() });
  }
  messages.push({ role: 'user', content: prompt });

  const payload = {
    model: model || 'intelligent',
    messages,
    temperature: parseFloat(temperature),
    max_tokens: parseInt(maxTokens, 10),
    x_routing_policy: routingMode || 'intelligent',
  };

  if (overrideCategory && overrideCategory !== 'auto') {
    payload['x_override_category'] = overrideCategory;
  }
  if (overrideComplexity && overrideComplexity !== 'auto') {
    payload['x_override_complexity'] = overrideComplexity;
  }

  const res = await fetch(`${GATEWAY_BASE}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${DEMO_KEY}`,
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Gateway completion failed' }));
    throw new Error(err.detail || err.error?.message || `HTTP ${res.status}`);
  }

  const json = await res.json();
  const cacheStatus = res.headers.get('X-IntelliGate-Cache') || 'MISS';
  const reqId = res.headers.get('X-IntelliGate-Request-ID') || json.id;
  const costUsd = res.headers.get('X-IntelliGate-Cost-USD') || '0.000000';
  const taskCategory = res.headers.get('X-IntelliGate-Task-Category') || json.routing_decision?.task_category;
  const complexity = res.headers.get('X-IntelliGate-Complexity') || json.routing_decision?.complexity;

  return {
    ...json,
    cache_status: cacheStatus,
    request_id: reqId,
    cost_usd: costUsd,
    task_category: taskCategory,
    complexity: complexity,
  };
}

export async function fetchEvaluationRuns(limit = 20) {
  try {
    const res = await fetch(`${API_BASE}/evaluation/runs?limit=${limit}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    return [];
  }
}

export async function fetchEvaluationRunDetails(runId) {
  try {
    const res = await fetch(`${API_BASE}/evaluation/runs/${runId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    return null;
  }
}

export async function fetchRequestLogs({ limit = 50, status = '', model = '', cacheHit = null } = {}) {
  try {
    let url = `${API_BASE}/logs?limit=${limit}`;
    if (status) url += `&status=${encodeURIComponent(status)}`;
    if (model) url += `&model=${encodeURIComponent(model)}`;
    if (cacheHit !== null && cacheHit !== undefined) url += `&cache_hit=${cacheHit}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    return [];
  }
}

export async function inspectRequest(requestId) {
  try {
    const res = await fetch(`${API_BASE}/logs/${requestId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    return null;
  }
}

