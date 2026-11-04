"""Small synchronous provider boundary for the drafting worker."""

from __future__ import annotations

import http.client
import ipaddress
import json
import math
import re
import socket
import threading
import time
from dataclasses import dataclass
from typing import Protocol, runtime_checkable
from urllib.parse import urlsplit


@dataclass(frozen=True)
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class ModelResult:
    text: str
    model_id: str
    usage: TokenUsage | None
    finish_reason: str


class ProviderError(Exception):
    """Safe to expose message/code; retryable never means retry automatically."""

    def __init__(self, code: str, message: str, retryable: bool):
        super().__init__(message)
        self.code = code
        self.retryable = retryable


@runtime_checkable
class ModelProvider(Protocol):
    def generate(self, prompt: str, max_output_tokens: int, timeout_s: float) -> ModelResult:
        """Return a completion or raise ProviderError; never return error text."""
        ...


DEFAULT_META_MODEL_ID = 'muse-spark-1.3'


def validate_request(prompt: str, max_output_tokens: int, timeout_s: float) -> None:
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError('prompt must be a nonempty string')
    if type(max_output_tokens) is not int or not 1 <= max_output_tokens <= 512:
        raise ValueError('max_output_tokens must be an integer from 1 to 512')
    if (type(timeout_s) not in (int, float) or not 0 < timeout_s <= 120
            or not math.isfinite(timeout_s)):
        raise ValueError('timeout_s must be finite and greater than 0, up to 120 seconds')


class LocalModelProvider:
    """One non-streaming HTTP request to an explicit local vLLM-compatible API.

    Uses no environment proxies, redirects, retries, cloud client or model fallback.
    A transport timeout closes the socket; server inference may still be running.
    The A-P3 worker must retain admission until server completion/abort is confirmed.
    """

    _MAX_RESPONSE_BYTES = 1024 * 1024
    _LOCAL_NAMES = ('localhost',)

    def __init__(self, base_url: str, model_id: str):
        try:
            url = urlsplit(base_url)
            host = url.hostname
            local = host in self._LOCAL_NAMES
            if host and not local:
                address = ipaddress.ip_address(host)
                local = address.is_private or address in ipaddress.ip_network('100.64.0.0/10')
            port = 80 if url.port is None else url.port
            valid = (url.scheme == 'http' and local and not url.username
                     and not url.password and not url.query and not url.fragment
                     and url.path.rstrip('/') == '/v1' and 1 <= port <= 65535
                     and not any(c.isspace() for c in base_url))
        except (ValueError, TypeError, AttributeError):
            valid = False
        if not valid:
            raise ValueError('base_url must be an explicit local HTTP /v1 endpoint without credentials')
        if (not isinstance(model_id, str) or not model_id.strip()
                or model_id != model_id.strip() or any(ord(c) < 32 for c in model_id)):
            raise ValueError('model_id must be an explicit nonempty model identifier')
        self.host = host
        self.port = port
        self.model_id = model_id

    def generate(self, prompt: str, max_output_tokens: int, timeout_s: float) -> ModelResult:
        validate_request(prompt, max_output_tokens, timeout_s)
        payload = {'model': self.model_id, 'messages': [
            {'role': 'user', 'content': prompt}], 'max_tokens': max_output_tokens,
            'temperature': 0, 'stream': False}
        return self._parse(self._request('POST', '/v1/chat/completions', payload, timeout_s))

    def count_input_tokens(self, prompt: str, timeout_s: float) -> int:
        validate_request(prompt, 512, timeout_s)
        raw = self._request('POST', '/tokenize', {'model': self.model_id, 'messages': [
            {'role': 'user', 'content': prompt}], 'add_generation_prompt': True}, timeout_s)
        try:
            count = json.loads(raw)['count']
            if type(count) is not int or count < 0:
                raise ValueError
            return count
        except (ValueError, TypeError, KeyError, RecursionError):
            raise ProviderError('provider_invalid_response', 'Local tokenizer returned an invalid count.', False) from None

    def is_idle(self, timeout_s: float = 5) -> bool:
        validate_request('idle probe', 1, timeout_s)
        raw = self._request('GET', '/metrics', None, timeout_s)
        try:
            metrics = {'running': [], 'waiting': []}
            for line in raw.decode('utf-8').splitlines():
                match = re.fullmatch(r'vllm:num_requests_(running|waiting)(?:\{[^\n]*\})?\s+(\S+)', line)
                if match:
                    count = float(match[2])
                    if not math.isfinite(count) or count < 0:
                        raise ValueError
                    metrics[match[1]].append(count)
            if not all(metrics.values()):
                raise ValueError
            return all(count == 0 for counts in metrics.values() for count in counts)
        except (ValueError, UnicodeError):
            raise ProviderError('provider_invalid_response', 'Could not confirm local model idleness.', True) from None

    def _request(self, method: str, path: str, payload: dict | None, timeout_s: float) -> bytes:
        body = json.dumps(payload).encode('utf-8') if payload is not None else None
        deadline = time.monotonic() + timeout_s
        connection = http.client.HTTPConnection(self.host, self.port, timeout=timeout_s)
        expired = threading.Event()
        timer = None
        try:
            connection.connect()
            transport = connection.sock

            def expire() -> None:
                expired.set()
                try:
                    transport.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

            # Shutdown interrupts even a peer that trickles headers/body forever.
            timer = threading.Timer(max(0, deadline - time.monotonic()), expire)
            timer.daemon = True
            timer.start()
            connection.request(method, path, body=body,
                               headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
            with connection.getresponse() as response:
                status = response.status
                if 300 <= status < 400:
                    raise ProviderError('provider_redirect', 'Local provider redirects are disabled.', False)
                if status == 429:
                    raise ProviderError('provider_busy', 'Local provider is busy.', True)
                if status >= 500:
                    raise ProviderError('provider_unavailable', 'Local provider is unavailable.', True)
                if status != 200:
                    raise ProviderError('provider_rejected', 'Local provider rejected the request.', False)
                raw = response.read(self._MAX_RESPONSE_BYTES + 1)
            if expired.is_set() or time.monotonic() >= deadline:
                raise TimeoutError
        except (OSError, http.client.HTTPException) as exc:
            if expired.is_set() or isinstance(exc, TimeoutError):
                raise ProviderError('provider_timeout',
                                    'Local provider timed out; inference may still be running.', True) from None
            raise ProviderError('provider_unavailable', 'Could not complete the local model request.', True) from None
        finally:
            if timer is not None:
                timer.cancel()
                timer.join()
            connection.close()
        if len(raw) > self._MAX_RESPONSE_BYTES:
            raise ProviderError('provider_invalid_response', 'Local provider response exceeded its size limit.', False)
        return raw

    def _parse(self, raw: bytes) -> ModelResult:
        try:
            if len(raw) > self._MAX_RESPONSE_BYTES:
                raise ValueError
            payload = json.loads(raw)
            if payload['model'] != self.model_id or len(payload['choices']) != 1:
                raise ValueError
            choice = payload['choices'][0]
            text = choice['message']['content']
            reason = choice['finish_reason']
            if not isinstance(text, str) or not text.strip() or reason not in ('stop', 'length'):
                raise ValueError
            usage = None
            if payload.get('usage') is not None:
                counts = [payload['usage'][key] for key in
                          ('prompt_tokens', 'completion_tokens', 'total_tokens')]
                if any(type(n) is not int or n < 0 for n in counts) or counts[0] + counts[1] != counts[2]:
                    raise ValueError
                usage = TokenUsage(*counts)
            return ModelResult(text=text, model_id=self.model_id, usage=usage, finish_reason=reason)
        except (ValueError, KeyError, IndexError, TypeError, UnicodeError, RecursionError):
            raise ProviderError('provider_invalid_response', 'Local provider returned an invalid completion.', False) from None


class OllamaModelProvider(LocalModelProvider):
    """Development-only inference on a teammate's own machine through Ollama.

    Uses the native chat API because the OpenAI-compatible route cannot set the
    context size, and Ollama silently truncates prompts that exceed it. Ollama has
    no tokenizer or running-request endpoint, so token counts are estimates and
    idle means reachable. Results do not count as Orin acceptance.
    """

    _LOCAL_NAMES = ('localhost', 'host.docker.internal')
    _NUM_CTX = 8192 + 512
    # Fixes the reply's shape only. Small models otherwise return citations as an
    # object; the citation checks still decide whether the content is valid.
    _DRAFT_FORMAT = {'type': 'object', 'required': ['text', 'citations', 'insufficient_evidence'], 'properties': {
        'text': {'type': 'string'}, 'insufficient_evidence': {'type': 'boolean'},
        'citations': {'type': 'array', 'items': {'type': 'object', 'required': ['source_id', 'quote'], 'properties': {
            'source_id': {'type': 'string'}, 'quote': {'type': 'string'}}}}}}

    def generate(self, prompt: str, max_output_tokens: int, timeout_s: float) -> ModelResult:
        validate_request(prompt, max_output_tokens, timeout_s)
        payload = {'model': self.model_id, 'messages': [{'role': 'user', 'content': prompt}],
                   'stream': False, 'think': False, 'format': self._DRAFT_FORMAT,
                   'options': {'num_ctx': self._NUM_CTX, 'num_predict': max_output_tokens, 'temperature': 0}}
        return self._parse(self._request('POST', '/api/chat', payload, timeout_s))

    def count_input_tokens(self, prompt: str, timeout_s: float) -> int:
        validate_request(prompt, 512, timeout_s)
        # Three bytes per token overestimates English, keeping prompts within num_ctx.
        return len(prompt.encode('utf-8')) // 3 + 32

    def is_idle(self, timeout_s: float = 5) -> bool:
        validate_request('idle probe', 1, timeout_s)
        self._request('GET', '/api/version', None, timeout_s)
        return True

    def _parse(self, raw: bytes) -> ModelResult:
        try:
            payload = json.loads(raw)
            text = payload['message']['content']
            reason = payload['done_reason']
            if (payload['model'] != self.model_id or payload['done'] is not True
                    or not isinstance(text, str) or not text.strip() or reason not in ('stop', 'length')):
                raise ValueError
            prompt_tokens, output_tokens = payload.get('prompt_eval_count'), payload.get('eval_count')
            usage = None
            if type(prompt_tokens) is int and type(output_tokens) is int:
                usage = TokenUsage(prompt_tokens, output_tokens, prompt_tokens + output_tokens)
            return ModelResult(text=text, model_id=self.model_id, usage=usage, finish_reason=reason)
        except (ValueError, KeyError, TypeError, UnicodeError, RecursionError):
            raise ProviderError('provider_invalid_response', 'Ollama returned an invalid completion.', False) from None


class MetaModelProvider:
    """Synchronous provider for Meta's Model API (dev.meta.ai / api.meta.ai).

    Uses HTTPS chat completions with Bearer token authentication.
    Drop-in OpenAI-compatible chat format.
    """

    _MAX_RESPONSE_BYTES = 1024 * 1024
    _ALLOWED_HOSTS = frozenset({'api.meta.ai', 'dev.meta.ai'})

    def __init__(
        self,
        api_key: str,
        model_id: str = DEFAULT_META_MODEL_ID,
        base_url: str = 'https://api.meta.ai/v1'
    ):
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError('api_key must be an explicit nonempty token')
        if (not isinstance(model_id, str) or not model_id.strip()
                or model_id != model_id.strip() or len(model_id) > 200
                or any(ord(char) < 32 or ord(char) == 127 for char in model_id)):
            raise ValueError('model_id must be an explicit nonempty model identifier')
        try:
            url = urlsplit(base_url)
            host = url.hostname
            port = url.port or (443 if url.scheme == 'https' else 80)
            try:
                loopback = host == 'localhost' or (
                    host is not None and ipaddress.ip_address(host).is_loopback
                )
            except ValueError:
                loopback = False
            valid_url = (
                host is not None
                and (
                    (url.scheme == 'https' and host in self._ALLOWED_HOSTS and port == 443)
                    or (url.scheme == 'http' and loopback)
                )
                and not url.username and not url.password and not url.query and not url.fragment
                and url.path.rstrip('/') in ('', '/v1')
                and 1 <= port <= 65535
            )
        except ValueError:
            valid_url = False
        if not valid_url:
            raise ValueError('base_url must use Meta HTTPS or loopback HTTP for local tests')
        self.api_key = api_key.strip()
        self.model_id = model_id.strip()
        self.is_https = url.scheme == 'https'
        self.host = host
        self.port = port
        self.base_path = url.path.rstrip('/')

    def generate(self, prompt: str, max_output_tokens: int, timeout_s: float) -> ModelResult:
        validate_request(prompt, max_output_tokens, timeout_s)
        effective_tokens = max(max_output_tokens, 1500)
        payload = {
            'model': self.model_id,
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': effective_tokens,
            'temperature': 0.1,
            'stream': False
        }
        path = f"{self.base_path}/chat/completions" if self.base_path else "/chat/completions"
        raw = self._request('POST', path, payload, timeout_s)
        return self._parse(raw)

    def count_input_tokens(self, prompt: str, timeout_s: float) -> int:
        validate_request(prompt, 512, timeout_s)
        # The API has no tokenizer endpoint; use a conservative UTF-8 byte bound.
        return len(prompt.encode('utf-8'))

    def is_idle(self, timeout_s: float = 5) -> bool:
        return True

    def _request(self, method: str, path: str, payload: dict | None, timeout_s: float) -> bytes:
        body = json.dumps(payload).encode('utf-8') if payload is not None else None
        deadline = time.monotonic() + timeout_s
        conn_cls = http.client.HTTPSConnection if self.is_https else http.client.HTTPConnection
        connection = conn_cls(self.host, self.port, timeout=timeout_s)
        expired = threading.Event()
        timer = None
        try:
            connection.connect()
            transport = connection.sock

            def expire() -> None:
                expired.set()
                try:
                    transport.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

            timer = threading.Timer(max(0, deadline - time.monotonic()), expire)
            timer.daemon = True
            timer.start()
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            connection.request(method, path, body=body, headers=headers)
            with connection.getresponse() as response:
                status = response.status
                if status in (401, 403):
                    raise ProviderError('provider_unauthorized', 'Meta API rejected credentials; verify your API key.', False)
                if status == 429:
                    raise ProviderError('provider_busy', 'Meta API rate limit reached.', True)
                if status >= 500:
                    raise ProviderError('provider_unavailable', 'Meta API service unavailable.', True)
                if status != 200:
                    raise ProviderError('provider_rejected', f'Meta API rejected the request ({status}).', False)
                raw = response.read(self._MAX_RESPONSE_BYTES + 1)
            if expired.is_set() or time.monotonic() >= deadline:
                raise TimeoutError
        except (OSError, http.client.HTTPException) as exc:
            if expired.is_set() or isinstance(exc, TimeoutError):
                raise ProviderError('provider_timeout', 'Meta API timed out.', True) from None
            raise ProviderError('provider_unavailable', f'Could not complete the Meta API request: {exc}', True) from None
        finally:
            if timer is not None:
                timer.cancel()
                timer.join()
            connection.close()
        if len(raw) > self._MAX_RESPONSE_BYTES:
            raise ProviderError('provider_invalid_response', 'Meta API response exceeded size limit.', False)
        return raw

    def _parse(self, raw: bytes) -> ModelResult:
        try:
            payload = json.loads(raw)
            if payload['model'] != self.model_id or len(payload['choices']) != 1:
                raise ValueError
            choice = payload['choices'][0]
            msg = choice['message']
            content = msg.get('content')
            if isinstance(content, str):
                text = content
            elif isinstance(content, list):
                parts = []
                for part in content:
                    if isinstance(part, str):
                        parts.append(part)
                    elif isinstance(part, dict) and isinstance(part.get('text'), str):
                        parts.append(part['text'])
                text = '\n'.join(parts)
            elif content is None:
                text = choice.get('text', '')
            else:
                raise ValueError
            if not text and isinstance(choice.get('text'), str):
                text = choice['text']
            reason = choice['finish_reason']
            if (not isinstance(text, str) or (not text.strip() and reason != 'length')
                    or reason not in ('stop', 'length')):
                raise ValueError
            usage = None
            if payload.get('usage') is not None:
                counts = [payload['usage'][key] for key in
                          ('prompt_tokens', 'completion_tokens', 'total_tokens')]
                if (any(type(count) is not int or count < 0 for count in counts)
                        or counts[0] + counts[1] != counts[2]):
                    raise ValueError
                usage = TokenUsage(*counts)
            return ModelResult(text=text, model_id=self.model_id, usage=usage, finish_reason=reason)
        except (ValueError, KeyError, IndexError, TypeError, UnicodeError, RecursionError):
            raise ProviderError('provider_invalid_response', 'Meta API returned an invalid response structure.', False) from None
