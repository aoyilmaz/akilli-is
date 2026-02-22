"""
Mesajlaşma - Kayıt Bazlı Mesajlaşma Butonu (Faz 4)

Herhangi bir modül view'ına eklenebilir.
Kullanım:
    btn = RecordMessagingButton(entity_type="sales_orders", entity_id=42)
    toolbar_layout.addWidget(btn)
"""

from typing import Optional

from PyQt6.QtWidgets import QPushButton, QApplication
from PyQt6.QtCore import Qt, QSize, QPoint, QRunnable, QThreadPool, pyqtSlot, QObject, pyqtSignal
import qtawesome as qta

from config.styles import BTN_SECONDARY_BG, BTN_SECONDARY_HOVER, TEXT_PRIMARY
from config.icons import ICONS


class _CreateRecordConvWorker(QRunnable):
    class Signals(QObject):
        result = pyqtSignal(dict)
        error = pyqtSignal(str)

    def __init__(self, entity_type: str, entity_id: int, creator_id: int):
        super().__init__()
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.creator_id = creator_id
        self.signals = self.Signals()

    @pyqtSlot()
    def run(self):
        session = None
        try:
            from modules.messaging.services import MessagingService
            from database.base import get_session

            session = get_session()
            service = MessagingService(session)
            conv = service.create_record_conversation(
                self.entity_type, self.entity_id, self.creator_id
            )
            self.signals.result.emit(
                {
                    "id": conv.id,
                    "title": conv.title,
                    "conversation_type": conv.conversation_type,
                    "last_message_at": conv.last_message_at,
                    "last_message_preview": conv.last_message_preview,
                    "unread_count": 0,
                    "is_muted": False,
                    "is_pinned": False,
                    "entity_type": conv.entity_type,
                    "entity_id": conv.entity_id,
                }
            )
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            if session:
                session.close()


class RecordMessagingButton(QPushButton):
    """
    ERP kaydına bağlı mesajlaşma butonu.

    Mevcut modül view'larının toolbar'ına eklenir.
    Tıklanınca ilgili kayda ait konuşmayı popup'ta açar.

    Örnek kullanım:
        # modules/sales/views/sales_form.py içinde
        self.msg_btn = RecordMessagingButton(
            entity_type="sales_orders",
            entity_id=self.order_id
        )
        self.toolbar.addWidget(self.msg_btn)
    """

    def __init__(
        self,
        entity_type: str,
        entity_id: int,
        parent=None,
    ):
        super().__init__(parent)
        self._entity_type = entity_type
        self._entity_id = entity_id
        self._thread_pool = QThreadPool.globalInstance()

        self.setIcon(qta.icon(ICONS.CHAT, color="#cccccc"))
        self.setIconSize(QSize(14, 14))
        self.setText("Mesajlar")
        self.setFixedHeight(30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(f"{entity_type} #{entity_id} konuşması")
        self.setStyleSheet(
            f"""
            QPushButton {{
                background: {BTN_SECONDARY_BG};
                color: {TEXT_PRIMARY};
                border: none;
                border-radius: 4px;
                padding: 0 10px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: {BTN_SECONDARY_HOVER};
            }}
            """
        )
        self.clicked.connect(self._on_clicked)

    def _on_clicked(self):
        try:
            from core.auth_service import AuthService

            user = AuthService.get_current_user()
            creator_id = user.id if user else 1
        except Exception:
            creator_id = 1

        worker = _CreateRecordConvWorker(
            self._entity_type, self._entity_id, creator_id
        )
        worker.signals.result.connect(self._open_popup_for_conv)
        worker.signals.error.connect(lambda e: print(f"Record conv error: {e}"))
        self._thread_pool.start(worker)

    def _open_popup_for_conv(self, conv_data: dict):
        """Konuşma oluşturuldu/bulundu → popup aç ve konuşmayı göster."""
        try:
            # Ana penceredeki MessagingButton'u bul ve popup'ı aç
            from PyQt6.QtWidgets import QMainWindow
            from modules.messaging.views.messaging_popup import MessagingButton, MessagingPopup

            # Ana pencereyi bul
            main_win = None
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, QMainWindow):
                    main_win = widget
                    break

            if not main_win:
                return

            # MessagingButton'u bul
            msg_btn = None
            for child in main_win.findChildren(MessagingButton):
                msg_btn = child
                break

            if msg_btn:
                # Popup'ı aç
                msg_btn._open_popup()
                # Kısa gecikme ile konuşmaya git
                from PyQt6.QtCore import QTimer

                if msg_btn._popup:
                    QTimer.singleShot(
                        300,
                        lambda: msg_btn._popup._on_conversation_selected(conv_data)
                        if msg_btn._popup
                        else None,
                    )
        except Exception as e:
            print(f"Record messaging popup error: {e}")
