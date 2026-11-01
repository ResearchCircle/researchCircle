"""Configure a new host runtime without relocating or deleting existing data."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import tomllib


def configure_storage(project: Path, docker_config: Path, containerd_config: Path,
                      legacy_paths: tuple[Path, ...]) -> dict:
    if not project.is_absolute() or project.is_symlink() or not project.is_dir():
        raise ValueError('Use an existing absolute project directory without a symlink.')
    guarded = (project / 'runtime', project / 'runtime/docker', project / 'runtime/containerd',
               project / 'config', project / 'config/system-backups', docker_config, containerd_config,
               docker_config.parent, containerd_config.parent, *legacy_paths)
    if any(path.is_symlink() for path in guarded):
        raise ValueError('Existing runtime configuration symlinks require manual review.')
    docker_text = docker_config.read_text() if docker_config.exists() else ''
    containerd_text = containerd_config.read_text() if containerd_config.exists() else ''
    try:
        docker = json.loads(docker_text) if docker_text else {}
        containerd = tomllib.loads(containerd_text)
    except (ValueError, TypeError):
        raise ValueError('Existing runtime configuration could not be safely parsed.') from None
    if not isinstance(docker, dict):
        raise ValueError('Existing Docker configuration is not an object.')
    docker_root = str(project / 'runtime/docker')
    containerd_root = str(project / 'runtime/containerd')
    if docker.get('data-root', docker_root) != docker_root or containerd.get('root', containerd_root) != containerd_root:
        raise ValueError('A different runtime storage root is configured; existing configuration was preserved.')
    already_configured = docker.get('data-root') == docker_root and containerd.get('root') == containerd_root
    if not already_configured:
        for path in (*legacy_paths, Path(docker_root), Path(containerd_root)):
            if path.exists() and (not path.is_dir() or any(path.iterdir())):
                raise ValueError('Preexisting runtime data requires manual review; no storage was relocated or deleted.')
    docker['data-root'] = docker_root
    rendered_containerd = containerd_text
    if 'root' not in containerd:
        rendered_containerd = 'root = ' + json.dumps(containerd_root) + '\n' + containerd_text
    if 'version' not in containerd:
        rendered_containerd = 'version = 3\n' + rendered_containerd
    backup_root = project / 'config/system-backups'
    backup_root.mkdir(parents=True, mode=0o700, exist_ok=True)
    for path, original, content in (
            (docker_config, docker_text, json.dumps(docker, indent=2) + '\n'),
            (containerd_config, containerd_text, rendered_containerd)):
        if original and original != content:
            backup = backup_root / (path.name + '.' + hashlib.sha256(original.encode()).hexdigest()[:16])
            if not backup.exists():
                descriptor = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(descriptor, 'w') as file:
                    file.write(original)
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
        try:
            with os.fdopen(descriptor, 'w') as file:
                file.write(content)
            os.replace(temporary, path)
        finally:
            if Path(temporary).exists():
                Path(temporary).unlink()
    for path in (Path(docker_root), Path(containerd_root)):
        path.mkdir(parents=True, mode=0o700, exist_ok=True)
    return {'status': 'runtime_storage_configured', 'docker_root': docker_root,
            'containerd_root': containerd_root, 'existing_data_relocated': False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, required=True)
    args = parser.parse_args()
    try:
        if os.geteuid() != 0:
            raise ValueError('Runtime configuration needs an interactive administrator session.')
        result = configure_storage(args.project_root, Path('/etc/docker/daemon.json'),
                                   Path('/etc/containerd/config.toml'),
                                   (Path('/var/lib/docker'), Path('/var/lib/containerd')))
        print(json.dumps(result))
        return 0
    except (OSError, ValueError):
        print(json.dumps({'status': 'runtime_storage_blocked',
                          'message': 'Review existing runtime configuration/data and permissions; nothing was relocated or deleted.'}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
