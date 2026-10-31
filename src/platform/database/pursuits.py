"""Manual opportunities and proposal submission/outcome records."""
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .models import Base, new_id, utcnow


class Opportunity(Base):
    __tablename__ = 'opportunities'
    __table_args__ = (CheckConstraint("eligibility IN ('unknown','eligible','ineligible')", name='ck_opportunities_eligibility'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    team_id: Mapped[str] = mapped_column(ForeignKey('teams.id'), index=True)
    title: Mapped[str] = mapped_column(String(300))
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deadline_timezone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str] = mapped_column(Text, default='')
    eligibility: Mapped[str] = mapped_column(String(20), default='unknown')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Pursuit(Base):
    __tablename__ = 'pursuits'
    __table_args__ = (
        UniqueConstraint('proposal_id', name='uq_pursuits_proposal_id'),
        CheckConstraint("state IN ('draft','shortlisted','collaborating','submitted','won','lost','withdrawn')", name='ck_pursuits_state'))
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    proposal_id: Mapped[str] = mapped_column(ForeignKey('proposals.id'))
    opportunity_id: Mapped[str | None] = mapped_column(ForeignKey('opportunities.id'), nullable=True)
    state: Mapped[str] = mapped_column(String(20))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PursuitHistory(Base):
    __tablename__ = 'pursuit_history'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    pursuit_id: Mapped[str] = mapped_column(ForeignKey('pursuits.id'), index=True)
    from_state: Mapped[str | None] = mapped_column(String(20), nullable=True)
    to_state: Mapped[str] = mapped_column(String(20))
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Outcome(Base):
    __tablename__ = 'outcomes'
    __table_args__ = (
        UniqueConstraint('pursuit_id', 'idempotency_key', name='uq_outcomes_pursuit_key'),
        CheckConstraint("outcome IN ('won','lost','withdrawn')", name='ck_outcomes_outcome'))
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    pursuit_id: Mapped[str] = mapped_column(ForeignKey('pursuits.id'), index=True)
    outcome: Mapped[str] = mapped_column(String(20))
    idempotency_key: Mapped[str] = mapped_column(String(200))
    award_reference: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
