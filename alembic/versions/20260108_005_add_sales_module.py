"""Add sales module tables

Revision ID: 005_add_sales_module
Revises: 004_add_qc_columns
Create Date: 2026-01-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005_add_sales_module'
down_revision: Union[str, None] = '004_add_qc_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Satış modülü tablolarını oluştur:
    - customers: Müşteriler
    - sales_quotes / sales_quote_items: Satış teklifleri
    - sales_orders / sales_order_items: Satış siparişleri
    - delivery_notes / delivery_note_items: Teslimat irsaliyeleri
    - invoices / invoice_items: Faturalar
    """

    # Enum türlerini oluştur
    salesquotestatus = postgresql.ENUM(
        'draft', 'sent', 'accepted', 'rejected', 'ordered', 'expired', 'cancelled',
        name='salesquotestatus', create_type=False
    )
    salesorderstatus = postgresql.ENUM(
        'draft', 'confirmed', 'partial', 'delivered', 'closed', 'cancelled',
        name='salesorderstatus', create_type=False
    )
    deliverynotestatus = postgresql.ENUM(
        'draft', 'shipped', 'delivered', 'cancelled',
        name='deliverynotestatus', create_type=False
    )
    invoicestatus = postgresql.ENUM(
        'draft', 'issued', 'partial', 'paid', 'overdue', 'cancelled',
        name='invoicestatus', create_type=False
    )
    currency_enum = postgresql.ENUM(
        'TRY', 'USD', 'EUR', 'GBP',
        name='currency_sales', create_type=False
    )

    # Enum'ları oluştur
    op.execute("CREATE TYPE salesquotestatus AS ENUM ('draft', 'sent', 'accepted', 'rejected', 'ordered', 'expired', 'cancelled')")
    op.execute("CREATE TYPE salesorderstatus AS ENUM ('draft', 'confirmed', 'partial', 'delivered', 'closed', 'cancelled')")
    op.execute("CREATE TYPE deliverynotestatus AS ENUM ('draft', 'shipped', 'delivered', 'cancelled')")
    op.execute("CREATE TYPE invoicestatus AS ENUM ('draft', 'issued', 'partial', 'paid', 'overdue', 'cancelled')")

    # 1. Customers tablosu
    op.create_table(
        'customers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),

        sa.Column('code', sa.String(20), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('short_name', sa.String(50), nullable=True),
        sa.Column('tax_number', sa.String(20), nullable=True),
        sa.Column('tax_office', sa.String(100), nullable=True),

        sa.Column('contact_person', sa.String(100), nullable=True),
        sa.Column('phone', sa.String(30), nullable=True),
        sa.Column('mobile', sa.String(30), nullable=True),
        sa.Column('fax', sa.String(30), nullable=True),
        sa.Column('email', sa.String(100), nullable=True),
        sa.Column('website', sa.String(200), nullable=True),

        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(50), nullable=True),
        sa.Column('district', sa.String(50), nullable=True),
        sa.Column('postal_code', sa.String(10), nullable=True),
        sa.Column('country', sa.String(50), server_default='Türkiye', nullable=True),

        sa.Column('payment_term_days', sa.Integer(), server_default='30', nullable=True),
        sa.Column('credit_limit', sa.Numeric(15, 2), server_default='0', nullable=True),
        sa.Column('currency', sa.String(10), server_default='TRY', nullable=True),

        sa.Column('bank_name', sa.String(100), nullable=True),
        sa.Column('bank_branch', sa.String(100), nullable=True),
        sa.Column('bank_account_no', sa.String(50), nullable=True),
        sa.Column('iban', sa.String(50), nullable=True),

        sa.Column('rating', sa.Integer(), server_default='0', nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index('idx_customer_code', 'customers', ['code'])

    # 2. Sales Quotes tablosu
    op.create_table(
        'sales_quotes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),

        sa.Column('quote_no', sa.String(20), nullable=False),
        sa.Column('quote_date', sa.Date(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('status', salesquotestatus, server_default='draft', nullable=True),
        sa.Column('valid_until', sa.Date(), nullable=True),
        sa.Column('priority', sa.Integer(), server_default='2', nullable=True),
        sa.Column('sales_rep', sa.String(100), nullable=True),

        sa.Column('currency', sa.String(10), server_default='TRY', nullable=True),
        sa.Column('exchange_rate', sa.Numeric(10, 4), server_default='1', nullable=True),
        sa.Column('subtotal', sa.Numeric(15, 2), server_default='0', nullable=True),
        sa.Column('discount_rate', sa.Numeric(5, 2), server_default='0', nullable=True),
        sa.Column('discount_amount', sa.Numeric(15, 2), server_default='0', nullable=True),
        sa.Column('tax_amount', sa.Numeric(15, 2), server_default='0', nullable=True),
        sa.Column('total', sa.Numeric(15, 2), server_default='0', nullable=True),

        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('quote_no'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'])
    )
    op.create_index('idx_sq_customer', 'sales_quotes', ['customer_id'])
    op.create_index('idx_sq_status', 'sales_quotes', ['status'])
    op.create_index('idx_sq_date', 'sales_quotes', ['quote_date'])

    # 3. Sales Quote Items tablosu
    op.create_table(
        'sales_quote_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),

        sa.Column('quote_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=True),
        sa.Column('quantity', sa.Numeric(15, 4), nullable=False),
        sa.Column('unit_id', sa.Integer(), nullable=True),
        sa.Column('unit_price', sa.Numeric(15, 4), server_default='0', nullable=True),
        sa.Column('discount_rate', sa.Numeric(5, 2), server_default='0', nullable=True),
        sa.Column('tax_rate', sa.Numeric(5, 2), server_default='18', nullable=True),
        sa.Column('line_total', sa.Numeric(15, 2), server_default='0', nullable=True),
        sa.Column('description', sa.Text(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['quote_id'], ['sales_quotes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['item_id'], ['items.id']),
        sa.ForeignKeyConstraint(['unit_id'], ['units.id'])
    )

    # 4. Sales Orders tablosu
    op.create_table(
        'sales_orders',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),

        sa.Column('order_no', sa.String(20), nullable=False),
        sa.Column('order_date', sa.Date(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('quote_id', sa.Integer(), nullable=True),
        sa.Column('status', salesorderstatus, server_default='draft', nullable=True),

        sa.Column('delivery_date', sa.Date(), nullable=True),
        sa.Column('actual_delivery_date', sa.Date(), nullable=True),

        sa.Column('currency', sa.String(10), server_default='TRY', nullable=True),
        sa.Column('exchange_rate', sa.Numeric(10, 4), server_default='1', nullable=True),
        sa.Column('subtotal', sa.Numeric(15, 2), server_default='0', nullable=True),
        sa.Column('discount_rate', sa.Numeric(5, 2), server_default='0', nullable=True),
        sa.Column('discount_amount', sa.Numeric(15, 2), server_default='0', nullable=True),
        sa.Column('tax_amount', sa.Numeric(15, 2), server_default='0', nullable=True),
        sa.Column('total', sa.Numeric(15, 2), server_default='0', nullable=True),

        sa.Column('payment_term_days', sa.Integer(), nullable=True),
        sa.Column('payment_due_date', sa.Date(), nullable=True),

        sa.Column('delivery_address', sa.Text(), nullable=True),
        sa.Column('source_warehouse_id', sa.Integer(), nullable=True),

        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('internal_notes', sa.Text(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_no'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.ForeignKeyConstraint(['quote_id'], ['sales_quotes.id']),
        sa.ForeignKeyConstraint(['source_warehouse_id'], ['warehouses.id'])
    )
    op.create_index('idx_so_customer', 'sales_orders', ['customer_id'])
    op.create_index('idx_so_status', 'sales_orders', ['status'])
    op.create_index('idx_so_date', 'sales_orders', ['order_date'])

    # 5. Sales Order Items tablosu
    op.create_table(
        'sales_order_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),

        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=True),
        sa.Column('quantity', sa.Numeric(15, 4), nullable=False),
        sa.Column('unit_id', sa.Integer(), nullable=True),
        sa.Column('delivered_quantity', sa.Numeric(15, 4), server_default='0', nullable=True),
        sa.Column('invoiced_quantity', sa.Numeric(15, 4), server_default='0', nullable=True),
        sa.Column('unit_price', sa.Numeric(15, 4), server_default='0', nullable=True),
        sa.Column('discount_rate', sa.Numeric(5, 2), server_default='0', nullable=True),
        sa.Column('tax_rate', sa.Numeric(5, 2), server_default='18', nullable=True),
        sa.Column('line_total', sa.Numeric(15, 2), server_default='0', nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('delivery_date', sa.Date(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['order_id'], ['sales_orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['item_id'], ['items.id']),
        sa.ForeignKeyConstraint(['unit_id'], ['units.id'])
    )

    # 6. Delivery Notes tablosu
    op.create_table(
        'delivery_notes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),

        sa.Column('delivery_no', sa.String(20), nullable=False),
        sa.Column('delivery_date', sa.Date(), nullable=False),
        sa.Column('sales_order_id', sa.Integer(), nullable=True),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('status', deliverynotestatus, server_default='draft', nullable=True),

        sa.Column('source_warehouse_id', sa.Integer(), nullable=False),
        sa.Column('shipping_address', sa.Text(), nullable=True),
        sa.Column('shipping_method', sa.String(100), nullable=True),
        sa.Column('tracking_no', sa.String(100), nullable=True),
        sa.Column('actual_delivery_date', sa.Date(), nullable=True),

        sa.Column('notes', sa.Text(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('delivery_no'),
        sa.ForeignKeyConstraint(['sales_order_id'], ['sales_orders.id']),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.ForeignKeyConstraint(['source_warehouse_id'], ['warehouses.id'])
    )
    op.create_index('idx_dn_customer', 'delivery_notes', ['customer_id'])
    op.create_index('idx_dn_order', 'delivery_notes', ['sales_order_id'])
    op.create_index('idx_dn_status', 'delivery_notes', ['status'])
    op.create_index('idx_dn_date', 'delivery_notes', ['delivery_date'])

    # 7. Delivery Note Items tablosu
    op.create_table(
        'delivery_note_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),

        sa.Column('delivery_note_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=True),
        sa.Column('so_item_id', sa.Integer(), nullable=True),
        sa.Column('quantity', sa.Numeric(15, 4), nullable=False),
        sa.Column('unit_id', sa.Integer(), nullable=True),
        sa.Column('lot_number', sa.String(50), nullable=True),
        sa.Column('serial_numbers', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['delivery_note_id'], ['delivery_notes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['item_id'], ['items.id']),
        sa.ForeignKeyConstraint(['so_item_id'], ['sales_order_items.id']),
        sa.ForeignKeyConstraint(['unit_id'], ['units.id'])
    )

    # 8. Invoices tablosu
    op.create_table(
        'invoices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),

        sa.Column('invoice_no', sa.String(20), nullable=False),
        sa.Column('invoice_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('sales_order_id', sa.Integer(), nullable=True),
        sa.Column('delivery_note_id', sa.Integer(), nullable=True),
        sa.Column('status', invoicestatus, server_default='draft', nullable=True),

        sa.Column('currency', sa.String(10), server_default='TRY', nullable=True),
        sa.Column('exchange_rate', sa.Numeric(10, 4), server_default='1', nullable=True),
        sa.Column('subtotal', sa.Numeric(15, 2), server_default='0', nullable=True),
        sa.Column('discount_amount', sa.Numeric(15, 2), server_default='0', nullable=True),
        sa.Column('tax_amount', sa.Numeric(15, 2), server_default='0', nullable=True),
        sa.Column('total', sa.Numeric(15, 2), server_default='0', nullable=True),

        sa.Column('paid_amount', sa.Numeric(15, 2), server_default='0', nullable=True),
        sa.Column('balance', sa.Numeric(15, 2), server_default='0', nullable=True),
        sa.Column('paid_date', sa.Date(), nullable=True),
        sa.Column('payment_method', sa.String(50), nullable=True),
        sa.Column('payment_notes', sa.Text(), nullable=True),

        sa.Column('notes', sa.Text(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invoice_no'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.ForeignKeyConstraint(['sales_order_id'], ['sales_orders.id']),
        sa.ForeignKeyConstraint(['delivery_note_id'], ['delivery_notes.id'])
    )
    op.create_index('idx_inv_customer', 'invoices', ['customer_id'])
    op.create_index('idx_inv_status', 'invoices', ['status'])
    op.create_index('idx_inv_date', 'invoices', ['invoice_date'])
    op.create_index('idx_inv_due_date', 'invoices', ['due_date'])

    # 9. Invoice Items tablosu
    op.create_table(
        'invoice_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),

        sa.Column('invoice_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=True),
        sa.Column('quantity', sa.Numeric(15, 4), nullable=False),
        sa.Column('unit_id', sa.Integer(), nullable=True),
        sa.Column('unit_price', sa.Numeric(15, 4), server_default='0', nullable=True),
        sa.Column('discount_rate', sa.Numeric(5, 2), server_default='0', nullable=True),
        sa.Column('tax_rate', sa.Numeric(5, 2), server_default='18', nullable=True),
        sa.Column('line_total', sa.Numeric(15, 2), server_default='0', nullable=True),
        sa.Column('description', sa.Text(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['item_id'], ['items.id']),
        sa.ForeignKeyConstraint(['unit_id'], ['units.id'])
    )


def downgrade() -> None:
    """Satış modülü tablolarını kaldır"""

    op.drop_table('invoice_items')
    op.drop_table('invoices')
    op.drop_table('delivery_note_items')
    op.drop_table('delivery_notes')
    op.drop_table('sales_order_items')
    op.drop_table('sales_orders')
    op.drop_table('sales_quote_items')
    op.drop_table('sales_quotes')
    op.drop_table('customers')

    op.execute('DROP TYPE IF EXISTS invoicestatus')
    op.execute('DROP TYPE IF EXISTS deliverynotestatus')
    op.execute('DROP TYPE IF EXISTS salesorderstatus')
    op.execute('DROP TYPE IF EXISTS salesquotestatus')
