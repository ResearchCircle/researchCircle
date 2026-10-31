from datetime import timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from src.platform.database.models import Membership, Proposal, ProposalSource, Source, User, utcnow
from .errors import WorkflowError


def source_view(source: Source) -> dict:
    return {key: getattr(source, key) for key in (
        'id', 'version', 'content_hash', 'title', 'origin', 'text', 'proposal_id', 'is_public')}


def proposal_view(session: Session, user: User, proposal: Proposal) -> dict:
    selected_ids = proposal.selected_source_ids
    sources = {source.id: source for source in session.scalars(select(Source).join(
        ProposalSource, Source.id == ProposalSource.source_id).where(
            ProposalSource.proposal_id == proposal.id, Source.id.in_(selected_ids)))} if selected_ids else {}
    updated = proposal.updated_at
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)
    return {'id': proposal.id, 'team_id': proposal.team_id, 'title': proposal.title,
            'content': proposal.content, 'revision': proposal.revision,
            'role': session.get(Membership, (proposal.team_id, user.id)).role,
            'selected_sources': [{key: getattr(sources[source_id], key) for key in ('id', 'version', 'content_hash')}
                                 for source_id in selected_ids if source_id in sources],
            'updated_at': updated.isoformat()}


def save_proposal(session: Session, proposal: Proposal, expected_revision: int, changes: dict) -> Proposal:
    selected = changes.get('selected_source_ids')
    if selected is not None:
        if len(set(selected)) != len(selected):
            raise WorkflowError(400, 'invalid_sources', 'Selected sources must be unique')
        linked = set(session.scalars(select(ProposalSource.source_id).where(
            ProposalSource.proposal_id == proposal.id, ProposalSource.source_id.in_(selected))))
        if linked != set(selected):
            raise WorkflowError(400, 'source_not_attached', 'Select only sources already attached to this proposal')
    result = session.execute(update(Proposal).where(
        Proposal.id == proposal.id, Proposal.revision == expected_revision).values(
            **changes, revision=expected_revision + 1, updated_at=utcnow()).execution_options(synchronize_session=False))
    if result.rowcount != 1:
        session.rollback()
        raise WorkflowError(409, 'revision_conflict', 'The proposal changed; reload before saving')
    session.commit()
    session.refresh(proposal)
    return proposal


def markdown_export(session: Session, proposal: Proposal) -> str:
    sources = session.scalars(select(Source).join(ProposalSource, Source.id == ProposalSource.source_id).where(
        ProposalSource.proposal_id == proposal.id, Source.id.in_(proposal.selected_source_ids))).all()
    result = f'# {proposal.title}\n\n{proposal.content}\n'
    if sources:
        result += '\n## Sources\n\n'
        for source in sources:
            result += f'- [{source.id}] {source.title} — {source.origin} (version {source.version}, SHA-256 {source.content_hash})\n'
    return result
