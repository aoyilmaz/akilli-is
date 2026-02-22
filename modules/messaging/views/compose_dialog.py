"""
Mesajlaşma - Yeni Mesaj / Yeni Grup Oluşturma Dialogu
"""

from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QWidget,
    QFrame,
    QSizePolicy,
)
from PyQt6.QtCore import pyqtSignal, Qt, QSize
import qtawesome as qta

from config.styles import (
    BG_SECONDARY,
    BG_TERTIARY,
    BORDER,
    TEXT_PRIMARY,
    TEXT_MUTED,
    ACCENT,
    BTN_PRIMARY_BG,
    BTN_PRIMARY_HOVER,
    BTN_SECONDARY_BG,
    BTN_SECONDARY_HOVER,
    INPUT_BG,
    INPUT_BORDER,
    INPUT_FOCUS,
)
from config.icons import ICONS
from modules.messaging.views.user_picker import UserPickerWidget


class ComposeDialog(QDialog):
    """
    Yeni mesaj oluşturma dialogu.
    - Direkt mesaj: Tek kullanıcı seç
    - Grup: Başlık + birden fazla kullanıcı seç
    - Departman: Departman seç
    """

    conversation_created = pyqtSignal(dict)  # {type, user_ids/dept_id, title}

    def __init__(self, users: List[Dict[str, Any]], departments: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self._users = users
        self._departments = departments
        self.setWindowTitle("Yeni Mesaj")
        self.setModal(True)
        self.setFixedSize(360, 480)
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Başlık barı
        header = QWidget()
        header.setFixedHeight(44)
        header.setStyleSheet(f"background: {BG_TERTIARY}; border-bottom: 1px solid {BORDER};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 8, 0)

        title = QLabel("Yeni Mesaj")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 14px; font-weight: 600;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        close_btn = QPushButton()
        close_btn.setIcon(qta.icon(ICONS.CLOSE, color="#cccccc"))
        close_btn.setIconSize(QSize(14, 14))
        close_btn.setFixedSize(28, 28)
        close_btn.setFlat(True)
        close_btn.setStyleSheet(
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
        close_btn.clicked.connect(self.reject)
        header_layout.addWidget(close_btn)
        layout.addWidget(header)

        # Sekmeler
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            f"""
            QTabWidget::pane {{
                border: none;
                background: {BG_SECONDARY};
            }}
            QTabBar::tab {{
                background: {BG_TERTIARY};
                color: {TEXT_MUTED};
                padding: 8px 16px;
                border: none;
                font-size: 12px;
            }}
            QTabBar::tab:selected {{
                background: {BG_SECONDARY};
                color: {TEXT_PRIMARY};
                border-bottom: 2px solid {ACCENT};
            }}
            QTabBar::tab:hover {{
                color: {TEXT_PRIMARY};
            }}
            """
        )

        # Direkt mesaj sekmesi
        self.direct_tab = self._build_direct_tab()
        self.tabs.addTab(self.direct_tab, "Direkt Mesaj")

        # Grup sekmesi
        self.group_tab = self._build_group_tab()
        self.tabs.addTab(self.group_tab, "Grup Oluştur")

        # Departman kanalı sekmesi (departman varsa)
        if self._departments:
            self.dept_tab = self._build_dept_tab()
            self.tabs.addTab(self.dept_tab, "Departman")

        layout.addWidget(self.tabs)

    def _build_direct_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        label = QLabel("Mesaj göndermek istediğiniz kişiyi seçin:")
        label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(label)

        self.direct_picker = UserPickerWidget(multi_select=False)
        self.direct_picker.set_users(self._users)
        self.direct_picker.user_selected.connect(self._on_direct_user_selected)
        layout.addWidget(self.direct_picker)

        return widget

    def _build_group_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Grup adı
        title_label = QLabel("Grup adı:")
        title_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(title_label)

        self.group_title_input = QLineEdit()
        self.group_title_input.setPlaceholderText("Grup adını girin...")
        self.group_title_input.setFixedHeight(32)
        self.group_title_input.setStyleSheet(
            f"""
            QLineEdit {{
                background: {INPUT_BG};
                border: 1px solid {INPUT_BORDER};
                border-radius: 4px;
                color: {TEXT_PRIMARY};
                padding: 0 8px;
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border-color: {INPUT_FOCUS};
            }}
            """
        )
        layout.addWidget(self.group_title_input)

        members_label = QLabel("Katılımcıları seçin:")
        members_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(members_label)

        self.group_picker = UserPickerWidget(multi_select=True)
        self.group_picker.set_users(self._users)
        layout.addWidget(self.group_picker)

        # Oluştur butonu
        self.create_group_btn = QPushButton("Grup Oluştur")
        self.create_group_btn.setFixedHeight(34)
        self.create_group_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.create_group_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: {BTN_PRIMARY_BG};
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {BTN_PRIMARY_HOVER};
            }}
            """
        )
        self.create_group_btn.clicked.connect(self._on_create_group)
        layout.addWidget(self.create_group_btn)

        return widget

    def _build_dept_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        label = QLabel("Departman kanalı oluşturun:")
        label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(label)

        for dept in self._departments:
            btn = QPushButton(dept["name"])
            btn.setFixedHeight(36)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background: {BG_TERTIARY};
                    color: {TEXT_PRIMARY};
                    border: 1px solid {BORDER};
                    border-radius: 4px;
                    font-size: 12px;
                    text-align: left;
                    padding: 0 12px;
                }}
                QPushButton:hover {{
                    background: {BTN_PRIMARY_BG};
                    border-color: {BTN_PRIMARY_BG};
                    color: white;
                }}
                """
            )
            dept_id = dept["id"]
            dept_name = dept["name"]
            btn.clicked.connect(
                lambda checked, did=dept_id, dname=dept_name: self._on_dept_selected(did, dname)
            )
            layout.addWidget(btn)

        layout.addStretch()
        return widget

    def _apply_style(self):
        self.setStyleSheet(
            f"""
            QDialog {{
                background: {BG_SECONDARY};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
            """
        )

    def _on_direct_user_selected(self, user_data: Dict[str, Any]):
        self.conversation_created.emit(
            {
                "type": "direct",
                "user_id": user_data["id"],
                "user_name": user_data["full_name"],
            }
        )
        self.accept()

    def _on_create_group(self):
        title = self.group_title_input.text().strip()
        participant_ids = self.group_picker.get_selected_ids()

        if not title:
            self.group_title_input.setPlaceholderText("Grup adı zorunludur!")
            return

        if len(participant_ids) < 1:
            return

        self.conversation_created.emit(
            {
                "type": "group",
                "title": title,
                "participant_ids": participant_ids,
            }
        )
        self.accept()

    def _on_dept_selected(self, dept_id: int, dept_name: str):
        self.conversation_created.emit(
            {
                "type": "department",
                "department_id": dept_id,
                "department_name": dept_name,
            }
        )
        self.accept()
