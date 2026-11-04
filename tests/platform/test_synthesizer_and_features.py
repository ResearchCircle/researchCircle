import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from services.api.app import create_app
from src.platform.database import Database
from src.platform.database.models import User
from src.platform.discovery.synthesizer import synthesize_idea
from services.api.routes.pursuits import get_opportunity_catalog


class SynthesizerAndFeaturesTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / 'test.db'
        self.db_url = f'sqlite:///{db_path}'
        self.app = create_app(self.db_url)
        self.app.state.db.create_schema()
        self.client = TestClient(self.app)
        self.database = self.app.state.db
        self.session = self.database.session_factory()

        with self.database.session_factory() as session:
            self.user = User(id=str(uuid4()), email='lead@rit.edu', name='Dr. Lead', password_hash='hash')
            session.add(self.user)
            session.commit()

    def tearDown(self):
        self.session.close()
        self.database.engine.dispose()
        self.temp_dir.cleanup()

    def test_synthesizer_produces_novelty_and_aims(self):
        result = synthesize_idea(
            self.session,
            title='Autonomous Swarm Robotics for Search and Rescue',
            description='Investigating distributed multi-robot perception, SLAM, and computer vision under degraded communication environments for disaster response.',
            tags='robotics, computer vision, distributed systems'
        )
        self.assertIn('impact_analysis', result)
        impact = result['impact_analysis']
        self.assertIn('target_agencies', impact)
        # Should detect NSF CISE or DARPA or DOE for robotics / vision
        self.assertTrue(len(impact['target_agencies']) > 0)
        self.assertIn('suggested_aims', impact)
        self.assertEqual(len(impact['suggested_aims']), 3)
        self.assertTrue(impact['suggested_aims'][0].startswith('Specific Aim 1'))
        self.assertIn('matches', result)
        self.assertIn('coverage', result)

    def test_opportunity_catalog_loading(self):
        catalog = get_opportunity_catalog()
        self.assertIn('items', catalog)
        items = catalog['items']
        self.assertGreater(len(items), 0)
        titles = [i['title'] for i in items]
        self.assertTrue(any('NSF' in t or 'NIH' in t or 'DARPA' in t for t in titles))
        for item in items:
            self.assertIn('title', item)
            self.assertIn('eligibility', item)
            self.assertIn('notes', item)

    def test_catalog_endpoint_http(self):
        resp = self.client.get('/api/v2/opportunities/catalog')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('items', data)
        self.assertGreater(len(data['items']), 0)

    def test_pdf_endpoint_404_for_unknown_source(self):
        resp = self.client.get(f'/api/v2/sources/{uuid4()}/pdf')
        self.assertEqual(resp.status_code, 404)

    def test_synthesize_collaborators_endpoint(self):
        self.client.cookies.set('tbr_session', self.user.id)
        resp = self.client.post(
            '/api/v2/collaborators/synthesize',
            json={
                'title': 'AI Healthcare Diagnostics',
                'description': 'Deep learning for medical tomography and federated patient imaging.',
                'tags': 'deep learning, healthcare, imaging'
            }
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('impact_analysis', data)
        self.assertIn('matches', data)
        self.assertIn('coverage', data)

