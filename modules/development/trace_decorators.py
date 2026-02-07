"""
Akıllı İş - Trace Decorators
Servis metodlarını izlemek için decorator'lar

Kullanım:
    from modules.development.trace_decorators import traced_method

    class CustomerService:
        @traced_method
        def create(self, **kwargs):
            ...
"""

import functools
import time
from typing import Any, Callable

from modules.development.trace_service import TraceService


def _summarize_result(result: Any) -> str:
    """
    Sonucu özet olarak döndür (tüm veriyi loglamadan)

    Örnekler:
        None -> "None"
        [item1, item2, ...] -> "List[15 items]"
        Customer(id=42) -> "Customer(id=42)"
        "string" -> "str(len=10)"
    """
    if result is None:
        return "None"

    if isinstance(result, list):
        return f"List[{len(result)} items]"

    if isinstance(result, dict):
        return f"Dict[{len(result)} keys]"

    if isinstance(result, tuple):
        return f"Tuple[{len(result)} items]"

    if isinstance(result, set):
        return f"Set[{len(result)} items]"

    if isinstance(result, str):
        return f"str(len={len(result)})"

    if isinstance(result, (int, float, bool)):
        return str(result)

    # ORM model objesi
    if hasattr(result, 'id'):
        return f"{type(result).__name__}(id={result.id})"

    # Diğer objeler
    return type(result).__name__


def _summarize_params(args: tuple, kwargs: dict) -> dict:
    """
    Parametreleri özet olarak döndür

    ORM objeleri için sadece id'yi al, büyük verileri kısalt
    """
    summary = {}

    # args (self hariç)
    if len(args) > 1:
        arg_summaries = []
        for arg in args[1:]:  # self'i atla
            if hasattr(arg, 'id'):
                arg_summaries.append(f"{type(arg).__name__}(id={arg.id})")
            elif isinstance(arg, (list, dict, tuple, set)):
                arg_summaries.append(f"{type(arg).__name__}[{len(arg)}]")
            elif isinstance(arg, str) and len(arg) > 100:
                arg_summaries.append(f"str(len={len(arg)})")
            else:
                arg_summaries.append(str(arg)[:50])
        if arg_summaries:
            summary["args"] = arg_summaries

    # kwargs
    if kwargs:
        kwarg_summary = {}
        for k, v in kwargs.items():
            if hasattr(v, 'id'):
                kwarg_summary[k] = f"{type(v).__name__}(id={v.id})"
            elif isinstance(v, (list, dict, tuple, set)):
                kwarg_summary[k] = f"{type(v).__name__}[{len(v)}]"
            elif isinstance(v, str) and len(v) > 100:
                kwarg_summary[k] = f"str(len={len(v)})"
            else:
                kwarg_summary[k] = str(v)[:50]
        summary["kwargs"] = kwarg_summary

    return summary


def traced_method(func: Callable) -> Callable:
    """
    Servis metodlarını izleyen decorator

    Kaydeder:
    - Metod adı (ClassName.method_name)
    - Parametreler (özet)
    - Çalışma süresi (ms)
    - Dönüş değeri (özet)
    - Hata durumu

    Performans:
    - Trace kapalıyken overhead: ~0 (sadece boolean check)
    - Trace açıkken: ~0.1ms overhead (time.perf_counter + dict oluşturma)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # PERFORMANS: Erken çıkış
        if not TraceService.is_active():
            return func(*args, **kwargs)

        # Metod adını oluştur
        if args and hasattr(args[0], '__class__'):
            method_name = f"{args[0].__class__.__name__}.{func.__name__}"
        else:
            method_name = func.__name__

        # Parametreleri özetle
        params = _summarize_params(args, kwargs)

        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            duration_ms = (time.perf_counter() - start_time) * 1000

            TraceService.record_event(
                event_type="method_call",
                widget_name=method_name,
                event_data={
                    "params": params,
                    "duration_ms": round(duration_ms, 2),
                    "return_type": type(result).__name__,
                    "return_summary": _summarize_result(result),
                    "status": "success"
                },
                duration_ms=int(duration_ms)
            )
            return result

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000

            TraceService.record_event(
                event_type="method_call",
                widget_name=method_name,
                event_data={
                    "params": params,
                    "duration_ms": round(duration_ms, 2),
                    "status": "error",
                    "error_type": type(e).__name__,
                    "error_message": str(e)[:200]
                },
                duration_ms=int(duration_ms)
            )
            raise

    return wrapper


def traced_class(cls):
    """
    Sınıftaki tüm public metodları trace et

    Kullanım:
        @traced_class
        class CustomerService:
            def create(self, **kwargs):
                ...
            def update(self, id, **kwargs):
                ...
    """
    for name, method in cls.__dict__.items():
        # Private metodları (_) ve magic metodları (__) atla
        if name.startswith('_'):
            continue
        # Sadece callable'ları wrap et
        if callable(method):
            setattr(cls, name, traced_method(method))
    return cls
