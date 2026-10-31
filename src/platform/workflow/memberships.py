"""Team mutation locking and the invariant that every team keeps an owner."""
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from src.platform.database.models import Membership, Team
from .errors import WorkflowError


def lock_team(session: Session, team_id: str):
    # Every membership/invitation mutation acquires the team before invitation
    # rows. This also serializes independent owners checking the last owner.
    if session.get_bind().dialect.name == 'sqlite':
        session.execute(text('BEGIN IMMEDIATE'))
    team = session.scalar(select(Team.id).where(Team.id == team_id).with_for_update())
    if team is None:
        raise WorkflowError(404, 'team_not_found', 'Team was not found')


def change_member(session: Session, team_id: str, user_id: str, role: str | None) -> Membership | None:
    """Caller must hold the team lock and have checked the current owner role."""
    membership = session.get(Membership, (team_id, user_id))
    if membership is None:
        if role is None:
            return None
        raise WorkflowError(404, 'member_not_found', 'Team member was not found')
    if membership.role == 'owner' and role != 'owner':
        owners = session.scalar(select(func.count()).select_from(Membership).where(
            Membership.team_id == team_id, Membership.role == 'owner'))
        if owners <= 1:
            raise WorkflowError(409, 'last_owner', 'Promote another owner before removing or demoting the last owner')
    if role is None:
        session.delete(membership)
    else:
        membership.role = role
    return membership
