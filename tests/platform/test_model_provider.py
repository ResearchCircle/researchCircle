import json
import socket
import threading
import time
import unittest
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from src.platform.models.fixtures import FixtureModelProvider
from src.platform.models.provider import LocalModelProvider, ModelProvider, ProviderError


class FixtureTests(unittest.TestCase):
    def test_deterministic_completion_with_explicit_fixture_identity(self):
        provider = FixtureModelProvider()
        self.assertIsInstance(provider, ModelProvider)
        result = provider.generate('Write a section', 64, 2)
        self.assertEqual(result, provider.generate('Write a section', 64, 2))
        self.assertEqual(result.model_id, 'fixture-deterministic-v1')
        self.assertIn('fixture', result.text.lower())
        self.assertIsNone(result.usage)
        self.assertEqual(result.finish_reason, 'stop')
        json.dumps(asdict(result))

    def test_invalid_arguments_are_rejected_by_both_providers(self):
        providers = [FixtureModelProvider(), LocalModelProvider('http://127.0.0.1:9/v1', 'test-model')]
        for provider in providers:
            for prompt, budget, timeout in [('', 32, 1), ('  ', 32, 1),
                    (None, 32, 1), ('p', 0, 1), ('p', 513, 1), ('p', True, 1),
                    ('p', 1.5, 1), ('p', 1, 0), ('p', 1, 121),
                    ('p', 1, float('nan')), ('p', 1, float('inf')), ('p', 1, True),
                    ('p', 1, 10**1000)]:
                with self.subTest(provider=type(provider).__name__, args=(prompt, budget, timeout)):
                    with self.assertRaises(ValueError):
                        provider.generate(prompt, budget, timeout)


class LocalProviderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(self.server.status)
                self.end_headers()
                self.wfile.write(self.server.body)

            def do_POST(self):
                request = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                self.server.seen.append((self.path, request))
                time.sleep(self.server.delay)
                self.send_response(self.server.status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Location', '/unexpected-redirect')
                self.end_headers()
                try:
                    self.wfile.write(self.server.body)
                except (BrokenPipeError, ConnectionResetError):
                    pass

            def log_message(self, *_args):
                pass

        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}/v1'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.server.status = 200
        self.server.delay = 0
        self.server.seen = []
        self.payload = {'model': 'test-model', 'choices': [
            {'message': {'content': 'A completion'}, 'finish_reason': 'stop'}],
            'usage': {'prompt_tokens': 12, 'completion_tokens': 3, 'total_tokens': 15}}
        self.server.body = json.dumps(self.payload).encode()
        self.provider = LocalModelProvider(self.url, 'test-model')

    def test_real_http_request_and_result_shape(self):
        self.assertIsInstance(self.provider, ModelProvider)
        result = self.provider.generate('Synthetic prompt', 32, 2)
        self.assertEqual(result.text, 'A completion')
        self.assertEqual(result.model_id, 'test-model')
        self.assertEqual(asdict(result.usage), {
            'prompt_tokens': 12, 'completion_tokens': 3, 'total_tokens': 15})
        path, request = self.server.seen[0]
        self.assertEqual(path, '/v1/chat/completions')
        self.assertEqual(request, {'model': 'test-model', 'messages': [
            {'role': 'user', 'content': 'Synthetic prompt'}], 'max_tokens': 32,
            'temperature': 0, 'stream': False})

    def test_length_finish_reason_and_missing_usage_are_preserved(self):
        self.payload['choices'][0]['finish_reason'] = 'length'
        del self.payload['usage']
        self.server.body = json.dumps(self.payload).encode()
        result = self.provider.generate('p', 32, 2)
        self.assertEqual(result.finish_reason, 'length')
        self.assertIsNone(result.usage)

    def test_input_count_uses_the_same_chat_messages_and_generation_prefix(self):
        self.server.body = b'{"count": 123, "tokens": [1,2,3]}'
        self.assertEqual(self.provider.count_input_tokens('count this', 2), 123)
        path, payload = self.server.seen[0]
        self.assertEqual(path, '/tokenize')
        self.assertEqual(payload, {'model': 'test-model', 'messages': [
            {'role': 'user', 'content': 'count this'}], 'add_generation_prompt': True})

    def test_bad_tokenizer_response_is_a_typed_failure(self):
        for body in [b'{}', b'{"count": true}', b'{"count": -1}', b'[]', b'[' * 10000]:
            with self.subTest(body=body[:30]):
                self.server.body = body
                with self.assertRaises(ProviderError) as caught:
                    self.provider.count_input_tokens('p', 2)
                self.assertEqual(caught.exception.code, 'provider_invalid_response')

    def test_idle_probe_requires_both_running_and_waiting_metrics(self):
        for running, waiting, expected in [(0, 0, True), (1, 0, False), (0, 1, False)]:
            self.server.body = (f'vllm:num_requests_running{{engine="0"}} {running}\n'
                                f'vllm:num_requests_waiting{{engine="0"}} {waiting}\n').encode()
            self.assertEqual(self.provider.is_idle(2), expected)
        for body in [b'', b'vllm:num_requests_running 0\n', b'vllm:num_requests_running NaN\nvllm:num_requests_waiting 0\n']:
            self.server.body = body
            with self.assertRaises(ProviderError):
                self.provider.is_idle(2)

    def test_http_errors_are_typed_sanitized_and_never_retried(self):
        for status, code, retryable in [(400, 'provider_rejected', False),
                (401, 'provider_rejected', False), (429, 'provider_busy', True),
                (500, 'provider_unavailable', True), (503, 'provider_unavailable', True),
                (307, 'provider_redirect', False)]:
            with self.subTest(status=status):
                self.server.status = status
                self.server.body = b'PRIVATE source text and credentials'
                self.server.seen = []
                with self.assertRaises(ProviderError) as caught:
                    self.provider.generate('PRIVATE prompt', 32, 2)
                self.assertEqual(caught.exception.code, code)
                self.assertEqual(caught.exception.retryable, retryable)
                self.assertNotIn('PRIVATE', str(caught.exception))
                self.assertEqual(len(self.server.seen), 1)

    def test_timeout_is_a_failure_not_completion(self):
        self.server.delay = .25
        start = time.monotonic()
        with self.assertRaises(ProviderError) as caught:
            self.provider.generate('p', 32, .05)
        self.assertEqual(caught.exception.code, 'provider_timeout')
        self.assertLess(time.monotonic() - start, .2)

    def test_connection_refused_has_no_fallback(self):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            url = f'http://127.0.0.1:{sock.getsockname()[1]}/v1'
        with self.assertRaises(ProviderError) as caught:
            LocalModelProvider(url, 'test-model').generate('p', 32, .2)
        self.assertEqual(caught.exception.code, 'provider_unavailable')

    def test_malformed_responses_do_not_become_success(self):
        variants = [None, [], {}, {'error': 'private'},
            {**self.payload, 'model': 'another-model'},
            {**self.payload, 'choices': []},
            {**self.payload, 'choices': [{'message': {'content': ' '}, 'finish_reason': 'stop'}]},
            {**self.payload, 'choices': [{'message': {'content': None}, 'finish_reason': 'stop'}]},
            {**self.payload, 'choices': [{'message': {'content': 'text'}, 'finish_reason': 'tool_calls'}]},
            {**self.payload, 'usage': {'prompt_tokens': -1, 'completion_tokens': 3, 'total_tokens': 2}},
            {**self.payload, 'usage': {'prompt_tokens': True, 'completion_tokens': 3, 'total_tokens': 4}},
            {**self.payload, 'usage': {'prompt_tokens': 12, 'completion_tokens': 3, 'total_tokens': 100}}]
        for payload in variants:
            with self.subTest(payload=payload):
                self.server.body = json.dumps(payload).encode()
                with self.assertRaises(ProviderError) as caught:
                    self.provider.generate('p', 32, 2)
                self.assertEqual(caught.exception.code, 'provider_invalid_response')
        for body in [b'not json PRIVATE', b'x' * (1024 * 1024 + 1)]:
            self.server.body = body
            with self.assertRaises(ProviderError):
                self.provider.generate('p', 32, 2)

    def test_deeply_nested_json_is_a_typed_failure(self):
        self.server.body = b'[' * 10000 + b']' * 10000
        with self.assertRaises(ProviderError) as caught:
            self.provider.generate('p', 32, 2)
        self.assertEqual(caught.exception.code, 'provider_invalid_response')

    def test_explicit_zero_port_is_rejected(self):
        with self.assertRaises(ValueError):
            LocalModelProvider('http://127.0.0.1:0/v1', 'test-model')

    def test_explicit_local_endpoint_and_model_are_required(self):
        for url in ['', 'https://example.com/v1', 'http://8.8.8.8/v1',
                    'http://user:secret@127.0.0.1/v1', 'http://127.0.0.1/v1?key=secret',
                    'http://127.0.0.1/v1#fragment', 'http://127.0.0.1:bad/v1',
                    'http://127.0.0.1/other']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                LocalModelProvider(url, 'test-model')
        for model in ['', '  ', None]:
            with self.subTest(model=model), self.assertRaises(ValueError):
                LocalModelProvider(self.url, model)


if __name__ == '__main__':
    unittest.main()
