"""
Mesajlaşma - Mesaj Thread Görünümü
"""

from datetime import datetime
from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QFrame,
    QSizePolicy,
    QTextEdit,
    QMenu,
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QSize, QPoint
from PyQt6.QtGui import QFont, QKeyEvent, QAction
import qtawesome as qta

from config.styles import (
    BG_PRIMARY,
    BG_SECONDARY,
    BG_TERTIARY,
    BORDER,
    TEXT_PRIMARY,
    TEXT_MUTED,
    ACCENT,
    BTN_PRIMARY_BG,
    BTN_PRIMARY_HOVER,
    INPUT_BG,
    INPUT_BORDER,
    INPUT_FOCUS,
    SUCCESS,
)
from config.icons import ICONS


def _format_msg_time(dt: Optional[datetime]) -> str:
    if not dt:
        return ""
    now = datetime.utcnow()
    delta = now - dt
    if delta.days == 0:
        return dt.strftime("%H:%M")
    elif delta.days == 1:
        return f"Dün {dt.strftime('%H:%M')}"
    else:
        return dt.strftime("%d.%m %H:%M")


class MessageBubble(QFrame):
    """Tek mesaj balonu."""

    reply_requested = pyqtSignal(dict)
    star_requested = pyqtSignal(int)
    pin_requested = pyqtSignal(int)
    delete_requested = pyqtSignal(int)

    def __init__(
        self,
        msg_data: Dict[str, Any],
        is_own: bool,
        show_sender: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self.msg_data = msg_data
        self.is_own = is_own
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self._setup_ui(show_sender)

    def _show_context_menu(self, pos: QPoint):
        if self.msg_data.get("message_type") == "system":
            return

        menu = QMenu(self)
        menu.setStyleSheet(
            f"""
            QMenu {{
                background: #2d2d2d;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                padding: 4px;
                color: #cccccc;
                font-size: 12px;
            }}
            QMenu::item {{
                padding: 6px 16px;
                border-radius: 3px;
            }}
            QMenu::item:selected {{
                background: #094771;
            }}
            QMenu::separator {{
                height: 1px;
                background: #3e3e42;
                margin: 3px 0;
            }}
            """
        )

        msg_id = self.msg_data.get("id", 0)

        reply_act = QAction(qta.icon(ICONS.REPLY, color="#cccccc"), "Yanıtla", self)
        reply_act.triggered.connect(lambda: self.reply_requested.emit(self.msg_data))
        menu.addAction(reply_act)

        star_act = QAction(qta.icon(ICONS.STAR, color="#dcdcaa"), "Yıldızla", self)
        star_act.triggered.connect(lambda: self.star_requested.emit(msg_id))
        menu.addAction(star_act)

        pin_act = QAction(qta.icon(ICONS.PIN, color="#cccccc"), "Sabitle", self)
        pin_act.triggered.connect(lambda: self.pin_requested.emit(msg_id))
        menu.addAction(pin_act)

        if self.is_own:
            menu.addSeparator()
            del_act = QAction(qta.icon(ICONS.DELETE, color="#f14c4c"), "Sil", self)
            del_act.triggered.connect(lambda: self.delete_requested.emit(msg_id))
            menu.addAction(del_act)

        menu.exec(self.mapToGlobal(pos))

    def _setup_ui(self, show_sender: bool):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(8, 2, 8, 2)
        outer.setSpacing(0)

        msg_type = self.msg_data.get("message_type", "text")
        content = self.msg_data.get("content", "")
        sender_name = self.msg_data.get("sender_name", "")
        created_at = self.msg_data.get("created_at")
        is_edited = self.msg_data.get("is_edited", False)

        if msg_type == "system":
            # Sistem mesajı - ortada, küçük italik
            outer.addStretch()
            sys_label = QLabel(content)
            sys_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sys_label.setWordWrap(True)
            sys_label.setStyleSheet(
                f"""
                QLabel {{
                    color: {TEXT_MUTED};
                    font-size: 10px;
                    font-style: italic;
                    padding: 2px 8px;
                }}
                """
            )
            outer.addWidget(sys_label)
            outer.addStretch()
            return

        if self.is_own:
            outer.addStretch()

        # Balon çerçevesi
        bubble = QFrame()
        bubble.setMaximumWidth(280)

        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(10, 6, 10, 6)
        bubble_layout.setSpacing(2)

        # Gönderen adı (grup konuşmalarında)
        if show_sender and not self.is_own and sender_name:
            sender_label = QLabel(sender_name)
            sender_label.setStyleSheet(
                f"color: {ACCENT}; font-size: 10px; font-weight: bold;"
            )
            bubble_layout.addWidget(sender_label)

        # Mesaj içeriği
        content_label = QLabel(content)
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        content_label.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 12px; line-height: 1.4;"
        )
        bubble_layout.addWidget(content_label)

        # Alt satır: zaman + düzenlendi
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(4)
        footer_layout.addStretch()

        if is_edited:
            edited_label = QLabel("düzenlendi")
            edited_label.setStyleSheet(
                f"color: {TEXT_MUTED}; font-size: 9px; font-style: italic;"
            )
            footer_layout.addWidget(edited_label)

        time_label = QLabel(_format_msg_time(created_at))
        time_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 9px;")
        footer_layout.addWidget(time_label)

        bubble_layout.addLayout(footer_layout)

        if self.is_own:
            bubble.setStyleSheet(
                f"""
                QFrame {{
                    background: {BTN_PRIMARY_BG};
                    border-radius: 12px;
                    border-bottom-right-radius: 4px;
                }}
                """
            )
            outer.addWidget(bubble)
        else:
            bubble.setStyleSheet(
                f"""
                QFrame {{
                    background: {BG_TERTIARY};
                    border-radius: 12px;
                    border-bottom-left-radius: 4px;
                }}
                """
            )
            outer.addWidget(bubble)
            outer.addStretch()


class SendInput(QTextEdit):
    """Enter ile gönderen çok satırlı input."""

    send_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumHeight(80)
        self.setMinimumHeight(36)
        self.setPlaceholderText("Mesaj yaz... (Enter: gönder, Shift+Enter: yeni satır)")
        self.document().contentsChanged.connect(self._adjust_height)

    def keyPressEvent(self, event: QKeyEvent):
        if (
            event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
            and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        ):
            self.send_requested.emit()
        else:
            super().keyPressEvent(event)

    def _adjust_height(self):
        doc_height = self.document().size().height()
        new_height = max(36, min(80, int(doc_height) + 12))
        self.setFixedHeight(new_height)


class ComposeBar(QWidget):
    """Mesaj yazma ve gönderme alanı."""

    message_sent = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        self.input = SendInput()
        self.input.setStyleSheet(
            f"""
            QTextEdit {{
                background: {INPUT_BG};
                border: 1px solid {INPUT_BORDER};
                border-radius: 8px;
                color: {TEXT_PRIMARY};
                padding: 6px 10px;
                font-size: 12px;
            }}
            QTextEdit:focus {{
                border-color: {INPUT_FOCUS};
            }}
            """
        )
        self.input.send_requested.connect(self._on_send)
        layout.addWidget(self.input)

        self.send_btn = QPushButton()
        self.send_btn.setFixedSize(34, 34)
        self.send_btn.setIcon(qta.icon(ICONS.SEND, color="white"))
        self.send_btn.setIconSize(QSize(16, 16))
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setToolTip("Gönder (Enter)")
        self.send_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: {BTN_PRIMARY_BG};
                border: none;
                border-radius: 17px;
            }}
            QPushButton:hover {{
                background: {BTN_PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background: #005fa3;
            }}
            """
        )
        self.send_btn.clicked.connect(self._on_send)
        layout.addWidget(self.send_btn)

    def _on_send(self):
        text = self.input.toPlainText().strip()
        if not text:
            return
        self.input.clear()
        self.message_sent.emit(text)

    def focus_input(self):
        self.input.setFocus()


class MessageThreadWidget(QWidget):
    """
    Mesaj thread görünümü.
    Seçili konuşmanın mesajlarını gösterir.
    """

    back_requested = pyqtSignal()
    message_sent = pyqtSignal(int, str)  # conversation_id, content

    def __init__(self, parent=None):
        super().__init__(parent)
        self._conversation_id: Optional[int] = None
        self._current_user_id: Optional[int] = None
        self._last_message_id: int = 0
        self._show_sender_name: bool = False
        self._poll_timer: Optional[QTimer] = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Başlık
        self.header = self._build_header()
        layout.addWidget(self.header)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {BORDER}; background: {BORDER}; height: 1px;")
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        # Mesaj scroll alanı
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll.setStyleSheet(
            f"""
            QScrollArea {{
                background: {BG_PRIMARY};
                border: none;
            }}
            QScrollBar:vertical {{
                background: {BG_PRIMARY};
                width: 4px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: #555;
                border-radius: 2px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            """
        )

        self.messages_container = QWidget()
        self.messages_container.setStyleSheet(f"background: {BG_PRIMARY};")
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(0, 8, 0, 8)
        self.messages_layout.setSpacing(2)
        self.messages_layout.addStretch()

        self.scroll.setWidget(self.messages_container)
        layout.addWidget(self.scroll)

        # Boş durum
        self.empty_label = QLabel("Henüz mesaj yok\nİlk mesajı siz gönderin!")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 12px;"
        )
        self.empty_label.setWordWrap(True)
        layout.addWidget(self.empty_label)
        self.empty_label.setVisible(False)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"color: {BORDER}; background: {BORDER}; height: 1px;")
        sep2.setFixedHeight(1)
        layout.addWidget(sep2)

        # Yanıt önizleme banner'ı (varsayılan gizli)
        self.reply_banner = QWidget()
        self.reply_banner.setFixedHeight(30)
        self.reply_banner.setStyleSheet(
            f"background: {BG_TERTIARY}; border-left: 3px solid {ACCENT};"
        )
        reply_banner_layout = QHBoxLayout(self.reply_banner)
        reply_banner_layout.setContentsMargins(8, 0, 4, 0)
        reply_banner_layout.setSpacing(4)

        self._reply_to_data: Optional[Dict[str, Any]] = None
        self._reply_label = QLabel()
        self._reply_label.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 11px; font-style: italic;"
        )
        reply_banner_layout.addWidget(self._reply_label)
        reply_banner_layout.addStretch()

        cancel_reply_btn = QPushButton()
        cancel_reply_btn.setIcon(qta.icon(ICONS.CLOSE, color="#969696"))
        cancel_reply_btn.setIconSize(QSize(10, 10))
        cancel_reply_btn.setFixedSize(20, 20)
        cancel_reply_btn.setFlat(True)
        cancel_reply_btn.clicked.connect(self._cancel_reply)
        cancel_reply_btn.setStyleSheet("background: transparent; border: none;")
        reply_banner_layout.addWidget(cancel_reply_btn)

        layout.addWidget(self.reply_banner)
        self.reply_banner.setVisible(False)

        # Compose bar
        self.compose = ComposeBar()
        self.compose.message_sent.connect(self._on_message_sent)
        layout.addWidget(self.compose)

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setFixedHeight(40)
        header.setStyleSheet(
            f"background: {BG_SECONDARY}; border: none;"
        )

        layout = QHBoxLayout(header)
        layout.setContentsMargins(6, 0, 8, 0)
        layout.setSpacing(6)

        # Geri butonu
        self.back_btn = QPushButton()
        self.back_btn.setIcon(qta.icon(ICONS.BACK, color="#cccccc"))
        self.back_btn.setIconSize(QSize(16, 16))
        self.back_btn.setFixedSize(28, 28)
        self.back_btn.setFlat(True)
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background: {BG_TERTIARY};
            }}
            """
        )
        self.back_btn.clicked.connect(self.back_requested)
        layout.addWidget(self.back_btn)

        self.title_label = QLabel()
        self.title_label.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 13px; font-weight: 600;"
        )
        layout.addWidget(self.title_label)
        layout.addStretch()

        return header

    def load_conversation(
        self,
        conv_data: Dict[str, Any],
        messages: List[Dict[str, Any]],
        current_user_id: int,
    ):
        """Konuşmayı ve mesajları yükler."""
        self._conversation_id = conv_data["id"]
        self._current_user_id = current_user_id
        self._show_sender_name = conv_data.get("conversation_type") in (
            "group",
            "department",
        )

        self.title_label.setText(conv_data.get("title", "Konuşma"))

        self._render_messages(messages)

        # Polling timer başlat
        self._stop_poll_timer()
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._request_poll)
        self._poll_timer.start(3000)

        self.compose.focus_input()

    def _render_messages(self, messages: List[Dict[str, Any]]):
        """Mesajları render eder."""
        # Temizle
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not messages:
            self.empty_label.setVisible(True)
            return

        self.empty_label.setVisible(False)

        for msg in messages:
            is_own = msg["sender_id"] == self._current_user_id
            bubble = MessageBubble(
                msg, is_own, show_sender=self._show_sender_name
            )
            self._connect_bubble(bubble)
            self.messages_layout.insertWidget(
                self.messages_layout.count() - 1, bubble
            )

        if messages:
            self._last_message_id = messages[-1]["id"]

        # En alta kaydır
        QTimer.singleShot(50, self._scroll_to_bottom)

    def append_messages(self, new_messages: List[Dict[str, Any]]):
        """Yeni gelen mesajları ekler."""
        if not new_messages:
            return

        self.empty_label.setVisible(False)
        for msg in new_messages:
            is_own = msg["sender_id"] == self._current_user_id
            bubble = MessageBubble(
                msg, is_own, show_sender=self._show_sender_name
            )
            self._connect_bubble(bubble)
            self.messages_layout.insertWidget(
                self.messages_layout.count() - 1, bubble
            )

        self._last_message_id = new_messages[-1]["id"]
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _connect_bubble(self, bubble: "MessageBubble"):
        """Mesaj balonunun sinyallerini bağlar."""
        bubble.reply_requested.connect(self._on_reply_requested)
        bubble.star_requested.connect(self._on_star_requested)
        bubble.pin_requested.connect(self._on_pin_requested)
        bubble.delete_requested.connect(self._on_delete_requested)

    def _on_reply_requested(self, msg_data: Dict[str, Any]):
        self._reply_to_data = msg_data
        sender = msg_data.get("sender_name", "")
        content = msg_data.get("content", "")[:40]
        self._reply_label.setText(f"↩ {sender}: {content}")
        self.reply_banner.setVisible(True)
        self.compose.focus_input()

    def _cancel_reply(self):
        self._reply_to_data = None
        self.reply_banner.setVisible(False)

    def _on_star_requested(self, msg_id: int):
        from PyQt6.QtCore import QRunnable, QThreadPool, pyqtSlot

        class StarWorker(QRunnable):
            def __init__(self, mid: int, uid: int):
                super().__init__()
                self.mid = mid
                self.uid = uid

            @pyqtSlot()
            def run(self):
                session = None
                try:
                    from modules.messaging.services import MessagingService
                    from database.base import get_session
                    session = get_session()
                    MessagingService(session).toggle_star(self.mid, self.uid)
                except Exception:
                    pass
                finally:
                    if session:
                        session.close()

        if self._current_user_id:
            w = StarWorker(msg_id, self._current_user_id)
            QThreadPool.globalInstance().start(w)

    def _on_pin_requested(self, msg_id: int):
        from PyQt6.QtCore import QRunnable, QThreadPool, pyqtSlot

        class PinWorker(QRunnable):
            def __init__(self, mid: int):
                super().__init__()
                self.mid = mid

            @pyqtSlot()
            def run(self):
                session = None
                try:
                    from modules.messaging.services import MessagingService
                    from database.base import get_session
                    session = get_session()
                    MessagingService(session).pin_message(self.mid)
                except Exception:
                    pass
                finally:
                    if session:
                        session.close()

        QThreadPool.globalInstance().start(PinWorker(msg_id))

    def _on_delete_requested(self, msg_id: int):
        from PyQt6.QtCore import QRunnable, QThreadPool, pyqtSlot

        class DeleteWorker(QRunnable):
            def __init__(self, mid: int, uid: int):
                super().__init__()
                self.mid = mid
                self.uid = uid

            @pyqtSlot()
            def run(self):
                session = None
                try:
                    from modules.messaging.services import MessagingService
                    from database.base import get_session
                    session = get_session()
                    MessagingService(session).delete_message(self.mid, self.uid)
                except Exception:
                    pass
                finally:
                    if session:
                        session.close()

        if self._current_user_id:
            QThreadPool.globalInstance().start(
                DeleteWorker(msg_id, self._current_user_id)
            )

    def _scroll_to_bottom(self):
        sb = self.scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_message_sent(self, content: str):
        if self._conversation_id:
            self.message_sent.emit(self._conversation_id, content)
        self._cancel_reply()

    def _request_poll(self):
        """Polling sinyali - MessagingPopup tarafından yakalanır."""
        if self._conversation_id and self._last_message_id:
            # Bu sinyal parent'ta bağlanır
            pass

    def get_poll_state(self):
        return self._conversation_id, self._last_message_id

    def _stop_poll_timer(self):
        if self._poll_timer and self._poll_timer.isActive():
            self._poll_timer.stop()
            self._poll_timer = None

    def cleanup(self):
        """Widget kapatılırken çağrılır."""
        self._stop_poll_timer()
