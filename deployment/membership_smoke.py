"""Run retained synthetic membership concurrency checks on configured PostgreSQL.

Run: python -m deployment.membership_smoke
Only new uniquely named records are written. No schema, queues or model services
are changed, and connection settings and passwords are never printed.
"""
from concurrent.futures import ThreadPoolExecutor
import json
import secrets
from threading import Barrier
from uuid import uuid4

from pwdlib import PasswordHash
from sqlalchemy import func, select, text

from services.api.dependencies import team_role
from src.platform.database import Database, DatabaseConfigurationError
from src.platform.database.models import Membership, Team, User
from src.platform.workflow.errors import WorkflowError
from src.platform.workflow.memberships import change_member, lock_team


def run(database: Database) -> dict:
    if database.engine.dialect.name != 'postgresql':
        raise ValueError('PostgreSQL is required')
    label = uuid4().hex
    password_hash = PasswordHash.recommended().hash(secrets.token_urlsafe(48))
    with database.session_factory() as session:
        users = [User(email=f'synthetic-membership-{label}-{index}@example.invalid',
                      name=f'Synthetic membership smoke {index}', password_hash=password_hash) for index in (1, 2)]
        team = Team(name=f'Synthetic membership concurrency smoke {label}')
        session.add_all([team, *users])
        session.flush()
        session.add_all([Membership(team_id=team.id, user_id=user.id, role='owner') for user in users])
        session.commit()
        team_id, user_ids = team.id, [user.id for user in users]
    start = Barrier(2)

    def demote(user_id):
        with database.session_factory() as session:
            session.execute(text("SET LOCAL lock_timeout = '10s'"))
            session.execute(text("SET LOCAL statement_timeout = '15s'"))
            backend = session.scalar(text('SELECT pg_backend_pid()'))
            user = session.get(User, user_id)
            start.wait(timeout=10)
            try:
                lock_team(session, team_id)
                team_role(session, user, team_id, owner=True)
                change_member(session, team_id, user_id, 'editor')
                session.commit()
                return 200, None, backend
            except WorkflowError as exc:
                session.rollback()
                return exc.status, exc.code, backend

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(demote, user_ids))
    with database.session_factory() as session:
        owners = session.scalar(select(func.count()).select_from(Membership).where(
            Membership.team_id == team_id, Membership.role == 'owner'))
    statuses = sorted(result[0] for result in results)
    independent = len({result[2] for result in results}) == 2
    passed = statuses == [200, 409] and owners == 1 and independent and all(
        status == 200 or code == 'last_owner' for status, code, _ in results)
    return {'status': 'passed' if passed else 'failed', 'check': 'concurrent_owner_self_demotion',
            'database': 'postgresql', 'response_statuses': statuses, 'remaining_owners': owners,
            'independent_connections': independent, 'synthetic_team_id': team_id, 'records_retained': True}


def main() -> int:
    database = None
    try:
        database = Database()
        result = run(database)
    except DatabaseConfigurationError:
        result = {'status': 'blocked', 'error': {'code': 'database_unconfigured'}, 'records_retained': True}
    except Exception:
        # Driver exceptions may include credentials or private SQL parameters.
        result = {'status': 'failed', 'error': {'code': 'membership_smoke_failed'}, 'records_retained': True}
    finally:
        if database is not None and database.configuration_error is None:
            database.engine.dispose()
    print(json.dumps(result))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
