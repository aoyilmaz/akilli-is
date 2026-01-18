"""
Akıllı İş - NotificationWidget

Okunmamış bildirimleri listeleyen widget.
"""

from typing import Optional, List
from datetime import datetime

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
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from config.styles import COLORS, FONT_FAMILY_QT
from .base import BaseWidget, WidgetConfig


class NotificationItem(QFrame):
    """Tek bir bildirim öğesi"""

    clicked = pyqtSignal(int)  # notification_id
    mark_read = pyqtSignal(int)

    # Bildirim türü renkleri
    TYPE_COLORS = {
        "info": COLORS.get("info", "#17a2b8"),
        "warning": COLORS.get("warning", "#ffc107"),
        "error": COLORS.get("danger", "#dc3545"),
        "success": COLORS.get("success", "#28a745"),
        "action_required": COLORS.get("primary", "#007bff"),
    }

    def __init__(self, notification_id: int, title: str, message: str,
                 notification_type: str, created_at: datetime, parent=None):
        super().__init__(parent)
        self.notification_id = notification_id
        self.notification_type = notification_type

        self._setup_ui(title, message, created_at)
        self._setup_style()

    def _setup_ui(self, title: str, message: str, created_at: datetime):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        # Üst satır: Başlık ve zaman
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # Tür göstergesi
        type_indicator = QLabel("●")
        type_indicator.setFixedWidth(12)
        color = self.TYPE_COLORS.get(self.notification_type, COLORS['text_secondary'])
        type_indicator.setStyleSheet(f"color: {color}; font-size: 8px;")
        header_layout.addWidget(type_indicator)

        # Başlık
        title_label = QLabel(title)
        title_label.setFont(QFont(FONT_FAMILY_QT, 10, QFont.Weight.DemiBold))
        title_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        title_label.setWordWrap(True)
        header_layout.addWidget(title_label, 1)

        # Zaman
        time_str = self._format_time(created_at)
        time_label = QLabel(time_str)
        time_label.setFont(QFont(FONT_FAMILY_QT, 9))
        time_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        header_layout.addWidget(time_label)

        layout.addLayout(header_layout)

        # Mesaj
        if message:
            msg_label = QLabel(message[:100] + "..." if len(message) > 100 else message)
            msg_label.setFont(QFont(FONT_FAMILY_QT, 9))
            msg_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
            msg_label.setWordWrap(True)
            layout.addWidget(msg_label)

    def _setup_style(self):
        self.setStyleSheet(f"""
            NotificationItem {{
                background: {COLORS['bg_secondary']};
                border-radius: 4px;
                border: none;
            }}
            NotificationItem:hover {{
                background: {COLORS['bg_hover']};
            }}
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _format_time(self, dt: datetime) -> str:
        """Zamanı formatlar"""
        now = datetime.now()
        diff = now - dt

        if diff.days == 0:
            if diff.seconds < 60:
                return "Az önce"
            elif diff.seconds < 3600:
                return f"{diff.seconds // 60} dk önce"
            else:
                return f"{diff.seconds // 3600} saat önce"
        elif diff.days == 1:
            return "Dün"
        elif diff.days < 7:
            return f"{diff.days} gün önce"
        else:
            return dt.strftime("%d.%m.%Y")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.notification_id)
        super().mousePressEvent(event)


class NotificationWidget(BaseWidget):
    """
    Bildirim listesi widget'ı

    Okunmamış bildirimleri listeler, tıklandığında okundu işaretler.
    """

    widget_code = "notifications"
    widget_name = "Bildirimler"
    widget_type = "list"
    widget_description = "Okunmamış bildirimler listesi"
    widget_icon = "bell"
    min_size = (1, 1)
    default_size = (1, 2)
    max_size = (2, 2)
    refresh_interval = 60  # 1 dakika

    # Signals
    notification_clicked = pyqtSignal(int)

    def __init__(
        self,
        config: Optional[WidgetConfig] = None,
        edit_mode: bool = False,
        parent: Optional[QWidget] = None
    ):
        self._notifications: List[dict] = []
        super().__init__(config, edit_mode, parent)

    def create_content(self):
        """Widget içeriğini oluşturur"""
        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['border']};
                border-radius: 3px;
            }}
        """)

        # İçerik container
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(4)
        self.list_layout.addStretch()

        self.scroll_area.setWidget(self.list_container)
        self.content_layout.addWidget(self.scroll_area, 1)

        # Boş durum mesajı
        self.empty_label = QLabel("Bildirim yok")
        self.empty_label.setFont(QFont(FONT_FAMILY_QT, 10))
        self.empty_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setVisible(False)
        self.content_layout.addWidget(self.empty_label)

        # Alt butonlar
        button_layout = QHBoxLayout()

        self.mark_all_btn = QPushButton("Tümünü Okundu İşaretle")
        self.mark_all_btn.setFont(QFont(FONT_FAMILY_QT, 9))
        self.mark_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mark_all_btn.clicked.connect(self._mark_all_read)
        self.mark_all_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {COLORS['primary']};
                padding: 4px;
            }}
            QPushButton:hover {{
                text-decoration: underline;
            }}
        """)
        button_layout.addWidget(self.mark_all_btn)
        button_layout.addStretch()

        self.content_layout.addLayout(button_layout)

    def refresh_data(self):
        """Bildirimleri yeniler"""
        self.set_loading(True)

        try:
            from core.user_context import get_current_user
            from modules.notifications.services import NotificationService

            user = get_current_user()
            if not user:
                self._show_empty()
                return

            # Son bildirimleri al
            notifications = NotificationService.get_latest(
                user_id=user.user_id,
                limit=10,
                include_read=False
            )

            self._notifications = []
            for n in notifications:
                self._notifications.append({
                    "id": n.id,
                    "title": n.title,
                    "message": n.message,
                    "type": n.notification_type,
                    "created_at": n.created_at,
                    "link": n.link
                })

            self._update_list()

        except Exception as e:
            print(f"NotificationWidget hatası: {e}")
            self._show_empty()
        finally:
            self.set_loading(False)

    def _update_list(self):
        """Bildirim listesini günceller"""
        # Mevcut öğeleri temizle
        while self.list_layout.count() > 1:  # Stretch hariç
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._notifications:
            self._show_empty()
            return

        self.scroll_area.setVisible(True)
        self.empty_label.setVisible(False)
        self.mark_all_btn.setVisible(True)

        # Bildirimleri ekle
        for i, notif in enumerate(self._notifications):
            item = NotificationItem(
                notification_id=notif["id"],
                title=notif["title"],
                message=notif["message"],
                notification_type=notif["type"],
                created_at=notif["created_at"],
                parent=self.list_container
            )
            item.clicked.connect(self._on_notification_clicked)
            self.list_layout.insertWidget(i, item)

        # Başlığı güncelle
        count = len(self._notifications)
        self.title_label.setText(f"Bildirimler ({count})")

    def _show_empty(self):
        """Boş durumu gösterir"""
        self.scroll_area.setVisible(False)
        self.empty_label.setVisible(True)
        self.mark_all_btn.setVisible(False)
        self.title_label.setText("Bildirimler")

    def _on_notification_clicked(self, notification_id: int):
        """Bildirime tıklandığında"""
        try:
            from core.user_context import get_current_user
            from modules.notifications.services import NotificationService

            user = get_current_user()
            if user:
                NotificationService.mark_as_read(notification_id, user.user_id)

            # Sinyal gönder
            self.notification_clicked.emit(notification_id)

            # Listeyi yenile
            self.refresh_data()

        except Exception as e:
            print(f"Bildirim okundu işaretleme hatası: {e}")

    def _mark_all_read(self):
        """Tüm bildirimleri okundu işaretle"""
        try:
            from core.user_context import get_current_user
            from modules.notifications.services import NotificationService

            user = get_current_user()
            if user:
                NotificationService.mark_all_as_read(user.user_id)

            # Listeyi yenile
            self.refresh_data()

        except Exception as e:
            print(f"Toplu okundu işaretleme hatası: {e}")
