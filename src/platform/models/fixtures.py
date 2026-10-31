"""Deterministic completions for integration without a model service."""

import json

from .provider import ModelResult, validate_request


FIXTURE_RESULT = ModelResult(
    text='Fixture completion. Insufficient evidence for research claims.',
    model_id='fixture-deterministic-v1',
    usage=None,
    finish_reason='stop',
)


class FixtureModelProvider:
    """Always returns a canned result; does not tokenize or perform inference."""

    def generate(self, prompt: str, max_output_tokens: int, timeout_s: float) -> ModelResult:
        validate_request(prompt, max_output_tokens, timeout_s)
        return FIXTURE_RESULT


class ExtractiveFixtureProvider:
    """Return a labeled excerpt from the supplied source, never model inference."""

    def generate(self, prompt: str, max_output_tokens: int, timeout_s: float) -> ModelResult:
        validate_request(prompt, max_output_tokens, timeout_s)
        data = json.loads(prompt.split('\nINPUT_DATA_JSON\n', 1)[1])
        source = data['sources'][0]
        quote = source['text'].strip()[:240]
        display = quote.replace('[', '(').replace(']', ')')
        output = {'text': f'Fixture evidence excerpt: {display} [{source["id"]}].',
                  'citations': [{'source_id': source['id'], 'quote': quote}], 'insufficient_evidence': False}
        return ModelResult(json.dumps(output), 'fixture-extractive-v1', None, 'stop')
