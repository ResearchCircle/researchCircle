"""Named accounts, teams, revisioned proposals, sources and durable draft jobs."""
from alembic import op
import sqlalchemy as sa

revision = '0001_workflow_core'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(320), nullable=False, unique=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_table('teams',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_table('login_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('token_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_login_sessions_user_id', 'login_sessions', ['user_id'])
    op.create_table('memberships',
        sa.Column('team_id', sa.String(36), sa.ForeignKey('teams.id'), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), primary_key=True),
        sa.Column('role', sa.String(10), nullable=False),
        sa.CheckConstraint("role IN ('owner','editor','viewer')"))
    op.create_table('invitations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('team_id', sa.String(36), sa.ForeignKey('teams.id'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('invited_by', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('role', sa.String(10), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('team_id', 'user_id'),
        sa.CheckConstraint("role IN ('editor','viewer')"))
    op.create_index('ix_invitations_team_id', 'invitations', ['team_id'])
    op.create_index('ix_invitations_user_id', 'invitations', ['user_id'])
    op.create_table('proposals',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('team_id', sa.String(36), sa.ForeignKey('teams.id'), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('revision', sa.Integer(), nullable=False),
        sa.Column('selected_source_ids', sa.JSON(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_proposals_team_id', 'proposals', ['team_id'])
    op.create_table('sources',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('version', sa.String(100), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('origin', sa.Text(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('proposal_id', sa.String(36), sa.ForeignKey('proposals.id'), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False))
    op.create_index('ix_sources_proposal_id', 'sources', ['proposal_id'])
    op.create_table('proposal_sources',
        sa.Column('proposal_id', sa.String(36), sa.ForeignKey('proposals.id'), primary_key=True),
        sa.Column('source_id', sa.String(36), sa.ForeignKey('sources.id'), primary_key=True))
    op.create_table('draft_jobs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('proposal_id', sa.String(36), sa.ForeignKey('proposals.id'), nullable=False),
        sa.Column('state', sa.String(20), nullable=False),
        sa.Column('request_json', sa.JSON(), nullable=False),
        sa.Column('sources_json', sa.JSON(), nullable=False),
        sa.Column('output_json', sa.JSON(), nullable=True),
        sa.Column('error_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_draft_jobs_user_id', 'draft_jobs', ['user_id'])
    op.create_index('ix_draft_jobs_proposal_id', 'draft_jobs', ['proposal_id'])
    op.create_index('ix_draft_jobs_state', 'draft_jobs', ['state'])


def downgrade():
    for name in ('draft_jobs', 'proposal_sources', 'sources', 'proposals', 'invitations',
                 'memberships', 'login_sessions', 'teams', 'users'):
        op.drop_table(name)
