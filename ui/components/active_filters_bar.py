"""
Akıllı İş ERP - Aktif Filtreler Çubuğu
Tablonun üstünde/altında aktif filtreleri gösteren widget.
"""

from typing import Dict, Callable
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from config.styles import COLORS, FONT_FAMILY_QT


class FilterChip(QFrame):
    """Tek bir filtre chip'i - tıklanabilir X ile"""

    remove_clicked = pyqtSignal(str)  # column_key

    def __init__(self, column_key: str, column_title: str, filter_text: str, parent=None):
        super().__init__(parent)
        self.column_key = column_key

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 4, 2)
        layout.setSpacing(4)

        # Filtre metni
        label = QLabel(f"{column_title}: {filter_text}")
        label.setFont(QFont(FONT_FAMILY_QT, 10))
        layout.addWidget(label)

        # X butonu
        close_btn = QPushButton("×")
        close_btn.setFixedSize(16, 16)
        close_btn.setFont(QFont(FONT_FAMILY_QT, 12, QFont.Weight.Bold))
        close_btn.clicked.connect(lambda: self.remove_clicked.emit(self.column_key))
        layout.addWidget(close_btn)

        self._setup_style()

    def _setup_style(self):
        self.setStyleSheet(f"""
            FilterChip {{
                background: {COLORS['bg_hover']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
            QLabel {{
                color: {COLORS['text_primary']};
                background: transparent;
                border: none;
            }}
            QPushButton {{
                background: transparent;
                border: none;
                color: {COLORS['text_muted']};
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background: {COLORS['danger']};
                color: white;
            }}
        """)


class ActiveFiltersBar(QFrame):
    """Aktif filtreleri gösteren çubuk"""

    filter_removed = pyqtSignal(str)  # column_key
    clear_all_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._chips: Dict[str, FilterChip] = {}
        self.setObjectName("ActiveFiltersBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # Başlık
        self._label = QLabel("Filtreler:")
        self._label.setFont(QFont(FONT_FAMILY_QT, 10))
        self._label.setStyleSheet(f"color: {COLORS['text_muted']};")
        layout.addWidget(self._label)

        # Chip'ler için container
        self._chips_layout = QHBoxLayout()
        self._chips_layout.setSpacing(4)
        self._chips_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self._chips_layout)

        layout.addStretch()

        # Tümünü temizle butonu
        self._clear_all_btn = QPushButton("Tümünü Temizle")
        self._clear_all_btn.setFixedHeight(22)
        self._clear_all_btn.setFont(QFont(FONT_FAMILY_QT, 10))
        self._clear_all_btn.clicked.connect(self.clear_all_clicked.emit)
        self._clear_all_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {COLORS['danger']};
                border-radius: 4px;
                color: {COLORS['danger']};
                padding: 2px 8px;
            }}
            QPushButton:hover {{
                background: {COLORS['danger']};
                color: white;
            }}
        """)
        layout.addWidget(self._clear_all_btn)

        # Başlangıçta gizle
        self.setVisible(False)
        self.setFixedHeight(32)

        self.setStyleSheet(f"""
            QFrame#ActiveFiltersBar {{
                background: {COLORS['bg_tertiary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
            }}
        """)

    def update_filters(self, filters: Dict[str, dict], column_titles: Dict[str, str]):
        """Filtreleri güncelle"""
        # Mevcut chip'leri temizle
        for chip in self._chips.values():
            chip.deleteLater()
        self._chips.clear()

        # Yeni chip'ler oluştur
        for col_key, filter_data in filters.items():
            title = column_titles.get(col_key, col_key)
            filter_text = self._get_filter_text(filter_data)

            chip = FilterChip(col_key, title, filter_text, self)
            chip.remove_clicked.connect(self._on_chip_removed)
            self._chips_layout.addWidget(chip)
            self._chips[col_key] = chip

        # Görünürlük
        has_filters = len(filters) > 0
        self.setVisible(has_filters)

    def _get_filter_text(self, filter_data: dict) -> str:
        """Filtre verisinden özet metin oluştur"""
        parts = []

        # Değer filtresi
        if not filter_data.get("all_selected", True):
            selected = filter_data.get("selected_values", [])
            if len(selected) <= 2:
                parts.append(", ".join(selected))
            else:
                parts.append(f"{len(selected)} seçili")

        # Metin filtresi
        text_filter = filter_data.get("text_filter")
        if text_filter:
            mode = text_filter.get("mode", "contains")
            text = text_filter.get("text", "")
            mode_labels = {
                "contains": "içerir",
                "equals": "=",
                "starts_with": "başlar",
                "ends_with": "biter",
                "not_contains": "içermez",
            }
            parts.append(f'{mode_labels.get(mode, mode)} "{text}"')

        return " | ".join(parts) if parts else "aktif"

    def _on_chip_removed(self, column_key: str):
        """Chip kaldırıldığında"""
        self.filter_removed.emit(column_key)
