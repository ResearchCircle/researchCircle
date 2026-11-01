"""Observe local HTTP readiness through the same proxy the browser uses."""
from http.client import HTTPConnection, HTTPException
import json
import math
from socket import SHUT_RDWR
from threading import Timer
import time


def _responds(port: int, path: str, timeout_s: float) -> bool:
    connection = HTTPConnection('127.0.0.1', port, timeout=timeout_s)
    deadline = time.monotonic() + timeout_s
    timer = None
    try:
        connection.connect()
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False
        transport = connection.sock

        def interrupt_read():
            # A socket timeout resets on each read. Shut down this transport at
            # the total deadline even if response bytes keep arriving slowly.
            try:
                transport.shutdown(SHUT_RDWR)
            except OSError:
                pass

        timer = Timer(remaining, interrupt_read)
        timer.daemon = True
        timer.start()
        connection.request('GET', path)
        response = connection.getresponse()
        if response.status != 200:
            return False
        if path == '/healthz':
            body = response.read(4097)
            if len(body) > 4096:
                return False
            value = json.loads(body)
            ready = isinstance(value, dict) and value.get('status') == 'ok' and value.get('service') == 'tigerexchange-api'
        else:
            ready = response.getheader('Content-Type', '').lower().startswith('text/html')
        return ready and time.monotonic() < deadline
    except (OSError, HTTPException, ValueError):
        return False
    finally:
        if timer is not None:
            timer.cancel()
        connection.close()


def wait_for_runtime(port: str | int, timeout_s: float = 60) -> None:
    try:
        if type(port) not in (str, int):
            raise ValueError
        port = int(port)
        if not 1 <= port <= 65535:
            raise ValueError
    except ValueError:
        raise ValueError('TBR_HTTP_PORT must be an integer from 1 to 65535.') from None
    if type(timeout_s) not in (int, float) or not math.isfinite(timeout_s) or not 0 < timeout_s <= 300:
        raise ValueError('Readiness timeout must be greater than zero and at most 300 seconds.')
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        ready = True
        for path in ('/healthz', '/'):
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not _responds(port, path, min(2, remaining)):
                ready = False
                break
        if ready and time.monotonic() < deadline:
            return
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(.25, remaining))
    raise ValueError('API and web did not become ready through the local proxy before the deadline. '
                     'Inspect service status; existing data was preserved.')
