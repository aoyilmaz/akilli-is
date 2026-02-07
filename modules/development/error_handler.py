"""
Akıllı İş - Merkezi Hata Yönetimi
Rich ile renkli konsol çıktısı ve database kaydı
"""

import sys
import traceback
import platform
from typing import Optional
from datetime import datetime

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.traceback import Traceback as RichTraceback

    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    Console = None
    Panel = None
    RichTraceback = None
    RICH_AVAILABLE = False
    console = None

try:
    from PyQt6.QtWidgets import QMessageBox
except ImportError:
    QMessageBox = None

from modules.development.services import ErrorLogService
from database.models.development import ErrorSeverity, TraceStatus


class ErrorHandler:
    """
    Merkezi Hata Yönetimi Sınıfı

    Özellikler:
    - Tüm exception'ları yakalar ve loglar
    - Rich ile renkli terminal çıktısı
    - Database'e detaylı kayıt
    - Opsiyonel QMessageBox popup
    - User context tracking
    """

    _current_user = None  # Login olunca set edilecek

    @classmethod
    def set_current_user(cls, user):
        """
        Login olunca çağrılacak
        Main window'da login başarılı olduğunda:
        ErrorHandler.set_current_user(user)
        """
        cls._current_user = user

    @classmethod
    def handle_error(
        cls,
        exception: Exception,
        module: str,
        screen: str,
        function: str,
        show_message: bool = True,
        severity: str = "error",
        parent_widget=None,
    ) -> Optional["ErrorLog"]:
        """
        Tüm hataları yönetir

        Args:
            exception: Yakalanan exception
            module: 'inventory', 'production', 'purchasing', etc.
            screen: 'WarehouseModule', 'WorkOrderModule', etc.
            function: '_save_warehouse', '_delete_item', etc.
            show_message: QMessageBox göster mi?
            severity: 'critical', 'error', 'warning', 'info'
            parent_widget: QMessageBox parent'ı

        Returns:
            ErrorLog instance (database'e kaydedilmiş)

        Örnek Kullanım:
            try:
                self.service.save(data)
            except Exception as e:
                ErrorHandler.handle_error(
                    e, 'inventory', 'WarehouseModule', '_save_warehouse',
                    parent_widget=self
                )
        """

        # 1. Traceback bilgisini al
        tb = traceback.extract_tb(exception.__traceback__)
        tb_str = "".join(
            traceback.format_exception(
                type(exception), exception, exception.__traceback__
            )
        )

        # Dosya ve satır bilgisi
        if tb:
            last_frame = tb[-1]
            file_path = last_frame.filename
            line_number = last_frame.lineno
        else:
            file_path = None
            line_number = None

        # 2. Console'a RICH ile yaz (RENKLI + GÜZEL)
        cls._log_to_console(exception, module, screen, function, severity, tb_str)

        # 3. Database'e kaydet (DETAYLI)
        error_log = cls._log_to_database(
            exception,
            module,
            screen,
            function,
            severity,
            tb_str,
            file_path,
            line_number,
        )

        # 4. QMessageBox göster (isteğe bağlı)
        if show_message and QMessageBox:
            cls._show_message_box(exception, severity, parent_widget)

        # 5. Trace aktifse otomatik durdur ve admin'e bildir
        cls._handle_trace_on_error(error_log, module, screen, tb_str, exception)

        return error_log

    @classmethod
    def _handle_trace_on_error(cls, error_log, module: str, screen: str,
                               traceback_str: str = None, exception: Exception = None):
        """
        Hata alındığında trace'i otomatik durdur ve admin'e bildir

        Args:
            error_log: ErrorLog kaydı
            module: Modül adı
            screen: Ekran adı
            traceback_str: Tam traceback string'i
            exception: Yakalanan exception objesi
        """
        try:
            from modules.development.trace_service import TraceService

            if not TraceService.is_active():
                return

            # ÖNCELİKLE: Hata event'ini kaydet (stop_trace buffer'ı flush edecek)
            if traceback_str or exception:
                TraceService.record_event(
                    event_type="error_occurred",
                    widget_name="exception",
                    widget_path=f"{module} > {screen}",
                    event_data={
                        "exception_type": type(exception).__name__ if exception else "Unknown",
                        "error_message": str(exception) if exception else "",
                        "traceback": traceback_str or "",
                        "module": module,
                        "screen": screen,
                        "error_log_id": error_log.id if error_log else None
                    }
                )

            # Trace'i hata durumu ile durdur
            error_log_id = error_log.id if error_log else None
            trace_session = TraceService.stop_trace(
                error_log_id=error_log_id,
                status=TraceStatus.ERROR
            )

            if trace_session:
                # Admin'e notification gönder
                cls._send_trace_notification(trace_session, module, screen)

        except Exception as e:
            # Trace işlemi başarısız olsa bile ana hata akışını bozma
            print(f"[ErrorHandler] Trace handling failed: {e}")

    @classmethod
    def _send_trace_notification(cls, trace_session, module: str, screen: str):
        """Trace raporu hazır bildirimi gönder"""
        try:
            from modules.system.services.notification_service import NotificationService

            username = "Bilinmeyen"
            if cls._current_user:
                username = cls._current_user.username

            NotificationService.create_admin_notification(
                title="Trace Raporu Hazir",
                message=f"{username} kullanicisi {screen} ekraninda hata aldi",
                link=f"development/trace-viewer/{trace_session.id}",
                notification_type="action_required"
            )
        except ImportError:
            # NotificationService henüz mevcut değilse sessizce geç
            print(f"[ErrorHandler] Trace session {trace_session.id} completed (notification service not available)")
        except Exception as e:
            print(f"[ErrorHandler] Notification failed: {e}")

    @classmethod
    def _log_to_console(cls, exception, module, screen, function, severity, tb_str):
        """Console'a hata yazdır (Rich varsa renkli, yoksa plain)"""

        # Severity'ye göre emoji
        severity_config = {
            "critical": {"emoji": "🔴"},
            "error": {"emoji": "🔴"},
            "warning": {"emoji": "🟡"},
            "info": {"emoji": "🔵"},
        }
        config = severity_config.get(severity, severity_config["error"])

        # Kullanıcı bilgisi
        user_info = "N/A"
        if cls._current_user:
            user_info = f"{cls._current_user.username} (ID: {cls._current_user.id})"

        if RICH_AVAILABLE and console:
            # Rich ile renkli output
            title = f"{config['emoji']} {severity.upper()}: {type(exception).__name__}"
            content_lines = [
                f"[bold cyan]Module:[/bold cyan] {module}",
                f"[bold cyan]Screen:[/bold cyan] {screen}",
                f"[bold cyan]Function:[/bold cyan] {function}",
                f"[bold cyan]Time:[/bold cyan] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"[bold cyan]User:[/bold cyan] {user_info}",
                "",
                "[bold red]Error Message:[/bold red]",
                str(exception),
            ]
            content = "\n".join(content_lines)

            console.print()
            console.print(
                Panel(
                    content,
                    title=title,
                    border_style=(
                        "red" if severity in ["critical", "error"] else "yellow"
                    ),
                    expand=False,
                )
            )

            console.print("[bold]Full Traceback:[/bold]")
            try:
                console.print(
                    RichTraceback.from_exception(
                        type(exception),
                        exception,
                        exception.__traceback__,
                        show_locals=False,
                    )
                )
            except:
                console.print(tb_str)
            console.print()
        else:
            # Plain text output (Rich yok)
            print(f"\n{'='*60}")
            print(f"{config['emoji']} {severity.upper()}: {type(exception).__name__}")
            print(f"{'='*60}")
            print(f"Module: {module}")
            print(f"Screen: {screen}")
            print(f"Function: {function}")
            print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"User: {user_info}")
            print(f"\nError Message:")
            print(f"  {exception}")
            print(f"\nFull Traceback:")
            print(tb_str)
            print(f"{'='*60}\n")

    @classmethod
    def _log_to_database(
        cls,
        exception,
        module,
        screen,
        function,
        severity,
        tb_str,
        file_path,
        line_number,
    ):
        """Database'e DETAYLI kayıt"""

        try:
            service = ErrorLogService()

            # Severity enum'a çevir (lowercase)
            severity_lower = severity.lower() if severity else "error"
            severity_map = {
                "critical": ErrorSeverity.CRITICAL,
                "error": ErrorSeverity.ERROR,
                "warning": ErrorSeverity.WARNING,
                "info": ErrorSeverity.INFO,
            }
            severity_enum = severity_map.get(severity_lower, ErrorSeverity.ERROR)

            # User bilgisi
            user_id = cls._current_user.id if cls._current_user else None
            username = cls._current_user.username if cls._current_user else "system"

            # ErrorLog oluştur
            error_log = service.create(
                user_id=user_id,
                username=username,
                error_type=type(exception).__name__,
                error_message=str(exception),
                error_traceback=tb_str,
                error_args=str(exception.args) if exception.args else None,
                module_name=module,
                screen_name=screen,
                function_name=function,
                file_path=file_path,
                line_number=line_number,
                python_version=platform.python_version(),
                os_info=f"{platform.system()} {platform.release()}",
                severity=severity_lower,  # String value, not enum
            )

            return error_log

        except Exception as db_error:
            # Database kayıt hatası durumunda sadece console'a yaz
            if console:
                console.print(
                    f"[bold red]Database logging failed:[/bold red] {db_error}"
                )
            else:
                print(f"Database logging failed: {db_error}")
            return None

    @classmethod
    def log_error(cls, exception: Exception, location: str, show_message: bool = False):
        """
        Basit hata loglama metodu

        Args:
            exception: Yakalanan exception
            location: Hata konumu (ör: "SalesQuoteModule._save_quote")
            show_message: QMessageBox göster mi? (default: False)

        Kullanım:
            ErrorHandler.log_error(e, "SalesQuoteModule._save_quote")
        """
        # location'ı parçala: "SalesQuoteModule._save_quote"
        # -> module="sales", screen="SalesQuoteModule", function="_save_quote"
        parts = location.rsplit(".", 1)
        if len(parts) == 2:
            screen = parts[0]
            function = parts[1]
        else:
            screen = location
            function = "unknown"

        # Module adını tahmin et
        module_map = {
            "SalesQuote": "sales",
            "SalesOrder": "sales",
            "DeliveryNote": "sales",
            "Invoice": "sales",
            "Customer": "sales",
            "Warehouse": "inventory",
            "Item": "inventory",
            "Stock": "inventory",
            "Unit": "inventory",
            "PurchaseRequest": "purchasing",
            "PurchaseOrder": "purchasing",
            "GoodsReceipt": "purchasing",
            "Supplier": "purchasing",
            "WorkOrder": "production",
            "BOM": "production",
            "Error": "development",
        }

        module = "unknown"
        for key, value in module_map.items():
            if key in screen:
                module = value
                break

        return cls.handle_error(
            exception,
            module,
            screen,
            function,
            show_message=show_message,
            severity="error",
        )

    @classmethod
    def _show_message_box(cls, exception, severity, parent):
        """QMessageBox göster"""

        if not QMessageBox:
            return

        title_map = {
            "critical": "Kritik Hata",
            "error": "Hata",
            "warning": "Uyarı",
            "info": "Bilgi",
        }
        title = title_map.get(severity, "Hata")

        message = f"{type(exception).__name__}: {str(exception)}"

        try:
            if severity in ["critical", "error"]:
                QMessageBox.critical(parent, title, message)
            elif severity == "warning":
                QMessageBox.warning(parent, title, message)
            else:
                QMessageBox.information(parent, title, message)
        except Exception as msg_error:
            # QMessageBox hatası durumunda sadece console'a yaz
            console.print(f"[bold yellow]QMessageBox failed:[/bold yellow] {msg_error}")


# Convenience function
def log_error(exception: Exception, module: str, screen: str, function: str, **kwargs):
    """
    Kısayol fonksiyon

    Kullanım:
        from modules.development.error_handler import log_error

        try:
            ...
        except Exception as e:
            log_error(e, 'inventory', 'WarehouseModule', '_save')
    """
    return ErrorHandler.handle_error(exception, module, screen, function, **kwargs)
