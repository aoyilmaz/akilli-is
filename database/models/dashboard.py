"""
Akıllı İş - Dashboard Modelleri

Modüler dashboard sistemi için veritabanı modelleri.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    Index,
    JSON,
)
from sqlalchemy.orm import relationship

from database.base import BaseModel


class DashboardWidget(BaseModel):
    """
    Widget tanımları tablosu

    Sistemdeki tüm widget türlerini tanımlar.
    Her widget'ın kodu, adı, boyut bilgileri ve erişim kuralları burada tutulur.
    """

    __tablename__ = "dashboard_widgets"

    # Temel bilgiler
    code = Column(String(50), unique=True, nullable=False, index=True)  # "stat_sales", "weather"
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    widget_type = Column(String(50), nullable=False)  # "stat", "chart", "external", "list"
    icon = Column(String(50), nullable=True)  # Icon adı

    # Boyut seçenekleri (grid birimleri)
    default_width = Column(Integer, default=1)   # 1 veya 2
    default_height = Column(Integer, default=1)  # 1 veya 2
    min_width = Column(Integer, default=1)
    min_height = Column(Integer, default=1)
    max_width = Column(Integer, default=2)
    max_height = Column(Integer, default=2)

    # Yapılandırma
    config_schema = Column(JSON, nullable=True)   # Widget ayarları JSON şeması
    default_config = Column(JSON, nullable=True)  # Varsayılan yapılandırma

    # Erişim kontrolü
    required_permission = Column(String(100), nullable=True)  # İzin kodu (örn: "sales.view")
    allowed_roles = Column(JSON, nullable=True)  # ["ADMIN", "SALES"] - boşsa herkese açık

    # Sıralama ve görünürlük
    sort_order = Column(Integer, default=0)
    is_system = Column(Boolean, default=False)  # Sistem widget'ı mı (silinemez)

    def __repr__(self):
        return f"<DashboardWidget(code={self.code}, name={self.name})>"


class RoleDefaultLayout(BaseModel):
    """
    Role göre varsayılan dashboard düzeni

    Her rol için farklı varsayılan widget düzeni tanımlanabilir.
    Kullanıcı kendi düzenini kaydetmemişse bu düzen kullanılır.
    """

    __tablename__ = "role_default_layouts"

    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    layout = Column(JSON, nullable=False)  # Widget pozisyonları ve yapılandırmaları

    # İlişkiler
    role = relationship("Role", backref="dashboard_default_layout")

    # Unique constraint - her rol için tek varsayılan düzen
    __table_args__ = (
        Index("idx_role_default_layout_role", "role_id", unique=True),
    )

    def __repr__(self):
        return f"<RoleDefaultLayout(role_id={self.role_id})>"


class UserDashboardLayout(BaseModel):
    """
    Kullanıcı özel dashboard düzeni

    Kullanıcının kendi özelleştirdiği widget düzeni.
    Her kullanıcının tek bir düzeni olabilir.
    """

    __tablename__ = "user_dashboard_layouts"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    layout = Column(JSON, nullable=False)  # Widget pozisyonları ve yapılandırmaları

    # İlişkiler
    user = relationship("User", backref="dashboard_layout")

    # Unique constraint - her kullanıcı için tek düzen
    __table_args__ = (
        Index("idx_user_dashboard_layout_user", "user_id", unique=True),
    )

    def __repr__(self):
        return f"<UserDashboardLayout(user_id={self.user_id})>"


# Layout JSON formatı örneği:
# {
#     "version": "1.0",
#     "grid_columns": 4,
#     "widgets": [
#         {
#             "widget_code": "stat_sales_today",
#             "position": {"row": 0, "col": 0},
#             "size": {"width": 1, "height": 1},
#             "config": {}
#         },
#         {
#             "widget_code": "currency_rates",
#             "position": {"row": 0, "col": 2},
#             "size": {"width": 2, "height": 1},
#             "config": {"currencies": ["USD", "EUR", "GBP"]}
#         }
#     ]
# }
