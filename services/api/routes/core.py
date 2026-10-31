import hashlib
import os
import unicodedata
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from services.api.dependencies import SESSION_COOKIE, current_user, get_session, require_proposal, team_role
from src.platform.database.models import Invitation, LoginSession, Membership, Proposal, ProposalSource, Source, Team, User, utcnow
from src.platform.workflow.accounts import authenticate, create_session, password_hasher
from src.platform.workflow.errors import WorkflowError
from src.platform.workflow.memberships import change_member, lock_team
from src.platform.workflow.proposals import markdown_export, proposal_view, save_proposal, source_view

router = APIRouter(prefix='/api/v2')


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Credentials(Input):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=1024)

    @field_validator('email')
    @classmethod
    def normalize_email(cls, value):
        value = value.strip().lower()
        if value.count('@') != 1 or not all(value.split('@')) or any(char.isspace() for char in value):
            raise ValueError('Enter a valid email')
        return value


class Register(Credentials):
    name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=12, max_length=1024)

    @field_validator('name')
    @classmethod
    def nonblank_name(cls, value):
        if not value.strip():
            raise ValueError('Name is required')
        return value.strip()


class TeamInput(Input):
    name: str = Field(min_length=1, max_length=200)

    @field_validator('name')
    @classmethod
    def nonblank_name(cls, value):
        if not value.strip():
            raise ValueError('Team name is required')
        return value.strip()


class MemberRoleInput(Input):
    role: Literal['owner', 'editor', 'viewer']


class InviteInput(Input):
    email: str = Field(min_length=3, max_length=320)
    role: Literal['editor', 'viewer']


class ProposalInput(Input):
    team_id: UUID
    title: str = Field(min_length=1, max_length=300)
    content: str = Field(default='', max_length=1_000_000)


class SaveInput(Input):
    expected_revision: int = Field(ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=300)
    content: str | None = Field(default=None, max_length=1_000_000)
    selected_source_ids: list[UUID] | None = Field(default=None, max_length=100)


class SourceInput(Input):
    title: str = Field(min_length=1, max_length=500)
    text: str = Field(min_length=1, max_length=1_000_000)
    origin: str = Field(min_length=1, max_length=2000)


class AttachInput(Input):
    source_id: UUID


def user_view(user):
    return {'user': {key: getattr(user, key) for key in ('id', 'email', 'name')}}


def session_cookie(response: Response, request: Request, token: str):
    secure = request.url.scheme == 'https' or os.environ.get('TBR_COOKIE_SECURE', '').lower() == 'true'
    response.set_cookie(SESSION_COOKIE, token, httponly=True, secure=secure, samesite='lax', max_age=7 * 86400, path='/')


@router.post('/auth/register', status_code=201)
def register(body: Register, request: Request, response: Response, session: Session = Depends(get_session)):
    user = User(email=body.email, name=body.name, password_hash=password_hasher.hash(body.password))
    session.add(user)
    try:
        session.flush()
        token = create_session(session, user)
        session.commit()
    except IntegrityError:
        session.rollback()
        raise WorkflowError(409, 'email_exists', 'An account with this email already exists') from None
    session_cookie(response, request, token)
    return user_view(user)


@router.post('/auth/login')
def login(body: Credentials, request: Request, response: Response, session: Session = Depends(get_session)):
    user = authenticate(session, body.email, body.password)
    # Rotate the current browser session at authentication.
    previous = request.cookies.get(SESSION_COOKIE)
    if previous:
        previous_row = session.scalar(select(LoginSession).where(LoginSession.token_hash == hashlib.sha256(previous.encode()).hexdigest()))
        if previous_row:
            session.delete(previous_row)
    token = create_session(session, user)
    session.commit()
    session_cookie(response, request, token)
    return user_view(user)


@router.get('/auth/me')
def me(user: User = Depends(current_user)):
    return user_view(user)


@router.post('/auth/logout', status_code=204)
def logout(request: Request, response: Response, session: Session = Depends(get_session)):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        row = session.scalar(select(LoginSession).where(LoginSession.token_hash == hashlib.sha256(token.encode()).hexdigest()))
        if row:
            session.delete(row)
            session.commit()
    response.delete_cookie(SESSION_COOKIE, path='/')


@router.get('/teams')
def teams(session: Session = Depends(get_session), user: User = Depends(current_user)):
    rows = session.execute(select(Team, Membership.role).join(Membership).where(Membership.user_id == user.id)).all()
    return {'items': [{'id': team.id, 'name': team.name, 'role': role} for team, role in rows]}


@router.post('/teams', status_code=201)
def create_team(body: TeamInput, session: Session = Depends(get_session), user: User = Depends(current_user)):
    team = Team(name=body.name)
    session.add(team)
    session.flush()
    session.add(Membership(team_id=team.id, user_id=user.id, role='owner'))
    session.commit()
    return {'id': team.id, 'name': team.name, 'role': 'owner'}


@router.get('/teams/{team_id}')
def get_team(team_id: UUID, session: Session = Depends(get_session), user: User = Depends(current_user)):
    role = team_role(session, user, str(team_id))
    team = session.get(Team, str(team_id))
    members = session.execute(select(User, Membership.role).join(Membership).where(Membership.team_id == str(team_id))).all()
    return {'id': team.id, 'name': team.name, 'role': role, 'members': [
        {'id': member.id, 'name': member.name, 'email': member.email, 'role': member_role} for member, member_role in members]}


@router.patch('/teams/{team_id}/members/{member_id}')
def update_member(team_id: UUID, member_id: UUID, body: MemberRoleInput,
                  session: Session = Depends(get_session), user: User = Depends(current_user)):
    team_id = str(team_id)
    lock_team(session, team_id)
    team_role(session, user, team_id, owner=True)
    membership = change_member(session, team_id, str(member_id), body.role)
    member = session.get(User, str(member_id))
    session.commit()
    return {'id': member.id, 'email': member.email, 'name': member.name, 'role': membership.role}


@router.delete('/teams/{team_id}/members/{member_id}', status_code=204)
def remove_member(team_id: UUID, member_id: UUID,
                  session: Session = Depends(get_session), user: User = Depends(current_user)):
    team_id = str(team_id)
    lock_team(session, team_id)
    team_role(session, user, team_id, owner=True)
    change_member(session, team_id, str(member_id), None)
    session.commit()


@router.post('/teams/{team_id}/invitations', status_code=201)
def invite(team_id: UUID, body: InviteInput, session: Session = Depends(get_session), user: User = Depends(current_user)):
    team_id = str(team_id)
    lock_team(session, team_id)
    team_role(session, user, team_id, owner=True)
    recipient = session.scalar(select(User).where(User.email == body.email.strip().lower()))
    if recipient is None:
        raise WorkflowError(404, 'user_not_found', 'Invite an existing registered user')
    if session.get(Membership, (team_id, recipient.id)):
        raise WorkflowError(409, 'already_member', 'This user is already a team member')
    invitation = session.scalar(select(Invitation).where(Invitation.team_id == team_id, Invitation.user_id == recipient.id)
                                .with_for_update())
    if invitation is None:
        invitation = Invitation(team_id=team_id, user_id=recipient.id, invited_by=user.id, role=body.role)
        session.add(invitation)
    else:
        invitation.role = body.role
        invitation.invited_by = user.id
        invitation.accepted_at = None
        invitation.created_at = utcnow()
    session.commit()
    return {'id': invitation.id, 'team_id': team_id, 'role': invitation.role, 'email': recipient.email}


@router.get('/invitations')
def invitations(session: Session = Depends(get_session), user: User = Depends(current_user)):
    rows = session.execute(select(Invitation, Team.name).join(Team).where(
        Invitation.user_id == user.id, Invitation.accepted_at.is_(None))).all()
    return {'items': [{'id': invite.id, 'team_id': invite.team_id, 'team_name': name, 'role': invite.role} for invite, name in rows]}


@router.post('/invitations/{invitation_id}/accept')
def accept(invitation_id: UUID, session: Session = Depends(get_session), user: User = Depends(current_user)):
    team_id = session.scalar(select(Invitation.team_id).where(
        Invitation.id == str(invitation_id), Invitation.user_id == user.id))
    if team_id is None:
        raise WorkflowError(404, 'invitation_not_found', 'Invitation was not found')
    lock_team(session, team_id)
    invitation = session.scalar(select(Invitation).where(
        Invitation.id == str(invitation_id), Invitation.user_id == user.id).with_for_update()
        .execution_options(populate_existing=True))
    if invitation is None:
        raise WorkflowError(404, 'invitation_not_found', 'Invitation was not found')
    membership = session.get(Membership, (team_id, user.id))
    if invitation.accepted_at is not None:
        if membership is None:
            raise WorkflowError(409, 'invitation_already_used', 'This invitation was already accepted; ask an owner to invite you again')
    else:
        if membership is None:
            insert = postgres_insert if session.get_bind().dialect.name == 'postgresql' else sqlite_insert
            session.execute(insert(Membership).values(team_id=team_id, user_id=user.id, role=invitation.role)
                            .on_conflict_do_nothing(index_elements=['team_id', 'user_id']))
        invitation.accepted_at = utcnow()
    session.commit()
    return {'team_id': invitation.team_id}


@router.get('/proposals')
def proposals(session: Session = Depends(get_session), user: User = Depends(current_user)):
    rows = session.scalars(select(Proposal).join(Membership, Proposal.team_id == Membership.team_id).where(
        Membership.user_id == user.id).order_by(Proposal.updated_at.desc())).all()
    return {'items': [proposal_view(session, user, proposal) for proposal in rows]}


@router.post('/proposals', status_code=201)
def create_proposal(body: ProposalInput, session: Session = Depends(get_session), user: User = Depends(current_user)):
    team_role(session, user, str(body.team_id), edit=True)
    proposal = Proposal(team_id=str(body.team_id), title=body.title, content=body.content)
    session.add(proposal)
    session.commit()
    return proposal_view(session, user, proposal)


@router.get('/proposals/{proposal_id}')
def get_proposal(proposal_id: UUID, session: Session = Depends(get_session), user: User = Depends(current_user)):
    return proposal_view(session, user, require_proposal(session, user, str(proposal_id)))


@router.patch('/proposals/{proposal_id}')
def patch_proposal(proposal_id: UUID, body: SaveInput, session: Session = Depends(get_session), user: User = Depends(current_user)):
    proposal = require_proposal(session, user, str(proposal_id), edit=True)
    changes = body.model_dump(exclude_unset=True, exclude={'expected_revision'})
    if any(value is None for value in changes.values()):
        raise WorkflowError(400, 'invalid_save', 'Changed fields cannot be null')
    if 'selected_source_ids' in changes:
        changes['selected_source_ids'] = [str(source_id) for source_id in changes['selected_source_ids']]
    return proposal_view(session, user, save_proposal(session, proposal, body.expected_revision, changes))


@router.get('/proposals/{proposal_id}/sources')
def sources(proposal_id: UUID, session: Session = Depends(get_session), user: User = Depends(current_user)):
    proposal = require_proposal(session, user, str(proposal_id))
    rows = session.scalars(select(Source).join(ProposalSource).where(ProposalSource.proposal_id == proposal.id)).all()
    return {'items': [source_view(source) for source in rows]}


@router.post('/proposals/{proposal_id}/sources', status_code=201)
def create_source(proposal_id: UUID, body: SourceInput, session: Session = Depends(get_session), user: User = Depends(current_user)):
    proposal = require_proposal(session, user, str(proposal_id), edit=True)
    text = unicodedata.normalize('NFC', body.text.replace('\r\n', '\n').replace('\r', '\n'))
    source = Source(title=body.title, text=text, origin=body.origin, content_hash=hashlib.sha256(text.encode('utf-8')).hexdigest(),
                    proposal_id=proposal.id, is_public=False)
    session.add(source)
    session.flush()
    session.add(ProposalSource(proposal_id=proposal.id, source_id=source.id))
    session.commit()
    return source_view(source)


@router.post('/proposals/{proposal_id}/sources/attach', status_code=201)
def attach_source(proposal_id: UUID, body: AttachInput, session: Session = Depends(get_session), user: User = Depends(current_user)):
    proposal = require_proposal(session, user, str(proposal_id), edit=True)
    source = session.get(Source, str(body.source_id))
    if source is None or not source.is_public or source.proposal_id is not None:
        raise WorkflowError(404, 'source_not_found', 'Public source was not found')
    insert = postgres_insert if session.get_bind().dialect.name == 'postgresql' else sqlite_insert
    session.execute(insert(ProposalSource).values(proposal_id=proposal.id, source_id=source.id)
                    .on_conflict_do_nothing(index_elements=['proposal_id', 'source_id']))
    session.commit()
    return source_view(source)


@router.get('/proposals/{proposal_id}/export')
def export(proposal_id: UUID, session: Session = Depends(get_session), user: User = Depends(current_user)):
    proposal = require_proposal(session, user, str(proposal_id))
    return Response(markdown_export(session, proposal), media_type='text/markdown; charset=utf-8',
                    headers={'Content-Disposition': f'attachment; filename="proposal-{proposal.id}.md"'})
