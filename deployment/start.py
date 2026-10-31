"""Validate staged integration first; start containers only with explicit --start."""

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

from .runtime import ROOT, RuntimeConfig, integration_gaps


def read_settings(path: Path) -> dict[str, str]:
    """Simple literal KEY=value file, without interpolation or shell evaluation."""
    values = {}
    for number, line in enumerate(path.read_text().splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        key, separator, value = line.partition('=')
        if not separator or not re.fullmatch(r'[A-Z_][A-Z0-9_]*', key.strip()):
            raise ValueError(f'Invalid runtime setting on line {number}.')
        value = value.strip()
        if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
            value = value[1:-1]
        values[key.strip()] = value
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path, default=ROOT / 'deployment/.env')
    parser.add_argument('--start', action='store_true', help='Start the staged local stack after prerequisites pass')
    args = parser.parse_args()
    try:
        env = {**read_settings(args.env_file), **os.environ}
        config = RuntimeConfig.from_env(env)
        gaps = integration_gaps(ROOT, env)
        if config.profile != 'demo':
            gaps.append('Shared runtime requires TBR_PROFILE=demo.')
        for key in ('TBR_API_IMAGE', 'TBR_WEB_IMAGE', 'TBR_DB_PASSWORD'):
            if not env.get(key):
                gaps.append(f'{key} is required.')
        if gaps:
            print(json.dumps({'status': 'dependencies_missing', 'gaps': gaps}))
            return 1
        command = ['docker', 'compose', '-f', str(ROOT / 'deployment/compose.yaml')]
        check = subprocess.run([*command, 'config', '--quiet'], env=env, capture_output=True, text=True)
        if check.returncode:
            raise ValueError('Compose configuration validation failed; review local settings.')
        if args.start:
            result = subprocess.run([*command, 'up', '-d'], env=env, capture_output=True, text=True)
            if result.returncode:
                raise ValueError('Staged stack startup failed; inspect container status locally.')
        print(json.dumps({'status': 'started' if args.start else 'configuration_valid',
                          'acceptance': 'Browser flow, membership, persistence and backup/restore still require validation.'}))
        return 0
    except (OSError, ValueError) as error:
        message = str(error) if isinstance(error, ValueError) else 'Could not read runtime configuration or execute Docker.'
        print(json.dumps({'status': 'runtime_unavailable', 'message': message}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
