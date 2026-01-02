"""Add actual fields to production

Revision ID: 001
Revises: 
Create Date: 2026-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_add_actual_fields'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    WorkOrder, WorkOrderLine ve WorkOrderOperation tablolarına
    actual (gerçekleşen) alanları ekle
    """
    
    # ============================================================
    # WORK_ORDERS tablosu
    # ============================================================
    with op.batch_alter_table('work_orders', schema=None) as batch_op:
        # Depo bilgisi
        batch_op.add_column(sa.Column('warehouse_id', sa.Integer(), nullable=True))
        
        # Gerçekleşen miktarlar
        batch_op.add_column(sa.Column('actual_quantity', sa.Numeric(18, 4), server_default='0'))
        batch_op.add_column(sa.Column('scrap_quantity', sa.Numeric(18, 4), server_default='0'))
        batch_op.add_column(sa.Column('actual_unit_cost', sa.Numeric(18, 4), server_default='0'))
        
        # Gerçekleşen maliyetler
        batch_op.add_column(sa.Column('actual_material_cost', sa.Numeric(18, 4), server_default='0'))
        batch_op.add_column(sa.Column('actual_labor_cost', sa.Numeric(18, 4), server_default='0'))
        batch_op.add_column(sa.Column('actual_overhead_cost', sa.Numeric(18, 4), server_default='0'))
        
        # Verimlilik
        batch_op.add_column(sa.Column('efficiency_rate', sa.Numeric(5, 2), server_default='0'))
        
        # Foreign key (SQLite batch mode'da ayrı eklenmeli)
        # batch_op.create_foreign_key('fk_work_orders_warehouse', 'warehouses', ['warehouse_id'], ['id'])
    
    # ============================================================
    # WORK_ORDER_LINES tablosu
    # ============================================================
    with op.batch_alter_table('work_order_lines', schema=None) as batch_op:
        # Çıkış yapılan miktar
        batch_op.add_column(sa.Column('issued_quantity', sa.Numeric(18, 4), server_default='0'))
        
        # Gerçekleşen maliyetler
        batch_op.add_column(sa.Column('actual_unit_cost', sa.Numeric(18, 4), server_default='0'))
        batch_op.add_column(sa.Column('actual_line_cost', sa.Numeric(18, 4), server_default='0'))
    
    # ============================================================
    # WORK_ORDER_OPERATIONS tablosu
    # ============================================================
    with op.batch_alter_table('work_order_operations', schema=None) as batch_op:
        # Durum
        batch_op.add_column(sa.Column('status', sa.String(20), server_default='pending'))
        
        # Gerçek tarihler
        batch_op.add_column(sa.Column('actual_start', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('actual_end', sa.DateTime(), nullable=True))
        
        # Gerçek süreler
        batch_op.add_column(sa.Column('actual_setup_time', sa.Integer(), server_default='0'))
        batch_op.add_column(sa.Column('actual_run_time', sa.Integer(), server_default='0'))
        
        # Operatör
        batch_op.add_column(sa.Column('operator_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Değişiklikleri geri al"""
    
    # WORK_ORDER_OPERATIONS
    with op.batch_alter_table('work_order_operations', schema=None) as batch_op:
        batch_op.drop_column('operator_id')
        batch_op.drop_column('actual_run_time')
        batch_op.drop_column('actual_setup_time')
        batch_op.drop_column('actual_end')
        batch_op.drop_column('actual_start')
        batch_op.drop_column('status')
    
    # WORK_ORDER_LINES
    with op.batch_alter_table('work_order_lines', schema=None) as batch_op:
        batch_op.drop_column('actual_line_cost')
        batch_op.drop_column('actual_unit_cost')
        batch_op.drop_column('issued_quantity')
    
    # WORK_ORDERS
    with op.batch_alter_table('work_orders', schema=None) as batch_op:
        batch_op.drop_column('efficiency_rate')
        batch_op.drop_column('actual_overhead_cost')
        batch_op.drop_column('actual_labor_cost')
        batch_op.drop_column('actual_material_cost')
        batch_op.drop_column('actual_unit_cost')
        batch_op.drop_column('scrap_quantity')
        batch_op.drop_column('actual_quantity')
        batch_op.drop_column('warehouse_id')
