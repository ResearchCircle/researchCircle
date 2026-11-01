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

    def test_explicit_target_architecture_reaches_docker_for_both_images(self):
        for component, requirements in [('api', 'services/api/requirements.txt'), ('web', None)]:
            for target in ('linux/amd64', 'linux/arm64'):
                with self.subTest(component=component, target=target):
                    command = build_command(component, 'tbr:test', requirements, platform=target)
                    self.assertEqual(command[command.index('--platform') + 1], target)
                    self.assertNotIn('--push', command)

    def test_unsupported_target_is_rejected_before_any_build(self):
        for target in ('amd64', 'linux/386', 'linux/amd64,linux/arm64', '--push'):
            with self.subTest(target=target), self.assertRaises(ValueError):
                build_command('web', 'tbr:test', None, platform=target)

    def test_native_build_does_not_force_an_architecture(self):
        self.assertNotIn('--platform', build_command('web', 'tbr:test', None))

    def test_web_build_uses_checked_in_frontend_without_api_requirements(self):
        command = build_command('web', 'tbr-web:test', None)
        self.assertIn('deployment/web.Dockerfile', ' '.join(command))
        self.assertFalse(any('TBR_API_REQUIREMENTS' in arg for arg in command))


if __name__ == '__main__':
    unittest.main()
