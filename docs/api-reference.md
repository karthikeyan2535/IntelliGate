# IntelliGate API Reference

IntelliGate provides a dual-interface architecture:
1. **Public OpenAI-Compatible Gateway API** (under `/v1`)
2. **Control Plane Management REST API** (under `/api/v1`)

---

## 1. Public Gateway API

### Chat Completions
```http
POST /v1/chat/completions
Authorization: Bearer ig-live-your_virtual_key
Content-Type: application/json
```

**Request Body:**
```json
{
  "model": "fast-model",
  "messages": [
    {"role": "system", "content": "You are a concise engineering assistant."},
    {"role": "user", "content": "What is the primary role of a circuit breaker in distributed systems?"}
  ],
  "temperature": 0.0,
  "max_tokens": 150,
  "stream": false,
  "x-routing-policy": "priority",
  "x-cache-ttl": 3600
}
```

**Response (HTTP 200 OK):**
```json
{
  "id": "req_8b31f7c2a490",
  "object": "chat.completion",
  "created": 1731936000,
  "model": "openai/gpt-4o-mini",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "A circuit breaker prevents cascading system failures by failing fast when an upstream dependency is unhealthy, giving it time to recover."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 34,
    "completion_tokens": 28,
    "total_tokens": 62
  }
}
```

**Response Headers:**
- `X-IntelliGate-Request-ID`: `req_8b31f7c2a490`
- `X-IntelliGate-Provider`: `openai`
- `X-IntelliGate-Model`: `gpt-4o-mini`
- `X-IntelliGate-Cost-USD`: `0.00002190`
- `X-IntelliGate-Cache`: `HIT` or `MISS`

---

## 2. Models Endpoint
```http
GET /v1/models
Authorization: Bearer ig-live-your_virtual_key
```

**Response (HTTP 200 OK):**
```json
{
  "object": "list",
  "data": [
    {"id": "gpt-4o", "object": "model", "created": 1731936000, "owned_by": "intelligate"},
    {"id": "claude-3-5-sonnet", "object": "model", "created": 1731936000, "owned_by": "intelligate"},
    {"id": "gemini-1.5-flash", "object": "model", "created": 1731936000, "owned_by": "intelligate"},
    {"id": "fast-model", "object": "model", "created": 1731936000, "owned_by": "intelligate"},
    {"id": "balanced-model", "object": "model", "created": 1731936000, "owned_by": "intelligate"},
    {"id": "premium-model", "object": "model", "created": 1731936000, "owned_by": "intelligate"}
  ]
}
```

---

## 3. Control Plane APIs

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Register initial user and organization |
| `POST` | `/api/v1/auth/login` | Authenticate and obtain JWT bearer token |
| `GET` | `/api/v1/auth/me` | Fetch current user profile |
| `POST` | `/api/v1/projects/{project_id}/keys` | Generate new Virtual API Key (returns raw key once) |
| `GET` | `/api/v1/projects/{project_id}/keys` | List virtual keys with prefix and rate limits |
| `DELETE`| `/api/v1/keys/{key_id}` | Revoke virtual API key |
| `POST` | `/api/v1/orgs/{org_id}/providers` | Register upstream provider with encrypted key |
| `GET` | `/api/v1/orgs/{org_id}/providers` | List configured providers |
| `POST` | `/api/v1/providers/{provider_id}/test`| Test provider live latency and connectivity |
| `GET` | `/api/v1/models` | List all registered models across providers |
| `POST` | `/api/v1/orgs/{org_id}/budgets` | Set monthly/daily organization spending limit |
| `GET` | `/api/v1/analytics/overview` | Fetch high-level KPIs (throughput, cost, cache hit rate) |
| `GET` | `/api/v1/analytics/timeseries` | Fetch 7-day request, token, and cost trend points |
| `GET` | `/api/v1/logs` | Query request audit log entries |
| `GET` | `/api/v1/logs/{request_id}` | Inspect 21-stage execution breakdown for request |
| `DELETE`| `/api/v1/cache/invalidate?key=...` | Evict specific cached fingerprint |

