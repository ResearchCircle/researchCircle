"""Manual team opportunities, proposal pursuits, history and outcomes."""
from alembic import op
import sqlalchemy as sa

revision = '0002_pursuits'
down_revision = '0001_workflow_core'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('opportunities',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('team_id', sa.String(36), sa.ForeignKey('teams.id'), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deadline_timezone', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=False),
        sa.Column('eligibility', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("eligibility IN ('unknown','eligible','ineligible')", name='ck_opportunities_eligibility'))
    op.create_index('ix_opportunities_team_id', 'opportunities', ['team_id'])
    op.create_table('pursuits',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('proposal_id', sa.String(36), sa.ForeignKey('proposals.id'), nullable=False),
        sa.Column('opportunity_id', sa.String(36), sa.ForeignKey('opportunities.id'), nullable=True),
        sa.Column('state', sa.String(20), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('proposal_id', name='uq_pursuits_proposal_id'),
        sa.CheckConstraint("state IN ('draft','shortlisted','collaborating','submitted','won','lost','withdrawn')", name='ck_pursuits_state'))
    op.create_table('pursuit_history',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('pursuit_id', sa.String(36), sa.ForeignKey('pursuits.id'), nullable=False),
        sa.Column('from_state', sa.String(20), nullable=True),
        sa.Column('to_state', sa.String(20), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_pursuit_history_pursuit_id', 'pursuit_history', ['pursuit_id'])
    op.create_table('outcomes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('pursuit_id', sa.String(36), sa.ForeignKey('pursuits.id'), nullable=False),
        sa.Column('outcome', sa.String(20), nullable=False),
        sa.Column('idempotency_key', sa.String(200), nullable=False),
        sa.Column('award_reference', sa.String(1000), nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('pursuit_id', 'idempotency_key', name='uq_outcomes_pursuit_key'),
        sa.CheckConstraint("outcome IN ('won','lost','withdrawn')", name='ck_outcomes_outcome'))
    op.create_index('ix_outcomes_pursuit_id', 'outcomes', ['pursuit_id'])


def downgrade():
    for name in ('outcomes', 'pursuit_history', 'pursuits', 'opportunities'):
        op.drop_table(name)
