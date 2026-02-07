"""
Akıllı İş - System Monitor
Sistem kaynak kullanımını izleyen modül (CPU, RAM)
"""

import threading
import platform
import os
from typing import Optional

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from modules.development.trace_service import TraceService


class SystemMonitor:
    """
    Sistem Kaynaklarını İzleyici

    Trace başladığında ve bittiğinde (veya periyodik olarak)
    CPU ve RAM kullanımını kaydeder.
    """

    _instance: Optional["SystemMonitor"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def get_stats(self) -> dict:
        """Anlık sistem istatistiklerini döndür"""
        stats = {
            "platform": platform.platform(),
            "python": platform.python_version(),
        }

        if PSUTIL_AVAILABLE:
            try:
                # CPU yüzdesi (son 1 saniye değil, anlık snapshot için interval=None veya 0)
                # interval=None non-blocking'dir
                stats["cpu_percent"] = psutil.cpu_percent(interval=None)

                # Bellek
                mem = psutil.virtual_memory()
                stats["memory_percent"] = mem.percent
                stats["memory_used_mb"] = round(mem.used / (1024 * 1024), 2)
                stats["memory_total_mb"] = round(mem.total / (1024 * 1024), 2)

                # Process'e özel (Uygulamanın kendi kullanımı)
                process = psutil.Process(os.getpid())
                stats["app_memory_mb"] = round(
                    process.memory_info().rss / (1024 * 1024), 2
                )
                stats["app_cpu_percent"] = round(process.cpu_percent(interval=None), 2)

            except Exception as e:
                stats["error"] = str(e)
        else:
            stats["warning"] = "psutil module not installed"

        return stats

    def record_snapshot(self, label: str = "snapshot"):
        """Sistem durumunu "system_stats" olarak kaydet"""
        if not TraceService.is_active():
            return

        stats = self.get_stats()
        stats["label"] = label

        TraceService.record_event(
            event_type="system_stats",
            widget_name="system",
            widget_path=platform.node(),  # Hostname
            event_data=stats,
        )


# Singleton
system_monitor = SystemMonitor()
