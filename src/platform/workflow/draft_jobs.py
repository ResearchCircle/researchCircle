"""Durable queue and immutable drafting snapshots for the application worker."""

from dataclasses import asdict
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, JSON, String, func, select, text, update
from sqlalchemy.orm import Mapped, mapped_column

from src.platform.database import Database
from src.platform.database.models import Base, new_id, utcnow
from src.platform.drafting.jobs import GenerationJob, JobError, JobFailure
from src.platform.drafting.types import Citation, DraftRequest, DraftResult, SourceRef, SourceSnapshot
from src.platform.models.provider import TokenUsage


class DraftJobRecord(Base):
    __tablename__ = 'draft_jobs'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey('proposals.id'), index=True)
    state: Mapped[str] = mapped_column(String(20), index=True, default='queued')
    request_json: Mapped[dict] = mapped_column(JSON)
    sources_json: Mapped[list] = mapped_column(JSON)
    output_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


def _iso(value):
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc).isoformat() if value.tzinfo is None else value.isoformat()


def _request(value: dict) -> DraftRequest:
    return DraftRequest(value['proposal_id'], value['base_revision'], value['section'], value['instruction'],
                        tuple(SourceRef(**ref) for ref in value['source_refs']))


def _output(value: dict | None) -> DraftResult | None:
    if value is None:
        return None
    return DraftResult(value['text'], tuple(Citation(**citation) for citation in value['citations']),
                       value['base_revision'], tuple(SourceRef(**ref) for ref in value['source_refs']),
                       value['model_id'], TokenUsage(**value['usage']) if value['usage'] else None,
                       value['input_tokens'], value['finish_reason'], value['insufficient_evidence'])


def _job(record: DraftJobRecord) -> GenerationJob:
    return GenerationJob(record.id, record.user_id, _request(record.request_json),
                         tuple(SourceSnapshot(**source) for source in record.sources_json), record.state,
                         _iso(record.created_at), _iso(record.started_at), _iso(record.finished_at),
                         _output(record.output_json), JobFailure(**record.error_json) if record.error_json else None)


def job_view(job: GenerationJob) -> dict:
    """Member-visible metadata; captured full source text stays inside the worker."""
    return {'id': job.id, 'proposal_id': job.request.proposal_id, 'base_revision': job.request.base_revision,
            'source_refs': [asdict(ref) for ref in job.request.source_refs], 'state': job.state,
            'output': asdict(job.output) if job.output else None, 'error': asdict(job.error) if job.error else None,
            'created_at': job.created_at, 'started_at': job.started_at, 'finished_at': job.finished_at}


class PersistedJobStore:
    def __init__(self, database: Database):
        self.db = database

    def _admission_lock(self, session):
        # One transaction lock covers count/check/insert across every API process.
        if self.db.engine.dialect.name == 'postgresql':
            session.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': 871267310})
        elif self.db.engine.dialect.name == 'sqlite':
            session.execute(text('BEGIN IMMEDIATE'))
        else:
            raise JobError('unsupported_database', 'Draft queue requires PostgreSQL.', False)

    def enqueue(self, user_id: str, request: DraftRequest, sources: tuple[SourceSnapshot, ...]) -> GenerationJob:
        with self.db.session_factory() as session:
            self._admission_lock(session)
            active = session.scalar(select(func.count()).select_from(DraftJobRecord).where(
                DraftJobRecord.user_id == user_id, DraftJobRecord.state.in_(('queued', 'running'))))
            if active:
                raise JobError('user_busy', 'You already have a queued or running draft.', True)
            queued = session.scalar(select(func.count()).select_from(DraftJobRecord).where(DraftJobRecord.state == 'queued'))
            if queued >= 4:
                raise JobError('queue_full', 'Draft queue is full; retry later.', True)
            record = DraftJobRecord(id=new_id(), user_id=user_id, proposal_id=request.proposal_id,
                                    state='queued', request_json=asdict(request), sources_json=[asdict(source) for source in sources])
            session.add(record)
            session.commit()
            return _job(record)

    def get(self, job_id: str) -> GenerationJob | None:
        with self.db.session_factory() as session:
            record = session.get(DraftJobRecord, job_id)
            return _job(record) if record else None

    def list_for_proposal(self, proposal_id: str) -> list[GenerationJob]:
        with self.db.session_factory() as session:
            records = session.scalars(select(DraftJobRecord).where(DraftJobRecord.proposal_id == proposal_id)
                                      .order_by(DraftJobRecord.created_at.desc()).limit(50))
            return [_job(record) for record in records]

    def claim_next(self) -> GenerationJob | None:
        with self.db.session_factory() as session:
            self._admission_lock(session)
            if session.scalar(select(func.count()).select_from(DraftJobRecord).where(DraftJobRecord.state == 'running')):
                return None
            record = session.scalar(select(DraftJobRecord).where(DraftJobRecord.state == 'queued')
                                    .order_by(DraftJobRecord.created_at, DraftJobRecord.id).limit(1).with_for_update())
            if record is None:
                return None
            record.state, record.started_at = 'running', utcnow()
            session.commit()
            return _job(record)

    def finish(self, job_id: str, *, output: DraftResult | None = None, error: JobFailure | None = None) -> bool:
        if (output is None) == (error is None):
            raise ValueError('Exactly one of output or error is required')
        with self.db.session_factory() as session:
            changed = session.execute(update(DraftJobRecord).where(DraftJobRecord.id == job_id, DraftJobRecord.state == 'running')
                                      .values(state='failed' if error else 'succeeded', finished_at=utcnow(),
                                              output_json=asdict(output) if output else None, error_json=asdict(error) if error else None))
            session.commit()
            return changed.rowcount == 1

    def cancel(self, job_id: str) -> bool:
        with self.db.session_factory() as session:
            changed = session.execute(update(DraftJobRecord).where(DraftJobRecord.id == job_id, DraftJobRecord.state.in_(('queued', 'running')))
                                      .values(state='failed', finished_at=utcnow(), output_json=None,
                                              error_json=asdict(JobFailure('cancelled', 'Draft cancelled; inference may still be draining.', True))))
            session.commit()
            return changed.rowcount == 1

    def interrupt_running(self) -> int:
        with self.db.session_factory() as session:
            changed = session.execute(update(DraftJobRecord).where(DraftJobRecord.state == 'running')
                                      .values(state='failed', finished_at=utcnow(), output_json=None,
                                              error_json=asdict(JobFailure('interrupted', 'Worker stopped; retry this draft.', True))))
            session.commit()
            return changed.rowcount
