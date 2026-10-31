"""Proposed job-store seam and in-memory fixture; T2 supplies durable transactions."""

import threading
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

from .types import DraftError, DraftRequest, DraftResult, SourceSnapshot


class JobError(DraftError):
    pass


@dataclass(frozen=True)
class JobFailure:
    code: str
    message: str
    retryable: bool


@dataclass(frozen=True)
class GenerationJob:
    id: str
    user_id: str
    request: DraftRequest
    sources: tuple[SourceSnapshot, ...]
    state: str
    created_at: str
    started_at: str | None = None
    finished_at: str | None = None
    output: DraftResult | None = None
    error: JobFailure | None = None


class JobStore(Protocol):
    def interrupt_running(self) -> int: ...
    def claim_next(self) -> GenerationJob | None: ...
    def finish(self, job_id: str, *, output: DraftResult | None = None,
               error: JobFailure | None = None) -> bool: ...
    def fail_next_queued(self, error: JobFailure) -> bool: ...


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class FixtureJobStore:
    """Thread-safe process-local fixture only; all data is lost on process exit."""

    def __init__(self):
        self._jobs: dict[str, GenerationJob] = {}
        self._lock = threading.RLock()

    def enqueue(self, user_id: str, request: DraftRequest,
                sources: tuple[SourceSnapshot, ...]) -> GenerationJob:
        with self._lock:
            if any(job.user_id == user_id and job.state in ('queued', 'running') for job in self._jobs.values()):
                raise JobError('user_busy', 'You already have a queued or running draft.', True)
            if sum(job.state == 'queued' for job in self._jobs.values()) >= 4:
                raise JobError('queue_full', 'Draft queue is full; retry later.', True)
            job = GenerationJob(str(uuid4()), user_id, request, tuple(sources), 'queued', _now())
            self._jobs[job.id] = job
            return job

    def get(self, job_id: str) -> GenerationJob:
        with self._lock:
            return self._jobs[job_id]

    def claim_next(self) -> GenerationJob | None:
        with self._lock:
            if any(job.state == 'running' for job in self._jobs.values()):
                return None
            for job in self._jobs.values():
                if job.state == 'queued':
                    claimed = replace(job, state='running', started_at=_now())
                    self._jobs[job.id] = claimed
                    return claimed
        return None

    def finish(self, job_id: str, *, output: DraftResult | None = None,
               error: JobFailure | None = None) -> bool:
        if (output is None) == (error is None):
            raise ValueError('Exactly one of output or error is required')
        with self._lock:
            job = self._jobs[job_id]
            if job.state != 'running':
                return False
            self._jobs[job_id] = replace(job, state='failed' if error else 'succeeded',
                                         output=output, error=error, finished_at=_now())
            return True

    def cancel(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs[job_id]
            if job.state not in ('queued', 'running'):
                return False
            self._jobs[job_id] = replace(job, state='failed', finished_at=_now(),
                                         error=JobFailure('cancelled', 'Draft cancelled.', True))
            return True

    def fail_next_queued(self, error: JobFailure) -> bool:
        with self._lock:
            for job in self._jobs.values():
                if job.state == 'queued':
                    self._jobs[job.id] = replace(job, state='failed', error=error, finished_at=_now())
                    return True
        return False

    def interrupt_running(self) -> int:
        with self._lock:
            running = [job for job in self._jobs.values() if job.state == 'running']
            for job in running:
                self.finish(job.id, error=JobFailure('interrupted', 'Worker stopped; retry this draft.', True))
            return len(running)
