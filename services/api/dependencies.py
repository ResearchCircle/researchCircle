import hashlib
from collections.abc import Iterator

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.platform.database import DatabaseConfigurationError
from src.platform.database.models import LoginSession, Membership, Proposal, User, utcnow
from src.platform.workflow.errors import WorkflowError

SESSION_COOKIE = 'tbr_session'


def get_session(request: Request) -> Iterator[Session]:
    try:
        session = request.app.state.db.session_factory()
    except DatabaseConfigurationError as exc:
        raise WorkflowError(503, 'database_unconfigured', str(exc)) from None
    try:
        yield session
    finally:
        session.close()


def current_user(request: Request, session: Session = Depends(get_session)) -> User:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise WorkflowError(401, 'unauthenticated', 'Sign in to continue')
    login = session.scalar(select(LoginSession).where(
        LoginSession.token_hash == hashlib.sha256(token.encode()).hexdigest(),
        LoginSession.expires_at > utcnow()))
    if login is None or (user := session.get(User, login.user_id)) is None:
        raise WorkflowError(401, 'unauthenticated', 'Sign in to continue')
    return user


def team_role(session: Session, user: User, team_id: str, edit: bool = False, owner: bool = False) -> str:
    membership = session.get(Membership, (team_id, user.id))
    if membership is None or (edit and membership.role not in ('owner', 'editor')) or (owner and membership.role != 'owner'):
        raise WorkflowError(403, 'forbidden', 'You do not have permission for this team')
    return membership.role


def require_proposal(session: Session, user: User, proposal_id: str, edit: bool = False) -> Proposal:
    proposal = session.get(Proposal, proposal_id)
    if proposal is None:
        raise WorkflowError(404, 'proposal_not_found', 'Proposal was not found')
    team_role(session, user, proposal.team_id, edit=edit)
    return proposal
