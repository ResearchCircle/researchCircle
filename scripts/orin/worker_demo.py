"""Demonstrate owned generation behavior with an in-memory job-store fixture."""

import argparse
from contextlib import ExitStack
import json
import os
import sys
import tempfile
import time
from dataclasses import asdict
from pathlib import Path

from src.platform.drafting.fixtures import SAMPLE_REQUEST, SAMPLE_SOURCE, FixtureDraftProvider, FixtureTokenCounter
from src.platform.drafting.jobs import FixtureJobStore, JobError
from src.platform.drafting.service import DraftingService
from src.platform.drafting.worker import GenerationWorker
from src.platform.models.provider import LocalModelProvider


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider', choices=['fixture', 'local'], default='fixture')
    parser.add_argument('--base-url')
    parser.add_argument('--model-id')
    parser.add_argument('--lease-path', help='Shared absolute model lease file, required for local mode')
    args = parser.parse_args()
    if args.provider == 'local' and (not args.base_url or not args.model_id):
        parser.error('local requires --base-url and --model-id')
    if args.provider == 'local':
        if not args.lease_path or not Path(args.lease_path).is_absolute():
            parser.error('local requires a shared absolute --lease-path')
        source = Path(os.environ.get('TBR_DATA_SOURCE', str(Path(__file__).resolve().parents[2] / 'data'))).resolve()
        lease = Path(args.lease_path).resolve()
        if lease == source or source in lease.parents or not lease.parent.is_dir():
            parser.error('--lease-path must be outside source data in an existing directory')
    try:
        provider = (FixtureDraftProvider() if args.provider == 'fixture' else
                    LocalModelProvider(args.base_url, args.model_id))
    except ValueError as error:
        print(json.dumps({'error': {'code': 'invalid_request', 'message': str(error), 'retryable': False}}), file=sys.stderr)
        return 1
    counter = FixtureTokenCounter() if args.provider == 'fixture' else provider
    store = FixtureJobStore()
    job = store.enqueue('synthetic-user', SAMPLE_REQUEST, (SAMPLE_SOURCE,))
    states = [job.state]
    start = time.monotonic()
    with ExitStack() as stack:
        lease = (Path(stack.enter_context(tempfile.TemporaryDirectory(prefix='tbr-worker-demo-'))) / 'model.lock'
                 if args.provider == 'fixture' else Path(args.lease_path))
        try:
            worker = GenerationWorker(store, DraftingService(provider, counter), lease,
                                      (lambda: True) if args.provider == 'fixture' else provider.is_idle)
        except JobError as error:
            print(json.dumps({'error': {'code': error.code, 'message': str(error), 'retryable': error.retryable}}), file=sys.stderr)
            return 1
        try:
            deadline = start + 130
            while time.monotonic() < deadline:
                worker.tick()
                current = store.get(job.id)
                if current.state != states[-1]:
                    states.append(current.state)
                if current.state in ('succeeded', 'failed'):
                    break
                time.sleep(.05)
            else:
                store.cancel(job.id)
            current = store.get(job.id)
        finally:
            worker.close(wait=True)
    print(json.dumps({'store': 'in_memory_fixture', 'evidence': 'synthetic_fixture', 'provider': args.provider,
                      'states': states, 'elapsed_s': round(time.monotonic() - start, 6),
                      'state': current.state, 'output': asdict(current.output) if current.output else None,
                      'error': asdict(current.error) if current.error else None}))
    return 0 if current.state == 'succeeded' else 1


if __name__ == '__main__':
    raise SystemExit(main())
