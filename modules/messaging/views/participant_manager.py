"""
Mesajlaşma - Grup Katılımcı Yönetimi
"""

from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QDialog,
    QSizePolicy,
)
from PyQt6.QtCore import pyqtSignal, Qt, QSize
import qtawesome as qta

from config.styles import (
    BG_SECONDARY,
    BG_TERTIARY,
    BG_HOVER,
    BORDER,
    TEXT_PRIMARY,
    TEXT_MUTED,
    ACCENT,
    BTN_PRIMARY_BG,
    BTN_PRIMARY_HOVER,
    BTN_DANGER_BG,
    BTN_DANGER_HOVER,
    ERROR,
)
from config.icons import ICONS


class ParticipantRow(QFrame):
    """Tek bir katılımcı satırı."""

    remove_requested = pyqtSignal(int)  # user_id

    def __init__(
        self,
        participant: Dict[str, Any],
        can_remove: bool = False,
        is_self: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.participant = participant
        self.setFixedHeight(44)
        self._setup_ui(can_remove, is_self)
        self.setStyleSheet(
            f"""
            ParticipantRow {{
                background: transparent;
                border: none;
                border-radius: 4px;
            }}
            ParticipantRow:hover {{
                background: {BG_HOVER};
            }}
            """
        )

    def _setup_ui(self, can_remove: bool, is_self: bool):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Avatar
        name = self.participant.get("full_name", "?")
        initials = "".join(w[0].upper() for w in name.split()[:2] if w) or "?"
        avatar = QLabel(initials)
        avatar.setFixedSize(30, 30)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(
            f"""
            QLabel {{
                background: {ACCENT};
                color: white;
                border-radius: 15px;
                font-size: 11px;
                font-weight: bold;
            }}
            """
        )
        layout.addWidget(avatar)

        # İsim + rol
        info = QVBoxLayout()
        info.setSpacing(1)
        info.setContentsMargins(0, 0, 0, 0)

        name_text = name + (" (Sen)" if is_self else "")
        name_label = QLabel(name_text)
        name_label.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 12px;"
        )
        info.addWidget(name_label)

        role = self.participant.get("role", "member")
        role_text = "Yönetici" if role == "admin" else "Üye"
        role_label = QLabel(role_text)
        role_label.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 10px;"
        )
        info.addWidget(role_label)
        layout.addLayout(info)
        layout.addStretch()

        # Çıkar butonu
        if can_remove and not is_self:
            remove_btn = QPushButton()
            remove_btn.setIcon(qta.icon(ICONS.CLOSE, color=ERROR))
            remove_btn.setIconSize(QSize(12, 12))
            remove_btn.setFixedSize(24, 24)
            remove_btn.setFlat(True)
            remove_btn.setToolTip("Gruptan çıkar")
            remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            remove_btn.setStyleSheet(
                f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    border-radius: 12px;
                }}
                QPushButton:hover {{
                    background: {BTN_DANGER_BG};
                }}
                """
            )
            uid = self.participant["user_id"]
            remove_btn.clicked.connect(lambda: self.remove_requested.emit(uid))
            layout.addWidget(remove_btn)


class ParticipantManagerWidget(QWidget):
    """
    Grup katılımcılarını listeler ve yönetir.
    Yeni katılımcı ekleme ve mevcut katılımcıları çıkarma.
    """

    participant_removed = pyqtSignal(int)  # user_id
    add_participants_requested = pyqtSignal()

    def __init__(self, current_user_id: int, is_admin: bool = False, parent=None):
        super().__init__(parent)
        self._current_user_id = current_user_id
        self._is_admin = is_admin
        self._participants: List[Dict[str, Any]] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Başlık
        header = QWidget()
        header.setFixedHeight(36)
        header.setStyleSheet(f"background: {BG_TERTIARY};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 0, 10, 0)

        title = QLabel("Katılımcılar")
        title.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 11px; font-weight: 600;"
        )
        header_layout.addWidget(title)
        header_layout.addStretch()

        if self._is_admin:
            add_btn = QPushButton()
            add_btn.setIcon(qta.icon(ICONS.PLUS, color="#cccccc"))
            add_btn.setIconSize(QSize(12, 12))
            add_btn.setFixedSize(24, 24)
            add_btn.setFlat(True)
            add_btn.setToolTip("Katılımcı ekle")
            add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            add_btn.setStyleSheet(
                f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background: {BTN_PRIMARY_BG};
                }}
                """
            )
            add_btn.clicked.connect(self.add_participants_requested)
            header_layout.addWidget(add_btn)

        layout.addWidget(header)

        # Liste
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            f"QScrollArea {{ background: {BG_SECONDARY}; border: none; }}"
        )

        self.list_container = QWidget()
        self.list_container.setStyleSheet(f"background: {BG_SECONDARY};")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(4, 4, 4, 4)
        self.list_layout.setSpacing(1)
        self.list_layout.addStretch()

        scroll.setWidget(self.list_container)
        layout.addWidget(scroll)

    def set_participants(self, participants: List[Dict[str, Any]]):
        """Katılımcı listesini günceller."""
        self._participants = participants

        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for p in participants:
            is_self = p["user_id"] == self._current_user_id
            row = ParticipantRow(
                p,
                can_remove=self._is_admin,
                is_self=is_self,
            )
            row.remove_requested.connect(self.participant_removed)
            self.list_layout.insertWidget(
                self.list_layout.count() - 1, row
            )

    def get_participant_count(self) -> int:
        return len(self._participants)
