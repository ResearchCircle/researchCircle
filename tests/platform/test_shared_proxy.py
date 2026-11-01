"""Opt-in real proxy/API/TLS checks; retain isolated PostgreSQL test volumes."""
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import secrets
import ssl
import subprocess
import tempfile
import threading
import unittest
from uuid import uuid4

import httpx

from deployment.rehearse import prepare_rehearsal
from deployment.runtime import ROOT
from deployment.start import start_stack


@unittest.skipUnless(os.environ.get('TBR_RUN_PROXY_TESTS') == '1', 'Requires explicit local Docker proxy rehearsal')
class SharedProxyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='tbr-proxy-tls-')
        cls.addClassCleanup(cls.temporary.cleanup)
        directory = Path(cls.temporary.name)
        cls.path, settings = prepare_rehearsal(ROOT / 'dist/rehearsals', 18094, {
            'TBR_API_IMAGE': os.environ.get('TBR_PROXY_API_IMAGE', 'tbr-v2-api:development'),
            'TBR_WEB_IMAGE': os.environ.get('TBR_PROXY_WEB_IMAGE', 'tbr-v2-web:development'),
            'TBR_DB_IMAGE': 'postgres:16.6-alpine', 'TBR_PROXY_IMAGE': 'nginx:1.27-alpine'})
        cls.path.write_text(cls.path.read_text() + 'TBR_PUBLIC_SCHEME=https\n')
        print('Retained proxy rehearsal project: ' + settings['COMPOSE_PROJECT_NAME'])
        cls.env = {**os.environ, **settings, 'TBR_PUBLIC_SCHEME': 'https'}
        cls.command = ['docker', 'compose', '-p', settings['COMPOSE_PROJECT_NAME'],
                       '--env-file', str(cls.path), '-f', str(ROOT / 'deployment/compose.yaml')]
        cls.addClassCleanup(cls.docker, 'stop')
        start_stack(cls.command, cls.env, 60)
        subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1',
                        '-keyout', str(directory / 'key.pem'), '-out', str(directory / 'cert.pem'),
                        '-subj', '/CN=localhost'], check=True, capture_output=True)

        class FrontDoor(BaseHTTPRequestHandler):
            def forward(self):
                body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
                headers = {key: value for key, value in self.headers.items()
                           if key.lower() not in ('connection', 'transfer-encoding')}
                connection = http.client.HTTPConnection('127.0.0.1', 18094, timeout=15)
                try:
                    connection.request(self.command, self.path, body, headers)
                    response = connection.getresponse()
                    payload = response.read()
                    self.send_response(response.status)
                    for key, value in response.getheaders():
                        if key.lower() not in ('connection', 'transfer-encoding', 'content-length'):
                            self.send_header(key, value)
                    self.send_header('Content-Length', str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                finally:
                    connection.close()

            do_GET = do_POST = do_PATCH = forward

            def log_message(self, *_args):
                pass

        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), FrontDoor)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(directory / 'cert.pem', directory / 'key.pem')
        cls.server.socket = context.wrap_socket(cls.server.socket, server_side=True)
        thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        thread.start()
        cls.addClassCleanup(cls.server.server_close)
        cls.addClassCleanup(cls.server.shutdown)
        cls.base_url = f'https://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def docker(cls, *args):
        result = subprocess.run([*cls.command, *args], env=cls.env, cwd=ROOT,
                                capture_output=True, text=True, timeout=90)
        if result.returncode:
            raise AssertionError('Isolated proxy rehearsal operation failed; retained project can be inspected.')

    def test_https_registration_secure_session_save_and_reopen_after_restart(self):
        email, password = f'proxy-{uuid4().hex}@example.test', secrets.token_urlsafe(24)
        with httpx.Client(base_url=self.base_url, verify=False, trust_env=False, timeout=15,
                          headers={'Origin': self.base_url, 'X-Forwarded-Proto': 'http'}) as client:
            self.assertEqual(client.get('/').status_code, 200)
            registered = client.post('/api/v2/auth/register', json={
                'email': email, 'password': password, 'name': 'Synthetic TLS rehearsal'})
            self.assertEqual(registered.status_code, 201)
            cookie = registered.headers['set-cookie'].lower()
            for flag in ('secure', 'httponly', 'samesite=lax'):
                self.assertIn(flag, cookie)
            team = client.post('/api/v2/teams', json={'name': 'Synthetic TLS team'})
            self.assertEqual(team.status_code, 201)
            proposal = client.post('/api/v2/proposals', json={
                'team_id': team.json()['id'], 'title': 'TLS rehearsal', 'content': 'Initial synthetic text.'})
            self.assertEqual(proposal.status_code, 201)
            path = '/api/v2/proposals/' + proposal.json()['id']
            saved = client.patch(path, json={'expected_revision': proposal.json()['revision'],
                                            'content': 'Saved through the HTTPS front door.'})
            self.assertEqual(saved.status_code, 200)
            self.docker('restart', 'api', 'worker')
            from deployment.readiness import wait_for_runtime
            wait_for_runtime(18094, 60)
            self.assertEqual(client.get(path).json()['content'], 'Saved through the HTTPS front door.')
            self.assertEqual(client.get('/api/v2/auth/me').status_code, 200)
            login = client.post('/api/v2/auth/login', json={'email': email, 'password': password})
            self.assertEqual(login.status_code, 200)
            self.assertIn('secure', login.headers['set-cookie'].lower())

    def test_foreign_origin_and_wrong_scheme_remain_rejected(self):
        with httpx.Client(base_url=self.base_url, verify=False, trust_env=False, timeout=15) as client:
            for origin in ('https://foreign.example.test', self.base_url.replace('https:', 'http:')):
                response = client.post('/api/v2/auth/login', json={}, headers={
                    'Origin': origin, 'X-Forwarded-Proto': 'https'})
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.json()['error']['code'], 'origin_rejected')


if __name__ == '__main__':
    unittest.main()
