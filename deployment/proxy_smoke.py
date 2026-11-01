"""Test the staged nginx config with disposable HTTP fixtures, not the product UI."""

import argparse
import http.client
import json
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4


UPSTREAM = '''import json, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  if self.path.endswith('/redirect'):
   self.send_response(307)
   self.send_header('Location', 'http://' + self.headers['Host'] + self.path.replace('/redirect', '/target'))
   self.end_headers()
   return
  body=json.dumps({'backend':sys.argv[2], 'path':self.path, 'host':self.headers['Host'],
                   'forwarded_host':self.headers.get('X-Forwarded-Host'),
                   'forwarded_proto':self.headers.get('X-Forwarded-Proto')}).encode()
  self.send_response(200)
  self.send_header('Content-Length',str(len(body)))
  self.end_headers()
  self.wfile.write(body)
 def log_message(self,*args): pass
HTTPServer(('0.0.0.0',int(sys.argv[1])),Handler).serve_forever()
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--proxy-image', default='nginx:stable-alpine')
    parser.add_argument('--upstream-image', default='python:3.12-slim')
    args = parser.parse_args()
    network = 'tbr-proxy-test-' + uuid4().hex[:12]
    created = []
    network_created = False

    def docker(*command):
        run = subprocess.run(['docker', *command], capture_output=True, text=True, timeout=30)
        if run.returncode:
            raise RuntimeError('Disposable Docker proxy check failed; inspect local Docker/image availability.')
        return run.stdout.strip()

    try:
        # Never pull images implicitly or change any existing network/container.
        for image in (args.proxy_image, args.upstream_image):
            docker('image', 'inspect', image)
        docker('network', 'create', network)
        network_created = True
        with tempfile.TemporaryDirectory(prefix='tbr-proxy-test-') as tmp:
            fixture = Path(tmp) / 'upstream.py'
            fixture.write_text(UPSTREAM)
            for alias, port in [('api', '8000'), ('web', '3000')]:
                container = docker('run', '-d', '--network', network, '--network-alias', alias,
                                   '--mount', f'type=bind,source={fixture},target=/fixture.py,readonly',
                                   args.upstream_image, 'python', '/fixture.py', port, alias)
                created.append(container)
            config = Path(__file__).with_name('nginx.conf').resolve()
            container = docker('run', '-d', '--network', network, '-p', '127.0.0.1::80',
                               '--mount', f'type=bind,source={config},target=/etc/nginx/templates/default.conf.template,readonly',
                               '-e', 'TBR_PUBLIC_SCHEME=http', '-e', 'NGINX_ENVSUBST_FILTER=^TBR_PUBLIC_SCHEME$',
                               args.proxy_image)
            created.append(container)
            port = int(docker('port', container, '80/tcp').rsplit(':', 1)[1])
            host = f'127.0.0.1:{port}'

            def request(path):
                connection = http.client.HTTPConnection('127.0.0.1', port, timeout=2)
                try:
                    connection.request('GET', path, headers={'X-Forwarded-Proto': 'https'})
                    response = connection.getresponse()
                    return response.status, response.getheader('Location'), response.read()
                finally:
                    connection.close()

            deadline = time.monotonic() + 10
            while True:
                try:
                    status, _, _ = request('/healthz')
                    if status == 200:
                        break
                except (OSError, http.client.HTTPException):
                    pass
                if time.monotonic() >= deadline:
                    raise RuntimeError('Disposable proxy did not become ready.')
                time.sleep(.1)
            for path, backend in [('/api/v2/echo?value=1', 'api'), ('/healthz', 'api'), ('/page', 'web')]:
                status, _, raw = request(path)
                value = json.loads(raw)
                if (status != 200 or value['backend'] != backend or value['path'] != path
                        or value['host'] != host or value['forwarded_host'] != host
                        or value['forwarded_proto'] != 'http'):
                    raise RuntimeError('Proxy path/host forwarding did not preserve the browser origin.')
            for path in ('/api/v2/redirect', '/redirect'):
                status, location, _ = request(path)
                if status != 307 or urlsplit(location).netloc != host:
                    raise RuntimeError('Proxy redirect lost the external browser port.')
            # Recreate an API at a different IP, as happens during compose upgrades.
            docker('rm', '-f', created[0])
            blocker = docker('run', '-d', '--network', network, args.upstream_image,
                             'python', '-c', 'import time; time.sleep(30)')
            created.append(blocker)
            replacement = docker('run', '-d', '--network', network, '--network-alias', 'api',
                                 '--mount', f'type=bind,source={fixture},target=/fixture.py,readonly',
                                 args.upstream_image, 'python', '/fixture.py', '8000', 'api')
            created.append(replacement)
            deadline = time.monotonic() + 12
            while True:
                try:
                    status, _, raw = request('/healthz')
                    if status == 200 and json.loads(raw)['backend'] == 'api':
                        break
                except (OSError, ValueError, http.client.HTTPException):
                    pass
                if time.monotonic() >= deadline:
                    raise RuntimeError('Proxy retained the replaced API container address.')
                time.sleep(.2)
        print(json.dumps({'status': 'passed', 'proxy_image': args.proxy_image,
                          'upstream_image': args.upstream_image, 'checks': [
                              'api_path_and_query', 'health_route', 'frontend_route', 'external_host_and_port',
                              'api_redirect_origin', 'frontend_redirect_origin', 'api_replacement_dns', 'client_scheme_spoof_ignored'],
                          'evidence': 'disposable_http_fixtures; not product/browser acceptance'}))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired):
        print(json.dumps({'status': 'failed', 'message': 'Disposable proxy validation failed; check local Docker and image availability.'}))
        return 1
    finally:
        for container in reversed(created):
            subprocess.run(['docker', 'rm', '-f', container], capture_output=True, timeout=20)
        if network_created:
            subprocess.run(['docker', 'network', 'rm', network], capture_output=True, timeout=20)


if __name__ == '__main__':
    raise SystemExit(main())
