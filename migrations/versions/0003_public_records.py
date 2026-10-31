"""Immutable public-source snapshot metadata."""
from alembic import op
import sqlalchemy as sa

revision = '0003_public_records'
down_revision = '0002_pursuits'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('public_records',
        sa.Column('source_id', sa.String(36), sa.ForeignKey('sources.id'), primary_key=True),
        sa.Column('external_id', sa.String(1000), nullable=False),
        sa.Column('kind', sa.String(20), nullable=False),
        sa.Column('evidence_kind', sa.String(20), nullable=False),
        sa.Column('is_current', sa.Boolean(), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('imported_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("kind IN ('paper','researcher')", name='ck_public_records_kind'),
        sa.CheckConstraint("evidence_kind IN ('public','synthetic')", name='ck_public_records_evidence'))
    op.create_index('ix_public_records_external_id', 'public_records', ['external_id'])
    op.create_index('uq_public_records_current', 'public_records', ['external_id'], unique=True,
                    postgresql_where=sa.text('is_current'), sqlite_where=sa.text('is_current = 1'))


def downgrade():
    op.drop_table('public_records')
