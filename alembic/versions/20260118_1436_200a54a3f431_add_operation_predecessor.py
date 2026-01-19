"""add_operation_predecessor

Revision ID: 200a54a3f431
Revises: 6be57edc6e91
Create Date: 2026-01-18 14:36:40.218501

Operasyon bağımlılığı için predecessor alanları eklendi.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "200a54a3f431"
down_revision: Union[str, None] = "6be57edc6e91"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # BOM operasyonlarına predecessor ekle
    with op.batch_alter_table("bom_operations", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("predecessor_operation_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_bomop_predecessor",
            "bom_operations",
            ["predecessor_operation_id"],
            ["id"],
        )

    # İş emri operasyonlarına predecessor ekle
    with op.batch_alter_table("work_order_operations", schema=None) as batch_op:
        batch_op.add_column(sa.Column("predecessor_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_woop_predecessor", "work_order_operations", ["predecessor_id"], ["id"]
        )


def downgrade() -> None:
    with op.batch_alter_table("work_order_operations", schema=None) as batch_op:
        batch_op.drop_constraint("fk_woop_predecessor", type_="foreignkey")
        batch_op.drop_column("predecessor_id")

    with op.batch_alter_table("bom_operations", schema=None) as batch_op:
        batch_op.drop_constraint("fk_bomop_predecessor", type_="foreignkey")
        batch_op.drop_column("predecessor_operation_id")
