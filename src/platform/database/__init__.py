"""Explicit PostgreSQL configuration; SQLite is only for isolated tests."""
import os
from collections.abc import Mapping

from sqlalchemy import create_engine, event
from sqlalchemy.engine import URL, Engine, make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from .models import Base


class DatabaseConfigurationError(ValueError):
    pass


def database_url_from_env(env: Mapping[str, str] | None = None) -> str | URL:
    env = os.environ if env is None else env
    if env.get('TBR_DATABASE_URL'):
        url = env['TBR_DATABASE_URL']
        if url.startswith('postgres://'):
            url = 'postgresql+psycopg://' + url.removeprefix('postgres://')
        elif url.startswith('postgresql://'):
            url = 'postgresql+psycopg://' + url.removeprefix('postgresql://')
        if not url.startswith('postgresql+psycopg://'):
            raise DatabaseConfigurationError('TBR_DATABASE_URL must use PostgreSQL with psycopg')
        return url
    required = ('TBR_DB_HOST', 'TBR_DB_NAME', 'TBR_DB_USER', 'TBR_DB_PASSWORD')
    if not all(env.get(key) for key in required):
        raise DatabaseConfigurationError('Set TBR_DATABASE_URL or all TBR_DB_HOST/NAME/USER/PASSWORD settings')
    try:
        port = int(env.get('TBR_DB_PORT', '5432'))
    except ValueError:
        raise DatabaseConfigurationError('TBR_DB_PORT must be an integer') from None
    return URL.create('postgresql+psycopg', username=env['TBR_DB_USER'], password=env['TBR_DB_PASSWORD'],
                      host=env['TBR_DB_HOST'], port=port, database=env['TBR_DB_NAME'])


class Database:
    def __init__(self, database_url: str | URL | None = None):
        self._engine: Engine | None = None
        self._session_factory = None
        self.configuration_error: str | None = None
        if database_url is None:
            try:
                database_url = database_url_from_env()
            except DatabaseConfigurationError as exc:
                self.configuration_error = str(exc)
                return
        parsed = make_url(database_url)
        sqlite = parsed.drivername == 'sqlite'
        if not sqlite:
            if parsed.drivername in ('postgres', 'postgresql'):
                parsed = parsed.set(drivername='postgresql+psycopg')
            elif parsed.drivername != 'postgresql+psycopg':
                raise DatabaseConfigurationError('Application database must use PostgreSQL with psycopg')
        database_url = parsed
        kwargs = {'pool_pre_ping': True}
        if sqlite:
            kwargs['connect_args'] = {'check_same_thread': False}
            if str(database_url) in ('sqlite://', 'sqlite:///:memory:'):
                kwargs['poolclass'] = StaticPool
        self._engine = create_engine(database_url, **kwargs)
        if sqlite:
            @event.listens_for(self._engine, 'connect')
            def enable_foreign_keys(connection, _record):
                connection.execute('PRAGMA foreign_keys=ON')
        self._session_factory = sessionmaker(self._engine, expire_on_commit=False)

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            raise DatabaseConfigurationError(self.configuration_error or 'Database is not configured')
        return self._engine

    def session_factory(self):
        if self._session_factory is None:
            raise DatabaseConfigurationError(self.configuration_error or 'Database is not configured')
        return self._session_factory()

    def create_schema(self):
        """Bootstrap a fresh database explicitly; never called during web startup."""
        Base.metadata.create_all(self.engine)
