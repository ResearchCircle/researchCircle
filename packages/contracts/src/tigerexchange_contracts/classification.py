from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from .tiers import Tier


class Decision(StrEnum):
    ALLOW = "allow"
    QUARANTINE = "quarantine"
    ABSTAIN = "abstain"


class ClassificationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    decision: Decision
    tier: Tier

    @property
    def is_retrievable(self) -> bool:
        return self.decision == Decision.ALLOW and self.tier == Tier.PUBLIC