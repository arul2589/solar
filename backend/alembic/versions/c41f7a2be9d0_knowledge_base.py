"""knowledge base (RAG) documents and chunks

Revision ID: c41f7a2be9d0
Revises: b808ad91a346
Create Date: 2026-11-26 23:40:00
"""
from alembic import op
import sqlalchemy as sa


revision = 'c41f7a2be9d0'
down_revision = 'b808ad91a346'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'kb_document',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('installer_id', sa.Integer(), sa.ForeignKey('installer.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('filename', sa.String(300), nullable=False),
        sa.Column('storage_key', sa.String(300), nullable=False),
        sa.Column('content_type', sa.String(80), nullable=False),
        sa.Column('size', sa.Integer(), nullable=False),
        sa.Column('sha256', sa.String(64), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('error', sa.String(500), nullable=True),
        sa.Column('pages', sa.Integer(), nullable=False),
        sa.Column('vision_pages', sa.Integer(), nullable=False),
        sa.Column('chunk_count', sa.Integer(), nullable=False),
        sa.Column('uploaded_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_kb_document_installer_id', 'kb_document', ['installer_id'])
    op.create_index('ix_kb_document_sha256', 'kb_document', ['sha256'])
    op.create_index('ix_kb_document_status', 'kb_document', ['status'])
    op.create_table(
        'kb_chunk',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('installer_id', sa.Integer(), sa.ForeignKey('installer.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_id', sa.Integer(), sa.ForeignKey('kb_document.id', ondelete='CASCADE'), nullable=False),
        sa.Column('page', sa.Integer(), nullable=False),
        sa.Column('ordinal', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('embedding', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_kb_chunk_installer_id', 'kb_chunk', ['installer_id'])
    op.create_index('ix_kb_chunk_document_id', 'kb_chunk', ['document_id'])


def downgrade() -> None:
    op.drop_table('kb_chunk')
    op.drop_table('kb_document')
