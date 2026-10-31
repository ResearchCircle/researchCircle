"""Behavioral API checks using an isolated SQLite database, never production data."""
import hashlib
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from sqlalchemy import select, text, update

from services.api.app import create_app
from src.platform.database import Database, DatabaseConfigurationError, database_url_from_env
from src.platform.database.models import Source, User, LoginSession, Proposal, Membership, Invitation, utcnow
from src.platform.workflow.errors import WorkflowError
from src.platform.workflow.proposals import save_proposal


class WorkflowCoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.url = f"sqlite:///{Path(self.tmp.name) / 'core.db'}"
        self.app = create_app(self.url)
        self.app.state.db.create_schema()
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()
        self.app.state.db.engine.dispose()
        self.tmp.cleanup()

    def register(self, email='owner@example.test'):
        response = self.client.post('/api/v2/auth/register', json={
            'email': email, 'password': 'a sufficiently long password', 'name': email.split('@')[0]})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()['user']

    def proposal(self):
        self.register()
        team = self.client.post('/api/v2/teams', json={'name': 'Research'}).json()
        response = self.client.post('/api/v2/proposals', json={
            'team_id': team['id'], 'title': 'Proposal', 'content': 'Original'})
        self.assertEqual(response.status_code, 201, response.text)
        return team, response.json()

    def test_session_password_storage_login_and_logout(self):
        user = self.register()
        cookie = self.client.cookies.get('tbr_session')
        self.assertTrue(cookie)
        self.assertIn('HttpOnly', self.client.post('/api/v2/auth/login', json={
            'email': user['email'], 'password': 'a sufficiently long password'}).headers['set-cookie'])
        with self.app.state.db.session_factory() as session:
            stored = session.get(User, user['id'])
            self.assertNotEqual(stored.password_hash, 'a sufficiently long password')
            tokens = session.scalars(select(LoginSession)).all()
            self.assertTrue(all(token.token_hash != cookie for token in tokens))
        self.assertEqual(self.client.get('/api/v2/auth/me').json()['user']['id'], user['id'])
        self.assertEqual(self.client.post('/api/v2/auth/logout').status_code, 204)
        self.assertEqual(self.client.get('/api/v2/auth/me').status_code, 401)
        self.assertEqual(self.client.post('/api/v2/auth/login', json={
            'email': user['email'], 'password': 'wrong'}).status_code, 401)

    def test_revision_save_reopen_stale_conflict_and_export(self):
        _, proposal = self.proposal()
        path = '/api/v2/proposals/' + proposal['id']
        saved = self.client.patch(path, json={'expected_revision': 1, 'content': 'Saved'} )
        self.assertEqual(saved.status_code, 200, saved.text)
        self.assertEqual(saved.json()['revision'], 2)
        stale = self.client.patch(path, json={'expected_revision': 1, 'content': 'Lost'})
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(stale.json()['error']['code'], 'revision_conflict')
        reopened = TestClient(create_app(self.url))
        reopened.cookies.update(self.client.cookies)
        self.assertEqual(reopened.get(path).json()['content'], 'Saved')
        exported = reopened.get(path + '/export')
        self.assertEqual(exported.status_code, 200)
        self.assertIn('Saved', exported.text)
        reopened.app.state.db.engine.dispose()
        reopened.close()

    def test_invitation_viewer_membership_and_cross_team_denial(self):
        team, proposal = self.proposal()
        owner_cookies = dict(self.client.cookies)
        self.client.cookies.clear()
        self.register('viewer@example.test')
        viewer_cookies = dict(self.client.cookies)
        path = '/api/v2/proposals/' + proposal['id']
        self.assertEqual(self.client.get(path).status_code, 403)
        self.client.cookies.clear()
        self.client.cookies.update(owner_cookies)
        response = self.client.post(f"/api/v2/teams/{team['id']}/invitations", json={
            'email': 'viewer@example.test', 'role': 'viewer'})
        self.assertEqual(response.status_code, 201, response.text)
        self.client.cookies.clear()
        self.client.cookies.update(viewer_cookies)
        invitations = self.client.get('/api/v2/invitations').json()['items']
        accepted = self.client.post('/api/v2/invitations/' + invitations[0]['id'] + '/accept')
        self.assertEqual(accepted.status_code, 200, accepted.text)
        self.assertEqual(self.client.get(path).json()['role'], 'viewer')
        self.assertEqual(self.client.patch(path, json={'expected_revision': 1, 'content': 'bad'}).status_code, 403)
        self.assertEqual(self.client.post(path + '/sources', json={'title': 'x', 'text': 'x', 'origin': 'x'}).status_code, 403)

    def test_private_sources_require_attachment_and_selection_is_versioned(self):
        _, proposal = self.proposal()
        path = '/api/v2/proposals/' + proposal['id']
        source = self.client.post(path + '/sources', json={
            'title': 'Evidence', 'text': 'A fact.', 'origin': 'sample'}).json()
        self.assertEqual(source['content_hash'], hashlib.sha256(b'A fact.').hexdigest())
        self.assertFalse(source['is_public'])
        with self.app.state.db.session_factory() as session:
            public = Source(title='Public', text='Public fact', origin='sample', is_public=True,
                            content_hash=hashlib.sha256(b'Public fact').hexdigest())
            session.add(public)
            session.commit()
            public_id = public.id
        missing = self.client.patch(path, json={'expected_revision': 1, 'selected_source_ids': [public_id]})
        self.assertEqual(missing.status_code, 400)
        self.assertEqual(self.client.post(path + '/sources/attach', json={'source_id': public_id}).status_code, 201)
        saved = self.client.patch(path, json={'expected_revision': 1, 'selected_source_ids': [source['id'], public_id]})
        self.assertEqual(saved.status_code, 200, saved.text)
        self.assertEqual(len(saved.json()['selected_sources']), 2)
        second = self.client.post('/api/v2/proposals', json={
            'team_id': proposal['team_id'], 'title': 'Other', 'content': ''}).json()
        denied = self.client.post('/api/v2/proposals/' + second['id'] + '/sources/attach', json={'source_id': source['id']})
        self.assertEqual(denied.status_code, 404)
        listed = self.client.get(path + '/sources').json()['items']
        self.assertEqual(len(listed), 2)


    def test_expired_and_revoked_session_cookies_are_rejected(self):
        self.register()
        token = self.client.cookies.get('tbr_session')
        self.client.post('/api/v2/auth/logout')
        self.client.cookies.set('tbr_session', token)
        self.assertEqual(self.client.get('/api/v2/auth/me').status_code, 401)
        self.client.cookies.clear()
        self.client.post('/api/v2/auth/login', json={
            'email': 'owner@example.test', 'password': 'a sufficiently long password'})
        from datetime import timedelta
        with self.app.state.db.session_factory() as session:
            session.execute(update(LoginSession).values(expires_at=utcnow() - timedelta(seconds=1)))
            session.commit()
        self.assertEqual(self.client.get('/api/v2/auth/me').status_code, 401)

    def test_editor_can_save_but_cannot_manage_invitations(self):
        team, proposal = self.proposal()
        owner_cookies = dict(self.client.cookies)
        self.client.cookies.clear()
        self.register('editor@example.test')
        editor_cookies = dict(self.client.cookies)
        self.client.cookies.clear()
        self.client.cookies.update(owner_cookies)
        invited = self.client.post(f"/api/v2/teams/{team['id']}/invitations", json={
            'email': 'editor@example.test', 'role': 'editor'}).json()
        # Even a team owner cannot accept an invitation addressed to another user.
        self.assertEqual(self.client.post('/api/v2/invitations/' + invited['id'] + '/accept').status_code, 404)
        self.client.cookies.clear()
        self.client.cookies.update(editor_cookies)
        for _ in range(2):
            self.assertEqual(self.client.post('/api/v2/invitations/' + invited['id'] + '/accept').status_code, 200)
        saved = self.client.patch('/api/v2/proposals/' + proposal['id'], json={
            'expected_revision': 1, 'content': 'Editor save'})
        self.assertEqual(saved.status_code, 200, saved.text)
        self.assertEqual(self.client.post(f"/api/v2/teams/{team['id']}/invitations", json={
            'email': 'owner@example.test', 'role': 'viewer'}).status_code, 403)
        self.assertEqual(self.client.get('/api/v2/teams').json()['items'][0]['role'], 'editor')
        self.assertEqual(len(self.client.get(f"/api/v2/teams/{team['id']}").json()['members']), 2)
        self.assertEqual(len(self.client.get('/api/v2/proposals').json()['items']), 1)

    def test_simultaneous_invitation_acceptance_is_idempotent(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from unittest.mock import patch
        from sqlalchemy.orm import Session

        team, _ = self.proposal()
        owner_cookies = dict(self.client.cookies)
        self.client.cookies.clear()
        recipient = self.register('concurrent@example.test')
        recipient_cookies = dict(self.client.cookies)
        self.client.cookies.clear()
        self.client.cookies.update(owner_cookies)
        invited = self.client.post(f"/api/v2/teams/{team['id']}/invitations", json={
            'email': recipient['email'], 'role': 'editor'}).json()
        # Synchronize real reads so both SQLite transactions observe no membership.
        # The requests, inserts, constraints and commits all use the real database.
        both_read = Barrier(2)
        original_get = Session.get

        def synchronized_get(session, entity, identity, *args, **kwargs):
            row = original_get(session, entity, identity, *args, **kwargs)
            if entity is Membership and row is None:
                both_read.wait(timeout=5)
            return row

        def accept_request():
            with TestClient(self.app) as client:
                client.cookies.update(recipient_cookies)
                return client.post('/api/v2/invitations/' + invited['id'] + '/accept')

        with patch.object(Session, 'get', synchronized_get), ThreadPoolExecutor(max_workers=2) as executor:
            responses = list(executor.map(lambda _: accept_request(), range(2)))
        self.assertEqual([response.status_code for response in responses], [200, 200],
                         [response.text for response in responses])
        self.assertTrue(all(response.json() == {'team_id': team['id']} for response in responses))
        with self.app.state.db.session_factory() as session:
            memberships = session.scalars(select(Membership).where(
                Membership.team_id == team['id'], Membership.user_id == recipient['id'])).all()
            self.assertEqual(len(memberships), 1)
            self.assertEqual(memberships[0].role, 'editor')
            self.assertIsNotNone(session.get(Invitation, invited['id']).accepted_at)

    def test_invitation_acceptance_does_not_mask_unrelated_integrity_failure(self):
        team, _ = self.proposal()
        owner_cookies = dict(self.client.cookies)
        self.client.cookies.clear()
        recipient = self.register('failed-accept@example.test')
        recipient_cookies = dict(self.client.cookies)
        self.client.cookies.clear()
        self.client.cookies.update(owner_cookies)
        invited = self.client.post(f"/api/v2/teams/{team['id']}/invitations", json={
            'email': recipient['email'], 'role': 'editor'}).json()
        with self.app.state.db.engine.begin() as connection:
            connection.execute(text("CREATE TRIGGER reject_accept BEFORE UPDATE ON invitations BEGIN SELECT RAISE(ABORT, 'unrelated failure'); END"))
        self.client.cookies.clear()
        self.client.cookies.update(recipient_cookies)
        failed = self.client.post('/api/v2/invitations/' + invited['id'] + '/accept')
        self.assertEqual(failed.status_code, 503)
        self.assertEqual(failed.json()['error']['code'], 'database_unavailable')
        with self.app.state.db.session_factory() as session:
            self.assertIsNone(session.get(Membership, (team['id'], recipient['id'])))
            self.assertIsNone(session.get(Invitation, invited['id']).accepted_at)

    def test_independent_stale_session_cannot_overwrite_committed_save(self):
        _, proposal = self.proposal()
        with self.app.state.db.session_factory() as first, self.app.state.db.session_factory() as second:
            original = first.get(Proposal, proposal['id'])
            stale = second.get(Proposal, proposal['id'])
            save_proposal(first, original, original.revision, {'content': 'First writer'})
            with self.assertRaises(WorkflowError) as conflict:
                save_proposal(second, stale, stale.revision, {'content': 'Second writer'})
            self.assertEqual(conflict.exception.status, 409)
        self.assertEqual(self.client.get('/api/v2/proposals/' + proposal['id']).json()['content'], 'First writer')

    def test_failed_commit_returns_error_without_claiming_saved(self):
        _, proposal = self.proposal()
        with self.app.state.db.engine.begin() as connection:
            connection.execute(text("CREATE TRIGGER reject_save BEFORE UPDATE ON proposals BEGIN SELECT RAISE(ABORT, 'save failure'); END"))
        path = '/api/v2/proposals/' + proposal['id']
        failed = self.client.patch(path, json={'expected_revision': 1, 'content': 'Not persisted'})
        self.assertEqual(failed.status_code, 503)
        self.assertEqual(failed.json()['error']['code'], 'database_unavailable')
        self.assertEqual(self.client.get(path).json()['content'], 'Original')
        self.assertEqual(self.client.get(path).json()['revision'], 1)

    def test_cross_origin_authentication_and_writes_are_rejected(self):
        blocked = self.client.post('/api/v2/auth/register', headers={'Origin': 'https://other.example'}, json={
            'email': 'owner@example.test', 'name': 'Owner', 'password': 'a sufficiently long password'})
        self.assertEqual(blocked.status_code, 403)
        self.assertEqual(blocked.json()['error']['code'], 'origin_rejected')
        self.register()
        self.assertEqual(self.client.post('/api/v2/auth/logout', headers={'Origin': 'https://other.example'}).status_code, 403)
        self.assertEqual(self.client.get('/api/v2/auth/me').status_code, 200)
        self.assertEqual(self.client.post('/api/v2/teams', headers={'Origin': 'http://testserver'}, json={'name': 'Allowed'}).status_code, 201)

    def test_database_settings_require_explicit_postgresql_and_escape_password(self):
        with self.assertRaises(DatabaseConfigurationError):
            database_url_from_env({})
        with self.assertRaises(DatabaseConfigurationError):
            database_url_from_env({'TBR_DATABASE_URL': 'sqlite:///:memory:'})
        configured = database_url_from_env({'TBR_DB_HOST': 'db', 'TBR_DB_NAME': 'tbr',
            'TBR_DB_USER': 'tbr', 'TBR_DB_PASSWORD': 'special:@/password'})
        self.assertEqual(configured.drivername, 'postgresql+psycopg')
        self.assertEqual(configured.password, 'special:@/password')
        self.assertNotIn('special', repr(configured))
        with self.assertRaises(DatabaseConfigurationError):
            Database('postgresql+psycopg2://user:password@localhost/db')
        database = Database('postgresql://user:password@localhost/db')
        self.assertEqual(database.engine.dialect.driver, 'psycopg')
        database.engine.dispose()

    def test_migration_tracks_fresh_schema_and_repeat_upgrade_preserves_records(self):
        from alembic import command
        from alembic.config import Config
        from sqlalchemy import inspect
        database = Database(f"sqlite:///{Path(self.tmp.name) / 'migrations.db'}")
        config = Config(str(Path(__file__).resolve().parents[2] / 'alembic.ini'))
        with database.engine.begin() as connection:
            config.attributes['connection'] = connection
            command.upgrade(config, 'head')
        expected = {'users', 'login_sessions', 'teams', 'memberships', 'invitations',
                    'proposals', 'sources', 'proposal_sources', 'draft_jobs', 'alembic_version'}
        self.assertEqual(set(inspect(database.engine).get_table_names()), expected)
        with database.session_factory() as session:
            user = User(email='migration@example.test', name='Migration', password_hash='test-only-hash')
            session.add(user)
            session.commit()
            user_id = user.id
        with database.engine.begin() as connection:
            config.attributes['connection'] = connection
            command.upgrade(config, 'head')
            self.assertEqual(connection.scalar(text('SELECT version_num FROM alembic_version')), '0001_workflow_core')
            command.check(config)
        with database.session_factory() as session:
            self.assertEqual(session.get(User, user_id).email, 'migration@example.test')
        database.engine.dispose()


if __name__ == '__main__':
    unittest.main()
