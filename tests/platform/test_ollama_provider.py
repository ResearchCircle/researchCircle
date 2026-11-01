import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from deployment.dev import configure_development
from deployment.runtime import RuntimeConfig
from src.platform.models.provider import LocalModelProvider, OllamaModelProvider, ProviderError


class _Ollama(BaseHTTPRequestHandler):
    requests, reply, status = [], {}, 200

    def _send(self, body):
        raw = json.dumps(body).encode()
        self.send_response(type(self).status)
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        type(self).requests.append((self.path, body))
        self._send(type(self).reply)

    def do_GET(self):
        type(self).requests.append((self.path, None))
        self._send({'version': 'test'})

    def log_message(self, *args):
        pass


class OllamaProviderTests(unittest.TestCase):
    def setUp(self):
        _Ollama.requests, _Ollama.status = [], 200
        _Ollama.reply = {'model': 'small', 'message': {'role': 'assistant', 'content': '{"a":1}'},
                         'done': True, 'done_reason': 'stop', 'prompt_eval_count': 7, 'eval_count': 3}
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), _Ollama)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.provider = OllamaModelProvider(f'http://127.0.0.1:{self.server.server_port}/v1', 'small')

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def test_generate_sets_context_so_ollama_cannot_silently_truncate_sources(self):
        result = self.provider.generate('Write', 64, 5)
        path, body = _Ollama.requests[0]
        self.assertEqual(path, '/api/chat')
        self.assertEqual(body['options'], {'num_ctx': 8704, 'num_predict': 64, 'temperature': 0})
        self.assertIs(body['stream'], False)
        self.assertEqual(body['format']['properties']['citations']['type'], 'array')
        self.assertEqual(body['messages'], [{'role': 'user', 'content': 'Write'}])
        self.assertEqual((result.text, result.model_id, result.finish_reason), ('{"a":1}', 'small', 'stop'))
        self.assertEqual((result.usage.prompt_tokens, result.usage.completion_tokens, result.usage.total_tokens), (7, 3, 10))

    def test_truncated_generation_is_reported_as_length(self):
        _Ollama.reply = {**_Ollama.reply, 'done_reason': 'length'}
        self.assertEqual(self.provider.generate('Write', 64, 5).finish_reason, 'length')

    def test_usage_is_unknown_when_ollama_omits_counts(self):
        del _Ollama.reply['prompt_eval_count']
        self.assertIsNone(self.provider.generate('Write', 64, 5).usage)

    def test_different_model_or_malformed_reply_is_rejected(self):
        for reply in [{**_Ollama.reply, 'model': 'other'}, {**_Ollama.reply, 'done': False},
                      {**_Ollama.reply, 'done_reason': 'load'}, {**_Ollama.reply, 'message': {'content': ' '}}, {}]:
            _Ollama.reply = reply
            with self.subTest(reply=reply), self.assertRaises(ProviderError) as caught:
                self.provider.generate('Write', 64, 5)
            self.assertEqual(caught.exception.code, 'provider_invalid_response')

    def test_token_estimate_never_undercounts_typical_english_or_needs_the_server(self):
        prompt = 'research proposal evidence ' * 100
        count = self.provider.count_input_tokens(prompt, 5)
        self.assertGreaterEqual(count, len(prompt) // 3)
        self.assertLess(count, len(prompt))
        self.assertEqual(_Ollama.requests, [])

    def test_idle_means_reachable_and_unreachable_is_an_error(self):
        self.assertIs(self.provider.is_idle(5), True)
        self.assertEqual(_Ollama.requests, [('/api/version', None)])
        self.server.shutdown()
        self.server.server_close()
        with self.assertRaises(ProviderError):
            self.provider.is_idle(1)
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), _Ollama)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()


class OllamaEndpointTests(unittest.TestCase):
    def test_container_host_name_is_only_allowed_for_ollama(self):
        OllamaModelProvider('http://host.docker.internal:11434/v1', 'small')
        with self.assertRaises(ValueError):
            LocalModelProvider('http://host.docker.internal:11434/v1', 'small')

    def test_cloud_and_credentialed_endpoints_stay_rejected(self):
        for url in ['https://api.example.com/v1', 'http://api.example.com/v1', 'http://user:pw@localhost:11434/v1',
                    'http://host.docker.internal.example.com/v1', 'http://8.8.8.8:11434/v1']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                OllamaModelProvider(url, 'small')
        with self.assertRaises(ValueError):
            OllamaModelProvider('http://localhost:11434/v1', ' ')


class OllamaRuntimeTests(unittest.TestCase):
    ENV = {'TBR_MODEL_PROVIDER': 'ollama', 'TBR_MODEL_BASE_URL': 'http://host.docker.internal:11434/v1',
           'TBR_MODEL_ID': 'small', 'TBR_DATA_SOURCE': '/tmp/tbr-a', 'TBR_DATA_WORK': '/tmp/tbr-b'}

    def test_development_profile_accepts_ollama(self):
        self.assertEqual(RuntimeConfig.from_env(self.ENV).provider, 'ollama')

    def test_shared_demo_refuses_ollama(self):
        with self.assertRaises(ValueError):
            RuntimeConfig.from_env({**self.ENV, 'TBR_PROFILE': 'demo'})

    def test_dev_launcher_stays_development_and_defaults_to_the_docker_host(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'runtime.env'
            values = configure_development(path, 'ollama', None, 'small')
            self.assertEqual(values['TBR_PROFILE'], 'development')
            self.assertEqual(values['TBR_MODEL_BASE_URL'], 'http://host.docker.internal:11434/v1')
            with self.assertRaises(ValueError):
                configure_development(path, 'ollama', None, None)
