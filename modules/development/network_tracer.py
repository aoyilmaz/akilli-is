"""
Akıllı İş - Network Tracer
HTTP isteklerini izleyen modül (requests kütüphanesi için)
"""

import time
import threading
from typing import Optional
from urllib.parse import urlparse

try:
    import requests
    from requests.adapters import HTTPAdapter

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None

from modules.development.trace_service import TraceService, mask_sensitive_data


class NetworkTracer:
    """
    Requests kütüphanesi için Network İzleyici

    Tüm giden HTTP isteklerini yakalar ve trace sistemine kaydeder.
    """

    _instance: Optional["NetworkTracer"] = None
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
        self._original_request = None

    def install(self):
        """Requests kütüphanesini patch'le"""
        if not REQUESTS_AVAILABLE or self._patched:
            return

        # Session.request metodunu patch'le
        # Bu metod tüm HTTP metodları (get, post, put, delete) tarafından kullanılır
        self._original_request = requests.Session.request
        requests.Session.request = self._patched_request

        self._patched = True
        print("[NetworkTracer] Installed on requests.Session")

    def uninstall(self):
        """Patch'i kaldır"""
        if not self._patched or not self._original_request:
            return

        requests.Session.request = self._original_request
        self._patched = False
        print("[NetworkTracer] Uninstalled")

    def _patched_request(self_session, method, url, *args, **kwargs):
        """Patch'lenmiş request metodu"""
        # Tracer instance'ına erişim (self değil, class instance)
        tracer = NetworkTracer()

        # Trace aktif değilse direkt çalıştır
        if not TraceService.is_active():
            return tracer._original_request(self_session, method, url, *args, **kwargs)

        start_time = time.perf_counter()
        status_code = 0
        response_size = 0
        error_msg = None

        try:
            # İsteği gerçekleştir
            response = tracer._original_request(
                self_session, method, url, *args, **kwargs
            )
            status_code = response.status_code
            response_size = len(response.content)
            return response

        except Exception as e:
            error_msg = str(e)
            raise

        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Domain bilgisini çıkar
            try:
                parsed = urlparse(url)
                domain = parsed.netloc
                path = parsed.path
            except:
                domain = "unknown"
                path = url

            # Parametreleri ve headerları özetle
            params_summary = {}
            if "params" in kwargs:
                params_summary["params"] = kwargs["params"]
            if "json" in kwargs:
                # JSON verisi büyük olabilir veya hassas veri içerebilir
                # Sadece key'leri veya özet bilgiyi alabiliriz
                # Şimdilik basitçe maskeleyip alalım
                from modules.development.trace_service import mask_dict_values

                if isinstance(kwargs["json"], dict):
                    params_summary["json"] = mask_dict_values(kwargs["json"])
                else:
                    params_summary["json"] = "Blob/Array Data"

            TraceService.record_event(
                event_type="network_request",
                widget_name=domain,
                widget_path=path,
                event_data={
                    "method": method.upper(),
                    "url": url,
                    "status_code": status_code,
                    "response_size_bytes": response_size,
                    "duration_ms": round(duration_ms, 2),
                    "error": error_msg,
                    "request_details": params_summary,
                },
                duration_ms=int(duration_ms),
            )


# Singleton oluştur
network_tracer = NetworkTracer()
