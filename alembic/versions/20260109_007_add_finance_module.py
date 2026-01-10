"""Add finance module tables

Revision ID: 007_add_finance_module
Revises: 006_add_price_lists
Create Date: 2026-01-09

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '007_add_finance_module'
down_revision = '006_add_price_lists'
branch_labels = None
depends_on = None


def upgrade():
    # Cari hesap hareketleri tablosu
    op.create_table(
        'account_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transaction_no', sa.String(20), nullable=False),
        sa.Column('transaction_date', sa.Date(), nullable=False),
        sa.Column('transaction_type', sa.String(20), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('supplier_id', sa.Integer(), nullable=True),
        sa.Column('invoice_id', sa.Integer(), nullable=True),
        sa.Column('receipt_id', sa.Integer(), nullable=True),
        sa.Column('payment_id', sa.Integer(), nullable=True),
        sa.Column('debit', sa.Numeric(15, 2), nullable=False, server_default='0'),
        sa.Column('credit', sa.Numeric(15, 2), nullable=False, server_default='0'),
        sa.Column('payment_method', sa.String(20), nullable=True),
        sa.Column('reference_no', sa.String(50), nullable=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id']),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id']),
    )
    op.create_index('ix_account_transactions_no', 'account_transactions', ['transaction_no'], unique=True)
    op.create_index('idx_transaction_customer', 'account_transactions', ['customer_id', 'transaction_date'])
    op.create_index('idx_transaction_supplier', 'account_transactions', ['supplier_id', 'transaction_date'])
    op.create_index('idx_transaction_date', 'account_transactions', ['transaction_date'])

    # Tahsilat tablosu (Musterilerden)
    op.create_table(
        'receipts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('receipt_no', sa.String(20), nullable=False),
        sa.Column('receipt_date', sa.Date(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('currency', sa.String(10), nullable=False, server_default='TRY'),
        sa.Column('exchange_rate', sa.Numeric(10, 4), nullable=False, server_default='1'),
        sa.Column('payment_method', sa.String(20), nullable=False),
        sa.Column('bank_name', sa.String(100), nullable=True),
        sa.Column('bank_account', sa.String(50), nullable=True),
        sa.Column('check_no', sa.String(50), nullable=True),
        sa.Column('check_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='completed'),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
    )
    op.create_index('ix_receipts_no', 'receipts', ['receipt_no'], unique=True)
    op.create_index('idx_receipt_customer', 'receipts', ['customer_id', 'receipt_date'])
    op.create_index('idx_receipt_date', 'receipts', ['receipt_date'])

    # Tahsilat-Fatura eslestirme tablosu
    op.create_table(
        'receipt_allocations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('receipt_id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['receipt_id'], ['receipts.id']),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id']),
    )
    op.create_index('idx_receipt_allocation', 'receipt_allocations', ['receipt_id', 'invoice_id'], unique=True)

    # Odeme tablosu (Tedarikcilere)
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('payment_no', sa.String(20), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('currency', sa.String(10), nullable=False, server_default='TRY'),
        sa.Column('exchange_rate', sa.Numeric(10, 4), nullable=False, server_default='1'),
        sa.Column('payment_method', sa.String(20), nullable=False),
        sa.Column('bank_name', sa.String(100), nullable=True),
        sa.Column('bank_account', sa.String(50), nullable=True),
        sa.Column('check_no', sa.String(50), nullable=True),
        sa.Column('check_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='completed'),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id']),
    )
    op.create_index('ix_payments_no', 'payments', ['payment_no'], unique=True)
    op.create_index('idx_payment_supplier', 'payments', ['supplier_id', 'payment_date'])
    op.create_index('idx_payment_date', 'payments', ['payment_date'])

    # Odeme-Fatura eslestirme tablosu (Tedarikci faturalari icin)
    op.create_table(
        'payment_allocations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('payment_id', sa.Integer(), nullable=False),
        sa.Column('reference_type', sa.String(50), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id']),
    )
    op.create_index('idx_payment_allocation', 'payment_allocations', ['payment_id', 'reference_type', 'reference_id'])

    # account_transactions tablosuna receipt_id ve payment_id FK ekle
    op.create_foreign_key(
        'fk_transaction_receipt',
        'account_transactions', 'receipts',
        ['receipt_id'], ['id']
    )
    op.create_foreign_key(
        'fk_transaction_payment',
        'account_transactions', 'payments',
        ['payment_id'], ['id']
    )


def downgrade():
    # FK kaldır
    op.drop_constraint('fk_transaction_payment', 'account_transactions', type_='foreignkey')
    op.drop_constraint('fk_transaction_receipt', 'account_transactions', type_='foreignkey')

    # Tablolari kaldır
    op.drop_index('idx_payment_allocation', 'payment_allocations')
    op.drop_table('payment_allocations')

    op.drop_index('idx_payment_date', 'payments')
    op.drop_index('idx_payment_supplier', 'payments')
    op.drop_index('ix_payments_no', 'payments')
    op.drop_table('payments')

    op.drop_index('idx_receipt_allocation', 'receipt_allocations')
    op.drop_table('receipt_allocations')

    op.drop_index('idx_receipt_date', 'receipts')
    op.drop_index('idx_receipt_customer', 'receipts')
    op.drop_index('ix_receipts_no', 'receipts')
    op.drop_table('receipts')

    op.drop_index('idx_transaction_date', 'account_transactions')
    op.drop_index('idx_transaction_supplier', 'account_transactions')
    op.drop_index('idx_transaction_customer', 'account_transactions')
    op.drop_index('ix_account_transactions_no', 'account_transactions')
    op.drop_table('account_transactions')
