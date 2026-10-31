from datetime import timezone
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, HttpUrl, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from services.api.dependencies import current_user, get_session, require_proposal, team_role
from src.platform.database.models import Membership, User
from src.platform.database.pursuits import Opportunity, Outcome
from src.platform.workflow.pursuits import get_pursuit, opportunity_view, outcome_view, pursuit_view, record_outcome, set_pursuit

router = APIRouter(prefix='/api/v2')


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid')


class OpportunityInput(Input):
    team_id: UUID
    title: str = Field(min_length=1, max_length=300)
    source_url: HttpUrl | None = None
    deadline: AwareDatetime | None = None
    deadline_timezone: str | None = Field(default=None, max_length=100)
    notes: str = Field(default='', max_length=10000)
    eligibility: Literal['unknown', 'eligible', 'ineligible'] = 'unknown'

    @field_validator('title')
    @classmethod
    def nonblank_title(cls, value):
        if not value.strip():
            raise ValueError('Title is required')
        return value.strip()

    @field_validator('deadline_timezone')
    @classmethod
    def known_timezone(cls, value):
        if value is not None:
            try:
                ZoneInfo(value)
            except (ZoneInfoNotFoundError, ValueError):
                raise ValueError('Use an IANA timezone name') from None
        return value


class PursuitInput(Input):
    state: Literal['draft', 'shortlisted', 'collaborating', 'submitted']
    opportunity_id: UUID | None


class OutcomeInput(Input):
    outcome: Literal['won', 'lost', 'withdrawn']
    idempotency_key: str = Field(min_length=1, max_length=200)
    award_reference: str | None = Field(default=None, max_length=1000)

    @field_validator('idempotency_key')
    @classmethod
    def nonblank_key(cls, value):
        if not value.strip():
            raise ValueError('Idempotency key is required')
        return value


@router.get('/opportunities')
def list_opportunities(session: Session = Depends(get_session), user: User = Depends(current_user)):
    rows = session.scalars(select(Opportunity).join(Membership, Opportunity.team_id == Membership.team_id)
                           .where(Membership.user_id == user.id).order_by(Opportunity.created_at, Opportunity.id)).all()
    return {'items': [opportunity_view(row) for row in rows]}


@router.post('/opportunities', status_code=201)
def create_opportunity(body: OpportunityInput, session: Session = Depends(get_session), user: User = Depends(current_user)):
    team_role(session, user, str(body.team_id), edit=True)
    opportunity = Opportunity(team_id=str(body.team_id), title=body.title,
        source_url=str(body.source_url) if body.source_url is not None else None,
        deadline=body.deadline.astimezone(timezone.utc) if body.deadline is not None else None,
        deadline_timezone=body.deadline_timezone, notes=body.notes, eligibility=body.eligibility)
    session.add(opportunity)
    session.commit()
    return opportunity_view(opportunity)


@router.get('/proposals/{proposal_id}/pursuit')
def read_pursuit(proposal_id: UUID, session: Session = Depends(get_session), user: User = Depends(current_user)):
    proposal = require_proposal(session, user, str(proposal_id))
    return {'pursuit': pursuit_view(session, get_pursuit(session, proposal.id))}


@router.put('/proposals/{proposal_id}/pursuit')
def update_pursuit(proposal_id: UUID, body: PursuitInput, session: Session = Depends(get_session), user: User = Depends(current_user)):
    proposal = require_proposal(session, user, str(proposal_id), edit=True)
    pursuit = set_pursuit(session, proposal, user.id, body.state, str(body.opportunity_id) if body.opportunity_id else None)
    return {'pursuit': pursuit_view(session, pursuit)}


@router.get('/proposals/{proposal_id}/outcomes')
def list_outcomes(proposal_id: UUID, session: Session = Depends(get_session), user: User = Depends(current_user)):
    proposal = require_proposal(session, user, str(proposal_id))
    pursuit = get_pursuit(session, proposal.id)
    rows = session.scalars(select(Outcome).where(Outcome.pursuit_id == pursuit.id)
                           .order_by(Outcome.recorded_at, Outcome.id)).all() if pursuit else []
    return {'items': [outcome_view(row) for row in rows]}


@router.post('/proposals/{proposal_id}/outcomes', status_code=201)
def create_outcome(proposal_id: UUID, body: OutcomeInput, session: Session = Depends(get_session), user: User = Depends(current_user)):
    proposal = require_proposal(session, user, str(proposal_id), edit=True)
    outcome = record_outcome(session, proposal, user.id, body.outcome, body.idempotency_key, body.award_reference)
    return outcome_view(outcome)
