"""
Budget policy schemas.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import Field

from app.database.models import BudgetPeriod
from app.schemas.common import ORMBase


class BudgetPolicyCreateRequest(ORMBase):
    name: str = Field(..., min_length=1, max_length=255)
    period: BudgetPeriod = BudgetPeriod.MONTHLY
    limit_usd: Decimal = Field(..., gt=0, decimal_places=4)
    alert_threshold_pct: int = Field(80, ge=1, le=100)
    hard_limit: bool = True


class BudgetPolicyUpdateRequest(ORMBase):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    period: Optional[BudgetPeriod] = None
    limit_usd: Optional[Decimal] = Field(None, gt=0, decimal_places=4)
    alert_threshold_pct: Optional[int] = Field(None, ge=1, le=100)
    hard_limit: Optional[bool] = None
    is_active: Optional[bool] = None


class BudgetPolicyResponse(ORMBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    period: BudgetPeriod
    limit_usd: Decimal
    current_spend_usd: Decimal
    alert_threshold_pct: int
    hard_limit: bool
    reset_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
