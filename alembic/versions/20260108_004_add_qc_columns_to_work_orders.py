"""Add QC columns to work_orders table

Revision ID: 004_add_qc_columns
Revises: 002_add_error_log_table
Create Date: 2026-01-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004_add_qc_columns'
down_revision: Union[str, None] = '002_add_error_log_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add Quality Control columns to work_orders table
    - qc_approved_quantity: Kalite onaylı miktar
    - qc_rejected_quantity: Kalite red miktar
    - qc_notes: Kalite kontrol notları
    - qc_checked_by: Kalite kontrol yapan kullanıcı
    - qc_checked_at: Kalite kontrol tarihi
    """

    with op.batch_alter_table('work_orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('qc_approved_quantity', sa.Numeric(18, 4), server_default='0', nullable=True))
        batch_op.add_column(sa.Column('qc_rejected_quantity', sa.Numeric(18, 4), server_default='0', nullable=True))
        batch_op.add_column(sa.Column('qc_notes', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('qc_checked_by', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('qc_checked_at', sa.DateTime(), nullable=True))

        # Foreign key for qc_checked_by
        batch_op.create_foreign_key(
            'fk_work_orders_qc_checked_by',
            'users',
            ['qc_checked_by'],
            ['id']
        )


def downgrade() -> None:
    """Remove QC columns from work_orders table"""

    with op.batch_alter_table('work_orders', schema=None) as batch_op:
        batch_op.drop_constraint('fk_work_orders_qc_checked_by', type_='foreignkey')
        batch_op.drop_column('qc_checked_at')
        batch_op.drop_column('qc_checked_by')
        batch_op.drop_column('qc_notes')
        batch_op.drop_column('qc_rejected_quantity')
        batch_op.drop_column('qc_approved_quantity')
