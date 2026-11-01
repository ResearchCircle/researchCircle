"""Citation failures remain strict while reporting safe, actionable categories."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from src.platform.database import Database
from src.platform.database.models import Proposal, Team, User
from src.platform.drafting.citations import parse_citations
from src.platform.drafting.fixtures import FixtureTokenCounter, SAMPLE_REQUEST, SAMPLE_SOURCE
from src.platform.drafting.service import DraftingService
from src.platform.drafting.types import DraftError
from src.platform.drafting.worker import GenerationWorker
from src.platform.models.provider import ModelResult
from src.platform.workflow.draft_jobs import PersistedJobStore, job_view


def completion(**changes):
    return {**{'text': f'Synthetic claim [{SAMPLE_SOURCE.id}].',
               'citations': [{'source_id': SAMPLE_SOURCE.id, 'quote': SAMPLE_SOURCE.text}],
               'insufficient_evidence': False}, **changes}


class CitationDiagnosticsTests(unittest.TestCase):
    def test_messages_distinguish_response_format_source_quote_and_marker_failures(self):
        cases = [
            ('PRIVATE_RESPONSE_SENTINEL not JSON', 'JSON'),
            (json.dumps({'text': 'PRIVATE_RESPONSE_SENTINEL'}), 'fields'),
            (json.dumps(completion(citations=[{'source_id': 'PRIVATE_UNKNOWN_SOURCE',
                                             'quote': SAMPLE_SOURCE.text}])), 'selected'),
            (json.dumps(completion(citations=[{'source_id': SAMPLE_SOURCE.id,
                                             'quote': 'PRIVATE_RESPONSE_SENTINEL'}])), 'quote'),
            (json.dumps(completion(text='Claim [PRIVATE_RESPONSE_SENTINEL].')), 'inline'),
        ]
        for raw, explanation in cases:
            with self.subTest(explanation=explanation), self.assertRaises(DraftError) as caught:
                parse_citations(raw, (SAMPLE_SOURCE,))
            self.assertEqual(caught.exception.code, 'invalid_citations')
            self.assertFalse(caught.exception.retryable)
            self.assertIn(explanation.lower(), str(caught.exception).lower())
            self.assertNotIn('PRIVATE_', str(caught.exception))
            self.assertNotIn(SAMPLE_SOURCE.text, str(caught.exception))

    def test_malformed_and_duplicate_references_remain_invalid(self):
        reference = {'source_id': SAMPLE_SOURCE.id, 'quote': SAMPLE_SOURCE.text}
        cases = [[None], [[]], [{'source_id': []}], [{**reference, 'quote': None}],
                 [reference, reference], [{**reference, 'quote': ''}], [{**reference, 'quote': 'x' * 1001}]]
        for references in cases:
            with self.subTest(references=references), self.assertRaises(DraftError) as caught:
                parse_citations(json.dumps(completion(citations=references)), (SAMPLE_SOURCE,))
            self.assertEqual(caught.exception.code, 'invalid_citations')

    def test_persisted_worker_failure_exposes_reason_without_raw_output_or_proposal_changes(self):
        class InvalidQuoteProvider:
            def generate(self, *_args):
                raw = json.dumps(completion(citations=[{
                    'source_id': SAMPLE_SOURCE.id, 'quote': 'PRIVATE_RESPONSE_SENTINEL'}]))
                return ModelResult(raw, 'synthetic-invalid-quote', None, 'stop')

        with TemporaryDirectory() as tmp:
            database = Database(f"sqlite:///{Path(tmp) / 'diagnostics.db'}")
            try:
                database.create_schema()
                with database.session_factory() as session:
                    user = User(email='diagnostic@example.test', name='Synthetic diagnostic', password_hash='unused-test-hash')
                    team = Team(name='Synthetic diagnostic')
                    session.add_all([user, team])
                    session.commit()
                    session.add(Proposal(id=SAMPLE_REQUEST.proposal_id, team_id=team.id, title='Synthetic proposal',
                                         revision=3, content='Saved text must remain.'))
                    session.commit()
                    user_id = user.id
                store = PersistedJobStore(database)
                queued = store.enqueue(user_id, SAMPLE_REQUEST, (SAMPLE_SOURCE,))
                worker = GenerationWorker(store, DraftingService(InvalidQuoteProvider(), FixtureTokenCounter()),
                                          Path(tmp) / 'generation.lock', lambda: True)
                try:
                    worker.tick()
                finally:
                    worker.close(wait=True)
                failed = store.get(queued.id)
                self.assertEqual(failed.state, 'failed')
                self.assertEqual(failed.error.code, 'invalid_citations')
                self.assertIn('quote', failed.error.message.lower())
                self.assertIsNone(failed.output)
                self.assertNotIn('PRIVATE_RESPONSE_SENTINEL', json.dumps(job_view(failed)))
                with database.session_factory() as session:
                    self.assertEqual(session.get(Proposal, SAMPLE_REQUEST.proposal_id).content, 'Saved text must remain.')
            finally:
                database.engine.dispose()


if __name__ == '__main__':
    unittest.main()
