"""Authored responses exercise persisted jobs without an external model."""
import importlib
import importlib.util
import contextlib
import io
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest

from services.api.app import create_app
from src.platform.drafting.citations import parse_citations
from src.platform.drafting.fixtures import SAMPLE_SOURCE
from scripts.orin.simulated_responses import SOURCE_TEXTS, response_for
from dataclasses import replace
import hashlib
from unittest.mock import patch


IDS = ('00000000-0000-4000-8000-000000000011', '00000000-0000-4000-8000-000000000012')


class SimulatedApplicationTests(unittest.TestCase):
    def test_authored_success_cites_both_sources_and_every_sentence(self):
        second = replace(SAMPLE_SOURCE, id=IDS[1], text=SOURCE_TEXTS[1],
                         content_hash=hashlib.sha256(SOURCE_TEXTS[1].encode()).hexdigest())
        output = response_for('two_source', IDS)
        text, citations, insufficient = parse_citations(output.text, (SAMPLE_SOURCE, second))
        self.assertFalse(insufficient)
        self.assertEqual({citation.source_id for citation in citations}, set(IDS))
        self.assertTrue(output.model_id.startswith('fixture-'))
        self.assertIsNone(output.usage)
        for sentence in re.split(r'(?<=[.!?])\s+', text):
            self.assertTrue(any(f'[{source_id}]' in sentence for source_id in IDS), sentence)

    def test_persisted_workflow_accepts_success_and_rejects_bad_or_stale_results(self):
        spec = importlib.util.find_spec('scripts.orin.simulated_application')
        self.assertIsNotNone(spec, 'The simulated persisted workflow runner is missing')
        module = importlib.import_module('scripts.orin.simulated_application')
        with TemporaryDirectory() as tmp:
            app = create_app(f"sqlite:///{Path(tmp) / 'application.db'}")
            try:
                app.state.db.create_schema()
                result = module.run_scenarios(app, Path(tmp) / 'simulation.lock')
                self.assertEqual(result['status'], 'passed')
                self.assertEqual(result['evidence'], 'scripted_responses')
                self.assertEqual(result['model_id'], 'fixture-scripted-v1')
                cases = {row['case']: row for row in result['cases']}
                self.assertEqual(cases['two_source']['citations'], 2)
                self.assertEqual(cases['two_source']['accept_status'], 200)
                self.assertTrue(cases['insufficient']['insufficient_evidence'])
                self.assertEqual(cases['invalid_quote']['error_code'], 'invalid_citations')
                self.assertEqual(cases['truncated']['error_code'], 'draft_truncated')
                self.assertEqual(cases['concurrent_save']['accept_status'], 409)
                self.assertTrue(cases['concurrent_save']['collaborator_text_preserved'])
                self.assertIn('cancelled_during_generation', cases)
                cancelled = cases['cancelled_during_generation']
                self.assertEqual(cancelled['error_code'], 'cancelled')
                self.assertTrue(cancelled['followup_queued_during_drain'])
                self.assertTrue(cancelled['late_output_discarded'])
                self.assertEqual(cancelled['followup_state'], 'succeeded')
                self.assertEqual(result['external_model_requests'], 0)
            finally:
                app.state.db.engine.dispose()

    def test_postgres_simulation_refuses_a_shared_demo_profile(self):
        from scripts.orin.simulated_application import main
        output = io.StringIO()
        with (patch.dict('os.environ', {'TBR_PROFILE': 'demo', 'TBR_MODEL_PROVIDER': 'local'}, clear=True),
              patch('sys.argv', ['simulation', '--postgres']), contextlib.redirect_stdout(output)):
            self.assertEqual(main(), 1)
        result = json.loads(output.getvalue())
        self.assertEqual(result['step'], 'development_fixture_required')
        self.assertIsNone(result['database_name'])
        self.assertFalse(result['creation_confirmed'])


if __name__ == '__main__':
    unittest.main()
