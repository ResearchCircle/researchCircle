import json
import subprocess
import sys
import unittest
from dataclasses import asdict
from pathlib import Path

from src.platform.models.fixtures import FIXTURE_RESULT
from src.platform.drafting.fixtures import SAMPLE_REQUEST, SAMPLE_SOURCE, FixtureDraftProvider, FixtureTokenCounter
from src.platform.drafting.service import DraftingService


ROOT = Path(__file__).resolve().parents[2]


class SmokeTests(unittest.TestCase):
    def run_smoke(self, *args):
        return subprocess.run([sys.executable, '-m', 'scripts.orin.smoke', *args],
                              cwd=ROOT, text=True, capture_output=True, timeout=5)

    def test_default_smoke_needs_no_endpoint_or_dependencies(self):
        run = self.run_smoke()
        self.assertEqual(run.returncode, 0, run.stderr)
        output = json.loads(run.stdout)
        self.assertEqual(output['provider'], 'fixture')
        self.assertEqual(output['result'], asdict(FIXTURE_RESULT))
        self.assertGreaterEqual(output['elapsed_s'], 0)
        self.assertEqual(run.stderr, '')

    def test_local_smoke_requires_explicit_configuration(self):
        run = self.run_smoke('--provider', 'local')
        self.assertEqual(run.returncode, 2)
        self.assertIn('--base-url', run.stderr)
        self.assertIn('--model-id', run.stderr)

    def test_local_worker_demo_requires_shared_lease_path(self):
        run = subprocess.run([sys.executable, '-m', 'scripts.orin.worker_demo',
                              '--provider', 'local', '--base-url', 'http://127.0.0.1:9/v1',
                              '--model-id', 'test-model'], cwd=ROOT, text=True, capture_output=True, timeout=5)
        self.assertEqual(run.returncode, 2)
        self.assertIn('--lease-path', run.stderr)

    def test_invalid_limit_is_reported_without_traceback(self):
        run = self.run_smoke('--max-output-tokens', '513')
        self.assertEqual(run.returncode, 1)
        self.assertEqual(json.loads(run.stderr)['error']['code'], 'invalid_request')
        self.assertEqual(run.stdout, '')

    def test_published_fixture_matches_result_and_proposed_job_states(self):
        fixture = json.loads((ROOT / 'scripts/orin/fixtures.json').read_text())
        self.assertEqual(fixture['evidence'], 'synthetic_fixture')
        self.assertEqual(fixture['model_result'], asdict(FIXTURE_RESULT))
        self.assertEqual(set(fixture['draft_jobs']), {'queued', 'running', 'succeeded', 'failed'})
        for state, job in fixture['draft_jobs'].items():
            self.assertEqual(job['state'], state)
            self.assertEqual(job['base_revision'], 3)
            self.assertEqual(job['source_refs'], [])
            self.assertEqual(job['output'] is not None, state == 'succeeded')
            self.assertEqual(job['error'] is not None, state == 'failed')
        self.assertEqual(fixture['draft_jobs']['succeeded']['output'], {
            **asdict(FIXTURE_RESULT), 'citations': []})

    def test_teammate_fixture_matches_real_drafting_types_and_fixture_behavior(self):
        fixture = json.loads((ROOT / 'docs/onboarding/handoff/platform-fixtures.json').read_text())
        self.assertEqual(fixture['evidence'], 'synthetic_fixture')
        self.assertEqual(fixture['contract_status'], 'proposed_for_T1_T2_T3_review')
        self.assertEqual(fixture['request'], json.loads(json.dumps(asdict(SAMPLE_REQUEST))))
        self.assertEqual(fixture['attached_sources'], [asdict(SAMPLE_SOURCE)])
        result = DraftingService(FixtureDraftProvider(), FixtureTokenCounter()).generate(SAMPLE_REQUEST, (SAMPLE_SOURCE,))
        self.assertEqual(fixture['result'], json.loads(json.dumps(asdict(result))))
        for state, job in fixture['draft_jobs'].items():
            self.assertEqual(state, job['state'])
            self.assertEqual(job['proposal_id'], SAMPLE_REQUEST.proposal_id)
            self.assertEqual(job['base_revision'], SAMPLE_REQUEST.base_revision)
            self.assertEqual(job['source_refs'], fixture['request']['source_refs'])
        self.assertEqual(fixture['draft_jobs']['succeeded']['output'], fixture['result'])


if __name__ == '__main__':
    unittest.main()
