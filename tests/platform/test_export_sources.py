"""Saved inline citations retain their attached snapshot bibliography."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from fastapi.testclient import TestClient

from services.api.app import create_app


class ExportSourcesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.app = create_app(f"sqlite:///{Path(self.tmp.name) / 'export.db'}")
        self.app.state.db.create_schema()
        self.client = TestClient(self.app)
        self.client.post('/api/v2/auth/register', json={
            'email': 'export@example.test', 'name': 'Export test', 'password': 'Synthetic export password'})
        self.team = self.client.post('/api/v2/teams', json={'name': 'Export test'}).json()
        self.proposal = self.make_proposal('Citation export')
        self.path = '/api/v2/proposals/' + self.proposal['id']

    def tearDown(self):
        self.client.close()
        self.app.state.db.engine.dispose()
        self.tmp.cleanup()

    def make_proposal(self, title):
        response = self.client.post('/api/v2/proposals', json={'team_id': self.team['id'], 'title': title})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def add_source(self, proposal, title):
        response = self.client.post('/api/v2/proposals/' + proposal['id'] + '/sources', json={
            'title': title, 'text': 'Synthetic evidence for ' + title, 'origin': 'Synthetic test fixture'})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_deselecting_draft_evidence_keeps_saved_inline_citation_reference(self):
        cited = self.add_source(self.proposal, 'Previously cited source')
        selected = self.add_source(self.proposal, 'Next draft source')
        content = f"Saved claim [{cited['id']}]. Another claim [{cited['id']}]."
        saved = self.client.patch(self.path, json={'expected_revision': 1, 'content': content,
            'selected_source_ids': [cited['id']]}).json()
        changed = self.client.patch(self.path, json={'expected_revision': saved['revision'],
            'selected_source_ids': [selected['id']]})
        self.assertEqual(changed.status_code, 200, changed.text)
        exported = self.client.get(self.path + '/export')
        self.assertEqual(exported.status_code, 200, exported.text)
        self.assertIn(content, exported.text)
        self.assertIn(cited['title'], exported.text)
        self.assertIn(cited['content_hash'], exported.text)
        self.assertIn(selected['title'], exported.text)
        self.assertEqual(exported.text.count('- [' + cited['id'] + ']'), 1)

    def test_inline_marker_cannot_export_a_source_from_another_proposal(self):
        other = self.make_proposal('Separate private proposal')
        private = self.add_source(other, 'Unattached private source title')
        saved = self.client.patch(self.path, json={'expected_revision': 1,
            'content': f"Unresolved marker [{private['id']}].", 'selected_source_ids': []})
        self.assertEqual(saved.status_code, 200, saved.text)
        exported = self.client.get(self.path + '/export')
        self.assertEqual(exported.status_code, 200, exported.text)
        self.assertNotIn(private['title'], exported.text)
        self.assertNotIn(private['content_hash'], exported.text)
        self.assertNotIn('## Sources', exported.text)


if __name__ == '__main__':
    unittest.main()
