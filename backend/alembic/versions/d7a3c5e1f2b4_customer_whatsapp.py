"""customer whatsapp number and quotation channel

Revision ID: d7a3c5e1f2b4
Revises: c41f7a2be9d0
Create Date: 2026-11-27 00:20:00
"""
from alembic import op
import sqlalchemy as sa


revision = 'd7a3c5e1f2b4'
down_revision = 'c41f7a2be9d0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('customer', sa.Column('whatsapp', sa.String(32), nullable=True))
    op.add_column('customer', sa.Column('contact_pref', sa.String(12), nullable=False, server_default='email'))


def downgrade() -> None:
    op.drop_column('customer', 'contact_pref')
    op.drop_column('customer', 'whatsapp')
