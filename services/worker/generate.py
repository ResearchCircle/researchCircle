"""Consume persisted draft jobs, serializing inference on the local model."""

import signal
import time

from sqlalchemy.exc import SQLAlchemyError

from deployment.runtime import RuntimeConfig
from src.platform.database import Database
from src.platform.drafting.fixtures import FixtureTokenCounter
from src.platform.drafting.service import DraftingService
from src.platform.drafting.worker import GenerationWorker
from src.platform.models.fixtures import ExtractiveFixtureProvider
from src.platform.models.provider import LocalModelProvider
from src.platform.workflow.draft_jobs import PersistedJobStore


def close_worker(worker, database) -> bool:
    try:
        worker.close(wait=True)
        return True
    except SQLAlchemyError:
        print('Draft result could not be persisted at shutdown; the next worker will mark it interrupted.', flush=True)
        return False
    finally:
        database.engine.dispose()


def main() -> int:
    import os
    config = RuntimeConfig.from_env(os.environ)
    database = Database()
    store = PersistedJobStore(database)
    config.work_dir.mkdir(parents=True, exist_ok=True)
    if config.provider == 'fixture':
        provider, counter, idle = ExtractiveFixtureProvider(), FixtureTokenCounter(), lambda: True
    else:
        provider = LocalModelProvider(config.model_base_url, config.model_id)
        counter, idle = provider, provider.is_idle
    stopped = False

    def stop(_signal, _frame):
        nonlocal stopped
        stopped = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        worker = GenerationWorker(store, DraftingService(provider, counter), config.work_dir / 'generation.lock', idle)
    except SQLAlchemyError:
        print('Draft database is unavailable at worker startup.', flush=True)
        database.engine.dispose()
        return 1
    print(f'Draft worker ready ({config.provider}); interrupted jobs: {worker.interrupted_count}', flush=True)
    try:
        while not stopped:
            try:
                worker.tick()
            except SQLAlchemyError:
                # SQL/driver exceptions may contain source text or connection secrets.
                print('Draft database operation failed; retaining worker state for retry.', flush=True)
            time.sleep(.25)
    finally:
        # Do not release the lease while the actual inference call is still active.
        closed = close_worker(worker, database)
    return 0 if closed else 1


if __name__ == '__main__':
    raise SystemExit(main())
