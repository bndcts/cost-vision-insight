"""add similar_articles field

Revision ID: 0006
Revises: 0005
Create Date: 2025-10-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0006'
down_revision: Union[str, None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add similar_articles column to articles table (stores array of article IDs)
    op.add_column('articles', sa.Column('similar_articles', postgresql.ARRAY(sa.Integer()), nullable=True))


def downgrade() -> None:
    op.drop_column('articles', 'similar_articles')

