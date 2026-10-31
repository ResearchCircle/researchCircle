"""Import short structured facts from three fixed official RIT directory pages."""
import json
import sys

from src.platform.database import Database
from src.platform.ingestion.rit_profiles import fetch_profiles
from src.platform.ingestion.public_store import import_public_records


def main():
    try:
        database = Database()
        database.engine
        records = fetch_profiles()
        with database.session_factory() as session:
            counts = import_public_records(session, records)
            session.commit()
        print(json.dumps({'status':'imported', **counts, 'evidence':'official_profile_keyword_facts',
                          'profiles':len(records), 'biographies_or_contacts_retained':False}))
        return 0
    except Exception:
        print(json.dumps({'status':'failed', 'message':'Official profile import could not be confirmed. Check database state before retrying.'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
