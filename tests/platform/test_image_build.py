import unittest
from pathlib import Path

from deployment.build import build_command


class ImageBuildTests(unittest.TestCase):
    def test_api_build_is_scoped_to_owned_dockerfile_and_explicit_dependencies(self):
        command = build_command('api', 'tbr-api:test', 'deployment/api-bootstrap.requirements.txt')
        self.assertIn('deployment/api.Dockerfile', ' '.join(command))
        self.assertIn('TBR_API_REQUIREMENTS=deployment/api-bootstrap.requirements.txt', command)
        self.assertEqual(command[-1], str(Path(__file__).resolve().parents[2]))
        self.assertNotIn('--push', command)

    def test_dependency_path_cannot_include_source_snapshot_or_escape_checkout(self):
        for path in ['.', '../requirements.txt', 'data/prompts/role.md', '/etc/passwd', 'deployment/.env']:
            with self.subTest(path=path), self.assertRaises(ValueError):
                build_command('api', 'tbr-api:test', path)

    def test_web_build_uses_checked_in_frontend_without_api_requirements(self):
        command = build_command('web', 'tbr-web:test', None)
        self.assertIn('deployment/web.Dockerfile', ' '.join(command))
        self.assertFalse(any('TBR_API_REQUIREMENTS' in arg for arg in command))


if __name__ == '__main__':
    unittest.main()
