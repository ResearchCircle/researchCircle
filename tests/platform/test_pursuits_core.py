"""Manual workflow checks against real isolated SQLAlchemy transactions."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import select, text

from services.api.app import create_app


class PursuitsCoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.app = create_app(f"sqlite:///{Path(self.tmp.name) / 'pursuits.db'}")
        self.app.state.db.create_schema()
        self.client = TestClient(self.app)
        self.owner = self.register('owner@example.test')
        self.owner_cookies = dict(self.client.cookies)
        self.team = self.client.post('/api/v2/teams', json={'name': 'Research'}).json()
        self.proposal = self.client.post('/api/v2/proposals', json={
            'team_id': self.team['id'], 'title': 'Sensor study', 'content': ''}).json()
        self.path = '/api/v2/proposals/' + self.proposal['id']

    def tearDown(self):
        self.client.close()
        self.app.state.db.engine.dispose()
        self.tmp.cleanup()

    def register(self, email):
        result = self.client.post('/api/v2/auth/register', json={
            'email': email, 'name': email.split('@')[0], 'password': 'a sufficiently long password'})
        self.assertEqual(result.status_code, 201, result.text)
        return result.json()['user']

    def opportunity(self, **changes):
        result = self.client.post('/api/v2/opportunities', json={
            'team_id': self.team['id'], 'title': 'Manual opportunity', **changes})
        self.assertEqual(result.status_code, 201, result.text)
        return result.json()

    def pursuit(self, state='submitted', opportunity_id=None):
        result = self.client.put(self.path + '/pursuit', json={'state': state, 'opportunity_id': opportunity_id})
        self.assertEqual(result.status_code, 200, result.text)
        return result.json()['pursuit']

    def test_manual_opportunity_preserves_unknowns_and_timezone_validation(self):
        unknown = self.opportunity()
        self.assertEqual(unknown['eligibility'], 'unknown')
        self.assertIsNone(unknown['deadline'])
        self.assertIsNone(unknown['deadline_timezone'])
        known = self.opportunity(source_url='https://example.test/funding', deadline='2027-01-15T17:00:00-05:00',
                                 deadline_timezone='America/New_York', eligibility='eligible', notes='Manually confirmed')
        self.assertTrue(known['deadline'].startswith('2027-01-15T22:00:00'))
        self.assertEqual(known['deadline_timezone'], 'America/New_York')
        self.assertEqual(known['eligibility'], 'eligible')
        invalid = [{'deadline': '2027-01-15T17:00:00'}, {'source_url': 'file:///tmp/private'},
                   {'deadline_timezone': 'MadeUp/Zone'}, {'eligibility': 'probably'}, {'title': '  '}]
        for fields in invalid:
            response = self.client.post('/api/v2/opportunities', json={
                'team_id': self.team['id'], 'title': 'Invalid', **fields})
            self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(len(self.client.get('/api/v2/opportunities').json()['items']), 2)

    def test_pursuit_history_linkage_and_outcome_retry_survive_reopening(self):
        opportunity = self.opportunity()
        self.assertEqual(self.client.get(self.path + '/pursuit').json(), {'pursuit': None})
        self.pursuit('draft', opportunity['id'])
        self.pursuit('collaborating', opportunity['id'])
        submitted = self.pursuit('submitted', opportunity['id'])
        self.assertEqual([row['to_state'] for row in submitted['history']], ['draft', 'collaborating', 'submitted'])
        self.assertEqual(self.client.get(self.path + '/pursuit').json()['pursuit']['state'], 'submitted')
        body = {'outcome': 'won', 'idempotency_key': 'award-1', 'award_reference': 'Grant 123'}
        first = self.client.post(self.path + '/outcomes', json=body)
        self.assertEqual(first.status_code, 201, first.text)
        second = self.client.post(self.path + '/outcomes', json=body)
        self.assertEqual(second.status_code, 201, second.text)
        self.assertEqual(first.json(), second.json())
        self.assertEqual(first.json()['outcome'], 'won')
        self.assertEqual(first.json()['pursuit_id'], submitted['id'])
        self.assertEqual(self.client.get(self.path + '/pursuit').json()['pursuit']['state'], 'won')
        self.assertEqual(len(self.client.get(self.path + '/outcomes').json()['items']), 1)
        reopened = TestClient(create_app(f"sqlite:///{Path(self.tmp.name) / 'pursuits.db'}"))
        reopened.cookies.update(self.owner_cookies)
        self.assertEqual(reopened.post(self.path + '/outcomes', json=body).json(), first.json())
        reopened.app.state.db.engine.dispose()
        reopened.close()

    def test_outcomes_require_submission_and_keys_cannot_change_payload(self):
        self.pursuit('draft')
        body = {'outcome': 'lost', 'idempotency_key': 'result-1'}
        self.assertEqual(self.client.post(self.path + '/outcomes', json=body).status_code, 409)
        self.pursuit('submitted')
        self.assertEqual(self.client.post(self.path + '/outcomes', json=body).status_code, 201)
        changed = self.client.post(self.path + '/outcomes', json={**body, 'award_reference': 'different'})
        self.assertEqual(changed.status_code, 409)
        self.assertEqual(changed.json()['error']['code'], 'idempotency_conflict')
        self.assertEqual(self.client.post(self.path + '/outcomes', json={**body, 'idempotency_key': 'result-2'}).status_code, 409)
        self.assertEqual(self.client.put(self.path + '/pursuit', json={'state': 'submitted', 'opportunity_id': None}).status_code, 409)

    def test_cross_team_opportunity_link_and_outsider_access_are_denied(self):
        other_team = self.client.post('/api/v2/teams', json={'name': 'Other team'}).json()
        other = self.client.post('/api/v2/opportunities', json={'team_id': other_team['id'], 'title': 'Other'}).json()
        link = self.client.put(self.path + '/pursuit', json={'state': 'draft', 'opportunity_id': other['id']})
        self.assertEqual(link.status_code, 400, link.text)
        self.opportunity()
        self.client.cookies.clear()
        self.register('outsider@example.test')
        self.assertEqual(self.client.get('/api/v2/opportunities').json(), {'items': []})
        self.assertEqual(self.client.get(self.path + '/pursuit').status_code, 403)
        self.assertEqual(self.client.get(self.path + '/outcomes').status_code, 403)
        self.assertEqual(self.client.post('/api/v2/opportunities', json={'team_id': self.team['id'], 'title': 'Forbidden'}).status_code, 403)

    def test_viewer_reads_but_cannot_create_link_or_record(self):
        self.opportunity()
        self.pursuit('submitted')
        self.client.cookies.clear()
        viewer = self.register('viewer@example.test')
        viewer_cookies = dict(self.client.cookies)
        self.client.cookies.clear()
        self.client.cookies.update(self.owner_cookies)
        invite = self.client.post('/api/v2/teams/' + self.team['id'] + '/invitations', json={
            'email': viewer['email'], 'role': 'viewer'}).json()
        self.client.cookies.clear()
        self.client.cookies.update(viewer_cookies)
        self.client.post('/api/v2/invitations/' + invite['id'] + '/accept')
        self.assertEqual(self.client.get(self.path + '/pursuit').status_code, 200)
        self.assertEqual(self.client.get(self.path + '/outcomes').status_code, 200)
        self.assertEqual(len(self.client.get('/api/v2/opportunities').json()['items']), 1)
        self.assertEqual(self.client.put(self.path + '/pursuit', json={'state': 'draft', 'opportunity_id': None}).status_code, 403)
        self.assertEqual(self.client.post(self.path + '/outcomes', json={'outcome': 'won', 'idempotency_key': 'x'}).status_code, 403)
        self.assertEqual(self.client.post('/api/v2/opportunities', json={'team_id': self.team['id'], 'title': 'No'}).status_code, 403)

    def test_concurrent_same_key_has_one_outcome_and_one_terminal_transition(self):
        from src.platform.database.pursuits import Outcome, PursuitHistory
        pursuit = self.pursuit('submitted')
        start = Barrier(2)
        body = {'outcome': 'withdrawn', 'idempotency_key': 'concurrent'}

        def post_outcome():
            with TestClient(self.app) as client:
                client.cookies.update(self.owner_cookies)
                start.wait(timeout=5)
                return client.post(self.path + '/outcomes', json=body)

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: post_outcome(), range(2)))
        self.assertEqual([response.status_code for response in results], [201, 201], [r.text for r in results])
        self.assertEqual(results[0].json(), results[1].json())
        with self.app.state.db.session_factory() as session:
            self.assertEqual(len(session.scalars(select(Outcome).where(Outcome.pursuit_id == pursuit['id'])).all()), 1)
            self.assertEqual(len(session.scalars(select(PursuitHistory).where(
                PursuitHistory.pursuit_id == pursuit['id'], PursuitHistory.to_state == 'withdrawn')).all()), 1)


    def test_failed_terminal_update_rolls_back_outcome_and_can_retry(self):
        self.pursuit('submitted')
        with self.app.state.db.engine.begin() as connection:
            connection.execute(text("CREATE TRIGGER reject_terminal BEFORE UPDATE ON pursuits WHEN NEW.state IN ('won','lost','withdrawn') BEGIN SELECT RAISE(ABORT, 'terminal failure'); END"))
        body = {'outcome': 'won', 'idempotency_key': 'retry-after-error'}
        failed = self.client.post(self.path + '/outcomes', json=body)
        self.assertEqual(failed.status_code, 503, failed.text)
        self.assertEqual(self.client.get(self.path + '/outcomes').json(), {'items': []})
        unchanged = self.client.get(self.path + '/pursuit').json()['pursuit']
        self.assertEqual(unchanged['state'], 'submitted')
        self.assertEqual([row['to_state'] for row in unchanged['history']], ['submitted'])
        with self.app.state.db.engine.begin() as connection:
            connection.execute(text('DROP TRIGGER reject_terminal'))
        self.assertEqual(self.client.post(self.path + '/outcomes', json=body).status_code, 201)

    def test_concurrent_changed_payload_has_one_success_and_one_conflict(self):
        self.pursuit('submitted')
        start = Barrier(2)

        def post_outcome(state):
            with TestClient(self.app) as client:
                client.cookies.update(self.owner_cookies)
                start.wait(timeout=5)
                return client.post(self.path + '/outcomes', json={
                    'outcome': state, 'idempotency_key': 'same-key-different-payload'})

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(post_outcome, ('won', 'lost')))
        self.assertEqual(sorted(response.status_code for response in results), [201, 409], [r.text for r in results])
        rejected = next(response for response in results if response.status_code == 409)
        self.assertEqual(rejected.json()['error']['code'], 'idempotency_conflict')
        self.assertEqual(len(self.client.get(self.path + '/outcomes').json()['items']), 1)

    def test_concurrent_initial_pursuit_creation_is_one_record(self):
        start = Barrier(2)

        def put_pursuit():
            with TestClient(self.app) as client:
                client.cookies.update(self.owner_cookies)
                start.wait(timeout=5)
                return client.put(self.path + '/pursuit', json={'state': 'submitted', 'opportunity_id': None})

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: put_pursuit(), range(2)))
        self.assertEqual([response.status_code for response in results], [200, 200], [r.text for r in results])
        self.assertEqual(results[0].json()['pursuit']['id'], results[1].json()['pursuit']['id'])
        self.assertEqual(len(self.client.get(self.path + '/pursuit').json()['pursuit']['history']), 1)

    def test_upgrade_from_core_baseline_preserves_existing_proposal(self):
        from alembic import command
        from alembic.config import Config
        from src.platform.database import Database
        from src.platform.database.models import Proposal, Team
        database = Database(f"sqlite:///{Path(self.tmp.name) / 'upgrade.db'}")
        config = Config(str(Path(__file__).resolve().parents[2] / 'alembic.ini'))
        with database.engine.begin() as connection:
            config.attributes['connection'] = connection
            command.upgrade(config, '0001_workflow_core')
        with database.session_factory() as session:
            team = Team(name='Existing team')
            session.add(team)
            session.flush()
            proposal = Proposal(team_id=team.id, title='Existing proposal', content='Preserved text')
            session.add(proposal)
            session.commit()
            proposal_id = proposal.id
        with database.engine.begin() as connection:
            config.attributes['connection'] = connection
            command.upgrade(config, 'head')
            command.upgrade(config, 'head')
            command.check(config)
            self.assertEqual(connection.scalar(text('SELECT version_num FROM alembic_version')), '0002_pursuits')
        with database.session_factory() as session:
            self.assertEqual(session.get(Proposal, proposal_id).content, 'Preserved text')
            self.assertEqual(session.get(Proposal, proposal_id).revision, 1)
        database.engine.dispose()


if __name__ == '__main__':
    unittest.main()
