"""Enhance maintenance module - CMMS features

Revision ID: a1b2c3d4e5f6
Revises: 68385b340842
Create Date: 2026-01-15 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "68385b340842"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create EquipmentStatus enum
    equipment_status_enum = postgresql.ENUM(
        'RUNNING', 'STOPPED', 'MAINTENANCE', 'BREAKDOWN', 'RETIRED',
        name='equipmentstatus',
        create_type=False
    )
    equipment_status_enum.create(op.get_bind(), checkfirst=True)

    # Add new columns to equipments table
    with op.batch_alter_table('equipments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('parent_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('current_status', sa.Enum(
            'RUNNING', 'STOPPED', 'MAINTENANCE', 'BREAKDOWN', 'RETIRED',
            name='equipmentstatus'
        ), nullable=True, server_default='RUNNING'))
        batch_op.add_column(sa.Column('running_hours', sa.Numeric(precision=18, scale=2), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('last_meter_reading', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.add_column(sa.Column('last_meter_date', sa.DateTime(), nullable=True))
        batch_op.create_foreign_key('fk_equipment_parent', 'equipments', ['parent_id'], ['id'])
        batch_op.create_index('idx_equipment_status', ['current_status'], unique=False)

    # Create maintenance_checklists table (must be created before tables that reference it)
    op.create_table(
        'maintenance_checklists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('equipment_id', sa.Integer(), nullable=True),
        sa.Column('maintenance_type', postgresql.ENUM(
            'BREAKDOWN', 'PREVENTIVE', 'PREDICTIVE', 'CALIBRATION',
            name='maintenancetype',
            create_type=False
        ), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['equipment_id'], ['equipments.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create maintenance_checklist_items table
    op.create_table(
        'maintenance_checklist_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('checklist_id', sa.Integer(), nullable=False),
        sa.Column('order_no', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['checklist_id'], ['maintenance_checklists.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Add new columns to maintenance_work_orders table
    with op.batch_alter_table('maintenance_work_orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('estimated_hours', sa.Numeric(precision=8, scale=2), nullable=True))
        batch_op.add_column(sa.Column('actual_hours', sa.Numeric(precision=8, scale=2), nullable=True))
        batch_op.add_column(sa.Column('labor_hours', sa.Numeric(precision=8, scale=2), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('hourly_rate', sa.Numeric(precision=18, scale=4), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('checklist_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_wo_checklist', 'maintenance_checklists', ['checklist_id'], ['id'])

    # Add new columns to maintenance_plans table
    with op.batch_alter_table('maintenance_plans', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_counter_based', sa.Boolean(), nullable=True, server_default='false'))
        batch_op.add_column(sa.Column('counter_interval', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('last_counter_value', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.add_column(sa.Column('next_due_counter', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.add_column(sa.Column('auto_generate_work_order', sa.Boolean(), nullable=True, server_default='true'))
        batch_op.add_column(sa.Column('lead_days', sa.Integer(), nullable=True, server_default='7'))
        batch_op.add_column(sa.Column('checklist_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_plan_checklist', 'maintenance_checklists', ['checklist_id'], ['id'])

    # Create equipment_spare_parts table
    op.create_table(
        'equipment_spare_parts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('equipment_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('min_quantity', sa.Numeric(precision=18, scale=4), nullable=True, server_default='1'),
        sa.Column('recommended_quantity', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['equipment_id'], ['equipments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['item_id'], ['items.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create equipment_downtimes table
    op.create_table(
        'equipment_downtimes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('equipment_id', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('reason', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('work_order_id', sa.Integer(), nullable=True),
        sa.Column('recorded_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['equipment_id'], ['equipments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['work_order_id'], ['maintenance_work_orders.id']),
        sa.ForeignKeyConstraint(['recorded_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('equipment_downtimes', schema=None) as batch_op:
        batch_op.create_index('idx_downtime_equipment', ['equipment_id'], unique=False)
        batch_op.create_index('idx_downtime_dates', ['start_time', 'end_time'], unique=False)

    # Create maintenance_request_attachments table
    op.create_table(
        'maintenance_request_attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('request_id', sa.Integer(), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('uploaded_by_id', sa.Integer(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['request_id'], ['maintenance_requests.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create work_order_attachments table
    op.create_table(
        'work_order_attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('work_order_id', sa.Integer(), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('uploaded_by_id', sa.Integer(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['work_order_id'], ['maintenance_work_orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create work_order_checklist_results table
    op.create_table(
        'work_order_checklist_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('work_order_id', sa.Integer(), nullable=False),
        sa.Column('checklist_item_id', sa.Integer(), nullable=False),
        sa.Column('is_checked', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('checked_by_id', sa.Integer(), nullable=True),
        sa.Column('checked_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['work_order_id'], ['maintenance_work_orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['checklist_item_id'], ['maintenance_checklist_items.id']),
        sa.ForeignKeyConstraint(['checked_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('work_order_checklist_results')
    op.drop_table('work_order_attachments')
    op.drop_table('maintenance_request_attachments')
    op.drop_table('equipment_downtimes')
    op.drop_table('equipment_spare_parts')

    # Remove columns from maintenance_plans
    with op.batch_alter_table('maintenance_plans', schema=None) as batch_op:
        batch_op.drop_constraint('fk_plan_checklist', type_='foreignkey')
        batch_op.drop_column('checklist_id')
        batch_op.drop_column('lead_days')
        batch_op.drop_column('auto_generate_work_order')
        batch_op.drop_column('next_due_counter')
        batch_op.drop_column('last_counter_value')
        batch_op.drop_column('counter_interval')
        batch_op.drop_column('is_counter_based')

    # Remove columns from maintenance_work_orders
    with op.batch_alter_table('maintenance_work_orders', schema=None) as batch_op:
        batch_op.drop_constraint('fk_wo_checklist', type_='foreignkey')
        batch_op.drop_column('checklist_id')
        batch_op.drop_column('hourly_rate')
        batch_op.drop_column('labor_hours')
        batch_op.drop_column('actual_hours')
        batch_op.drop_column('estimated_hours')

    # Drop checklist tables
    op.drop_table('maintenance_checklist_items')
    op.drop_table('maintenance_checklists')

    # Remove columns from equipments
    with op.batch_alter_table('equipments', schema=None) as batch_op:
        batch_op.drop_index('idx_equipment_status')
        batch_op.drop_constraint('fk_equipment_parent', type_='foreignkey')
        batch_op.drop_column('last_meter_date')
        batch_op.drop_column('last_meter_reading')
        batch_op.drop_column('running_hours')
        batch_op.drop_column('current_status')
        batch_op.drop_column('parent_id')

    # Drop enum type
    equipment_status_enum = postgresql.ENUM(
        'RUNNING', 'STOPPED', 'MAINTENANCE', 'BREAKDOWN', 'RETIRED',
        name='equipmentstatus'
    )
    equipment_status_enum.drop(op.get_bind(), checkfirst=True)
