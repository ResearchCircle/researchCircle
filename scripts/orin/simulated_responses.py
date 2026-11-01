"""Deterministic synthetic model completions for local workflow checks.

These responses are hand-authored fixtures. They make no model or network calls
and do not read the private research corpus.
"""

from __future__ import annotations

import json
import uuid

from src.platform.drafting.fixtures import SAMPLE_SOURCE
from src.platform.models.provider import ModelResult


SOURCE_TEXTS = (
    SAMPLE_SOURCE.text,
    'Synthetic calibration log: greenhouse sensors were calibrated weekly to a '
    'tolerance of 0.5 degrees C. The log contains no crop yield or energy observations.',
)


def _source_ids(source_ids: tuple[str, str]) -> tuple[str, str]:
    if not isinstance(source_ids, tuple) or len(source_ids) != 2:
        raise ValueError('source_ids must be a tuple containing exactly two UUIDs')
    if any(not isinstance(value, str) for value in source_ids):
        raise ValueError('source_ids must contain UUID strings')
    try:
        parsed = tuple(uuid.UUID(value) for value in source_ids)
    except (ValueError, AttributeError, TypeError) as exc:
        raise ValueError('source_ids must contain valid UUIDs') from exc
    if parsed[0] == parsed[1]:
        raise ValueError('source_ids must be distinct')
    return source_ids


def response_for(case: str, source_ids: tuple[str, str]) -> ModelResult:
    """Return one named synthetic completion using the caller's source UUIDs."""
    first_id, second_id = _source_ids(source_ids)
    if case == 'two_source':
        payload = {
            'text': (
                f'This fixture-simulated methods summary reports ten-minute readings '
                f'over seven days [{first_id}], with weekly sensor calibration to a '
                f'0.5 degrees C tolerance [{second_id}]. Neither source establishes '
                f'crop-yield or energy savings [{first_id}] [{second_id}].'
            ),
            'citations': [
                {'source_id': first_id, 'quote': 'one reading every ten minutes for seven days'},
                {'source_id': second_id, 'quote': 'calibrated weekly to a tolerance of 0.5 degrees C'},
            ],
            'insufficient_evidence': False,
        }
        raw = json.dumps(payload)
        finish_reason = 'stop'
    elif case == 'insufficient':
        raw = json.dumps({
            'text': '', 'citations': [], 'insufficient_evidence': True,
            'fixture': 'simulated',
        })
        finish_reason = 'stop'
    elif case == 'invalid_quote':
        raw = json.dumps({
            'text': f'Fixture-simulated claim [{first_id}].',
            'citations': [{'source_id': first_id, 'quote': 'A deliberately absent fixture quote.'}],
            'insufficient_evidence': False,
        })
        finish_reason = 'stop'
    elif case == 'truncated':
        raw = (f'{{"text":"Fixture-simulated partial response [{first_id}]",'
               f'"citations":[{{"source_id":"{first_id}","quote":"'
               f'{SOURCE_TEXTS[0]}')
        finish_reason = 'length'
    else:
        raise ValueError(f'unknown simulated response case: {case}')

    return ModelResult(raw, 'fixture-scripted-v1', None, finish_reason)
