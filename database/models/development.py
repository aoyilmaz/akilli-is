"""
Akıllı İş - Geliştirme Modülü Modelleri
Hata Yönetimi ve Loglama
"""

import enum
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, Enum as SQLEnum, Index, JSON
)
from sqlalchemy.orm import relationship

from database.base import BaseModel


class ErrorSeverity(enum.Enum):
    """Hata şiddet seviyeleri"""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ErrorLog(BaseModel):
    """
    DETAYLI Hata Kayıt Tablosu

    Tüm uygulama hatalarını kaydeder:
    - Exception detayları (type, message, traceback)
    - Kullanıcı bilgisi (kim, ne zaman)
    - Konum bilgisi (modül, ekran, fonksiyon, dosya, satır)
    - Sistem bilgisi (Python version, OS)
    - Çözüm takibi (çözüldü mü, kim çözdü, notlar)
    """

    __tablename__ = 'error_logs'

    # ========== KULLANICI BİLGİSİ ==========
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    username = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # ========== HATA DETAYI ==========
    error_type = Column(String(200), nullable=False)  # Exception.__class__.__name__
    error_message = Column(Text, nullable=False)  # str(exception)
    error_traceback = Column(Text, nullable=True)  # Full stack trace
    error_args = Column(Text, nullable=True)  # str(exception.args)

    # ========== LOKASYON BİLGİSİ ==========
    module_name = Column(String(100), nullable=True)  # 'inventory', 'production'
    screen_name = Column(String(200), nullable=True)  # 'WarehouseModule'
    function_name = Column(String(200), nullable=True)  # '_save_warehouse'
    file_path = Column(String(500), nullable=True)  # Tam dosya yolu
    line_number = Column(Integer, nullable=True)  # Hata satır numarası

    # ========== SİSTEM BİLGİSİ ==========
    python_version = Column(String(50), nullable=True)
    os_info = Column(String(200), nullable=True)

    # ========== SEVERITY ==========
    severity = Column(
        SQLEnum(ErrorSeverity, values_callable=lambda x: [e.value for e in x]),
        default=ErrorSeverity.ERROR,
        nullable=False
    )

    # ========== ÇÖZÜM TAKİBİ ==========
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # ========== İLİŞKİLER ==========
    user = relationship("User", foreign_keys=[user_id], backref="error_logs")
    resolver = relationship("User", foreign_keys=[resolved_by], backref="resolved_errors")

    # ========== INDEX'LER ==========
    __table_args__ = (
        Index('idx_error_severity', 'severity'),
        Index('idx_error_module', 'module_name'),
        Index('idx_error_resolved', 'is_resolved'),
        Index('idx_error_date', 'created_at'),
        Index('idx_error_user', 'user_id'),
    )

    def __repr__(self):
        return f"<ErrorLog {self.id}: {self.error_type} in {self.module_name}>"
