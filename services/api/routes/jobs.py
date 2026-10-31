from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from services.api.dependencies import current_user, get_session, require_proposal
from src.platform.database.models import ProposalSource, Source, User
from src.platform.drafting.jobs import JobError
from src.platform.drafting.types import DraftRequest, SourceRef, SourceSnapshot
from src.platform.workflow.draft_jobs import job_view
from src.platform.workflow.errors import WorkflowError

router = APIRouter(prefix='/api/v2')


class JobInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    expected_revision: int = Field(ge=1)
    section: str = Field(min_length=1, max_length=200)
    instruction: str = Field(min_length=1, max_length=8000)
    source_ids: list[UUID] = Field(default_factory=list, max_length=100)


def _visible_job(request, session, user, job_id, edit=False):
    job = request.app.state.jobs.get(str(job_id))
    if job is None:
        raise WorkflowError(404, 'job_not_found', 'Draft job was not found')
    require_proposal(session, user, job.request.proposal_id, edit=edit)
    return job


@router.post('/proposals/{proposal_id}/jobs', status_code=202)
def submit(proposal_id: UUID, body: JobInput, request: Request,
           session: Session = Depends(get_session), user: User = Depends(current_user)):
    proposal = require_proposal(session, user, str(proposal_id), edit=True)
    if proposal.revision != body.expected_revision:
        raise WorkflowError(409, 'revision_conflict', 'The proposal changed; reload before requesting a draft')
    if not body.section.strip() or not body.instruction.strip():
        raise WorkflowError(422, 'invalid_draft_request', 'Section and instruction are required')
    ids = [str(value) for value in body.source_ids]
    if len(ids) != len(set(ids)):
        raise WorkflowError(422, 'invalid_sources', 'Select each source once')
    if set(ids) != set(proposal.selected_source_ids):
        raise WorkflowError(409, 'source_selection_changed', 'Save the selected sources before requesting a draft')
    attached = {source.id: source for source in session.scalars(select(Source).join(ProposalSource).where(
        ProposalSource.proposal_id == proposal.id, Source.id.in_(ids)))}
    if len(attached) != len(ids):
        raise WorkflowError(404, 'source_unavailable', 'A selected source is not attached to this proposal')
    snapshots = []
    for source_id in ids:
        source = attached[source_id]
        if not source.is_public and source.proposal_id != proposal.id:
            raise WorkflowError(404, 'source_unavailable', 'A selected source is unavailable')
        snapshots.append(SourceSnapshot(**{key: getattr(source, key) for key in
                                          ('id', 'version', 'content_hash', 'title', 'origin', 'text', 'proposal_id', 'is_public')}))
    refs = tuple(SourceRef(source.id, source.version, source.content_hash) for source in snapshots)
    captured = DraftRequest(proposal.id, body.expected_revision, body.section.strip(), body.instruction.strip(), refs)
    try:
        job = request.app.state.jobs.enqueue(user.id, captured, tuple(snapshots))
    except JobError as error:
        raise WorkflowError(429, error.code, str(error), error.retryable) from None
    return job_view(job)


@router.get('/proposals/{proposal_id}/jobs')
def list_jobs(proposal_id: UUID, request: Request, session: Session = Depends(get_session), user: User = Depends(current_user)):
    require_proposal(session, user, str(proposal_id))
    return {'items': [job_view(job) for job in request.app.state.jobs.list_for_proposal(str(proposal_id))]}


@router.get('/jobs/{job_id}')
def get_job(job_id: UUID, request: Request, session: Session = Depends(get_session), user: User = Depends(current_user)):
    return job_view(_visible_job(request, session, user, job_id))


@router.post('/jobs/{job_id}/cancel')
def cancel_job(job_id: UUID, request: Request, session: Session = Depends(get_session), user: User = Depends(current_user)):
    job = _visible_job(request, session, user, job_id, edit=True)
    request.app.state.jobs.cancel(job.id)
    return job_view(request.app.state.jobs.get(job.id))
