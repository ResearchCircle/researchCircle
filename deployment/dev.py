"""Start the isolated local workspace; preserve its database and source snapshot."""

import argparse
import json
import os
import secrets
import subprocess
import sys
from pathlib import Path

from .runtime import ROOT, RuntimeConfig
from .start import read_settings
from .readiness import wait_for_runtime


def configure_development(path: Path, provider: str, base_url: str | None, model_id: str | None) -> dict[str, str]:
    values = read_settings(path) if path.exists() else {}
    if values and values.get('COMPOSE_PROJECT_NAME') != 'tbr-core':
        raise ValueError('Use a separate environment file for the tbr-core development stack.')
    defaults = {'COMPOSE_PROJECT_NAME': 'tbr-core', 'TBR_API_IMAGE': 'tbr-v2-api:development',
                'TBR_WEB_IMAGE': 'tbr-v2-web:development', 'TBR_WORKER_MODULE': 'services.worker.generate',
                'TBR_HTTP_PORT': '18088', 'TBR_DATA_WORK': '/tmp/tbr-core-work',
                'TBR_DEV_IDENTITY': 'false'}
    values = {**defaults, **values}
    values.setdefault('TBR_DB_PASSWORD', secrets.token_urlsafe(32))
    values['TBR_MODEL_PROVIDER'] = provider
    values['TBR_PROFILE'] = 'demo' if provider == 'local' else 'development'
    if provider == 'local':
        if not base_url or not model_id:
            raise ValueError('Local inference requires --base-url and --model-id from observation.')
        values.update(TBR_MODEL_BASE_URL=base_url, TBR_MODEL_ID=model_id)
    elif provider == 'ollama':
        if not model_id:
            raise ValueError('Ollama inference requires --model-id for a model you have pulled.')
        values.update(TBR_MODEL_BASE_URL=base_url or 'http://host.docker.internal:11434/v1', TBR_MODEL_ID=model_id)
    else:
        values.pop('TBR_MODEL_BASE_URL', None)
        values.pop('TBR_MODEL_ID', None)
    RuntimeConfig.from_env(values)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, 'w') as output:
        os.fchmod(output.fileno(), 0o600)
        output.write(''.join(f'{key}={value}\n' for key, value in values.items()))
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path, default=ROOT / 'dist/core-runtime.env')
    parser.add_argument('--provider', choices=['fixture', 'local', 'ollama'], default='fixture')
    parser.add_argument('--base-url')
    parser.add_argument('--model-id')
    parser.add_argument('--build', action='store_true')
    parser.add_argument('--ready-timeout', type=float, default=60, help='Wait up to this many seconds for API and web readiness')
    args = parser.parse_args()
    try:
        settings = configure_development(args.env_file, args.provider, args.base_url, args.model_id)
        startup_env = {**os.environ, **settings}
        if args.build:
            subprocess.run([sys.executable, '-m', 'deployment.build'], cwd=ROOT, env=startup_env, check=True)
        compose = ['docker', 'compose', '-p', 'tbr-core', '--env-file', str(args.env_file),
                   '-f', str(ROOT / 'deployment/compose.yaml')]
        commands = [[*compose, 'config', '--quiet'], [*compose, 'up', '-d', 'db'],
                    [*compose, 'run', '--rm', '-T', 'api', 'python', '-m', 'alembic', 'upgrade', 'head'],
                    [*compose, 'run', '--rm', '-T', 'api', 'python', '-m', 'services.api.bootstrap'],
                    [*compose, 'up', '-d', 'api', 'worker', 'web', 'proxy']]
        for command in commands:
            result = subprocess.run(command, cwd=ROOT, env=startup_env, capture_output=True, text=True)
            if result.returncode:
                raise RuntimeError('Local workspace startup failed; inspect development service status. Existing data was preserved.')
        wait_for_runtime(settings['TBR_HTTP_PORT'], args.ready_timeout)
        print(json.dumps({'status': 'started', 'url': f'http://127.0.0.1:{settings["TBR_HTTP_PORT"]}',
                          'provider': args.provider, 'schema': 'migrated', 'accounts': 'register through the browser',
                          'sources': 'labeled synthetic samples', 'scope': 'Isolated local development; no shared deployment.'}))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        message = str(error) if isinstance(error, (ValueError, RuntimeError)) else 'Could not run local Docker/build tools.'
        print(json.dumps({'status': 'startup_failed', 'message': message}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
