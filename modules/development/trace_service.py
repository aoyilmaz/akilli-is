"""
Akıllı İş - Trace Service
On-demand hata izleme servisi

Performans garantileri:
- Trace kapalıyken overhead: ~0 (sadece boolean check)
- In-memory buffer ile batch DB yazımı
- Session isolation: Her kullanıcı kendi trace'ini görür
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import threading

from PyQt6.QtCore import QTimer, QObject, pyqtSignal, Qt

from database.base import get_session, get_engine
from sqlalchemy.orm import Session as SASession, make_transient
from database.models.development import (
    TraceSession,
    TraceEvent,
    TraceStatus,
    TraceEventType,
)


# Hassas veri maskeleme pattern'leri
SENSITIVE_PATTERNS = [
    "password",
    "parola",
    "sifre",
    "şifre",
    "credit_card",
    "kredi_kart",
    "cvv",
    "cvc",
    "token",
    "secret",
    "api_key",
]


def mask_sensitive_data(field_name: str, value: Any) -> Any:
    """Hassas verileri maskele"""
    if not isinstance(value, str):
        return value
    field_lower = str(field_name).lower()
    for pattern in SENSITIVE_PATTERNS:
        if pattern in field_lower:
            return "***MASKED***"
    return value


def mask_dict_values(data: dict) -> dict:
    """Dict içindeki hassas değerleri maskele"""
    if not isinstance(data, dict):
        return data
    return {k: mask_sensitive_data(k, v) for k, v in data.items()}


class TraceServiceSignals(QObject):
    """TraceService sinyalleri"""

    trace_started = pyqtSignal(int)  # session_id
    trace_stopped = pyqtSignal(int)  # session_id
    trace_timeout = pyqtSignal(int)  # user_id
    event_recorded = pyqtSignal(str)  # event_type


class TraceService:
    """
    On-demand Trace Service (Singleton)

    Kullanım:
        TraceService.start_trace(user_id)  # Trace başlat
        TraceService.record_event(...)      # Event kaydet (sadece aktifse)
        TraceService.stop_trace()           # Trace durdur
    """

    _instance: Optional["TraceService"] = None
    _lock = threading.Lock()
    _thread_local = threading.local()

    # Session bazlı izolasyon
    _active_sessions: Dict[int, "TraceSessionContext"] = {}

    # Sinyaller
    signals: TraceServiceSignals = None

    # Timeout süresi (5 dakika)
    TIMEOUT_MS = 5 * 60 * 1000

    # Buffer boyutu (her N event'te DB'ye flush)
    BUFFER_SIZE = 50

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.signals = TraceServiceSignals()

    # ==================== PUBLIC API ====================

    @classmethod
    def start_trace(cls, user_id: int, reason: str = "manual") -> Optional[int]:
        """
        Trace oturumu başlat

        Args:
            user_id: Kullanıcı ID'si
            reason: Başlatma nedeni ("manual" veya "auto")

        Returns:
            session_id veya None (zaten aktifse)
        """
        instance = cls()

        # Zaten aktif session var mı?
        if user_id in cls._active_sessions:
            return None

        try:
            session = get_session()
            trace_session = TraceSession(
                user_id=user_id,
                started_at=datetime.utcnow(),
                status=TraceStatus.ACTIVE,
                trigger_reason=reason,
                total_events=0,
            )
            session.add(trace_session)
            session.commit()

            # Context oluştur
            context = TraceSessionContext(
                session_id=trace_session.id,
                user_id=user_id,
                started_at=trace_session.started_at,
            )

            # Timeout timer başlat
            context.start_timeout_timer(
                cls.TIMEOUT_MS, lambda: cls._on_timeout(user_id)
            )

            cls._active_sessions[user_id] = context

            # Yeni tracer'ları etkinleştir
            try:
                from modules.development.network_tracer import network_tracer
                from modules.development.log_tracer import log_tracer
                from modules.development.system_monitor import system_monitor

                from modules.development.message_box_tracer import message_box_tracer

                network_tracer.install()
                log_tracer.install()
                message_box_tracer.install()

                # Başlangıç snapshot'ı al
                system_monitor.record_snapshot(label="start")
            except Exception as e:
                print(f"[TraceService] Failed to activate additional tracers: {e}")

            if instance.signals:
                instance.signals.trace_started.emit(trace_session.id)

            return trace_session.id

        except Exception as e:
            print(f"[TraceService] start_trace error: {e}")
            return None

    @classmethod
    def stop_trace(
        cls,
        user_id: int = None,
        error_log_id: int = None,
        status: TraceStatus = TraceStatus.COMPLETED,
    ) -> Optional[TraceSession]:
        """
        Trace oturumunu durdur

        Args:
            user_id: Kullanıcı ID (None ise tüm aktif sessionlar)
            error_log_id: Hata log ID (hata ile sonlanıyorsa)
            status: Bitiş durumu

        Returns:
            TraceSession objesi
        """
        instance = cls()

        if user_id is None:
            # Tüm aktif sessionları bul (tek kullanıcı varsayımı)
            if not cls._active_sessions:
                return None
            user_id = next(iter(cls._active_sessions.keys()))

        context = cls._active_sessions.pop(user_id, None)
        if context is None:
            return None

        try:
            # Timeout timer'ı durdur
            context.stop_timeout_timer()

            # Buffer'ı flush et
            cls._flush_buffer(context)

            # Session'ı güncelle
            session = get_session()
            trace_session = session.query(TraceSession).get(context.session_id)
            if trace_session:
                trace_session.ended_at = datetime.utcnow()
                trace_session.status = status
                trace_session.total_events = context.event_count
                if error_log_id:
                    trace_session.error_log_id = error_log_id
                session.commit()

                if instance.signals:
                    instance.signals.trace_stopped.emit(trace_session.id)

                return trace_session

        except Exception as e:
            print(f"[TraceService] stop_trace error: {e}")

        return None

    @classmethod
    def record_event(
        cls,
        event_type: str,
        widget_name: str = None,
        widget_path: str = None,
        event_data: dict = None,
        duration_ms: int = None,
        user_id: int = None,
    ) -> bool:
        """
        Event kaydet (sadece trace aktifse)

        Args:
            event_type: Event tipi (page_navigation, button_click, vb.)
            widget_name: Widget adı
            widget_path: Widget yolu (breadcrumb)
            event_data: Event verisi (JSON)
            duration_ms: Süre (ms)
            user_id: Kullanıcı ID (None ise ilk aktif session)

        Returns:
            True kayıt başarılıysa
        """
        # Performans: Erken çıkış
        if not cls._active_sessions:
            return False

        # Recursion Guard: Trace işlemi sırasında event kaydını engelle
        if getattr(cls._thread_local, "suppressed", False):
            return False

        instance = cls()

        # User ID yoksa ilk aktif session'ı kullan
        if user_id is None:
            if not cls._active_sessions:
                return False
            user_id = next(iter(cls._active_sessions.keys()))

        context = cls._active_sessions.get(user_id)
        if context is None:
            return False

        try:
            # Hassas verileri maskele
            if event_data:
                event_data = mask_dict_values(event_data)

            # Event tipini enum'a çevir
            try:
                event_type_enum = TraceEventType(event_type)
            except ValueError:
                event_type_enum = TraceEventType.BUTTON_CLICK  # Fallback

            # Buffer'a ekle
            event = TraceEvent(
                session_id=context.session_id,
                event_type=event_type_enum,
                widget_name=widget_name,
                widget_path=widget_path,
                event_data=event_data,
                duration_ms=duration_ms,
                timestamp=datetime.utcnow(),
            )
            context.event_buffer.append(event)
            context.event_count += 1

            # Timeout'u sıfırla (aktivite var)
            context.reset_timeout()

            # Buffer doluysa flush et
            if len(context.event_buffer) >= cls.BUFFER_SIZE:
                cls._flush_buffer(context)

            if instance.signals:
                instance.signals.event_recorded.emit(event_type)

            return True

        except Exception as e:
            print(f"[TraceService] record_event error: {e}")
            return False

    @classmethod
    def is_active(cls, user_id: int = None) -> bool:
        """Trace aktif mi?"""
        if user_id is None:
            return bool(cls._active_sessions)
        return user_id in cls._active_sessions

    @classmethod
    def get_active_session_id(cls, user_id: int = None) -> Optional[int]:
        """Aktif session ID'sini döndür"""
        if user_id is None:
            if not cls._active_sessions:
                return None
            context = next(iter(cls._active_sessions.values()))
            return context.session_id
        context = cls._active_sessions.get(user_id)
        return context.session_id if context else None

    # ==================== PRIVATE METHODS ====================

    @classmethod
    def _flush_buffer(cls, context: "TraceSessionContext"):
        """
        Buffer'daki event'leri DB'ye yaz

        IMPORTANT: SQLAlchemy event listener icinde cagrilabilecegi icin
        ayri bir session kullaniyoruz (scoped session degil).
        Bu sayede ana islem ile cakisma olmaz.
        """
        if not context.event_buffer:
            return

        # Recursion Guard: Disable recording during flush
        if not hasattr(cls._thread_local, "suppressed"):
            cls._thread_local.suppressed = False

        cls._thread_local.suppressed = True

        # Ayri session olustur (scoped session ile cakismasin)
        trace_session = SASession(bind=get_engine())
        try:
            # Event data'ları JSON-serializable yap ve session'dan ayır
            for event in context.event_buffer:
                if event.event_data:
                    event.event_data = cls._sanitize_event_data(event.event_data)
                # Objeyi onceki session'lardan ayir (varsa)
                make_transient(event)
                trace_session.add(event)

            trace_session.commit()
            context.event_buffer.clear()
        except Exception as e:
            print(f"[TraceService] _flush_buffer error: {e}")
            try:
                trace_session.rollback()
            except Exception:
                pass
            context.event_buffer.clear()
        finally:
            trace_session.close()
            cls._thread_local.suppressed = False

    @classmethod
    def _sanitize_event_data(cls, data: Any) -> Any:
        """Event data'yı JSON-serializable yap"""
        from datetime import date, datetime
        from decimal import Decimal

        if data is None:
            return None

        if isinstance(data, dict):
            return {k: cls._sanitize_event_data(v) for k, v in data.items()}

        if isinstance(data, list):
            return [cls._sanitize_event_data(item) for item in data]

        if isinstance(data, datetime):
            return data.isoformat()

        if isinstance(data, date):
            return data.isoformat()

        if isinstance(data, Decimal):
            return float(data)

        if isinstance(data, (str, int, float, bool, type(None))):
            return data

        # Diğer tipler için string'e çevir
        return str(data)

    @classmethod
    def _on_timeout(cls, user_id: int):
        """Timeout callback"""
        instance = cls()
        print(f"[TraceService] Timeout for user {user_id}")
        cls.stop_trace(user_id=user_id, status=TraceStatus.TIMEOUT)
        if instance.signals:
            instance.signals.trace_timeout.emit(user_id)


class TraceSessionContext(QObject):
    """
    Aktif trace oturumu context'i

    QObject'ten türetildi çünkü QTimer main thread'de çalışmalı.
    """

    # Timeout sinyali (thread-safe)
    timeout_signal = pyqtSignal()

    def __init__(self, session_id: int, user_id: int, started_at: datetime):
        super().__init__()
        self.session_id = session_id
        self.user_id = user_id
        self.started_at = started_at
        self.event_buffer: List[TraceEvent] = []
        self.event_count = 0
        self._timeout_timer: Optional[QTimer] = None
        self._timeout_callback = None
        self._timeout_ms = 0

    def start_timeout_timer(self, timeout_ms: int, callback):
        """
        Timeout timer başlat

        Timer main thread'de oluşturulur ve çalışır.
        """
        self._timeout_ms = timeout_ms
        self._timeout_callback = callback

        # Sinyal bağlantısı (thread-safe)
        self.timeout_signal.connect(callback, Qt.ConnectionType.QueuedConnection)

        # Timer'ı oluştur - QTimer parent'ı olarak self kullan
        self._timeout_timer = QTimer(self)
        self._timeout_timer.setSingleShot(True)
        self._timeout_timer.timeout.connect(self._on_timer_timeout)
        self._timeout_timer.start(timeout_ms)

    def _on_timer_timeout(self):
        """Timer timeout olduğunda çağrılır"""
        self.timeout_signal.emit()

    def stop_timeout_timer(self):
        """Timeout timer durdur"""
        if self._timeout_timer:
            # Timer'ı güvenli şekilde durdur
            try:
                self._timeout_timer.stop()
                self._timeout_timer.deleteLater()
            except RuntimeError:
                # Timer zaten silinmişse
                pass
            self._timeout_timer = None

        # Sinyal bağlantısını kes
        try:
            if self._timeout_callback:
                self.timeout_signal.disconnect(self._timeout_callback)
        except (TypeError, RuntimeError):
            # Bağlantı zaten kesilmişse
            pass

    def reset_timeout(self):
        """Timeout'u sıfırla (aktivite var)"""
        if self._timeout_timer and self._timeout_timer.isActive():
            # Timer'ı yeniden başlat
            self._timeout_timer.stop()
            self._timeout_timer.start(self._timeout_ms)


# Module-level singleton instance
trace_service = TraceService()
