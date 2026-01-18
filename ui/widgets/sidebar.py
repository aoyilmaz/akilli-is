"""
Akıllı İş ERP - Sidebar Widget
PyERP Pro stili - Modern, badge'li, gradient'li
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
    QComboBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QLinearGradient, QPainterPath

from config import APP_NAME, APP_VERSION
from config.themes import get_theme, ThemeManager, THEMES


# Emoji ikonlar
ICONS = {
    "dashboard": "📊",
    "inventory": "📦",
    "production": "🏭",
    "purchasing": "🛒",
    "sales": "📈",
    "finance": "💳",
    "hr": "👥",
    "reports": "📊",
    "settings": "⚙️",
    "stock-cards": "🗃️",
    "categories": "📁",
    "units": "📏",
    "warehouses": "🏪",
    "movements": "↔️",
    "stock-count": "📋",
    "stock-reports": "📊",
    "bom": "📝",
    "work-stations": "🔧",
    "work-orders": "📋",
    "planning": "📅",
    "calendar": "🗓️",
}


def get_icon(name: str) -> str:
    return ICONS.get(name, "•")


class AkilliIsLogo(QWidget):
    """Akıllı İş Logosu - Tıklanabilir"""

    clicked = pyqtSignal()

    def __init__(self, size: int = 40, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Gradient arka plan (rounded rect)
        gradient = QLinearGradient(0, 0, self._size, self._size)
        gradient.setColorAt(0, QColor("#6366f1"))
        gradient.setColorAt(1, QColor("#a855f7"))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(0, 0, self._size, self._size, 12, 12)

        # İç logo (beyaz)
        center = self._size / 2
        scale = self._size / 100

        painter.setPen(QPen(QColor("white"), 4 * scale))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Dış daire
        r1 = 30 * scale
        painter.drawEllipse(QPointF(center, center), r1, r1)

        # İç dolu daire
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("white"))
        r2 = 10 * scale
        painter.drawEllipse(QPointF(center, center), r2, r2)

        # Zap/şimşek ikonu - basit
        pen = QPen(QColor("white"), 3 * scale)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        # Şimşek çizgisi
        path = QPainterPath()
        path.moveTo(center + 2 * scale, center - 12 * scale)
        path.lineTo(center - 4 * scale, center + 2 * scale)
        path.lineTo(center + 2 * scale, center + 2 * scale)
        path.lineTo(center - 2 * scale, center + 12 * scale)
        painter.drawPath(path)


class MenuButton(QPushButton):
    """Ana menü butonu - Badge destekli"""

    def __init__(
        self,
        text: str,
        icon_name: str = "",
        page_id: str = "",
        badge: int = 0,
        parent=None,
    ):
        super().__init__(parent)
        self.page_id = page_id
        self.icon_name = icon_name
        self.full_text = text
        self.badge = badge
        self._selected = False
        self._collapsed = False
        self._has_children = False
        self._expanded = False
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(44)
        self._update_text()
        self.update_style()

    def set_has_children(self, has: bool):
        self._has_children = has
        self._update_text()

    def set_expanded(self, expanded: bool):
        self._expanded = expanded
        self._update_text()

    def _update_text(self):
        icon = get_icon(self.icon_name) if self.icon_name else ""
        if self._collapsed:
            self.setText(icon)
            self.setToolTip(self.full_text)
        else:
            arrow = ""
            if self._has_children:
                arrow = " ▼" if self._expanded else " ▶"
            self.setText(
                f"  {icon}   {self.full_text}{arrow}" if icon else self.full_text
            )
            self.setToolTip("")

    def set_collapsed(self, collapsed: bool):
        self._collapsed = collapsed
        self._update_text()
        self.update_style()

    def update_style(self):
        t = get_theme()

        if self._collapsed:
            align = "center"
            padding = "0px"
            font_size = "18px"
        else:
            align = "left"
            padding = "12px"
            font_size = f"{t.font_size}px"

        if self._selected:
            # Gradient arka plan efekti
            self.setStyleSheet(
                f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 rgba(99, 102, 241, 0.2), stop:1 rgba(168, 85, 247, 0.2));
                    color: {t.accent_primary};
                    border: none;
                    border-radius: {t.radius_medium}px;
                    text-align: {align};
                    padding-left: {padding};
                    font-weight: 600;
                    font-size: {font_size};
                    margin: 2px 8px;
                }}
            """
            )
        else:
            self.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: transparent;
                    color: {t.text_muted};
                    border: none;
                    border-radius: {t.radius_medium}px;
                    text-align: {align};
                    padding-left: {padding};
                    font-size: {font_size};
                    margin: 2px 8px;
                }}
                QPushButton:hover {{
                    background-color: {t.bg_hover}80;
                    color: {t.text_secondary};
                }}
            """
            )

    def set_selected(self, selected: bool):
        self._selected = selected
        self.setChecked(selected)
        self.update_style()

    def paintEvent(self, event):
        super().paintEvent(event)

        # Badge çiz
        if self.badge > 0 and not self._collapsed:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            t = get_theme()

            # Badge arka plan
            badge_text = str(self.badge)
            badge_width = max(20, len(badge_text) * 8 + 10)
            badge_height = 18
            badge_x = self.width() - badge_width - 40
            badge_y = (self.height() - badge_height) // 2

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(t.accent_primary))
            painter.drawRoundedRect(badge_x, badge_y, badge_width, badge_height, 9, 9)

            # Badge text
            painter.setPen(QColor("white"))
            from PyQt6.QtGui import QFont

            font = QFont()
            font.setPointSize(9)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(
                badge_x,
                badge_y,
                badge_width,
                badge_height,
                Qt.AlignmentFlag.AlignCenter,
                badge_text,
            )


class SubMenuButton(QPushButton):
    """Alt menü butonu"""

    def __init__(self, text: str, page_id: str = "", parent=None):
        super().__init__(parent)
        self.page_id = page_id
        self.full_text = text
        self._selected = False
        self._collapsed = False
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(36)
        self._update_text()
        self.update_style()

    def _update_text(self):
        if self._collapsed:
            self.setText("•")
            self.setToolTip(self.full_text)
        else:
            self.setText(self.full_text)
            self.setToolTip("")

    def set_collapsed(self, collapsed: bool):
        self._collapsed = collapsed
        self._update_text()
        self.update_style()

    def update_style(self):
        t = get_theme()

        if self._collapsed:
            align = "center"
            margin = "2px 8px"
        else:
            align = "left"
            margin = "1px 8px 1px 24px"

        if self._selected:
            self.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {t.accent_primary}15;
                    color: {t.accent_primary};
                    border: none;
                    border-radius: {t.radius_small}px;
                    text-align: {align};
                    padding-left: 16px;
                    font-size: {t.font_size_small + 1}px;
                    margin: {margin};
                }}
            """
            )
        else:
            self.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: transparent;
                    color: {t.text_muted};
                    border: none;
                    border-left: 2px solid {t.border};
                    border-radius: 0px;
                    text-align: {align};
                    padding-left: 14px;
                    font-size: {t.font_size_small + 1}px;
                    margin: {margin};
                }}
                QPushButton:hover {{
                    background-color: {t.bg_hover}50;
                    color: {t.text_secondary};
                }}
            """
            )

    def set_selected(self, selected: bool):
        self._selected = selected
        self.setChecked(selected)
        self.update_style()


class Sidebar(QFrame):
    """Ana sidebar - PyERP Pro stili"""

    page_changed = pyqtSignal(str)
    sidebar_toggled = pyqtSignal(bool)
    theme_changed = pyqtSignal(str)

    EXPANDED_WIDTH = 256
    COLLAPSED_WIDTH = 72

    def __init__(self, parent=None):
        super().__init__(parent)
        self.collapsed = False
        self.current_page = "dashboard"
        self.menu_buttons = {}
        self.submenu_buttons = {}
        self.expanded_menus = set()
        self.submenu_containers = {}
        self.setup_ui()
        ThemeManager.register_callback(self._on_theme_changed)

        # Bildirim kontrolü için timer (30 saniyede bir)
        self.notification_timer = QTimer(self)
        self.notification_timer.timeout.connect(self._check_notifications)
        self.notification_timer.start(30000)  # 30 saniye

        # İlk kontrol (1 saniye sonra - UI hazır olunca)
        QTimer.singleShot(1000, self._check_notifications)

    def _on_theme_changed(self, theme):
        self._apply_styles()
        for btn in self.menu_buttons.values():
            btn.update_style()
        for btn in self.submenu_buttons.values():
            btn.update_style()

    def _check_notifications(self):
        """Bildirim sayılarını kontrol et ve badge'leri güncelle"""
        try:
            from core.user_context import get_current_user
            from modules.notifications.services import NotificationService

            user = get_current_user()
            if not user or not user.user_id:
                return

            # Modül bazlı bildirim sayılarını al
            counts = NotificationService.get_module_counts(user.user_id)

            # Menu butonlarının badge'lerini güncelle
            for module_id, btn in self.menu_buttons.items():
                badge_count = counts.get(module_id, 0)
                if btn.badge != badge_count:
                    btn.badge = badge_count
                    btn.update()

        except Exception as e:
            # Bildirim kontrolü hatası uygulamayı etkilememeli
            print(f"Bildirim kontrolü hatası: {e}")

    def start_notification_timer(self):
        """Bildirim timer'ını başlat (login sonrası çağrılabilir)"""
        if not self.notification_timer.isActive():
            self.notification_timer.start(30000)
            self._check_notifications()

    def stop_notification_timer(self):
        """Bildirim timer'ını durdur (logout sonrası çağrılabilir)"""
        self.notification_timer.stop()

    def _apply_styles(self):
        t = get_theme()
        self.setStyleSheet(
            f"""
            QFrame#sidebar {{
                background-color: {t.sidebar_bg};
                border-right: 1px solid {t.border};
            }}
        """
        )

    def setup_ui(self):
        self.setObjectName("sidebar")
        self.setFixedWidth(self.EXPANDED_WIDTH)
        self._apply_styles()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo bölümü
        logo_frame = self.create_logo_section()
        layout.addWidget(logo_frame)

        # Ayırıcı
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {get_theme().border};")
        layout.addWidget(sep)

        # Menü
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        menu_widget = QWidget()
        menu_widget.setStyleSheet("background: transparent;")
        self.menu_layout = QVBoxLayout(menu_widget)
        self.menu_layout.setContentsMargins(4, 12, 4, 12)
        self.menu_layout.setSpacing(2)

        self.add_menu_items(self.menu_layout)
        self.menu_layout.addStretch()
        scroll.setWidget(menu_widget)
        layout.addWidget(scroll)

        # Alt bölüm
        bottom = QFrame()
        bottom.setStyleSheet("background: transparent;")
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(8, 8, 8, 12)
        bottom_layout.setSpacing(8)

        self.theme_frame = self.create_theme_selector()
        bottom_layout.addWidget(self.theme_frame)

        self.user_frame = self.create_user_section()
        bottom_layout.addWidget(self.user_frame)

        layout.addWidget(bottom)

    def create_logo_section(self) -> QFrame:
        t = get_theme()

        frame = QFrame()
        frame.setStyleSheet("background: transparent;")
        frame.setFixedHeight(64)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 12, 12, 12)
        layout.setSpacing(12)

        # Logo - TIKLANABİLİR
        self.logo = AkilliIsLogo(40)
        self.logo.clicked.connect(self.toggle_sidebar)
        self.logo.setToolTip("Menüyü aç/kapat")
        layout.addWidget(self.logo)

        # Başlık
        self.title_widget = QWidget()
        self.title_widget.setStyleSheet("background: transparent;")
        title_layout = QVBoxLayout(self.title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)

        self.title_label = QLabel(APP_NAME)
        self.title_label.setStyleSheet(
            f"""
            font-size: 16px; 
            font-weight: 700; 
            color: {t.text_primary}; 
            background: transparent;
            letter-spacing: -0.5px;
        """
        )
        title_layout.addWidget(self.title_label)

        self.subtitle_label = QLabel(f"v{APP_VERSION}")
        self.subtitle_label.setStyleSheet(
            f"""
            font-size: 10px; 
            color: {t.text_muted}; 
            background: transparent;
        """
        )
        title_layout.addWidget(self.subtitle_label)

        layout.addWidget(self.title_widget)
        layout.addStretch()

        return frame

    def create_theme_selector(self) -> QFrame:
        t = get_theme()

        frame = QFrame()
        frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {t.bg_tertiary}80;
                border-radius: {t.radius_medium}px;
            }}
        """
        )

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        self.theme_icon = QLabel("🎨")
        self.theme_icon.setStyleSheet("font-size: 14px; background: transparent;")
        layout.addWidget(self.theme_icon)

        self.theme_combo = QComboBox()
        self.theme_combo.setStyleSheet(
            f"""
            QComboBox {{
                background-color: {t.bg_secondary};
                border: 1px solid {t.border};
                border-radius: 6px;
                padding: 6px 10px;
                color: {t.text_primary};
                min-width: 130px;
                font-size: 12px;
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{
                background-color: {t.bg_secondary};
                border: 1px solid {t.border};
                color: {t.text_primary};
                selection-background-color: {t.bg_hover};
            }}
        """
        )

        for name, theme in THEMES.items():
            self.theme_combo.addItem(theme.display_name, name)

        idx = list(THEMES.keys()).index(t.name)
        self.theme_combo.setCurrentIndex(idx)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_selected)
        layout.addWidget(self.theme_combo)

        return frame

    def _on_theme_selected(self, index):
        name = self.theme_combo.currentData()
        if name:
            ThemeManager.set_theme(name)
            self.theme_changed.emit(name)

    def add_menu_items(self, layout: QVBoxLayout):
        # İzin kontrolü için AuthService import
        try:
            from core.auth_service import AuthService
            from core.permission_map import get_menu_permission

            has_auth = True
        except ImportError:
            has_auth = False

        def can_access_menu(menu_id: str) -> bool:
            """Menüye erişim izni var mı?"""
            if not has_auth:
                return True  # Auth yoksa hepsini göster
            if not AuthService.is_authenticated():
                return True  # Development mode
            if AuthService.is_superuser():
                return True
            perm = get_menu_permission(menu_id)
            if perm is None:
                return True
            return AuthService.has_permission(perm)

        def can_access_page(page_id: str) -> bool:
            """Sayfaya erişim izni var mı?"""
            if not has_auth:
                return True
            if not AuthService.is_authenticated():
                return True
            return AuthService.can_access_page(page_id)

        # Badge'li menü yapısı
        menu_structure = [
            ("dashboard", "Dashboard", "dashboard", 0, []),
            (
                "inventory",
                "Stok Yönetimi",
                "inventory",
                0,
                [
                    ("stock-cards", "Stok Kartları"),
                    ("categories", "Kategoriler"),
                    ("units", "Birimler"),
                    ("warehouses", "Depolar"),
                    ("movements", "Stok Hareketleri"),
                    ("stock-count", "Sayım İşlemleri"),
                    ("stock-reports", "Stok Raporları"),
                ],
            ),
            (
                "production",
                "Üretim",
                "production",
                3,
                [
                    ("work-orders", "İş Emirleri"),
                    ("bom", "Ürün Reçeteleri"),
                    ("planning", "Üretim Planlama"),
                    ("work-stations", "İş İstasyonları"),
                    ("calendar", "Çalışma Takvimi"),
                ],
            ),
            (
                "purchasing",
                "Satın Alma",
                "purchasing",
                0,
                [
                    ("suppliers", "Tedarikçiler"),
                    ("purchase-requests", "Talepler"),
                    ("purchase-orders", "Siparişler"),
                    ("goods-receipts", "Mal Kabul"),
                ],
            ),
            ("sales", "Satış", "sales", 5, []),
            ("finance", "Finans", "finance", 0, []),
            (
                "hr",
                "İnsan Kaynakları",
                "hr",
                0,
                [
                    ("employees", "Çalışanlar"),
                    ("departments", "Departmanlar"),
                    ("positions", "Pozisyonlar"),
                    ("leaves", "İzin Yönetimi"),
                    ("org-chart", "Organizasyon Şeması"),
                    ("shift-teams", "Vardiya Ekipleri"),
                ],
            ),
            ("reports", "Raporlar", "reports", 0, []),
            (
                "settings",
                "Ayarlar",
                "settings",
                0,
                [
                    ("users", "Kullanıcı Yönetimi"),
                    ("settings", "Genel Ayarlar"),
                ],
            ),
        ]

        for menu_id, title, icon_name, badge, submenus in menu_structure:
            # Ana menü için izin kontrolü
            if not can_access_menu(menu_id):
                continue

            btn = MenuButton(title, icon_name, menu_id, badge)
            btn.set_has_children(len(submenus) > 0)
            btn.clicked.connect(
                lambda checked, m=menu_id, s=submenus: self.on_menu_click(m, s)
            )
            self.menu_buttons[menu_id] = btn
            layout.addWidget(btn)

            if submenus:
                container = QWidget()
                container.setStyleSheet("background: transparent;")
                container.setVisible(False)
                sub_layout = QVBoxLayout(container)
                sub_layout.setContentsMargins(0, 4, 0, 4)
                sub_layout.setSpacing(2)

                visible_submenus = 0
                for sub_id, sub_title in submenus:
                    # Alt menü için izin kontrolü
                    if not can_access_page(sub_id):
                        continue

                    sub_btn = SubMenuButton(sub_title, sub_id)
                    sub_btn.clicked.connect(
                        lambda checked, p=sub_id: self.select_page(p)
                    )
                    self.submenu_buttons[sub_id] = sub_btn
                    sub_layout.addWidget(sub_btn)
                    visible_submenus += 1

                # Alt menü yoksa parent'ı da gösterme
                if visible_submenus > 0:
                    layout.addWidget(container)
                    self.submenu_containers[menu_id] = container
                else:
                    # Alt menüsü olmayan menüyü gizle
                    btn.setVisible(False)

        self.menu_buttons["dashboard"].set_selected(True)

    def create_user_section(self) -> QFrame:
        t = get_theme()

        frame = QFrame()
        frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {t.bg_tertiary}80;
                border-radius: {t.radius_medium}px;
            }}
        """
        )

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)

        # Avatar - gradient
        self.avatar = QLabel("OK")
        self.avatar.setFixedSize(36, 36)
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar.setStyleSheet(
            f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                stop:0 #34d399, stop:1 #06b6d4);
            color: white;
            font-weight: 700;
            font-size: 12px;
            border-radius: 18px;
        """
        )
        layout.addWidget(self.avatar)

        self.user_info = QWidget()
        self.user_info.setStyleSheet("background: transparent;")
        info_layout = QVBoxLayout(self.user_info)
        info_layout.setContentsMargins(10, 0, 0, 0)
        info_layout.setSpacing(0)

        self.user_name = QLabel("Okan")
        self.user_name.setStyleSheet(
            f"""
            color: {t.text_primary}; 
            font-weight: 600; 
            font-size: 13px; 
            background: transparent;
        """
        )
        info_layout.addWidget(self.user_name)

        self.user_role = QLabel("Yönetici")
        self.user_role.setStyleSheet(
            f"""
            color: {t.text_muted}; 
            font-size: 11px; 
            background: transparent;
        """
        )
        info_layout.addWidget(self.user_role)

        layout.addWidget(self.user_info)
        layout.addStretch()

        return frame

    def on_menu_click(self, menu_id: str, submenus: list):
        if submenus:
            container = self.submenu_containers.get(menu_id)
            btn = self.menu_buttons.get(menu_id)
            if container:
                if menu_id in self.expanded_menus:
                    self.expanded_menus.remove(menu_id)
                    container.setVisible(False)
                    if btn:
                        btn.set_expanded(False)
                else:
                    self.expanded_menus.add(menu_id)
                    container.setVisible(True)
                    if btn:
                        btn.set_expanded(True)
        else:
            self.select_page(menu_id)

    def select_page(self, page_id: str):
        for btn in self.menu_buttons.values():
            btn.set_selected(False)
        for btn in self.submenu_buttons.values():
            btn.set_selected(False)

        if page_id in self.menu_buttons:
            self.menu_buttons[page_id].set_selected(True)
        elif page_id in self.submenu_buttons:
            self.submenu_buttons[page_id].set_selected(True)

        self.current_page = page_id
        self.page_changed.emit(page_id)

    def toggle_sidebar(self):
        self.collapsed = not self.collapsed

        target = self.COLLAPSED_WIDTH if self.collapsed else self.EXPANDED_WIDTH

        # Görünürlük
        self.title_widget.setVisible(not self.collapsed)
        self.theme_combo.setVisible(not self.collapsed)
        self.user_info.setVisible(not self.collapsed)

        # Butonları güncelle
        for btn in self.menu_buttons.values():
            btn.set_collapsed(self.collapsed)
        for btn in self.submenu_buttons.values():
            btn.set_collapsed(self.collapsed)

        # Alt menüleri gizle
        if self.collapsed:
            for container in self.submenu_containers.values():
                container.setVisible(False)

        self.setFixedWidth(target)
        self.sidebar_toggled.emit(self.collapsed)
