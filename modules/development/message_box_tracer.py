"""
Akıllı İş - Message Box Tracer
QMessageBox kullanımlarını yakalayan modül
"""

import threading
from typing import Optional
from PyQt6.QtWidgets import QMessageBox

from modules.development.trace_service import TraceService


class MessageBoxTracer:
    """
    QMessageBox Interceptor

    QMessageBox'ın statik metodlarını (information, warning, critical, question)
    patch'leyerek kullanıcıya gösterilen uyarıları loglar.
    """

    _instance: Optional["MessageBoxTracer"] = None
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
        self._patched = False
        self._originals = {}

    def install(self):
        """QMessageBox metodlarını patch'le"""
        if self._patched:
            return

        # Orijinal metodları sakla
        self._originals["information"] = QMessageBox.information
        self._originals["warning"] = QMessageBox.warning
        self._originals["critical"] = QMessageBox.critical
        self._originals["question"] = QMessageBox.question

        # Patch'leri uygula (class method oldukları için direkt class üzerinden)
        QMessageBox.information = self._make_wrapper(
            "information", self._originals["information"]
        )
        QMessageBox.warning = self._make_wrapper("warning", self._originals["warning"])
        QMessageBox.critical = self._make_wrapper(
            "critical", self._originals["critical"]
        )
        QMessageBox.question = self._make_wrapper(
            "question", self._originals["question"]
        )

        self._patched = True
        print("[MessageBoxTracer] Installed on QMessageBox")

    def uninstall(self):
        """Patch'leri kaldır ve orijinalleri geri yükle"""
        if not self._patched:
            return

        QMessageBox.information = self._originals["information"]
        QMessageBox.warning = self._originals["warning"]
        QMessageBox.critical = self._originals["critical"]
        QMessageBox.question = self._originals["question"]

        self._originals.clear()
        self._patched = False
        print("[MessageBoxTracer] Uninstalled")

    def _make_wrapper(self, level, original_func):
        """Wrapper fonksiyon oluşturucu"""

        def wrapper(parent, title, text, *args, **kwargs):
            # Trace aktif değilse direkt çalıştır
            if not TraceService.is_active():
                return original_func(parent, title, text, *args, **kwargs)

            # Logla
            try:
                TraceService.record_event(
                    event_type="log_entry",  # UI dialog, ama log gibi düşünülebilir
                    widget_name="QMessageBox",
                    widget_path=str(parent.__class__.__name__) if parent else "None",
                    event_data={
                        "type": "message_box",
                        "level": level,
                        "title": title,
                        "message": text,
                    },
                )
            except Exception:
                pass

            # Orijinali çağır
            return original_func(parent, title, text, *args, **kwargs)

        return wrapper


# Singleton oluştur
message_box_tracer = MessageBoxTracer()
