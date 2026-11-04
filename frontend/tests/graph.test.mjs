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

test('fetches public knowledge graph data with same-origin credentials', async () => {
  const originalFetch = globalThis.fetch;

  try {
    globalThis.fetch = async (url, options) => {
      assert.equal(url, '/api/v2/graph?limit=150');
      assert.equal(options.credentials, 'same-origin');

      return Response.json({
        nodes: [
          {
            id: 'src-1',
            name: 'Dr. Jane Doe',
            type: 'faculty',
            evidence_kind: 'public',
            metadata: { department: 'Computer Science' },
          },
          {
            id: 'src-2',
            name: 'Autonomous Systems Survey',
            type: 'paper',
            evidence_kind: 'public',
            metadata: { year: 2024 },
          },
        ],
        links: [
          {
            source: 'src-1',
            target: 'src-2',
            relationship: 'authored',
          },
        ],
      });
    };

    const graph = await api.graph();
    assert.equal(graph.nodes.length, 2);
    assert.equal(graph.links.length, 1);
    assert.equal(graph.nodes[0].name, 'Dr. Jane Doe');
    assert.equal(graph.links[0].relationship, 'authored');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('encodes topic filter in graph query parameters', async () => {
  const originalFetch = globalThis.fetch;

  try {
    globalThis.fetch = async (url, options) => {
      assert.equal(url, '/api/v2/graph?limit=200&topic=sensor+networks');
      assert.equal(options.credentials, 'same-origin');

      return Response.json({
        nodes: [],
        links: [],
      });
    };

    const graph = await api.graph(200, 'sensor networks');
    assert.deepEqual(graph, { nodes: [], links: [] });
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('encodes center_id and hops for ego-network subgraph queries', async () => {
  const originalFetch = globalThis.fetch;

  try {
    globalThis.fetch = async (url, options) => {
      assert.equal(url, '/api/v2/graph?limit=150&center_id=src-1&hops=2');
      assert.equal(options.credentials, 'same-origin');

      return Response.json({
        nodes: [
          {
            id: 'src-1',
            name: 'Dr. Jane Doe',
            type: 'faculty',
            is_center: true,
            hop: 0,
            x: 0,
            y: 0,
            cluster: 'Computing & Information Sciences',
            cluster_color: '#2563eb',
          },
        ],
        links: [],
        clusters: [
          {
            id: 'Computing & Information Sciences',
            name: 'Computing & Information Sciences',
            count: 1,
            color: '#2563eb',
          },
        ],
        center_node: {
          id: 'src-1',
          name: 'Dr. Jane Doe',
          type: 'faculty',
        },
      });
    };

    const graph = await api.graph(150, undefined, 'src-1', 2);
    assert.equal(graph.nodes.length, 1);
    assert.equal(graph.nodes[0].is_center, true);
    assert.equal(graph.nodes[0].x, 0);
    assert.equal(graph.clusters.length, 1);
    assert.equal(graph.center_node.id, 'src-1');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('propagates API errors when graph retrieval fails', async () => {
  const originalFetch = globalThis.fetch;

  try {
    globalThis.fetch = async () =>
      Response.json(
        {
          error: {
            code: 'service_unavailable',
            message: 'Graph database currently unavailable',
          },
        },
        { status: 503 }
      );

    await assert.rejects(
      api.graph(),
      (error) =>
        error instanceof ApiError &&
        error.status === 503 &&
        error.code === 'service_unavailable'
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});
