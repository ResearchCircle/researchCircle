"""Run scripted drafts through real application routes and persisted workers.

Default: temporary SQLite. --postgres creates and retains a new simulation
database using the configured development connection. No model service is called.
"""
import argparse
import json
import os
from pathlib import Path
import secrets
from tempfile import TemporaryDirectory
from threading import Event
from uuid import uuid4

from fastapi.testclient import TestClient

from services.api.app import create_app
from src.platform.database import Database
from src.platform.drafting.fixtures import FixtureTokenCounter
from src.platform.drafting.service import DraftingService
from src.platform.drafting.worker import GenerationWorker
from src.platform.models.provider import validate_request
from .simulated_responses import SOURCE_TEXTS, response_for


class SimulationError(RuntimeError):
    """The message is a fixed scenario step, never a response or database error."""


def _check(condition, step):
    if not condition:
        raise SimulationError(step)


def _read(response, status, step):
    _check(response.status_code == status, step)
    return response.json()


class ScriptedProvider:
    def __init__(self, output, entered=None, release=None):
        self.output, self.entered, self.release = output, entered, release
        self.calls = 0

    def generate(self, prompt, max_output_tokens, timeout_s):
        validate_request(prompt, max_output_tokens, timeout_s)
        self.calls += 1
        if self.entered is not None:
            self.entered.set()
        if self.release is not None and not self.release.wait(timeout_s):
            raise TimeoutError('Scripted response was not released')
        return self.output


def run_scenarios(app, lease_path: Path) -> dict:
    """Use a fresh, initialized simulation database, never a user's workspace."""
    run_id = uuid4().hex
    password = secrets.token_urlsafe(24)
    cases = []
    with TestClient(app) as owner, TestClient(app) as editor:
        for client, name in ((owner, 'owner'), (editor, 'editor')):
            _read(client.post('/api/v2/auth/register', json={
                'email': f'simulation-{run_id}-{name}@example.test', 'name': f'Synthetic {name}',
                'password': password}), 201, 'register_simulation_users')
        team = _read(owner.post('/api/v2/teams', json={'name': 'Synthetic draft simulation'}), 201, 'create_team')
        invite = _read(owner.post(f"/api/v2/teams/{team['id']}/invitations", json={
            'email': f'simulation-{run_id}-editor@example.test', 'role': 'editor'}), 201, 'invite_editor')
        _read(editor.post(f"/api/v2/invitations/{invite['id']}/accept"), 200, 'accept_editor_invitation')
        original = 'Existing manual proposal text must be preserved.'
        proposal = _read(owner.post('/api/v2/proposals', json={
            'team_id': team['id'], 'title': 'Synthetic greenhouse protocol', 'content': original}), 201, 'create_proposal')
        path = f"/api/v2/proposals/{proposal['id']}"
        sources = [_read(owner.post(path + '/sources', json={
            'title': f'Synthetic evidence {index + 1}', 'text': text,
            'origin': 'Scripted simulation fixture; no public URL'}), 201, 'attach_synthetic_source')
            for index, text in enumerate(SOURCE_TEXTS)]
        source_ids = tuple(source['id'] for source in sources)
        proposal = _read(owner.patch(path, json={
            'expected_revision': proposal['revision'], 'selected_source_ids': list(source_ids)}), 200, 'save_evidence_selection')

        def enqueue(instruction):
            return _read(owner.post(path + '/jobs', json={
                'expected_revision': proposal['revision'], 'section': 'Methods',
                'instruction': instruction, 'source_ids': list(source_ids)}), 202, 'enqueue_scripted_job')

        def make_worker(provider):
            return GenerationWorker(app.state.jobs, DraftingService(provider, FixtureTokenCounter()), lease_path, lambda: True)

        def complete(case):
            instruction = ('Estimate the percentage crop-yield improvement and energy savings.' if case == 'insufficient'
                           else 'Describe the synthetic measurement protocol and its limits.')
            queued = enqueue(instruction)
            worker = make_worker(ScriptedProvider(response_for(case, source_ids)))
            try:
                worker.tick()
            finally:
                worker.close(wait=True)
            return _read(owner.get('/api/v2/jobs/' + queued['id']), 200, 'read_scripted_job')

        job = complete('two_source')
        _check(job['state'] == 'succeeded' and len(job['output']['citations']) == 2, 'two_source_citations')
        _check(job['output']['model_id'] == 'fixture-scripted-v1', 'fixture_provenance')
        accepted = owner.patch(path, json={'expected_revision': job['base_revision'],
            'content': original + '\n\n' + job['output']['text']})
        proposal = _read(accepted, 200, 'accept_scripted_suggestion')
        _check(proposal['content'].startswith(original), 'manual_text_preserved')
        exported = owner.get(path + '/export')
        _check(exported.status_code == 200 and all(source['content_hash'] in exported.text for source in sources), 'export_cited_snapshots')
        cases.append({'case': 'two_source', 'job_id': job['id'], 'state': job['state'], 'citations': 2,
                      'accept_status': accepted.status_code})

        saved = proposal['content']
        job = complete('insufficient')
        _check(job['state'] == 'succeeded' and job['output']['insufficient_evidence']
               and not job['output']['citations'], 'insufficient_evidence_result')
        _check(_read(owner.get(path), 200, 'read_saved_proposal')['content'] == saved, 'insufficient_does_not_save')
        cases.append({'case': 'insufficient', 'job_id': job['id'], 'state': job['state'], 'insufficient_evidence': True})

        for case, error in (('invalid_quote', 'invalid_citations'), ('truncated', 'draft_truncated')):
            job = complete(case)
            _check(job['state'] == 'failed' and job['output'] is None and job['error']['code'] == error, case + '_failure')
            _check(_read(owner.get(path), 200, 'read_saved_proposal')['content'] == saved, case + '_does_not_save')
            cases.append({'case': case, 'job_id': job['id'], 'state': job['state'], 'error_code': error})

        queued = enqueue('Summarize the same synthetic protocol.')
        entered, release = Event(), Event()
        worker = make_worker(ScriptedProvider(response_for('two_source', source_ids), entered, release))
        collaborator_text = saved + '\n\nA collaborator saved this newer manual edit.'
        try:
            worker.tick()
            _check(entered.wait(2), 'scripted_generation_started')
            _read(editor.patch(path, json={'expected_revision': proposal['revision'],
                  'content': collaborator_text}), 200, 'concurrent_collaborator_save')
        finally:
            release.set()
            worker.close(wait=True)
        job = _read(owner.get('/api/v2/jobs/' + queued['id']), 200, 'read_late_job')
        _check(job['state'] == 'succeeded', 'late_result_completed')
        rejected = owner.patch(path, json={'expected_revision': job['base_revision'],
            'content': saved + '\n\n' + job['output']['text']})
        _check(rejected.status_code == 409, 'stale_acceptance_rejected')
        current = _read(owner.get(path), 200, 'read_concurrent_proposal')
        _check(current['content'] == collaborator_text, 'collaborator_text_preserved')
        cases.append({'case': 'concurrent_save', 'job_id': job['id'], 'state': job['state'],
                      'accept_status': rejected.status_code, 'collaborator_text_preserved': True})

        proposal = current
        queued = enqueue('Describe the synthetic protocol.')
        entered, release = Event(), Event()
        provider = ScriptedProvider(response_for('two_source', source_ids), entered, release)
        worker = make_worker(provider)
        try:
            worker.tick()
            _check(entered.wait(2), 'cancellable_generation_started')
            cancelled = _read(owner.post('/api/v2/jobs/' + queued['id'] + '/cancel'), 200, 'cancel_active_job')
            _check(cancelled['error']['code'] == 'cancelled', 'cancellation_recorded')
            followup = enqueue('Describe the same synthetic protocol after cancellation.')
            worker.tick()
            waiting = _read(owner.get('/api/v2/jobs/' + followup['id']), 200, 'read_waiting_followup')
            _check(waiting['state'] == 'queued' and provider.calls == 1, 'followup_waits_for_drain')
        finally:
            release.set()
            worker.close(wait=True)
        cancelled = _read(owner.get('/api/v2/jobs/' + queued['id']), 200, 'read_cancelled_after_drain')
        _check(cancelled['state'] == 'failed' and cancelled['error']['code'] == 'cancelled'
               and cancelled['output'] is None, 'cancelled_late_output_discarded')
        worker = make_worker(ScriptedProvider(response_for('two_source', source_ids)))
        try:
            worker.tick()
        finally:
            worker.close(wait=True)
        completed = _read(owner.get('/api/v2/jobs/' + followup['id']), 200, 'read_followup_after_drain')
        _check(completed['state'] == 'succeeded', 'followup_runs_after_drain')
        _check(_read(owner.get(path), 200, 'read_after_cancellation')['content'] == collaborator_text,
               'cancellation_does_not_change_proposal')
        cases.append({'case': 'cancelled_during_generation', 'job_id': queued['id'], 'state': cancelled['state'],
                      'error_code': cancelled['error']['code'], 'followup_queued_during_drain': True,
                      'late_output_discarded': True, 'followup_job_id': followup['id'], 'followup_state': completed['state']})
        public = _read(owner.get('/api/v2/search?q=greenhouse'), 200, 'check_source_scope')
        _check(not public['items'], 'private_sources_not_published')
    return {'status': 'passed', 'evidence': 'scripted_responses', 'transport': 'in_process_api',
            'model_id': 'fixture-scripted-v1', 'external_model_requests': 0, 'cases': cases}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--postgres', action='store_true', help='Create and retain a new development simulation database')
    args = parser.parse_args()
    app, admin, database_name = None, None, None
    creation_confirmed = False
    with TemporaryDirectory(prefix='tbr-draft-simulation-') as tmp:
        try:
            if args.postgres:
                _check(os.environ.get('TBR_PROFILE') == 'development'
                       and os.environ.get('TBR_MODEL_PROVIDER') == 'fixture', 'development_fixture_required')
                admin = Database()
                _check(admin.engine.dialect.name == 'postgresql', 'postgresql_required')
                database_name = 'tbr_simulation_' + uuid4().hex
                with admin.engine.connect().execution_options(isolation_level='AUTOCOMMIT') as connection:
                    connection.exec_driver_sql(f'CREATE DATABASE "{database_name}"')
                creation_confirmed = True
                app = create_app(admin.engine.url.set(database=database_name))
                from alembic import command
                from alembic.config import Config
                config = Config(str(Path(__file__).resolve().parents[2] / 'alembic.ini'))
                with app.state.db.engine.begin() as connection:
                    config.attributes['connection'] = connection
                    command.upgrade(config, 'head')
            else:
                app = create_app(f"sqlite:///{Path(tmp) / 'simulation.db'}")
                app.state.db.create_schema()
            result = run_scenarios(app, Path(tmp) / 'generation.lock')
            result.update(database='postgresql' if args.postgres else 'sqlite',
                          database_name=database_name, records_retained=bool(database_name))
        except Exception as error:
            result = {'status': 'failed', 'step': str(error) if isinstance(error, SimulationError) else 'simulation_failed',
                      'database_name': database_name, 'creation_confirmed': creation_confirmed,
                      'records_retained': True if creation_confirmed else None}
        finally:
            if app is not None:
                app.state.db.engine.dispose()
            if admin is not None:
                admin.engine.dispose()
        print(json.dumps(result))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
