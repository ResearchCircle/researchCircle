import hashlib
import secrets
from datetime import timedelta

from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.platform.database.models import LoginSession, User, utcnow
from .errors import WorkflowError

password_hasher = PasswordHash.recommended()
# Equal-cost verification for unknown emails avoids a cheap account-existence oracle.
_dummy_hash = password_hasher.hash(secrets.token_urlsafe(24))


def authenticate(session: Session, email: str, password: str) -> User:
    user = session.scalar(select(User).where(User.email == email))
    valid = password_hasher.verify(password, user.password_hash if user else _dummy_hash)
    if user is None or not valid:
        raise WorkflowError(401, 'invalid_credentials', 'Email or password is incorrect')
    return user


def create_session(session: Session, user: User) -> str:
    token = secrets.token_urlsafe(32)
    session.add(LoginSession(user_id=user.id, token_hash=hashlib.sha256(token.encode()).hexdigest(),
                             expires_at=utcnow() + timedelta(days=7)))
    return token
