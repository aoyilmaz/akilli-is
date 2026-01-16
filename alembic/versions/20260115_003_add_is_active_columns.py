"""Add is_active columns to new tables

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-01-15 10:45:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6g7h8"
down_revision: Union[str, None] = "b2c3d4e5f6g7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_active to equipment_downtimes
    with op.batch_alter_table('equipment_downtimes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'))

    # Add is_active to equipment_spare_parts
    with op.batch_alter_table('equipment_spare_parts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'))

    # Add is_active to maintenance_checklist_items
    with op.batch_alter_table('maintenance_checklist_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'))

    # Add is_active to maintenance_request_attachments
    with op.batch_alter_table('maintenance_request_attachments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'))

    # Add is_active to work_order_attachments
    with op.batch_alter_table('work_order_attachments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'))

    # Add is_active to work_order_checklist_results
    with op.batch_alter_table('work_order_checklist_results', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'))


def downgrade() -> None:
    tables = [
        'equipment_downtimes',
        'equipment_spare_parts',
        'maintenance_checklist_items',
        'maintenance_request_attachments',
        'work_order_attachments',
        'work_order_checklist_results',
    ]

    for table in tables:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.drop_column('is_active')
