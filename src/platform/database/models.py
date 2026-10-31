"""Business records shared by the API and the persisted drafting worker."""
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def new_id() -> str:
    return str(uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LoginSession(Base):
    __tablename__ = 'login_sessions'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Team(Base):
    __tablename__ = 'teams'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Membership(Base):
    __tablename__ = 'memberships'
    __table_args__ = (CheckConstraint("role IN ('owner','editor','viewer')"),)
    team_id: Mapped[str] = mapped_column(ForeignKey('teams.id'), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), primary_key=True)
    role: Mapped[str] = mapped_column(String(10))


class Invitation(Base):
    __tablename__ = 'invitations'
    __table_args__ = (UniqueConstraint('team_id', 'user_id'), CheckConstraint("role IN ('editor','viewer')"))
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    team_id: Mapped[str] = mapped_column(ForeignKey('teams.id'), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    invited_by: Mapped[str] = mapped_column(ForeignKey('users.id'))
    role: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Proposal(Base):
    __tablename__ = 'proposals'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    team_id: Mapped[str] = mapped_column(ForeignKey('teams.id'), index=True)
    title: Mapped[str] = mapped_column(String(300))
    content: Mapped[str] = mapped_column(Text, default='')
    revision: Mapped[int] = mapped_column(Integer, default=1)
    selected_source_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Source(Base):
    __tablename__ = 'sources'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    version: Mapped[str] = mapped_column(String(100), default='1')
    content_hash: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(500))
    origin: Mapped[str] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text)
    proposal_id: Mapped[str | None] = mapped_column(ForeignKey('proposals.id'), nullable=True, index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)


class ProposalSource(Base):
    __tablename__ = 'proposal_sources'
    proposal_id: Mapped[str] = mapped_column(ForeignKey('proposals.id'), primary_key=True)
    source_id: Mapped[str] = mapped_column(ForeignKey('sources.id'), primary_key=True)
