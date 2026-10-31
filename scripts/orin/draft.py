"""Bounded selected-source draft demo using labeled synthetic evidence."""

import argparse
import json
import sys
import time
from dataclasses import asdict

from src.platform.drafting.fixtures import FixtureDraftProvider, FixtureTokenCounter, SAMPLE_REQUEST, SAMPLE_SOURCE
from src.platform.drafting.service import DraftingService
from src.platform.drafting.types import DraftError
from src.platform.models.provider import LocalModelProvider, ProviderError


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider', choices=['fixture', 'local'], default='fixture')
    parser.add_argument('--base-url')
    parser.add_argument('--model-id')
    parser.add_argument('--timeout-s', type=float, default=120)
    args = parser.parse_args()
    if args.provider == 'local' and (not args.base_url or not args.model_id):
        parser.error('local requires --base-url and --model-id')
    start = time.monotonic()
    try:
        provider = (FixtureDraftProvider() if args.provider == 'fixture' else
                    LocalModelProvider(args.base_url, args.model_id))
        counter = FixtureTokenCounter() if args.provider == 'fixture' else provider
        result = DraftingService(provider, counter).generate(SAMPLE_REQUEST, (SAMPLE_SOURCE,), args.timeout_s)
    except (ProviderError, DraftError, ValueError) as error:
        print(json.dumps({'error': {'code': getattr(error, 'code', 'invalid_request'),
                                   'message': str(error), 'retryable': getattr(error, 'retryable', False)}}), file=sys.stderr)
        return 1
    print(json.dumps({'provider': args.provider, 'evidence': 'synthetic_fixture',
                      'token_count_method': 'synthetic_utf8_bytes' if args.provider == 'fixture' else 'server_chat_tokenizer',
                      'elapsed_s': round(time.monotonic() - start, 6), 'result': asdict(result)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
