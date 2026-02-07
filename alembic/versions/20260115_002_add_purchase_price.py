"""Add purchase_price to equipments

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-15 11:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6g7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if column exists before adding
    bind = op.get_bind()
    insp = sa.inspect(bind)
    column_names = [c["name"] for c in insp.get_columns("equipments")]

    if "purchase_price" not in column_names:
        with op.batch_alter_table("equipments", schema=None) as batch_op:
            batch_op.add_column(
                sa.Column(
                    "purchase_price", sa.Numeric(precision=18, scale=2), nullable=True
                )
            )
    else:
        print("Column purchase_price already exists in equipments, skipping.")


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    column_names = [c["name"] for c in insp.get_columns("equipments")]

    if "purchase_price" in column_names:
        with op.batch_alter_table("equipments", schema=None) as batch_op:
            batch_op.drop_column("purchase_price")
