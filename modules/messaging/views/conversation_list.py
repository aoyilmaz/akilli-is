"""
Mesajlaşma - Konuşma Listesi Widget
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Callable

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QFrame,
    QSizePolicy,
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont
import qtawesome as qta

from config.styles import (
    BG_SECONDARY,
    BG_TERTIARY,
    BG_HOVER,
    BG_SELECTED,
    BORDER,
    TEXT_PRIMARY,
    TEXT_MUTED,
    ACCENT,
    ERROR,
)
from config.icons import ICONS


def _format_time(dt: Optional[datetime]) -> str:
    """Zamanı kısa formatta döndürür."""
    if not dt:
        return ""
    now = datetime.utcnow()
    delta = now - dt
    if delta.days == 0:
        return dt.strftime("%H:%M")
    elif delta.days == 1:
        return "Dün"
    elif delta.days < 7:
        days = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
        return days[dt.weekday()]
    else:
        return dt.strftime("%d.%m")


class AvatarLabel(QLabel):
    """Baş harf avatar."""

    def __init__(self, name: str, size: int = 36, parent=None):
        super().__init__(parent)
        initials = "".join(w[0].upper() for w in name.split()[:2] if w) or "?"
        self.setText(initials)
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            f"""
            QLabel {{
                background: {ACCENT};
                color: white;
                border-radius: {size // 2}px;
                font-size: {max(10, size // 3)}px;
                font-weight: bold;
            }}
            """
        )


class UnreadBadge(QLabel):
    """Okunmamış mesaj sayısı badge'i."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(18)
        self.setMinimumWidth(18)
        self.setStyleSheet(
            f"""
            QLabel {{
                background: {ERROR};
                color: white;
                border-radius: 9px;
                font-size: 10px;
                font-weight: bold;
                padding: 0 4px;
            }}
            """
        )

    def set_count(self, count: int):
        if count <= 0:
            self.setVisible(False)
            return
        self.setVisible(True)
        self.setText(str(count) if count <= 99 else "99+")


class ConversationItem(QFrame):
    """Tek bir konuşma satırı."""

    clicked = pyqtSignal(dict)

    def __init__(self, conv_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.conv_data = conv_data
        self._selected = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(60)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        # Avatar
        title = self.conv_data.get("title", "?")
        conv_type = self.conv_data.get("conversation_type", "direct")

        if conv_type in ("group", "department"):
            # Grup ikonu
            avatar = QLabel()
            avatar.setFixedSize(36, 36)
            icon = qta.icon(ICONS.GROUP_CHAT, color="white")
            avatar.setPixmap(icon.pixmap(20, 20))
            avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
            avatar.setStyleSheet(
                f"""
                QLabel {{
                    background: #5e3b8e;
                    border-radius: 18px;
                }}
                """
            )
        else:
            avatar = AvatarLabel(title)

        layout.addWidget(avatar)

        # İçerik
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Üst satır: isim + zaman
        top_row = QHBoxLayout()
        top_row.setSpacing(4)

        name_label = QLabel(title)
        name_label.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 12px; font-weight: 600;"
        )
        name_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        top_row.addWidget(name_label)

        time_str = _format_time(self.conv_data.get("last_message_at"))
        time_label = QLabel(time_str)
        time_label.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 10px;"
        )
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        top_row.addWidget(time_label)

        content_layout.addLayout(top_row)

        # Alt satır: önizleme + unread badge
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(4)

        preview = self.conv_data.get("last_message_preview", "")
        preview_label = QLabel(preview or "Henüz mesaj yok")
        preview_label.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 11px;"
        )
        preview_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        preview_label.setMaximumWidth(250)

        # Uzun önizlemeyi kırp
        if len(preview) > 35:
            preview_label.setText(preview[:35] + "...")

        bottom_row.addWidget(preview_label)

        self.badge = UnreadBadge()
        self.badge.set_count(self.conv_data.get("unread_count", 0))
        bottom_row.addWidget(self.badge)

        content_layout.addLayout(bottom_row)
        layout.addLayout(content_layout)

    def _apply_style(self):
        self.setStyleSheet(
            f"""
            ConversationItem {{
                background: transparent;
                border: none;
                border-radius: 4px;
            }}
            ConversationItem:hover {{
                background: {BG_HOVER};
            }}
            """
        )

    def set_selected(self, selected: bool):
        self._selected = selected
        if selected:
            self.setStyleSheet(
                f"""
                ConversationItem {{
                    background: {BG_SELECTED};
                    border: none;
                    border-radius: 4px;
                }}
                """
            )
        else:
            self._apply_style()

    def update_unread(self, count: int):
        self.badge.set_count(count)

    def mousePressEvent(self, event):
        self.clicked.emit(self.conv_data)
        super().mousePressEvent(event)


class ConversationListWidget(QWidget):
    """
    Konuşma listesi paneli.
    Kullanıcının tüm konuşmalarını gösterir.
    """

    conversation_selected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._conversations: List[Dict[str, Any]] = []
        self._items: Dict[int, ConversationItem] = {}
        self._selected_id: Optional[int] = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll.setStyleSheet(
            f"""
            QScrollArea {{
                background: {BG_SECONDARY};
                border: none;
            }}
            QScrollBar:vertical {{
                background: {BG_SECONDARY};
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

        self.list_container = QWidget()
        self.list_container.setStyleSheet(
            f"background: {BG_SECONDARY};"
        )
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(4, 4, 4, 4)
        self.list_layout.setSpacing(1)
        self.list_layout.addStretch()

        scroll.setWidget(self.list_container)
        layout.addWidget(scroll)

        # Boş durum label
        self.empty_label = QLabel("Henüz konuşma yok\n\nYeni mesaj göndermek için + butonuna basın")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 12px; padding: 20px;"
        )
        self.empty_label.setWordWrap(True)
        layout.addWidget(self.empty_label)
        self.empty_label.setVisible(False)

    def set_conversations(self, conversations: List[Dict[str, Any]]):
        """Konuşma listesini günceller."""
        self._conversations = conversations

        # Mevcut itemları temizle
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._items.clear()

        if not conversations:
            self.empty_label.setVisible(True)
            return

        self.empty_label.setVisible(False)
        for conv in conversations:
            item = ConversationItem(conv)
            item.clicked.connect(self._on_item_clicked)
            if conv["id"] == self._selected_id:
                item.set_selected(True)
            self.list_layout.insertWidget(
                self.list_layout.count() - 1, item
            )
            self._items[conv["id"]] = item

    def update_unread(self, conv_id: int, count: int):
        """Tek bir konuşmanın okunmamış sayısını günceller."""
        if conv_id in self._items:
            self._items[conv_id].update_unread(count)

    def _on_item_clicked(self, conv_data: Dict[str, Any]):
        # Seçim vurgusunu güncelle
        if self._selected_id and self._selected_id in self._items:
            self._items[self._selected_id].set_selected(False)

        conv_id = conv_data["id"]
        self._selected_id = conv_id
        if conv_id in self._items:
            self._items[conv_id].set_selected(True)

        self.conversation_selected.emit(conv_data)
