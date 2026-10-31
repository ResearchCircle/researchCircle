"""Run from the repository root: python -m scripts.orin.smoke."""

import argparse
import json
import sys
import time
from dataclasses import asdict

from src.platform.models.fixtures import FixtureModelProvider
from src.platform.models.provider import LocalModelProvider, ProviderError


SMOKE_PROMPT = '''Role: concise technical writer.
Context: a bounded local provider connectivity check, without research data.
Task: return the exact sentence in Inputs once.
Inputs: <sentence>Local provider ready.</sentence>
Deliverables: the sentence only.
Constraints: no commentary, no tools, no additional facts.'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider', choices=['fixture', 'local'], default='fixture')
    parser.add_argument('--base-url', help='Explicit local HTTP endpoint ending in /v1')
    parser.add_argument('--model-id', help='Observed served model identifier')
    parser.add_argument('--max-output-tokens', type=int, default=32)
    parser.add_argument('--timeout-s', type=float, default=30)
    args = parser.parse_args()
    if args.provider == 'local' and (not args.base_url or not args.model_id):
        parser.error('local requires --base-url and --model-id')
    start = time.monotonic()
    try:
        provider = (FixtureModelProvider() if args.provider == 'fixture' else
                    LocalModelProvider(args.base_url, args.model_id))
        result = provider.generate(SMOKE_PROMPT, args.max_output_tokens, args.timeout_s)
    except (ProviderError, ValueError) as exc:
        error = ({'code': exc.code, 'message': str(exc), 'retryable': exc.retryable}
                 if isinstance(exc, ProviderError) else
                 {'code': 'invalid_request', 'message': str(exc), 'retryable': False})
        print(json.dumps({'error': error}), file=sys.stderr)
        return 1
    print(json.dumps({'provider': args.provider, 'elapsed_s': round(time.monotonic() - start, 6),
                      'result': asdict(result)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
