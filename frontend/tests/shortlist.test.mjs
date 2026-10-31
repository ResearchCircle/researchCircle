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
const { canChangeTeam, canAttachToProposal, sourceKindLabel, editShortlistDraft, acknowledgeShortlistDraft } = load('../src/lib/shortlist.ts');
const { api } = load('../src/lib/api.ts');
const originalFetch = global.fetch;
afterEach(() => { global.fetch = originalFetch; });

test('team change preserves the current context when dirty-edit confirmation is cancelled', () => {
  let confirmations = 0;
  const cancel = () => { confirmations++; return false; };
  assert.equal(canChangeTeam('team-a', 'team-b', true, cancel), false);
  assert.equal(confirmations, 1);
  assert.equal(canChangeTeam('team-a', 'team-a', true, cancel), true);
  assert.equal(confirmations, 1);
  assert.equal(canChangeTeam('team-a', 'team-b', false, cancel), true);
  assert.equal(confirmations, 1);
  assert.equal(canChangeTeam('team-a', 'team-b', true, () => true), true);
});

test('shortlist attachment requires an editable proposal in the selected team', () => {
  assert.equal(canAttachToProposal('team-a', { team_id: 'team-a', role: 'editor' }), true);
  assert.equal(canAttachToProposal('team-a', { team_id: 'team-a', role: 'owner' }), true);
  assert.equal(canAttachToProposal('team-a', { team_id: 'team-b', role: 'owner' }), false);
  assert.equal(canAttachToProposal('team-a', { team_id: 'team-a', role: 'viewer' }), false);
  assert.equal(canAttachToProposal('team-a', null), false);
});

test('publication authorship evidence is labelled without claiming a resolved researcher profile', () => {
  assert.equal(sourceKindLabel('researcher', 'public'), 'Listed author');
  assert.equal(sourceKindLabel('researcher', 'synthetic'), 'Researcher example');
  assert.equal(sourceKindLabel('paper', 'public'), 'Paper');
});

test('shortlist persistence uses team-scoped paths, entry IDs for mutations, and source IDs for insertion', async () => {
  const calls = [];
  global.fetch = async (url, options) => { calls.push({ url, options }); return options.method === 'DELETE' ? new Response(null, { status: 204 }) : new Response(JSON.stringify({ items: [] })); };
  await api.shortlist('team-a');
  await api.addShortlist('team-a', 'source-a');
  await api.updateShortlist('team-a', 'entry-a', 'Keep for calibration evidence.');
  await api.removeShortlist('team-a', 'entry-a');
  assert.deepEqual(calls.map(call => call.url), ['/api/v2/teams/team-a/shortlist', '/api/v2/teams/team-a/shortlist', '/api/v2/teams/team-a/shortlist/entry-a', '/api/v2/teams/team-a/shortlist/entry-a']);
  assert.deepEqual(JSON.parse(calls[1].options.body), { source_id: 'source-a' });
  assert.equal(calls[2].options.method, 'PATCH');
  assert.deepEqual(JSON.parse(calls[2].options.body), { note: 'Keep for calibration evidence.' });
  assert.equal(calls[3].options.method, 'DELETE');
});


test('session draft maps preserve another team and acknowledge only the submitted note', () => {
  const first = editShortlistDraft({}, 'team-a', 'entry-a', 'unsaved note', 'saved note');
  const second = editShortlistDraft(first, 'team-b', 'entry-b', 'another team note', '');
  assert.equal(second['team-a']['entry-a'], 'unsaved note');
  assert.equal(second['team-b']['entry-b'], 'another team note');
  assert.deepEqual(acknowledgeShortlistDraft(second, 'team-a', 'entry-a', 'older note'), second);
  const saved = acknowledgeShortlistDraft(second, 'team-a', 'entry-a', 'unsaved note');
  assert.equal(saved['team-a']?.['entry-a'], undefined);
  assert.equal(saved['team-b']['entry-b'], 'another team note');
  const pristine = editShortlistDraft(first, 'team-a', 'entry-a', 'saved note', 'saved note');
  assert.equal(pristine['team-a']?.['entry-a'], undefined);
});
