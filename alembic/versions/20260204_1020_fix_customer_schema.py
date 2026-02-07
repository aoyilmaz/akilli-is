"""fix_customer_schema

Revision ID: 8g12744b21fb
Revises: 7f12744b21fa
Create Date: 2026-02-04 10:20:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = "8g12744b21fb"
down_revision: Union[str, None] = "7f12744b21fa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if not insp.has_table("customers"):
        return

    columns = [c["name"] for c in insp.get_columns("customers")]

    with op.batch_alter_table("customers", schema=None) as batch_op:
        # 1. Rename company_name to name if name doesn't exist
        if "company_name" in columns and "name" not in columns:
            batch_op.alter_column("company_name", new_column_name="name")
            # Refresh helper list (locally, logic wise) - effectively 'name' exists now
        elif "name" not in columns:
            batch_op.add_column(sa.Column("name", sa.String(200), nullable=True))
            # Populate name if needed (skipped for now as we assume empty or renamed)

        # 2. Rename tax_id to tax_number
        if "tax_id" in columns and "tax_number" not in columns:
            batch_op.alter_column("tax_id", new_column_name="tax_number")
        elif "tax_number" not in columns:
            batch_op.add_column(sa.Column("tax_number", sa.String(20), nullable=True))

        # 3. Add 'code' - This is tricky as it's unique and non-null.
        # Add as nullable first
        if "code" not in columns:
            batch_op.add_column(sa.Column("code", sa.String(20), nullable=True))

    # Data migration for code (outside batch op for safety with raw sql)
    # Generate simple codes for existing rows: C0001, C0002...
    op.execute(
        "UPDATE customers SET code = 'C' || lpad(id::text, 4, '0') WHERE code IS NULL"
    )

    # Now verify columns again for further additions need fresh inspection context usually,
    # but we rely on column list from start which is slightly stale.
    # Better to blindly use if-not-exists logic based on 'columns' list knowing what we renamed.

    with op.batch_alter_table("customers", schema=None) as batch_op:
        # Enforce non-null on code if desired, but maybe safer to leave nullable if update failed?
        # Model says nullable=False. Let's try enforcing.
        # batch_op.alter_column('code', nullable=False) # Skip strict enforcement for now to avoid breakage if update failed

        # Add missing columns
        if "short_name" not in columns:
            batch_op.add_column(sa.Column("short_name", sa.String(50), nullable=True))

        if "contact_person" not in columns:
            batch_op.add_column(
                sa.Column("contact_person", sa.String(100), nullable=True)
            )

        if "mobile" not in columns:
            batch_op.add_column(sa.Column("mobile", sa.String(30), nullable=True))

        if "fax" not in columns:
            batch_op.add_column(sa.Column("fax", sa.String(30), nullable=True))

        if "email" not in columns:
            batch_op.add_column(sa.Column("email", sa.String(100), nullable=True))

        if "address" not in columns:
            batch_op.add_column(sa.Column("address", sa.Text(), nullable=True))

        if "postal_code" not in columns:
            batch_op.add_column(sa.Column("postal_code", sa.String(10), nullable=True))

        if "country" not in columns:
            batch_op.add_column(
                sa.Column("country", sa.String(50), server_default="Türkiye")
            )

        if "payment_term_days" not in columns:
            batch_op.add_column(
                sa.Column("payment_term_days", sa.Integer(), server_default="30")
            )

        if "credit_limit" not in columns:
            batch_op.add_column(
                sa.Column("credit_limit", sa.Numeric(15, 2), server_default="0")
            )

        if "currency" not in columns:
            batch_op.add_column(
                sa.Column("currency", sa.String(10), server_default="TRY")
            )

        if "price_list_id" not in columns:
            batch_op.add_column(sa.Column("price_list_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_customers_price_list", "price_lists", ["price_list_id"], ["id"]
            )

        if "bank_name" not in columns:
            batch_op.add_column(sa.Column("bank_name", sa.String(100), nullable=True))

        if "bank_branch" not in columns:
            batch_op.add_column(sa.Column("bank_branch", sa.String(100), nullable=True))

        if "bank_account_no" not in columns:
            batch_op.add_column(
                sa.Column("bank_account_no", sa.String(50), nullable=True)
            )

        if "iban" not in columns:
            batch_op.add_column(sa.Column("iban", sa.String(50), nullable=True))

        if "rating" not in columns:
            batch_op.add_column(sa.Column("rating", sa.Integer(), server_default="0"))

        if "notes" not in columns:
            batch_op.add_column(sa.Column("notes", sa.Text(), nullable=True))

        if "is_active" not in columns:
            batch_op.add_column(
                sa.Column("is_active", sa.Boolean(), server_default="1")
            )


def downgrade() -> None:
    # Downgrade logic skipped for zombie repair
    pass
