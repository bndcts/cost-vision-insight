"""add value_per_gram column and name/date uniqueness

Revision ID: 0002
Revises: 0001
Create Date: 2024-10-25 00:00:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "indices",
        sa.Column(
            "value_per_gram",
            sa.Numeric(precision=18, scale=6),
            nullable=False,
            server_default="0",
        ),
    )
    op.drop_constraint("uq_indices_name", "indices", type_="unique")
    op.create_unique_constraint("uq_indices_name_date", "indices", ["name", "date"])
    op.alter_column("indices", "value_per_gram", server_default=None)


def downgrade() -> None:
    op.drop_constraint("uq_indices_name_date", "indices", type_="unique")
    op.create_unique_constraint("uq_indices_name", "indices", ["name"])
    op.drop_column("indices", "value_per_gram")
