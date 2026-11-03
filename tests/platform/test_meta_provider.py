import http.server
import json
import threading
import unittest

from src.platform.models.provider import MetaModelProvider, ModelProvider, ProviderError


class MetaProviderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                auth = self.headers.get('Authorization', '')
                if not auth.startswith('Bearer test-valid-key'):
                    self.send_response(401)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"error": "Unauthorized"}')
                    return

                length = int(self.headers.get('Content-Length', 0))
                payload = json.loads(self.rfile.read(length)) if length else {}

                if self.server.status_code != 200:
                    self.send_response(self.server.status_code)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"error": "Simulated error"}')
                    return

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = {
                    'id': 'chatcmpl-123',
                    'object': 'chat.completion',
                    'model': payload.get('model', 'meta/llama-3.3-70b-instruct'),
                    'choices': [{
                        'index': 0,
                        'message': {
                            'role': 'assistant',
                            'content': 'This is a verified Meta Llama draft completion.'
                        },
                        'finish_reason': 'stop'
                    }],
                    'usage': {
                        'prompt_tokens': 15,
                        'completion_tokens': 10,
                        'total_tokens': 25
                    }
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))

            def log_message(self, *_args):
                pass

        cls.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.server.status_code = 200
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever)
        cls.thread.daemon = True
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_implements_model_provider_protocol(self):
        provider = MetaModelProvider(
            api_key='test-valid-key',
            base_url=f'http://127.0.0.1:{self.port}'
        )
        self.assertIsInstance(provider, ModelProvider)

    def test_successful_generation_and_token_accounting(self):
        self.server.status_code = 200
        provider = MetaModelProvider(
            api_key='test-valid-key',
            base_url=f'http://127.0.0.1:{self.port}'
        )
        result = provider.generate('Draft research intro', 64, 5.0)
        self.assertEqual(result.text, 'This is a verified Meta Llama draft completion.')
        self.assertEqual(result.model_id, 'meta/llama-3.3-70b-instruct')
        self.assertIsNotNone(result.usage)
        self.assertEqual(result.usage.prompt_tokens, 15)
        self.assertEqual(result.usage.completion_tokens, 10)
        self.assertEqual(result.usage.total_tokens, 25)
        self.assertEqual(result.finish_reason, 'stop')

    def test_unauthorized_key_surfaces_provider_error(self):
        provider = MetaModelProvider(
            api_key='invalid-token',
            base_url=f'http://127.0.0.1:{self.port}'
        )
        with self.assertRaises(ProviderError) as ctx:
            provider.generate('Hello', 32, 5.0)
        self.assertEqual(ctx.exception.code, 'provider_unauthorized')
        self.assertFalse(ctx.exception.retryable)

    def test_rate_limit_surfaces_retryable_busy_error(self):
        self.server.status_code = 429
        provider = MetaModelProvider(
            api_key='test-valid-key',
            base_url=f'http://127.0.0.1:{self.port}'
        )
        with self.assertRaises(ProviderError) as ctx:
            provider.generate('Hello', 32, 5.0)
        self.assertEqual(ctx.exception.code, 'provider_busy')
        self.assertTrue(ctx.exception.retryable)

    def test_argument_validation(self):
        with self.assertRaises(ValueError):
            MetaModelProvider(api_key='')
        with self.assertRaises(ValueError):
            MetaModelProvider(api_key='valid', model_id='')
        with self.assertRaises(ValueError):
            MetaModelProvider(api_key='valid', base_url='ftp://not-http')
