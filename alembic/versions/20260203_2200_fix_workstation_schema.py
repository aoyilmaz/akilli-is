"""fix_workstation_schema

Revision ID: 5d12744b21ee
Revises: 4c12744b21dd
Create Date: 2026-02-03 22:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = "5d12744b21ee"
down_revision: Union[str, None] = "4c12744b21dd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if not insp.has_table("work_stations"):
        # This shouldn't ensure create here as likely it exists but missing cols.
        # But if it really doesn't exist, we let standard migrations handle it or create it here?
        # Assuming it exists based on error.
        return

    columns = [c["name"] for c in insp.get_columns("work_stations")]

    with op.batch_alter_table("work_stations", schema=None) as batch_op:
        if "overhead_rate" not in columns:
            batch_op.add_column(
                sa.Column("overhead_rate", sa.Numeric(18, 4), server_default="0")
            )

        if "is_external" not in columns:
            batch_op.add_column(
                sa.Column("is_external", sa.Boolean(), server_default="0")
            )

        if "supplier_id" not in columns:
            batch_op.add_column(sa.Column("supplier_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_work_stations_supplier", "suppliers", ["supplier_id"], ["id"]
            )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    columns = [c["name"] for c in insp.get_columns("work_stations")]

    with op.batch_alter_table("work_stations", schema=None) as batch_op:
        if "supplier_id" in columns:
            batch_op.drop_constraint("fk_work_stations_supplier", type_="foreignkey")
            batch_op.drop_column("supplier_id")

        if "is_external" in columns:
            batch_op.drop_column("is_external")

        if "overhead_rate" in columns:
            batch_op.drop_column("overhead_rate")
