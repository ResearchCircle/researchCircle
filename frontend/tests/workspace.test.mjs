import { test, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import Module from 'node:module';
import ts from 'typescript';
const __dirname = path.dirname(fileURLToPath(import.meta.url));

function loadTypeScript(relativePath) {
  const filename = path.resolve(__dirname, relativePath);
  const compiled = ts.transpileModule(fs.readFileSync(filename, 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 } }).outputText;
  const loaded = new Module(filename);
  loaded.filename = filename;
  loaded.paths = Module._nodeModulePaths(path.dirname(filename));
  loaded._compile(compiled, filename);
  return loaded.exports;
}
const { hasEdits, canApplyDraft, appendSuggestion, safeOrigin } = loadTypeScript('../src/lib/editor.ts');
const { api, ApiError } = loadTypeScript('../src/lib/api.ts');
const originalFetch = global.fetch;
afterEach(() => { global.fetch = originalFetch; });
const proposal = { id: 'proposal-a', revision: 4, title: 'Research', content: 'Current text', selected_sources: [{ id: 'source-a' }, { id: 'source-b' }] };
const job = { proposal_id: 'proposal-a', base_revision: 4, state: 'succeeded', output: { base_revision: 4, text: 'Suggested text' } };

test('draft acceptance rejects stale, unsaved, failed, or unrelated suggestions', () => {
  assert.equal(canApplyDraft(job, proposal, false), true);
  assert.equal(canApplyDraft(job, proposal, true), false);
  assert.equal(canApplyDraft(job, { ...proposal, revision: 5 }, false), false);
  assert.equal(canApplyDraft({ ...job, output: { ...job.output, base_revision: 3 } }, proposal, false), false);
  assert.equal(canApplyDraft({ ...job, proposal_id: 'unrelated' }, proposal, false), false);
  assert.equal(canApplyDraft({ ...job, state: 'failed' }, proposal, false), false);
  assert.equal(canApplyDraft({ ...job, output: null }, proposal, false), false);
});

test('dirty detection includes source selections but ignores their order', () => {
  assert.equal(hasEdits(proposal, 'Research', 'Current text', ['source-b', 'source-a']), false);
  assert.equal(hasEdits(proposal, 'Changed title', 'Current text', ['source-a', 'source-b']), true);
  assert.equal(hasEdits(proposal, 'Research', 'Changed content', ['source-a', 'source-b']), true);
  assert.equal(hasEdits(proposal, 'Research', 'Current text', ['source-a']), true);
});

test('acceptance appends instead of replacing existing proposal content', () => {
  assert.equal(appendSuggestion('Current text\n', 'Suggestion'), 'Current text\n\nSuggestion');
  assert.equal(appendSuggestion('', 'Suggestion'), 'Suggestion');
});

test('external evidence links reject executable and relative URLs', () => {
  assert.equal(safeOrigin('https://example.org/paper'), 'https://example.org/paper');
  assert.equal(safeOrigin('javascript:alert(1)'), undefined);
  assert.equal(safeOrigin('data:text/html,example'), undefined);
  assert.equal(safeOrigin('/private-path'), undefined);
  assert.equal(safeOrigin('Sample document'), undefined);
});

test('save sends expected revision and selections to same-origin cookie API', async () => {
  let observed;
  global.fetch = async (url, options) => { observed = { url, options }; return new Response(JSON.stringify({ ...proposal, revision: 5 })); };
  const body = { expected_revision: 4, title: 'Research', content: 'Updated', selected_source_ids: ['source-a'] };
  const result = await api.save('proposal-a', body);
  assert.equal(observed.url, '/api/v2/proposals/proposal-a');
  assert.equal(observed.options.method, 'PATCH');
  assert.equal(observed.options.credentials, 'same-origin');
  assert.equal(observed.options.cache, 'no-store');
  assert.deepEqual(JSON.parse(observed.options.body), body);
  assert.equal(result.revision, 5);
});

test('conflict and queue errors keep HTTP status and server message', async () => {
  global.fetch = async () => new Response(JSON.stringify({ error: { code: 'stale_revision', message: 'Revision changed', retryable: false } }), { status: 409 });
  await assert.rejects(api.save('proposal-a', {}), error => error instanceof ApiError && error.status === 409 && error.message === 'Revision changed');
  global.fetch = async () => new Response(JSON.stringify({ error: { code: 'queue_full', message: 'Draft queue is full', retryable: true } }), { status: 429 });
  await assert.rejects(api.draft('proposal-a', {}), error => error.code === 'queue_full' && error.retryable === true);
});

test('network failure is surfaced and logout accepts empty success response', async () => {
  global.fetch = async () => { throw new TypeError('network failed'); };
  await assert.rejects(api.me(), error => error instanceof ApiError && error.code === 'network_error' && error.retryable);
  global.fetch = async () => new Response(null, { status: 204 });
  assert.equal(await api.logout(), undefined);
});

test('search encodes query and submits real selected source IDs for draft jobs', async () => {
  const calls = [];
  global.fetch = async (url, options) => { calls.push([url, options]); return new Response(JSON.stringify({ items: [] })); };
  await api.search('climate & energy');
  await api.draft('proposal-a', { section: 'Approach', instruction: 'Compare', source_ids: ['source-a'] });
  assert.equal(calls[0][0], '/api/v2/search?q=climate%20%26%20energy');
  assert.deepEqual(JSON.parse(calls[1][1].body).source_ids, ['source-a']);
});


test('export downloads saved Markdown and surfaces server failure', async () => {
  global.fetch = async url => { assert.equal(url, '/api/v2/proposals/proposal-a/export'); return new Response('# Saved research\n', { headers: { 'Content-Type': 'text/markdown' } }); };
  assert.equal(await (await api.exportMarkdown('proposal-a')).text(), '# Saved research\n');
  global.fetch = async () => new Response(JSON.stringify({ error: { code: 'forbidden', message: 'Membership required' } }), { status: 403 });
  await assert.rejects(api.exportMarkdown('proposal-a'), error => error.status === 403 && error.message === 'Membership required');
});
