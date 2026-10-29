from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from .pep import PepAction
from .tiers import Tier


class AuditEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tenant_id: UUID
    user_id: UUID
    action: PepAction
    resource_id: str
    decision: str
    tier: Tier
    reason: str