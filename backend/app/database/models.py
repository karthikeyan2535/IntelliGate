"""
SQLAlchemy 2.0 ORM models for IntelliGate.

Tables:
  - organizations
  - users
  - organization_members
  - projects
  - virtual_api_keys
  - providers
  - llm_models
  - routing_policies
  - budget_policies
  - usage_records
  - request_logs
  - provider_health
  - audit_logs
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


# ── Enums ─────────────────────────────────────────────────────────────────────


class OrgRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class KeyStatus(str, enum.Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class ProviderStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEGRADED = "degraded"


class RequestStatus(str, enum.Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    BUDGET_EXCEEDED = "budget_exceeded"


class RoutingStrategy(str, enum.Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_LATENCY = "least_latency"
    LEAST_COST = "least_cost"
    PRIORITY = "priority"
    RANDOM = "random"
    WEIGHTED = "weighted"


class BudgetPeriod(str, enum.Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    TOTAL = "total"


class AuditAction(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    KEY_GENERATE = "key_generate"
    KEY_REVOKE = "key_revoke"
    PROVIDER_TEST = "provider_test"


# ── organizations ─────────────────────────────────────────────────────────────


class Organization(Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)

    # Relationships
    members: Mapped[list["OrganizationMember"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    projects: Mapped[list["Project"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    providers: Mapped[list["Provider"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    budget_policies: Mapped[list["BudgetPolicy"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    usage_records: Mapped[list["UsageRecord"]] = relationship(
        back_populates="organization"
    )

    __table_args__ = (
        UniqueConstraint("slug", name="uq_organizations_slug"),
        Index("ix_organizations_slug", "slug"),
        Index("ix_organizations_is_active", "is_active"),
    )


# ── users ─────────────────────────────────────────────────────────────────────


class User(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    org_memberships: Mapped[list["OrganizationMember"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        primaryjoin="User.id == OrganizationMember.user_id",
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user")

    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("username", name="uq_users_username"),
        Index("ix_users_email", "email"),
        Index("ix_users_username", "username"),
        Index("ix_users_is_active", "is_active"),
    )


# ── organization_members ──────────────────────────────────────────────────────


class OrganizationMember(Base):
    __tablename__ = "organization_members"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[OrgRole] = mapped_column(
        Enum(OrgRole), default=OrgRole.MEMBER, nullable=False
    )
    invited_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(
        back_populates="org_memberships", foreign_keys=[user_id]
    )

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "user_id", name="uq_org_members_org_user"
        ),
        Index("ix_org_members_org_id", "organization_id"),
        Index("ix_org_members_user_id", "user_id"),
    )


# ── projects ──────────────────────────────────────────────────────────────────


class Project(Base):
    __tablename__ = "projects"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    settings_: Mapped[Optional[dict]] = mapped_column("settings", JSONB, nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="projects")
    virtual_api_keys: Mapped[list["VirtualApiKey"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    routing_policies: Mapped[list["RoutingPolicy"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    request_logs: Mapped[list["RequestLog"]] = relationship(back_populates="project")

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "slug", name="uq_projects_org_slug"
        ),
        Index("ix_projects_organization_id", "organization_id"),
        Index("ix_projects_slug", "slug"),
    )


# ── virtual_api_keys ──────────────────────────────────────────────────────────


class VirtualApiKey(Base):
    __tablename__ = "virtual_api_keys"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256 hex
    key_prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[KeyStatus] = mapped_column(
        Enum(KeyStatus), default=KeyStatus.ACTIVE, nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    allowed_models: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    rate_limit_rpm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rate_limit_tpm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="virtual_api_keys")
    request_logs: Mapped[list["RequestLog"]] = relationship(
        back_populates="virtual_api_key"
    )
    usage_records: Mapped[list["UsageRecord"]] = relationship(
        back_populates="virtual_api_key"
    )

    __table_args__ = (
        UniqueConstraint("key_hash", name="uq_virtual_api_keys_hash"),
        Index("ix_virtual_api_keys_project_id", "project_id"),
        Index("ix_virtual_api_keys_key_hash", "key_hash"),
        Index("ix_virtual_api_keys_status", "status"),
        Index("ix_virtual_api_keys_prefix", "key_prefix"),
    )


# ── providers ─────────────────────────────────────────────────────────────────


class Provider(Base):
    __tablename__ = "providers"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(50), nullable=False)  # openai, anthropic, etc.
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    api_key_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    api_base_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    status: Mapped[ProviderStatus] = mapped_column(
        Enum(ProviderStatus), default=ProviderStatus.ACTIVE, nullable=False
    )
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    weight: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    extra_headers: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    extra_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="providers")
    llm_models: Mapped[list["LLMModel"]] = relationship(
        back_populates="provider", cascade="all, delete-orphan"
    )
    health_records: Mapped[list["ProviderHealth"]] = relationship(
        back_populates="provider", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "name", name="uq_providers_org_name"
        ),
        Index("ix_providers_organization_id", "organization_id"),
        Index("ix_providers_provider_type", "provider_type"),
        Index("ix_providers_status", "status"),
        Index("ix_providers_is_active", "is_active"),
    )


# ── llm_models ────────────────────────────────────────────────────────────────


class LLMModel(Base):
    __tablename__ = "llm_models"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("providers.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)       # provider's model ID
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    aliases: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)   # alternative names
    context_window: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_output_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    input_cost_per_1k_tokens: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 8), nullable=True
    )
    output_cost_per_1k_tokens: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 8), nullable=True
    )
    supports_streaming: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supports_function_calling: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_vision: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    extra_params: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    provider: Mapped["Provider"] = relationship(back_populates="llm_models")
    request_logs: Mapped[list["RequestLog"]] = relationship(back_populates="llm_model")

    __table_args__ = (
        UniqueConstraint("provider_id", "name", name="uq_llm_models_provider_name"),
        Index("ix_llm_models_provider_id", "provider_id"),
        Index("ix_llm_models_name", "name"),
        Index("ix_llm_models_is_active", "is_active"),
    )


# ── routing_policies ──────────────────────────────────────────────────────────


class RoutingPolicy(Base):
    __tablename__ = "routing_policies"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    strategy: Mapped[RoutingStrategy] = mapped_column(
        Enum(RoutingStrategy), default=RoutingStrategy.ROUND_ROBIN, nullable=False
    )
    fallback_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fallback_provider_ids: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    rules: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="routing_policies")

    __table_args__ = (
        Index("ix_routing_policies_project_id", "project_id"),
        Index("ix_routing_policies_is_active", "is_active"),
    )


# ── budget_policies ───────────────────────────────────────────────────────────


class BudgetPolicy(Base):
    __tablename__ = "budget_policies"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    period: Mapped[BudgetPeriod] = mapped_column(
        Enum(BudgetPeriod), default=BudgetPeriod.MONTHLY, nullable=False
    )
    limit_usd: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    current_spend_usd: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), default=Decimal("0"), nullable=False
    )
    alert_threshold_pct: Mapped[int] = mapped_column(Integer, default=80, nullable=False)
    hard_limit: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    reset_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="budget_policies")

    __table_args__ = (
        Index("ix_budget_policies_organization_id", "organization_id"),
        Index("ix_budget_policies_is_active", "is_active"),
    )


# ── usage_records ─────────────────────────────────────────────────────────────


class UsageRecord(Base):
    __tablename__ = "usage_records"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    virtual_api_key_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("virtual_api_keys.id", ondelete="SET NULL"),
        nullable=True,
    )
    provider_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("providers.id", ondelete="SET NULL"),
        nullable=True,
    )
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(12, 8), default=Decimal("0"), nullable=False
    )
    period_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="usage_records")
    virtual_api_key: Mapped[Optional["VirtualApiKey"]] = relationship(
        back_populates="usage_records"
    )

    __table_args__ = (
        Index("ix_usage_records_organization_id", "organization_id"),
        Index("ix_usage_records_virtual_api_key_id", "virtual_api_key_id"),
        Index("ix_usage_records_period_date", "period_date"),
        Index("ix_usage_records_model_name", "model_name"),
    )


# ── request_logs ─────────────────────────────────────────────────────────────


class RequestLog(Base):
    __tablename__ = "request_logs"

    virtual_api_key_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("virtual_api_keys.id", ondelete="SET NULL"),
        nullable=True,
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
    )
    provider_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("providers.id", ondelete="SET NULL"),
        nullable=True,
    )
    llm_model_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("llm_models.id", ondelete="SET NULL"),
        nullable=True,
    )
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    model_requested: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    model_used: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[RequestStatus] = mapped_column(Enum(RequestStatus), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(12, 8), default=Decimal("0"), nullable=False
    )
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_streaming: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cached: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    client_ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    request_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    virtual_api_key: Mapped[Optional["VirtualApiKey"]] = relationship(
        back_populates="request_logs"
    )
    project: Mapped[Optional["Project"]] = relationship(back_populates="request_logs")
    llm_model: Mapped[Optional["LLMModel"]] = relationship(back_populates="request_logs")

    __table_args__ = (
        Index("ix_request_logs_request_id", "request_id"),
        Index("ix_request_logs_virtual_api_key_id", "virtual_api_key_id"),
        Index("ix_request_logs_project_id", "project_id"),
        Index("ix_request_logs_provider_id", "provider_id"),
        Index("ix_request_logs_status", "status"),
        Index("ix_request_logs_created_at", "created_at"),
    )


# ── provider_health ───────────────────────────────────────────────────────────


class ProviderHealth(Base):
    __tablename__ = "provider_health"

    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("providers.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_healthy: Mapped[bool] = mapped_column(Boolean, nullable=False)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    provider: Mapped["Provider"] = relationship(back_populates="health_records")

    __table_args__ = (
        Index("ix_provider_health_provider_id", "provider_id"),
        Index("ix_provider_health_checked_at", "checked_at"),
        Index("ix_provider_health_is_healthy", "is_healthy"),
    )


# ── audit_logs ────────────────────────────────────────────────────────────────


class AuditLog(Base):
    __tablename__ = "audit_logs"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction), nullable=False)
    resource_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    changes: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error_detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped[Optional["User"]] = relationship(back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_logs_user_id", "user_id"),
        Index("ix_audit_logs_organization_id", "organization_id"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_created_at", "created_at"),
        Index("ix_audit_logs_resource_type", "resource_type"),
    )


# ── evaluation_records ────────────────────────────────────────────────────────


class EvaluationRecord(Base):
    __tablename__ = "evaluation_records"

    model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(100), nullable=False)
    total_prompts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passed_prompts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    overall_quality_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    category_scores: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    avg_latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    item_details: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_evaluation_records_model_id", "model_id"),
        Index("ix_evaluation_records_created_at", "created_at"),
    )

