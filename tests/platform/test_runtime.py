import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from deployment.runtime import RuntimeConfig, integration_gaps
from deployment.start import main, read_settings


class RuntimeTests(unittest.TestCase):
    def test_default_is_explicit_development_fixture(self):
        config = RuntimeConfig.from_env({})
        self.assertEqual(config.profile, 'development')
        self.assertEqual(config.provider, 'fixture')

    def test_shared_demo_requires_local_model_and_no_development_identity(self):
        for env in [{'TBR_PROFILE': 'demo'}, {'TBR_PROFILE': 'demo', 'TBR_MODEL_PROVIDER': 'fixture'},
                    {'TBR_PROFILE': 'demo', 'TBR_MODEL_PROVIDER': 'local',
                     'TBR_MODEL_BASE_URL': 'http://127.0.0.1:18080/v1', 'TBR_MODEL_ID': 'homelab-llm',
                     'TBR_DEV_IDENTITY': 'true'}]:
            with self.subTest(env=env), self.assertRaises(ValueError):
                RuntimeConfig.from_env(env)

    def test_no_cloud_or_unknown_profile_fallback(self):
        for env in [{'TBR_MODEL_PROVIDER': 'gemini'}, {'TBR_PROFILE': 'unknown'},
                    {'TBR_MODEL_PROVIDER': 'local'}, {'TBR_MODEL_PROVIDER': 'local',
                     'TBR_MODEL_BASE_URL': 'https://example.com/v1', 'TBR_MODEL_ID': 'model'}]:
            with self.subTest(env=env), self.assertRaises(ValueError):
                RuntimeConfig.from_env(env)

    def test_work_directory_cannot_be_inside_source_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'source'
            source.mkdir()
            for work in [source, source / 'work', Path(tmp)]:
                with self.subTest(work=work), self.assertRaises(ValueError):
                    RuntimeConfig.from_env({'TBR_DATA_SOURCE': str(source), 'TBR_DATA_WORK': str(work)})
            config = RuntimeConfig.from_env({'TBR_DATA_SOURCE': str(source), 'TBR_DATA_WORK': str(Path(tmp) / 'work')})
            self.assertFalse(config.work_dir.exists())

    def test_staging_validation_reports_missing_team_dependencies(self):
        with tempfile.TemporaryDirectory() as tmp:
            gaps = integration_gaps(Path(tmp), {})
            self.assertTrue(any('worker' in gap.lower() for gap in gaps))
            self.assertTrue(any('T1' in gap for gap in gaps))
            self.assertTrue(any('T2' in gap for gap in gaps))
            self.assertTrue(any('T3' in gap for gap in gaps))

    def test_settings_are_literal_and_errors_do_not_echo_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / '.env'
            path.write_text('# comment\nTBR_DB_PASSWORD="literal$secret"\nTBR_PROFILE=demo\n')
            self.assertEqual(read_settings(path)['TBR_DB_PASSWORD'], 'literal$secret')
            path.write_text('INVALID SECRET CONTENT\n')
            with self.assertRaises(ValueError) as caught:
                read_settings(path)
            self.assertNotIn('SECRET', str(caught.exception))

    def test_start_does_not_contact_docker_when_integration_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / '.env'
            path.write_text('TBR_PROFILE=demo\nTBR_MODEL_PROVIDER=local\n'
                            'TBR_MODEL_BASE_URL=http://127.0.0.1:18080/v1\nTBR_MODEL_ID=homelab-llm\n')
            output = io.StringIO()
            with patch('sys.argv', ['start', '--env-file', str(path), '--start']), \
                    patch('deployment.start.subprocess.run') as docker, \
                    contextlib.redirect_stdout(output):
                self.assertEqual(main(), 1)
            docker.assert_not_called()
            self.assertEqual(json.loads(output.getvalue())['status'], 'dependencies_missing')

    def test_proxy_preserves_external_host_and_port_for_api_and_frontend(self):
        # At a non-default port, upstream redirects must keep the full browser Host.
        config = (Path(__file__).resolve().parents[2] / 'deployment/nginx.conf').read_text()
        self.assertNotIn('proxy_set_header Host $host;', config)
        self.assertEqual(config.count('proxy_set_header Host $http_host;'), 3)
        self.assertEqual(config.count('proxy_set_header X-Forwarded-Host $http_host;'), 3)


if __name__ == '__main__':
    unittest.main()
