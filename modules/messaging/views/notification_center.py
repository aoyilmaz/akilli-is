"""
Mesajlaşma - Bildirim Merkezi Widget (Faz 5)
"""

from datetime import datetime
from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QSizePolicy,
)
from PyQt6.QtCore import pyqtSignal, Qt, QSize
import qtawesome as qta

from config.styles import (
    BG_PRIMARY,
    BG_SECONDARY,
    BG_TERTIARY,
    BG_HOVER,
    BORDER,
    TEXT_PRIMARY,
    TEXT_MUTED,
    ACCENT,
    SUCCESS,
    WARNING,
    ERROR,
    INFO,
)
from config.icons import ICONS


def _format_time(dt: Optional[datetime]) -> str:
    if not dt:
        return ""
    now = datetime.utcnow()
    delta = now - dt
    if delta.seconds < 60:
        return "Az önce"
    elif delta.seconds < 3600:
        return f"{delta.seconds // 60}dk önce"
    elif delta.days == 0:
        return dt.strftime("%H:%M")
    elif delta.days == 1:
        return "Dün"
    else:
        return dt.strftime("%d.%m")


_PRIORITY_COLOR = {
    "low": TEXT_MUTED,
    "normal": TEXT_PRIMARY,
    "high": WARNING,
    "urgent": ERROR,
}

_PRIORITY_ICON = {
    "low": ICONS.INFO,
    "normal": ICONS.INFO,
    "high": ICONS.WARNING,
    "urgent": ICONS.DANGER,
}


class NotificationItem(QFrame):
    """Tek bir bildirim satırı."""

    clicked = pyqtSignal(dict)

    def __init__(self, notif: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.notif = notif
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(56)
        self._setup_ui()
        self.setStyleSheet(
            f"""
            NotificationItem {{
                background: transparent;
                border: none;
                border-radius: 4px;
            }}
            NotificationItem:hover {{
                background: {BG_HOVER};
            }}
            """
        )

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)

        priority = self.notif.get("priority", "normal")
        color = _PRIORITY_COLOR.get(priority, TEXT_PRIMARY)
        icon_name = _PRIORITY_ICON.get(priority, ICONS.INFO)

        # İkon
        icon_label = QLabel()
        icon_label.setFixedSize(24, 24)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon = qta.icon(icon_name, color=color)
        icon_label.setPixmap(icon.pixmap(16, 16))
        layout.addWidget(icon_label)

        # İçerik
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)
        content_layout.setContentsMargins(0, 0, 0, 0)

        content = self.notif.get("content", "")
        lines = content.split("\n", 1)
        title_text = lines[0].replace("**", "").strip()

        title_label = QLabel(title_text)
        title_label.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 12px; font-weight: 600;"
        )
        content_layout.addWidget(title_label)

        if len(lines) > 1:
            body_label = QLabel(lines[1][:60] + ("..." if len(lines[1]) > 60 else ""))
            body_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
            content_layout.addWidget(body_label)

        layout.addLayout(content_layout)
        layout.addStretch()

        # Zaman
        time_label = QLabel(_format_time(self.notif.get("created_at")))
        time_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px;")
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(time_label)

    def mousePressEvent(self, event):
        self.clicked.emit(self.notif)
        super().mousePressEvent(event)


class NotificationCenterWidget(QWidget):
    """
    Bildirim merkezi paneli.
    Sistem bildirimlerini ve mesaj bildirimlerini listeler.
    """

    notification_clicked = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._notifications: List[Dict[str, Any]] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Scroll
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
        self.list_container.setStyleSheet(f"background: {BG_SECONDARY};")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(4, 4, 4, 4)
        self.list_layout.setSpacing(1)
        self.list_layout.addStretch()

        scroll.setWidget(self.list_container)
        layout.addWidget(scroll)

        # Boş durum
        self.empty_label = QLabel("Bildirim yok")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 12px; padding: 20px;"
        )
        layout.addWidget(self.empty_label)

    def set_notifications(self, notifications: List[Dict[str, Any]]):
        """Bildirim listesini günceller."""
        self._notifications = notifications

        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not notifications:
            self.empty_label.setVisible(True)
            return

        self.empty_label.setVisible(False)
        for notif in notifications:
            item = NotificationItem(notif)
            item.clicked.connect(self.notification_clicked)
            self.list_layout.insertWidget(
                self.list_layout.count() - 1, item
            )
