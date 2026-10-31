"""Import 1–5 verified Crossref metadata records into the configured database."""
import argparse
import json
import sys

from src.platform.database import Database
from src.platform.ingestion.crossref import DEFAULT_DOIS, fetch_crossref
from src.platform.ingestion.public_store import import_public_records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--doi', action='append', help='Repeat for up to five DOI records; defaults to three verified examples')
    args = parser.parse_args()
    database = Database()
    try:
        # Validate configured storage before performing any network request.
        database.engine
        records = fetch_crossref(args.doi or DEFAULT_DOIS)
        with database.session_factory() as session:
            counts = import_public_records(session, records)
            session.commit()
        print(json.dumps({'status': 'imported', **counts, 'evidence': 'public_bibliographic_metadata', 'abstracts_included': False}))
        return 0
    except Exception:
        print(json.dumps({'status': 'failed', 'message': 'Public metadata import could not be confirmed. Retry is safe: identical snapshots are retained once.'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
