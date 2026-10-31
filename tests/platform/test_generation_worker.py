import tempfile
import threading
import time
import unittest
from pathlib import Path

from src.platform.drafting.fixtures import SAMPLE_REQUEST, SAMPLE_SOURCE, FixtureDraftProvider, FixtureTokenCounter
from src.platform.drafting.jobs import FixtureJobStore, JobError
from src.platform.drafting.service import DraftingService
from src.platform.drafting.worker import GenerationWorker
from src.platform.models.provider import ProviderError


class GenerationWorkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.lease = Path(self.tmp.name) / 'generation.lock'
        self.store = FixtureJobStore()
        self.entered = threading.Event()
        self.release = threading.Event()
        self.calls = 0
        self.idle = True
        self.error = None
        self.workers = []
        parent = self

        class BlockingProvider(FixtureDraftProvider):
            def generate(self, *args):
                parent.calls += 1
                parent.entered.set()
                parent.release.wait(2)
                if parent.error:
                    raise parent.error
                return super().generate(*args)

        self.service = DraftingService(BlockingProvider(), FixtureTokenCounter())

    def tearDown(self):
        self.release.set()
        for worker in self.workers:
            worker.close(wait=True)
        self.tmp.cleanup()

    def worker(self, **kwargs):
        worker = GenerationWorker(self.store, self.service, self.lease, lambda: self.idle, **kwargs)
        self.workers.append(worker)
        return worker

    def enqueue(self, user='user-1'):
        return self.store.enqueue(user, SAMPLE_REQUEST, (SAMPLE_SOURCE,))

    def until(self, worker, predicate):
        deadline = time.monotonic() + 2
        while not predicate() and time.monotonic() < deadline:
            worker.tick()
            time.sleep(.005)
        self.assertTrue(predicate())

    def test_queue_and_user_limits_are_atomic_fixture_behavior(self):
        self.enqueue()
        with self.assertRaises(JobError) as caught:
            self.enqueue()
        self.assertEqual(caught.exception.code, 'user_busy')
        for user in ['2', '3', '4']:
            self.enqueue(user)
        with self.assertRaises(JobError) as caught:
            self.enqueue('5')
        self.assertEqual(caught.exception.code, 'queue_full')

    def test_success_records_result_without_changing_proposal_revision(self):
        job = self.enqueue()
        self.release.set()
        worker = self.worker()
        self.until(worker, lambda: self.store.get(job.id).state == 'succeeded')
        result = self.store.get(job.id)
        self.assertEqual(result.output.base_revision, 3)
        self.assertEqual(result.request, SAMPLE_REQUEST)
        self.assertIsNone(result.error)
        self.assertIsNotNone(result.finished_at)

    def test_cancel_does_not_admit_another_call_or_accept_late_output(self):
        first, second = self.enqueue(), self.enqueue('user-2')
        worker = self.worker()
        worker.tick()
        self.assertTrue(self.entered.wait(1))
        self.store.cancel(first.id)
        worker.tick()
        self.assertEqual(self.calls, 1)
        self.assertEqual(self.store.get(second.id).state, 'queued')
        self.release.set()
        self.until(worker, lambda: self.store.get(second.id).state == 'succeeded')
        self.assertEqual(self.store.get(first.id).error.code, 'cancelled')
        self.assertIsNone(self.store.get(first.id).output)

    def test_deadline_marks_failed_while_slot_stays_occupied(self):
        first, second = self.enqueue(), self.enqueue('user-2')
        worker = self.worker(deadline_s=.02)
        worker.tick()
        self.assertTrue(self.entered.wait(1))
        time.sleep(.03)
        worker.tick()
        self.assertEqual(self.store.get(first.id).error.code, 'draft_timeout')
        self.assertEqual(self.store.get(second.id).state, 'queued')
        self.assertEqual(self.calls, 1)
        self.assertFalse(worker.close(wait=False))

    def test_transport_timeout_quarantines_until_model_is_observed_idle(self):
        first, second = self.enqueue(), self.enqueue('user-2')
        self.error = ProviderError('provider_timeout', 'Local provider timed out.', True)
        worker = self.worker()
        worker.tick()
        self.assertTrue(self.entered.wait(1))
        self.idle = False
        self.release.set()
        self.until(worker, lambda: self.store.get(first.id).state == 'failed')
        worker.tick()
        self.assertEqual(self.store.get(second.id).state, 'queued')
        self.assertEqual(self.calls, 1)
        self.idle, self.error = True, None
        self.until(worker, lambda: self.store.get(second.id).state == 'succeeded')

    def test_restart_marks_running_interrupted_and_waits_for_idle(self):
        old = self.enqueue()
        self.store.claim_next()
        next_job = self.enqueue('user-2')
        self.idle = False
        worker = self.worker()
        self.assertEqual(self.store.get(old.id).error.code, 'interrupted')
        worker.tick()
        self.assertEqual(self.store.get(next_job.id).state, 'queued')
        self.idle = True
        self.release.set()
        self.until(worker, lambda: self.store.get(next_job.id).state == 'succeeded')

    def test_exclusive_lease_prevents_second_worker_from_interrupting_live_jobs(self):
        job = self.enqueue()
        worker = self.worker()
        worker.tick()
        with self.assertRaises(JobError) as caught:
            self.worker()
        self.assertEqual(caught.exception.code, 'worker_busy')
        self.assertEqual(self.store.get(job.id).state, 'running')

    def test_internal_failure_is_sanitized_and_cancelled_queue_never_runs(self):
        cancelled = self.enqueue()
        self.store.cancel(cancelled.id)
        broken = self.enqueue('user-2')
        self.error = RuntimeError('PRIVATE source text')
        self.release.set()
        worker = self.worker()
        self.until(worker, lambda: self.store.get(broken.id).state == 'failed')
        error = self.store.get(broken.id).error
        self.assertEqual(error.code, 'generation_failed')
        self.assertNotIn('PRIVATE', error.message)
        self.assertEqual(self.calls, 1)

    def test_shutdown_write_failure_releases_lease_only_after_inference_finishes(self):
        self.enqueue()
        worker = self.worker()
        worker.tick()
        self.assertTrue(self.entered.wait(1))
        original = self.store.finish
        def rejected_finish(*_args, **_kwargs):
            raise RuntimeError('Synthetic persistence failure')
        self.store.finish = rejected_finish
        self.assertFalse(worker.close(wait=False))
        self.release.set()
        try:
            with self.assertRaises(RuntimeError):
                worker.close(wait=True)
        finally:
            self.store.finish = original
        replacement = self.worker()
        self.assertEqual(replacement.interrupted_count, 1)


if __name__ == '__main__':
    unittest.main()
