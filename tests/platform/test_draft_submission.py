"""Draft jobs must capture the revision and source selection the user reviewed."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from services.api.app import create_app
from src.platform.database.models import Proposal
from src.platform.workflow.proposals import save_proposal


class DraftSubmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.app = create_app(f"sqlite:///{Path(self.tmp.name) / 'submission.db'}")
        self.app.state.db.create_schema()
        self.client = TestClient(self.app)
        self.client.post('/api/v2/auth/register', json={
            'email': 'draft@example.test', 'name': 'Draft tester', 'password': 'a sufficiently long password'})
        team = self.client.post('/api/v2/teams', json={'name': 'Draft review'}).json()
        self.proposal = self.client.post('/api/v2/proposals', json={
            'team_id': team['id'], 'title': 'Draft study', 'content': 'Reviewed text'}).json()
        self.path = '/api/v2/proposals/' + self.proposal['id']
        self.sources = [self.client.post(self.path + '/sources', json={
            'title': f'Evidence {i}', 'text': f'Checkable evidence {i}.', 'origin': 'synthetic'}).json() for i in (1, 2)]
        self.ids = [source['id'] for source in self.sources]
        self.proposal = self.client.patch(self.path, json={
            'expected_revision': 1, 'selected_source_ids': self.ids}).json()
        self.body = {'expected_revision': self.proposal['revision'], 'section': 'Methods',
                     'instruction': 'Describe the selected evidence.', 'source_ids': self.ids}

    def tearDown(self):
        self.client.close()
        self.app.state.db.engine.dispose()
        self.tmp.cleanup()

    def assert_no_jobs(self):
        self.assertEqual(self.client.get(self.path + '/jobs').json(), {'items': []})

    def test_submission_requires_reviewed_revision(self):
        body = {key: value for key, value in self.body.items() if key != 'expected_revision'}
        missing = self.client.post(self.path + '/jobs', json=body)
        self.assertEqual(missing.status_code, 422, missing.text)
        self.assert_no_jobs()
        invalid = self.client.post(self.path + '/jobs', json={**self.body, 'expected_revision': 0})
        self.assertEqual(invalid.status_code, 422)
        self.assert_no_jobs()

    def test_stale_client_cannot_capture_new_server_revision(self):
        saved = self.client.patch(self.path, json={
            'expected_revision': self.proposal['revision'], 'content': 'A newer collaborator edit',
            'selected_source_ids': [self.ids[1]]})
        self.assertEqual(saved.status_code, 200, saved.text)
        rejected = self.client.post(self.path + '/jobs', json=self.body)
        self.assertEqual(rejected.status_code, 409, rejected.text)
        self.assertEqual(rejected.json()['error']['code'], 'revision_conflict')
        self.assert_no_jobs()

    def test_unsaved_source_selection_returns_conflict_without_enqueuing(self):
        rejected = self.client.post(self.path + '/jobs', json={**self.body, 'source_ids': self.ids[:1]})
        self.assertEqual(rejected.status_code, 409, rejected.text)
        self.assertEqual(rejected.json()['error']['code'], 'source_selection_changed')
        self.assert_no_jobs()

    def test_matching_saved_selection_ignores_order_and_captures_exact_revision(self):
        created = self.client.post(self.path + '/jobs', json={**self.body, 'source_ids': list(reversed(self.ids))})
        self.assertEqual(created.status_code, 202, created.text)
        self.assertEqual(created.json()['base_revision'], self.proposal['revision'])
        self.assertEqual({ref['id'] for ref in created.json()['source_refs']}, set(self.ids))
        self.assertEqual(len(self.client.get(self.path + '/jobs').json()['items']), 1)

    def test_save_after_valid_read_keeps_legitimate_older_base_revision(self):
        enqueue = self.app.state.jobs.enqueue

        def save_then_enqueue(*args, **kwargs):
            with self.app.state.db.session_factory() as session:
                proposal = session.get(Proposal, self.proposal['id'])
                save_proposal(session, proposal, self.proposal['revision'], {'content': 'Saved during admission'})
            return enqueue(*args, **kwargs)

        with patch.object(self.app.state.jobs, 'enqueue', side_effect=save_then_enqueue):
            created = self.client.post(self.path + '/jobs', json=self.body)
        self.assertEqual(created.status_code, 202, created.text)
        self.assertEqual(created.json()['base_revision'], self.proposal['revision'])
        self.assertEqual(self.client.get(self.path).json()['revision'], self.proposal['revision'] + 1)


if __name__ == '__main__':
    unittest.main()
