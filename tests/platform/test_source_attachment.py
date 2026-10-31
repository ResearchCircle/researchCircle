"""Explicit public attachment is atomic for teammates and preserves scope guards."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import event, select, text

from services.api.app import create_app
from src.platform.database.models import ProposalSource, Source


class SourceAttachmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.app = create_app(f"sqlite:///{Path(self.tmp.name) / 'attachments.db'}")
        self.app.state.db.create_schema()
        self.client = TestClient(self.app)
        self.register('owner@example.test')
        self.owner_cookies = dict(self.client.cookies)
        self.team = self.client.post('/api/v2/teams', json={'name': 'Evidence team'}).json()
        proposal = self.client.post('/api/v2/proposals', json={
            'team_id': self.team['id'], 'title': 'Evidence study', 'content': ''}).json()
        self.proposal_id = proposal['id']
        self.path = '/api/v2/proposals/' + self.proposal_id + '/sources'
        self.client.cookies.clear()
        self.register('editor@example.test')
        self.editor_cookies = dict(self.client.cookies)
        self.client.cookies.clear()
        self.client.cookies.update(self.owner_cookies)
        invite = self.client.post('/api/v2/teams/' + self.team['id'] + '/invitations', json={
            'email': 'editor@example.test', 'role': 'editor'}).json()
        with TestClient(self.app) as editor:
            editor.cookies.update(self.editor_cookies)
            self.assertEqual(editor.post('/api/v2/invitations/' + invite['id'] + '/accept').status_code, 200)

    def tearDown(self):
        self.client.close()
        self.app.state.db.engine.dispose()
        self.tmp.cleanup()

    def register(self, email):
        result = self.client.post('/api/v2/auth/register', json={
            'email': email, 'name': email.split('@')[0], 'password': 'a sufficiently long password'})
        self.assertEqual(result.status_code, 201, result.text)

    def source(self, public=True, proposal_id=None):
        with self.app.state.db.session_factory() as session:
            source = Source(title='Synthetic public evidence', origin='https://example.test/evidence',
                text='A checkable fact.', content_hash=hashlib.sha256(b'A checkable fact.').hexdigest(),
                is_public=public, proposal_id=proposal_id)
            session.add(source)
            session.commit()
            return source.id

    def test_competing_teammate_attachments_create_one_link(self):
        source_id = self.source()
        competing_inserts = Barrier(2)

        def synchronize_insert(_connection, _cursor, statement, _parameters, _context, _many):
            # Both requests reach the actual INSERT before either can commit.
            if statement.lstrip().upper().startswith('INSERT INTO PROPOSAL_SOURCES'):
                competing_inserts.wait(timeout=5)

        def attach(cookies):
            with TestClient(self.app) as client:
                client.cookies.update(cookies)
                return client.post(self.path + '/attach', json={'source_id': source_id})

        event.listen(self.app.state.db.engine, 'before_cursor_execute', synchronize_insert)
        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                responses = list(executor.map(attach, (self.owner_cookies, self.editor_cookies)))
        finally:
            event.remove(self.app.state.db.engine, 'before_cursor_execute', synchronize_insert)
        self.assertEqual([response.status_code for response in responses], [201, 201], [r.text for r in responses])
        self.assertEqual(responses[0].json(), responses[1].json())
        with self.app.state.db.session_factory() as session:
            links = session.scalars(select(ProposalSource).where(ProposalSource.proposal_id == self.proposal_id)).all()
            self.assertEqual(len(links), 1)
            self.assertEqual(links[0].source_id, source_id)
        duplicate = self.client.post(self.path + '/attach', json={'source_id': source_id})
        self.assertEqual(duplicate.status_code, 201)
        self.assertEqual(duplicate.json(), responses[0].json())

    def test_private_scoped_and_missing_sources_stay_unavailable(self):
        for source_id in (self.source(public=False), self.source(proposal_id=self.proposal_id), str(uuid4())):
            response = self.client.post(self.path + '/attach', json={'source_id': source_id})
            self.assertEqual(response.status_code, 404, response.text)
        self.assertEqual(self.client.get(self.path).json(), {'items': []})

    def test_unrelated_insert_failure_is_not_suppressed(self):
        source_id = self.source()
        with self.app.state.db.engine.begin() as connection:
            connection.execute(text("CREATE TRIGGER reject_link BEFORE INSERT ON proposal_sources BEGIN SELECT RAISE(ABORT, 'unrelated link failure'); END"))
        failed = self.client.post(self.path + '/attach', json={'source_id': source_id})
        self.assertEqual(failed.status_code, 503, failed.text)
        self.assertEqual(failed.json()['error']['code'], 'database_unavailable')
        self.assertEqual(self.client.get(self.path).json(), {'items': []})


if __name__ == '__main__':
    unittest.main()
