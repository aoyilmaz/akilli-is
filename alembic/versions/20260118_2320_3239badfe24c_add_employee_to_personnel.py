"""add_employee_to_personnel

Revision ID: 3239badfe24c
Revises: 5d896da36d67
Create Date: 2026-01-18 23:20:33.124759

WorkOrderOperationPersonnel modeline employee_id eklendi.
User'a bağlı olmayan çalışanlar da operasyona atanabilir.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = "3239badfe24c"
down_revision: Union[str, None] = "5d896da36d67"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [
        c["name"] for c in inspector.get_columns("work_order_operation_personnel")
    ]
    fks = [
        fk["name"]
        for fk in inspector.get_foreign_keys("work_order_operation_personnel")
    ]

    with op.batch_alter_table(
        "work_order_operation_personnel", schema=None
    ) as batch_op:
        # employee_id ekle (idempotent)
        if "employee_id" not in columns:
            batch_op.add_column(sa.Column("employee_id", sa.Integer(), nullable=True))

        # user_id artık nullable
        batch_op.alter_column("user_id", existing_type=sa.INTEGER(), nullable=True)

        # Index ekle (handled separately safely or via batch if we knew it didn't exist, but safest is raw SQL outside)
        # batch_op.create_index("idx_woopp_emp", ["employee_id"], unique=False)

        # Foreign key ekle
        if "fk_woopp_employee" not in fks:
            batch_op.create_foreign_key(
                "fk_woopp_employee", "employees", ["employee_id"], ["id"]
            )

    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_woopp_emp ON work_order_operation_personnel (employee_id)"
    )


def downgrade() -> None:
    with op.batch_alter_table(
        "work_order_operation_personnel", schema=None
    ) as batch_op:
        batch_op.drop_constraint("fk_woopp_employee", type_="foreignkey")
        batch_op.drop_index("idx_woopp_emp")
        batch_op.alter_column("user_id", existing_type=sa.INTEGER(), nullable=False)
        batch_op.drop_column("employee_id")
