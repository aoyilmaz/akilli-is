"""Add price lists tables

Revision ID: 006_add_price_lists
Revises: 005_add_sales_module
Create Date: 2026-01-09

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '006_add_price_lists'
down_revision = '005_add_sales_module'
branch_labels = None
depends_on = None


def upgrade():
    # Fiyat listeleri tablosu
    op.create_table(
        'price_lists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(20), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('list_type', sa.String(20), nullable=False, server_default='sales'),
        sa.Column('currency', sa.String(10), nullable=False, server_default='TRY'),
        sa.Column('valid_from', sa.Date(), nullable=True),
        sa.Column('valid_until', sa.Date(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_price_lists_code', 'price_lists', ['code'], unique=True)

    # Fiyat listesi kalemleri tablosu
    op.create_table(
        'price_list_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('price_list_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(18, 4), nullable=False),
        sa.Column('min_quantity', sa.Numeric(18, 4), nullable=False, server_default='0'),
        sa.Column('discount_rate', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('notes', sa.String(200), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['price_list_id'], ['price_lists.id']),
        sa.ForeignKeyConstraint(['item_id'], ['items.id']),
    )
    op.create_index(
        'idx_price_list_item_unique',
        'price_list_items',
        ['price_list_id', 'item_id', 'min_quantity'],
        unique=True
    )

    # Müşteri tablosuna fiyat listesi referansı ekle
    op.add_column(
        'customers',
        sa.Column('price_list_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_customers_price_list',
        'customers', 'price_lists',
        ['price_list_id'], ['id']
    )


def downgrade():
    # Müşteri tablosundan fiyat listesi referansını kaldır
    op.drop_constraint('fk_customers_price_list', 'customers', type_='foreignkey')
    op.drop_column('customers', 'price_list_id')

    # Tabloları kaldır
    op.drop_index('idx_price_list_item_unique', 'price_list_items')
    op.drop_table('price_list_items')
    op.drop_index('ix_price_lists_code', 'price_lists')
    op.drop_table('price_lists')
