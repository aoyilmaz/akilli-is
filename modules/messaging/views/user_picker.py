"""
Mesajlaşma - Kullanıcı Seçici Widget
"""

from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QScrollArea,
    QFrame,
    QLabel,
    QPushButton,
)
from PyQt6.QtCore import pyqtSignal, Qt
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
    INPUT_BG,
    INPUT_BORDER,
    INPUT_FOCUS,
)
from config.icons import ICONS


class UserItem(QFrame):
    """Tek bir kullanıcı satırı."""

    clicked = pyqtSignal(dict)

    def __init__(self, user_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self._selected = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(40)
        self._setup_ui()
        self._setup_style()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Avatar placeholder
        avatar = QLabel()
        avatar.setFixedSize(28, 28)
        name = self.user_data.get("full_name", "?")
        initials = "".join(
            w[0].upper() for w in name.split()[:2] if w
        ) or "?"
        avatar.setText(initials)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(
            f"""
            QLabel {{
                background: {ACCENT};
                color: white;
                border-radius: 14px;
                font-size: 11px;
                font-weight: bold;
            }}
            """
        )
        layout.addWidget(avatar)

        # İsim ve email
        info_layout = QVBoxLayout()
        info_layout.setSpacing(0)
        info_layout.setContentsMargins(0, 0, 0, 0)

        name_label = QLabel(name)
        name_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 12px;")

        email = self.user_data.get("email", "")
        email_label = QLabel(email)
        email_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px;")

        info_layout.addWidget(name_label)
        info_layout.addWidget(email_label)
        layout.addLayout(info_layout)
        layout.addStretch()

    def _setup_style(self):
        self.setStyleSheet(
            f"""
            UserItem {{
                background: transparent;
                border: none;
                border-radius: 4px;
            }}
            UserItem:hover {{
                background: {BG_HOVER};
            }}
            """
        )

    def mousePressEvent(self, event):
        self.clicked.emit(self.user_data)
        super().mousePressEvent(event)


class UserPickerWidget(QWidget):
    """
    Kullanıcı arama ve seçme widget'ı.
    Tek veya çoklu seçim destekler.
    """

    user_selected = pyqtSignal(dict)  # Tek kullanıcı seçildi
    selection_changed = pyqtSignal(list)  # Çoklu seçim değişti

    def __init__(
        self,
        multi_select: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.multi_select = multi_select
        self._users: List[Dict[str, Any]] = []
        self._selected_users: List[Dict[str, Any]] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Arama kutusu
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Kullanıcı ara...")
        self.search_input.setFixedHeight(32)
        self.search_input.setStyleSheet(
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
        self.search_input.textChanged.connect(self._filter_users)
        layout.addWidget(self.search_input)

        # Seçili kullanıcılar (çoklu seçim)
        if self.multi_select:
            self.selected_container = QWidget()
            self.selected_layout = QHBoxLayout(self.selected_container)
            self.selected_layout.setContentsMargins(0, 0, 0, 0)
            self.selected_layout.setSpacing(4)
            self.selected_container.setVisible(False)
            layout.addWidget(self.selected_container)

        # Kullanıcı listesi
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(1)
        self.list_layout.addStretch()

        scroll.setWidget(self.list_container)
        layout.addWidget(scroll)

    def set_users(self, users: List[Dict[str, Any]]):
        """Kullanıcı listesini ayarlar."""
        self._users = users
        self._render_users(users)

    def _filter_users(self, text: str):
        """Arama metnine göre filtreler."""
        if not text:
            self._render_users(self._users)
            return

        text_lower = text.lower()
        filtered = [
            u
            for u in self._users
            if text_lower in u.get("full_name", "").lower()
            or text_lower in u.get("username", "").lower()
            or text_lower in u.get("email", "").lower()
        ]
        self._render_users(filtered)

    def _render_users(self, users: List[Dict[str, Any]]):
        """Kullanıcı listesini render eder."""
        # Mevcut itemları temizle
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for user in users:
            item = UserItem(user)
            item.clicked.connect(self._on_user_clicked)
            self.list_layout.insertWidget(
                self.list_layout.count() - 1, item
            )

    def _on_user_clicked(self, user_data: Dict[str, Any]):
        """Kullanıcı tıklandığında."""
        if self.multi_select:
            # Toggle seçim
            is_selected = any(
                u["id"] == user_data["id"] for u in self._selected_users
            )
            if is_selected:
                self._selected_users = [
                    u
                    for u in self._selected_users
                    if u["id"] != user_data["id"]
                ]
            else:
                self._selected_users.append(user_data)
            self._update_selected_chips()
            self.selection_changed.emit(self._selected_users)
        else:
            self.user_selected.emit(user_data)

    def _update_selected_chips(self):
        """Seçili kullanıcı chip'lerini günceller."""
        if not self.multi_select:
            return

        # Temizle
        while self.selected_layout.count():
            item = self.selected_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for user in self._selected_users:
            chip = QPushButton(
                f"{user['full_name']} x"
            )
            chip.setFixedHeight(24)
            chip.setStyleSheet(
                f"""
                QPushButton {{
                    background: {ACCENT};
                    color: white;
                    border: none;
                    border-radius: 12px;
                    padding: 0 8px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background: {BG_HOVER};
                }}
                """
            )
            uid = user["id"]
            chip.clicked.connect(
                lambda checked, u=uid: self._remove_selected(u)
            )
            self.selected_layout.addWidget(chip)

        self.selected_container.setVisible(len(self._selected_users) > 0)

    def _remove_selected(self, user_id: int):
        """Seçili kullanıcıyı kaldırır."""
        self._selected_users = [
            u for u in self._selected_users if u["id"] != user_id
        ]
        self._update_selected_chips()
        self.selection_changed.emit(self._selected_users)

    def get_selected_ids(self) -> List[int]:
        """Seçili kullanıcı ID'lerini döndürür."""
        return [u["id"] for u in self._selected_users]

    def clear(self):
        """Seçimi ve aramayı temizler."""
        self.search_input.clear()
        self._selected_users.clear()
        if self.multi_select:
            self._update_selected_chips()
