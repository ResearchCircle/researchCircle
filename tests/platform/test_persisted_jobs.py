import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from sqlalchemy import func, select

from src.platform.database import Database
from src.platform.database.models import Proposal, Team, User, new_id
from src.platform.drafting.fixtures import SAMPLE_REQUEST, SAMPLE_SOURCE, FixtureDraftProvider, FixtureTokenCounter
from src.platform.drafting.jobs import JobError, JobFailure
from src.platform.drafting.service import DraftingService
from src.platform.workflow.draft_jobs import DraftJobRecord, PersistedJobStore, job_view


class PersistedJobTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database('sqlite:///' + str(Path(self.tmp.name) / 'jobs.sqlite'))
        self.db.create_schema()
        self.users = [new_id() for _ in range(8)]
        team_id = new_id()
        with self.db.session_factory() as session:
            for index, user_id in enumerate(self.users):
                session.add(User(id=user_id, email=f'fixture{index}@example.test', name=f'Fixture {index}', password_hash='not-used-for-login'))
            session.add(Team(id=team_id, name='Fixture team'))
            session.commit()
            session.add(Proposal(id=SAMPLE_REQUEST.proposal_id, team_id=team_id, title='Fixture proposal', content='', revision=3))
            session.commit()
        self.store = PersistedJobStore(self.db)

    def tearDown(self):
        self.db.engine.dispose()
        self.tmp.cleanup()

    def enqueue(self, user=0):
        return self.store.enqueue(self.users[user], SAMPLE_REQUEST, (SAMPLE_SOURCE,))

    def test_source_snapshot_and_result_survive_a_new_store(self):
        queued = self.enqueue()
        restored = PersistedJobStore(self.db).claim_next()
        self.assertEqual(restored.id, queued.id)
        self.assertEqual(restored.request, SAMPLE_REQUEST)
        self.assertEqual(restored.sources, (SAMPLE_SOURCE,))
        result = DraftingService(FixtureDraftProvider(), FixtureTokenCounter()).generate(restored.request, restored.sources)
        self.assertTrue(self.store.finish(queued.id, output=result))
        saved = PersistedJobStore(self.db).get(queued.id)
        self.assertEqual(saved.state, 'succeeded')
        self.assertEqual(saved.output, result)
        self.assertIsNotNone(saved.finished_at)
        self.assertNotIn('sources', job_view(saved))
        self.assertNotIn('request', job_view(saved))

    def test_cancel_suppresses_late_completion(self):
        queued = self.enqueue()
        self.store.claim_next()
        self.assertTrue(self.store.cancel(queued.id))
        result = DraftingService(FixtureDraftProvider(), FixtureTokenCounter()).generate(SAMPLE_REQUEST, (SAMPLE_SOURCE,))
        self.assertFalse(self.store.finish(queued.id, output=result))
        saved = self.store.get(queued.id)
        self.assertEqual(saved.error.code, 'cancelled')
        self.assertIsNone(saved.output)

    def test_restart_interrupts_running_and_preserves_queue(self):
        running = self.enqueue()
        self.store.claim_next()
        queued = self.enqueue(1)
        self.assertEqual(PersistedJobStore(self.db).interrupt_running(), 1)
        self.assertEqual(self.store.get(running.id).error.code, 'interrupted')
        self.assertEqual(self.store.get(queued.id).state, 'queued')

    def test_provider_failure_can_end_waiting_job_without_false_running_state(self):
        job = self.enqueue()
        self.assertTrue(self.store.fail_next_queued(JobFailure('provider_unavailable', 'Model status unavailable.', True)))
        saved = PersistedJobStore(self.db).get(job.id)
        self.assertEqual(saved.state, 'failed')
        self.assertIsNone(saved.started_at)
        self.assertEqual(saved.error.code, 'provider_unavailable')
        self.assertIsNone(self.store.claim_next())

    def test_concurrent_admission_never_exceeds_four_queued(self):
        barrier = threading.Barrier(8)
        def enqueue(index):
            barrier.wait()
            try:
                return self.enqueue(index).state
            except JobError as error:
                return error.code
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(enqueue, range(8)))
        self.assertEqual(results.count('queued'), 4)
        self.assertEqual(results.count('queue_full'), 4)
        with self.db.session_factory() as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(DraftJobRecord)), 4)

    def test_concurrent_admission_never_duplicates_active_user(self):
        barrier = threading.Barrier(8)
        def enqueue(_index):
            barrier.wait()
            try:
                return self.enqueue().state
            except JobError as error:
                return error.code
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(enqueue, range(8)))
        self.assertEqual(results.count('queued'), 1)
        self.assertEqual(results.count('user_busy'), 7)


if __name__ == '__main__':
    unittest.main()
