from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from .tenant import TenantContext


class PepAction(StrEnum):
    RETRIEVE_PUBLIC = "retrieve_public"
    RETRIEVE_CONFIDENTIAL = "retrieve_confidential"
    DERIVE_PUBLIC = "derive_public"
    DERIVE_CONFIDENTIAL = "derive_confidential"
    EGRESS_PUBLIC = "egress_public"
    EGRESS_CONFIDENTIAL = "egress_confidential"


class PepEffect(StrEnum):
    ALLOW = "allow"
    DENY = "deny"


class PepRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    tenant_context: TenantContext
    action: PepAction
    resource_id: str


class PepResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    authorized: bool
    reason: str