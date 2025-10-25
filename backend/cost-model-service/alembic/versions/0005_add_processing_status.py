"""add processing status fields

Revision ID: 0005
Revises: 0004
Create Date: 2025-10-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0005'
down_revision: Union[str, None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add processing status fields to articles table
    op.add_column('articles', sa.Column('processing_status', sa.String(length=50), nullable=False, server_default='pending'))
    op.add_column('articles', sa.Column('processing_error', sa.Text(), nullable=True))
    op.add_column('articles', sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('articles', sa.Column('processing_completed_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove processing status fields
    op.drop_column('articles', 'processing_completed_at')
    op.drop_column('articles', 'processing_started_at')
    op.drop_column('articles', 'processing_error')
    op.drop_column('articles', 'processing_status')

