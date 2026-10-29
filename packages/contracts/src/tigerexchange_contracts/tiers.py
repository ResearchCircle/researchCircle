from __future__ import annotations

from enum import IntEnum
from typing import Iterable


class Tier(IntEnum):
    PUBLIC = 0
    PRIVATE = 1
    CONFIDENTIAL = 2

    def to_label(self) -> str:
        return self.name.lower()

    @classmethod
    def from_label(cls, label: str) -> "Tier":
        return cls[label.strip().upper()]


MOST_RESTRICTIVE_TIER: Tier = Tier.CONFIDENTIAL


def tier_join(a: Tier, b: Tier) -> Tier:
    return a if a >= b else b


def tier_join_all(tiers: Iterable[Tier]) -> Tier:
    result = Tier.PUBLIC
    seen = False
    for tier in tiers:
        seen = True
        result = tier_join(result, tier)
    return result if seen else MOST_RESTRICTIVE_TIER