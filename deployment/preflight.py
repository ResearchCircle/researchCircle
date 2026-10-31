"""Validate runtime settings; --integration checks structural prerequisites only."""

import argparse
import json
import os

from .runtime import ROOT, RuntimeConfig, integration_gaps


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--integration', action='store_true')
    args = parser.parse_args()
    try:
        config = RuntimeConfig.from_env(os.environ)
    except ValueError as error:
        print(json.dumps({'status': 'invalid_configuration', 'message': str(error)}))
        return 1
    gaps = integration_gaps(ROOT, os.environ) if args.integration else []
    print(json.dumps({'status': 'dependencies_missing' if gaps else 'configuration_valid',
                      'profile': config.profile, 'provider': config.provider, 'gaps': gaps,
                      'scope': 'Structural checks only; no browser, persistence or release acceptance claim.'}))
    return 1 if gaps else 0


if __name__ == '__main__':
    raise SystemExit(main())
