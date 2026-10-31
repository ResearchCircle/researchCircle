"""Provenance for immutable public-source versions; private sources stay separate."""

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, JSON, String, text
from sqlalchemy.orm import Mapped, mapped_column

from .models import Base, utcnow


class PublicRecord(Base):
    __tablename__ = 'public_records'
    __table_args__ = (
        CheckConstraint("kind IN ('paper','researcher')", name='ck_public_records_kind'),
        CheckConstraint("evidence_kind IN ('public','synthetic')", name='ck_public_records_evidence'),
        Index('uq_public_records_current', 'external_id', unique=True,
              postgresql_where=text('is_current'), sqlite_where=text('is_current = 1')),
    )
    source_id: Mapped[str] = mapped_column(ForeignKey('sources.id'), primary_key=True)
    external_id: Mapped[str] = mapped_column(String(1000), index=True)
    kind: Mapped[str] = mapped_column(String(20))
    evidence_kind: Mapped[str] = mapped_column(String(20))
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
