from __future__ import annotations

from typing import Any, Mapping, Sequence
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from .tiers import Tier


class RelationTuple(BaseModel):
    model_config = ConfigDict(frozen=True)

    object_id: str
    relation: str
    subject_id: str


class RetrievedItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    item_id: str
    content: str
    tier: Tier
    score: float = 0.0
    metadata: Mapping[str, Any] = Field(default_factory=dict)


class GenerationRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    request_id: UUID = Field(default_factory=uuid4)
    prompt: str
    tenant_id: UUID
    context_items: Sequence[RetrievedItem] = Field(default_factory=tuple)


class GenerationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    request_id: UUID
    output: str
    tier: Tier


class KeyRef(BaseModel):
    model_config = ConfigDict(frozen=True)

    tenant_id: UUID
    key_id: str
    purpose: str