"""Initialize a fresh configured application database without resetting existing data."""
from src.platform.database import Database
from src.platform.workflow.draft_jobs import DraftJobRecord
from services.api.routes.search import seed_samples


def main():
    database = Database()
    database.create_schema()
    with database.session_factory() as session:
        inserted = seed_samples(session)
        session.commit()
    print(f'Application schema initialized; {inserted} synthetic sample sources added; existing records were preserved.')


if __name__ == '__main__':
    main()
