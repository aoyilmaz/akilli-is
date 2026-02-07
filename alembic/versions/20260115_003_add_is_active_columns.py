"""Add is_active columns to new tables

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-01-15 10:45:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6g7h8"
down_revision: Union[str, None] = "b2c3d4e5f6g7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def add_column_safe(table_name, column_name, column_type, default=None):
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if not insp.has_table(table_name):
        return  # Or handle error? But here if table missing, adding col fails anyway.
        # Since 001 ensures existence, we assume it exists.

    columns = [c["name"] for c in insp.get_columns(table_name)]
    if column_name not in columns:
        with op.batch_alter_table(table_name, schema=None) as batch_op:
            batch_op.add_column(
                sa.Column(
                    column_name, column_type, nullable=True, server_default=default
                )
            )
    else:
        print(f"Column {column_name} already exists in {table_name}, skipping.")


def upgrade() -> None:
    tables = [
        "equipment_downtimes",
        "equipment_spare_parts",
        "maintenance_checklist_items",
        "maintenance_request_attachments",
        "work_order_attachments",
        "work_order_checklist_results",
    ]

    for table in tables:
        add_column_safe(table, "is_active", sa.Boolean(), "true")


def downgrade() -> None:
    # Downgrade logic also safe check
    bind = op.get_bind()
    insp = sa.inspect(bind)

    tables = [
        "equipment_downtimes",
        "equipment_spare_parts",
        "maintenance_checklist_items",
        "maintenance_request_attachments",
        "work_order_attachments",
        "work_order_checklist_results",
    ]

    for table in tables:
        if insp.has_table(table):
            columns = [c["name"] for c in insp.get_columns(table)]
            if "is_active" in columns:
                with op.batch_alter_table(table, schema=None) as batch_op:
                    batch_op.drop_column("is_active")
