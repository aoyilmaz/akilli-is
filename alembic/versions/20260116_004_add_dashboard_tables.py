"""Add dashboard tables

Revision ID: g7h8i9j0k1l2
Revises: f6g7h8i9j0k1
Create Date: 2026-01-16

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'g7h8i9j0k1l2'
down_revision = 'f6g7h8i9j0k1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # DashboardWidget tablosu - Widget tanımları
    op.create_table(
        'dashboard_widgets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('widget_type', sa.String(50), nullable=False),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('default_width', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('default_height', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('min_width', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('min_height', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('max_width', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('max_height', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('config_schema', sa.JSON(), nullable=True),
        sa.Column('default_config', sa.JSON(), nullable=True),
        sa.Column('required_permission', sa.String(100), nullable=True),
        sa.Column('allowed_roles', sa.JSON(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_dashboard_widget_code', 'dashboard_widgets', ['code'], unique=True)

    # RoleDefaultLayout tablosu - Role varsayılan düzenleri
    op.create_table(
        'role_default_layouts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('layout', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_role_default_layout_role', 'role_default_layouts', ['role_id'], unique=True)

    # UserDashboardLayout tablosu - Kullanıcı özel düzenleri
    op.create_table(
        'user_dashboard_layouts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('layout', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_dashboard_layout_user', 'user_dashboard_layouts', ['user_id'], unique=True)

    # Varsayılan widget'ları ekle
    op.execute("""
        INSERT INTO dashboard_widgets (code, name, description, widget_type, icon, default_width, default_height, is_system, sort_order) VALUES
        -- Sistem Widget'ları (Herkese Açık)
        ('weather', 'Hava Durumu', 'Şehir hava durumu bilgisi', 'external', 'cloud', 1, 1, true, 1),
        ('currency_rates', 'Döviz Kurları', 'TCMB döviz kurları (USD, EUR, GBP)', 'external', 'money', 2, 1, true, 2),
        ('stock_bist', 'Borsa Özeti', 'BIST endeks bilgileri', 'external', 'chart-line', 2, 1, true, 3),
        ('notifications', 'Bildirimler', 'Okunmamış bildirimler listesi', 'list', 'bell', 1, 2, true, 4),
        ('quick_actions', 'Hızlı İşlemler', 'Sık kullanılan işlemler', 'action', 'bolt', 1, 1, true, 5),

        -- Modül Widget'ları (İzne Bağlı)
        ('stat_sales_today', 'Bugünkü Satışlar', 'Günlük satış toplamı', 'stat', 'shopping-cart', 1, 1, true, 10),
        ('stat_pending_orders', 'Bekleyen Siparişler', 'Onay bekleyen sipariş sayısı', 'stat', 'clock', 1, 1, true, 11),
        ('stat_low_stock', 'Stok Uyarıları', 'Kritik seviyedeki stok sayısı', 'stat', 'exclamation-triangle', 1, 1, true, 12),
        ('stat_open_work_orders', 'Açık İş Emirleri', 'Devam eden iş emri sayısı', 'stat', 'cogs', 1, 1, true, 13),
        ('chart_sales', 'Satış Grafiği', 'Son 7 günlük satış trendi', 'chart', 'chart-bar', 2, 2, true, 20),
        ('chart_production', 'Üretim Grafiği', 'Günlük üretim miktarları', 'chart', 'industry', 2, 2, true, 21);
    """)

    # Widget izinlerini güncelle
    op.execute("""
        UPDATE dashboard_widgets SET required_permission = 'sales.view'
        WHERE code IN ('stat_sales_today', 'stat_pending_orders', 'chart_sales');

        UPDATE dashboard_widgets SET required_permission = 'inventory.view'
        WHERE code = 'stat_low_stock';

        UPDATE dashboard_widgets SET required_permission = 'production.view'
        WHERE code IN ('stat_open_work_orders', 'chart_production');
    """)


def downgrade() -> None:
    op.drop_index('idx_user_dashboard_layout_user', table_name='user_dashboard_layouts')
    op.drop_table('user_dashboard_layouts')
    op.drop_index('idx_role_default_layout_role', table_name='role_default_layouts')
    op.drop_table('role_default_layouts')
    op.drop_index('idx_dashboard_widget_code', table_name='dashboard_widgets')
    op.drop_table('dashboard_widgets')
