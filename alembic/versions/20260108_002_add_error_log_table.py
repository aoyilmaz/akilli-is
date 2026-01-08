"""Add ErrorLog table for development module

Revision ID: 002_add_error_log_table
Revises: 001_add_actual_fields
Create Date: 2026-01-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_add_error_log_table'
down_revision: Union[str, None] = '001_add_actual_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    ErrorLog tablosunu oluştur
    Detaylı hata kaydı için tüm alanlar
    """

    op.create_table(
        'error_logs',
        # BaseModel alanları (id, created_at, updated_at, is_active)
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),

        # Kullanıcı Bilgisi
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('username', sa.String(100), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),

        # Hata Detayı
        sa.Column('error_type', sa.String(200), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('error_traceback', sa.Text(), nullable=True),
        sa.Column('error_args', sa.Text(), nullable=True),

        # Lokasyon Bilgisi
        sa.Column('module_name', sa.String(100), nullable=True),
        sa.Column('screen_name', sa.String(200), nullable=True),
        sa.Column('function_name', sa.String(200), nullable=True),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('line_number', sa.Integer(), nullable=True),

        # Sistem Bilgisi
        sa.Column('python_version', sa.String(50), nullable=True),
        sa.Column('os_info', sa.String(200), nullable=True),

        # Severity
        sa.Column('severity', sa.Enum('critical', 'error', 'warning', 'info', name='errorseverity'), nullable=False),

        # Çözüm Takibi
        sa.Column('is_resolved', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.Integer(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),

        # Primary Key
        sa.PrimaryKeyConstraint('id'),

        # Foreign Keys
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ),
    )

    # İndeksler
    with op.batch_alter_table('error_logs', schema=None) as batch_op:
        batch_op.create_index('idx_error_severity', ['severity'], unique=False)
        batch_op.create_index('idx_error_module', ['module_name'], unique=False)
        batch_op.create_index('idx_error_resolved', ['is_resolved'], unique=False)
        batch_op.create_index('idx_error_date', ['created_at'], unique=False)
        batch_op.create_index('idx_error_user', ['user_id'], unique=False)


def downgrade() -> None:
    """ErrorLog tablosunu sil"""

    # İndeksleri sil
    with op.batch_alter_table('error_logs', schema=None) as batch_op:
        batch_op.drop_index('idx_error_user')
        batch_op.drop_index('idx_error_date')
        batch_op.drop_index('idx_error_resolved')
        batch_op.drop_index('idx_error_module')
        batch_op.drop_index('idx_error_severity')

    # Tabloyu sil
    op.drop_table('error_logs')

    # Enum tipini sil (PostgreSQL için)
    op.execute('DROP TYPE IF EXISTS errorseverity')
