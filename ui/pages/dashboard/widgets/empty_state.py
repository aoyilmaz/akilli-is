"""
Akıllı İş - Empty State Bileşeni

Widget'larda veri olmadığında gösterilen modern boş durum ekranı.
"""

from typing import Optional, Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from config.styles import COLORS, FONT_FAMILY_QT, get_button_style


# Emoji ikonları - basit ve cross-platform
EMPTY_STATE_ICONS = {
    "inbox": "📥",
    "search": "🔍",
    "chart": "📊",
    "list": "📋",
    "notification": "🔔",
    "warning": "⚠️",
    "error": "❌",
    "success": "✅",
    "data": "📈",
    "calendar": "📅",
    "clock": "⏰",
    "folder": "📁",
    "document": "📄",
    "user": "👤",
    "settings": "⚙️",
    "refresh": "🔄",
}


class EmptyStateWidget(QFrame):
    """
    Modern boş durum gösterge bileşeni.

    Veri olmadığında veya hata durumlarında gösterilir.
    İkon, mesaj ve opsiyonel aksiyon butonu içerir.
    """

    action_clicked = pyqtSignal()

    def __init__(
        self,
        icon: str = "inbox",
        title: str = "Veri yok",
        message: str = "",
        action_text: Optional[str] = None,
        action_callback: Optional[Callable] = None,
        parent: Optional[QWidget] = None
    ):
        """
        Args:
            icon: İkon adı (EMPTY_STATE_ICONS'dan)
            title: Ana başlık
            message: Açıklama mesajı
            action_text: Aksiyon butonu metni (opsiyonel)
            action_callback: Buton tıklanınca çağrılacak fonksiyon
            parent: Parent widget
        """
        super().__init__(parent)
        self._action_callback = action_callback
        self._setup_ui(icon, title, message, action_text)
        self._setup_style()

    def _setup_ui(
        self,
        icon: str,
        title: str,
        message: str,
        action_text: Optional[str]
    ):
        """UI elemanlarını oluştur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 24, 16, 24)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # İkon
        icon_label = QLabel(EMPTY_STATE_ICONS.get(icon, "📥"))
        icon_label.setStyleSheet(f"""
            font-size: 48px;
            color: {COLORS['text_muted']};
        """)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # Başlık
        title_label = QLabel(title)
        title_label.setFont(QFont(FONT_FAMILY_QT, 14, QFont.Weight.DemiBold))
        title_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # Mesaj (opsiyonel)
        if message:
            msg_label = QLabel(message)
            msg_label.setFont(QFont(FONT_FAMILY_QT, 11))
            msg_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
            msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            msg_label.setWordWrap(True)
            layout.addWidget(msg_label)

        # Aksiyon butonu (opsiyonel)
        if action_text:
            layout.addSpacing(8)
            action_btn = QPushButton(action_text)
            action_btn.setStyleSheet(get_button_style("primary"))
            action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            action_btn.clicked.connect(self._on_action_clicked)
            action_btn.setFixedHeight(32)
            layout.addWidget(
                action_btn,
                alignment=Qt.AlignmentFlag.AlignCenter
            )

    def _setup_style(self):
        """Widget stilini ayarla"""
        self.setStyleSheet(f"""
            EmptyStateWidget, QFrame {{
                background: transparent;
                border: none;
            }}
        """)

    def _on_action_clicked(self):
        """Aksiyon butonuna tıklandı"""
        self.action_clicked.emit()
        if self._action_callback:
            self._action_callback()


class ErrorStateWidget(EmptyStateWidget):
    """Hata durumu göstergesi"""

    def __init__(
        self,
        error_message: str = "Bir hata oluştu",
        retry_callback: Optional[Callable] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(
            icon="error",
            title="Hata",
            message=error_message,
            action_text="Tekrar Dene" if retry_callback else None,
            action_callback=retry_callback,
            parent=parent
        )


class NoDataWidget(EmptyStateWidget):
    """Veri yok durumu göstergesi"""

    def __init__(
        self,
        data_type: str = "veri",
        create_callback: Optional[Callable] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(
            icon="inbox",
            title=f"Henüz {data_type} yok",
            message=f"Görüntülenecek {data_type} bulunamadı.",
            action_text="Yeni Ekle" if create_callback else None,
            action_callback=create_callback,
            parent=parent
        )


class LoadingFailedWidget(EmptyStateWidget):
    """Yükleme başarısız durumu"""

    def __init__(
        self,
        retry_callback: Optional[Callable] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(
            icon="warning",
            title="Yüklenemedi",
            message="Veriler yüklenirken bir sorun oluştu.",
            action_text="Yenile" if retry_callback else None,
            action_callback=retry_callback,
            parent=parent
        )


class SearchEmptyWidget(EmptyStateWidget):
    """Arama sonucu yok durumu"""

    def __init__(
        self,
        search_term: str = "",
        clear_callback: Optional[Callable] = None,
        parent: Optional[QWidget] = None
    ):
        message = f'"{search_term}" için sonuç bulunamadı.' if search_term \
            else "Aramanızla eşleşen sonuç bulunamadı."

        super().__init__(
            icon="search",
            title="Sonuç Yok",
            message=message,
            action_text="Aramayı Temizle" if clear_callback else None,
            action_callback=clear_callback,
            parent=parent
        )
