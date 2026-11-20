// Native fetch-based HTTP client for IntelliGate

const BASE_URL = '/api/v1';

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMsg = `HTTP Error ${response.status}`;
    try {
      const errJson = await response.json();
      errorMsg = errJson.detail || errJson.message || errorMsg;
    } catch (_) {}
    const error = new Error(errorMsg);
    error.status = response.status;
    throw error;
  }

  return await response.json();
}

// ── Coding Specific APIs ─────────────────────────────────────────────────────

// Overview analytics
export async function fetchCodingAnalytics() {
  return await request('/coding/analytics/overview');
}

// Problem Ingestion
export async function importCodingProblem(url) {
  return await request('/coding/problems/import', {
    method: 'POST',
    body: JSON.stringify({ url }),
  });
}

export async function createCodingProblem(data) {
  return await request('/coding/problems', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function fetchCodingProblems(params = {}) {
  const query = new URLSearchParams(params).toString();
  return await request(`/coding/problems${query ? `?${query}` : ''}`);
}

export async function fetchCodingProblemDetails(problemId) {
  return await request(`/coding/problems/${problemId}`);
}

// Submissions & Execution
export async function submitCodingProblem(payload) {
  return await request('/coding/submissions', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function fetchCodingSubmissions(limit = 50) {
  return await request(`/coding/submissions?limit=${limit}`);
}

export async function fetchCodingSubmissionDetails(submissionId) {
  return await request(`/coding/submissions/${submissionId}`);
}

// Model Intelligence & Profiles
export async function fetchCodingModelProfiles() {
  return await request('/coding/models/performance');
}

export async function resetCodingBaselines() {
  return await request('/coding/models/performance/reset', {
    method: 'POST',
  });
}

// Benchmarks & Baseline Experiments
export async function runCodingBenchmark(payload) {
  return await request('/coding/benchmarks/run', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function fetchCodingBenchmarkHistory(limit = 20) {
  return await request(`/coding/benchmarks/history?limit=${limit}`);
}

// Machine Learning Difficulty Prediction
export async function predictDifficulty(payload) {
  return await request('/coding/difficulty/predict', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}


export async function fetchBaselineComparisons() {
  return await request('/coding/benchmarks/compare');
}
