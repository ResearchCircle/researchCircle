"""Database-only concurrency smoke for the isolated development stack; pause its worker first."""

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

from sqlalchemy import func, select

from src.platform.database import Database
from src.platform.database.models import Proposal, Team, User, new_id
from src.platform.drafting.fixtures import SAMPLE_REQUEST, SAMPLE_SOURCE
from src.platform.drafting.jobs import JobError
from src.platform.workflow.accounts import password_hasher
from src.platform.workflow.draft_jobs import DraftJobRecord, PersistedJobStore
from src.platform.workflow.errors import WorkflowError
from src.platform.workflow.proposals import save_proposal


def main() -> int:
    database = Database()
    assert database.engine.dialect.name == 'postgresql', 'This smoke requires real PostgreSQL.'
    store = PersistedJobStore(database)
    with database.session_factory() as session:
        assert session.scalar(select(func.count()).select_from(DraftJobRecord).where(
            DraftJobRecord.state.in_(('queued', 'running')))) == 0, 'Existing active work must finish first.'
        users = [new_id() for _ in range(8)]
        team_id, proposal_id = new_id(), new_id()
        fixture_hash = password_hasher.hash('Postgres synthetic test passphrase')
        for user_id in users:
            session.add(User(id=user_id, email=f'postgres-smoke-{user_id}@example.test', name='Postgres smoke fixture', password_hash=fixture_hash))
        session.add(Team(id=team_id, name='Postgres smoke fixture'))
        session.commit()
        session.add(Proposal(id=proposal_id, team_id=team_id, title='Concurrency smoke fixture', content='', revision=1))
        session.commit()
    request = replace(SAMPLE_REQUEST, proposal_id=proposal_id, base_revision=1)
    source = replace(SAMPLE_SOURCE, proposal_id=proposal_id)
    accepted = []

    def admission(same_user=False):
        barrier = threading.Barrier(8)
        lock = threading.Lock()
        def submit(index):
            barrier.wait()
            try:
                job = store.enqueue(users[0] if same_user else users[index], request, (source,))
                with lock:
                    accepted.append(job.id)
                return 'queued'
            except JobError as error:
                return error.code
        with ThreadPoolExecutor(max_workers=8) as pool:
            return list(pool.map(submit, range(8)))

    queue = admission()
    assert queue.count('queued') == 4 and queue.count('queue_full') == 4, queue
    for job_id in accepted:
        store.cancel(job_id)
    accepted.clear()
    user = admission(same_user=True)
    assert user.count('queued') == 1 and user.count('user_busy') == 7, user
    job = store.claim_next()
    assert job and job.sources == (source,) and job.request == request
    assert PersistedJobStore(database).interrupt_running() == 1
    assert store.get(job.id).error.code == 'interrupted'
    barrier = threading.Barrier(2)

    def save(index):
        with database.session_factory() as session:
            proposal = session.get(Proposal, proposal_id)
            barrier.wait()
            try:
                save_proposal(session, proposal, 1, {'content': f'Synthetic concurrent edit {index}'})
                return 200
            except WorkflowError as error:
                return error.status
    with ThreadPoolExecutor(max_workers=2) as pool:
        saves = list(pool.map(save, range(2)))
    assert sorted(saves) == [200, 409], saves
    with database.session_factory() as session:
        assert session.get(Proposal, proposal_id).revision == 2
    database.engine.dispose()
    print(json.dumps({'status': 'passed', 'database': 'postgresql', 'queued_admitted': 4,
                      'queue_full_rejected': 4, 'same_user_admitted': 1, 'same_user_rejected': 7,
                      'concurrent_save_statuses': sorted(saves), 'restart_interrupted': True,
                      'snapshot_roundtrip': True, 'evidence': 'synthetic_development_records'}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
