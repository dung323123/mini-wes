"""add telemetry

Revision ID: f17b3e4a2d90
Revises: c92db4e6f3aa
Create Date: 2026-02-24 11:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f17b3e4a2d90'
down_revision: Union[str, None] = 'c92db4e6f3aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'telemetry',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('robot_id', sa.UUID(), nullable=False),
        sa.Column('x', sa.Float(), nullable=False),
        sa.Column('y', sa.Float(), nullable=False),
        sa.Column('theta', sa.Float(), nullable=False),
        sa.Column('battery_pct', sa.Integer(), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['robot_id'], ['robots.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_telemetry_robot_recorded_at', 'telemetry', ['robot_id', 'recorded_at'], unique=False)
    op.create_index('ix_telemetry_recorded_at', 'telemetry', ['recorded_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_telemetry_recorded_at', table_name='telemetry')
    op.drop_index('ix_telemetry_robot_recorded_at', table_name='telemetry')
    op.drop_table('telemetry')
