"""add allocator runs

Revision ID: c92db4e6f3aa
Revises: a4f2d9c8b1e7
Create Date: 2026-02-24 11:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c92db4e6f3aa'
down_revision: Union[str, None] = 'a4f2d9c8b1e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'allocator_runs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('battery_min_pct', sa.Integer(), nullable=False),
        sa.Column('max_orders', sa.Integer(), nullable=False),
        sa.Column('total_orders', sa.Integer(), nullable=False),
        sa.Column('assigned_count', sa.Integer(), nullable=False),
        sa.Column('unassigned_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'allocator_run_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('run_id', sa.UUID(), nullable=False),
        sa.Column('order_id', sa.UUID(), nullable=False),
        sa.Column('robot_id', sa.UUID(), nullable=True),
        sa.Column('mission_id', sa.UUID(), nullable=True),
        sa.Column('result', sa.String(length=32), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('distance', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['mission_id'], ['missions.id'], ),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
        sa.ForeignKeyConstraint(['robot_id'], ['robots.id'], ),
        sa.ForeignKeyConstraint(['run_id'], ['allocator_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index('ix_allocator_runs_created_at', 'allocator_runs', ['created_at'], unique=False)
    op.create_index('ix_allocator_run_items_run_id', 'allocator_run_items', ['run_id'], unique=False)
    op.create_index('ix_allocator_run_items_result', 'allocator_run_items', ['result'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_allocator_run_items_result', table_name='allocator_run_items')
    op.drop_index('ix_allocator_run_items_run_id', table_name='allocator_run_items')
    op.drop_index('ix_allocator_runs_created_at', table_name='allocator_runs')
    op.drop_table('allocator_run_items')
    op.drop_table('allocator_runs')
