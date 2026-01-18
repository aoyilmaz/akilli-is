"""Add notifications table

Revision ID: f6g7h8i9j0k1
Revises: e5f6g7h8i9j0
Create Date: 2026-01-16

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f6g7h8i9j0k1'
down_revision = 'e5f6g7h8i9j0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Notifications tablosu
    # notification_type: String olarak tanımlanıyor, enum değerleri uygulama seviyesinde kontrol ediliyor
    # Mevcut 'notificationtype' PostgreSQL enum'u varsa onu kullan

    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column(
            'notification_type',
            sa.String(20),
            nullable=False,
            server_default='info'
        ),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('link', sa.String(255), nullable=True),
        sa.Column('related_module', sa.String(50), nullable=True),
        sa.Column('related_record_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Index'ler (performans için)
    op.create_index(
        'idx_notification_user_unread',
        'notifications',
        ['user_id', 'is_read']
    )
    op.create_index(
        'idx_notification_module',
        'notifications',
        ['related_module']
    )
    op.create_index(
        'idx_notification_created',
        'notifications',
        ['created_at']
    )


def downgrade() -> None:
    op.drop_index('idx_notification_created', table_name='notifications')
    op.drop_index('idx_notification_module', table_name='notifications')
    op.drop_index('idx_notification_user_unread', table_name='notifications')
    op.drop_table('notifications')
