"""Add category column if it doesn't exist

Revision ID: add_category_field
Revises:
Create Date: 2025-05-04 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = 'add_category_field'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Check if the category column already exists before trying to add it
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [column['name']
               for column in inspector.get_columns('news_articles')]

    if 'category' not in columns:
        op.add_column('news_articles', sa.Column(
            'category', sa.String(50), nullable=True))

    # Also add the ai_summary column if it doesn't exist
    if 'ai_summary' not in columns:
        op.add_column('news_articles', sa.Column(
            'ai_summary', sa.Text(), nullable=True))


def downgrade():
    # Drop the category column if it exists
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [column['name']
               for column in inspector.get_columns('news_articles')]

    if 'category' in columns:
        op.drop_column('news_articles', 'category')

    if 'ai_summary' in columns:
        op.drop_column('news_articles', 'ai_summary')
