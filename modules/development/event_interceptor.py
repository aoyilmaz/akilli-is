"""
Akıllı İş - Event Interceptor
Qt Event Filter ile global UI event yakalama

Performans garantisi:
- Trace kapalıyken sadece boolean check (~0 overhead)
- Trace açıkken bile lightweight processing

Backend Slot Detection:
- pyqtBoundSignal.connect patch'i ile gerçek fonksiyon adları yakalanır
- Patch modül import edildiğinde uygulanır (widget init öncesi)
"""

import inspect
import re
import linecache
from typing import Optional, Callable

from PyQt6.QtCore import QObject, QEvent, pyqtBoundSignal
from PyQt6.QtWidgets import (
    QApplication,
    QPushButton,
    QToolButton,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QDateEdit,
    QCheckBox,
    QRadioButton,
    QTextEdit,
    QPlainTextEdit,
    QTableWidget,
    QTreeWidget,
    QListWidget,
)

from modules.development.trace_service import TraceService, mask_sensitive_data


# ==================== SLOT DETECTION PATCH ====================

# Orijinal connect metodunu sakla
_original_signal_connect = pyqtBoundSignal.connect


def _resolve_slot_name(slot_callable) -> str:
    """
    Slot callable'dan fonksiyon adını çıkar

    Args:
        slot_callable: Signal'e bağlanan callable

    Returns:
        "ClassName.method_name" formatında string
    """
    try:
        if hasattr(slot_callable, "__func__"):
            # Bound method: self.method
            func = slot_callable.__func__
            cls_name = slot_callable.__self__.__class__.__name__
            return f"{cls_name}.{func.__name__}"
        elif hasattr(slot_callable, "__name__"):
            # Regular function veya lambda
            return slot_callable.__qualname__
        else:
            # Partial veya diğer callable'lar
            return "<callable>"
    except Exception:
        return "<unknown>"


def _patched_signal_connect(self, slot, *args, **kwargs):
    """
    pyqtBoundSignal.connect için patch

    Connect çağrıldığında slot adını widget property'sine kaydeder.
    Bu sayede tıklama anında hangi fonksiyonun çağrılacağı bilinir.

    Performans:
    - Cold path (widget init): ~10µs per connect
    - Hot path (click): 0 overhead (property zaten kayıtlı)
    """
    # Önce orijinal connect'i çağır (hata durumunda bile çalışsın)
    result = _original_signal_connect(self, slot, *args, **kwargs)

    try:
        # Hangi widget'a bağlı olduğunu bul
        frame = inspect.currentframe().f_back
        if frame is None:
            return result

        source_line = linecache.getline(
            frame.f_code.co_filename, frame.f_lineno
        ).strip()

        # "self.btn.clicked.connect(...)" veya "btn.clicked.connect(...)" pattern'i
        # clicked, pressed, toggled, triggered gibi sinyalleri yakala
        patterns = [
            r"(self\.\w+)\.(?:clicked|pressed|toggled|triggered|activated)\.connect",
            r"(\w+)\.(?:clicked|pressed|toggled|triggered|activated)\.connect",
        ]

        widget = None
        for pattern in patterns:
            match = re.match(pattern, source_line)
            if match:
                widget_expr = match.group(1)
                try:
                    widget = eval(widget_expr, frame.f_globals, frame.f_locals)
                    break
                except Exception:
                    continue

        if widget is not None and hasattr(widget, "setProperty"):
            # Mevcut slot listesini al veya oluştur
            existing = widget.property("_trace_slots")
            if existing is None:
                existing = []
            elif isinstance(existing, str):
                existing = [existing]

            slot_name = _resolve_slot_name(slot)
            if slot_name not in existing:
                existing.append(slot_name)

            widget.setProperty("_trace_slots", existing)

    except Exception:
        # Hata durumunda sessizce geç - connect çalışmaya devam etsin
        pass

    return result


# Patch'i uygula (modül import edildiğinde, widget'lar oluşturulmadan önce)
pyqtBoundSignal.connect = _patched_signal_connect


class TraceEventFilter(QObject):
    """
    Global Qt Event Filter

    QApplication'a install edildiğinde tüm widget event'lerini yakalar.
    Sadece trace aktifken işlem yapar.
    """

    _instance: Optional["TraceEventFilter"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._initialized = True
        self._breadcrumb_provider: Optional[Callable] = None
        self._installed = False

    def install(self, app: QApplication = None):
        """Event filter'ı QApplication'a install et"""
        if self._installed:
            return

        if app is None:
            app = QApplication.instance()

        if app:
            app.installEventFilter(self)
            self._installed = True
            print("[TraceEventFilter] Installed on QApplication")

    def uninstall(self, app: QApplication = None):
        """Event filter'ı kaldır"""
        if not self._installed:
            return

        if app is None:
            app = QApplication.instance()

        if app:
            app.removeEventFilter(self)
            self._installed = False
            print("[TraceEventFilter] Removed from QApplication")

    def set_breadcrumb_provider(self, provider: Callable):
        """
        Breadcrumb provider fonksiyonu ayarla

        Args:
            provider: () -> str şeklinde fonksiyon
        """
        self._breadcrumb_provider = provider

    def _get_breadcrumb(self) -> str:
        """Mevcut breadcrumb'ı al"""
        if self._breadcrumb_provider:
            try:
                return self._breadcrumb_provider()
            except Exception:
                pass
        return ""

    def _get_widget_name(self, widget: QObject) -> str:
        """Widget adını al"""
        name = widget.objectName()
        if name:
            return name
        return widget.__class__.__name__

    def _get_connected_slot(self, button: QPushButton) -> str:
        """
        Butona bağlı slot'un adını al

        pyqtBoundSignal.connect patch'i sayesinde slot adları
        widget property'si olarak saklanır.

        QDialogButtonBox butonları için özel handling:
        - Qt dahili bağlantıları patch'e takılmaz
        - Bu durumda buton rolü + dialog sınıfı gösterilir

        Returns:
            "ClassName.method_name" veya birden fazla slot varsa
            "ClassName.method1, ClassName.method2"
        """
        try:
            # Patch tarafından kaydedilen slot adlarını kontrol et
            slots = button.property("_trace_slots")
            if slots:
                if isinstance(slots, list):
                    return ", ".join(slots)
                return str(slots)

            # QDialogButtonBox kontrolü
            from PyQt6.QtWidgets import QDialogButtonBox, QDialog

            parent = button.parent()
            if parent and isinstance(parent, QDialogButtonBox):
                # Buton rolünü al
                role = parent.buttonRole(button)
                role_names = {
                    QDialogButtonBox.ButtonRole.AcceptRole: "accept",
                    QDialogButtonBox.ButtonRole.RejectRole: "reject",
                    QDialogButtonBox.ButtonRole.ApplyRole: "apply",
                    QDialogButtonBox.ButtonRole.ResetRole: "reset",
                    QDialogButtonBox.ButtonRole.HelpRole: "help",
                    QDialogButtonBox.ButtonRole.YesRole: "yes",
                    QDialogButtonBox.ButtonRole.NoRole: "no",
                }
                role_name = role_names.get(role, "action")

                # Parent hierarchy'de QDialog ara
                dialog_name = "Dialog"
                widget = parent.parent()
                while widget:
                    if isinstance(widget, QDialog):
                        dialog_name = widget.__class__.__name__
                        # objectName varsa onu da ekle
                        obj_name = widget.objectName()
                        if obj_name:
                            dialog_name = f"{dialog_name}({obj_name})"
                        break
                    widget = widget.parent() if hasattr(widget, "parent") else None

                return f"{dialog_name}.{role_name}"

            # Fallback: parent class adı ile "?" göster
            if parent:
                return f"{parent.__class__.__name__}.?"
        except Exception:
            pass
        return "unknown"

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """
        Qt event filter ana metodu

        Returns:
            False - Event'i consume etmeden devam et
        """
        # PERFORMANS: Erken çıkış
        if not TraceService.is_active():
            return False

        try:
            event_type = event.type()

            # Mouse button release (tıklama)
            if event_type == QEvent.MouseButtonRelease:
                self._handle_click(obj)

            # Focus out (input tamamlandı)
            elif event_type == QEvent.FocusOut:
                self._handle_focus_out(obj)

            # Key press (Enter tuşu ile submit)
            elif event_type == QEvent.KeyPress:
                self._handle_key_press(obj, event)

        except Exception as e:
            # Event filter'da hata sessizce geç
            print(f"[TraceEventFilter] Error: {e}")

        # Event'i consume etme
        return False

    def _handle_click(self, obj: QObject):
        """Mouse click event'lerini işle"""
        # QPushButton veya QToolButton
        if isinstance(obj, (QPushButton, QToolButton)):
            button_text = obj.text() if hasattr(obj, "text") else ""
            button_name = self._get_widget_name(obj)

            TraceService.record_event(
                event_type="button_click",
                widget_name=button_name,
                widget_path=self._get_breadcrumb(),
                event_data={
                    "button_text": button_text,
                    "button_name": button_name,
                    "backend_slot": self._get_connected_slot(obj),
                    "is_checkable": (
                        obj.isCheckable() if hasattr(obj, "isCheckable") else False
                    ),
                    "is_checked": (
                        obj.isChecked() if hasattr(obj, "isChecked") else False
                    ),
                },
            )

        # CheckBox
        elif isinstance(obj, QCheckBox):
            TraceService.record_event(
                event_type="form_input",
                widget_name=self._get_widget_name(obj),
                widget_path=self._get_breadcrumb(),
                event_data={
                    "field_type": "checkbox",
                    "label": obj.text(),
                    "checked": obj.isChecked(),
                },
            )

        # RadioButton
        elif isinstance(obj, QRadioButton):
            if obj.isChecked():  # Sadece seçilen radio
                TraceService.record_event(
                    event_type="form_input",
                    widget_name=self._get_widget_name(obj),
                    widget_path=self._get_breadcrumb(),
                    event_data={
                        "field_type": "radio",
                        "label": obj.text(),
                        "selected": True,
                    },
                )

        # QTreeWidget (Navigasyon veya Liste)
        elif isinstance(obj, QTreeWidget):
            item = obj.currentItem()
            if item:
                # Column 0 textini al
                text = item.text(0)
                TraceService.record_event(
                    event_type="table_selection",
                    widget_name=self._get_widget_name(obj),
                    widget_path=self._get_breadcrumb(),
                    event_data={
                        "selection_type": "tree_item",
                        "item_text": text,
                        "column_count": item.columnCount(),
                    },
                )

        # QTableWidget (Liste Seçimi)
        elif isinstance(obj, QTableWidget):
            items = obj.selectedItems()
            if items:
                # Sadece ilk hücreyi logla veya satır özetini
                first_item = items[0]
                row = first_item.row()

                # Olası önemli kolonları bul (Kod, Ad vb.)
                details = {"row_index": row}
                try:
                    # İlk 3 kolonu kaydet
                    for col in range(min(3, obj.columnCount())):
                        it = obj.item(row, col)
                        if it:
                            details[f"col_{col}"] = it.text()
                except Exception:
                    pass

                TraceService.record_event(
                    event_type="table_selection",
                    widget_name=self._get_widget_name(obj),
                    widget_path=self._get_breadcrumb(),
                    event_data=details,
                )

    def _handle_focus_out(self, obj: QObject):
        """Focus out event'lerini işle (input completion)"""
        # QLineEdit
        if isinstance(obj, QLineEdit):
            field_name = self._get_widget_name(obj)
            value = obj.text()

            # Hassas veri maskeleme
            value = mask_sensitive_data(field_name, value)

            TraceService.record_event(
                event_type="form_input",
                widget_name=field_name,
                widget_path=self._get_breadcrumb(),
                event_data={
                    "field_type": "text",
                    "value": value,
                    "placeholder": obj.placeholderText() or "",
                },
            )

        # QComboBox
        elif isinstance(obj, QComboBox):
            TraceService.record_event(
                event_type="form_input",
                widget_name=self._get_widget_name(obj),
                widget_path=self._get_breadcrumb(),
                event_data={
                    "field_type": "combobox",
                    "selected_text": obj.currentText(),
                    "selected_index": obj.currentIndex(),
                },
            )

        # QSpinBox / QDoubleSpinBox
        elif isinstance(obj, (QSpinBox, QDoubleSpinBox)):
            TraceService.record_event(
                event_type="form_input",
                widget_name=self._get_widget_name(obj),
                widget_path=self._get_breadcrumb(),
                event_data={"field_type": "spinbox", "value": obj.value()},
            )

        # QDateEdit
        elif isinstance(obj, QDateEdit):
            TraceService.record_event(
                event_type="form_input",
                widget_name=self._get_widget_name(obj),
                widget_path=self._get_breadcrumb(),
                event_data={
                    "field_type": "date",
                    "value": obj.date().toString("yyyy-MM-dd"),
                },
            )

        # QTextEdit / QPlainTextEdit
        elif isinstance(obj, (QTextEdit, QPlainTextEdit)):
            field_name = self._get_widget_name(obj)
            text = obj.toPlainText()

            # Uzun metinleri kısalt
            if len(text) > 500:
                text = text[:500] + "..."

            # Hassas veri maskeleme
            text = mask_sensitive_data(field_name, text)

            TraceService.record_event(
                event_type="form_input",
                widget_name=field_name,
                widget_path=self._get_breadcrumb(),
                event_data={
                    "field_type": "textarea",
                    "value": text,
                    "length": len(obj.toPlainText()),
                },
            )

    def _handle_key_press(self, obj: QObject, event):
        """Key press event'lerini işle"""
        from PyQt6.QtCore import Qt

        key = event.key()
        modifiers = event.modifiers()

        # Clipboard İşlemleri (Ctrl+C, Ctrl+V, Cmd+C, Cmd+V)
        is_ctrl = modifiers & (
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier
        )

        if is_ctrl and key == Qt.Key.Key_C:
            # COPY
            TraceService.record_event(
                event_type="form_input",
                widget_name=self._get_widget_name(obj),
                widget_path=self._get_breadcrumb(),
                event_data={
                    "action": "clipboard_copy",
                    "source_widget": str(type(obj).__name__),
                },
            )

        elif is_ctrl and key == Qt.Key.Key_V:
            # PASTE
            # Clipboard içeriğini al (mümkünse)
            clipboard_content = "<protected>"
            try:
                clip = QApplication.clipboard()
                text = clip.text()
                if text:
                    # Hassas veri kontrolü
                    clipboard_content = mask_sensitive_data("clipboard", text)
            except Exception:
                pass

            TraceService.record_event(
                event_type="form_input",
                widget_name=self._get_widget_name(obj),
                widget_path=self._get_breadcrumb(),
                event_data={
                    "action": "clipboard_paste",
                    "content": clipboard_content,
                    "target_widget": str(type(obj).__name__),
                },
            )

        # Enter/Return tuşu - form submit gibi davranabilir
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if isinstance(obj, QLineEdit):
                TraceService.record_event(
                    event_type="button_click",
                    widget_name=self._get_widget_name(obj),
                    widget_path=self._get_breadcrumb(),
                    event_data={
                        "action": "enter_pressed",
                        "field_name": self._get_widget_name(obj),
                    },
                )


# Module-level singleton
trace_event_filter = TraceEventFilter()
