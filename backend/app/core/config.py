from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── App ────────────────────────────────────────────────────────────────
    APP_NAME: str = "IntelliGate"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ── Security ──────────────────────────────────────────────────────────
    SECRET_KEY: str = Field(
        default="e3d5bfe7559507229598486a27b1d174a195c7c1e6b568271e204015e9b049f6",
        min_length=32,
    )
    FERNET_KEY: str = Field(
        default="HPcCDO2RT6rJ1vRa3O3XtvlsyOaZG1yjHl0FUyUO32E=",
    )          # base64-encoded 32-byte key
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ALGORITHM: str = "HS256"
    ALLOWED_HOSTS: list[str] = ["*"]

    # ── CORS ──────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://intelligate:intelligate@localhost:5432/intelligate"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_ECHO: bool = False

    # Sync URL for Alembic migrations
    @property
    def SYNC_DATABASE_URL(self) -> str:
        return self.DATABASE_URL.replace("+asyncpg", "+psycopg2").replace(
            "asyncpg://", "psycopg2://"
        )

    # ── Redis ─────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300            # seconds
    REDIS_MAX_CONNECTIONS: int = 50

    # ── Gateway ───────────────────────────────────────────────────────────
    GATEWAY_REQUEST_TIMEOUT: int = 120    # seconds
    GATEWAY_MAX_RETRIES: int = 3
    GATEWAY_RETRY_DELAY: float = 1.0
    GATEWAY_DEFAULT_MODEL: str = "gpt-4o-mini"

    # ── Rate limiting ─────────────────────────────────────────────────────
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT_RPM: int = 60      # requests per minute
    RATE_LIMIT_DEFAULT_TPM: int = 100_000 # tokens per minute

    # ── Metrics / tracing ─────────────────────────────────────────────────
    METRICS_ENABLED: bool = True
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""
    OTEL_SERVICE_NAME: str = "intelligate"

    # ── Providers ────────────────────────────────────────────────────────
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    ANTHROPIC_API_BASE: str = "https://api.anthropic.com"
    GOOGLE_API_BASE: str = "https://generativelanguage.googleapis.com"
    MISTRAL_API_BASE: str = "https://api.mistral.ai/v1"

    # ── PII scanning ─────────────────────────────────────────────────────
    PII_SCAN_ENABLED: bool = True
    PII_SCAN_THRESHOLD: float = 0.7

    # ── Pagination ────────────────────────────────────────────────────────
    PAGE_SIZE_DEFAULT: int = 20
    PAGE_SIZE_MAX: int = 100

    @field_validator("FERNET_KEY")
    @classmethod
    def validate_fernet_key(cls, v: str) -> str:
        import base64

        try:
            decoded = base64.urlsafe_b64decode(v + "==")
            if len(decoded) != 32:
                raise ValueError("FERNET_KEY must decode to exactly 32 bytes")
        except Exception as exc:
            raise ValueError(f"Invalid FERNET_KEY: {exc}") from exc
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
