from __future__ import annotations

from enum import StrEnum
from typing import FrozenSet
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .tiers import Tier


class DiscoverabilityScope(StrEnum):
    PUBLIC = "public"
    TENANT = "tenant"
    WORKSPACE = "workspace"
    CONSORTIUM = "consortium"


class PublishableProjection(BaseModel):
    model_config = ConfigDict(frozen=True)

    projection_id: str
    tenant_id: UUID
    tier: Tier
    discoverability_scope: DiscoverabilityScope = DiscoverabilityScope.PUBLIC
    title: str
    summary: str
    tags: FrozenSet[str] = Field(default_factory=frozenset)

    @model_validator(mode="after")
    def _reject_confidential(self) -> "PublishableProjection":
        if self.tier != Tier.PUBLIC:
            raise ValueError("publishable projections must be public-tier")
        return self