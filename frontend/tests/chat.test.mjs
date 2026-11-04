import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import ts from 'typescript';

const source = await readFile(
  new URL('../src/lib/api.ts', import.meta.url),
  'utf8'
);

const compiled = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.ESNext,
    target: ts.ScriptTarget.ES2022,
  },
}).outputText;

const { api, ApiError } = await import(
  `data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`
);

test('sends research chat request with same-origin credentials and parses verified citations', async () => {
  const originalFetch = globalThis.fetch;

  try {
    globalThis.fetch = async (url, options) => {
      assert.equal(url, '/api/v2/chat');
      assert.equal(options.method, 'POST');
      assert.equal(options.credentials, 'same-origin');

      const body = JSON.parse(options.body);
      assert.equal(body.message, 'What sensor architectures are evaluated?');
      assert.equal(body.proposal_id, 'prop-123');
      assert.equal(body.history.length, 1);

      return Response.json({
        response: 'Low-power soil sensors were evaluated across agricultural testbeds [src-1].',
        citations: [
          {
            source_id: 'src-1',
            version: 'v1',
            content_hash: 'h1',
            title: 'Wireless Soil Monitoring',
            origin: 'https://doi.org/10.1000/soil',
            quote: 'Low-power soil sensors were evaluated across agricultural testbeds',
          },
        ],
        insufficient_evidence: false,
        sources_consulted: [
          { id: 'src-1', title: 'Wireless Soil Monitoring', origin: 'https://doi.org/10.1000/soil', is_public: true },
        ],
      });
    };

    const result = await api.chat({
      message: 'What sensor architectures are evaluated?',
      history: [{ role: 'user', content: 'Hello' }],
      proposal_id: 'prop-123',
    });

    assert.equal(result.citations.length, 1);
    assert.equal(result.citations[0].source_id, 'src-1');
    assert.equal(result.insufficient_evidence, false);
    assert.match(result.response, /soil sensors/);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('propagates API error when chat request fails or unauthorized', async () => {
  const originalFetch = globalThis.fetch;

  try {
    globalThis.fetch = async () => {
      return new Response(
        JSON.stringify({
          error: {
            code: 'unauthorized',
            message: 'Authentication required for research chat',
            retryable: false,
          },
        }),
        { status: 401 }
      );
    };

    await assert.rejects(
      async () => {
        await api.chat({ message: 'Hello' });
      },
      (err) => {
        assert(err instanceof ApiError);
        assert.equal(err.status, 401);
        assert.equal(err.code, 'unauthorized');
        assert.equal(err.message, 'Authentication required for research chat');
        return true;
      }
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});
