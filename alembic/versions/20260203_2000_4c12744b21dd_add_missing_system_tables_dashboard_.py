"""add_missing_system_tables_dashboard_notifications

Revision ID: 4c12744b21dd
Revises: 7b767d66be67
Create Date: 2026-02-03 20:00:33.271435

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = "4c12744b21dd"
down_revision: Union[str, None] = "7b767d66be67"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # 1. user_sessions table
    if not insp.has_table("user_sessions"):
        op.create_table(
            "user_sessions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("session_token", sa.String(64), nullable=False),
            sa.Column("refresh_token", sa.String(64), nullable=True),
            sa.Column("device_name", sa.String(100), nullable=True),
            sa.Column("device_type", sa.String(20), nullable=True),
            sa.Column("os_info", sa.String(100), nullable=True),
            sa.Column("app_version", sa.String(20), nullable=True),
            sa.Column("ip_address", sa.String(45), nullable=True),
            sa.Column("location", sa.String(200), nullable=True),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("last_activity", sa.DateTime(), nullable=True),
            sa.Column("is_revoked", sa.Boolean(), default=False, nullable=False),
            sa.Column("revoked_at", sa.DateTime(), nullable=True),
            sa.Column("revoke_reason", sa.String(100), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        )
        op.create_index("idx_session_user", "user_sessions", ["user_id"])
        op.create_index(
            "idx_session_token", "user_sessions", ["session_token"], unique=True
        )
        op.create_index(
            "idx_session_refresh", "user_sessions", ["refresh_token"], unique=True
        )
        op.create_index("idx_session_expires", "user_sessions", ["expires_at"])
        op.create_index(
            "idx_session_active", "user_sessions", ["is_active", "is_revoked"]
        )

    # 2. user_page_permissions table
    if not insp.has_table("user_page_permissions"):
        op.create_table(
            "user_page_permissions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("page_id", sa.String(100), nullable=False),
            sa.Column("granted_by", sa.Integer(), nullable=True),
            sa.Column(
                "granted_at",
                sa.DateTime(),
                server_default=sa.text("NOW()"),
                nullable=True,
            ),
            sa.Column("notes", sa.String(500), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["granted_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "idx_user_page",
            "user_page_permissions",
            ["user_id", "page_id"],
            unique=True,
        )

    # 3. notifications table
    if not insp.has_table("notifications"):
        op.create_table(
            "notifications",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column(
                "notification_type",
                sa.String(20),
                nullable=False,
                server_default="info",
            ),
            sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("read_at", sa.DateTime(), nullable=True),
            sa.Column("link", sa.String(255), nullable=True),
            sa.Column("related_module", sa.String(50), nullable=True),
            sa.Column("related_record_id", sa.Integer(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("NOW()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("NOW()"),
            ),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "idx_notification_user_unread", "notifications", ["user_id", "is_read"]
        )
        op.create_index("idx_notification_module", "notifications", ["related_module"])
        op.create_index("idx_notification_created", "notifications", ["created_at"])

    # 4. dashboard tables
    if not insp.has_table("dashboard_widgets"):
        op.create_table(
            "dashboard_widgets",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("code", sa.String(50), nullable=False),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("description", sa.String(255), nullable=True),
            sa.Column("widget_type", sa.String(50), nullable=False),
            sa.Column("icon", sa.String(50), nullable=True),
            sa.Column(
                "default_width", sa.Integer(), nullable=False, server_default="1"
            ),
            sa.Column(
                "default_height", sa.Integer(), nullable=False, server_default="1"
            ),
            sa.Column("min_width", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("min_height", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("max_width", sa.Integer(), nullable=False, server_default="2"),
            sa.Column("max_height", sa.Integer(), nullable=False, server_default="2"),
            sa.Column("config_schema", sa.JSON(), nullable=True),
            sa.Column("default_config", sa.JSON(), nullable=True),
            sa.Column("required_permission", sa.String(100), nullable=True),
            sa.Column("allowed_roles", sa.JSON(), nullable=True),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column(
                "is_system", sa.Boolean(), nullable=False, server_default="false"
            ),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("NOW()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("NOW()"),
            ),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "idx_dashboard_widget_code", "dashboard_widgets", ["code"], unique=True
        )

    if not insp.has_table("role_default_layouts"):
        op.create_table(
            "role_default_layouts",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("role_id", sa.Integer(), nullable=False),
            sa.Column("layout", sa.JSON(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("NOW()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("NOW()"),
            ),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "idx_role_default_layout_role",
            "role_default_layouts",
            ["role_id"],
            unique=True,
        )

    if not insp.has_table("user_dashboard_layouts"):
        op.create_table(
            "user_dashboard_layouts",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("layout", sa.JSON(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("NOW()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("NOW()"),
            ),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "idx_user_dashboard_layout_user",
            "user_dashboard_layouts",
            ["user_id"],
            unique=True,
        )

    # Insert default widgets - IDEMPOTENT using ON CONFLICT DO NOTHING (PostgreSQL specific)
    # Since we can't easily use ON CONFLICT in raw insert string without listing constraints,
    # we can use NOT EXISTS check.
    op.execute(
        """
        INSERT INTO dashboard_widgets (code, name, description, widget_type, icon, default_width, default_height, is_system, sort_order) 
        SELECT code, name, description, widget_type, icon, default_width, default_height, is_system, sort_order 
        FROM (VALUES
            ('weather', 'Hava Durumu', 'Şehir hava durumu bilgisi', 'external', 'cloud', 1, 1, true, 1),
            ('currency_rates', 'Döviz Kurları', 'TCMB döviz kurları (USD, EUR, GBP)', 'external', 'money', 2, 1, true, 2),
            ('stock_bist', 'Borsa Özeti', 'BIST endeks bilgileri', 'external', 'chart-line', 2, 1, true, 3),
            ('notifications', 'Bildirimler', 'Okunmamış bildirimler listesi', 'list', 'bell', 1, 2, true, 4),
            ('quick_actions', 'Hızlı İşlemler', 'Sık kullanılan işlemler', 'action', 'bolt', 1, 1, true, 5),
            ('stat_sales_today', 'Bugünkü Satışlar', 'Günlük satış toplamı', 'stat', 'shopping-cart', 1, 1, true, 10),
            ('stat_pending_orders', 'Bekleyen Siparişler', 'Onay bekleyen sipariş sayısı', 'stat', 'clock', 1, 1, true, 11),
            ('stat_low_stock', 'Stok Uyarıları', 'Kritik seviyedeki stok sayısı', 'stat', 'exclamation-triangle', 1, 1, true, 12),
            ('stat_open_work_orders', 'Açık İş Emirleri', 'Devam eden iş emri sayısı', 'stat', 'cogs', 1, 1, true, 13),
            ('chart_sales', 'Satış Grafiği', 'Son 7 günlük satış trendi', 'chart', 'chart-bar', 2, 2, true, 20),
            ('chart_production', 'Üretim Grafiği', 'Günlük üretim miktarları', 'chart', 'industry', 2, 2, true, 21)
        ) AS v(code, name, description, widget_type, icon, default_width, default_height, is_system, sort_order)
        WHERE NOT EXISTS (SELECT 1 FROM dashboard_widgets WHERE code = v.code);
    """
    )

    # Update widget permissions
    op.execute(
        """
        UPDATE dashboard_widgets SET required_permission = 'sales.view'
        WHERE code IN ('stat_sales_today', 'stat_pending_orders', 'chart_sales');

        UPDATE dashboard_widgets SET required_permission = 'inventory.view'
        WHERE code = 'stat_low_stock';

        UPDATE dashboard_widgets SET required_permission = 'production.view'
        WHERE code IN ('stat_open_work_orders', 'chart_production');
    """
    )


def downgrade() -> None:
    # Reverse order
    if op.get_bind().dialect.has_table(op.get_bind(), "user_dashboard_layouts"):
        op.drop_table("user_dashboard_layouts")

    if op.get_bind().dialect.has_table(op.get_bind(), "role_default_layouts"):
        op.drop_table("role_default_layouts")

    if op.get_bind().dialect.has_table(op.get_bind(), "dashboard_widgets"):
        op.drop_table("dashboard_widgets")

    if op.get_bind().dialect.has_table(op.get_bind(), "notifications"):
        op.drop_table("notifications")

    if op.get_bind().dialect.has_table(op.get_bind(), "user_page_permissions"):
        op.drop_table("user_page_permissions")

    if op.get_bind().dialect.has_table(op.get_bind(), "user_sessions"):
        op.drop_table("user_sessions")
