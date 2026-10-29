from __future__ import annotations

from typing import FrozenSet
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .capabilities import Capability, Entitlement


class TenantContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    tenant_id: UUID
    user_id: UUID
    entitlement: Entitlement
    capabilities: FrozenSet[Capability] = Field(default_factory=frozenset)