import { test, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import Module from 'node:module';
import ts from 'typescript';
import { fileURLToPath } from 'node:url';
const directory = path.dirname(fileURLToPath(import.meta.url));
function load(relative) {
  const filename = path.resolve(directory, relative);
  const loaded = new Module(filename);
  loaded.paths = Module._nodeModulePaths(path.dirname(filename));
  loaded._compile(ts.transpileModule(fs.readFileSync(filename, 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 } }).outputText, filename);
  return loaded.exports;
}
const { outcomeAttempt, localDeadline, isTerminal, RequestScope } = load('../src/lib/pursuits.ts');
const { api } = load('../src/lib/api.ts');
const originalTimezone = process.env.TZ;
const originalFetch = global.fetch;
afterEach(() => { process.env.TZ = originalTimezone; global.fetch = originalFetch; });

test('outcome retries retain their key only for the identical proposal and payload', () => {
  const first = outcomeAttempt(null, 'proposal-a', 'won', 'Award 1', 'key-one');
  const retry = outcomeAttempt(first, 'proposal-a', 'won', 'Award 1', 'key-two');
  assert.equal(retry.key, 'key-one');
  assert.equal(outcomeAttempt(first, 'proposal-a', 'lost', 'Award 1', 'key-two').key, 'key-two');
  assert.equal(outcomeAttempt(first, 'proposal-b', 'won', 'Award 1', 'key-two').key, 'key-two');
  assert.equal(outcomeAttempt(first, 'proposal-a', 'won', 'Award 2', 'key-two').key, 'key-two');
});

test('browser-local deadline conversion accounts for summer/winter offset and leaves unknown deadline null', () => {
  process.env.TZ = 'America/New_York';
  assert.deepEqual(localDeadline('2026-07-15T09:00'), { deadline: '2026-07-15T13:00:00.000Z', deadline_timezone: 'America/New_York' });
  assert.deepEqual(localDeadline('2026-12-15T09:00'), { deadline: '2026-12-15T14:00:00.000Z', deadline_timezone: 'America/New_York' });
  assert.deepEqual(localDeadline(''), { deadline: null, deadline_timezone: null });
  assert.throws(() => localDeadline('2026-03-08T02:30'), /does not exist/);
  assert.throws(() => localDeadline('invalid'), /valid/);
});

test('terminal outcomes are read-only and new request scope rejects stale responses', () => {
  assert.equal(isTerminal('submitted'), false);
  for (const state of ['won', 'lost', 'withdrawn']) assert.equal(isTerminal(state), true);
  const scope = new RequestScope();
  const previous = scope.begin();
  const current = scope.begin();
  assert.equal(scope.current(previous), false);
  assert.equal(scope.current(current), true);
  scope.invalidate();
  assert.equal(scope.current(current), false);
});

test('manual opportunity, status and outcome requests use the documented paths and stable retry key', async () => {
  const calls = [];
  global.fetch = async (url, options) => { calls.push({ url, options }); return new Response(JSON.stringify({ items: [], pursuit: null })); };
  await api.opportunities();
  await api.createOpportunity({ team_id: 'team-a', title: 'Manual call', source_url: null, deadline: null, deadline_timezone: null, notes: '', eligibility: 'unknown' });
  await api.pursuit('proposal-a');
  await api.updatePursuit('proposal-a', { state: 'submitted', opportunity_id: null });
  await api.recordOutcome('proposal-a', { outcome: 'won', idempotency_key: 'retained-key', award_reference: null });
  await api.outcomes('proposal-a');
  assert.deepEqual(calls.map(call => call.url), ['/api/v2/opportunities', '/api/v2/opportunities', '/api/v2/proposals/proposal-a/pursuit', '/api/v2/proposals/proposal-a/pursuit', '/api/v2/proposals/proposal-a/outcomes', '/api/v2/proposals/proposal-a/outcomes']);
  assert.equal(calls[3].options.method, 'PUT');
  assert.deepEqual(JSON.parse(calls[3].options.body), { state: 'submitted', opportunity_id: null });
  assert.equal(JSON.parse(calls[4].options.body).idempotency_key, 'retained-key');
  assert.equal(JSON.parse(calls[1].options.body).eligibility, 'unknown');
});
