"""add direct_cost_eur to cost_models

Revision ID: 0007
Revises: 0006
Create Date: 2025-10-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0007'
down_revision: Union[str, None] = '0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add direct_cost_eur column to cost_models table."""
    op.add_column(
        'cost_models',
        sa.Column('direct_cost_eur', sa.Numeric(precision=10, scale=4), nullable=True)
    )


def downgrade() -> None:
    """Remove direct_cost_eur column from cost_models table."""
    op.drop_column('cost_models', 'direct_cost_eur')

