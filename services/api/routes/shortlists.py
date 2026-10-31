from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete
from sqlalchemy.orm import Session

from services.api.dependencies import current_user, get_session, team_role
from src.platform.database.models import User
from src.platform.database.shortlists import TeamShortlistEntry
from src.platform.workflow.errors import WorkflowError
from src.platform.workflow.shortlists import add_entry, entry_view, list_entries, public_source, require_entry

router = APIRouter(prefix='/api/v2')


class AddInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    source_id: UUID
    note: str = Field(default='', max_length=2000)


class NoteInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    note: str = Field(max_length=2000)


@router.get('/teams/{team_id}/shortlist')
def shortlist(team_id: UUID, session: Session = Depends(get_session), user: User = Depends(current_user)):
    team_role(session, user, str(team_id))
    return {'items': list_entries(session, str(team_id))}


@router.post('/teams/{team_id}/shortlist', status_code=201)
def add(team_id: UUID, body: AddInput, session: Session = Depends(get_session), user: User = Depends(current_user)):
    team_role(session, user, str(team_id), edit=True)
    return add_entry(session, str(team_id), str(body.source_id), user.id, body.note)


@router.patch('/teams/{team_id}/shortlist/{entry_id}')
def change_note(team_id: UUID, entry_id: UUID, body: NoteInput,
                session: Session = Depends(get_session), user: User = Depends(current_user)):
    team_role(session, user, str(team_id), edit=True)
    entry = require_entry(session, str(team_id), str(entry_id))
    source, record = public_source(session, entry.source_id)
    entry.note = body.note
    session.commit()
    return entry_view(entry, source, record)


@router.delete('/teams/{team_id}/shortlist/{entry_id}', status_code=204)
def remove(team_id: UUID, entry_id: UUID, session: Session = Depends(get_session), user: User = Depends(current_user)):
    team_role(session, user, str(team_id), edit=True)
    existing = session.get(TeamShortlistEntry, str(entry_id))
    if existing is not None and existing.team_id != str(team_id):
        raise WorkflowError(404, 'shortlist_entry_not_found', 'Team shortlist entry was not found')
    session.execute(delete(TeamShortlistEntry).where(
        TeamShortlistEntry.id == str(entry_id), TeamShortlistEntry.team_id == str(team_id)))
    session.commit()
