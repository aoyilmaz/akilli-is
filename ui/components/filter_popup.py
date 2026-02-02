"""
Akıllı İş ERP - Filtre Popup Bileşeni
Excel benzeri sütun filtreleme popup'ı.
"""

from typing import List, Dict, Optional, Set
from PyQt6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QComboBox,
    QWidget,
    QScrollArea,
    QCheckBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from config.styles import COLORS, FONT_FAMILY_QT


class FilterPopup(QFrame):
    """
    Excel benzeri sütun filtre popup'ı.

    Özellikler:
    - Değer arama kutusu
    - Benzersiz değerler listesi (checkbox)
    - Tümünü seç / Temizle
    - Metin filtresi (içerir, başlar, eşittir, biter)
    - Uygula / Sıfırla butonları
    """

    filter_applied = pyqtSignal(dict)  # filter_data
    filter_cleared = pyqtSignal()

    # Metin filtre modları
    TEXT_FILTER_MODES = [
        ("contains", "İçerir"),
        ("equals", "Eşittir"),
        ("starts_with", "İle Başlar"),
        ("ends_with", "İle Biter"),
        ("not_contains", "İçermez"),
    ]

    def __init__(
        self,
        column_key: str,
        column_title: str,
        unique_values: Optional[List[str]] = None,
        current_filter: Optional[dict] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.column_key = column_key
        self.column_title = column_title
        self._all_values: List[str] = []
        self._selected_values: Set[str] = set()
        self._checkboxes: Dict[str, QCheckBox] = {}

        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        self._setup_ui()
        self._setup_style()

        if unique_values:
            self.set_unique_values(unique_values)

        if current_filter:
            self._apply_current_filter(current_filter)

    def _setup_ui(self):
        """UI oluştur - Kompakt tasarım"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # Arama kutusu (başlık yerine placeholder)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(f"🔍 {self.column_title}")
        self.search_input.setFixedHeight(14)
        self.search_input.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_input)

        # Tümünü seç / Temizle butonları - tek satır, kompakt
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(2)
        buttons_layout.setContentsMargins(0, 0, 0, 0)

        self.select_all_btn = QPushButton("Tümü")
        self.select_all_btn.setFixedHeight(14)
        self.select_all_btn.clicked.connect(self._select_all)
        buttons_layout.addWidget(self.select_all_btn)

        self.clear_btn = QPushButton("Hiçbiri")
        self.clear_btn.setFixedHeight(14)
        self.clear_btn.clicked.connect(self._clear_selection)
        buttons_layout.addWidget(self.clear_btn)

        layout.addLayout(buttons_layout)

        # Değerler listesi - daha küçük
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setMinimumHeight(60)
        self.scroll_area.setMaximumHeight(120)

        self.values_container = QWidget()
        self.values_layout = QVBoxLayout(self.values_container)
        self.values_layout.setContentsMargins(2, 2, 2, 2)
        self.values_layout.setSpacing(0)
        self.values_layout.addStretch()

        self.scroll_area.setWidget(self.values_container)
        layout.addWidget(self.scroll_area)

        # Metin filtresi - tek satır
        text_filter_layout = QHBoxLayout()
        text_filter_layout.setSpacing(2)
        text_filter_layout.setContentsMargins(0, 0, 0, 0)

        self.text_mode_combo = QComboBox()
        self.text_mode_combo.setFixedWidth(70)
        self.text_mode_combo.setFixedHeight(14)
        for mode, label in self.TEXT_FILTER_MODES:
            self.text_mode_combo.addItem(label, mode)
        text_filter_layout.addWidget(self.text_mode_combo)

        self.text_filter_input = QLineEdit()
        self.text_filter_input.setPlaceholderText("metin...")
        self.text_filter_input.setFixedHeight(14)
        text_filter_layout.addWidget(self.text_filter_input)

        layout.addLayout(text_filter_layout)

        # Alt butonlar - kompakt
        action_layout = QHBoxLayout()
        action_layout.setSpacing(2)
        action_layout.setContentsMargins(0, 1, 0, 0)

        self.reset_btn = QPushButton("Sıfırla")
        self.reset_btn.setFixedHeight(16)
        self.reset_btn.clicked.connect(self._on_reset)
        action_layout.addWidget(self.reset_btn)

        self.apply_btn = QPushButton("Uygula")
        self.apply_btn.setFixedHeight(16)
        self.apply_btn.setProperty("class", "primary")
        self.apply_btn.clicked.connect(self._on_apply)
        action_layout.addWidget(self.apply_btn)

        layout.addLayout(action_layout)

        # Daha dar popup
        self.setFixedWidth(180)

    def _setup_style(self):
        """Stil ayarları"""
        self.setStyleSheet(
            f"""
            FilterPopup {{
                background: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
            }}

            QLineEdit {{
                background: {COLORS['bg_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 2px;
                padding: 0px 4px;
                color: {COLORS['text_primary']};
                font-family: {FONT_FAMILY_QT};
                font-size: 9px;
                min-height: 14px;
            }}

            QLineEdit:focus {{
                border-color: {COLORS['primary']};
            }}

            QComboBox {{
                background: {COLORS['bg_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 2px;
                padding: 0px 4px;
                color: {COLORS['text_primary']};
                font-family: {FONT_FAMILY_QT};
                font-size: 9px;
                min-height: 14px;
            }}

            QComboBox::drop-down {{
                border: none;
                width: 12px;
            }}

            QComboBox::down-arrow {{
                image: none;
                border-left: 2px solid transparent;
                border-right: 2px solid transparent;
                border-top: 3px solid {COLORS['text_secondary']};
            }}

            QComboBox QAbstractItemView {{
                background: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                selection-background-color: {COLORS['primary']};
                font-size: 9px;
            }}

            QPushButton {{
                background: {COLORS['bg_hover']};
                border: 1px solid {COLORS['border']};
                border-radius: 2px;
                padding: 0px 4px;
                color: {COLORS['text_primary']};
                font-family: {FONT_FAMILY_QT};
                font-size: 9px;
            }}

            QPushButton:hover {{
                background: {COLORS['bg_active']};
            }}

            QPushButton[class="primary"] {{
                background: {COLORS['primary']};
                border: none;
                color: white;
            }}

            QPushButton[class="primary"]:hover {{
                background: {COLORS['primary_hover']};
            }}

            QScrollArea {{
                background: {COLORS['bg_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 3px;
            }}

            QScrollBar:vertical {{
                background: {COLORS['bg_primary']};
                width: 6px;
                border-radius: 3px;
            }}

            QScrollBar::handle:vertical {{
                background: {COLORS['border']};
                border-radius: 3px;
                min-height: 16px;
            }}

            QScrollBar::handle:vertical:hover {{
                background: {COLORS['text_muted']};
            }}

            QCheckBox {{
                color: {COLORS['text_primary']};
                font-family: {FONT_FAMILY_QT};
                font-size: 10px;
                spacing: 3px;
                padding: 1px;
            }}

            QCheckBox:hover {{
                background: {COLORS['bg_hover']};
                border-radius: 2px;
            }}

            QCheckBox::indicator {{
                width: 10px;
                height: 10px;
                border: 1px solid {COLORS['border']};
                border-radius: 2px;
                background: {COLORS['bg_primary']};
            }}

            QCheckBox::indicator:checked {{
                background: {COLORS['primary']};
                border-color: {COLORS['primary']};
            }}

            QCheckBox::indicator:checked:hover {{
                background: {COLORS['primary_hover']};
            }}
        """
        )

    def set_unique_values(self, values: List[str]):
        """Benzersiz değerleri ayarla"""
        self._all_values = sorted(set(str(v) for v in values if v is not None))
        self._selected_values = set(self._all_values)  # Başlangıçta hepsi seçili
        self._rebuild_checkboxes()

    def _rebuild_checkboxes(self, filter_text: str = ""):
        """Checkbox listesini yeniden oluştur"""
        # Mevcut checkbox'ları temizle
        for cb in self._checkboxes.values():
            cb.deleteLater()
        self._checkboxes.clear()

        # Stretch'i kaldır
        while self.values_layout.count() > 0:
            item = self.values_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Filtrelenmiş değerleri ekle
        filter_lower = filter_text.lower()
        for value in self._all_values:
            if filter_lower and filter_lower not in value.lower():
                continue

            checkbox = QCheckBox(value if value else "(Boş)")
            checkbox.setChecked(value in self._selected_values)
            checkbox.stateChanged.connect(
                lambda state, v=value: self._on_checkbox_changed(v, state)
            )
            self._checkboxes[value] = checkbox
            self.values_layout.addWidget(checkbox)

        self.values_layout.addStretch()

    def _on_checkbox_changed(self, value: str, state: int):
        """Checkbox değiştiğinde"""
        if state == Qt.CheckState.Checked.value:
            self._selected_values.add(value)
        else:
            self._selected_values.discard(value)

    def _on_search_changed(self, text: str):
        """Arama metni değiştiğinde"""
        self._rebuild_checkboxes(text)

    def _select_all(self):
        """Tümünü seç"""
        self._selected_values = set(self._all_values)
        for value, checkbox in self._checkboxes.items():
            checkbox.blockSignals(True)
            checkbox.setChecked(True)
            checkbox.blockSignals(False)

    def _clear_selection(self):
        """Seçimi temizle"""
        self._selected_values.clear()
        for checkbox in self._checkboxes.values():
            checkbox.blockSignals(True)
            checkbox.setChecked(False)
            checkbox.blockSignals(False)

    def _on_reset(self):
        """Filtreyi sıfırla"""
        self._selected_values = set(self._all_values)
        self._rebuild_checkboxes()
        self.text_filter_input.clear()
        self.text_mode_combo.setCurrentIndex(0)
        self.filter_cleared.emit()
        self.close()

    def _on_apply(self):
        """Filtreyi uygula"""
        filter_data = self.get_filter_data()
        self.filter_applied.emit(filter_data)
        self.close()

    def get_filter_data(self) -> dict:
        """Filtre verilerini döndür"""
        data = {
            "column_key": self.column_key,
            "selected_values": list(self._selected_values),
            "all_selected": len(self._selected_values) == len(self._all_values),
        }

        # Metin filtresi
        text_filter = self.text_filter_input.text().strip()
        if text_filter:
            data["text_filter"] = {
                "mode": self.text_mode_combo.currentData(),
                "text": text_filter,
            }

        return data

    def _apply_current_filter(self, filter_data: dict):
        """Mevcut filtreyi uygula"""
        if "selected_values" in filter_data:
            self._selected_values = set(filter_data["selected_values"])
            self._rebuild_checkboxes()

        if "text_filter" in filter_data:
            tf = filter_data["text_filter"]
            self.text_filter_input.setText(tf.get("text", ""))
            mode = tf.get("mode", "contains")
            for i in range(self.text_mode_combo.count()):
                if self.text_mode_combo.itemData(i) == mode:
                    self.text_mode_combo.setCurrentIndex(i)
                    break

    def has_active_filter(self) -> bool:
        """Aktif filtre var mı?"""
        # Tüm değerler seçili değilse veya metin filtresi varsa aktif
        if len(self._selected_values) < len(self._all_values):
            return True
        if self.text_filter_input.text().strip():
            return True
        return False
