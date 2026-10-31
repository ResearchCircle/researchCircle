"""Owner membership management and invitation replay use real persisted requests."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import select

from services.api.app import create_app
from src.platform.database.models import Membership, Source


class TeamManagementTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.app = create_app(f"sqlite:///{Path(self.tmp.name) / 'teams.db'}")
        self.app.state.db.create_schema()
        self.client = TestClient(self.app)
        self.owner = self.register('owner@example.test')
        self.owner_cookies = dict(self.client.cookies)
        self.team = self.client.post('/api/v2/teams', json={'name': 'Research'}).json()
        self.path = '/api/v2/teams/' + self.team['id']
        self.client.cookies.clear()
        self.editor = self.register('editor@example.test')
        self.editor_cookies = dict(self.client.cookies)
        self.as_owner()
        self.invitation = self.invite()
        self.as_editor()
        self.assertEqual(self.client.post('/api/v2/invitations/' + self.invitation['id'] + '/accept').status_code, 200)
        self.as_owner()

    def tearDown(self):
        self.client.close()
        self.app.state.db.engine.dispose()
        self.tmp.cleanup()

    def register(self, email):
        response = self.client.post('/api/v2/auth/register', json={
            'email': email, 'name': email.split('@')[0], 'password': 'a sufficiently long password'})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()['user']

    def as_owner(self):
        self.client.cookies.clear()
        self.client.cookies.update(self.owner_cookies)

    def as_editor(self):
        self.client.cookies.clear()
        self.client.cookies.update(self.editor_cookies)

    def invite(self, role='editor'):
        result = self.client.post(self.path + '/invitations', json={'email': self.editor['email'], 'role': role})
        self.assertEqual(result.status_code, 201, result.text)
        return result.json()

    def test_owner_updates_role_removes_member_and_reinvite_is_explicit(self):
        member_path = self.path + '/members/' + self.editor['id']
        changed = self.client.patch(member_path, json={'role': 'viewer'})
        self.assertEqual(changed.status_code, 200, changed.text)
        self.assertEqual(changed.json()['role'], 'viewer')
        self.assertEqual(changed.json()['email'], self.editor['email'])
        self.assertEqual(self.client.delete(member_path).status_code, 204)
        self.assertEqual(self.client.delete(member_path).status_code, 204)
        self.as_editor()
        replay = self.client.post('/api/v2/invitations/' + self.invitation['id'] + '/accept')
        self.assertEqual(replay.status_code, 409, replay.text)
        self.assertEqual(replay.json()['error']['code'], 'invitation_already_used')
        self.assertEqual(self.client.get(self.path).status_code, 403)
        self.as_owner()
        renewed = self.invite('viewer')
        self.assertEqual(renewed['id'], self.invitation['id'])
        self.as_editor()
        self.assertEqual(len(self.client.get('/api/v2/invitations').json()['items']), 1)
        self.assertEqual(self.client.post('/api/v2/invitations/' + renewed['id'] + '/accept').status_code, 200)
        self.assertEqual(self.client.get(self.path).json()['role'], 'viewer')

    def test_only_owner_can_manage_existing_team_members(self):
        self.as_editor()
        target = self.path + '/members/' + self.owner['id']
        self.assertEqual(self.client.patch(target, json={'role': 'viewer'}).status_code, 403)
        self.assertEqual(self.client.delete(target).status_code, 403)
        other = self.client.post('/api/v2/teams', json={'name': 'Other'}).json()
        other_target = '/api/v2/teams/' + other['id'] + '/members/' + self.owner['id']
        self.assertEqual(self.client.patch(other_target, json={'role': 'editor'}).status_code, 404)
        self.assertEqual(self.client.delete(other_target).status_code, 204)
        self.as_owner()
        members = self.client.get(self.path).json()['members']
        self.assertEqual({row['id'] for row in members}, {self.owner['id'], self.editor['id']})
        self.client.cookies.clear()
        self.register('outsider@example.test')
        self.assertEqual(self.client.delete(self.path + '/members/' + self.editor['id']).status_code, 403)

    def test_last_owner_cannot_be_demoted_or_removed_and_other_owner_can_manage(self):
        own_path = self.path + '/members/' + self.owner['id']
        for response in (self.client.patch(own_path, json={'role': 'editor'}), self.client.delete(own_path)):
            self.assertEqual(response.status_code, 409, response.text)
            self.assertEqual(response.json()['error']['code'], 'last_owner')
        promoted = self.client.patch(self.path + '/members/' + self.editor['id'], json={'role': 'owner'})
        self.assertEqual(promoted.status_code, 200, promoted.text)
        self.assertEqual(self.client.patch(own_path, json={'role': 'viewer'}).status_code, 200)
        self.assertEqual(self.client.delete(self.path + '/members/' + self.editor['id']).status_code, 403)
        self.as_editor()
        self.assertEqual(self.client.delete(own_path).status_code, 204)
        self.assertEqual(len(self.client.get(self.path).json()['members']), 1)

    def test_concurrent_self_demotions_preserve_one_owner(self):
        self.assertEqual(self.client.patch(self.path + '/members/' + self.editor['id'], json={'role': 'owner'}).status_code, 200)
        start = Barrier(2)

        def demote(args):
            user, cookies = args
            with TestClient(self.app) as client:
                client.cookies.update(cookies)
                start.wait(timeout=5)
                return client.patch(self.path + '/members/' + user['id'], json={'role': 'editor'})

        with ThreadPoolExecutor(max_workers=2) as executor:
            responses = list(executor.map(demote, ((self.owner, self.owner_cookies), (self.editor, self.editor_cookies))))
        self.assertEqual(sorted(response.status_code for response in responses), [200, 409], [r.text for r in responses])
        with self.app.state.db.session_factory() as session:
            owners = session.scalars(select(Membership).where(Membership.team_id == self.team['id'], Membership.role == 'owner')).all()
            self.assertEqual(len(owners), 1)

    def test_concurrent_removal_and_old_invitation_replay_cannot_restore_membership(self):
        start = Barrier(2)

        def remove():
            with TestClient(self.app) as client:
                client.cookies.update(self.owner_cookies)
                start.wait(timeout=5)
                return client.delete(self.path + '/members/' + self.editor['id'])

        def replay():
            with TestClient(self.app) as client:
                client.cookies.update(self.editor_cookies)
                start.wait(timeout=5)
                return client.post('/api/v2/invitations/' + self.invitation['id'] + '/accept')

        with ThreadPoolExecutor(max_workers=2) as executor:
            removed = executor.submit(remove)
            replayed = executor.submit(replay)
            self.assertEqual(removed.result().status_code, 204)
            replay_response = replayed.result()
            self.assertIn(replay_response.status_code, (200, 409), replay_response.text)
        with self.app.state.db.session_factory() as session:
            self.assertIsNone(session.get(Membership, (self.team['id'], self.editor['id'])))

    def test_replay_after_demotion_does_not_restore_invitation_role(self):
        self.assertEqual(self.client.patch(self.path + '/members/' + self.editor['id'], json={'role': 'viewer'}).status_code, 200)
        self.as_editor()
        self.assertEqual(self.client.post('/api/v2/invitations/' + self.invitation['id'] + '/accept').status_code, 200)
        self.assertEqual(self.client.get(self.path).json()['role'], 'viewer')

    def test_malformed_public_proposal_source_cannot_cross_team_boundary(self):
        proposal = self.client.post('/api/v2/proposals', json={'team_id': self.team['id'], 'title': 'Private study', 'content': ''}).json()
        original_path = '/api/v2/proposals/' + proposal['id']
        source = self.client.post(original_path + '/sources', json={'title': 'Private evidence', 'text': 'Private fact.', 'origin': 'private'}).json()
        with self.app.state.db.session_factory() as session:
            session.get(Source, source['id']).is_public = True
            session.commit()
        self.assertEqual(len(self.client.get(original_path + '/sources').json()['items']), 1)
        self.client.cookies.clear()
        self.register('outsider-source@example.test')
        team = self.client.post('/api/v2/teams', json={'name': 'Separate'}).json()
        other = self.client.post('/api/v2/proposals', json={'team_id': team['id'], 'title': 'Other study', 'content': ''}).json()
        other_path = '/api/v2/proposals/' + other['id']
        attached = self.client.post(other_path + '/sources/attach', json={'source_id': source['id']})
        self.assertEqual(attached.status_code, 404, attached.text)
        self.assertEqual(self.client.get(other_path + '/sources').json(), {'items': []})
        self.assertEqual(self.client.get(original_path + '/sources').status_code, 403)


if __name__ == '__main__':
    unittest.main()
