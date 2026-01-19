"""add_operation_qc_fields

Revision ID: 5d896da36d67
Revises: d0102112e102
Create Date: 2026-01-18 19:25:24.314624

Operasyon bazlı kalite kontrol alanları eklendi.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5d896da36d67"
down_revision: Union[str, None] = "d0102112e102"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # BOMOperation'a requires_qc ekle
    with op.batch_alter_table("bom_operations", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("requires_qc", sa.Boolean(), default=False, nullable=True)
        )

    # WorkOrderOperation'a requires_qc ve qc_status ekle
    with op.batch_alter_table("work_order_operations", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("requires_qc", sa.Boolean(), default=False, nullable=True)
        )
        batch_op.add_column(sa.Column("qc_status", sa.String(length=20), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("work_order_operations", schema=None) as batch_op:
        batch_op.drop_column("qc_status")
        batch_op.drop_column("requires_qc")

    with op.batch_alter_table("bom_operations", schema=None) as batch_op:
        batch_op.drop_column("requires_qc")
