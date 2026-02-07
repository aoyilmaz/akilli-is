"""
Akıllı İş - Geliştirme Modülü Modelleri
Hata Yönetimi ve Loglama
"""

import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    Index,
    JSON,
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

    __tablename__ = "error_logs"

    # ========== KULLANICI BİLGİSİ ==========
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
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
        nullable=False,
    )

    # ========== ÇÖZÜM TAKİBİ ==========
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # ========== İLİŞKİLER ==========
    user = relationship("User", foreign_keys=[user_id], backref="error_logs")
    resolver = relationship(
        "User", foreign_keys=[resolved_by], backref="resolved_errors"
    )

    # ========== INDEX'LER ==========
    __table_args__ = (
        Index("idx_error_severity", "severity"),
        Index("idx_error_module", "module_name"),
        Index("idx_error_resolved", "is_resolved"),
        Index("idx_error_date", "created_at"),
        Index("idx_error_user", "user_id"),
    )

    def __repr__(self):
        return f"<ErrorLog {self.id}: {self.error_type} in {self.module_name}>"


class TraceStatus(enum.Enum):
    """Trace oturum durumları"""

    ACTIVE = "active"
    COMPLETED = "completed"
    ERROR = "error"
    TIMEOUT = "timeout"


class TraceEventType(enum.Enum):
    """Trace event tipleri"""

    PAGE_NAVIGATION = "page_navigation"
    BUTTON_CLICK = "button_click"
    TABLE_FILTER = "table_filter"
    TABLE_SELECTION = "table_selection"
    FORM_INPUT = "form_input"
    METHOD_CALL = "method_call"
    SQL_QUERY = "sql_query"
    ERROR_OCCURRED = "error_occurred"
    NETWORK_REQUEST = "network_request"
    SYSTEM_STATS = "system_stats"
    LOG_ENTRY = "log_entry"


class TraceSession(BaseModel):
    """
    Trace Oturum Tablosu

    Kullanıcı trace'i başlattığında oluşturulur:
    - Hangi kullanıcı başlattı
    - Ne zaman başladı/bitti
    - Kaç event kaydedildi
    - Hata ile mi sonlandı
    """

    __tablename__ = "trace_sessions"

    # ========== KULLANICI BİLGİSİ ==========
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # ========== ZAMAN BİLGİSİ ==========
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)

    # ========== DURUM ==========
    status = Column(
        SQLEnum(TraceStatus, values_callable=lambda x: [e.value for e in x]),
        default=TraceStatus.ACTIVE,
        nullable=False,
    )
    trigger_reason = Column(String(50), default="manual")  # manual, auto

    # ========== İSTATİSTİK ==========
    total_events = Column(Integer, default=0)

    # ========== HATA İLİŞKİSİ ==========
    error_log_id = Column(Integer, ForeignKey("error_logs.id"), nullable=True)

    # ========== İLİŞKİLER ==========
    user = relationship("User", backref="trace_sessions")
    error_log = relationship("ErrorLog", backref="trace_session")
    events = relationship(
        "TraceEvent", back_populates="session", cascade="all, delete-orphan"
    )

    # ========== INDEX'LER ==========
    __table_args__ = (
        Index("idx_trace_session_user", "user_id"),
        Index("idx_trace_session_status", "status"),
        Index("idx_trace_session_date", "started_at"),
    )

    def __repr__(self):
        return (
            f"<TraceSession {self.id}: user={self.user_id} status={self.status.value}>"
        )


class TraceEvent(BaseModel):
    """
    Trace Event Tablosu

    Her kullanıcı aksiyonu bir event olarak kaydedilir:
    - Sayfa geçişleri
    - Buton tıklamaları
    - Tablo filtreleri
    - Form girişleri
    - Servis metod çağrıları
    - SQL sorguları
    """

    __tablename__ = "trace_events"

    # ========== OTURUM İLİŞKİSİ ==========
    session_id = Column(Integer, ForeignKey("trace_sessions.id"), nullable=False)

    # ========== EVENT BİLGİSİ ==========
    event_type = Column(
        SQLEnum(TraceEventType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    widget_name = Column(String(200), nullable=True)  # "customer_list", "save_btn"
    widget_path = Column(String(500), nullable=True)  # "Satış > Müşteriler > Form"

    # ========== EVENT VERİSİ ==========
    event_data = Column(JSON, nullable=True)  # {"button_text": "Kaydet", ...}

    # ========== PERFORMANS ==========
    duration_ms = Column(Integer, nullable=True)  # Method/SQL süreleri için

    # ========== ZAMAN ==========
    timestamp = Column(DateTime, nullable=False)

    # ========== İLİŞKİLER ==========
    session = relationship("TraceSession", back_populates="events")

    # ========== INDEX'LER ==========
    __table_args__ = (
        Index("idx_trace_event_session", "session_id"),
        Index("idx_trace_event_type", "event_type"),
        Index("idx_trace_event_timestamp", "timestamp"),
    )

    def __repr__(self):
        return f"<TraceEvent {self.id}: {self.event_type.value} at {self.timestamp}>"
