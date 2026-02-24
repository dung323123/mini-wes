"""add events

Revision ID: 7d21be8c9f01
Revises: f17b3e4a2d90
Create Date: 2026-02-24 12:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d21be8c9f01'
down_revision: Union[str, None] = 'f17b3e4a2d90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('robot_id', sa.UUID(), nullable=True),
        sa.Column('order_id', sa.UUID(), nullable=True),
        sa.Column('mission_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['mission_id'], ['missions.id'], ),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
        sa.ForeignKeyConstraint(['robot_id'], ['robots.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_events_created_at', 'events', ['created_at'], unique=False)
    op.create_index('ix_events_event_type', 'events', ['event_type'], unique=False)
    op.create_index('ix_events_robot_id', 'events', ['robot_id'], unique=False)
    op.create_index('ix_events_order_id', 'events', ['order_id'], unique=False)
    op.create_index('ix_events_mission_id', 'events', ['mission_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_events_mission_id', table_name='events')
    op.drop_index('ix_events_order_id', table_name='events')
    op.drop_index('ix_events_robot_id', table_name='events')
    op.drop_index('ix_events_event_type', table_name='events')
    op.drop_index('ix_events_created_at', table_name='events')
    op.drop_table('events')
