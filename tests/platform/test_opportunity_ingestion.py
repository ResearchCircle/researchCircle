import json
import unittest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from src.platform.ingestion.opportunities import (
    filter_opportunities,
    load_opportunities,
    prepare_opportunities,
)

FIXTURE = Path(__file__).parent / 'fixtures' / 'opportunities-sample.json'


class OpportunityIngestionTests(unittest.TestCase):
    def test_synthetic_sample_preserves_sources_and_unknown_values(self):
        rows = load_opportunities(FIXTURE)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['eligibility'], 'unknown')
        self.assertIsNone(rows[0]['deadline'])
        self.assertEqual(rows[0]['source_url'], 'https://example.test/opportunities/early-career')
        self.assertEqual(rows[1]['deadline_timezone'], 'America/New_York')
        self.assertEqual(rows[1]['deadline'], '2027-01-15T17:00:00-05:00')
        self.assertTrue(all('Synthetic test data' in row['notes'] for row in rows))

    def test_import_payloads_match_manual_opportunity_api_contract(self):
        payload, = prepare_opportunities([{
            'title': '  Reviewed call  ',
            'source_url': 'https://funding.example/call',
            'deadline': '2027-01-15T17:00:00-05:00',
            'deadline_timezone': 'America/New_York',
            'notes': 'Deadline copied from the cited call.',
            'eligibility': 'unknown',
            'ignored_private_field': 'discarded',
        }])
        self.assertEqual(set(payload), {
            'title', 'source_url', 'deadline', 'deadline_timezone', 'notes', 'eligibility',
        })
        self.assertEqual(payload['title'], 'Reviewed call')
        self.assertEqual(payload['eligibility'], 'unknown')

    def test_filter_requires_explicit_values_and_excludes_unknown_deadlines_from_bounds(self):
        rows = load_opportunities(FIXTURE)
        selected = filter_opportunities(
            rows, query='infrastructure', eligibility='unknown',
            deadline_before=datetime.fromisoformat('2027-02-01T00:00:00+00:00'),
        )
        self.assertEqual([row['title'] for row in selected], [
            'Synthetic Research Infrastructure Grant',
        ])
        self.assertEqual(filter_opportunities(rows, deadline_before=datetime.fromisoformat(
            '2027-02-01T00:00:00+00:00')), selected)

    def test_invalid_input_fails_without_silent_defaults(self):
        base = {'title': 'A call'}
        for invalid in (
            {'deadline': '2027-01-15T17:00:00'},
            {'source_url': 'file:///private'},
            {'source_url': 'https://user:pass@example.test'},
            {'deadline_timezone': 'Unknown/Zone'},
            {'eligibility': 'likely'},
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                prepare_opportunities([{**base, **invalid}])

    def test_load_rejects_bad_envelope_and_duplicate_identity(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'opportunities.json'
            path.write_text(json.dumps({'opportunities': [
                {'title': 'Same', 'source_url': 'https://example.test/call'},
                {'title': ' same ', 'source_url': 'https://example.test/call'},
            ]}), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                load_opportunities(path)
            path.write_text(json.dumps({'unexpected': []}), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'only an opportunities list'):
                load_opportunities(path)
