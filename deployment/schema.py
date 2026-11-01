"""Apply existing application migrations and verify the actual resulting schema."""
import contextlib
import io
import json

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory

from src.platform.database import Database
from .runtime import ROOT


class SchemaGateError(RuntimeError):
    pass


def upgrade_and_verify(database: Database | None = None) -> dict:
    owned = database is None
    try:
        database = database or Database()
        config = Config(str(ROOT / 'alembic.ini'))
        config.stdout = io.StringIO()
        expected = set(ScriptDirectory.from_config(config).get_heads())
        if not expected:
            raise ValueError('No application migration head exists')
        # Alembic diagnostics can include schema details. The launcher needs only
        # the safe result below, never driver errors or connection settings.
        with contextlib.redirect_stdout(io.StringIO()), database.engine.begin() as connection:
            config.attributes['connection'] = connection
            command.upgrade(config, 'head')
            actual = set(MigrationContext.configure(connection).get_current_heads())
            if actual != expected:
                raise ValueError('Application migration head mismatch')
            # A stamped revision alone does not prove tables/columns exist.
            command.check(config)
        return {'status': 'schema_ready', 'heads': sorted(actual), 'schema_verified': True}
    except Exception:
        raise SchemaGateError('Database migration or schema verification failed; application startup is blocked.') from None
    finally:
        if owned and database is not None and database.configuration_error is None:
            database.engine.dispose()


def main() -> int:
    try:
        result = upgrade_and_verify()
    except SchemaGateError as error:
        print(json.dumps({'status': 'schema_failed', 'message': str(error)}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
