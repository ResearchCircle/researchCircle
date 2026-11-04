from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from services.api.dependencies import get_session
from src.platform.discovery.graph import get_public_graph

router = APIRouter(prefix='/api/v2')


@router.get('/graph')
def read_public_graph(
    limit: int = Query(default=150, ge=1, le=500),
    topic: str | None = Query(default=None, max_length=200),
    center_id: str | None = Query(default=None, max_length=200),
    hops: int = Query(default=2, ge=1, le=3),
    session: Session = Depends(get_session)
) -> dict[str, Any]:
    """Read public researcher, paper, and topic relationships for visualization.

    Supports ego-network querying (`center_id`, `hops`), precomputed layout
    coordinates, and community clustering.
    Guarantees private proposal-scoped sources are strictly excluded.
    """
    return get_public_graph(
        session,
        limit=limit,
        topic_filter=topic,
        center_id=center_id,
        hops=hops
    )
