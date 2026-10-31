import hashlib
import subprocess
import sys
import unittest
from uuid import UUID

from src.platform.discovery.search import SampleSearch, list_samples, search
from src.platform.ingestion.import_public import import_records


def record(**changes):
    return {
        'external_id': 'synthetic:test:sensor-paper',
        'title': 'Synthetic paper: Sensor sampling',
        'text': 'Synthetic sample: A temperature sensor recorded a reading every ten minutes.',
        'origin': 'Synthetic test fixture; no public URL',
        'version': 'synthetic-v1',
        'kind': 'paper',
        'evidence_kind': 'synthetic',
        'is_public': True,
        'proposal_id': None,
        **changes,
    }


class PublicImportTests(unittest.TestCase):
    def test_import_is_reproducible_deduplicated_and_preserves_text(self):
        source = record()
        before = dict(source)
        first = import_records([source, dict(source)])
        second = import_records([dict(source)])
        self.assertEqual(first, second)
        self.assertEqual(len(first), 1)
        self.assertEqual(source, before)
        item = first[0]
        self.assertEqual(str(UUID(item['id'])), item['id'])
        self.assertEqual(item['id'], item['source_id'])
        self.assertEqual(item['text'], source['text'])
        self.assertEqual(item['content_hash'], hashlib.sha256(source['text'].encode('utf-8')).hexdigest())
        self.assertIn(item['snippet'], item['text'])
        self.assertEqual(item['version'], 'synthetic-v1')
        self.assertEqual(item['origin'], source['origin'])

    def test_identity_survives_a_versioned_text_update(self):
        first = import_records([record()])[0]
        newer = import_records([record(text='Synthetic sample: A sensor recorded a reading hourly.', version='synthetic-v2')])[0]
        self.assertEqual(first['id'], newer['id'])
        self.assertNotEqual(first['content_hash'], newer['content_hash'])
        self.assertNotEqual(first['version'], newer['version'])

    def test_content_hash_deduplication_is_independent_of_input_order(self):
        first, duplicate = record(), record(external_id='synthetic:test:duplicate')
        self.assertEqual(import_records([first, duplicate]), import_records([duplicate, first]))
        self.assertEqual(len(import_records([first, duplicate])), 1)

    def test_conflicting_identity_versions_in_one_import_are_rejected(self):
        with self.assertRaises(ValueError):
            import_records([record(), record(text='Synthetic changed text.', version='synthetic-v2')])

    def test_private_or_proposal_scoped_input_is_never_indexed(self):
        for source in [record(is_public=False), record(is_public='true'),
                       record(proposal_id='00000000-0000-4000-8000-000000000001')]:
            with self.subTest(source=source), self.assertRaises(ValueError):
                import_records([source])
            with self.subTest(source=source), self.assertRaises(ValueError):
                SampleSearch([source])

    def test_malformed_or_misleading_provenance_is_rejected(self):
        for source in [record(external_id=''), record(version=''), record(text=' '),
                       record(kind='unknown'), record(evidence_kind='unknown'),
                       record(title='Unlabeled faculty profile'), record(origin='https://example.com'),
                       record(evidence_kind='public', origin='no source URL'),
                       record(evidence_kind='public', origin='https://user:secret@example.com/paper')]:
            with self.subTest(source=source), self.assertRaises(ValueError):
                import_records([source])


class SampleSearchTests(unittest.TestCase):
    def test_sample_sensor_search_returns_both_kinds_and_checkable_provenance(self):
        samples = list_samples()
        self.assertGreaterEqual(len(samples), 4)
        result = search('sensor')
        self.assertTrue(result['degraded'])
        self.assertIsNone(result['next_cursor'])
        self.assertEqual({item['kind'] for item in result['items']}, {'paper', 'researcher'})
        required = {'id', 'source_id', 'version', 'content_hash', 'title', 'snippet',
                    'origin', 'score', 'reason', 'kind', 'evidence_kind', 'text'}
        for item in result['items']:
            self.assertEqual(set(item), required)
            self.assertEqual(item['evidence_kind'], 'synthetic')
            self.assertIn('synthetic', item['title'].lower())
            self.assertIn('synthetic', item['origin'].lower())
            self.assertIn('keyword', item['reason'].lower())
            self.assertGreater(item['score'], 0)
            self.assertIn(item['snippet'], item['text'])
            self.assertEqual(item['content_hash'], hashlib.sha256(item['text'].encode()).hexdigest())

    def test_nonmatching_and_empty_queries_return_empty_not_arbitrary_samples(self):
        for query in ['', '  ', '???', 'the and of', 'quantum banana teleportation']:
            with self.subTest(query=query):
                self.assertEqual(search(query)['items'], [])

    def test_ranking_limit_and_caller_mutation_are_deterministic(self):
        expected = search('sensor greenhouse')
        self.assertEqual(expected, search('SENSOR, greenhouse!'))
        self.assertEqual(search('sensor greenhouse', limit=1)['items'], expected['items'][:1])
        samples = list_samples()
        samples[0]['text'] = 'PRIVATE MUTATION'
        self.assertNotIn('PRIVATE MUTATION', str(list_samples()))
        expected['items'][0]['title'] = 'MUTATION'
        self.assertNotIn('MUTATION', str(search('sensor greenhouse')))

    def test_invalid_query_or_limit_fails_explicitly(self):
        for query, limit in [(None, 10), ('sensor', 0), ('sensor', 101), ('sensor', True), ('sensor', 1.5)]:
            with self.subTest(query=query, limit=limit), self.assertRaises(ValueError):
                search(query, limit)

    def test_imports_do_not_load_legacy_model_or_configuration_modules(self):
        code = '''import sys
from src.platform.discovery.search import list_samples
list_samples()
assert 'src.utils.config' not in sys.modules
assert 'src.database.vector_store' not in sys.modules
assert 'sentence_transformers' not in sys.modules
assert 'chromadb' not in sys.modules
'''
        run = subprocess.run([sys.executable, '-c', code], text=True, capture_output=True, timeout=5)
        self.assertEqual(run.returncode, 0, run.stderr)


if __name__ == '__main__':
    unittest.main()
