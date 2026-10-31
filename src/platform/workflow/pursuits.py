"""Persist manual pursuit state and outcome retries in one transaction."""
from datetime import timezone

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from src.platform.database.models import Proposal, new_id, utcnow
from src.platform.database.pursuits import Opportunity, Outcome, Pursuit, PursuitHistory
from .errors import WorkflowError

TERMINAL_STATES = ('won', 'lost', 'withdrawn')


def iso(value):
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def opportunity_view(opportunity: Opportunity) -> dict:
    return {key: getattr(opportunity, key) for key in (
        'id', 'team_id', 'title', 'source_url', 'deadline_timezone', 'notes', 'eligibility')} | {
            'deadline': iso(opportunity.deadline), 'created_at': iso(opportunity.created_at)}


def pursuit_view(session: Session, pursuit: Pursuit | None) -> dict | None:
    if pursuit is None:
        return None
    history = session.scalars(select(PursuitHistory).where(PursuitHistory.pursuit_id == pursuit.id)
                              .order_by(PursuitHistory.recorded_at, PursuitHistory.id)).all()
    return {key: getattr(pursuit, key) for key in ('id', 'proposal_id', 'opportunity_id', 'state')} | {
        'updated_at': iso(pursuit.updated_at), 'history': [
            {key: getattr(row, key) for key in ('id', 'from_state', 'to_state', 'user_id')} | {
                'recorded_at': iso(row.recorded_at)} for row in history]}


def outcome_view(outcome: Outcome) -> dict:
    return {key: getattr(outcome, key) for key in ('id', 'pursuit_id', 'outcome', 'award_reference')} | {
        'recorded_at': iso(outcome.recorded_at)}


def get_pursuit(session: Session, proposal_id: str) -> Pursuit | None:
    return session.scalar(select(Pursuit).where(Pursuit.proposal_id == proposal_id))


def _lock_proposal(session: Session, proposal_id: str):
    # PostgreSQL serializes every pursuit mutation for a proposal, including its
    # first creation. Explicit SQLite tests use their database's writer lock.
    if session.get_bind().dialect.name == 'sqlite':
        session.execute(text('BEGIN IMMEDIATE'))
    else:
        session.execute(select(Proposal.id).where(Proposal.id == proposal_id).with_for_update()).scalar_one()


def set_pursuit(session: Session, proposal: Proposal, user_id: str, state: str, opportunity_id: str | None) -> Pursuit:
    _lock_proposal(session, proposal.id)
    if opportunity_id is not None:
        opportunity = session.get(Opportunity, opportunity_id)
        if opportunity is None or opportunity.team_id != proposal.team_id:
            raise WorkflowError(400, 'invalid_opportunity', 'Choose an opportunity belonging to the proposal team')
    pursuit = get_pursuit(session, proposal.id)
    if pursuit is not None and pursuit.state in TERMINAL_STATES:
        raise WorkflowError(409, 'pursuit_terminal', 'A recorded outcome cannot be changed through pursuit state')
    previous = pursuit.state if pursuit else None
    if pursuit is None:
        pursuit = Pursuit(proposal_id=proposal.id, opportunity_id=opportunity_id, state=state)
        session.add(pursuit)
        session.flush()
    else:
        pursuit.state = state
        pursuit.opportunity_id = opportunity_id
        pursuit.updated_at = utcnow()
    if previous != state:
        session.add(PursuitHistory(pursuit_id=pursuit.id, from_state=previous, to_state=state, user_id=user_id))
    session.commit()
    return pursuit


def _same_payload(outcome: Outcome, state: str, award_reference: str | None) -> Outcome:
    if outcome.outcome != state or outcome.award_reference != award_reference:
        raise WorkflowError(409, 'idempotency_conflict', 'This idempotency key was already used with different outcome details')
    return outcome


def record_outcome(session: Session, proposal: Proposal, user_id: str, state: str,
                   idempotency_key: str, award_reference: str | None) -> Outcome:
    _lock_proposal(session, proposal.id)
    pursuit = get_pursuit(session, proposal.id)
    if pursuit is None:
        raise WorkflowError(409, 'not_submitted', 'Record submission before recording an outcome')
    previous = session.scalar(select(Outcome).where(
        Outcome.pursuit_id == pursuit.id, Outcome.idempotency_key == idempotency_key))
    if previous is not None:
        result = _same_payload(previous, state, award_reference)
        session.commit()
        return result
    if pursuit.state != 'submitted':
        raise WorkflowError(409, 'not_submitted', 'Only a submitted pursuit can receive an outcome')
    insert = postgres_insert if session.get_bind().dialect.name == 'postgresql' else sqlite_insert
    result = session.execute(insert(Outcome).values(
        id=new_id(), pursuit_id=pursuit.id, outcome=state, idempotency_key=idempotency_key,
        award_reference=award_reference, recorded_at=utcnow())
        .on_conflict_do_nothing(index_elements=['pursuit_id', 'idempotency_key']).returning(Outcome.id)).scalar_one_or_none()
    stored = session.scalar(select(Outcome).where(
        Outcome.pursuit_id == pursuit.id, Outcome.idempotency_key == idempotency_key))
    if result is None:
        stored = _same_payload(stored, state, award_reference)
        session.commit()
        return stored
    pursuit.state = state
    pursuit.updated_at = utcnow()
    session.add(PursuitHistory(pursuit_id=pursuit.id, from_state='submitted', to_state=state, user_id=user_id))
    session.commit()
    return stored
