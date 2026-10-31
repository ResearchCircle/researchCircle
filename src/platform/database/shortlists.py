"""User-curated team entries retain their immutable public source snapshot."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .models import Base, new_id, utcnow


class TeamShortlistEntry(Base):
    __tablename__ = 'team_shortlist_entries'
    __table_args__ = (UniqueConstraint('team_id', 'source_id', name='uq_team_shortlist_source'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    team_id: Mapped[str] = mapped_column(ForeignKey('teams.id'), index=True)
    source_id: Mapped[str] = mapped_column(ForeignKey('sources.id'))
    created_by: Mapped[str] = mapped_column(ForeignKey('users.id'))
    note: Mapped[str] = mapped_column(Text, default='')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
