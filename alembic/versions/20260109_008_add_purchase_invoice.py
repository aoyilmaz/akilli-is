"""Add purchase invoice tables

Revision ID: 008_add_purchase_invoice
Revises: 007_add_finance_module
Create Date: 2026-01-09

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "008_add_purchase_invoice"
down_revision = "007_add_finance_module"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PurchaseInvoice tablosu
    op.create_table(
        "purchase_invoices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("invoice_no", sa.String(50), nullable=False),
        sa.Column("invoice_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("supplier_invoice_no", sa.String(50), nullable=True),
        sa.Column("supplier_invoice_date", sa.Date(), nullable=True),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("purchase_order_id", sa.Integer(), nullable=True),
        sa.Column("goods_receipt_id", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "received",
                "partial",
                "paid",
                "overdue",
                "cancelled",
                name="purchaseinvoicestatus",
            ),
            nullable=True,
            server_default="draft",
        ),
        sa.Column(
            "currency",
            sa.String(10),
            nullable=True,
            server_default="TRY",
        ),
        sa.Column(
            "exchange_rate", sa.Numeric(10, 4), nullable=True, server_default="1"
        ),
        sa.Column("subtotal", sa.Numeric(15, 2), nullable=True, server_default="0"),
        sa.Column(
            "discount_amount", sa.Numeric(15, 2), nullable=True, server_default="0"
        ),
        sa.Column("tax_amount", sa.Numeric(15, 2), nullable=True, server_default="0"),
        sa.Column("total", sa.Numeric(15, 2), nullable=True, server_default="0"),
        sa.Column("paid_amount", sa.Numeric(15, 2), nullable=True, server_default="0"),
        sa.Column("balance", sa.Numeric(15, 2), nullable=True, server_default="0"),
        sa.Column("paid_date", sa.Date(), nullable=True),
        sa.Column("payment_method", sa.String(50), nullable=True),
        sa.Column("payment_notes", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"]),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"]),
        sa.ForeignKeyConstraint(["goods_receipt_id"], ["goods_receipts.id"]),
    )
    op.create_index(
        "idx_purchase_invoice_no", "purchase_invoices", ["invoice_no"], unique=True
    )
    op.create_index(
        "idx_purchase_invoice_supplier", "purchase_invoices", ["supplier_id"]
    )
    op.create_index("idx_purchase_invoice_date", "purchase_invoices", ["invoice_date"])

    # PurchaseInvoiceItem tablosu
    op.create_table(
        "purchase_invoice_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=True),
        sa.Column("quantity", sa.Numeric(15, 4), nullable=False),
        sa.Column("unit_id", sa.Integer(), nullable=True),
        sa.Column("unit_price", sa.Numeric(15, 4), nullable=False, server_default="0"),
        sa.Column("discount_rate", sa.Numeric(5, 2), nullable=True, server_default="0"),
        sa.Column("tax_rate", sa.Numeric(5, 2), nullable=True, server_default="18"),
        sa.Column("line_total", sa.Numeric(15, 2), nullable=True, server_default="0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["invoice_id"], ["purchase_invoices.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"]),
    )
    op.create_index(
        "idx_purchase_invoice_item_invoice", "purchase_invoice_items", ["invoice_id"]
    )


def downgrade() -> None:
    op.drop_table("purchase_invoice_items")
    op.drop_table("purchase_invoices")
    op.execute("DROP TYPE IF EXISTS purchaseinvoicestatus")
