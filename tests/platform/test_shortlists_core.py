"""Saved team curation uses real sources, membership and database constraints."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select, text

from services.api.app import create_app
from src.platform.database.models import Membership, Source
from src.platform.database.public_records import PublicRecord


class ShortlistsCoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.url = f"sqlite:///{Path(self.tmp.name) / 'shortlist.db'}"
        self.app = create_app(self.url)
        self.app.state.db.create_schema()
        self.client = TestClient(self.app)
        self.owner = self.register('owner@example.test')
        self.owner_cookies = dict(self.client.cookies)
        self.team = self.client.post('/api/v2/teams', json={'name': 'Research'}).json()
        self.path = '/api/v2/teams/' + self.team['id'] + '/shortlist'

    def tearDown(self):
        self.client.close()
        self.app.state.db.engine.dispose()
        self.tmp.cleanup()

    def register(self, email):
        response = self.client.post('/api/v2/auth/register', json={
            'email': email, 'name': email.split('@')[0], 'password': 'a sufficiently long password'})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()['user']

    def source(self, *, public=True, metadata=True, proposal_id=None, current=True,
               version='version-a', content='Checkable public evidence.', external_id=None):
        with self.app.state.db.session_factory() as session:
            source = Source(title='Sample paper', text=content, origin='https://example.test/paper',
                version=version, content_hash=hashlib.sha256(content.encode()).hexdigest(),
                is_public=public, proposal_id=proposal_id)
            session.add(source)
            session.flush()
            if metadata:
                session.add(PublicRecord(source_id=source.id, external_id=external_id or 'sample:' + source.id,
                    kind='paper', evidence_kind='synthetic', is_current=current, metadata_json={}))
            session.commit()
            return source.id

    def add(self, source_id, note=''):
        response = self.client.post(self.path, json={'source_id': source_id, 'note': note})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_saved_selection_duplicate_note_update_and_reopen(self):
        source_id = self.source()
        saved = self.add(source_id, 'Discuss with team')
        same = self.add(source_id, 'Do not overwrite previous note')
        self.assertEqual(saved, same)
        self.assertEqual(saved['source_id'], source_id)
        self.assertEqual(saved['version'], 'version-a')
        self.assertEqual(saved['created_by'], self.owner['id'])
        self.assertEqual(saved['snippet'], 'Checkable public evidence.')
        self.assertEqual(saved['kind'], 'paper')
        self.assertEqual(saved['evidence_kind'], 'synthetic')
        changed = self.client.patch(self.path + '/' + saved['id'], json={'note': 'Reviewed'})
        self.assertEqual(changed.status_code, 200, changed.text)
        self.assertEqual(changed.json()['note'], 'Reviewed')
        reopened_app = create_app(self.url)
        with TestClient(reopened_app) as reopened:
            reopened.cookies.update(self.owner_cookies)
            self.assertEqual(reopened.get(self.path).json()['items'], [changed.json()])
        reopened_app.state.db.engine.dispose()
        self.assertEqual(self.client.delete(self.path + '/' + saved['id']).status_code, 204)
        self.assertEqual(self.client.delete(self.path + '/' + saved['id']).status_code, 204)
        self.assertEqual(self.client.get(self.path).json(), {'items': []})

    def test_private_scoped_unresolved_and_missing_metadata_are_rejected(self):
        proposal = self.client.post('/api/v2/proposals', json={
            'team_id': self.team['id'], 'title': 'Private', 'content': ''}).json()
        rejected = [self.source(public=False), self.source(metadata=False),
                    self.source(public=True, proposal_id=proposal['id']), str(uuid4())]
        for source_id in rejected:
            response = self.client.post(self.path, json={'source_id': source_id})
            self.assertEqual(response.status_code, 404, response.text)
        self.assertEqual(self.client.get(self.path).json(), {'items': []})
        self.assertEqual(self.client.post(self.path, json={'source_id': 'unresolved-name'}).status_code, 422)
        self.assertEqual(self.client.post(self.path, json={'source_id': self.source(), 'note': 'x' * 2001}).status_code, 422)

    def test_historical_source_reference_survives_new_current_version(self):
        source_id = self.source()
        saved = self.add(source_id)
        with self.app.state.db.session_factory() as session:
            record = session.get(PublicRecord, source_id)
            external_id = record.external_id
            record.is_current = False
            session.commit()
        self.source(version='version-b', content='Revised public evidence.', external_id=external_id)
        self.assertEqual(self.client.get(self.path).json()['items'], [saved])
        self.assertEqual(self.add(source_id), saved)

    def test_viewer_reads_editor_edits_and_outsider_cannot_access(self):
        saved = self.add(self.source())
        self.client.cookies.clear()
        viewer = self.register('viewer@example.test')
        viewer_cookies = dict(self.client.cookies)
        self.client.cookies.clear()
        editor = self.register('editor@example.test')
        editor_cookies = dict(self.client.cookies)
        with self.app.state.db.session_factory() as session:
            session.add_all([Membership(team_id=self.team['id'], user_id=viewer['id'], role='viewer'),
                             Membership(team_id=self.team['id'], user_id=editor['id'], role='editor')])
            session.commit()
        self.client.cookies.clear()
        self.client.cookies.update(viewer_cookies)
        self.assertEqual(len(self.client.get(self.path).json()['items']), 1)
        self.assertEqual(self.client.post(self.path, json={'source_id': saved['source_id']}).status_code, 403)
        self.assertEqual(self.client.patch(self.path + '/' + saved['id'], json={'note': 'No'}).status_code, 403)
        self.assertEqual(self.client.delete(self.path + '/' + saved['id']).status_code, 403)
        self.client.cookies.clear()
        self.client.cookies.update(editor_cookies)
        self.assertEqual(self.client.patch(self.path + '/' + saved['id'], json={'note': 'Editor note'}).status_code, 200)
        self.assertEqual(self.client.delete(self.path + '/' + saved['id']).status_code, 204)
        self.assertEqual(self.client.post(self.path, json={'source_id': saved['source_id']}).status_code, 201)
        self.client.cookies.clear()
        self.register('outsider@example.test')
        self.assertEqual(self.client.get(self.path).status_code, 403)
        self.assertEqual(self.client.post(self.path, json={'source_id': saved['source_id']}).status_code, 403)

    def test_malformed_existing_entry_cannot_expose_private_source(self):
        from src.platform.database.shortlists import TeamShortlistEntry
        private = self.source(public=False)
        with self.app.state.db.session_factory() as session:
            session.add(TeamShortlistEntry(team_id=self.team['id'], source_id=private, created_by=self.owner['id'], note=''))
            session.commit()
        self.assertEqual(self.client.get(self.path).json(), {'items': []})

    def test_cross_team_delete_does_not_remove_entry(self):
        saved = self.add(self.source())
        other = self.client.post('/api/v2/teams', json={'name': 'Other'}).json()
        other_path = '/api/v2/teams/' + other['id'] + '/shortlist/' + saved['id']
        self.assertEqual(self.client.delete(other_path).status_code, 404)
        self.assertEqual(self.client.patch(other_path, json={'note': 'No'}).status_code, 404)
        self.assertEqual(len(self.client.get(self.path).json()['items']), 1)

    def test_concurrent_add_is_one_stored_entry_with_original_note(self):
        from src.platform.database.shortlists import TeamShortlistEntry
        source_id = self.source()
        start = Barrier(2)

        def add(note):
            with TestClient(self.app) as client:
                client.cookies.update(self.owner_cookies)
                start.wait(timeout=5)
                return client.post(self.path, json={'source_id': source_id, 'note': note})

        with ThreadPoolExecutor(max_workers=2) as executor:
            responses = list(executor.map(add, ('First note', 'Second note')))
        self.assertEqual([response.status_code for response in responses], [201, 201], [r.text for r in responses])
        self.assertEqual(responses[0].json(), responses[1].json())
        with self.app.state.db.session_factory() as session:
            self.assertEqual(len(session.scalars(select(TeamShortlistEntry)).all()), 1)


    def test_public_record_baseline_upgrade_preserves_curated_source(self):
        from alembic import command
        from alembic.config import Config
        from src.platform.database import Database
        from src.platform.database.models import Team, User
        from src.platform.database.shortlists import TeamShortlistEntry
        database = Database(f"sqlite:///{Path(self.tmp.name) / 'upgrade.db'}")
        config = Config(str(Path(__file__).resolve().parents[2] / 'alembic.ini'))
        with database.engine.begin() as connection:
            config.attributes['connection'] = connection
            command.upgrade(config, '0003_public_records')
        with database.session_factory() as session:
            user = User(email='migration@example.test', name='Existing', password_hash='test-only-hash')
            team = Team(name='Existing team')
            source = Source(title='Existing public source', text='Original evidence.', version='one', origin='sample',
                content_hash=hashlib.sha256(b'Original evidence.').hexdigest(), is_public=True)
            session.add_all([user, team, source])
            session.flush()
            session.add(PublicRecord(source_id=source.id, external_id='migration-paper', kind='paper',
                evidence_kind='synthetic', is_current=True, metadata_json={}))
            session.commit()
            user_id, team_id, source_id = user.id, team.id, source.id
        with database.engine.begin() as connection:
            config.attributes['connection'] = connection
            command.upgrade(config, 'head')
        with database.session_factory() as session:
            entry = TeamShortlistEntry(team_id=team_id, source_id=source_id, created_by=user_id, note='Keep this')
            session.add(entry)
            session.commit()
            entry_id = entry.id
        with database.engine.begin() as connection:
            config.attributes['connection'] = connection
            command.upgrade(config, 'head')
            command.check(config)
            self.assertEqual(connection.scalar(text('SELECT version_num FROM alembic_version')), '0004_team_shortlist')
        with database.session_factory() as session:
            self.assertEqual(session.get(TeamShortlistEntry, entry_id).note, 'Keep this')
            self.assertEqual(session.get(Source, source_id).text, 'Original evidence.')
        database.engine.dispose()


if __name__ == '__main__':
    unittest.main()
