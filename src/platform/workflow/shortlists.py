"""Explicit saved selections; discovery ranking never changes team membership."""
from datetime import timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from src.platform.database.models import Source, new_id, utcnow
from src.platform.database.public_records import PublicRecord
from src.platform.database.shortlists import TeamShortlistEntry
from .errors import WorkflowError


def public_source(session: Session, source_id: str):
    row = session.execute(select(Source, PublicRecord).join(PublicRecord, PublicRecord.source_id == Source.id).where(
        Source.id == source_id, Source.is_public.is_(True), Source.proposal_id.is_(None))).one_or_none()
    if row is None:
        raise WorkflowError(404, 'source_not_found', 'Resolved public source was not found')
    return row


def entry_view(entry: TeamShortlistEntry, source: Source, record: PublicRecord) -> dict:
    created = entry.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return {'id': entry.id, 'team_id': entry.team_id, 'source_id': source.id, 'version': source.version,
            'content_hash': source.content_hash, 'title': source.title, 'snippet': source.text[:280],
            'origin': source.origin, 'kind': record.kind, 'evidence_kind': record.evidence_kind,
            'note': entry.note, 'created_at': created.astimezone(timezone.utc).isoformat(), 'created_by': entry.created_by,
            **({'identity_status': record.metadata_json['identity_status']}
               if record.metadata_json.get('identity_status') else {})}


def list_entries(session: Session, team_id: str) -> list[dict]:
    rows = session.execute(select(TeamShortlistEntry, Source, PublicRecord)
        .join(Source, TeamShortlistEntry.source_id == Source.id)
        .join(PublicRecord, PublicRecord.source_id == Source.id).where(
            TeamShortlistEntry.team_id == team_id, Source.is_public.is_(True), Source.proposal_id.is_(None))
        .order_by(TeamShortlistEntry.created_at, TeamShortlistEntry.id)).all()
    return [entry_view(entry, source, record) for entry, source, record in rows]


def add_entry(session: Session, team_id: str, source_id: str, user_id: str, note: str) -> dict:
    source, record = public_source(session, source_id)
    insert = postgres_insert if session.get_bind().dialect.name == 'postgresql' else sqlite_insert
    session.execute(insert(TeamShortlistEntry).values(
        id=new_id(), team_id=team_id, source_id=source_id, created_by=user_id, note=note, created_at=utcnow())
        .on_conflict_do_nothing(index_elements=['team_id', 'source_id']))
    entry = session.scalar(select(TeamShortlistEntry).where(
        TeamShortlistEntry.team_id == team_id, TeamShortlistEntry.source_id == source_id))
    result = entry_view(entry, source, record)
    session.commit()
    return result


def require_entry(session: Session, team_id: str, entry_id: str) -> TeamShortlistEntry:
    entry = session.scalar(select(TeamShortlistEntry).where(
        TeamShortlistEntry.id == entry_id, TeamShortlistEntry.team_id == team_id))
    if entry is None:
        raise WorkflowError(404, 'shortlist_entry_not_found', 'Team shortlist entry was not found')
    return entry
