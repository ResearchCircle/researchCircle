"""Deterministic completion for integration without a model service."""

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
