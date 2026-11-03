"""Dry-run or explicitly approved import of a small RIT snapshot subset."""

import argparse
import json
import sys
from pathlib import Path

from .rit_snapshot import MAX_IMPORT_RECORDS, load_rit_snapshot


class DatabaseImportError(Exception):
    pass


def _persist(records: list[dict]) -> dict:
    from sqlalchemy.exc import SQLAlchemyError

    from src.platform.database import Database
    from src.platform.ingestion.public_store import import_public_records

    try:
        database = Database()
        with database.engine.connect():
            pass
        with database.session_factory() as session:
            imported = import_public_records(session, records)
            session.commit()
        return imported
    except SQLAlchemyError:
        raise DatabaseImportError from None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--source-file',
        required=True,
        type=Path,
        help=f'Explicit path to {Path("data") / "rit_data_v2.json"}',
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=MAX_IMPORT_RECORDS,
        help=f'Maximum profiles to prepare (1-{MAX_IMPORT_RECORDS})',
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Persist the prepared records to the configured application database.',
    )
    parser.add_argument(
        '--confirm-public-source-rights',
        action='store_true',
        help='Confirm the selected snapshot facts have been reviewed for public reuse.',
    )
    args = parser.parse_args(argv)
    if args.apply and not args.confirm_public_source_rights:
        print(
            json.dumps(
                {
                    'status': 'blocked',
                    'message': 'Review source reuse rights before applying the import.',
                }
            ),
            file=sys.stderr,
        )
        return 2

    try:
        records, inventory = load_rit_snapshot(args.source_file, args.limit)
        result = {
            'status': 'validated',
            **inventory,
            'persisted': False,
            'rights_reviewed': args.confirm_public_source_rights,
        }
        if args.apply:
            imported = _persist(records)
            result.update(status='imported', persisted=True, import_counts=imported)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (TypeError, ValueError) as exc:
        print(json.dumps({'status': 'failed', 'message': str(exc)}), file=sys.stderr)
        return 1
    except OSError:
        print(
            json.dumps(
                {
                    'status': 'failed',
                    'message': 'Snapshot file could not be read; verify the explicit source path.',
                }
            ),
            file=sys.stderr,
        )
        return 1
    except ImportError as exc:
        print(
            json.dumps(
                {
                    'status': 'failed',
                    'message': 'Install the API requirements before applying the import.',
                    'dependency': str(exc.name),
                }
            ),
            file=sys.stderr,
        )
        return 1
    except DatabaseImportError:
        print(
            json.dumps(
                {
                    'status': 'failed',
                    'message': 'Database import failed; verify database state before retrying.',
                }
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
