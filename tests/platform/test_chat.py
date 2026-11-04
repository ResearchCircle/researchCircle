import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from services.api.app import create_app
from src.platform.chatbot.service import ResearchChatService
from src.platform.database import Database
from src.platform.database.models import Proposal, ProposalSource, Source, Team, User
from src.platform.database.public_records import PublicRecord
from src.platform.drafting.types import SourceSnapshot
from src.platform.models.fixtures import ExtractiveFixtureProvider


class ResearchChatTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / 'test_chat.db'
        self.db_url = f'sqlite:///{db_path}'
        self.app = create_app(self.db_url)
        self.app.state.db.create_schema()
        self.provider = ExtractiveFixtureProvider()
        self.app.state.chat_service = ResearchChatService(self.provider)
        self.client = TestClient(self.app)

        with self.app.state.db.session_factory() as session:
            # Users
            self.user = User(id=str(uuid4()), email='researcher@rit.edu', name='Dr. Researcher', password_hash='hash')
            self.other_user = User(id=str(uuid4()), email='other@rit.edu', name='Dr. Other', password_hash='hash')
            session.add(self.user)
            session.add(self.other_user)

            # Teams
            self.team = Team(id=str(uuid4()), name='AI Systems Lab')
            self.other_team = Team(id=str(uuid4()), name='Secret Lab')
            session.add(self.team)
            session.add(self.other_team)
            session.flush()

            # Membership
            from src.platform.database.models import Membership
            session.add(Membership(user_id=self.user.id, team_id=self.team.id, role='owner'))
            session.add(Membership(user_id=self.other_user.id, team_id=self.other_team.id, role='owner'))

            # Sources
            self.public_source = Source(
                id=str(uuid4()),
                version='1',
                content_hash='hash1',
                title='Public Sensor Paper',
                origin='https://doi.org/10.1000/sensors',
                text='Environmental sensing nodes sample soil temperature every ten minutes.',
                is_public=True,
                proposal_id=None
            )
            session.add(self.public_source)
            session.add(PublicRecord(
                source_id=self.public_source.id,
                external_id='paper:sensor',
                kind='paper',
                evidence_kind='public',
                is_current=True,
                metadata_json={}
            ))

            # Proposal in team 1
            self.proposal = Proposal(
                id=str(uuid4()),
                team_id=self.team.id,
                title='AgriSensors Grant',
                content='Initial proposal text',
                revision=1,
                selected_source_ids=[self.public_source.id]
            )
            session.add(self.proposal)
            session.flush()
            session.add(ProposalSource(proposal_id=self.proposal.id, source_id=self.public_source.id))

            # Proposal in team 2 (private context)
            self.other_proposal = Proposal(
                id=str(uuid4()),
                team_id=self.other_team.id,
                title='Secret Defense Proposal',
                content='Confidential content',
                revision=1,
                selected_source_ids=[]
            )
            session.add(self.other_proposal)
            session.commit()

    def tearDown(self):
        self.app.state.db.engine.dispose()
        self.temp_dir.cleanup()

    def test_meta_chat_provider_defaults_to_muse_and_requires_credentials(self):
        with patch.dict(os.environ, {'TBR_MODEL_PROVIDER': 'meta'}, clear=True):
            with self.assertRaisesRegex(ValueError, 'Meta provider requires'):
                create_app('sqlite://')

        with patch.dict(os.environ, {
            'TBR_MODEL_PROVIDER': 'meta',
            'META_API_KEY': 'local-test-secret',
        }, clear=True):
            app = create_app('sqlite://')
        try:
            self.assertEqual(app.state.chat_service.provider.model_id, 'muse-spark-1.3')
        finally:
            app.state.db.engine.dispose()

    def _auth_cookie(self, user):
        from src.platform.workflow.accounts import create_session
        with self.app.state.db.session_factory() as session:
            u = session.get(User, user.id)
            token = create_session(session, u)
            session.commit()
            return {'tbr_session': token}

    def test_chat_service_direct_unit(self):
        service = ResearchChatService(self.provider)
        snapshot = SourceSnapshot(
            id=self.public_source.id,
            version=self.public_source.version,
            content_hash=self.public_source.content_hash,
            title=self.public_source.title,
            origin=self.public_source.origin,
            text=self.public_source.text,
            proposal_id=None,
            is_public=True
        )
        result = service.answer('What is the sample frequency?', [], [snapshot])
        self.assertFalse(result.insufficient_evidence)
        self.assertGreater(len(result.citations), 0)
        self.assertEqual(result.citations[0].source_id, self.public_source.id)
        self.assertIn('ten minutes', result.citations[0].quote)

    def test_chat_service_empty_sources(self):
        service = ResearchChatService(self.provider)
        result = service.answer('Any sensors?', [], [])
        self.assertTrue(result.insufficient_evidence)
        self.assertEqual(len(result.citations), 0)

    def test_chat_unauthenticated_rejected(self):
        res = self.client.post('/api/v2/chat', json={'message': 'Hello'})
        self.assertEqual(res.status_code, 401)

    def test_chat_public_literature_grounding(self):
        cookies = self._auth_cookie(self.user)
        res = self.client.post(
            '/api/v2/chat',
            json={'message': 'environmental sensing temperature', 'history': []},
            cookies=cookies
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('response', data)
        self.assertIn('citations', data)
        self.assertGreaterEqual(len(data['sources_consulted']), 1)

    def test_chat_proposal_scoped_grounding(self):
        cookies = self._auth_cookie(self.user)
        res = self.client.post(
            '/api/v2/chat',
            json={
                'message': 'Tell me about the proposal sensors',
                'history': [{'role': 'user', 'content': 'Hi'}, {'role': 'assistant', 'content': 'Hello!'}],
                'proposal_id': self.proposal.id
            },
            cookies=cookies
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('response', data)
        self.assertGreater(len(data['citations']), 0)
        self.assertEqual(data['citations'][0]['source_id'], self.public_source.id)

    def test_chat_tenant_boundary_enforced(self):
        """User cannot scope chat to another team's proposal."""
        cookies = self._auth_cookie(self.user)
        res = self.client.post(
            '/api/v2/chat',
            json={
                'message': 'Tell me confidential data',
                'history': [],
                'proposal_id': self.other_proposal.id
            },
            cookies=cookies
        )
        self.assertEqual(res.status_code, 403)
