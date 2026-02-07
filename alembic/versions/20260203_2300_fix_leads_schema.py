"""fix_leads_schema

Revision ID: 7f12744b21fa
Revises: 6e12744b21ef
Create Date: 2026-02-03 23:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = "7f12744b21fa"
down_revision: Union[str, None] = "6e12744b21ef"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if not insp.has_table("leads"):
        return

    columns = [c["name"] for c in insp.get_columns("leads")]

    with op.batch_alter_table("leads", schema=None) as batch_op:
        if "title" not in columns:
            batch_op.add_column(sa.Column("title", sa.String(100), nullable=True))

        if "email" not in columns:
            batch_op.add_column(sa.Column("email", sa.String(100), nullable=True))

        if "phone" not in columns:
            batch_op.add_column(sa.Column("phone", sa.String(30), nullable=True))

        if "mobile" not in columns:
            batch_op.add_column(sa.Column("mobile", sa.String(30), nullable=True))

        if "website" not in columns:
            batch_op.add_column(sa.Column("website", sa.String(200), nullable=True))

        if "address" not in columns:
            batch_op.add_column(sa.Column("address", sa.Text(), nullable=True))

        if "city" not in columns:
            batch_op.add_column(sa.Column("city", sa.String(50), nullable=True))

        if "country" not in columns:
            batch_op.add_column(
                sa.Column("country", sa.String(50), server_default="Türkiye")
            )

        if "notes" not in columns:
            batch_op.add_column(sa.Column("notes", sa.Text(), nullable=True))

        if "assigned_to_id" not in columns:
            batch_op.add_column(
                sa.Column("assigned_to_id", sa.Integer(), nullable=True)
            )
            batch_op.create_foreign_key(
                "fk_leads_assigned_to", "users", ["assigned_to_id"], ["id"]
            )

        if "is_active" not in columns:
            batch_op.add_column(
                sa.Column("is_active", sa.Boolean(), server_default="1")
            )


def downgrade() -> None:
    # Downgrade logic skipped for zombie repair
    pass
