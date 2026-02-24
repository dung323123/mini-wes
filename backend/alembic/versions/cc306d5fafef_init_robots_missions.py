"""init robots missions

Revision ID: cc306d5fafef
Revises: 989ce2fd5280
Create Date: 2026-02-24 00:47:22.999117

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc306d5fafef'
down_revision: Union[str, None] = '989ce2fd5280'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Kept as no-op for compatibility with existing revision history.
    pass


def downgrade() -> None:
    # Kept as no-op for compatibility with existing revision history.
    pass
