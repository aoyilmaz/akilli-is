"""
Akıllı İş ERP - Sidebar Widget
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtSvgWidgets import QSvgWidget
from pathlib import Path

from config import settings


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
        if self._selected:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 rgba(99, 102, 241, 0.2), stop:1 rgba(168, 85, 247, 0.2));
                    color: #818cf8; border: none; border-radius: 12px;
                    text-align: left; padding-left: 16px; font-weight: 600; font-size: 14px;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: transparent; color: #94a3b8; border: none;
                    border-radius: 12px; text-align: left; padding-left: 16px; font-size: 14px;
                }
                QPushButton:hover { background-color: rgba(51, 65, 85, 0.5); color: #e2e8f0; }
            """)

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
        if self._selected:
            self.setStyleSheet("""
                QPushButton {
                    background: rgba(99, 102, 241, 0.1); color: #818cf8; border: none;
                    border-radius: 8px; text-align: left; padding-left: 48px; font-size: 13px;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: transparent; color: #64748b; border: none;
                    border-radius: 8px; text-align: left; padding-left: 48px; font-size: 13px;
                }
                QPushButton:hover { background-color: rgba(51, 65, 85, 0.3); color: #94a3b8; }
            """)

    def set_selected(self, selected: bool):
        self._selected = selected
        self.setChecked(selected)
        self.update_style()


class Sidebar(QFrame):
    page_changed = pyqtSignal(str)
    sidebar_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.collapsed = False
        self.current_page = "dashboard"
        self.menu_buttons = {}
        self.submenu_buttons = {}
        self.expanded_menus = set()
        self.setup_ui()

    def setup_ui(self):
        self.setObjectName("sidebar")
        self.setFixedWidth(260)
        self.setStyleSheet("""
            QFrame#sidebar { background-color: #1e293b; border-right: 1px solid #334155; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        logo_frame = self.create_logo_section()
        layout.addWidget(logo_frame)
        layout.addSpacing(16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollArea > QWidget > QWidget { background: transparent; }
        """)

        menu_widget = QWidget()
        menu_layout = QVBoxLayout(menu_widget)
        menu_layout.setContentsMargins(0, 0, 0, 0)
        menu_layout.setSpacing(4)

        self.add_menu_items(menu_layout)
        menu_layout.addStretch()
        scroll.setWidget(menu_widget)
        layout.addWidget(scroll)

        user_frame = self.create_user_section()
        layout.addWidget(user_frame)

    def create_logo_section(self) -> QFrame:
        frame = QFrame()
        frame.setFixedHeight(60)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 0, 8, 0)

        logo_path = Path(settings.BASE_DIR) / "assets" / "favicon.svg"
        if logo_path.exists():
            logo = QSvgWidget(str(logo_path))
            logo.setFixedSize(40, 40)
            layout.addWidget(logo)
        else:
            logo_label = QLabel("🔄")
            logo_label.setStyleSheet("font-size: 32px;")
            layout.addWidget(logo_label)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(0)
        title = QLabel(settings.APP_NAME)
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #f8fafc;")
        title_layout.addWidget(title)
        version = QLabel(f"v{settings.APP_VERSION}")
        version.setStyleSheet("font-size: 11px; color: #64748b;")
        title_layout.addWidget(version)
        layout.addLayout(title_layout)
        layout.addStretch()

        toggle_btn = QPushButton("◀")
        toggle_btn.setFixedSize(28, 28)
        toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle_btn.setStyleSheet("""
            QPushButton { background-color: #334155; color: #94a3b8; border: none; border-radius: 8px; font-size: 10px; }
            QPushButton:hover { background-color: #475569; }
        """)
        toggle_btn.clicked.connect(self.toggle_sidebar)
        layout.addWidget(toggle_btn)

        return frame

    def add_menu_items(self, layout: QVBoxLayout):
        menu_structure = [
            ("dashboard", "Dashboard", "📊", []),
            ("inventory", "Stok Yönetimi", "📦", [
                ("stock-cards", "Stok Kartları"),
                ("categories", "Kategoriler"),
                ("units", "Birimler"),
                ("warehouses", "Depolar"),
                ("movements", "Stok Hareketleri"),
                ("stock-count", "Stok Sayımı"),
                ("stock-reports", "Stok Raporları"),
            ]),
            ("production", "Üretim", "🏭", [
                ("work-orders", "İş Emirleri"),
                ("bom", "Ürün Reçeteleri"),
                ("planning", "Üretim Planlama"),
            ]),
            ("purchasing", "Satın Alma", "🛒", []),
            ("sales", "Satış", "💰", []),
            ("finance", "Finans", "💳", []),
            ("hr", "İnsan Kaynakları", "👥", []),
            ("reports", "Raporlar", "📈", []),
            ("settings", "Ayarlar", "⚙️", []),
        ]

        for menu_id, title, icon, submenus in menu_structure:
            btn = MenuButton(title, icon, menu_id)
            btn.clicked.connect(lambda checked, m=menu_id, s=submenus: self.on_menu_click(m, s))
            self.menu_buttons[menu_id] = btn
            layout.addWidget(btn)

            if submenus:
                submenu_container = QWidget()
                submenu_container.setVisible(False)
                submenu_layout = QVBoxLayout(submenu_container)
                submenu_layout.setContentsMargins(0, 4, 0, 4)
                submenu_layout.setSpacing(2)

                for sub_id, sub_title in submenus:
                    sub_btn = SubMenuButton(sub_title, sub_id)
                    sub_btn.clicked.connect(lambda checked, p=sub_id: self.select_page(p))
                    self.submenu_buttons[sub_id] = sub_btn
                    submenu_layout.addWidget(sub_btn)

                layout.addWidget(submenu_container)
                btn.submenu_container = submenu_container

        self.menu_buttons["dashboard"].set_selected(True)

    def create_user_section(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame { background-color: rgba(51, 65, 85, 0.5); border-radius: 12px; padding: 8px; }
        """)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)

        avatar = QLabel("OK")
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #10b981, stop:1 #06b6d4);
            color: white; font-weight: 700; font-size: 13px; border-radius: 18px;
        """)
        layout.addWidget(avatar)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(0)
        name = QLabel("Okan")
        name.setStyleSheet("color: #e2e8f0; font-weight: 600; font-size: 13px;")
        info_layout.addWidget(name)
        role = QLabel("Yönetici")
        role.setStyleSheet("color: #64748b; font-size: 11px;")
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
