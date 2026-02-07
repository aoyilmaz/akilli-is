"""
Akıllı İş - SQL Tracer
SQLAlchemy engine-level SQL izleyici

Kaydeder:
- Raw SQL sorguları
- Bind parametreleri (hassas veriler maskelenmiş)
- Çalışma süreleri
- Dönen satır sayıları

Performans:
- Trace kapalıyken overhead: ~0 (sadece boolean check)
- Trace açıkken: ~0.2ms overhead per query
"""

import time
from typing import Dict, Optional, Any
import threading

from sqlalchemy import event

from modules.development.trace_service import TraceService


# Hassas parametre pattern'leri
SENSITIVE_PARAM_PATTERNS = ['password', 'token', 'secret', 'credit', 'cvv', 'api_key']


class SQLTracer:
    """
    SQLAlchemy Engine-Level SQL İzleyici (Singleton)

    Engine event'lerine bağlanarak tüm SQL sorgularını yakalar.
    """

    _instance: Optional['SQLTracer'] = None
    _lock = threading.Lock()

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
        self._enabled = False
        self._listeners_registered = False
        # Thread-safe query timing storage
        self._query_start_times: Dict[int, float] = {}
        self._times_lock = threading.Lock()

    def init_listeners(self, engine=None):
        """
        Engine event listener'larını kaydet

        Args:
            engine: SQLAlchemy engine (None ise get_engine() kullanılır)
        """
        if self._listeners_registered:
            return

        if engine is None:
            from database.base import get_engine
            engine = get_engine()

        event.listen(engine, "before_cursor_execute", self._before_execute)
        event.listen(engine, "after_cursor_execute", self._after_execute)
        self._listeners_registered = True
        print("[SQLTracer] Listeners registered on engine")

    def enable(self):
        """SQL tracing'i etkinleştir"""
        self._enabled = True

    def disable(self):
        """SQL tracing'i devre dışı bırak"""
        self._enabled = False

    def is_enabled(self) -> bool:
        """SQL tracing etkin mi?"""
        return self._enabled

    def _before_execute(self, conn, cursor, statement, parameters, context, executemany):
        """
        SQL sorgusu çalıştırılmadan önce

        Sorgu başlangıç zamanını kaydet.
        """
        # PERFORMANS: Erken çıkış
        if not self._enabled or not TraceService.is_active():
            return

        cursor_id = id(cursor)
        with self._times_lock:
            self._query_start_times[cursor_id] = time.perf_counter()

    def _after_execute(self, conn, cursor, statement, parameters, context, executemany):
        """
        SQL sorgusu çalıştırıldıktan sonra

        Süreyi hesapla ve event kaydet.
        """
        # PERFORMANS: Erken çıkış
        if not self._enabled or not TraceService.is_active():
            return

        cursor_id = id(cursor)

        # Başlangıç zamanını al
        with self._times_lock:
            start_time = self._query_start_times.pop(cursor_id, None)

        if start_time is None:
            duration_ms = 0
        else:
            duration_ms = (time.perf_counter() - start_time) * 1000

        # Satır sayısını al
        try:
            row_count = cursor.rowcount if cursor.rowcount >= 0 else None
        except Exception:
            row_count = None

        # Event kaydet
        TraceService.record_event(
            event_type="sql_query",
            widget_name="database",
            event_data={
                "sql": self._truncate_sql(statement),
                "params": self._safe_params(parameters),
                "duration_ms": round(duration_ms, 2),
                "row_count": row_count,
                "operation": self._get_operation(statement),
                "executemany": executemany
            },
            duration_ms=int(duration_ms)
        )

    def _truncate_sql(self, sql: str, max_length: int = 2000) -> str:
        """
        SQL sorgusunu kısalt

        Args:
            sql: SQL sorgusu
            max_length: Maksimum karakter sayısı (varsayılan: 2000)

        Returns:
            Kısaltılmış SQL veya orijinal
        """
        if sql is None:
            return ""
        sql = str(sql)
        if len(sql) > max_length:
            truncated = len(sql) - max_length
            return sql[:max_length] + f"... [{truncated} chars truncated]"
        return sql

    def _safe_params(self, params: Any) -> Any:
        """
        Parametreleri güvenli formata çevir

        Hassas değerler maskelenir, büyük değerler kısaltılır.
        """
        if params is None:
            return None

        if isinstance(params, dict):
            return {k: self._mask_value(k, v) for k, v in params.items()}

        if isinstance(params, (list, tuple)):
            # Çok fazla parametre varsa kısalt
            if len(params) > 20:
                return f"[{len(params)} parameters]"
            return [self._mask_value(f"param_{i}", v) for i, v in enumerate(params)]

        return str(params)[:500]

    def _mask_value(self, key: str, value: Any) -> Any:
        """
        Hassas değerleri maskele ve JSON-serializable yap

        Args:
            key: Parametre adı
            value: Parametre değeri

        Returns:
            Maskelenmiş veya orijinal değer (JSON-serializable)
        """
        from datetime import date, datetime
        from decimal import Decimal

        key_lower = str(key).lower()

        # Hassas parametre kontrolü
        for pattern in SENSITIVE_PARAM_PATTERNS:
            if pattern in key_lower:
                return '***MASKED***'

        # None kontrolü
        if value is None:
            return None

        # date/datetime objelerini string'e çevir
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()

        # Decimal'ı float'a çevir
        if isinstance(value, Decimal):
            return float(value)

        # Değer çok büyükse kısalt
        if isinstance(value, str) and len(value) > 200:
            return value[:200] + "..."

        if isinstance(value, bytes) and len(value) > 100:
            return f"<bytes len={len(value)}>"

        # Diğer JSON-serializable olmayan tipler için string'e çevir
        if not isinstance(value, (str, int, float, bool, list, dict, type(None))):
            return str(value)

        return value

    def _get_operation(self, sql: str) -> str:
        """
        SQL işlem tipini belirle

        Returns:
            SELECT, INSERT, UPDATE, DELETE veya OTHER
        """
        if sql is None:
            return "OTHER"

        sql_upper = str(sql).strip().upper()

        if sql_upper.startswith('SELECT'):
            return 'SELECT'
        elif sql_upper.startswith('INSERT'):
            return 'INSERT'
        elif sql_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif sql_upper.startswith('DELETE'):
            return 'DELETE'
        elif sql_upper.startswith('BEGIN'):
            return 'BEGIN'
        elif sql_upper.startswith('COMMIT'):
            return 'COMMIT'
        elif sql_upper.startswith('ROLLBACK'):
            return 'ROLLBACK'
        else:
            return 'OTHER'


# Module-level singleton
sql_tracer = SQLTracer()
