"""add orders

Revision ID: 6b5e4a1d9c2f
Revises: 3aac46238d94
Create Date: 2026-02-24 10:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b5e4a1d9c2f'
down_revision: Union[str, None] = '3aac46238d94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'orders',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(length=64), nullable=False),
        sa.Column('pickup_x', sa.Float(), nullable=False),
        sa.Column('pickup_y', sa.Float(), nullable=False),
        sa.Column('dropoff_x', sa.Float(), nullable=False),
        sa.Column('dropoff_y', sa.Float(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )
    op.create_index('ix_orders_status', 'orders', ['status'], unique=False)
    op.create_index('ix_orders_priority', 'orders', ['priority'], unique=False)
    op.create_index('ix_orders_created_at', 'orders', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_orders_created_at', table_name='orders')
    op.drop_index('ix_orders_priority', table_name='orders')
    op.drop_index('ix_orders_status', table_name='orders')
    op.drop_table('orders')
