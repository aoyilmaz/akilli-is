"""
Akıllı İş - Log Tracer
Python standart logging modülü entegrasyonu
"""

import logging
from modules.development.trace_service import TraceService


class TraceLogHandler(logging.Handler):
    """
    Python logging modülü için handler

    Loglanan mesajları (INFO, WARNING, ERROR, vb.) yakalar ve
    trace sistemine 'log_entry' olarak kaydeder.
    """

    def __init__(self):
        super().__init__()
        self.setFormatter(logging.Formatter("%(name)s - %(message)s"))

    def emit(self, record):
        """Log kaydını işle"""
        # Sonsuz döngü koruması: Trace sistemi kendi loglarını kaydetmeye çalışmamalı
        # TraceService veya SQLAlchemy loglarını yoksayabiliriz gerekirse
        if not TraceService.is_active():
            return

        # Recursion Guard:
        # 1. SQLAlchemy loglarını yoksay (DB yazarken hata oluşursa loop başlar)
        # 2. Trace servisi ve development modülü loglarını yoksay
        if (
            record.name.startswith("sqlalchemy")
            or record.name.startswith("modules.development")
            or record.name.startswith("psycopg2")
        ):
            return

        try:
            msg = self.format(record)

            TraceService.record_event(
                event_type="log_entry",
                widget_name=record.name,  # Logger adı
                widget_path=record.funcName,
                event_data={
                    "level": record.levelname,
                    "message": msg,
                    "filename": record.filename,
                    "lineno": record.lineno,
                    "module": record.module,
                },
            )
        except Exception:
            self.handleError(record)


class LogTracer:
    """Log İzleyici Yöneticisi"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._handler = None
            cls._installed = False
        return cls._instance

    def install(self):
        """Handler'ı root logger'a ekle"""
        if self._installed:
            return

        self._handler = TraceLogHandler()
        # DEBUG seviyesi çok gürültülü olabilir, INFO ile başlayalım
        # Ancak kullanıcı uygulamasında DEBUG açıksa onu da yakalamak isteyebiliriz
        # Şimdilik handler'a seviye kısıtlaması koymuyoruz, root logger seviyesi geçerli

        logging.getLogger().addHandler(self._handler)
        self._installed = True
        print("[LogTracer] Log handler installed")

    def uninstall(self):
        """Handler'ı kaldır"""
        if not self._installed or not self._handler:
            return

        logging.getLogger().removeHandler(self._handler)
        self._handler = None
        self._installed = False
        print("[LogTracer] Log handler uninstalled")


# Singleton
log_tracer = LogTracer()
