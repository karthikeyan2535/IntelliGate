# IntelliGate Security & Governance Specification

IntelliGate treats security, credential protection, and tenant privacy as first-class architectural constraints.

---

## 1. Virtual API Key Cryptography
- Virtual keys are generated with 48 random URL-safe base64 characters with standard prefix: `ig-live-...`.
- The raw key is returned to the developer **exactly once** upon creation.
- Raw keys are never stored in the database. Only an HMAC-SHA256 digest (`key_hash`) and an 8-character prefix (`key_prefix`) are persisted.
- Key authentication computes `HMAC-SHA256(raw_key, SECRET_KEY)` and performs a constant-time indexed lookup.

## 2. Upstream Credential Vault
- Provider secrets (e.g. OpenAI `sk-...`, Anthropic `sk-ant-...`, Gemini API keys) are symmetrically encrypted before persisting into PostgreSQL.
- Encryption uses Fernet AES-128-CBC with PKCS7 padding and HMAC authentication.
- Decrypted keys are never logged, never returned over REST APIs, and never sent to the dashboard UI.

## 3. Strict Multi-Tenant Isolation
- Every Virtual API Key is bound to a single Project and Organization.
- Cache fingerprints embed the tenant Organization ID in the SHA-256 canonical hashing payload (`cache:{org_id[:8]}:{digest[:32]}`).
- Cross-tenant cache lookups are physically impossible; deserialization explicitly checks matching `organization_id`.
- Rate limits and budget counters in Redis are prefixed by scope (`rl:org:{org_id}`, `budget:org:{org_id}`).

## 4. PII Redaction & Content Privacy
- Detection engine recognizes Email Addresses, IP Addresses, Credit Card Numbers, US SSNs, and API Keys / Secrets.
- Configurable policies:
  - `DISABLED`: No scanning.
  - `DETECT_ONLY`: Log presence without mutation.
  - `REDACT`: Replace with sanitized tokens (e.g. `[REDACTED_EMAIL_ADDRESS]`).
  - `BLOCK`: Reject request with HTTP 400 Bad Request.
- Prompts are never saved to `request_logs`. Only timing, token counts, and sanitized metadata are persisted.

## 5. Distributed Budget Concurrency Protection
- Atomic budget reservations use Redis Lua scripts prior to upstream invocation.
- Multiple simultaneous requests across different workers cannot exceed the monthly spending limit due to single-threaded Lua script atomicity.
- All monetary math uses Python `Decimal` with `ROUND_HALF_UP` to prevent floating-point calculation drift.

