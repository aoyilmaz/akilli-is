"""fix_woo_schema

Revision ID: 6e12744b21ef
Revises: 5d12744b21ee
Create Date: 2026-02-03 22:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = "6e12744b21ef"
down_revision: Union[str, None] = "5d12744b21ee"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if not insp.has_table("work_order_operations"):
        return

    columns = [c["name"] for c in insp.get_columns("work_order_operations")]

    with op.batch_alter_table("work_order_operations", schema=None) as batch_op:
        if "last_start_time" not in columns:
            batch_op.add_column(
                sa.Column("last_start_time", sa.DateTime(), nullable=True)
            )

        if "purchase_order_id" not in columns:
            batch_op.add_column(
                sa.Column("purchase_order_id", sa.Integer(), nullable=True)
            )
            batch_op.create_foreign_key(
                "fk_woop_purchase_order",
                "purchase_orders",
                ["purchase_order_id"],
                ["id"],
            )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    columns = [c["name"] for c in insp.get_columns("work_order_operations")]

    with op.batch_alter_table("work_order_operations", schema=None) as batch_op:
        if "purchase_order_id" in columns:
            batch_op.drop_constraint("fk_woop_purchase_order", type_="foreignkey")
            batch_op.drop_column("purchase_order_id")

        if "last_start_time" in columns:
            batch_op.drop_column("last_start_time")
