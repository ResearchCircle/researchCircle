import json
from pathlib import Path
import tempfile
import tomllib
import unittest

from deployment.host_storage import configure_storage


class HostRuntimeStorageTests(unittest.TestCase):
    def prepare(self, tmp):
        base = Path(tmp)
        project = base / 'researchCircle'
        project.mkdir()
        docker = base / 'etc/docker/daemon.json'
        containerd = base / 'etc/containerd/config.toml'
        legacy = (base / 'var/lib/docker', base / 'var/lib/containerd')
        return project, docker, containerd, legacy

    def test_new_runtime_keeps_both_daemon_stores_inside_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            project, docker, containerd, legacy = self.prepare(tmp)
            configure_storage(project, docker, containerd, legacy)
            self.assertEqual(json.loads(docker.read_text())['data-root'], str(project / 'runtime/docker'))
            self.assertEqual(tomllib.loads(containerd.read_text())['root'], str(project / 'runtime/containerd'))
            self.assertEqual(docker.stat().st_mode & 0o777, 0o600)
            self.assertTrue((project / 'runtime/docker').is_dir())

    def test_unrelated_configuration_is_preserved_and_backed_up(self):
        with tempfile.TemporaryDirectory() as tmp:
            project, docker, containerd, legacy = self.prepare(tmp)
            docker.parent.mkdir(parents=True)
            containerd.parent.mkdir(parents=True)
            old_docker = '{"log-driver":"local","features":{"containerd-snapshotter":true}}\n'
            old_containerd = 'version = 3\n[grpc]\n  address = "/run/containerd/containerd.sock"\n'
            docker.write_text(old_docker)
            containerd.write_text(old_containerd)
            configure_storage(project, docker, containerd, legacy)
            self.assertEqual(json.loads(docker.read_text())['log-driver'], 'local')
            self.assertTrue(json.loads(docker.read_text())['features']['containerd-snapshotter'])
            self.assertEqual(tomllib.loads(containerd.read_text())['grpc']['address'], '/run/containerd/containerd.sock')
            backups = [x.read_text() for x in (project / 'config/system-backups').iterdir()]
            self.assertIn(old_docker, backups)
            self.assertIn(old_containerd, backups)

    def test_preexisting_default_runtime_data_blocks_all_configuration_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            project, docker, containerd, legacy = self.prepare(tmp)
            legacy[1].mkdir(parents=True)
            sentinel = legacy[1] / 'existing-state'
            sentinel.write_text('Preserve this runtime data.')
            with self.assertRaises(ValueError):
                configure_storage(project, docker, containerd, legacy)
            self.assertFalse(docker.exists())
            self.assertFalse(containerd.exists())
            self.assertEqual(sentinel.read_text(), 'Preserve this runtime data.')

    def test_foreign_configured_root_is_never_replaced(self):
        for which in ('docker', 'containerd'):
            with self.subTest(which=which), tempfile.TemporaryDirectory() as tmp:
                project, docker, containerd, legacy = self.prepare(tmp)
                target = docker if which == 'docker' else containerd
                target.parent.mkdir(parents=True)
                original = '{"data-root":"/different/docker"}' if which == 'docker' else 'root = "/different/containerd"\n'
                target.write_text(original)
                with self.assertRaises(ValueError):
                    configure_storage(project, docker, containerd, legacy)
                self.assertEqual(target.read_text(), original)

    def test_repeat_preserves_existing_project_runtime_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            project, docker, containerd, legacy = self.prepare(tmp)
            configure_storage(project, docker, containerd, legacy)
            sentinel = project / 'runtime/docker/existing-image'
            sentinel.write_text('Keep the existing image.')
            configure_storage(project, docker, containerd, legacy)
            self.assertEqual(sentinel.read_text(), 'Keep the existing image.')

    def test_symlink_runtime_or_backup_directory_cannot_redirect_writes(self):
        for relative in ('runtime', 'runtime/docker', 'config/system-backups'):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as tmp:
                project, docker, containerd, legacy = self.prepare(tmp)
                other = Path(tmp) / 'preserved-input'
                other.mkdir()
                link = project / relative
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(other, target_is_directory=True)
                with self.assertRaises(ValueError):
                    configure_storage(project, docker, containerd, legacy)
                self.assertEqual(list(other.iterdir()), [])
                self.assertFalse(docker.exists())

    def test_symlink_configuration_is_rejected_without_touching_its_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            project, docker, containerd, legacy = self.prepare(tmp)
            other = Path(tmp) / 'existing.json'
            other.write_text('{}')
            docker.parent.mkdir(parents=True)
            docker.symlink_to(other)
            with self.assertRaises(ValueError):
                configure_storage(project, docker, containerd, legacy)
            self.assertEqual(other.read_text(), '{}')


if __name__ == '__main__':
    unittest.main()
