"""
Akıllı İş ERP - Sidebar Widget (Düzeltilmiş)
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
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtSvgWidgets import QSvgWidget
from pathlib import Path

from config import APP_NAME, APP_VERSION, BASE_DIR
from config.themes import get_theme, ThemeManager, THEMES


class MenuButton(QPushButton):
    def __init__(self, text: str, icon_text: str = "", page_id: str = "", parent=None):
        super().__init__(parent)
        self.page_id = page_id
        self.icon_text = icon_text
        self._selected = False
        self.setText(f"  {icon_text}  {text}" if icon_text else text)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(44)
        self.update_style()

    def update_style(self):
        t = get_theme()
        if self._selected:
            self.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {t.accent_primary};
                    color: white;
                    border: none;
                    border-radius: {t.radius_medium}px;
                    text-align: left;
                    padding-left: 16px;
                    font-weight: 600;
                    font-size: {t.font_size}px;
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
                    text-align: left;
                    padding-left: 16px;
                    font-size: {t.font_size}px;
                }}
                QPushButton:hover {{
                    background-color: {t.bg_hover};
                    color: {t.text_primary};
                }}
            """
            )

    def set_selected(self, selected: bool):
        self._selected = selected
        self.setChecked(selected)
        self.update_style()


class SubMenuButton(QPushButton):
    def __init__(self, text: str, page_id: str = "", parent=None):
        super().__init__(parent)
        self.page_id = page_id
        self._selected = False
        self.setText(text)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(36)
        self.update_style()

    def update_style(self):
        t = get_theme()
        if self._selected:
            self.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {t.bg_selected};
                    color: {t.text_accent};
                    border: none;
                    border-radius: {t.radius_small}px;
                    text-align: left;
                    padding-left: 48px;
                    font-size: {t.font_size_small + 1}px;
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
                    border-radius: {t.radius_small}px;
                    text-align: left;
                    padding-left: 48px;
                    font-size: {t.font_size_small + 1}px;
                }}
                QPushButton:hover {{
                    background-color: {t.bg_hover};
                    color: {t.text_secondary};
                }}
            """
            )

    def set_selected(self, selected: bool):
        self._selected = selected
        self.setChecked(selected)
        self.update_style()


class Sidebar(QFrame):
    page_changed = pyqtSignal(str)
    sidebar_toggled = pyqtSignal(bool)
    theme_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.collapsed = False
        self.current_page = "dashboard"
        self.menu_buttons = {}
        self.submenu_buttons = {}
        self.expanded_menus = set()
        self.setup_ui()
        ThemeManager.register_callback(self._on_theme_changed)

    def _on_theme_changed(self, theme):
        self._apply_styles()
        for btn in self.menu_buttons.values():
            btn.update_style()
        for btn in self.submenu_buttons.values():
            btn.update_style()

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
        t = get_theme()

        self.setObjectName("sidebar")
        self.setFixedWidth(260)
        self._apply_styles()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        logo_frame = self.create_logo_section()
        layout.addWidget(logo_frame)
        layout.addSpacing(16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        menu_widget = QWidget()
        menu_widget.setStyleSheet("background: transparent;")
        menu_layout = QVBoxLayout(menu_widget)
        menu_layout.setContentsMargins(0, 0, 0, 0)
        menu_layout.setSpacing(4)

        self.add_menu_items(menu_layout)
        menu_layout.addStretch()
        scroll.setWidget(menu_widget)
        layout.addWidget(scroll)

        theme_frame = self.create_theme_selector()
        layout.addWidget(theme_frame)

        user_frame = self.create_user_section()
        layout.addWidget(user_frame)

    def create_logo_section(self) -> QFrame:
        t = get_theme()

        frame = QFrame()
        frame.setStyleSheet("background: transparent;")
        frame.setFixedHeight(60)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 0, 8, 0)

        logo_path = Path(BASE_DIR) / "assets" / "favicon.svg"
        if logo_path.exists():
            logo = QSvgWidget(str(logo_path))
            logo.setFixedSize(40, 40)
            layout.addWidget(logo)
        else:
            logo_label = QLabel("🔄")
            logo_label.setStyleSheet("font-size: 32px; background: transparent;")
            layout.addWidget(logo_label)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(0)
        title = QLabel(APP_NAME)
        title.setStyleSheet(
            f"font-size: 18px; font-weight: 700; color: {t.text_primary}; background: transparent;"
        )
        title_layout.addWidget(title)
        version = QLabel(f"v{APP_VERSION}")
        version.setStyleSheet(
            f"font-size: 11px; color: {t.text_muted}; background: transparent;"
        )
        title_layout.addWidget(version)
        layout.addLayout(title_layout)
        layout.addStretch()

        toggle_btn = QPushButton("◀")
        toggle_btn.setFixedSize(28, 28)
        toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {t.bg_tertiary};
                color: {t.text_muted};
                border: none;
                border-radius: 8px;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: {t.bg_hover};
                color: {t.text_primary};
            }}
        """
        )
        toggle_btn.clicked.connect(self.toggle_sidebar)
        layout.addWidget(toggle_btn)

        return frame

    def create_theme_selector(self) -> QFrame:
        t = get_theme()

        frame = QFrame()
        frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {t.bg_tertiary};
                border-radius: {t.radius_medium}px;
            }}
        """
        )

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        theme_icon = QLabel("🎨")
        theme_icon.setStyleSheet("font-size: 14px; background: transparent;")
        layout.addWidget(theme_icon)

        self.theme_combo = QComboBox()
        self.theme_combo.setStyleSheet(
            f"""
            QComboBox {{
                background-color: {t.bg_secondary};
                border: 1px solid {t.border};
                border-radius: {t.radius_small}px;
                padding: 6px 10px;
                color: {t.text_primary};
                min-width: 140px;
            }}
            QComboBox:hover {{
                border-color: {t.border_light};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 8px;
            }}
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

        current_index = list(THEMES.keys()).index(t.name)
        self.theme_combo.setCurrentIndex(current_index)

        self.theme_combo.currentIndexChanged.connect(self._on_theme_selected)
        layout.addWidget(self.theme_combo)

        return frame

    def _on_theme_selected(self, index):
        theme_name = self.theme_combo.currentData()
        if theme_name:
            ThemeManager.set_theme(theme_name)
            self.theme_changed.emit(theme_name)

    def add_menu_items(self, layout: QVBoxLayout):
        menu_structure = [
            ("dashboard", "Dashboard", "📊", []),
            (
                "inventory",
                "Stok Yönetimi",
                "📦",
                [
                    ("stock-cards", "Stok Kartları"),
                    ("categories", "Kategoriler"),
                    ("units", "Birimler"),
                    ("warehouses", "Depolar"),
                    ("movements", "Stok Hareketleri"),
                    ("stock-count", "Stok Sayımı"),
                    ("stock-reports", "Stok Raporları"),
                ],
            ),
            (
                "production",
                "Üretim",
                "🏭",
                [
                    ("work-orders", "İş Emirleri"),
                    ("bom", "Ürün Reçeteleri"),
                    ("planning", "Üretim Planlama"),
                    ("work-stations", "İş İstasyonları"),
                ],
            ),
            ("purchasing", "Satın Alma", "🛒", []),
            ("sales", "Satış", "💰", []),
            ("finance", "Finans", "💳", []),
            ("hr", "İnsan Kaynakları", "👥", []),
            ("reports", "Raporlar", "📈", []),
            ("settings", "Ayarlar", "⚙️", []),
        ]

        for menu_id, title, icon, submenus in menu_structure:
            btn = MenuButton(title, icon, menu_id)
            btn.clicked.connect(
                lambda checked, m=menu_id, s=submenus: self.on_menu_click(m, s)
            )
            self.menu_buttons[menu_id] = btn
            layout.addWidget(btn)

            if submenus:
                submenu_container = QWidget()
                submenu_container.setStyleSheet("background: transparent;")
                submenu_container.setVisible(False)
                submenu_layout = QVBoxLayout(submenu_container)
                submenu_layout.setContentsMargins(0, 4, 0, 4)
                submenu_layout.setSpacing(2)

                for sub_id, sub_title in submenus:
                    sub_btn = SubMenuButton(sub_title, sub_id)
                    sub_btn.clicked.connect(
                        lambda checked, p=sub_id: self.select_page(p)
                    )
                    self.submenu_buttons[sub_id] = sub_btn
                    submenu_layout.addWidget(sub_btn)

                layout.addWidget(submenu_container)
                btn.submenu_container = submenu_container

        self.menu_buttons["dashboard"].set_selected(True)

    def create_user_section(self) -> QFrame:
        t = get_theme()

        frame = QFrame()
        frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {t.bg_tertiary};
                border-radius: {t.radius_medium}px;
            }}
        """
        )

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)

        avatar = QLabel("OK")
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(
            f"""
            background-color: {t.success};
            color: white;
            font-weight: 700;
            font-size: 13px;
            border-radius: 18px;
        """
        )
        layout.addWidget(avatar)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(0)
        name = QLabel("Okan")
        name.setStyleSheet(
            f"color: {t.text_secondary}; font-weight: 600; font-size: 13px; background: transparent;"
        )
        info_layout.addWidget(name)
        role = QLabel("Yönetici")
        role.setStyleSheet(
            f"color: {t.text_muted}; font-size: 11px; background: transparent;"
        )
        info_layout.addWidget(role)
        layout.addLayout(info_layout)
        layout.addStretch()

        return frame

    def on_menu_click(self, menu_id: str, submenus: list):
        btn = self.menu_buttons[menu_id]
        if submenus:
            if menu_id in self.expanded_menus:
                self.expanded_menus.remove(menu_id)
                btn.submenu_container.setVisible(False)
            else:
                self.expanded_menus.add(menu_id)
                btn.submenu_container.setVisible(True)
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
        self.sidebar_toggled.emit(self.collapsed)
