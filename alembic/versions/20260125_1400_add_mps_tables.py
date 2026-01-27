"""Add MPS (Master Production Scheduling) tables

Revision ID: 1d12a4ad122d
Revises: 9f6a91342f90
Create Date: 2026-01-25 14:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "1d12a4ad122d"
down_revision: Union[str, None] = "9f6a91342f90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ProductionPlanStatus enum
    productionplanstatus = postgresql.ENUM(
        "draft", "approved", "released", "completed", "cancelled",
        name="productionplanstatus",
        create_type=False,
    )
    productionplanstatus.create(op.get_bind(), checkfirst=True)

    # Create production_plans table
    op.create_table(
        "production_plans",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        # Plan bilgileri
        sa.Column("plan_no", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        # Planlama dönemi
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        # Durum
        sa.Column(
            "status",
            postgresql.ENUM(
                "draft", "approved", "released", "completed", "cancelled",
                name="productionplanstatus",
                create_type=False,
            ),
            nullable=False,
            server_default="draft",
        ),
        # Onay
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        # Notlar
        sa.Column("notes", sa.Text(), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
    )

    # Create indexes for production_plans
    with op.batch_alter_table("production_plans", schema=None) as batch_op:
        batch_op.create_index("idx_pp_dates", ["period_start", "period_end"], unique=False)
        batch_op.create_index("idx_pp_status", ["status"], unique=False)
        batch_op.create_index(batch_op.f("ix_production_plans_plan_no"), ["plan_no"], unique=True)

    # Create production_plan_lines table
    op.create_table(
        "production_plan_lines",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        # Plan bağlantısı
        sa.Column("plan_id", sa.Integer(), nullable=False),
        # Ürün
        sa.Column("item_id", sa.Integer(), nullable=False),
        # Talep kaynağı
        sa.Column("sales_order_id", sa.Integer(), nullable=True),
        sa.Column("sales_order_item_id", sa.Integer(), nullable=True),
        sa.Column("forecast_id", sa.Integer(), nullable=True),
        # Miktarlar
        sa.Column("demand_quantity", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("planned_quantity", sa.Numeric(precision=18, scale=4), nullable=False),
        # Tarihler
        sa.Column("demand_date", sa.Date(), nullable=False),
        sa.Column("planned_start", sa.DateTime(), nullable=True),
        sa.Column("planned_end", sa.DateTime(), nullable=True),
        # Öncelik
        sa.Column("priority_score", sa.Numeric(precision=5, scale=2), nullable=True, server_default="50.00"),
        # Üretilen iş emri
        sa.Column("work_order_id", sa.Integer(), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["plan_id"], ["production_plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.ForeignKeyConstraint(["sales_order_id"], ["sales_orders.id"]),
        sa.ForeignKeyConstraint(["sales_order_item_id"], ["sales_order_items.id"]),
        sa.ForeignKeyConstraint(["work_order_id"], ["work_orders.id"]),
    )

    # Create indexes for production_plan_lines
    with op.batch_alter_table("production_plan_lines", schema=None) as batch_op:
        batch_op.create_index("idx_ppl_plan", ["plan_id"], unique=False)
        batch_op.create_index("idx_ppl_item", ["item_id"], unique=False)
        batch_op.create_index("idx_ppl_demand_date", ["demand_date"], unique=False)
        batch_op.create_index("idx_ppl_priority", ["priority_score"], unique=False)

    # Add cascade tracking columns to work_order_operations
    with op.batch_alter_table("work_order_operations", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("is_locked", sa.Boolean(), nullable=True, server_default="false")
        )
        batch_op.add_column(
            sa.Column("cascade_group_id", sa.String(length=50), nullable=True)
        )


def downgrade() -> None:
    # Remove cascade tracking columns from work_order_operations
    with op.batch_alter_table("work_order_operations", schema=None) as batch_op:
        batch_op.drop_column("cascade_group_id")
        batch_op.drop_column("is_locked")

    # Drop production_plan_lines table
    op.drop_table("production_plan_lines")

    # Drop production_plans table
    op.drop_table("production_plans")

    # Drop ProductionPlanStatus enum
    op.execute("DROP TYPE IF EXISTS productionplanstatus")
