import tempfile
import unittest
from pathlib import Path

from deployment.dev import configure_development
from deployment.start import read_settings


class DevelopmentSetupTests(unittest.TestCase):
    def test_default_setup_is_explicit_fixture_and_keeps_credentials_private(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'runtime.env'
            settings = configure_development(path, 'fixture', None, None)
            self.assertEqual(settings['TBR_PROFILE'], 'development')
            self.assertEqual(settings['TBR_MODEL_PROVIDER'], 'fixture')
            self.assertNotIn('TBR_MODEL_BASE_URL', settings)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertGreaterEqual(len(settings['TBR_DB_PASSWORD']), 32)
            again = configure_development(path, 'fixture', None, None)
            self.assertEqual(settings['TBR_DB_PASSWORD'], again['TBR_DB_PASSWORD'])

    def test_local_inference_requires_real_explicit_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'runtime.env'
            with self.assertRaises(ValueError):
                configure_development(path, 'local', None, None)
            self.assertFalse(path.exists())
            settings = configure_development(path, 'local', 'http://127.0.0.1:18080/v1', 'observed-model')
            self.assertEqual(settings['TBR_PROFILE'], 'demo')
            self.assertEqual(settings['TBR_MODEL_ID'], 'observed-model')

    def test_does_not_repurpose_another_application_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'runtime.env'
            path.write_text('COMPOSE_PROJECT_NAME=another-project\nTBR_DB_PASSWORD=private-fixture\n')
            before = path.read_text()
            with self.assertRaises(ValueError):
                configure_development(path, 'fixture', None, None)
            self.assertEqual(path.read_text(), before)


if __name__ == '__main__':
    unittest.main()
