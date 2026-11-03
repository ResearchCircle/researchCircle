import unittest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.platform.database import Database
from src.platform.database.models import Source, Proposal, Team
from src.platform.database.public_records import PublicRecord
from src.platform.discovery.graph import get_public_graph
from services.api.app import create_app
from services.api.dependencies import get_session


class GraphServiceTests(unittest.TestCase):
    def setUp(self):
        self.db = Database('sqlite://')
        self.db.create_schema()
        self.session = self.db.session_factory()

    def tearDown(self):
        self.session.close()
        self.db.engine.dispose()

    def test_empty_graph_returns_empty_contract(self):
        result = get_public_graph(self.session)
        self.assertEqual(result, {'nodes': [], 'links': []})

    def test_public_relationships_and_topics(self):
        paper = Source(
            id='paper-1', version='v1', content_hash='h1',
            title='Synthetic paper: Greenhouse sensor measurement schedule',
            origin='https://doi.org/10.1000/greenhouse',
            text='Synthetic sample study on greenhouse sensors.',
            is_public=True, proposal_id=None
        )
        paper_rec = PublicRecord(
            source_id='paper-1', external_id='doi:10.1000/greenhouse',
            kind='paper', evidence_kind='public', is_current=True,
            metadata_json={'doi': '10.1000/greenhouse', 'year': 2024, 'authors': ['Dr. Alex River', 'Dr. Morgan Lee']}
        )

        author1 = Source(
            id='auth-1', version='v1', content_hash='h2',
            title='Listed author: Dr. Alex River',
            origin='https://doi.org/10.1000/greenhouse',
            text='Author Dr. Alex River researching greenhouse sensors.',
            is_public=True, proposal_id=None
        )
        auth1_rec = PublicRecord(
            source_id='auth-1', external_id='doi:10.1000/greenhouse#author:0',
            kind='researcher', evidence_kind='public', is_current=True,
            metadata_json={'author_name': 'Dr. Alex River', 'paper_external_id': 'doi:10.1000/greenhouse', 'interests': ['Greenhouse Sensors']}
        )

        author2 = Source(
            id='auth-2', version='v1', content_hash='h3',
            title='Listed author: Dr. Morgan Lee',
            origin='https://doi.org/10.1000/greenhouse',
            text='Author Dr. Morgan Lee researching sensor networks.',
            is_public=True, proposal_id=None
        )
        auth2_rec = PublicRecord(
            source_id='auth-2', external_id='doi:10.1000/greenhouse#author:1',
            kind='researcher', evidence_kind='public', is_current=True,
            metadata_json={'author_name': 'Dr. Morgan Lee', 'paper_external_id': 'doi:10.1000/greenhouse'}
        )

        self.session.add_all([paper, paper_rec, author1, auth1_rec, author2, auth2_rec])
        self.session.commit()

        graph = get_public_graph(self.session)
        node_ids = {n['id'] for n in graph['nodes']}
        self.assertIn('paper-1', node_ids)
        self.assertIn('auth-1', node_ids)
        self.assertIn('auth-2', node_ids)

        # Check types
        paper_node = next(n for n in graph['nodes'] if n['id'] == 'paper-1')
        self.assertEqual(paper_node['type'], 'paper')
        self.assertEqual(paper_node['evidence_kind'], 'public')

        auth_node = next(n for n in graph['nodes'] if n['id'] == 'auth-1')
        self.assertEqual(auth_node['type'], 'faculty')
        self.assertEqual(auth_node['name'], 'Dr. Alex River')

        # Check relationships: authorship and co-authorship
        rel_types = {link['relationship'] for link in graph['links']}
        self.assertIn('authored', rel_types)
        self.assertIn('co_authorship', rel_types)

    def test_strict_exclusion_of_private_proposal_sources(self):
        team = Team(id='team-1', name='Private Lab')
        self.session.add(team)
        self.session.flush()

        proposal = Proposal(id='prop-1', team_id='team-1', title='Private Proposal')
        self.session.add(proposal)
        self.session.flush()

        private_source = Source(
            id='priv-src-1', version='v1', content_hash='h_priv',
            title='Confidential Lab Notes', origin='Uploaded internal notes',
            text='Internal unreleased experiment details.',
            is_public=False, proposal_id='prop-1'
        )
        self.session.add(private_source)
        self.session.commit()

        graph = get_public_graph(self.session)
        self.assertEqual(graph['nodes'], [])
        self.assertEqual(graph['links'], [])

    def test_topic_filter(self):
        paper = Source(
            id='paper-1', version='v1', content_hash='h1',
            title='Greenhouse study', origin='https://doi.org/10.1000/greenhouse',
            text='greenhouse sensor study', is_public=True, proposal_id=None
        )
        paper_rec = PublicRecord(
            source_id='paper-1', external_id='doi:10.1000/greenhouse',
            kind='paper', evidence_kind='public', is_current=True,
            metadata_json={'interests': ['Greenhouse Sensors']}
        )
        paper2 = Source(
            id='paper-2', version='v1', content_hash='h2',
            title='Astronomy study', origin='https://doi.org/10.1000/astronomy',
            text='Telescope optics', is_public=True, proposal_id=None
        )
        paper2_rec = PublicRecord(
            source_id='paper-2', external_id='doi:10.1000/astronomy',
            kind='paper', evidence_kind='public', is_current=True,
            metadata_json={'interests': ['Deep Space Optics']}
        )
        self.session.add_all([paper, paper_rec, paper2, paper2_rec])
        self.session.commit()

        filtered = get_public_graph(self.session, topic_filter='Greenhouse')
        filtered_ids = {n['id'] for n in filtered['nodes']}
        self.assertIn('paper-1', filtered_ids)
        self.assertNotIn('paper-2', filtered_ids)


from pathlib import Path
from tempfile import TemporaryDirectory


class GraphEndpointTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.url = f"sqlite:///{Path(self.tmp.name) / 'graph.db'}"
        self.app = create_app(self.url)
        self.app.state.db.create_schema()
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()
        self.app.state.db.engine.dispose()
        self.tmp.cleanup()

    def test_get_graph_endpoint_contract(self):
        res = self.client.get('/api/v2/graph')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('nodes', data)
        self.assertIn('links', data)
        self.assertIsInstance(data['nodes'], list)
        self.assertIsInstance(data['links'], list)
