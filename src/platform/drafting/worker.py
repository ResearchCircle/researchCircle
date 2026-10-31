"""Single-host generation controller. Persistence and routes are supplied by T2."""

import fcntl
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable

from ..models.provider import ProviderError, validate_request
from .jobs import GenerationJob, JobError, JobFailure, JobStore
from .service import DraftingService
from .types import DraftError


class GenerationWorker:
    """tick() polls work without blocking on inference; keep one instance per model.

    All processes for this model must share lease_path on the same host filesystem.
    A second host needs coordination from the deployment/job store before use.
    Cancellation/timeout may finish a UI job while its inference slot stays held.
    """

    def __init__(self, store: JobStore, service: DraftingService, lease_path: Path,
                 idle_check: Callable[[], bool], deadline_s: float = 120):
        validate_request('worker', 512, deadline_s)
        self._lease = Path(lease_path).open('a')
        try:
            fcntl.flock(self._lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self._lease.close()
            raise JobError('worker_busy', 'Another generation worker holds the model lease.', True) from None
        self.store, self.service, self.idle_check = store, service, idle_check
        self.deadline_s = deadline_s
        self._mutex = threading.Lock()
        self._active = None
        self._closed = False
        self.blocked_reason = None
        try:
            self.interrupted_count = self.store.interrupt_running()
            self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='draft-generation')
        except Exception:
            self._lease.close()
            raise

    def _generate(self, job: GenerationJob):
        try:
            result = self.service.generate(job.request, job.sources, self.deadline_s)
            return result, None, time.monotonic()
        except (ProviderError, DraftError) as error:
            return None, JobFailure(error.code, str(error), error.retryable), time.monotonic()
        except Exception:
            return None, JobFailure('generation_failed', 'Draft generation failed.', True), time.monotonic()

    def _collect(self) -> None:
        if self._active is None:
            return
        job, future, deadline = self._active
        if future.done():
            result, error, finished = future.result()
            if finished > deadline:
                result, error = None, JobFailure('draft_timeout', 'Draft deadline expired.', True)
            self.store.finish(job.id, output=result, error=error)
            self._active = None
        elif time.monotonic() >= deadline:
            self.store.finish(job.id, error=JobFailure('draft_timeout', 'Draft deadline expired; inference may still be running.', True))

    def tick(self) -> None:
        with self._mutex:
            if self._closed:
                raise RuntimeError('Worker is closed')
            self._collect()
            if self._active is not None:
                return
            try:
                ready = self.idle_check()
            except Exception:
                ready = False
            if ready is not True:
                self.blocked_reason = 'model_not_confirmed_idle'
                return
            self.blocked_reason = None
            job = self.store.claim_next()
            if job is not None:
                deadline = time.monotonic() + self.deadline_s
                self._active = (job, self._executor.submit(self._generate, job), deadline)

    def close(self, wait: bool = False) -> bool:
        with self._mutex:
            if self._closed:
                return True
            if self._active is not None and not self._active[1].done() and not wait:
                return False
            self._executor.shutdown(wait=wait)
            try:
                self._collect()
            finally:
                # Inference has ended; a failed DB write must not strand the lease.
                self._lease.close()
                self._closed = True
            return True
