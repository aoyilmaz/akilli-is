"""
Akıllı İş - QuickActionWidget

Hızlı işlem butonları widget'ı.
"""

from typing import Optional, List, Dict, Callable

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QPushButton,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from config.styles import COLORS, FONT_FAMILY_QT
from .base import BaseWidget, WidgetConfig


class QuickActionButton(QPushButton):
    """Hızlı işlem butonu"""

    def __init__(self, text: str, icon: str = "", color: str = "", parent=None):
        super().__init__(parent)
        self.setText(text)

        # Stil
        bg_color = color or COLORS['bg_secondary']
        hover_color = COLORS.get('bg_hover', '#e9ecef')

        self.setFont(QFont(FONT_FAMILY_QT, 10))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(40)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setStyleSheet(f"""
            QPushButton {{
                background: {bg_color};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 12px;
                color: {COLORS['text_primary']};
                text-align: left;
            }}
            QPushButton:hover {{
                background: {hover_color};
                border-color: {COLORS['primary']};
            }}
            QPushButton:pressed {{
                background: {COLORS['border']};
            }}
        """)


class QuickActionWidget(BaseWidget):
    """
    Hızlı işlem butonları widget'ı

    Role göre farklı işlem butonları gösterir.
    """

    widget_code = "quick_actions"
    widget_name = "Hızlı İşlemler"
    widget_type = "action"
    widget_description = "Sık kullanılan işlemler"
    widget_icon = "bolt"
    min_size = (1, 1)
    default_size = (1, 1)
    max_size = (2, 2)
    refresh_interval = 0  # Yenileme gerekli değil

    # Signals
    action_triggered = pyqtSignal(str)  # action_code

    # Varsayılan aksiyonlar
    DEFAULT_ACTIONS = [
        {
            "code": "new_sales_order",
            "text": "Yeni Sipariş",
            "icon": "plus",
            "permission": "sales.create",
            "page": "sales_orders"
        },
        {
            "code": "new_purchase",
            "text": "Satınalma Talebi",
            "icon": "shopping-cart",
            "permission": "purchasing.create",
            "page": "purchase_requests"
        },
        {
            "code": "new_work_order",
            "text": "İş Emri Oluştur",
            "icon": "industry",
            "permission": "production.create",
            "page": "work_orders"
        },
        {
            "code": "stock_check",
            "text": "Stok Sorgula",
            "icon": "boxes",
            "permission": "inventory.view",
            "page": "stock_cards"
        },
    ]

    def __init__(
        self,
        config: Optional[WidgetConfig] = None,
        edit_mode: bool = False,
        parent: Optional[QWidget] = None
    ):
        self._action_callbacks: Dict[str, Callable] = {}
        super().__init__(config, edit_mode, parent)

    def create_content(self):
        """Widget içeriğini oluşturur"""
        self.buttons_layout = QGridLayout()
        self.buttons_layout.setSpacing(8)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)

        self.content_layout.addLayout(self.buttons_layout)
        self.content_layout.addStretch()

    def refresh_data(self):
        """Butonları yeniler (kullanıcı izinlerine göre)"""
        # Mevcut butonları temizle
        while self.buttons_layout.count():
            item = self.buttons_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            from core.user_context import get_current_user

            user = get_current_user()
            if not user:
                return

            permissions = user.permissions or []
            is_admin = user.is_superuser

            # Kullanıcının erişebildiği aksiyonları filtrele
            available_actions = []
            for action in self.DEFAULT_ACTIONS:
                required_perm = action.get("permission")
                if is_admin or not required_perm or required_perm in permissions:
                    available_actions.append(action)

            # Butonları oluştur
            row = 0
            col = 0
            max_cols = 2 if self._config.size.get("width", 1) > 1 else 1

            for action in available_actions[:6]:  # Maksimum 6 buton
                btn = QuickActionButton(action["text"], action.get("icon", ""))
                btn.clicked.connect(lambda checked, a=action: self._on_action_clicked(a))
                self.buttons_layout.addWidget(btn, row, col)

                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

        except Exception as e:
            print(f"QuickActionWidget hatası: {e}")

    def _on_action_clicked(self, action: dict):
        """Aksiyona tıklandığında"""
        action_code = action.get("code")
        page = action.get("page")

        # Callback varsa çağır
        if action_code in self._action_callbacks:
            self._action_callbacks[action_code]()

        # Sinyal gönder
        self.action_triggered.emit(action_code)

        # Sayfaya yönlendir (main_window'a sinyal ile)
        if page:
            try:
                # Ana pencereye erişmeye çalış
                main_window = self.window()
                if hasattr(main_window, 'navigate_to_page'):
                    main_window.navigate_to_page(page)
            except Exception as e:
                print(f"Sayfa yönlendirme hatası: {e}")

    def set_action_callback(self, action_code: str, callback: Callable):
        """Aksiyon için callback ayarlar"""
        self._action_callbacks[action_code] = callback

    def add_custom_action(self, code: str, text: str, icon: str = "",
                          permission: str = None, callback: Callable = None):
        """Özel aksiyon ekler"""
        action = {
            "code": code,
            "text": text,
            "icon": icon,
            "permission": permission
        }

        # Mevcut aksiyonlara ekle
        self.DEFAULT_ACTIONS.append(action)

        if callback:
            self._action_callbacks[code] = callback

        # Yeniden yükle
        self.refresh_data()
