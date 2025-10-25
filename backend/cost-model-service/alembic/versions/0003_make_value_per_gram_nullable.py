"""allow nullable value_per_gram

Revision ID: 0003
Revises: 0002
Create Date: 2024-10-25 00:00:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "indices",
        "value_per_gram",
        existing_type=sa.Numeric(precision=18, scale=6),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "indices",
        "value_per_gram",
        existing_type=sa.Numeric(precision=18, scale=6),
        nullable=False,
    )
