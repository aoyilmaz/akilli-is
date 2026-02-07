"""Add trace tables for debug system

Revision ID: add_trace_tables
Revises:
Create Date: 2026-02-05 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_trace_tables'
down_revision = '8g12744b21fb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # TraceSession tablosu
    op.create_table(
        'trace_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.Enum('active', 'completed', 'error', 'timeout', name='tracestatus'), nullable=False),
        sa.Column('trigger_reason', sa.String(length=50), nullable=True, default='manual'),
        sa.Column('total_events', sa.Integer(), nullable=True, default=0),
        sa.Column('error_log_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['error_log_id'], ['error_logs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_trace_session_user', 'trace_sessions', ['user_id'])
    op.create_index('idx_trace_session_status', 'trace_sessions', ['status'])
    op.create_index('idx_trace_session_date', 'trace_sessions', ['started_at'])

    # TraceEvent tablosu
    op.create_table(
        'trace_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.Enum(
            'page_navigation', 'button_click', 'table_filter', 'table_selection',
            'form_input', 'method_call', 'sql_query', 'error_occurred',
            name='traceeventtype'
        ), nullable=False),
        sa.Column('widget_name', sa.String(length=200), nullable=True),
        sa.Column('widget_path', sa.String(length=500), nullable=True),
        sa.Column('event_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.ForeignKeyConstraint(['session_id'], ['trace_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_trace_event_session', 'trace_events', ['session_id'])
    op.create_index('idx_trace_event_type', 'trace_events', ['event_type'])
    op.create_index('idx_trace_event_timestamp', 'trace_events', ['timestamp'])


def downgrade() -> None:
    op.drop_index('idx_trace_event_timestamp', table_name='trace_events')
    op.drop_index('idx_trace_event_type', table_name='trace_events')
    op.drop_index('idx_trace_event_session', table_name='trace_events')
    op.drop_table('trace_events')

    op.drop_index('idx_trace_session_date', table_name='trace_sessions')
    op.drop_index('idx_trace_session_status', table_name='trace_sessions')
    op.drop_index('idx_trace_session_user', table_name='trace_sessions')
    op.drop_table('trace_sessions')

    # Enum tiplerini kaldır
    op.execute("DROP TYPE IF EXISTS traceeventtype")
    op.execute("DROP TYPE IF EXISTS tracestatus")
