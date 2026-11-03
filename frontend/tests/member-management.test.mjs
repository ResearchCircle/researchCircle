
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

test('loads team members with the existing session', async () => {
  const originalFetch = globalThis.fetch;

  try {
    globalThis.fetch = async (url, options) => {
      assert.equal(url, '/api/v2/teams/team-1');
      assert.equal(options.credentials, 'same-origin');

      return Response.json({
        id: 'team-1',
        name: 'Research',
        role: 'owner',
        members: [
          {
            id: 'user-1',
            name: 'Test Owner',
            email: 'owner@example.test',
            role: 'owner',
          },
        ],
      });
    };

    const team = await api.teamDetails('team-1');
    assert.equal(team.members.length, 1);
    assert.equal(team.members[0].role, 'owner');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('updates member role using PATCH', async () => {
  const originalFetch = globalThis.fetch;

  try {
    globalThis.fetch = async (url, options) => {
      assert.equal(
        url,
        '/api/v2/teams/team-1/members/user-2'
      );
      assert.equal(options.method, 'PATCH');
      assert.equal(options.credentials, 'same-origin');
      assert.equal(
        options.headers['Content-Type'],
        'application/json'
      );
      assert.deepEqual(JSON.parse(options.body), {
        role: 'viewer',
      });

      return Response.json({
        id: 'user-2',
        name: 'Test Member',
        email: 'member@example.test',
        role: 'viewer',
      });
    };

    const result = await api.updateMemberRole(
      'team-1',
      'user-2',
      'viewer'
    );

    assert.equal(result.role, 'viewer');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('removes a member using DELETE', async () => {
  const originalFetch = globalThis.fetch;

  try {
    globalThis.fetch = async (url, options) => {
      assert.equal(
        url,
        '/api/v2/teams/team-1/members/user-2'
      );
      assert.equal(options.method, 'DELETE');

      return new Response(null, { status: 204 });
    };

    const result = await api.removeMember(
      'team-1',
      'user-2'
    );

    assert.equal(result, undefined);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('preserves owner-only authorization errors', async () => {
  const originalFetch = globalThis.fetch;

  try {
    globalThis.fetch = async () =>
      Response.json(
        {
          error: {
            code: 'forbidden',
            message: 'Owner access required',
          },
        },
        { status: 403 }
      );

    await assert.rejects(
      api.updateMemberRole('team-1', 'user-2', 'owner'),
      error =>
        error instanceof ApiError &&
        error.status === 403 &&
        error.code === 'forbidden'
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('surfaces last-owner protection errors', async () => {
  const originalFetch = globalThis.fetch;

  try {
    globalThis.fetch = async () =>
      Response.json(
        {
          error: {
            code: 'last_owner',
            message: 'Cannot remove the last owner',
          },
        },
        { status: 409 }
      );

    await assert.rejects(
      api.removeMember('team-1', 'user-1'),
      error =>
        error instanceof ApiError &&
        error.status === 409 &&
        error.message.includes('last owner')
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});
