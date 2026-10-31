"""Synthetic drafting evidence; not a public corpus or persisted application data."""

import hashlib
import json

from ..models.provider import ModelResult, validate_request
from .types import DraftRequest, SourceRef, SourceSnapshot


PROPOSAL_ID = '00000000-0000-4000-8000-000000000010'
SOURCE_ID = '00000000-0000-4000-8000-000000000011'
SAMPLE_TEXT = ('In a synthetic greenhouse experiment, temperature sensors recorded one reading '
               'every ten minutes for seven days. The trial evaluated data collection reliability; '
               'it did not measure crop yields or establish an energy-saving benefit.')
SAMPLE_SOURCE = SourceSnapshot(SOURCE_ID, 'synthetic-v1', hashlib.sha256(SAMPLE_TEXT.encode()).hexdigest(),
                               'Synthetic greenhouse sensor trial', 'synthetic fixture; no public URL',
                               SAMPLE_TEXT, PROPOSAL_ID, False)
SAMPLE_REQUEST = DraftRequest(PROPOSAL_ID, 3, 'Methods',
                             'Describe the measurement schedule and what this trial cannot establish.',
                             (SourceRef(SOURCE_ID, SAMPLE_SOURCE.version, SAMPLE_SOURCE.content_hash),))


class FixtureTokenCounter:
    """UTF-8 byte count for deterministic tests, not a model token measurement."""

    def count_input_tokens(self, prompt: str, timeout_s: float) -> int:
        validate_request(prompt, 512, timeout_s)
        return len(prompt.encode('utf-8'))


class FixtureDraftProvider:
    """Canned output specific to SAMPLE_REQUEST; not a general drafting model."""

    def generate(self, prompt: str, max_output_tokens: int, timeout_s: float) -> ModelResult:
        validate_request(prompt, max_output_tokens, timeout_s)
        output = {'text': f'Temperature readings were recorded every ten minutes for seven days [{SOURCE_ID}]. '
                  f'The trial assessed collection reliability, without establishing crop-yield or energy-saving benefits [{SOURCE_ID}].',
                  'citations': [{'source_id': SOURCE_ID, 'quote': SAMPLE_TEXT}], 'insufficient_evidence': False}
        return ModelResult(json.dumps(output), 'fixture-draft-v1', None, 'stop')
