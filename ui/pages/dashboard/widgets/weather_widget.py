"""
Akıllı İş - WeatherWidget

Çoklu lokasyon destekli hava durumu widget'ı.
"""

from typing import Optional, List, Dict

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QPushButton,
    QDialog,
    QDialogButtonBox,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QFrame,
    QScrollArea,
    QGridLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from config.styles import COLORS, FONT_FAMILY_QT
from .base import BaseWidget, WidgetConfig


# Türkiye il ve ilçe verileri
TURKEY_LOCATIONS = {
    "İstanbul": {
        "districts": ["Kadıköy", "Beşiktaş", "Üsküdar", "Beyoğlu", "Şişli", "Bakırköy",
                     "Ataşehir", "Maltepe", "Kartal", "Pendik", "Tuzla", "Sarıyer",
                     "Fatih", "Eyüpsultan", "Başakşehir", "Esenyurt", "Beylikdüzü"],
        "code": "TR"
    },
    "Ankara": {
        "districts": ["Çankaya", "Keçiören", "Mamak", "Yenimahalle", "Etimesgut",
                     "Sincan", "Altındağ", "Pursaklar", "Gölbaşı", "Polatlı"],
        "code": "TR"
    },
    "İzmir": {
        "districts": ["Konak", "Karşıyaka", "Bornova", "Buca", "Bayraklı", "Çiğli",
                     "Gaziemir", "Karabağlar", "Balçova", "Narlıdere", "Urla", "Çeşme"],
        "code": "TR"
    },
    "Bursa": {
        "districts": ["Osmangazi", "Nilüfer", "Yıldırım", "Gemlik", "Mudanya", "İnegöl"],
        "code": "TR"
    },
    "Antalya": {
        "districts": ["Muratpaşa", "Kepez", "Konyaaltı", "Alanya", "Manavgat", "Serik", "Kaş"],
        "code": "TR"
    },
    "Adana": {
        "districts": ["Seyhan", "Yüreğir", "Çukurova", "Sarıçam", "Ceyhan"],
        "code": "TR"
    },
    "Konya": {
        "districts": ["Selçuklu", "Meram", "Karatay", "Ereğli", "Akşehir"],
        "code": "TR"
    },
    "Gaziantep": {
        "districts": ["Şahinbey", "Şehitkamil", "Nizip", "İslahiye"],
        "code": "TR"
    },
    "Kocaeli": {
        "districts": ["İzmit", "Gebze", "Darıca", "Körfez", "Derince"],
        "code": "TR"
    },
    "Mersin": {
        "districts": ["Yenişehir", "Mezitli", "Akdeniz", "Toroslar", "Tarsus"],
        "code": "TR"
    },
    "Diyarbakır": {
        "districts": ["Bağlar", "Kayapınar", "Yenişehir", "Sur"],
        "code": "TR"
    },
    "Kayseri": {
        "districts": ["Melikgazi", "Kocasinan", "Talas"],
        "code": "TR"
    },
    "Eskişehir": {
        "districts": ["Odunpazarı", "Tepebaşı"],
        "code": "TR"
    },
    "Samsun": {
        "districts": ["Atakum", "İlkadım", "Canik", "Tekkeköy"],
        "code": "TR"
    },
    "Trabzon": {
        "districts": ["Ortahisar", "Akçaabat", "Yomra", "Arsin"],
        "code": "TR"
    },
    "Denizli": {
        "districts": ["Pamukkale", "Merkezefendi"],
        "code": "TR"
    },
    "Malatya": {
        "districts": ["Battalgazi", "Yeşilyurt"],
        "code": "TR"
    },
    "Erzurum": {
        "districts": ["Yakutiye", "Palandöken", "Aziziye"],
        "code": "TR"
    },
    "Van": {
        "districts": ["İpekyolu", "Tuşba", "Edremit"],
        "code": "TR"
    },
    "Şanlıurfa": {
        "districts": ["Haliliye", "Karaköprü", "Eyyübiye"],
        "code": "TR"
    },
}

# Diğer ülke şehirleri
WORLD_LOCATIONS = {
    "Türkiye": TURKEY_LOCATIONS,
    "Almanya": {
        "Berlin": {"districts": [], "code": "DE"},
        "Münih": {"districts": [], "code": "DE"},
        "Frankfurt": {"districts": [], "code": "DE"},
        "Hamburg": {"districts": [], "code": "DE"},
    },
    "İngiltere": {
        "Londra": {"districts": [], "code": "GB"},
        "Manchester": {"districts": [], "code": "GB"},
        "Birmingham": {"districts": [], "code": "GB"},
    },
    "ABD": {
        "New York": {"districts": [], "code": "US"},
        "Los Angeles": {"districts": [], "code": "US"},
        "Chicago": {"districts": [], "code": "US"},
    },
    "Fransa": {
        "Paris": {"districts": [], "code": "FR"},
        "Lyon": {"districts": [], "code": "FR"},
        "Marsilya": {"districts": [], "code": "FR"},
    },
}


class LocationSettingsDialog(QDialog):
    """Lokasyon seçim diyaloğu"""

    def __init__(self, current_locations: List[Dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Lokasyon Seçimi")
        self.setMinimumWidth(500)
        self.setMinimumHeight(500)
        self._current_locations = current_locations or []
        self._setup_ui()
        self._setup_style()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Başlık
        title = QLabel("Hava Durumu Lokasyonları")
        title.setFont(QFont(FONT_FAMILY_QT, 12, QFont.Weight.DemiBold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(title)

        # Seçim alanı
        selection_frame = QFrame()
        selection_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 12px;
            }}
        """)
        selection_layout = QVBoxLayout(selection_frame)

        # Ülke seçimi
        country_layout = QHBoxLayout()
        country_label = QLabel("Ülke:")
        country_label.setFont(QFont(FONT_FAMILY_QT, 10))
        country_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        country_label.setFixedWidth(60)
        country_layout.addWidget(country_label)

        self.country_combo = QComboBox()
        self.country_combo.addItems(list(WORLD_LOCATIONS.keys()))
        self.country_combo.currentTextChanged.connect(self._on_country_changed)
        self._style_combo(self.country_combo)
        country_layout.addWidget(self.country_combo, 1)
        selection_layout.addLayout(country_layout)

        # Şehir seçimi
        city_layout = QHBoxLayout()
        city_label = QLabel("Şehir:")
        city_label.setFont(QFont(FONT_FAMILY_QT, 10))
        city_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        city_label.setFixedWidth(60)
        city_layout.addWidget(city_label)

        self.city_combo = QComboBox()
        self.city_combo.currentTextChanged.connect(self._on_city_changed)
        self._style_combo(self.city_combo)
        city_layout.addWidget(self.city_combo, 1)
        selection_layout.addLayout(city_layout)

        # İlçe seçimi
        district_layout = QHBoxLayout()
        district_label = QLabel("İlçe:")
        district_label.setFont(QFont(FONT_FAMILY_QT, 10))
        district_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        district_label.setFixedWidth(60)
        district_layout.addWidget(district_label)

        self.district_combo = QComboBox()
        self._style_combo(self.district_combo)
        district_layout.addWidget(self.district_combo, 1)
        selection_layout.addLayout(district_layout)

        # Ekle butonu
        add_btn = QPushButton("+ Lokasyon Ekle")
        add_btn.clicked.connect(self._add_location)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: white;
            }}
            QPushButton:hover {{
                background: {COLORS['primary_hover']};
            }}
        """)
        selection_layout.addWidget(add_btn)

        layout.addWidget(selection_frame)

        # Eklenen lokasyonlar listesi
        list_label = QLabel("Eklenen Lokasyonlar:")
        list_label.setFont(QFont(FONT_FAMILY_QT, 10, QFont.Weight.DemiBold))
        list_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(list_label)

        self.location_list = QListWidget()
        self.location_list.setStyleSheet(f"""
            QListWidget {{
                background: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 4px;
            }}
            QListWidget::item {{
                background: {COLORS['bg_card']};
                border-radius: 4px;
                padding: 8px;
                margin: 2px;
                color: {COLORS['text_primary']};
            }}
            QListWidget::item:selected {{
                background: {COLORS['primary']};
            }}
        """)
        layout.addWidget(self.location_list, 1)

        # Kaldır butonu
        remove_btn = QPushButton("Seçili Lokasyonu Kaldır")
        remove_btn.clicked.connect(self._remove_selected)
        remove_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['danger']};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: white;
            }}
            QPushButton:hover {{
                background: #d73a3a;
            }}
        """)
        layout.addWidget(remove_btn)

        # Dialog butonları
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

        # İlk yükleme
        self._on_country_changed(self.country_combo.currentText())
        self._load_current_locations()

    def _style_combo(self, combo: QComboBox):
        combo.setStyleSheet(f"""
            QComboBox {{
                background: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 6px 10px;
                color: {COLORS['text_primary']};
                min-height: 28px;
            }}
            QComboBox:hover {{
                border-color: {COLORS['primary']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox QAbstractItemView {{
                background: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                color: {COLORS['text_primary']};
                selection-background-color: {COLORS['primary']};
            }}
        """)

    def _setup_style(self):
        self.setStyleSheet(f"""
            QDialog {{
                background: {COLORS['bg_card']};
            }}
        """)

    def _on_country_changed(self, country: str):
        self.city_combo.clear()
        self.district_combo.clear()

        if country in WORLD_LOCATIONS:
            cities = list(WORLD_LOCATIONS[country].keys())
            self.city_combo.addItems(cities)

    def _on_city_changed(self, city: str):
        self.district_combo.clear()
        country = self.country_combo.currentText()

        if country in WORLD_LOCATIONS and city in WORLD_LOCATIONS[country]:
            districts = WORLD_LOCATIONS[country][city].get("districts", [])
            if districts:
                self.district_combo.addItem("(Tümü)")
                self.district_combo.addItems(districts)

    def _add_location(self):
        country = self.country_combo.currentText()
        city = self.city_combo.currentText()
        district = self.district_combo.currentText()

        if not city:
            return

        # Lokasyon verisi oluştur
        location = {
            "country": country,
            "city": city,
            "district": district if district and district != "(Tümü)" else None,
            "query": district if district and district != "(Tümü)" else city
        }

        # Listeye ekle
        display = f"🌍 {city}"
        if location["district"]:
            display += f", {location['district']}"
        display += f" ({country})"

        item = QListWidgetItem(display)
        item.setData(Qt.ItemDataRole.UserRole, location)
        self.location_list.addItem(item)

    def _remove_selected(self):
        current = self.location_list.currentRow()
        if current >= 0:
            self.location_list.takeItem(current)

    def _load_current_locations(self):
        for loc in self._current_locations:
            display = f"🌍 {loc.get('city', 'Unknown')}"
            if loc.get("district"):
                display += f", {loc['district']}"
            display += f" ({loc.get('country', 'TR')})"

            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, loc)
            self.location_list.addItem(item)

    def get_locations(self) -> List[Dict]:
        """Seçili lokasyonları döner"""
        locations = []
        for i in range(self.location_list.count()):
            item = self.location_list.item(i)
            loc = item.data(Qt.ItemDataRole.UserRole)
            if loc:
                locations.append(loc)
        return locations


class WeatherCard(QFrame):
    """Tek bir lokasyon için hava durumu kartı"""

    def __init__(self, location: Dict, parent=None):
        super().__init__(parent)
        self._location = location
        self._setup_ui()
        self._setup_style()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # Sol: İkon ve sıcaklık
        left_layout = QVBoxLayout()
        left_layout.setSpacing(0)

        self.icon_label = QLabel("☀️")
        self.icon_label.setFont(QFont(FONT_FAMILY_QT, 24))
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.icon_label)

        self.temp_label = QLabel("--°")
        self.temp_label.setFont(QFont(FONT_FAMILY_QT, 20, QFont.Weight.Bold))
        self.temp_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        self.temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.temp_label)

        layout.addLayout(left_layout)

        # Sağ: Detaylar
        right_layout = QVBoxLayout()
        right_layout.setSpacing(2)

        self.city_label = QLabel(self._location.get("city", "--"))
        self.city_label.setFont(QFont(FONT_FAMILY_QT, 10, QFont.Weight.DemiBold))
        self.city_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        right_layout.addWidget(self.city_label)

        if self._location.get("district"):
            self.district_label = QLabel(self._location["district"])
            self.district_label.setFont(QFont(FONT_FAMILY_QT, 9))
            self.district_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
            right_layout.addWidget(self.district_label)

        self.condition_label = QLabel("--")
        self.condition_label.setFont(QFont(FONT_FAMILY_QT, 9))
        self.condition_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        right_layout.addWidget(self.condition_label)

        self.details_label = QLabel("")
        self.details_label.setFont(QFont(FONT_FAMILY_QT, 8))
        self.details_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        right_layout.addWidget(self.details_label)

        right_layout.addStretch()
        layout.addLayout(right_layout, 1)

    def _setup_style(self):
        self.setStyleSheet(f"""
            WeatherCard {{
                background: {COLORS['bg_secondary']};
                border-radius: 6px;
            }}
        """)

    def update_weather(self, weather):
        """Hava durumu verilerini günceller"""
        if weather:
            self.icon_label.setText(weather.condition_icon)
            self.temp_label.setText(f"{weather.temperature}°")
            self.condition_label.setText(weather.condition)

            # Sıcaklığa göre renk
            if weather.temperature >= 30:
                self.temp_label.setStyleSheet(f"color: {COLORS['danger']};")
            elif weather.temperature >= 20:
                self.temp_label.setStyleSheet(f"color: {COLORS['warning']};")
            elif weather.temperature >= 10:
                self.temp_label.setStyleSheet(f"color: {COLORS['text_primary']};")
            else:
                self.temp_label.setStyleSheet(f"color: {COLORS['info']};")

            # Detaylar
            details = []
            if weather.humidity:
                details.append(f"💧{weather.humidity}%")
            if weather.wind_speed:
                details.append(f"💨{weather.wind_speed}km/s")
            self.details_label.setText(" ".join(details))
        else:
            self.icon_label.setText("❓")
            self.temp_label.setText("--°")
            self.condition_label.setText("Veri alınamadı")
            self.details_label.setText("")


class WeatherWidget(BaseWidget):
    """
    Çoklu lokasyon destekli hava durumu widget'ı
    """

    widget_code = "weather"
    widget_name = "Hava Durumu"
    widget_type = "external"
    widget_description = "Çoklu lokasyon hava durumu"
    widget_icon = "cloud"
    min_size = (1, 1)
    default_size = (1, 2)
    max_size = (2, 3)
    refresh_interval = 1800  # 30 dakika

    DEFAULT_LOCATIONS = [{"country": "Türkiye", "city": "İstanbul", "query": "Istanbul"}]

    settings_changed = pyqtSignal(list)

    def __init__(
        self,
        config: Optional[WidgetConfig] = None,
        edit_mode: bool = False,
        parent: Optional[QWidget] = None
    ):
        self._weather_cards: List[WeatherCard] = []
        super().__init__(config, edit_mode, parent)

    def _create_header(self):
        """Widget başlık çubuğunu oluşturur (ayarlar butonu ekli)"""
        super()._create_header()

        # Ayarlar butonu
        self.settings_btn = QPushButton("☰")  # Hamburger menu icon
        self.settings_btn.setFixedSize(24, 24)
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.setToolTip("Lokasyon Ayarları")
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
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent;")

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(6)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)

        scroll.setWidget(self.cards_container)
        self.content_layout.addWidget(scroll, 1)

    def _open_settings(self):
        """Lokasyon ayarları diyalogunu açar"""
        current = self._config.config.get("locations", self.DEFAULT_LOCATIONS)
        dialog = LocationSettingsDialog(current, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            locations = dialog.get_locations()
            if locations:
                self._config.config["locations"] = locations
                self.settings_changed.emit(locations)
                self.refresh_data()

    def refresh_data(self):
        """Tüm lokasyonlar için hava durumu verilerini yeniler"""
        self.set_loading(True)

        try:
            from core.external_apis.weather_api import WeatherService

            # Mevcut kartları temizle
            while self.cards_layout.count():
                item = self.cards_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            self._weather_cards = []

            # Lokasyonları al
            locations = self._config.config.get("locations", self.DEFAULT_LOCATIONS)

            for loc in locations:
                # Kart oluştur
                card = WeatherCard(loc, self)
                self.cards_layout.addWidget(card)
                self._weather_cards.append(card)

                # Hava durumu verisi al
                query = loc.get("query", loc.get("city", "Istanbul"))
                weather = WeatherService.get_weather(query)
                card.update_weather(weather)

            self.cards_layout.addStretch()

        except Exception as e:
            print(f"WeatherWidget hatası: {e}")
        finally:
            self.set_loading(False)

    def set_locations(self, locations: List[Dict]):
        """Lokasyonları ayarlar"""
        self._config.config["locations"] = locations
        self.refresh_data()
