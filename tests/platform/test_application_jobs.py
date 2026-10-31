import tempfile
import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from services.api.app import create_app
from services.api.routes.search import seed_samples
from src.platform.drafting.fixtures import FixtureTokenCounter
from src.platform.drafting.worker import GenerationWorker
from src.platform.drafting.service import DraftingService
from src.platform.models.fixtures import ExtractiveFixtureProvider


class ApplicationJobTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app('sqlite:///' + str(Path(self.tmp.name) / 'app.sqlite'))
        self.app.state.db.create_schema()
        with self.app.state.db.session_factory() as session:
            seed_samples(session)
            session.commit()
        self.client = TestClient(self.app)
        registered = self.client.post('/api/v2/auth/register', json={
            'email': 'owner@example.test', 'name': 'Owner', 'password': 'long-fixture-password'})
        self.assertEqual(registered.status_code, 201, registered.text)
        team = self.client.post('/api/v2/teams', json={'name': 'Job test team'}).json()
        self.proposal = self.client.post('/api/v2/proposals', json={'team_id': team['id'], 'title': 'Sensor proposal'}).json()

    def tearDown(self):
        self.client.close()
        self.app.state.db.engine.dispose()
        self.tmp.cleanup()

    def test_real_api_job_uses_attached_snapshots_and_requires_revision_acceptance(self):
        sample = self.client.get('/api/v2/search?q=sensor').json()['items'][0]
        attached = self.client.post(f"/api/v2/proposals/{self.proposal['id']}/sources/attach", json={'source_id': sample['source_id']})
        self.assertEqual(attached.status_code, 201)
        saved = self.client.patch(f"/api/v2/proposals/{self.proposal['id']}", json={
            'expected_revision': self.proposal['revision'], 'selected_source_ids': [sample['source_id']]})
        self.assertEqual(saved.status_code, 200, saved.text)
        job = self.client.post(f"/api/v2/proposals/{self.proposal['id']}/jobs", json={
            'expected_revision': saved.json()['revision'], 'section': 'Methods',
            'instruction': 'Describe sensor evidence.', 'source_ids': [sample['source_id']]})
        self.assertEqual(job.status_code, 202, job.text)
        job = job.json()
        worker = GenerationWorker(self.app.state.jobs, DraftingService(ExtractiveFixtureProvider(), FixtureTokenCounter()),
                                  Path(self.tmp.name) / 'worker.lock', lambda: True)
        try:
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                worker.tick()
                view = self.client.get('/api/v2/jobs/' + job['id']).json()
                if view['state'] in ('succeeded', 'failed'):
                    break
                time.sleep(.01)
            self.assertEqual(view['state'], 'succeeded', view)
            self.assertEqual(view['output']['citations'][0]['source_id'], sample['source_id'])
            current = self.client.get('/api/v2/proposals/' + self.proposal['id']).json()
            self.assertEqual(current['content'], '')
            saved = self.client.patch('/api/v2/proposals/' + self.proposal['id'], json={
                'expected_revision': current['revision'], 'content': 'Newer manual edit'})
            self.assertEqual(saved.status_code, 200)
            stale = self.client.patch('/api/v2/proposals/' + self.proposal['id'], json={
                'expected_revision': view['base_revision'], 'content': view['output']['text']})
            self.assertEqual(stale.status_code, 409)
        finally:
            worker.close(wait=True)

    def test_unsaved_sources_and_other_team_job_reads_are_rejected(self):
        sample = self.client.get('/api/v2/search?q=sensor').json()['items'][0]
        rejected = self.client.post(f"/api/v2/proposals/{self.proposal['id']}/jobs", json={
            'expected_revision': 1, 'section': 'Methods', 'instruction': 'Describe evidence.', 'source_ids': [sample['source_id']]})
        self.assertEqual(rejected.status_code, 409)
        self.assertEqual(rejected.json()['error']['code'], 'source_selection_changed')
        queued = self.client.post(f"/api/v2/proposals/{self.proposal['id']}/jobs", json={
            'expected_revision': 1, 'section': 'Methods', 'instruction': 'Describe evidence.', 'source_ids': []}).json()
        with TestClient(self.app) as other:
            other.post('/api/v2/auth/register', json={'email': 'other@example.test', 'name': 'Other', 'password': 'long-fixture-password'})
            self.assertEqual(other.get('/api/v2/jobs/' + queued['id']).status_code, 403)
            self.assertEqual(other.post('/api/v2/jobs/' + queued['id'] + '/cancel').status_code, 403)
        cancelled = self.client.post('/api/v2/jobs/' + queued['id'] + '/cancel')
        self.assertEqual(cancelled.json()['error']['code'], 'cancelled')


if __name__ == '__main__':
    unittest.main()
