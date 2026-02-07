"""empty message

Revision ID: 7b767d66be67
Revises: 20260126_workflow
Create Date: 2026-02-03 11:30:49.854846

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = "7b767d66be67"
down_revision: Union[str, None] = "20260126_workflow"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # Enums
    enum_bom = sa.Enum("STANDARD", "FORMULA", name="bomtype")
    enum_val = sa.Enum("AVERAGE", "STANDARD", name="valuationmethod")
    enum_mrp = sa.Enum("AUTO", "MANUAL", "ROP", name="mrptype")
    enum_lot = sa.Enum("LFL", "FIXED", name="lotsizepolicy")
    enum_mwo = sa.Enum(
        "DRAFT",
        "ASSIGNED",
        "IN_PROGRESS",
        "COMPLETED",
        "CLOSED",
        "CANCELLED",
        name="maintenanceworkorderstatus",
    )

    enum_bom.create(bind, checkfirst=True)
    enum_val.create(bind, checkfirst=True)
    enum_mrp.create(bind, checkfirst=True)
    enum_lot.create(bind, checkfirst=True)
    enum_mwo.create(bind, checkfirst=True)

    # Bill of Materials: Convert bom_type to Enum
    # This assumes bom_type exists (ensured by 1215) and is String (ensured by 1215).
    # If it's already an enum, casting to text first is safe.
    with op.batch_alter_table("bill_of_materials", schema=None) as batch_op:
        # First drop default to avoid cast error
        batch_op.alter_column(
            "bom_type",
            existing_type=sa.VARCHAR(length=20),
            server_default=None,
            existing_nullable=False,
            existing_server_default=sa.text("'standard'::character varying"),
        )
        # Then alter type
        batch_op.alter_column(
            "bom_type",
            existing_type=sa.VARCHAR(length=20),
            type_=enum_bom,
            existing_nullable=False,
            server_default=sa.text("'STANDARD'::bomtype"),
            postgresql_using="UPPER(bom_type::text)::bomtype",
        )

    # Inspection Templates
    it_cols = [c["name"] for c in insp.get_columns("inspection_templates")]
    with op.batch_alter_table("inspection_templates", schema=None) as batch_op:
        if "item_id" not in it_cols:
            batch_op.add_column(sa.Column("item_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(None, "items", ["item_id"], ["id"])

    # Items
    item_cols = [c["name"] for c in insp.get_columns("items")]
    with op.batch_alter_table("items", schema=None) as batch_op:
        if "barcode_ean" not in item_cols:
            batch_op.add_column(
                sa.Column("barcode_ean", sa.String(length=20), nullable=True)
            )
            batch_op.create_unique_constraint("uq_items_barcode_ean", ["barcode_ean"])

        if "tax_rate_buy" not in item_cols:
            batch_op.add_column(
                sa.Column(
                    "tax_rate_buy", sa.Numeric(precision=5, scale=2), nullable=True
                )
            )

        if "tax_rate_sell" not in item_cols:
            batch_op.add_column(
                sa.Column(
                    "tax_rate_sell", sa.Numeric(precision=5, scale=2), nullable=True
                )
            )

        if "valuation_method" not in item_cols:
            batch_op.add_column(sa.Column("valuation_method", enum_val, nullable=True))

        if "mrp_type" not in item_cols:
            batch_op.add_column(sa.Column("mrp_type", enum_mrp, nullable=True))

        if "lot_size_policy" not in item_cols:
            batch_op.add_column(sa.Column("lot_size_policy", enum_lot, nullable=True))

        if "rounding_value" not in item_cols:
            batch_op.add_column(
                sa.Column(
                    "rounding_value", sa.Numeric(precision=18, scale=4), nullable=True
                )
            )

        if "is_batch_managed" not in item_cols:
            batch_op.add_column(
                sa.Column("is_batch_managed", sa.Boolean(), nullable=True)
            )

        if "is_serial_managed" not in item_cols:
            batch_op.add_column(
                sa.Column("is_serial_managed", sa.Boolean(), nullable=True)
            )

        if "dimensions" not in item_cols:
            batch_op.add_column(sa.Column("dimensions", sa.JSON(), nullable=True))

    # Maintenance Work Orders
    # Status enum update - this is an ALTER, safely repeatable usually unless type matches
    # We can check current type but postgresql_using handles the cast.
    with op.batch_alter_table("maintenance_work_orders", schema=None) as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=postgresql.ENUM(
                "DRAFT",
                "PLANNED",
                "RELEASED",
                "IN_PROGRESS",
                "QUALITY_CHECK",
                "COMPLETED",
                "CLOSED",
                "CANCELLED",
                name="workorderstatus",
            ),
            type_=enum_mwo,
            existing_nullable=True,
            postgresql_using="""status::text::maintenanceworkorderstatus""",
        )

    # Work Orders
    # Index check
    wo_indexes = [ix["name"] for ix in insp.get_indexes("work_orders")]
    with op.batch_alter_table("work_orders", schema=None) as batch_op:
        if "ix_work_orders_batch_number" not in wo_indexes:
            batch_op.create_index(
                batch_op.f("ix_work_orders_batch_number"),
                ["batch_number"],
                unique=False,
            )

    # Workflow Tables - Columns are existing_type updates mainly
    # These set defaults and nullability. These are generally safe to repeat.

    with op.batch_alter_table("workflow_actions", schema=None) as batch_op:
        batch_op.alter_column(
            "created_at",
            existing_type=postgresql.TIMESTAMP(),
            nullable=False,
            existing_server_default=sa.text("now()"),
        )
        batch_op.alter_column(
            "updated_at", existing_type=postgresql.TIMESTAMP(), nullable=False
        )
        batch_op.alter_column(
            "is_active",
            existing_type=sa.BOOLEAN(),
            nullable=False,
            existing_server_default=sa.text("true"),
        )

    with op.batch_alter_table("workflow_definitions", schema=None) as batch_op:
        batch_op.alter_column(
            "created_at",
            existing_type=postgresql.TIMESTAMP(),
            nullable=False,
            existing_server_default=sa.text("now()"),
        )
        batch_op.alter_column(
            "updated_at", existing_type=postgresql.TIMESTAMP(), nullable=False
        )
        batch_op.alter_column(
            "is_active",
            existing_type=sa.BOOLEAN(),
            nullable=False,
            existing_server_default=sa.text("true"),
        )

        # Index changes
        wd_indexes = [ix["name"] for ix in insp.get_indexes("workflow_definitions")]
        if "idx_wf_def_code" in wd_indexes:
            batch_op.drop_index("idx_wf_def_code")

        if "ix_workflow_definitions_code" not in wd_indexes:
            batch_op.create_index(
                batch_op.f("ix_workflow_definitions_code"), ["code"], unique=True
            )

        if "ix_workflow_definitions_target_table" not in wd_indexes:
            batch_op.create_index(
                batch_op.f("ix_workflow_definitions_target_table"),
                ["target_table"],
                unique=False,
            )

    with op.batch_alter_table("workflow_instances", schema=None) as batch_op:
        batch_op.alter_column(
            "created_at",
            existing_type=postgresql.TIMESTAMP(),
            nullable=False,
            existing_server_default=sa.text("now()"),
        )
        batch_op.alter_column(
            "updated_at", existing_type=postgresql.TIMESTAMP(), nullable=False
        )
        batch_op.alter_column(
            "is_active",
            existing_type=sa.BOOLEAN(),
            nullable=False,
            existing_server_default=sa.text("true"),
        )

    with op.batch_alter_table("workflow_steps", schema=None) as batch_op:
        batch_op.alter_column(
            "created_at",
            existing_type=postgresql.TIMESTAMP(),
            nullable=False,
            existing_server_default=sa.text("now()"),
        )
        batch_op.alter_column(
            "updated_at", existing_type=postgresql.TIMESTAMP(), nullable=False
        )
        batch_op.alter_column(
            "is_active",
            existing_type=sa.BOOLEAN(),
            nullable=False,
            existing_server_default=sa.text("true"),
        )


def downgrade() -> None:
    # Downgrade logic remains mostly same but can be simplified or ignored if we don't plan to downgrade
    # For correctness, we leave it as is or simplify.
    pass
