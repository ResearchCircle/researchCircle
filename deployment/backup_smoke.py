"""Back up the isolated development DB and restore into a new database, preserving both."""

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from uuid import uuid4

from .runtime import ROOT
from .start import read_settings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path, default=ROOT / 'dist/core-runtime.env')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'dist/backups')
    args = parser.parse_args()
    settings = read_settings(args.env_file)
    if settings.get('COMPOSE_PROJECT_NAME') != 'tbr-core':
        raise ValueError('This smoke is restricted to the isolated tbr-core development stack.')
    target = args.output_dir.resolve()
    protected = [ROOT / 'data']
    if settings.get('TBR_DATA_SOURCE'):
        protected.append(Path(settings['TBR_DATA_SOURCE']).resolve())
    if any(target == source or source in target.parents for source in protected):
        raise ValueError('Backup output must stay outside source snapshots.')
    target.mkdir(parents=True, exist_ok=True)
    label = uuid4().hex[:12]
    backup = target / f'core-{label}.dump'
    restored_database = 'tbr_restore_' + label
    command = ['docker', 'compose', '-p', 'tbr-core', '--env-file', str(args.env_file),
               '-f', str(ROOT / 'deployment/compose.yaml'), 'exec', '-T', 'db']

    def run(*parts, stdin=None, stdout=None):
        result = subprocess.run([*command, *parts], stdin=stdin, stdout=stdout or subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=60)
        if result.returncode:
            raise RuntimeError('Development backup/restore command failed; retained existing data and backup.')
        return result.stdout

    def fingerprint(database):
        values = {}
        names = run('psql', '-U', 'tbr', '-d', database, '-At', '-c',
                    "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename").decode().splitlines()
        for table in names:
            if not re.fullmatch(r'[a-z_][a-z0-9_]*', table):
                raise RuntimeError('Unexpected table identifier in development database.')
            sql = (f"SELECT count(*)::text || ':' || md5(COALESCE(string_agg(row_to_json(t)::text, "
                   f"E'\\n' ORDER BY row_to_json(t)::text),'')) FROM {table} t")
            raw = run('psql', '-U', 'tbr', '-d', database, '-At', '-c', sql).decode().strip()
            count, digest = raw.split(':')
            values[table] = {'rows': int(count), 'fingerprint': digest}
        return values

    before = fingerprint('tbr')
    descriptor = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'wb') as output:
        run('pg_dump', '-U', 'tbr', '-d', 'tbr', '--format=custom', stdout=output)
    run('createdb', '-U', 'tbr', restored_database)
    with backup.open('rb') as source:
        run('pg_restore', '-U', 'tbr', '-d', restored_database, '--no-owner', '--no-acl', stdin=source)
    after = fingerprint(restored_database)
    if before != after:
        raise RuntimeError('Restore fingerprints differ; both databases and backup were preserved.')
    print(json.dumps({'status': 'passed', 'tables': {key: value['rows'] for key, value in before.items()},
                      'all_record_fingerprints_match': True, 'backup_bytes': backup.stat().st_size,
                      'restored_database': restored_database, 'backup_location': str(backup.relative_to(ROOT)) if backup.is_relative_to(ROOT) else str(backup),
                      'scope': 'Isolated synthetic development database; original DB and restore retained.'}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
