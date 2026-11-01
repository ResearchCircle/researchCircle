"""Startup succeeds only after the same-origin browser and API respond."""
import contextlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from deployment.dev import main
from deployment.start import main as start_main
from deployment.readiness import wait_for_runtime


class RuntimeReadinessTests(unittest.TestCase):
    def setUp(self):
        self.api_requests = 0
        self.web_requests = 0
        self.api_mode = 'warmup'
        self.web_ready = True
        case = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/healthz':
                    case.api_requests += 1
                    ready = case.api_mode != 'offline' and case.api_requests > 1
                    self.send_response(200 if ready else 502)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    body = json.dumps({'status': 'ok' if ready else 'starting',
                                       'service': 'unrelated-service' if case.api_mode == 'wrong_service' else 'tigerexchange-api'}).encode()
                    try:
                        if case.api_mode == 'slow_body':
                            for value in body:
                                self.wfile.write(bytes([value]))
                                self.wfile.flush()
                                time.sleep(.03)
                        else:
                            self.wfile.write(body)
                    except OSError:
                        pass
                elif self.path == '/':
                    case.web_requests += 1
                    self.send_response(200 if case.web_ready else 502)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(b'<!doctype html><html>Workspace</html>')
                else:
                    self.send_error(404)

            def log_message(self, *_args):
                pass

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def test_development_start_waits_for_api_and_web_after_containers_start(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'runtime.env'
            path.write_text('COMPOSE_PROJECT_NAME=tbr-core\n'
                            f'TBR_HTTP_PORT={self.server.server_port}\n'
                            'TBR_DB_PASSWORD=synthetic-test-only-password\n')
            output = io.StringIO()
            with (patch('sys.argv', ['dev', '--env-file', str(path), '--provider', 'fixture']),
                  patch('deployment.dev.subprocess.run', return_value=subprocess.CompletedProcess([], 0)),
                  contextlib.redirect_stdout(output)):
                status = main()
            self.assertEqual(status, 0, output.getvalue())
            self.assertEqual(json.loads(output.getvalue())['status'], 'started')
            self.assertGreaterEqual(self.api_requests, 2, 'Launcher returned before the API became ready')
            self.assertGreaterEqual(self.web_requests, 1, 'Launcher did not check the browser route')

    def test_web_unavailable_causes_startup_failure_instead_of_started(self):
        self.web_ready = False
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'runtime.env'
            path.write_text('COMPOSE_PROJECT_NAME=tbr-core\n'
                            f'TBR_HTTP_PORT={self.server.server_port}\n'
                            'TBR_DB_PASSWORD=private-synthetic-password\n')
            output = io.StringIO()
            with (patch('sys.argv', ['dev', '--env-file', str(path), '--ready-timeout', '.4']),
                  patch('deployment.dev.subprocess.run', return_value=subprocess.CompletedProcess([], 0)),
                  contextlib.redirect_stdout(output)):
                status = main()
            self.assertEqual(status, 1, output.getvalue())
            result = json.loads(output.getvalue())
            self.assertEqual(result['status'], 'startup_failed')
            self.assertIn('ready', result['message'])
            self.assertNotIn('private-synthetic-password', output.getvalue())
            self.assertTrue(path.exists(), 'Failed readiness must retain runtime settings')
            self.assertGreater(self.web_requests, 0, 'API readiness alone must not pass')

    def test_unrelated_healthy_service_cannot_satisfy_shared_start_readiness(self):
        self.api_mode = 'wrong_service'
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'runtime.env'
            path.write_text('TBR_PROFILE=demo\nTBR_MODEL_PROVIDER=local\n'
                            'TBR_MODEL_BASE_URL=http://127.0.0.1:19091/v1\nTBR_MODEL_ID=homelab-llm\n'
                            'TBR_API_IMAGE=test-api\nTBR_WEB_IMAGE=test-web\nTBR_DB_PASSWORD=private-synthetic-password\n'
                            f'TBR_HTTP_PORT={self.server.server_port}\n')
            output = io.StringIO()
            with (patch('sys.argv', ['start', '--env-file', str(path), '--start', '--ready-timeout', '.4']),
                  patch.dict('os.environ', {}, clear=True),
                  patch('deployment.start.subprocess.run', return_value=subprocess.CompletedProcess([], 0)),
                  contextlib.redirect_stdout(output)):
                status = start_main()
            self.assertEqual(status, 1, output.getvalue())
            self.assertEqual(json.loads(output.getvalue())['status'], 'runtime_unavailable')
            self.assertNotIn('private-synthetic-password', output.getvalue())
            self.assertGreaterEqual(self.api_requests, 2)
            self.assertEqual(self.web_requests, 0)

    def test_streamed_health_body_cannot_extend_the_startup_deadline(self):
        self.api_mode = 'slow_body'
        self.api_requests = 1
        started = time.monotonic()
        with self.assertRaises(ValueError):
            wait_for_runtime(self.server.server_port, timeout_s=.12)
        self.assertLess(time.monotonic() - started, .7, 'Trickled bytes extended the total deadline')

    def test_development_uses_the_configured_port_despite_shell_overrides(self):
        run_child = subprocess.run
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'runtime.env'
            path.write_text('COMPOSE_PROJECT_NAME=tbr-core\n'
                            f'TBR_HTTP_PORT={self.server.server_port}\n'
                            'TBR_DB_PASSWORD=synthetic-test-only-password\n')

            def docker_child(_command, **kwargs):
                # Exercise the actual environment passed to child processes;
                # Docker's service mutations are outside this unit test.
                program = ('import os,sys; sys.exit(0 if os.environ.get("TBR_HTTP_PORT") == '
                           f'"{self.server.server_port}" else 1)')
                return run_child([sys.executable, '-c', program], **kwargs)

            output = io.StringIO()
            with (patch('sys.argv', ['dev', '--env-file', str(path), '--ready-timeout', '2']),
                  patch.dict('os.environ', {'TBR_HTTP_PORT': '1'}),
                  patch('deployment.dev.subprocess.run', side_effect=docker_child),
                  contextlib.redirect_stdout(output)):
                status = main()
            self.assertEqual(status, 0, output.getvalue())
            self.assertEqual(json.loads(output.getvalue())['url'], f'http://127.0.0.1:{self.server.server_port}')
            self.assertGreaterEqual(self.web_requests, 1)


if __name__ == '__main__':
    unittest.main()
