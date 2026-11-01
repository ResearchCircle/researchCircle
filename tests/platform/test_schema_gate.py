"""Application services may start only after migrations and schema verification."""
import contextlib
import importlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from deployment.runtime import ROOT
from deployment.start import main
from src.platform.database import Database
from src.platform.database.models import Proposal, Team


class SchemaGateTests(unittest.TestCase):
    def schema_module(self):
        self.assertIsNotNone(importlib.util.find_spec('deployment.schema'), 'Schema gate is missing')
        return importlib.import_module('deployment.schema')

    def test_fresh_migration_and_repeat_start_preserve_existing_proposal(self):
        schema = self.schema_module()
        with TemporaryDirectory() as tmp:
            db = Database(f"sqlite:///{Path(tmp) / 'fresh.db'}")
            try:
                result = schema.upgrade_and_verify(db)
                self.assertEqual(result['status'], 'schema_ready')
                self.assertEqual(result['heads'], ['0004_team_shortlist'])
                self.assertTrue({'users', 'proposals', 'draft_jobs', 'public_records',
                                 'team_shortlist_entries'} <= set(inspect(db.engine).get_table_names()))
                with db.session_factory() as session:
                    team = Team(name='Retained fixture team')
                    session.add(team)
                    session.flush()
                    proposal = Proposal(team_id=team.id, title='Retained fixture', content='Keep this saved text.', revision=2)
                    session.add(proposal)
                    session.commit()
                    proposal_id = proposal.id
                schema.upgrade_and_verify(db)
                with db.session_factory() as session:
                    self.assertEqual(session.get(Proposal, proposal_id).content, 'Keep this saved text.')
                    self.assertEqual(session.get(Proposal, proposal_id).revision, 2)
            finally:
                db.engine.dispose()

    def test_recorded_head_with_missing_schema_is_rejected(self):
        schema = self.schema_module()
        with TemporaryDirectory() as tmp:
            db = Database(f"sqlite:///{Path(tmp) / 'incomplete.db'}")
            try:
                config = Config(str(ROOT / 'alembic.ini'))
                with db.engine.begin() as connection:
                    config.attributes['connection'] = connection
                    command.stamp(config, 'head')
                with self.assertRaises(schema.SchemaGateError):
                    schema.upgrade_and_verify(db)
                self.assertEqual(set(inspect(db.engine).get_table_names()), {'alembic_version'})
            finally:
                db.engine.dispose()

    def launch(self, start, fail_gate=False):
        calls = []

        def docker(arguments, **_kwargs):
            calls.append(arguments)
            return subprocess.CompletedProcess(arguments, 1 if fail_gate and 'deployment.schema' in arguments else 0)

        with TemporaryDirectory() as tmp:
            settings = Path(tmp) / 'runtime.env'
            settings.write_text('TBR_PROFILE=demo\nTBR_MODEL_PROVIDER=local\n'
                                'TBR_MODEL_BASE_URL=http://127.0.0.1:19091/v1\nTBR_MODEL_ID=homelab-llm\n'
                                'TBR_API_IMAGE=fixture-api\nTBR_WEB_IMAGE=fixture-web\n'
                                'TBR_DB_PASSWORD=private-synthetic-password\n')
            output = io.StringIO()
            args = ['start', '--env-file', str(settings)] + (['--start'] if start else [])
            with (patch.dict('os.environ', {}, clear=True), patch('sys.argv', args),
                  patch('deployment.start.subprocess.run', side_effect=docker),
                  patch('deployment.start.wait_for_runtime'), contextlib.redirect_stdout(output)):
                status = main()
        self.assertNotIn('private-synthetic-password', output.getvalue())
        return status, json.loads(output.getvalue()), calls

    def test_shared_start_runs_database_gate_before_starting_worker(self):
        status, result, calls = self.launch(True)
        self.assertEqual(status, 0, result)
        gates = [i for i, call in enumerate(calls) if 'deployment.schema' in call]
        self.assertEqual(len(gates), 1, 'Worker startup has no migration/schema gate')
        workers = [i for i, call in enumerate(calls) if 'up' in call and 'worker' in call]
        self.assertEqual(len(workers), 1)
        self.assertLess(gates[0], workers[0])
        databases = [call for call in calls[:gates[0]] if 'up' in call and call[-1] == 'db']
        self.assertEqual(len(databases), 1)
        self.assertIn('--wait', databases[0], 'Migration gate must wait for PostgreSQL health')
        self.assertIn('--wait-timeout', databases[0])

    def test_failed_database_gate_blocks_application_startup(self):
        status, result, calls = self.launch(True, fail_gate=True)
        self.assertEqual(status, 1, result)
        self.assertNotEqual(result['status'], 'started')
        self.assertFalse(any('up' in call and ('worker' in call or 'web' in call) for call in calls))

    def test_configuration_only_does_not_migrate_or_start_services(self):
        status, result, calls = self.launch(False)
        self.assertEqual(status, 0, result)
        self.assertEqual(result['status'], 'configuration_valid')
        self.assertTrue(all('config' in call for call in calls))


if __name__ == '__main__':
    unittest.main()
