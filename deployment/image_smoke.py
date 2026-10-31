"""Check local image startup over HTTP; this is not browser/product acceptance."""

import argparse
import http.client
import json
import subprocess
import time


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--api-image', default='tbr-v2-api:development')
    parser.add_argument('--web-image', default='tbr-v2-web:development')
    args = parser.parse_args()
    containers = []
    evidence = {}

    def docker(*command):
        result = subprocess.run(['docker', *command], capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise RuntimeError('Image startup check failed.')
        return result.stdout.strip()

    try:
        for component, image, internal_port, path in [('api', args.api_image, 8000, '/healthz'),
                                                       ('web', args.web_image, 3000, '/')]:
            image_id = docker('image', 'inspect', '--format', '{{.Id}}', image)
            container = docker('run', '--pull=never', '-d', '-p', f'127.0.0.1::{internal_port}', image)
            containers.append(container)
            port = int(docker('port', container, f'{internal_port}/tcp').rsplit(':', 1)[1])

            def request(target):
                connection = http.client.HTTPConnection('127.0.0.1', port, timeout=2)
                try:
                    connection.request('GET', target)
                    response = connection.getresponse()
                    return response.status, response.read()
                finally:
                    connection.close()

            deadline = time.monotonic() + 15
            while True:
                try:
                    status, raw = request(path)
                    if status == 200:
                        break
                except (OSError, http.client.HTTPException):
                    pass
                if time.monotonic() >= deadline:
                    raise RuntimeError('Image did not become HTTP ready.')
                time.sleep(.1)
            item = {'image_id': image_id, 'http_status': status,
                    'user': docker('inspect', '--format', '{{.Config.User}}', container)}
            if component == 'api':
                if json.loads(raw).get('status') != 'ok':
                    raise RuntimeError('API health response was invalid.')
                status, raw = request('/openapi.json')
                paths = list(json.loads(raw)['paths'])
                if status != 200 or '/healthz' not in paths:
                    raise RuntimeError('API schema was unavailable.')
                item['api_paths'] = paths
            elif b'TigerResearchBuddy' not in raw:
                raise RuntimeError('Existing frontend page did not render.')
            evidence[component] = item
        print(json.dumps({'status': 'passed', 'evidence': evidence,
                          'scope': 'Existing health-only API and legacy page startup; no v2 workflow or browser acceptance.'}))
        return 0
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.TimeoutExpired):
        print(json.dumps({'status': 'failed', 'message': 'Local image startup validation failed.'}))
        return 1
    finally:
        for container in reversed(containers):
            subprocess.run(['docker', 'rm', '-f', container], capture_output=True, timeout=20)


if __name__ == '__main__':
    raise SystemExit(main())
