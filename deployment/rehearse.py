"""Prove fresh-install persistence in a new local project; retain every volume."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
from uuid import uuid4

import httpx

from .readiness import wait_for_runtime
from .runtime import ROOT, RuntimeConfig
from .start import start_stack


def prepare_rehearsal(output_root: Path, port: int, images: dict[str, str],
                      source_dir: Path | None = None) -> tuple[Path, dict[str, str]]:
    source = (source_dir or Path(os.environ.get('TBR_DATA_SOURCE', ROOT / 'data'))).expanduser().resolve()
    output = output_root.expanduser().resolve()
    for protected in {source, (ROOT / 'data').resolve()}:
        if output == protected or protected in output.parents or output in protected.parents:
            raise ValueError('Rehearsal output must be separate from collected source data.')
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError('Rehearsal port must be an integer from 1 to 65535.')
    required = {'TBR_API_IMAGE', 'TBR_WEB_IMAGE', 'TBR_DB_IMAGE', 'TBR_PROXY_IMAGE'}
    if set(images) != required or any(not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/:@-]{0,254}', value)
                                      for value in images.values()):
        raise ValueError('Supply explicit valid rehearsal image references.')
    project = 'tbr-fresh-' + uuid4().hex[:12]
    settings = {'COMPOSE_PROJECT_NAME': project, 'TBR_PROFILE': 'development',
                'TBR_MODEL_PROVIDER': 'fixture', 'TBR_MODEL_BASE_URL': '', 'TBR_MODEL_ID': '',
                'TBR_DEV_IDENTITY': 'false', 'TBR_WORKER_MODULE': 'services.worker.generate',
                'TBR_HTTP_PORT': str(port), 'TBR_DB_PASSWORD': secrets.token_urlsafe(32),
                'TBR_DATA_SOURCE': str(source), 'TBR_DATA_WORK': '/tmp/' + project, **images}
    RuntimeConfig.from_env(settings)
    directory = output / project
    directory.mkdir(parents=True, mode=0o700, exist_ok=False)
    path = directory / 'runtime.env'
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w') as file:
        file.write(''.join(f'{key}={value}\n' for key, value in settings.items()))
    return path, settings


def _docker(command, env, *arguments) -> str:
    result = subprocess.run([*command, *arguments], env=env, cwd=ROOT, capture_output=True, text=True, timeout=180)
    if result.returncode:
        raise ValueError('Rehearsal Docker operation failed; inspect the retained project.')
    return result.stdout


def exercise_persistence(base_url: str, restart) -> dict:
    label = uuid4().hex
    password = secrets.token_urlsafe(24)
    email = f'fresh-{label}@example.test'

    def read(response, expected):
        if response.status_code != expected:
            raise ValueError('Fresh-install account/proposal persistence check failed.')
        return response.json()

    with httpx.Client(base_url=base_url, trust_env=False, timeout=10) as client:
        user = read(client.post('/api/v2/auth/register', json={
            'email': email, 'name': 'Synthetic fresh-install user', 'password': password}), 201)['user']
        team = read(client.post('/api/v2/teams', json={'name': 'Synthetic fresh-install team'}), 201)
        proposal = read(client.post('/api/v2/proposals', json={
            'team_id': team['id'], 'title': 'Synthetic persistence rehearsal', 'content': 'Initial synthetic text.'}), 201)
        path = '/api/v2/proposals/' + proposal['id']
        content = 'Saved synthetic proposal text must survive application restart.'
        saved = read(client.patch(path, json={'expected_revision': proposal['revision'], 'content': content}), 200)
        restart()
        reopened = read(client.get(path), 200)
        session = read(client.get('/api/v2/auth/me'), 200)
        if (reopened['content'] != content or reopened['revision'] != saved['revision']
                or session['user']['id'] != user['id']):
            raise ValueError('Saved proposal or named session did not survive restart.')
    with httpx.Client(base_url=base_url, trust_env=False, timeout=10) as fresh:
        read(fresh.post('/api/v2/auth/login', json={'email': email, 'password': password}), 200)
        if read(fresh.get(path), 200)['content'] != content:
            raise ValueError('Fresh login could not reopen the saved proposal.')
    return {'registration_status': 201, 'save_status': 200, 'saved_revision': saved['revision'],
            'session_survived_restart': True, 'fresh_login_reopened_proposal': True,
            'proposal_id': proposal['id'], 'saved_content_sha256': hashlib.sha256(content.encode()).hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'dist/rehearsals')
    parser.add_argument('--port', type=int, default=18092)
    parser.add_argument('--api-image', default='tbr-v2-api:development')
    parser.add_argument('--web-image', default='tbr-v2-web:development')
    parser.add_argument('--db-image', default='postgres:16-alpine')
    parser.add_argument('--proxy-image', default='nginx:stable-alpine')
    args = parser.parse_args()
    command, env, settings = None, None, None
    phase = 'prepare_rehearsal'
    result = {'status': 'failed', 'message': 'Fresh-install rehearsal failed; existing data was not reset.'}
    try:
        path, settings = prepare_rehearsal(args.output_dir, args.port, {
            'TBR_API_IMAGE': args.api_image, 'TBR_WEB_IMAGE': args.web_image,
            'TBR_DB_IMAGE': args.db_image, 'TBR_PROXY_IMAGE': args.proxy_image})
        env = {**os.environ, **settings}
        command = ['docker', 'compose', '-p', settings['COMPOSE_PROJECT_NAME'], '--env-file', str(path),
                   '-f', str(ROOT / 'deployment/compose.yaml')]
        phase = 'require_fresh_volume'
        volumes = subprocess.run(['docker', 'volume', 'ls', '--filter', 'name=' + settings['COMPOSE_PROJECT_NAME'] + '_',
                                  '--format', '{{.Name}}'], capture_output=True, text=True, timeout=15)
        if volumes.returncode or volumes.stdout.strip():
            raise ValueError('Fresh rehearsal requires a new project with no preexisting volumes.')
        _docker(command, env, 'config', '--quiet')
        phase = 'gated_startup'
        start_stack(command, env, 60)
        base_url = f'http://127.0.0.1:{args.port}'

        def restart():
            _docker(command, env, 'restart', 'api', 'worker')
            wait_for_runtime(args.port, 60)

        phase = 'registration_save_and_restart'
        checks = exercise_persistence(base_url, restart)
        phase = 'schema_after_restart'
        schema = json.loads(_docker(command, env, 'run', '--rm', '-T', '--no-deps', 'api', 'python', '-m', 'deployment.schema'))
        if schema.get('status') != 'schema_ready':
            raise ValueError('Schema was not ready after application restart.')
        result = {'status': 'passed', 'profile': 'development', 'provider': 'fixture',
                  'fresh_volume_at_start': True, 'schema_heads': schema['heads'], 'schema_verified': True,
                  'drafting_exercised': False, **checks}
    except Exception:
        result['failed_step'] = phase
    finally:
        if command is not None:
            try:
                _docker(command, env, 'stop')
                result['rehearsal_services_stopped'] = True
            except Exception:
                result.update(status='failed', rehearsal_services_stopped=False)
        if settings is not None:
            result.update(project=settings['COMPOSE_PROJECT_NAME'],
                          settings_location=str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path))
            try:
                volumes = subprocess.run(['docker', 'volume', 'ls', '--filter', 'name=' + settings['COMPOSE_PROJECT_NAME'] + '_',
                                          '--format', '{{.Name}}'], capture_output=True, text=True, timeout=15)
                retained = volumes.stdout.splitlines() if volumes.returncode == 0 else []
                result['retained_volumes'] = retained
                result['database_volume_retained'] = settings['COMPOSE_PROJECT_NAME'] + '_postgres-data' in retained
                if result['status'] == 'passed' and not result['database_volume_retained']:
                    result.update(status='failed', failed_step='verify_retained_volume')
            except Exception:
                result.update(status='failed', failed_step='verify_retained_volume')
    print(json.dumps(result))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
