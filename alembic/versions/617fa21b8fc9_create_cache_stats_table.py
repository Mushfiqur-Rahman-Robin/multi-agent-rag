"""create_cache_stats_table

Revision ID: 617fa21b8fc9
Revises: 3611184d1964
Create Date: 2026-02-06 19:53:24.996768

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '617fa21b8fc9' # pragma: allowlist secret
down_revision: Union[str, Sequence[str], None] = '3611184d1964'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'cache_audit',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('hits', sa.Integer(), server_default='0', nullable=False),
        sa.Column('misses', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('cache_audit')
