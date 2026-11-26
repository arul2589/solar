"""design review (AI cross-check before sending a quotation)

Revision ID: e5c2a9d4b7f1
Revises: d7a3c5e1f2b4
Create Date: 2026-11-27 00:40:00
"""
from alembic import op
import sqlalchemy as sa


revision = 'e5c2a9d4b7f1'
down_revision = 'd7a3c5e1f2b4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'design_review',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('installer_id', sa.Integer(), sa.ForeignKey('installer.id', ondelete='CASCADE'), nullable=False),
        sa.Column('analysis_run_id', sa.Integer(), sa.ForeignKey('analysis_run.id', ondelete='CASCADE'), nullable=False),
        sa.Column('items', sa.JSON(), nullable=True),
        sa.Column('sources', sa.JSON(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('conflicts', sa.Integer(), nullable=False),
        sa.Column('checks', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('acknowledged_by', sa.Integer(), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ack_note', sa.Text(), nullable=True),
    )
    op.create_index('ix_design_review_installer_id', 'design_review', ['installer_id'])
    op.create_index('ix_design_review_analysis_run_id', 'design_review', ['analysis_run_id'])


def downgrade() -> None:
    op.drop_table('design_review')
