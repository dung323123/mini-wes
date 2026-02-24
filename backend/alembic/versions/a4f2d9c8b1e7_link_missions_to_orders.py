"""link missions to orders

Revision ID: a4f2d9c8b1e7
Revises: 6b5e4a1d9c2f
Create Date: 2026-02-24 11:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4f2d9c8b1e7'
down_revision: Union[str, None] = '6b5e4a1d9c2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('missions', sa.Column('order_id', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_missions_order_id_orders', 'missions', 'orders', ['order_id'], ['id'])
    op.create_index('ix_missions_order_id', 'missions', ['order_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_missions_order_id', table_name='missions')
    op.drop_constraint('fk_missions_order_id_orders', 'missions', type_='foreignkey')
    op.drop_column('missions', 'order_id')
