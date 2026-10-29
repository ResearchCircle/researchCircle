from uuid import UUID

import pytest
from pydantic import ValidationError

from tigerexchange_contracts import (
    Capability,
    ClassificationResult,
    Decision,
    DiscoverabilityScope,
    Edition,
    Entitlement,
    PepAction,
    PepRequest,
    PepResponse,
    PublishableProjection,
    Tier,
    tier_join,
    tier_join_all,
)


def test_empty_join_is_confidential() -> None:
    assert tier_join_all([]) == Tier.CONFIDENTIAL


def test_max_rule_uses_most_restrictive_tier() -> None:
    assert tier_join(Tier.PUBLIC, Tier.CONFIDENTIAL) == Tier.CONFIDENTIAL
    assert tier_join_all([Tier.PUBLIC, Tier.PRIVATE, Tier.PUBLIC]) == Tier.PRIVATE


def test_entitlement_permits_confidential_only_with_confidential_capability() -> None:
    entitlement = Entitlement(
        edition=Edition.DISCOVERY_ONLY,
        capabilities=frozenset({Capability.PUBLIC_RETRIEVAL}),
    )
    assert entitlement.permits_tier(Tier.CONFIDENTIAL) is False


def test_publishable_projection_rejects_confidential() -> None:
    with pytest.raises(ValidationError):
        PublishableProjection(
            projection_id="p1",
            tenant_id=UUID(int=1),
            tier=Tier.CONFIDENTIAL,
            discoverability_scope=DiscoverabilityScope.PUBLIC,
            title="Draft",
            summary="Secret",
        )


def test_classification_result_retrievable_only_for_public_allow() -> None:
    assert ClassificationResult(decision=Decision.ALLOW, tier=Tier.PUBLIC).is_retrievable is True
    assert ClassificationResult(decision=Decision.ALLOW, tier=Tier.PRIVATE).is_retrievable is False


def test_pep_types_are_frozen_value_objects() -> None:
    request = PepRequest(
        tenant_context={
            "tenant_id": UUID(int=2),
            "user_id": UUID(int=3),
            "entitlement": {"edition": Edition.DISCOVERY_ONLY, "capabilities": []},
            "capabilities": [],
        },
        action=PepAction.RETRIEVE_PUBLIC,
        resource_id="resource-1",
    )

    with pytest.raises(ValidationError):
        request.resource_id = "changed"  # type: ignore[misc]

    response = PepResponse(authorized=True, reason="ok")
    with pytest.raises(ValidationError):
        response.reason = "changed"  # type: ignore[misc]