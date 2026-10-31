"""Run application migrations with explicit database configuration."""
from alembic import context
from sqlalchemy import create_engine

from src.platform.database import database_url_from_env
from src.platform.database.models import Base
from src.platform.database.public_records import PublicRecord
from src.platform.database.shortlists import TeamShortlistEntry
from src.platform.database.pursuits import Opportunity, Outcome, Pursuit, PursuitHistory  # noqa: F401
from src.platform.workflow.draft_jobs import DraftJobRecord  # noqa: F401

config = context.config


def run_with_connection(connection):
    context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    context.configure(url=database_url_from_env(), target_metadata=Base.metadata,
                      literal_binds=True, dialect_opts={'paramstyle': 'named'})
    with context.begin_transaction():
        context.run_migrations()
elif config.attributes.get('connection') is not None:
    run_with_connection(config.attributes['connection'])
else:
    engine = create_engine(database_url_from_env(), pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            run_with_connection(connection)
    finally:
        engine.dispose()
