/**
 * API Service for IntelliGate Dashboard.
 * Connects directly to backend FastAPI endpoints.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

async function request(endpoint: string, options: RequestInit = {}) {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  try {
    const res = await fetch(url, { ...options, headers });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || err.error?.message || `Request failed with status ${res.status}`);
    }
    return await res.json();
  } catch (error: any) {
    console.error(`API Error on ${endpoint}:`, error);
    throw error;
  }
}

export const api = {
  // Analytics
  getOverview: async () => {
    return request("/api/v1/analytics/overview");
  },
  getTimeseries: async (days: number = 7) => {
    return request(`/api/v1/analytics/timeseries?days=${days}`);
  },
  getBreakdown: async () => {
    return request("/api/v1/analytics/breakdown");
  },

  // Logs & Inspector
  getLogs: async (limit: number = 50) => {
    return request(`/api/v1/logs?limit=${limit}`);
  },
  inspectRequest: async (requestId: string) => {
    return request(`/api/v1/logs/${requestId}`);
  },

  // Models
  getModels: async () => {
    return request("/api/v1/models");
  },

  // Cache
  getCacheStats: async () => {
    return request("/api/v1/cache/stats");
  },
  invalidateCache: async (key: string) => {
    return request(`/api/v1/cache/invalidate?key=${encodeURIComponent(key)}`, {
      method: "DELETE",
    });
  },

  // Gateway Live Test (OpenAI-compatible)
  sendChatCompletion: async (apiKey: string, model: string, prompt: string) => {
    return request("/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model,
        messages: [{ role: "user", content: prompt }],
        temperature: 0.0,
      }),
    });
  },
};

