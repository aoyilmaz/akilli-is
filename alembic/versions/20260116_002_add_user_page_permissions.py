"""Add user_page_permissions table

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2026-01-16

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e5f6g7h8i9j0'
down_revision = 'd4e5f6g7h8i9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Kullanıcı bazlı sayfa izinleri tablosu
    op.create_table(
        'user_page_permissions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('page_id', sa.String(100), nullable=False),
        sa.Column('granted_by', sa.Integer(), nullable=True),
        sa.Column('granted_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['granted_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Unique index: aynı kullanıcıya aynı sayfa iki kez verilemez
    op.create_index(
        'idx_user_page',
        'user_page_permissions',
        ['user_id', 'page_id'],
        unique=True
    )


def downgrade() -> None:
    op.drop_index('idx_user_page', table_name='user_page_permissions')
    op.drop_table('user_page_permissions')
