"""
Akıllı İş - CurrencyWidget

TCMB döviz kurları widget'ı - seçilebilir para birimleri.
"""

from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QSizePolicy,
    QPushButton,
    QDialog,
    QDialogButtonBox,
    QCheckBox,
    QScrollArea,
    QGridLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from config.styles import COLORS, FONT_FAMILY_QT
from .base import BaseWidget, WidgetConfig


# Desteklenen para birimleri
AVAILABLE_CURRENCIES = {
    "USD": {"name": "ABD Doları", "flag": "🇺🇸"},
    "EUR": {"name": "Euro", "flag": "🇪🇺"},
    "GBP": {"name": "İngiliz Sterlini", "flag": "🇬🇧"},
    "CHF": {"name": "İsviçre Frangı", "flag": "🇨🇭"},
    "JPY": {"name": "Japon Yeni", "flag": "🇯🇵"},
    "SAR": {"name": "Suudi Riyali", "flag": "🇸🇦"},
    "AUD": {"name": "Avustralya Doları", "flag": "🇦🇺"},
    "CAD": {"name": "Kanada Doları", "flag": "🇨🇦"},
    "RUB": {"name": "Rus Rublesi", "flag": "🇷🇺"},
    "CNY": {"name": "Çin Yuanı", "flag": "🇨🇳"},
    "NOK": {"name": "Norveç Kronu", "flag": "🇳🇴"},
    "SEK": {"name": "İsveç Kronu", "flag": "🇸🇪"},
    "DKK": {"name": "Danimarka Kronu", "flag": "🇩🇰"},
    "KWD": {"name": "Kuveyt Dinarı", "flag": "🇰🇼"},
    "AED": {"name": "BAE Dirhemi", "flag": "🇦🇪"},
    "QAR": {"name": "Katar Riyali", "flag": "🇶🇦"},
}


class CurrencySettingsDialog(QDialog):
    """Para birimi seçim diyaloğu"""

    def __init__(self, selected_currencies: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Döviz Seçimi")
        self.setMinimumWidth(350)
        self.setMinimumHeight(400)
        self._selected = set(selected_currencies)
        self._checkboxes = {}
        self._setup_ui()
        self._setup_style()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Başlık
        title = QLabel("Görüntülenecek Para Birimlerini Seçin")
        title.setFont(QFont(FONT_FAMILY_QT, 11, QFont.Weight.DemiBold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(title)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(8)

        row = 0
        col = 0
        for code, info in AVAILABLE_CURRENCIES.items():
            cb = QCheckBox(f"{info['flag']} {code} - {info['name']}")
            cb.setChecked(code in self._selected)
            cb.setFont(QFont(FONT_FAMILY_QT, 10))
            cb.setStyleSheet(f"color: {COLORS['text_primary']};")
            self._checkboxes[code] = cb
            grid.addWidget(cb, row, col)
            col += 1
            if col >= 2:
                col = 0
                row += 1

        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        # Hızlı seçim butonları
        quick_layout = QHBoxLayout()

        select_all = QPushButton("Tümünü Seç")
        select_all.clicked.connect(self._select_all)
        select_all.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 6px 12px;
                color: {COLORS['text_primary']};
            }}
            QPushButton:hover {{
                background: {COLORS['bg_hover']};
            }}
        """)
        quick_layout.addWidget(select_all)

        clear_all = QPushButton("Temizle")
        clear_all.clicked.connect(self._clear_all)
        clear_all.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 6px 12px;
                color: {COLORS['text_primary']};
            }}
            QPushButton:hover {{
                background: {COLORS['bg_hover']};
            }}
        """)
        quick_layout.addWidget(clear_all)

        quick_layout.addStretch()
        layout.addLayout(quick_layout)

        # Butonlar
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: white;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background: {COLORS['primary_hover']};
            }}
        """)
        layout.addWidget(buttons)

    def _setup_style(self):
        self.setStyleSheet(f"""
            QDialog {{
                background: {COLORS['bg_card']};
            }}
            QScrollArea {{
                background: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
            }}
        """)

    def _select_all(self):
        for cb in self._checkboxes.values():
            cb.setChecked(True)

    def _clear_all(self):
        for cb in self._checkboxes.values():
            cb.setChecked(False)

    def get_selected(self) -> List[str]:
        """Seçili para birimlerini döner"""
        return [code for code, cb in self._checkboxes.items() if cb.isChecked()]


class CurrencyRow(QFrame):
    """Tek bir döviz satırı"""

    def __init__(self, code: str, name: str, buying: float, selling: float,
                 change: float = 0.0, parent=None):
        super().__init__(parent)
        self._setup_ui(code, name, buying, selling, change)
        self._setup_style()

    def _setup_ui(self, code: str, name: str, buying: float, selling: float, change: float):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        # Para birimi kodu ve bayrağı
        info = AVAILABLE_CURRENCIES.get(code, {"flag": "💱"})
        flag = info.get("flag", "💱")

        code_label = QLabel(f"{flag} {code}")
        code_label.setFont(QFont(FONT_FAMILY_QT, 11, QFont.Weight.DemiBold))
        code_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        code_label.setFixedWidth(80)
        layout.addWidget(code_label)

        # Alış
        buying_layout = QVBoxLayout()
        buying_layout.setSpacing(0)

        buying_title = QLabel("Alış")
        buying_title.setFont(QFont(FONT_FAMILY_QT, 8))
        buying_title.setStyleSheet(f"color: {COLORS['text_secondary']};")
        buying_layout.addWidget(buying_title)

        buying_value = QLabel(f"₺{buying:.4f}")
        buying_value.setFont(QFont(FONT_FAMILY_QT, 10))
        buying_value.setStyleSheet(f"color: {COLORS['text_primary']};")
        buying_layout.addWidget(buying_value)

        layout.addLayout(buying_layout)

        # Satış
        selling_layout = QVBoxLayout()
        selling_layout.setSpacing(0)

        selling_title = QLabel("Satış")
        selling_title.setFont(QFont(FONT_FAMILY_QT, 8))
        selling_title.setStyleSheet(f"color: {COLORS['text_secondary']};")
        selling_layout.addWidget(selling_title)

        selling_value = QLabel(f"₺{selling:.4f}")
        selling_value.setFont(QFont(FONT_FAMILY_QT, 10))
        selling_value.setStyleSheet(f"color: {COLORS['text_primary']};")
        selling_layout.addWidget(selling_value)

        layout.addLayout(selling_layout)

        # Değişim (opsiyonel)
        if change != 0:
            change_label = QLabel(f"{'+' if change > 0 else ''}{change:.2f}%")
            change_label.setFont(QFont(FONT_FAMILY_QT, 9))
            if change > 0:
                change_label.setStyleSheet(f"color: {COLORS['success']};")
            else:
                change_label.setStyleSheet(f"color: {COLORS['danger']};")
            layout.addWidget(change_label)

        layout.addStretch()

    def _setup_style(self):
        self.setStyleSheet(f"""
            CurrencyRow {{
                background: {COLORS['bg_secondary']};
                border-radius: 4px;
            }}
        """)


class CurrencyWidget(BaseWidget):
    """
    Döviz kurları widget'ı

    TCMB'den güncel döviz kurlarını gösterir.
    Kullanıcı hangi para birimlerini görmek istediğini seçebilir.
    """

    widget_code = "currency_rates"
    widget_name = "Döviz Kurları"
    widget_type = "external"
    widget_description = "TCMB döviz kurları (seçilebilir)"
    widget_icon = "money"
    min_size = (1, 1)
    default_size = (2, 1)
    max_size = (2, 2)
    refresh_interval = 3600  # 1 saat

    # Varsayılan olarak gösterilecek para birimleri
    DEFAULT_CURRENCIES = ["USD", "EUR", "GBP"]

    # Signals
    settings_changed = pyqtSignal(list)

    def __init__(
        self,
        config: Optional[WidgetConfig] = None,
        edit_mode: bool = False,
        parent: Optional[QWidget] = None
    ):
        self._currency_rows: List[CurrencyRow] = []
        super().__init__(config, edit_mode, parent)

    def _create_header(self):
        """Widget başlık çubuğunu oluşturur (ayarlar butonu ekli)"""
        super()._create_header()

        # Ayarlar butonu ekle (yenile butonundan önce)
        self.settings_btn = QPushButton("☰")  # Hamburger menu icon
        self.settings_btn.setFixedSize(24, 24)
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.setToolTip("Döviz Seçimi")
        self.settings_btn.clicked.connect(self._open_settings)
        self.settings_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
                color: {COLORS['text_secondary']};
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {COLORS['bg_hover']};
                color: {COLORS['primary']};
            }}
        """)

        # Yenile butonundan önce ekle (refresh_btn'den önce)
        self.header_layout.insertWidget(self.header_layout.count() - 2, self.settings_btn)

    def create_content(self):
        """Widget içeriğini oluşturur"""
        # Döviz satırları container
        self.rows_layout = QVBoxLayout()
        self.rows_layout.setSpacing(4)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)

        self.content_layout.addLayout(self.rows_layout)

        # Son güncelleme
        self.update_label = QLabel("")
        self.update_label.setFont(QFont(FONT_FAMILY_QT, 9))
        self.update_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.update_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.content_layout.addWidget(self.update_label)

        self.content_layout.addStretch()

    def _open_settings(self):
        """Ayarlar diyalogunu açar"""
        current = self._config.config.get("currencies", self.DEFAULT_CURRENCIES)
        dialog = CurrencySettingsDialog(current, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected = dialog.get_selected()
            if selected:  # En az bir tane seçili olmalı
                self._config.config["currencies"] = selected
                self.settings_changed.emit(selected)
                self.refresh_data()

    def refresh_data(self):
        """Döviz verilerini yeniler"""
        self.set_loading(True)

        try:
            from core.external_apis.tcmb_api import TCMBService

            rates = TCMBService.get_rates()

            # Mevcut satırları temizle
            while self.rows_layout.count():
                item = self.rows_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            self._currency_rows = []

            # Config'den para birimlerini al
            currencies = self._config.config.get("currencies", self.DEFAULT_CURRENCIES)

            for code in currencies:
                rate = rates.get(code)
                if rate:
                    row = CurrencyRow(
                        code=rate.code,
                        name=rate.name,
                        buying=rate.buying,
                        selling=rate.selling,
                        change=rate.change,
                        parent=self
                    )
                    self.rows_layout.addWidget(row)
                    self._currency_rows.append(row)

            # Son güncelleme zamanı
            last_update = TCMBService.get_last_update()
            if last_update:
                self.update_label.setText(f"TCMB • {last_update.strftime('%H:%M')}")
            else:
                self.update_label.setText("TCMB")

        except Exception as e:
            print(f"CurrencyWidget hatası: {e}")
            self.update_label.setText("Veri alınamadı")
        finally:
            self.set_loading(False)

    def set_currencies(self, currencies: List[str]):
        """Gösterilecek para birimlerini ayarlar"""
        self._config.config["currencies"] = currencies
        self.refresh_data()
