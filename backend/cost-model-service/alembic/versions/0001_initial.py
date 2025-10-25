"""initial schema

Revision ID: 0001
Revises: 
Create Date: 2024-03-16 00:00:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("article_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("unit_weight", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("article_name", name="uq_articles_article_name"),
    )
    op.create_index(op.f("ix_articles_id"), "articles", ["id"], unique=False)

    op.create_table(
        "indices",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("value", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("price_factor", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("unit", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name", name="uq_indices_name"),
    )
    op.create_index(op.f("ix_indices_id"), "indices", ["id"], unique=False)

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=True),
        sa.Column("article_name", sa.String(length=255), nullable=False),
        sa.Column("price", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("price_factor", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("unit", sa.String(length=64), nullable=False),
        sa.Column("order_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_orders_id"), "orders", ["id"], unique=False)

    op.create_table(
        "cost_models",
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("index_id", sa.Integer(), nullable=False),
        sa.Column("part", sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["index_id"], ["indices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("article_id", "index_id", name="pk_cost_models"),
    )


def downgrade() -> None:
    op.drop_table("cost_models")
    op.drop_index(op.f("ix_orders_id"), table_name="orders")
    op.drop_table("orders")
    op.drop_index(op.f("ix_indices_id"), table_name="indices")
    op.drop_table("indices")
    op.drop_index(op.f("ix_articles_id"), table_name="articles")
    op.drop_table("articles")
