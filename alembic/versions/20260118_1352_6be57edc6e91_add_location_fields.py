"""add_location_fields

Revision ID: 6be57edc6e91
Revises: 0a404c858c12
Create Date: 2026-01-18 13:52:01.827728

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = "6be57edc6e91"
down_revision: Union[str, None] = "0a404c858c12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # 1. FK constraint check
    fks = [fk["name"] for fk in inspector.get_foreign_keys("account_transactions")]
    if "fk_account_transactions_customer" not in fks:
        with op.batch_alter_table("account_transactions", schema=None) as batch_op:
            batch_op.create_foreign_key(
                "fk_account_transactions_customer", "customers", ["customer_id"], ["id"]
            )

    # 2. Add location fields safely
    existing_columns = [c["name"] for c in inspector.get_columns("warehouse_locations")]

    with op.batch_alter_table("warehouse_locations", schema=None) as batch_op:
        if "barcode" not in existing_columns:
            batch_op.add_column(
                sa.Column("barcode", sa.String(length=50), nullable=True)
            )
            batch_op.create_index("idx_location_barcode", ["barcode"], unique=False)
            batch_op.create_unique_constraint("uq_location_barcode", ["barcode"])

        if "priority" not in existing_columns:
            batch_op.add_column(sa.Column("priority", sa.Integer(), nullable=True))

        if "zone" not in existing_columns:
            batch_op.add_column(sa.Column("zone", sa.String(length=50), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("warehouse_locations", schema=None) as batch_op:
        batch_op.drop_constraint("uq_location_barcode", type_="unique")
        batch_op.drop_index("idx_location_barcode")
        batch_op.drop_column("zone")
        batch_op.drop_column("priority")
        batch_op.drop_column("barcode")

    with op.batch_alter_table("account_transactions", schema=None) as batch_op:
        batch_op.drop_constraint("fk_account_transactions_customer", type_="foreignkey")
