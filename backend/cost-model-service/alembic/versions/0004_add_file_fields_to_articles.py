"""add file fields to articles

Revision ID: 0004
Revises: 0003
Create Date: 2025-10-25 00:00:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "articles",
        sa.Column("product_specification_file", sa.LargeBinary, nullable=True),
    )
    op.add_column(
        "articles",
        sa.Column("product_specification_filename", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "articles",
        sa.Column("drawing_file", sa.LargeBinary, nullable=True),
    )
    op.add_column(
        "articles",
        sa.Column("drawing_filename", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "articles",
        sa.Column("comment", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("articles", "comment")
    op.drop_column("articles", "drawing_filename")
    op.drop_column("articles", "drawing_file")
    op.drop_column("articles", "product_specification_filename")
    op.drop_column("articles", "product_specification_file")


