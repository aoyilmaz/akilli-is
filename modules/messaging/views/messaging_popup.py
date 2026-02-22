"""
Mesajlaşma - Status Bar Butonu ve Ana Popup Panel
"""

from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QStackedWidget,
    QApplication,
    QSizePolicy,
)
from PyQt6.QtCore import (
    pyqtSignal,
    Qt,
    QTimer,
    QPoint,
    QSize,
    QRunnable,
    QThreadPool,
    pyqtSlot,
    QObject,
)
from PyQt6.QtGui import QFont
import qtawesome as qta

from config.styles import (
    BG_PRIMARY,
    BG_SECONDARY,
    BG_TERTIARY,
    BORDER,
    TEXT_PRIMARY,
    TEXT_MUTED,
    ACCENT,
    ERROR,
    BTN_PRIMARY_BG,
    BTN_PRIMARY_HOVER,
)
from config.icons import ICONS
from database.base import get_session


# ============================================================
# Arka Plan Worker'ları
# ============================================================


class WorkerSignals(QObject):
    result = pyqtSignal(object)
    error = pyqtSignal(str)


class UnreadCountWorker(QRunnable):
    """Okunmamış sayısını arka planda sorgular."""

    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        session = None
        try:
            from modules.messaging.services import MessagingService

            session = get_session()
            service = MessagingService(session)
            count = service.get_total_unread_count(self.user_id)
            self.signals.result.emit(count)
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            if session:
                session.close()


class ConversationsWorker(QRunnable):
    """Konuşma listesini arka planda sorgular."""

    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        session = None
        try:
            from modules.messaging.services import MessagingService

            session = get_session()
            service = MessagingService(session)
            convs = service.get_user_conversations(user_id=self.user_id)
            self.signals.result.emit(convs)
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            if session:
                session.close()


class MessagesWorker(QRunnable):
    """Yeni mesajları arka planda sorgular."""

    def __init__(self, conversation_id: int, after_id: int):
        super().__init__()
        self.conversation_id = conversation_id
        self.after_id = after_id
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        session = None
        try:
            from modules.messaging.services import MessagingService

            session = get_session()
            service = MessagingService(session)
            msgs = service.get_new_messages(self.conversation_id, self.after_id)
            self.signals.result.emit(msgs)
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            if session:
                session.close()


class SendMessageWorker(QRunnable):
    """Mesajı arka planda gönderir."""

    def __init__(
        self,
        conversation_id: int,
        sender_id: int,
        content: str,
    ):
        super().__init__()
        self.conversation_id = conversation_id
        self.sender_id = sender_id
        self.content = content
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        session = None
        try:
            from modules.messaging.services import MessagingService

            session = get_session()
            service = MessagingService(session)
            msg = service.send_message(
                conversation_id=self.conversation_id,
                sender_id=self.sender_id,
                content=self.content,
            )
            self.signals.result.emit(
                {
                    "id": msg.id,
                    "conversation_id": msg.conversation_id,
                    "sender_id": msg.sender_id,
                    "sender_name": "Sen",
                    "content": msg.content,
                    "message_type": msg.message_type,
                    "reply_to_id": msg.reply_to_id,
                    "priority": msg.priority,
                    "is_edited": msg.is_edited,
                    "is_pinned": msg.is_pinned,
                    "created_at": msg.created_at,
                }
            )
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            if session:
                session.close()


class LoadConversationWorker(QRunnable):
    """Konuşma detayı + mesajlarını arka planda yükler."""

    def __init__(self, conversation_id: int, user_id: int):
        super().__init__()
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        session = None
        try:
            from modules.messaging.services import MessagingService

            session = get_session()
            service = MessagingService(session)
            msgs = service.get_messages(self.conversation_id, limit=50)
            service.mark_conversation_read(self.conversation_id, self.user_id)
            self.signals.result.emit(msgs)
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            if session:
                session.close()


class CreateDirectConvWorker(QRunnable):
    """Direkt konuşma oluşturur."""

    def __init__(self, user_id_1: int, user_id_2: int, target_user_name: str):
        super().__init__()
        self.user_id_1 = user_id_1
        self.user_id_2 = user_id_2
        self.target_user_name = target_user_name
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        session = None
        try:
            from modules.messaging.services import MessagingService

            session = get_session()
            service = MessagingService(session)
            conv = service.create_direct_conversation(
                self.user_id_1, self.user_id_2
            )
            self.signals.result.emit(
                {
                    "id": conv.id,
                    "title": self.target_user_name,
                    "conversation_type": conv.conversation_type,
                    "last_message_at": conv.last_message_at,
                    "last_message_preview": conv.last_message_preview,
                    "unread_count": 0,
                    "is_muted": False,
                    "is_pinned": False,
                }
            )
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            if session:
                session.close()


class CreateGroupConvWorker(QRunnable):
    """Grup konuşması oluşturur."""

    def __init__(self, title: str, creator_id: int, participant_ids: list):
        super().__init__()
        self.title = title
        self.creator_id = creator_id
        self.participant_ids = participant_ids
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        session = None
        try:
            from modules.messaging.services import MessagingService

            session = get_session()
            service = MessagingService(session)
            conv = service.create_group_conversation(
                self.title, self.creator_id, self.participant_ids
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
                }
            )
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            if session:
                session.close()


class CreateDeptConvWorker(QRunnable):
    """Departman kanalı oluşturur."""

    def __init__(self, department_id: int, creator_id: int):
        super().__init__()
        self.department_id = department_id
        self.creator_id = creator_id
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        session = None
        try:
            from modules.messaging.services import MessagingService

            session = get_session()
            service = MessagingService(session)
            conv = service.create_department_conversation(
                self.department_id, self.creator_id
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
                }
            )
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            if session:
                session.close()


# ============================================================
# Popup Paneli
# ============================================================


class MessagingPopup(QFrame):
    """
    Status bar üstünde açılan mesajlaşma popup paneli.
    Qt.WindowType.Popup ile dışına tıklanınca kapanır.
    """

    closed = pyqtSignal()

    POPUP_W = 400
    POPUP_H = 520

    def __init__(self, user_id: int, parent=None):
        super().__init__(parent)
        self._user_id = user_id
        self._current_conv: Optional[Dict[str, Any]] = None
        self._conv_poll_timer: Optional[QTimer] = None
        self._thread_poll_timer: Optional[QTimer] = None
        self._thread_pool = QThreadPool.globalInstance()

        self.setWindowFlags(
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setFixedSize(self.POPUP_W, self.POPUP_H)

        self._setup_ui()
        self._apply_style()

        # Konuşma listesini hemen yükle
        self._load_conversations()

        # Konuşma listesi polling (5s)
        self._conv_poll_timer = QTimer(self)
        self._conv_poll_timer.timeout.connect(self._load_conversations)
        self._conv_poll_timer.start(5000)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = self._build_header()
        layout.addWidget(header)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {BORDER}; height: 1px;")
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        # İçerik stack: [0] konuşma listesi, [1] mesaj thread
        self.content_stack = QStackedWidget()
        layout.addWidget(self.content_stack)

        # Konuşma listesi
        from modules.messaging.views.conversation_list import ConversationListWidget
        self.conv_list = ConversationListWidget()
        self.conv_list.conversation_selected.connect(self._on_conversation_selected)
        self.content_stack.addWidget(self.conv_list)

        # Mesaj thread
        from modules.messaging.views.message_thread import MessageThreadWidget
        self.thread_view = MessageThreadWidget()
        self.thread_view.back_requested.connect(self._show_conv_list)
        self.thread_view.message_sent.connect(self._on_message_sent)
        self.content_stack.addWidget(self.thread_view)

        self.content_stack.setCurrentIndex(0)

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setFixedHeight(42)
        header.setStyleSheet(f"background: {BG_TERTIARY}; border: none;")

        layout = QHBoxLayout(header)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(8)

        title = QLabel("Mesajlar")
        title.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 13px; font-weight: 600;"
        )
        layout.addWidget(title)
        layout.addStretch()

        # Arama butonu (ileride arama paneli açacak)
        search_btn = QPushButton()
        search_btn.setIcon(qta.icon(ICONS.SEARCH, color="#969696"))
        search_btn.setIconSize(QSize(14, 14))
        search_btn.setFixedSize(28, 28)
        search_btn.setFlat(True)
        search_btn.setToolTip("Mesajlarda ara")
        search_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background: {BG_SECONDARY};
            }}
            """
        )
        layout.addWidget(search_btn)

        # Yeni mesaj butonu
        new_btn = QPushButton()
        new_btn.setIcon(qta.icon(ICONS.PLUS, color="#cccccc"))
        new_btn.setIconSize(QSize(14, 14))
        new_btn.setFixedSize(28, 28)
        new_btn.setFlat(True)
        new_btn.setToolTip("Yeni mesaj")
        new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background: {BTN_PRIMARY_BG};
            }}
            """
        )
        new_btn.clicked.connect(self._on_new_message)
        layout.addWidget(new_btn)

        return header

    def _apply_style(self):
        self.setStyleSheet(
            f"""
            MessagingPopup {{
                background: {BG_SECONDARY};
                border: 1px solid {BORDER};
                border-radius: 6px;
            }}
            """
        )

    # ============================================================
    # Konuşma Yükleme
    # ============================================================

    def _load_conversations(self):
        worker = ConversationsWorker(self._user_id)
        worker.signals.result.connect(self._on_conversations_loaded)
        self._thread_pool.start(worker)

    def _on_conversations_loaded(self, conversations: List[Dict[str, Any]]):
        self.conv_list.set_conversations(conversations)

    # ============================================================
    # Konuşma Seçimi → Thread Görünümü
    # ============================================================

    def _on_conversation_selected(self, conv_data: Dict[str, Any]):
        self._current_conv = conv_data
        self.content_stack.setCurrentIndex(1)

        # Mesajları arka planda yükle
        worker = LoadConversationWorker(conv_data["id"], self._user_id)
        worker.signals.result.connect(
            lambda msgs: self._on_messages_loaded(conv_data, msgs)
        )
        self._thread_pool.start(worker)

        # Thread polling başlat (3s)
        self._stop_thread_poll()
        self._thread_poll_timer = QTimer(self)
        self._thread_poll_timer.timeout.connect(self._poll_new_messages)
        self._thread_poll_timer.start(3000)

    def _on_messages_loaded(
        self, conv_data: Dict[str, Any], messages: List[Dict[str, Any]]
    ):
        self.thread_view.load_conversation(conv_data, messages, self._user_id)

    def _show_conv_list(self):
        self._current_conv = None
        self._stop_thread_poll()
        self.thread_view.cleanup()
        self.content_stack.setCurrentIndex(0)
        self._load_conversations()  # Listeyi yenile

    # ============================================================
    # Thread Polling
    # ============================================================

    def _poll_new_messages(self):
        conv_id, last_id = self.thread_view.get_poll_state()
        if not conv_id or not last_id:
            return

        worker = MessagesWorker(conv_id, last_id)
        worker.signals.result.connect(self._on_new_messages)
        self._thread_pool.start(worker)

    def _on_new_messages(self, messages: List[Dict[str, Any]]):
        if messages:
            self.thread_view.append_messages(messages)

    def _stop_thread_poll(self):
        if self._thread_poll_timer and self._thread_poll_timer.isActive():
            self._thread_poll_timer.stop()
            self._thread_poll_timer = None

    # ============================================================
    # Mesaj Gönderme
    # ============================================================

    def _on_message_sent(self, conv_id: int, content: str):
        worker = SendMessageWorker(conv_id, self._user_id, content)
        worker.signals.result.connect(self._on_message_send_ok)
        self._thread_pool.start(worker)

    def _on_message_send_ok(self, msg_data: Dict[str, Any]):
        self.thread_view.append_messages([msg_data])

    # ============================================================
    # Yeni Mesaj / Konuşma Oluşturma
    # ============================================================

    def _on_new_message(self):
        session = None
        try:
            from modules.messaging.views.compose_dialog import ComposeDialog
            from modules.messaging.services import MessagingService

            session = get_session()
            service = MessagingService(session)
            users = service.get_available_users(self._user_id)
            departments = service.get_departments_for_messaging()
        finally:
            if session:
                session.close()

        dialog = ComposeDialog(users, departments, parent=self)
        dialog.conversation_created.connect(self._on_conversation_created)
        dialog.exec()

    def _on_conversation_created(self, data: Dict[str, Any]):
        conv_type = data.get("type")

        if conv_type == "direct":
            worker = CreateDirectConvWorker(
                self._user_id, data["user_id"], data["user_name"]
            )
            worker.signals.result.connect(self._on_conversation_selected)
            self._thread_pool.start(worker)

        elif conv_type == "group":
            worker = CreateGroupConvWorker(
                data["title"], self._user_id, data["participant_ids"]
            )
            worker.signals.result.connect(self._on_conversation_selected)
            self._thread_pool.start(worker)

        elif conv_type == "department":
            worker = CreateDeptConvWorker(
                data["department_id"], self._user_id
            )
            worker.signals.result.connect(self._on_conversation_selected)
            self._thread_pool.start(worker)

    # ============================================================
    # Lifecycle
    # ============================================================

    def closeEvent(self, event):
        self._stop_thread_poll()
        if self._conv_poll_timer and self._conv_poll_timer.isActive():
            self._conv_poll_timer.stop()
        self.thread_view.cleanup()
        self.closed.emit()
        super().closeEvent(event)


# ============================================================
# Status Bar Butonu
# ============================================================


class MessagingButton(QWidget):
    """
    Status bar'a eklenen mesajlaşma butonu.
    Okunmamış mesaj sayısını badge olarak gösterir.
    """

    def __init__(self, user_id: int, parent=None):
        super().__init__(parent)
        self._user_id = user_id
        self._popup: Optional[MessagingPopup] = None
        self._thread_pool = QThreadPool.globalInstance()
        self.setFixedSize(32, 24)
        self._setup_ui()

        # Badge polling (10s)
        self._badge_timer = QTimer(self)
        self._badge_timer.timeout.connect(self._poll_unread)
        self._badge_timer.start(10000)

        # İlk sorgu (2s sonra - app yüklendikten sonra)
        QTimer.singleShot(2000, self._poll_unread)

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(0)

        # Ana buton
        self.btn = QPushButton()
        self.btn.setFixedSize(24, 22)
        self.btn.setIcon(qta.icon(ICONS.CHAT, color="#cccccc"))
        self.btn.setIconSize(QSize(14, 14))
        self.btn.setFlat(True)
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.setToolTip("Mesajlar")
        self.btn.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background: rgba(255,255,255,0.1);
            }}
            QPushButton:pressed {{
                background: rgba(255,255,255,0.15);
            }}
            """
        )
        self.btn.clicked.connect(self._toggle_popup)
        layout.addWidget(self.btn)

        # Badge (sağ üstte)
        self.badge = QLabel()
        self.badge.setFixedSize(14, 14)
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge.setStyleSheet(
            f"""
            QLabel {{
                background: {ERROR};
                color: white;
                border-radius: 7px;
                font-size: 8px;
                font-weight: bold;
            }}
            """
        )
        self.badge.setVisible(False)
        # Absolute position üst sağ köşe
        self.badge.setParent(self)
        self.badge.move(16, 0)

    def _poll_unread(self):
        worker = UnreadCountWorker(self._user_id)
        worker.signals.result.connect(self._update_badge)
        self._thread_pool.start(worker)

    def _update_badge(self, count: int):
        if count <= 0:
            self.badge.setVisible(False)
        else:
            self.badge.setVisible(True)
            self.badge.setText(str(count) if count <= 9 else "9+")

    def _toggle_popup(self):
        if self._popup and self._popup.isVisible():
            self._popup.close()
            self._popup = None
            return

        self._open_popup()

    def _open_popup(self):
        self._popup = MessagingPopup(user_id=self._user_id, parent=None)
        self._popup.closed.connect(self._on_popup_closed)

        # Pozisyon: status bar üstünde, butona hizalı (sağa)
        btn_global = self.mapToGlobal(QPoint(0, 0))

        popup_w = MessagingPopup.POPUP_W
        popup_h = MessagingPopup.POPUP_H

        popup_x = btn_global.x() + self.width() - popup_w
        popup_y = btn_global.y() - popup_h - 4

        # Ekran sınırı kontrolü
        screen = QApplication.primaryScreen().availableGeometry()
        popup_x = max(screen.left(), min(popup_x, screen.right() - popup_w))
        popup_y = max(screen.top(), popup_y)

        self._popup.move(popup_x, popup_y)
        self._popup.show()
        self._popup.raise_()

    def _on_popup_closed(self):
        self._popup = None
        # Badge'i güncelle
        self._poll_unread()

    def force_refresh_badge(self):
        """Dışarıdan badge yenileme tetiklemek için."""
        self._poll_unread()
