import tempfile
import unittest
from pathlib import Path

import numpy as np

from src.platform.database import Database
from src.platform.database.models import Source
from src.platform.database.public_records import PublicRecord
from src.platform.discovery.public_search import search_public
from src.platform.discovery.semantic import SemanticVectorizer, reciprocal_rank_fusion


class SemanticSearchTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / 'test_semantic.db'
        self.db = Database(f'sqlite:///{db_path}')
        self.db.create_schema()
        self.session = self.db.session_factory()

        # Seed sample public sources
        self.source1 = Source(
            id='00000000-0000-0000-0000-000000000001',
            version='1',
            content_hash='hash1',
            title='Wireless Sensor Networks for Environmental Telemetry',
            origin='https://doi.org/10.1000/1',
            text='We deploy low-power soil moisture sensors and battery-powered telemetry units across agricultural fields.',
            is_public=True,
            proposal_id=None
        )
        self.source2 = Source(
            id='00000000-0000-0000-0000-000000000002',
            version='1',
            content_hash='hash2',
            title='Deep Neural Architectures for Computer Vision',
            origin='https://doi.org/10.1000/2',
            text='Convolutional vision transformers achieve state of the art results on biomedical image classification benchmarks.',
            is_public=True,
            proposal_id=None
        )
        self.session.add(self.source1)
        self.session.add(self.source2)
        self.session.add(PublicRecord(
            source_id=self.source1.id,
            external_id='paper:1',
            kind='paper',
            evidence_kind='public',
            is_current=True,
            metadata_json={}
        ))
        self.session.add(PublicRecord(
            source_id=self.source2.id,
            external_id='paper:2',
            kind='paper',
            evidence_kind='public',
            is_current=True,
            metadata_json={}
        ))
        self.session.commit()

    def tearDown(self):
        self.session.close()
        self.temp_dir.cleanup()

    def test_vectorizer_properties(self):
        vec = SemanticVectorizer(dim=128)
        empty = vec.encode('')
        self.assertEqual(len(empty), 128)
        self.assertEqual(float(np.linalg.norm(empty)), 0.0)

        v1 = vec.encode('Wireless sensor telemetry')
        self.assertAlmostEqual(float(np.linalg.norm(v1)), 1.0, places=4)

        v2 = vec.encode('Low power wireless sensing networks')
        v3 = vec.encode('Biomedical image neural classification')

        sim_related = vec.similarity(v1, v2)
        sim_unrelated = vec.similarity(v1, v3)
        self.assertGreater(sim_related, sim_unrelated)

    def test_reciprocal_rank_fusion(self):
        bm25_ids = ['doc1', 'doc2']
        semantic_ids = ['doc2', 'doc3']
        scores = reciprocal_rank_fusion(bm25_ids, semantic_ids, rrf_k=60)
        self.assertIn('doc1', scores)
        self.assertIn('doc2', scores)
        self.assertIn('doc3', scores)
        self.assertGreater(scores['doc2'], scores['doc1'])
        self.assertGreater(scores['doc2'], scores['doc3'])

    def test_search_public_hybrid_not_degraded(self):
        result = search_public(self.session, 'wireless sensors agricultural telemetry', limit=5, semantic=True)
        self.assertFalse(result['degraded'])
        self.assertGreater(len(result['items']), 0)
        top = result['items'][0]
        self.assertEqual(top['id'], self.source1.id)
        self.assertIn('hybrid match', top['reason'].lower())
        self.assertIn('RRF score', top['reason'])

    def test_search_public_bm25_mode_is_degraded(self):
        result = search_public(self.session, 'wireless', limit=5, semantic=False)
        self.assertTrue(result['degraded'])
        self.assertGreater(len(result['items']), 0)
        self.assertIn('BM25 keyword match', result['items'][0]['reason'])

    def test_search_public_empty_query(self):
        result = search_public(self.session, '', limit=5, semantic=True)
        self.assertFalse(result['degraded'])
        self.assertEqual(len(result['items']), 0)

    def test_search_public_kind_filter(self):
        result = search_public(self.session, 'neural vision', limit=5, kind='paper', semantic=True)
        self.assertFalse(result['degraded'])
        self.assertEqual(len(result['items']), 1)
        self.assertEqual(result['items'][0]['id'], self.source2.id)

        result_none = search_public(self.session, 'neural vision', limit=5, kind='researcher', semantic=True)
        self.assertEqual(len(result_none['items']), 0)
