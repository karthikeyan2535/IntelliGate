# IntelliGate Database Schema Reference

The IntelliGate database is implemented in PostgreSQL 17 using SQLAlchemy 2.0 async annotations and Alembic migrations.

---

## 1. Entity-Relationship Overview

```
organizations (1) ───< organization_members >─── (1) users
       │
       ├───< projects (1) ───< virtual_api_keys
       │
       ├───< providers (1) ───< llm_models
       │
       ├───< budget_policies
       ├───< routing_policies
       ├───< usage_records
       ├───< request_logs
       └───< audit_logs
```

---

## 2. Table Specifications

### `organizations`
- `id` (UUID, PK)
- `name` (VARCHAR 255, NOT NULL)
- `slug` (VARCHAR 100, UNIQUE, NOT NULL)
- `is_active` (BOOLEAN, DEFAULT True)
- `created_at`, `updated_at` (TIMESTAMPTZ)

### `users`
- `id` (UUID, PK)
- `email` (VARCHAR 255, UNIQUE, NOT NULL)
- `username` (VARCHAR 100, UNIQUE, NOT NULL)
- `hashed_password` (VARCHAR 255, NOT NULL - bcrypt)
- `full_name` (VARCHAR 255)
- `is_active` (BOOLEAN)
- `is_superuser` (BOOLEAN)
- `created_at`, `updated_at` (TIMESTAMPTZ)

### `virtual_api_keys`
- `id` (UUID, PK)
- `project_id` (UUID, FK -> `projects.id`)
- `name` (VARCHAR 255, NOT NULL)
- `key_prefix` (VARCHAR 32, NOT NULL - e.g. `ig-live-a1b2`)
- `key_hash` (VARCHAR 64, UNIQUE, NOT NULL - HMAC-SHA256)
- `status` (VARCHAR 20 - `ACTIVE`, `REVOKED`, `EXPIRED`)
- `expires_at` (TIMESTAMPTZ, NULLABLE)
- `allowed_models` (JSONB - e.g. `["gpt-4o", "fast-model"]`)
- `rate_limit_rpm` (INTEGER, NULLABLE)
- `rate_limit_tpm` (INTEGER, NULLABLE)
- `created_at`, `updated_at` (TIMESTAMPTZ)

### `providers`
- `id` (UUID, PK)
- `organization_id` (UUID, FK -> `organizations.id`)
- `name` (VARCHAR 100 - e.g. `openai`, `anthropic`, `gemini`)
- `provider_type` (VARCHAR 50 - `openai`, `anthropic`, `gemini`, `openai_compatible`)
- `display_name` (VARCHAR 255)
- `encrypted_api_key` (TEXT - Fernet symmetrically encrypted)
- `api_base_url` (VARCHAR 512, NULLABLE)
- `priority` (INTEGER, DEFAULT 100)
- `weight` (INTEGER, DEFAULT 1)
- `status` (VARCHAR 20 - `HEALTHY`, `DEGRADED`, `UNHEALTHY`)
- `is_active` (BOOLEAN)
- `created_at`, `updated_at` (TIMESTAMPTZ)

### `llm_models`
- `id` (UUID, PK)
- `provider_id` (UUID, FK -> `providers.id`)
- `name` (VARCHAR 255 - e.g. `gpt-4o`, `claude-3-5-sonnet`)
- `display_name` (VARCHAR 255)
- `aliases` (JSONB - e.g. `["balanced-model"]`)
- `context_window` (INTEGER)
- `max_output_tokens` (INTEGER)
- `input_cost_per_1k_tokens` (NUMERIC(12,8))
- `output_cost_per_1k_tokens` (NUMERIC(12,8))
- `supports_streaming` (BOOLEAN, DEFAULT True)
- `supports_function_calling` (BOOLEAN, DEFAULT False)
- `supports_vision` (BOOLEAN, DEFAULT False)
- `created_at`, `updated_at` (TIMESTAMPTZ)

### `request_logs`
- `id` (UUID, PK)
- `request_id` (VARCHAR 64, UNIQUE, INDEXED)
- `organization_id`, `project_id`, `virtual_key_id` (UUID)
- `model_name` (VARCHAR 255)
- `status` (VARCHAR 20 - `success`, `rate_limited`, `budget_exceeded`, `error`)
- `duration_ms` (INTEGER)
- `cache_hit` (BOOLEAN)
- `pii_detected` (BOOLEAN)
- `retry_count` (INTEGER)
- `fallback_used` (BOOLEAN)
- `stage_timings` (JSONB)
- `created_at` (TIMESTAMPTZ, INDEXED)

