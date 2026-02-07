"""pro_phase_updates

Revision ID: 0a404c858c12
Revises: g7h8i9j0k1l2
Create Date: 2026-01-18 12:15:45.606990

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = "0a404c858c12"
down_revision: Union[str, None] = "g7h8i9j0k1l2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def create_table_if_not_exists(table_name, *args, **kwargs):
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if not insp.has_table(table_name):
        op.create_table(table_name, *args, **kwargs)
    else:
        print(f"Table {table_name} already exists, skipping creation.")


def upgrade() -> None:
    # --- RESTORE MISSING TABLES (Legacy State) ---
    # These tables are restored here to fix a broken migration chain where they were missing.

    # 1. Sales & CRM Base
    create_table_if_not_exists(
        "price_lists",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(20), unique=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("currency", sa.String(10), default="TRY"),
        sa.Column("is_default", sa.Boolean(), default=False),
        sa.PrimaryKeyConstraint("id"),
    )

    create_table_if_not_exists(
        "customers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(20), nullable=True),  # Will be made non-null
        sa.Column("name", sa.String(200), nullable=True),
        sa.Column("company_name", sa.String(200), nullable=True),  # Will be dropped
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("website", sa.String(255), nullable=True),
        sa.Column("tax_id", sa.String(50), nullable=True),  # Will be dropped
        sa.Column("status", sa.String(20), nullable=True),  # Will be dropped
        sa.Column("sector", sa.String(100), nullable=True),  # Will be dropped
        sa.Column("price_list_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("is_active", sa.Boolean(), server_default="1"),
        sa.ForeignKeyConstraint(["price_list_id"], ["price_lists.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    create_table_if_not_exists(
        "leads",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("company_name", sa.String(200)),
        sa.Column("status", sa.String(50), default="NEW"),
        sa.Column("source", sa.String(50), default="OTHER"),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    create_table_if_not_exists(
        "opportunities",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=True),
        sa.Column("customer_id", sa.Integer(), nullable=True),
        sa.Column("expected_revenue", sa.Float(), default=0.0),
        sa.Column("stage", sa.String(50), default="NEW"),
        sa.Column("closing_date", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # 2. HR (Already restored, kept here for completeness of this patch)
    create_table_if_not_exists(
        "leaves",
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("leave_type", sa.String(50), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("days", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="1"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.ForeignKeyConstraint(["approved_by"], ["employees.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    create_table_if_not_exists(
        "attendances",
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("check_in", sa.Time(), nullable=True),
        sa.Column("check_out", sa.Time(), nullable=True),
        sa.Column("status", sa.String(20), nullable=True),
        sa.Column("work_minutes", sa.Integer(), nullable=True),
        sa.Column("overtime_minutes", sa.Integer(), server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="1"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # 3. Quality & Audits
    create_table_if_not_exists(
        "audits",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("audit_no", sa.String(20), unique=True, nullable=False),
        sa.Column("audit_type", sa.String(50), nullable=False),
        sa.Column("auditee", sa.String(200)),
        sa.Column("auditor_id", sa.Integer(), nullable=True),
        sa.Column("planned_date", sa.Date()),
        sa.Column("status", sa.String(20), default="planned"),
        sa.ForeignKeyConstraint(["auditor_id"], ["employees.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    create_table_if_not_exists(
        "inspection_templates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(20), unique=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("inspection_type", sa.String(50), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    create_table_if_not_exists(
        "inspection_criteria",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("criteria_type", sa.String(50), nullable=False),
        sa.ForeignKeyConstraint(["template_id"], ["inspection_templates.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    create_table_if_not_exists(
        "inspections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("inspection_no", sa.String(20), unique=True, nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=True),
        sa.Column("item_id", sa.Integer(), nullable=True),
        sa.Column("inspector_id", sa.Integer(), nullable=True),
        sa.Column("inspection_date", sa.Date(), default=sa.func.current_date()),
        sa.Column("status", sa.String(50), default="PENDING"),
        sa.ForeignKeyConstraint(["template_id"], ["inspection_templates.id"]),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.ForeignKeyConstraint(["inspector_id"], ["employees.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    create_table_if_not_exists(
        "inspection_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("inspection_id", sa.Integer(), nullable=False),
        sa.Column("criteria_id", sa.Integer(), nullable=False),
        sa.Column("is_passed", sa.Boolean(), default=True),
        sa.ForeignKeyConstraint(["inspection_id"], ["inspections.id"]),
        sa.ForeignKeyConstraint(["criteria_id"], ["inspection_criteria.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    create_table_if_not_exists(
        "non_conformances",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ncr_no", sa.String(20), unique=True, nullable=False),
        sa.Column("inspection_id", sa.Integer(), nullable=True),
        sa.Column("item_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(50), default="MINOR"),
        sa.Column("status", sa.String(50), default="OPEN"),
        sa.Column("reported_by", sa.Integer(), nullable=True),
        sa.Column("assigned_to", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["inspection_id"], ["inspections.id"]),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.ForeignKeyConstraint(["reported_by"], ["employees.id"]),
        sa.ForeignKeyConstraint(["assigned_to"], ["employees.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    create_table_if_not_exists(
        "customer_complaints",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("complaint_no", sa.String(20), unique=True, nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=True),
        sa.Column("complaint_date", sa.Date(), default=sa.func.current_date()),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(50), default="OPEN"),
        sa.Column("assigned_to", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["assigned_to"], ["employees.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    create_table_if_not_exists(
        "capas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("capa_no", sa.String(20), unique=True, nullable=False),
        sa.Column("capa_type", sa.String(50), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("ncr_id", sa.Integer(), nullable=True),
        sa.Column("complaint_id", sa.Integer(), nullable=True),
        sa.Column("audit_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(50), default="OPEN"),
        sa.Column("responsible_id", sa.Integer(), nullable=True),
        sa.Column("verified_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["ncr_id"], ["non_conformances.id"]),
        sa.ForeignKeyConstraint(["complaint_id"], ["customer_complaints.id"]),
        sa.ForeignKeyConstraint(["audit_id"], ["audits.id"]),
        sa.ForeignKeyConstraint(["responsible_id"], ["employees.id"]),
        sa.ForeignKeyConstraint(["verified_by"], ["employees.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # 4. Production Base (BOM & Work Orders)
    create_table_if_not_exists(
        "bill_of_materials",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), default=1),
        sa.Column("revision", sa.String(20), default="A"),
        sa.Column("status", sa.String(20), default="DRAFT"),
        sa.Column("bom_type", sa.String(20), default="STANDARD"),
        sa.Column("base_quantity", sa.Numeric(18, 4), default=1),
        sa.Column("unit_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("is_active", sa.Boolean(), server_default="1"),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # PATCH: Ensure bom_type exists if table already existed (zombie table)
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "bill_of_materials" in insp.get_table_names():
        bom_cols = [c["name"] for c in insp.get_columns("bill_of_materials")]
        if "bom_type" not in bom_cols:
            with op.batch_alter_table("bill_of_materials") as batch_op:
                batch_op.add_column(
                    sa.Column("bom_type", sa.String(20), default="STANDARD")
                )

    create_table_if_not_exists(
        "bom_lines",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("bom_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("unit_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("is_active", sa.Boolean(), server_default="1"),
        sa.ForeignKeyConstraint(
            ["bom_id"], ["bill_of_materials.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    create_table_if_not_exists(
        "bom_operations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("bom_id", sa.Integer(), nullable=False),
        sa.Column("operation_no", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("work_station_id", sa.Integer(), nullable=True),
        sa.Column("setup_time", sa.Integer(), default=0),
        sa.Column("run_time", sa.Integer(), default=0),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("is_active", sa.Boolean(), server_default="1"),
        sa.ForeignKeyConstraint(
            ["bom_id"], ["bill_of_materials.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["work_station_id"], ["work_stations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    create_table_if_not_exists(
        "bom_by_products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("bom_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("unit_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("is_active", sa.Boolean(), server_default="1"),
        sa.ForeignKeyConstraint(
            ["bom_id"], ["bill_of_materials.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    create_table_if_not_exists(
        "work_orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_no", sa.String(50), unique=True, nullable=False),
        sa.Column("status", sa.String(20), default="DRAFT"),
        sa.Column("priority", sa.String(20), default="NORMAL"),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("bom_id", sa.Integer(), nullable=False),
        sa.Column("planned_quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("completed_quantity", sa.Numeric(18, 4), default=0),
        sa.Column("unit_id", sa.Integer(), nullable=True),
        sa.Column("source_warehouse_id", sa.Integer(), nullable=True),
        sa.Column("target_warehouse_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("is_active", sa.Boolean(), server_default="1"),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.ForeignKeyConstraint(["bom_id"], ["bill_of_materials.id"]),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"]),
        sa.ForeignKeyConstraint(["source_warehouse_id"], ["warehouses.id"]),
        sa.ForeignKeyConstraint(["target_warehouse_id"], ["warehouses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # PATCH: Ensure batch_number exists in work_orders
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "work_orders" in insp.get_table_names():
        wo_cols = [c["name"] for c in insp.get_columns("work_orders")]
        if "batch_number" not in wo_cols:
            with op.batch_alter_table("work_orders") as batch_op:
                batch_op.add_column(
                    sa.Column("batch_number", sa.String(100), nullable=True)
                )
                batch_op.create_index("ix_work_orders_batch_number", ["batch_number"])

    create_table_if_not_exists(
        "work_order_lines",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("work_order_id", sa.Integer(), nullable=False),
        sa.Column("bom_line_id", sa.Integer(), nullable=True),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("required_quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("issued_quantity", sa.Numeric(18, 4), default=0),
        sa.Column("unit_id", sa.Integer(), nullable=True),
        sa.Column("warehouse_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("is_active", sa.Boolean(), server_default="1"),
        sa.ForeignKeyConstraint(
            ["work_order_id"], ["work_orders.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["bom_line_id"], ["bom_lines.id"]),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"]),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    create_table_if_not_exists(
        "work_order_operations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("work_order_id", sa.Integer(), nullable=False),
        sa.Column("bom_operation_id", sa.Integer(), nullable=True),
        sa.Column("operation_no", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("work_station_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("planned_setup_time", sa.Integer(), default=0),
        sa.Column("planned_run_time", sa.Integer(), default=0),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("is_active", sa.Boolean(), server_default="1"),
        sa.ForeignKeyConstraint(
            ["work_order_id"], ["work_orders.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["bom_operation_id"], ["bom_operations.id"]),
        sa.ForeignKeyConstraint(["work_station_id"], ["work_stations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    create_table_if_not_exists(
        "work_order_operation_personnel",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("operation_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("employee_id", sa.Integer(), nullable=True),
        sa.Column("role", sa.String(50), default="operator"),
        sa.Column("start_time", sa.DateTime(), default=sa.func.now()),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), default=0),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("is_active", sa.Boolean(), server_default="1"),
        sa.ForeignKeyConstraint(
            ["operation_id"], ["work_order_operations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    create_table_if_not_exists(
        "work_order_by_products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("work_order_id", sa.Integer(), nullable=False),
        sa.Column("bom_by_product_id", sa.Integer(), nullable=True),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("planned_quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("is_active", sa.Boolean(), server_default="1"),
        sa.ForeignKeyConstraint(
            ["work_order_id"], ["work_orders.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["bom_by_product_id"], ["bom_by_products.id"]),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ### commands auto generated by Alembic - please adjust! ###
    op.execute(
        """
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'downtimereason') THEN
            CREATE TYPE downtimereason AS ENUM ('BREAKDOWN', 'SETUP', 'MATERIAL_WAIT', 'OP_ABSENCE', 'POWER_FAILURE', 'MEAL_BREAK', 'QUALITY_ISSUE', 'OTHER');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'locationtype') THEN
            CREATE TYPE locationtype AS ENUM ('NORMAL', 'QUARANTINE', 'SCRAP', 'TRANSIT');
        END IF;
        
        -- HR Enums
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'attendancestatus') THEN
            CREATE TYPE attendancestatus AS ENUM ('PRESENT', 'ABSENT', 'LATE', 'EARLY_LEAVE', 'ON_LEAVE', 'HOLIDAY');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'leavetype') THEN
            CREATE TYPE leavetype AS ENUM ('ANNUAL', 'SICK', 'MATERNITY', 'PATERNITY', 'MARRIAGE', 'BEREAVEMENT', 'UNPAID', 'OTHER');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'leavestatus') THEN
            CREATE TYPE leavestatus AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'gender') THEN
            CREATE TYPE gender AS ENUM ('MALE', 'FEMALE', 'OTHER');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'employmenttype') THEN
            CREATE TYPE employmenttype AS ENUM ('FULL_TIME', 'PART_TIME', 'CONTRACT', 'INTERN', 'TEMPORARY');
        END IF;

        -- Sales Enums
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'currency') THEN
            CREATE TYPE currency AS ENUM ('TRY', 'USD', 'EUR', 'GBP');
        END IF;

        -- Quality Enums
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'audittype') THEN
            CREATE TYPE audittype AS ENUM ('INTERNAL', 'EXTERNAL', 'SUPPLIER');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'inspectiontype') THEN
            CREATE TYPE inspectiontype AS ENUM ('INCOMING', 'IN_PROCESS', 'FINAL', 'PERIODIC');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'criteriatype') THEN
            CREATE TYPE criteriatype AS ENUM ('VISUAL', 'MEASUREMENT', 'FUNCTIONAL', 'DOCUMENT');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'inspectionstatus') THEN
            CREATE TYPE inspectionstatus AS ENUM ('PENDING', 'PASSED', 'FAILED', 'CONDITIONAL');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ncrseverity') THEN
            CREATE TYPE ncrseverity AS ENUM ('MINOR', 'MAJOR', 'CRITICAL');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ncrdisposition') THEN
            CREATE TYPE ncrdisposition AS ENUM ('REWORK', 'SCRAP', 'USE_AS_IS', 'RETURN');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ncrstatus') THEN
            CREATE TYPE ncrstatus AS ENUM ('OPEN', 'ANALYSIS', 'ACTION', 'VERIFICATION', 'CLOSED');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'complaintcategory') THEN
            CREATE TYPE complaintcategory AS ENUM ('QUALITY', 'DELIVERY', 'SERVICE', 'DOCUMENTATION', 'OTHER');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'complaintstatus') THEN
            CREATE TYPE complaintstatus AS ENUM ('OPEN', 'INVESTIGATION', 'RESOLUTION', 'CLOSED');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'capatype') THEN
            CREATE TYPE capatype AS ENUM ('CORRECTIVE', 'PREVENTIVE');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'capasource') THEN
            CREATE TYPE capasource AS ENUM ('NCR', 'AUDIT', 'CUSTOMER_COMPLAINT', 'INTERNAL');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'capastatus') THEN
            CREATE TYPE capastatus AS ENUM ('OPEN', 'IN_PROGRESS', 'VERIFICATION', 'CLOSED');
        END IF;

    END
    $$;
    """
    )
    create_table_if_not_exists(  # Modified to check first
        "payrolls",
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("period_year", sa.Integer(), nullable=False),
        sa.Column("period_month", sa.Integer(), nullable=False),
        sa.Column("base_salary", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("overtime_pay", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("bonus", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("deductions", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("net_salary", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("is_paid", sa.Boolean(), nullable=True),
        sa.Column("paid_date", sa.Date(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employees.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Use raw SQL for indexes to be safe
    op.execute("CREATE INDEX IF NOT EXISTS idx_payroll_emp ON payrolls (employee_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_payroll_period ON payrolls (period_year, period_month)"
    )

    create_table_if_not_exists(  # Modified to check first
        "production_downtimes",
        sa.Column("work_order_id", sa.Integer(), nullable=False),
        sa.Column("operation_id", sa.Integer(), nullable=True),
        sa.Column("work_station_id", sa.Integer(), nullable=False),
        sa.Column(
            "reason_code",
            postgresql.ENUM(
                "BREAKDOWN",
                "SETUP",
                "MATERIAL_WAIT",
                "OP_ABSENCE",
                "POWER_FAILURE",
                "MEAL_BREAK",
                "QUALITY_ISSUE",
                "OTHER",
                name="downtimereason",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("operator_id", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["operation_id"],
            ["work_order_operations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["operator_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["work_order_id"], ["work_orders.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["work_station_id"],
            ["work_stations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # Safe indices for production_downtimes
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_downtime_date ON production_downtimes (start_time)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_downtime_station ON production_downtimes (work_station_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_downtime_wo ON production_downtimes (work_order_id)"
    )

    op.execute(
        "ALTER TABLE account_transactions ADD COLUMN IF NOT EXISTS purchase_invoice_id INTEGER REFERENCES purchase_invoices(id)"
    )
    op.execute(
        "ALTER TABLE account_transactions ADD COLUMN IF NOT EXISTS journal_entry_id INTEGER REFERENCES journal_entries(id)"
    )

    op.execute("ALTER TABLE attendances ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TABLE employees ALTER COLUMN employment_type DROP DEFAULT")
    op.execute("ALTER TABLE leaves ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TABLE purchase_invoices ALTER COLUMN currency DROP DEFAULT")

    with op.batch_alter_table("attendances", schema=None) as batch_op:
        batch_op.alter_column(
            "check_in",
            existing_type=postgresql.TIME(),
            type_=sa.DateTime(),
            existing_nullable=True,
            postgresql_using="date + check_in",
        )
        batch_op.alter_column(
            "check_out",
            existing_type=postgresql.TIME(),
            type_=sa.DateTime(),
            existing_nullable=True,
            postgresql_using="date + check_out",
        )
        batch_op.alter_column(
            "status",
            existing_type=sa.VARCHAR(length=20),
            type_=sa.Enum(
                "PRESENT",
                "ABSENT",
                "LATE",
                "EARLY_LEAVE",
                "ON_LEAVE",
                "HOLIDAY",
                name="attendancestatus",
                create_type=False,
            ),
            existing_nullable=True,
            server_default=sa.text("'PRESENT'"),
            postgresql_using="UPPER(status)::attendancestatus",
        )
        batch_op.alter_column(
            "created_at",
            existing_type=postgresql.TIMESTAMP(),
            nullable=False,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),  # type: ignore[arg-type]
        )
        batch_op.alter_column(
            "updated_at",
            existing_type=postgresql.TIMESTAMP(),
            nullable=False,
            existing_server_default=sa.text("now()"),  # type: ignore[arg-type]
        )
        batch_op.alter_column(
            "is_active",
            existing_type=sa.BOOLEAN(),
            nullable=False,
            existing_server_default=sa.text("true"),  # type: ignore[arg-type]
        )

    # Safe indices
    op.execute("CREATE INDEX IF NOT EXISTS idx_att_date ON attendances (date)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_att_emp ON attendances (employee_id)")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_att_emp_date ON attendances (employee_id, date)"
    )

    with op.batch_alter_table("audits", schema=None) as batch_op:
        pass  # Aready restored

    with op.batch_alter_table("capas", schema=None) as batch_op:
        pass  # Already restored

    with op.batch_alter_table("customer_complaints", schema=None) as batch_op:
        pass  # Already restored

    op.execute(
        "ALTER TABLE customers DROP CONSTRAINT IF EXISTS customers_company_name_key"
    )
    op.execute("DROP INDEX IF EXISTS idx_customers_code")
    with op.batch_alter_table("customers", schema=None) as batch_op:
        batch_op.alter_column(
            "code", existing_type=sa.VARCHAR(length=20), nullable=False
        )
        batch_op.alter_column(
            "name", existing_type=sa.VARCHAR(length=200), nullable=False
        )
        batch_op.alter_column(
            "phone",
            existing_type=sa.VARCHAR(length=50),
            type_=sa.String(length=30),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "website",
            existing_type=sa.VARCHAR(length=255),
            type_=sa.String(length=200),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "created_at",
            existing_type=postgresql.TIMESTAMP(),
            nullable=False,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),  # type: ignore[arg-type]
        )
        batch_op.alter_column(
            "updated_at",
            existing_type=postgresql.TIMESTAMP(),
            nullable=False,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),  # type: ignore[arg-type]
        )
        batch_op.alter_column("is_active", existing_type=sa.BOOLEAN(), nullable=False)
        # indices/constraints handled safely

    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_customers_code ON customers (code)"
    )
    op.execute("ALTER TABLE customers DROP COLUMN IF EXISTS tax_id")
    op.execute("ALTER TABLE customers DROP COLUMN IF EXISTS status")
    op.execute("ALTER TABLE customers DROP COLUMN IF EXISTS company_name")
    op.execute("ALTER TABLE customers DROP COLUMN IF EXISTS sector")

    op.execute("DROP INDEX IF EXISTS idx_dashboard_widget_code")
    with op.batch_alter_table("dashboard_widgets", schema=None) as batch_op:
        batch_op.alter_column(
            "default_width",
            existing_type=sa.INTEGER(),
            nullable=True,
            existing_server_default=sa.text("1"),  # type: ignore[arg-type]
        )
        batch_op.alter_column(
            "default_height",
            existing_type=sa.INTEGER(),
            nullable=True,
            existing_server_default=sa.text("1"),  # type: ignore[arg-type]
        )
        batch_op.alter_column(
            "min_width",
            existing_type=sa.INTEGER(),
            nullable=True,
            existing_server_default=sa.text("1"),  # type: ignore[arg-type]
        )
        batch_op.alter_column(
            "min_height",
            existing_type=sa.INTEGER(),
            nullable=True,
            existing_server_default=sa.text("1"),  # type: ignore[arg-type]
        )
        batch_op.alter_column(
            "max_width",
            existing_type=sa.INTEGER(),
            nullable=True,
            existing_server_default=sa.text("2"),  # type: ignore[arg-type]
        )
        batch_op.alter_column(
            "max_height",
            existing_type=sa.INTEGER(),
            nullable=True,
            existing_server_default=sa.text("2"),  # type: ignore[arg-type]
        )
        batch_op.alter_column(
            "sort_order",
            existing_type=sa.INTEGER(),
            nullable=True,
            existing_server_default=sa.text("0"),  # type: ignore[arg-type]
        )
        batch_op.alter_column(
            "is_system",
            existing_type=sa.BOOLEAN(),
            nullable=True,
            existing_server_default=sa.text("false"),  # type: ignore[arg-type]
        )

    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_dashboard_widgets_code ON dashboard_widgets (code)"
    )

    with op.batch_alter_table("delivery_notes", schema=None) as batch_op:
        batch_op.create_foreign_key(None, "customers", ["customer_id"], ["id"])

    op.execute("ALTER TABLE departments DROP CONSTRAINT IF EXISTS departments_code_key")
    with op.batch_alter_table("departments", schema=None) as batch_op:
        batch_op.alter_column(
            "created_at",
            existing_type=postgresql.TIMESTAMP(),
            nullable=False,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),  # type: ignore[arg-type]
        )
        batch_op.alter_column(
            "updated_at",
            existing_type=postgresql.TIMESTAMP(),
            nullable=False,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),  # type: ignore[arg-type]
        )
        batch_op.alter_column(
            "is_active",
            existing_type=sa.BOOLEAN(),
            nullable=False,
            existing_server_default=sa.text("true"),  # type: ignore[arg-type]
        )
        # Handled
        batch_op.create_foreign_key(
            None, "employees", ["manager_id"], ["id"], use_alter=True
        )
        batch_op.create_foreign_key(None, "departments", ["parent_id"], ["id"])

    op.execute("CREATE INDEX IF NOT EXISTS idx_dept_code ON departments (code)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_dept_parent ON departments (parent_id)")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_departments_code ON departments (code)"
    )

    op.execute(
        "ALTER TABLE employees DROP CONSTRAINT IF EXISTS employees_employee_no_key"
    )
    with op.batch_alter_table("employees", schema=None) as batch_op:
        batch_op.alter_column(
            "gender",
            existing_type=sa.VARCHAR(length=20),
            type_=sa.Enum("MALE", "FEMALE", "OTHER", name="gender", create_type=False),
            existing_nullable=True,
            postgresql_using="UPPER(gender::text)::gender",
        )
        batch_op.alter_column(
            "hire_date",
            existing_type=sa.DATE(),
            nullable=False,
            existing_server_default=sa.text("CURRENT_DATE"),  # type: ignore[arg-type]
        )
        batch_op.alter_column(
            "employment_type",
            existing_type=sa.VARCHAR(length=20),
            type_=sa.Enum(
                "FULL_TIME",
                "PART_TIME",
                "CONTRACT",
                "INTERN",
                "TEMPORARY",
                name="employmenttype",
                create_type=False,
            ),
            existing_nullable=True,
            existing_server_default=sa.text("'full_time'::character varying"),  # type: ignore[arg-type]
            postgresql_using="UPPER(employment_type::text)::employmenttype",
        )
        batch_op.alter_column(
            "created_at",
            existing_type=postgresql.TIMESTAMP(),
            nullable=False,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),  # type: ignore[arg-type]
        )
        batch_op.alter_column(
            "updated_at",
            existing_type=postgresql.TIMESTAMP(),
            nullable=False,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),  # type: ignore[arg-type]
        )
        batch_op.alter_column(
            "is_active",
            existing_type=sa.BOOLEAN(),
            nullable=False,
            existing_server_default=sa.text("true"),  # type: ignore[arg-type]
        )
        # Handled
        batch_op.create_foreign_key(None, "employees", ["manager_id"], ["id"])
        batch_op.create_foreign_key(None, "users", ["user_id"], ["id"])

    op.execute("CREATE INDEX IF NOT EXISTS idx_emp_active ON employees (is_active)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_emp_dept ON employees (department_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_emp_name ON employees (first_name, last_name)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_emp_no ON employees (employee_no)")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_employees_employee_no ON employees (employee_no)"
    )

    with op.batch_alter_table("equipment_downtimes", schema=None) as batch_op:
        batch_op.alter_column(
            "created_at", existing_type=postgresql.TIMESTAMP(), nullable=False
        )
        batch_op.alter_column(
            "updated_at", existing_type=postgresql.TIMESTAMP(), nullable=False
        )
        batch_op.alter_column(
            "is_active",
            existing_type=sa.BOOLEAN(),
            nullable=False,
            existing_server_default=sa.text("true"),  # type: ignore[arg-type]
        )

    with op.batch_alter_table("equipment_spare_parts", schema=None) as batch_op:
        batch_op.alter_column(
            "created_at", existing_type=postgresql.TIMESTAMP(), nullable=False
        )
        batch_op.alter_column(
            "updated_at", existing_type=postgresql.TIMESTAMP(), nullable=False
        )
        batch_op.alter_column(
            "is_active",
            existing_type=sa.BOOLEAN(),
            nullable=False,
            existing_server_default=sa.text("true"),  # type: ignore[arg-type]
        )

    with op.batch_alter_table("equipments", schema=None) as batch_op:
        pass
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_equipment_criticality ON equipments (criticality)"
    )

    with op.batch_alter_table("inspections", schema=None) as batch_op:
        batch_op.create_foreign_key(None, "employees", ["inspector_id"], ["id"])

    with op.batch_alter_table("invoices", schema=None) as batch_op:
        batch_op.create_foreign_key(None, "customers", ["customer_id"], ["id"])

    op.execute("ALTER TABLE items ADD COLUMN IF NOT EXISTS is_qc_required BOOLEAN")

    with op.batch_alter_table("leaves", schema=None) as batch_op:
        batch_op.alter_column(
            "leave_type",
            existing_type=sa.VARCHAR(length=50),
            type_=sa.Enum(
                "ANNUAL",
                "SICK",
                "MATERNITY",
                "PATERNITY",
                "MARRIAGE",
                "BEREAVEMENT",
                "UNPAID",
                "OTHER",
                name="leavetype",
                create_type=False,
            ),
            existing_nullable=False,
            postgresql_using="UPPER(leave_type)::leavetype",
        )
        batch_op.alter_column(
            "days",
            existing_type=sa.INTEGER(),
            type_=sa.Numeric(precision=5, scale=1),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "status",
            existing_type=sa.VARCHAR(length=20),
            type_=sa.Enum(
                "PENDING",
                "APPROVED",
                "REJECTED",
                "CANCELLED",
                name="leavestatus",
                create_type=False,
            ),
            existing_nullable=True,
            existing_server_default=sa.text("'pending'::character varying"),  # type: ignore[arg-type]
            postgresql_using="UPPER(status)::leavestatus",
        )
        batch_op.alter_column(
            "created_at",
            existing_type=postgresql.TIMESTAMP(),
            nullable=False,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),  # type: ignore[arg-type]
        )
        batch_op.alter_column(
            "updated_at",
            existing_type=postgresql.TIMESTAMP(),
            nullable=False,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),  # type: ignore[arg-type]
        )
        batch_op.alter_column(
            "is_active",
            existing_type=sa.BOOLEAN(),
            nullable=False,
            existing_server_default=sa.text("true"),  # type: ignore[arg-type]
        )
        # Safe indexes
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_leave_dates ON leaves (start_date, end_date)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_leave_emp ON leaves (employee_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_leave_status ON leaves (status)")

    with op.batch_alter_table("maintenance_checklist_items", schema=None) as batch_op:
        batch_op.alter_column(
            "created_at", existing_type=postgresql.TIMESTAMP(), nullable=False
        )
        batch_op.alter_column(
            "updated_at", existing_type=postgresql.TIMESTAMP(), nullable=False
        )
        batch_op.alter_column(
            "is_active",
            existing_type=sa.BOOLEAN(),
            nullable=False,
            existing_server_default=sa.text("true"),  # type: ignore[arg-type]
        )

    with op.batch_alter_table("maintenance_checklists", schema=None) as batch_op:
        batch_op.alter_column(
            "created_at", existing_type=postgresql.TIMESTAMP(), nullable=False
        )
        batch_op.alter_column(
            "updated_at", existing_type=postgresql.TIMESTAMP(), nullable=False
        )

    with op.batch_alter_table("maintenance_plans", schema=None) as batch_op:
        pass
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_plan_equipment ON maintenance_plans (equipment_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_plan_next_date ON maintenance_plans (next_maintenance_date)"
    )

    with op.batch_alter_table(
        "maintenance_request_attachments", schema=None
    ) as batch_op:
        batch_op.alter_column(
            "created_at", existing_type=postgresql.TIMESTAMP(), nullable=False
        )
        batch_op.alter_column(
            "updated_at", existing_type=postgresql.TIMESTAMP(), nullable=False
        )
        batch_op.alter_column(
            "is_active",
            existing_type=sa.BOOLEAN(),
            nullable=False,
            existing_server_default=sa.text("true"),  # type: ignore[arg-type]
        )

    with op.batch_alter_table("maintenance_requests", schema=None) as batch_op:
        pass
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_maint_req_date ON maintenance_requests (request_date)"
    )

    with op.batch_alter_table("maintenance_work_orders", schema=None) as batch_op:
        pass
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_mwo_assigned ON maintenance_work_orders (assigned_to_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_mwo_equipment ON maintenance_work_orders (equipment_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_mwo_status ON maintenance_work_orders (status)"
    )

    with op.batch_alter_table("non_conformances", schema=None) as batch_op:
        batch_op.create_foreign_key(None, "employees", ["assigned_to"], ["id"])
        batch_op.create_foreign_key(None, "employees", ["reported_by"], ["id"])

    op.execute("ALTER TABLE positions DROP CONSTRAINT IF EXISTS positions_code_key")
    with op.batch_alter_table("positions", schema=None) as batch_op:
        batch_op.alter_column(
            "created_at",
            existing_type=postgresql.TIMESTAMP(),
            nullable=False,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),  # type: ignore[arg-type]
        )
        batch_op.alter_column(
            "updated_at",
            existing_type=postgresql.TIMESTAMP(),
            nullable=False,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),  # type: ignore[arg-type]
        )
        batch_op.alter_column(
            "is_active",
            existing_type=sa.BOOLEAN(),
            nullable=False,
            existing_server_default=sa.text("true"),  # type: ignore[arg-type]
        )

    op.execute("CREATE INDEX IF NOT EXISTS idx_pos_code ON positions (code)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_pos_dept ON positions (department_id)")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_positions_code ON positions (code)"
    )

    op.execute("DROP INDEX IF EXISTS idx_purchase_invoice_item_invoice")
    with op.batch_alter_table("purchase_invoice_items", schema=None) as batch_op:
        batch_op.alter_column(
            "created_at",
            existing_type=postgresql.TIMESTAMP(),
            nullable=False,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),  # type: ignore[arg-type]
        )
        batch_op.alter_column(
            "updated_at", existing_type=postgresql.TIMESTAMP(), nullable=False
        )
        batch_op.alter_column(
            "is_active",
            existing_type=sa.BOOLEAN(),
            nullable=False,
            existing_server_default=sa.text("true"),  # type: ignore[arg-type]
        )
        # batch_op.drop_index("idx_purchase_invoice_item_invoice") # Handled

    op.execute("DROP INDEX IF EXISTS idx_purchase_invoice_date")
    op.execute("DROP INDEX IF EXISTS idx_purchase_invoice_no")
    op.execute("DROP INDEX IF EXISTS idx_purchase_invoice_supplier")
    with op.batch_alter_table("purchase_invoices", schema=None) as batch_op:
        batch_op.alter_column(
            "currency",
            existing_type=sa.VARCHAR(length=10),
            type_=sa.Enum(
                "TRY", "USD", "EUR", "GBP", name="currency", create_type=False
            ),
            existing_nullable=True,
            existing_server_default=sa.text("'TRY'::character varying"),  # type: ignore[arg-type]
            postgresql_using="UPPER(currency)::currency",
        )
        batch_op.alter_column(
            "created_at",
            existing_type=postgresql.TIMESTAMP(),
            nullable=False,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),  # type: ignore[arg-type]
        )
        batch_op.alter_column(
            "updated_at", existing_type=postgresql.TIMESTAMP(), nullable=False
        )
        batch_op.alter_column(
            "is_active",
            existing_type=sa.BOOLEAN(),
            nullable=False,
            existing_server_default=sa.text("true"),  # type: ignore[arg-type]
        )
        # indexes handled above
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_purchase_invoices_invoice_no ON purchase_invoices (invoice_no)"
    )

    with op.batch_alter_table("receipts", schema=None) as batch_op:
        batch_op.create_foreign_key(None, "customers", ["customer_id"], ["id"])

    op.execute("DROP INDEX IF EXISTS idx_rotation_pattern_code")
    with op.batch_alter_table("rotation_patterns", schema=None) as batch_op:
        batch_op.alter_column(
            "created_at",
            existing_type=postgresql.TIMESTAMP(),
            nullable=False,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),  # type: ignore[arg-type]
        )
        batch_op.alter_column(
            "updated_at", existing_type=postgresql.TIMESTAMP(), nullable=False
        )
        batch_op.alter_column(
            "is_active",
            existing_type=sa.BOOLEAN(),
            nullable=False,
            existing_server_default=sa.text("true"),  # type: ignore[arg-type]
        )

    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_rotation_pattern_code ON rotation_patterns (code)"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_rotation_patterns_code ON rotation_patterns (code)"
    )

    with op.batch_alter_table("rotation_schedules", schema=None) as batch_op:
        batch_op.alter_column(
            "created_at",
            existing_type=postgresql.TIMESTAMP(),
            nullable=False,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),  # type: ignore[arg-type]
        )
        batch_op.alter_column(
            "updated_at", existing_type=postgresql.TIMESTAMP(), nullable=False
        )
        batch_op.alter_column(
            "is_active",
            existing_type=sa.BOOLEAN(),
            nullable=False,
            existing_server_default=sa.text("true"),  # type: ignore[arg-type]
        )

    with op.batch_alter_table("sales_orders", schema=None) as batch_op:
        batch_op.create_foreign_key(None, "customers", ["customer_id"], ["id"])

    with op.batch_alter_table("sales_quotes", schema=None) as batch_op:
        batch_op.add_column(sa.Column("opportunity_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, "customers", ["customer_id"], ["id"])
        batch_op.create_foreign_key(None, "opportunities", ["opportunity_id"], ["id"])

    op.execute("DROP INDEX IF EXISTS idx_shift_team_code")
    with op.batch_alter_table("shift_teams", schema=None) as batch_op:
        batch_op.alter_column(
            "created_at",
            existing_type=postgresql.TIMESTAMP(),
            nullable=False,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),  # type: ignore[arg-type]
        )
        batch_op.alter_column(
            "updated_at", existing_type=postgresql.TIMESTAMP(), nullable=False
        )
        batch_op.alter_column(
            "is_active",
            existing_type=sa.BOOLEAN(),
            nullable=False,
            existing_server_default=sa.text("true"),  # type: ignore[arg-type]
        )
        # index handled
    op.execute("CREATE INDEX IF NOT EXISTS idx_shift_team_code ON shift_teams (code)")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_shift_teams_code ON shift_teams (code)"
    )

    op.execute("DROP INDEX IF EXISTS idx_session_refresh")
    op.execute("DROP INDEX IF EXISTS idx_session_token")
    with op.batch_alter_table("user_sessions", schema=None) as batch_op:
        batch_op.alter_column("is_revoked", existing_type=sa.BOOLEAN(), nullable=True)
        # indexes handled
        batch_op.create_unique_constraint(None, ["refresh_token"])

    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_session_token ON user_sessions (session_token)"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_user_sessions_session_token ON user_sessions (session_token)"
    )

    op.execute(
        "ALTER TABLE warehouse_locations ADD COLUMN IF NOT EXISTS location_type locationtype NOT NULL DEFAULT 'NORMAL'"
    )

    with op.batch_alter_table("work_order_attachments", schema=None) as batch_op:
        batch_op.alter_column(
            "created_at", existing_type=postgresql.TIMESTAMP(), nullable=False
        )
        batch_op.alter_column(
            "updated_at", existing_type=postgresql.TIMESTAMP(), nullable=False
        )
        batch_op.alter_column(
            "is_active",
            existing_type=sa.BOOLEAN(),
            nullable=False,
            existing_server_default=sa.text("true"),  # type: ignore[arg-type]
        )

    with op.batch_alter_table("work_order_checklist_results", schema=None) as batch_op:
        batch_op.alter_column(
            "created_at", existing_type=postgresql.TIMESTAMP(), nullable=False
        )
        batch_op.alter_column(
            "updated_at", existing_type=postgresql.TIMESTAMP(), nullable=False
        )
        batch_op.alter_column(
            "is_active",
            existing_type=sa.BOOLEAN(),
            nullable=False,
            existing_server_default=sa.text("true"),  # type: ignore[arg-type]
        )

    with op.batch_alter_table(
        "work_order_operation_personnel", schema=None
    ) as batch_op:
        batch_op.alter_column(
            "created_at",
            existing_type=postgresql.TIMESTAMP(),
            nullable=False,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),  # type: ignore[arg-type]
        )
        batch_op.alter_column(
            "updated_at",
            existing_type=postgresql.TIMESTAMP(),
            nullable=False,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),  # type: ignore[arg-type]
        )
        batch_op.alter_column(
            "is_active",
            existing_type=sa.BOOLEAN(),
            nullable=False,
            existing_server_default=sa.text("true"),  # type: ignore[arg-type]
        )

    # ### end Alembic commands ###


def downgrade() -> None:
    pass
