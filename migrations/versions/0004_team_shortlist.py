"""Saved team shortlist with explicit user curation and immutable source references."""
from alembic import op
import sqlalchemy as sa

revision = '0004_team_shortlist'
down_revision = '0003_public_records'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('team_shortlist_entries',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('team_id', sa.String(36), sa.ForeignKey('teams.id'), nullable=False),
        sa.Column('source_id', sa.String(36), sa.ForeignKey('sources.id'), nullable=False),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('note', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('team_id', 'source_id', name='uq_team_shortlist_source'))
    op.create_index('ix_team_shortlist_entries_team_id', 'team_shortlist_entries', ['team_id'])


def downgrade():
    op.drop_table('team_shortlist_entries')
