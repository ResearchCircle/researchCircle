from fastapi import APIRouter, Query
from sqlalchemy.orm import Session

from src.platform.database.models import Source
from src.platform.discovery.search import list_samples, search
from src.platform.workflow.errors import WorkflowError

router = APIRouter(prefix='/api/v2')


def seed_samples(session: Session) -> int:
    inserted = 0
    for row in list_samples():
        previous = session.get(Source, row['source_id'])
        if previous is not None:
            if not previous.is_public or previous.proposal_id is not None or previous.content_hash != row['content_hash']:
                raise WorkflowError(409, 'sample_conflict', 'A sample source conflicts with an existing record')
            continue
        session.add(Source(id=row['source_id'], version=row['version'], content_hash=row['content_hash'],
                           title=row['title'], origin=row['origin'], text=row['text'], is_public=True, proposal_id=None))
        inserted += 1
    return inserted


@router.get('/search')
def search_catalog(q: str = Query(default='', max_length=1000), limit: int = Query(default=10, ge=1, le=100)):
    return search(q, limit)
