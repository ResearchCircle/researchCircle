from __future__ import annotations

from enum import StrEnum
from typing import FrozenSet

from pydantic import BaseModel, ConfigDict, Field

from .tiers import Tier


class Capability(StrEnum):
    OWN_MATERIALS = "own_materials"
    PUBLIC_RETRIEVAL = "public_retrieval"
    CONFIDENTIAL_RETRIEVAL = "confidential_retrieval"
    CROSS_GROUP_SHARE = "cross_group_share"
    CONFIDENTIAL_DRAFTING = "confidential_drafting"


class Edition(StrEnum):
    DISCOVERY_ONLY = "discovery_only"
    COLLABORATION = "collaboration"


class Entitlement(BaseModel):
    model_config = ConfigDict(frozen=True)

    edition: Edition
    capabilities: FrozenSet[Capability] = Field(default_factory=frozenset)

    def has(self, capability: Capability) -> bool:
        return capability in self.capabilities

    def permits_tier(self, tier: Tier) -> bool:
        if tier == Tier.PUBLIC:
            return self.has(Capability.PUBLIC_RETRIEVAL) or self.has(Capability.OWN_MATERIALS)
        if tier == Tier.PRIVATE:
            return self.has(Capability.OWN_MATERIALS)
        if tier == Tier.CONFIDENTIAL:
            return self.has(Capability.CONFIDENTIAL_RETRIEVAL) or self.has(
                Capability.CONFIDENTIAL_DRAFTING
            )
        return False