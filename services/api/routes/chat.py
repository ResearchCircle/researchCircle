"""Evidence-grounded research chat endpoint."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from services.api.dependencies import current_user, get_session, require_proposal
from src.platform.database.models import ProposalSource, Source, User
from src.platform.database.public_records import PublicRecord
from src.platform.discovery.public_search import search_public
from src.platform.drafting.types import SourceSnapshot
from src.platform.workflow.errors import WorkflowError

router = APIRouter(prefix='/api/v2')


class ChatMessageInput(BaseModel):
    role: str = Field(pattern=r'^(user|assistant)$')
    content: str = Field(min_length=1, max_length=4000)


class ChatRequestInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    message: str = Field(min_length=1, max_length=2000)
    history: list[ChatMessageInput] = Field(default_factory=list, max_length=20)
    proposal_id: UUID | None = None


@router.post('/chat')
def research_chat(
    body: ChatRequestInput,
    request: Request,
    session: Session = Depends(get_session),
    user: User = Depends(current_user)
):
    if not body.message.strip():
        raise WorkflowError(422, 'invalid_message', 'Message cannot be empty')

    snapshots: list[SourceSnapshot] = []

    if body.proposal_id is not None:
        # Enforce tenancy: named user must belong to proposal team
        proposal = require_proposal(session, user, str(body.proposal_id))
        stmt = (
            select(Source)
            .join(ProposalSource, ProposalSource.source_id == Source.id)
            .where(ProposalSource.proposal_id == proposal.id)
        )
        sources = session.scalars(stmt).all()
        for s in sources:
            snapshots.append(SourceSnapshot(
                id=s.id,
                version=s.version,
                content_hash=s.content_hash,
                title=s.title,
                origin=s.origin,
                text=s.text,
                proposal_id=s.proposal_id,
                is_public=s.is_public
            ))

        # If proposal currently has no attached evidence, supplement with public literature so questions get answered
        if not snapshots:
            search_res = search_public(session, body.message, limit=5, semantic=True)
            for item in search_res.get('items', []):
                snapshots.append(SourceSnapshot(
                    id=item['id'],
                    version=item['version'],
                    content_hash=item['content_hash'],
                    title=item['title'],
                    origin=item['origin'],
                    text=item['text'],
                    proposal_id=None,
                    is_public=True
                ))
    else:
        # Use approved public records via hybrid semantic search
        search_res = search_public(session, body.message, limit=5, semantic=True)
        for item in search_res.get('items', []):
            snapshots.append(SourceSnapshot(
                id=item['id'],
                version=item['version'],
                content_hash=item['content_hash'],
                title=item['title'],
                origin=item['origin'],
                text=item['text'],
                proposal_id=None,
                is_public=True
            ))

    chat_service = getattr(request.app.state, 'chat_service', None)
    if chat_service is None:
        raise WorkflowError(503, 'chat_unavailable', 'Research chat service is not initialized', retryable=True)

    result = chat_service.answer(
        body.message,
        [m.model_dump() for m in body.history],
        snapshots
    )

    citation_source_ids = {c.source_id for c in result.citations}
    pdf_source_ids: set[str] = set()
    if citation_source_ids:
        records = session.scalars(
            select(PublicRecord).where(PublicRecord.source_id.in_(citation_source_ids))
        ).all()
        for rec in records:
            meta = rec.metadata_json if isinstance(rec.metadata_json, dict) else {}
            if meta.get('pdf_file'):
                pdf_source_ids.add(rec.source_id)

    return {
        'response': result.response,
        'citations': [
            {
                'source_id': c.source_id,
                'version': c.version,
                'content_hash': c.content_hash,
                'title': c.title,
                'origin': c.origin,
                'quote': c.quote,
                'has_pdf': c.source_id in pdf_source_ids,
            }
            for c in result.citations
        ],
        'insufficient_evidence': result.insufficient_evidence,
        'sources_consulted': list(result.sources_consulted)
    }
