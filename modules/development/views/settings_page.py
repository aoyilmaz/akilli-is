"""
Akıllı İş - Tema ve Yazı Tipi Ayarları Sayfası
Kullanıcı tercihlerini yönetir
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
    QGridLayout,
    QButtonGroup,
    QRadioButton,
    QGroupBox,
    QSizePolicy,
    QMessageBox,
    QApplication,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from config.themes import ThemeManager, THEMES, FONT_SCALES


class ThemeCard(QFrame):
    """Tema önizleme kartı"""

    def __init__(self, theme_name: str, theme, is_selected: bool = False, parent=None):
        super().__init__(parent)
        self.theme_name = theme_name
        self.theme = theme
        self._is_selected = is_selected

        self.setFixedSize(180, 140)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_style()
        self._setup_ui()

    def _setup_ui(self):
        """Kart içeriğini oluştur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Önizleme alanı
        preview = QFrame()
        preview.setFixedHeight(70)
        preview.setStyleSheet(
            f"""
            QFrame {{
                background-color: {self.theme.bg_primary};
                border: 1px solid {self.theme.border};
                border-radius: 6px;
            }}
        """
        )

        preview_layout = QVBoxLayout(preview)
        preview_layout.setContentsMargins(8, 8, 8, 8)
        preview_layout.setSpacing(3)

        # Mini başlık çubuğu
        title_bar = QFrame()
        title_bar.setFixedHeight(12)
        title_bar.setStyleSheet(
            f"""
            background-color: {self.theme.bg_secondary};
            border-radius: 3px;
        """
        )
        preview_layout.addWidget(title_bar)

        # Mini içerik çizgileri
        for width in [80, 60, 70]:
            line = QFrame()
            line.setFixedHeight(6)
            line.setFixedWidth(width)
            line.setStyleSheet(
                f"""
                background-color: {self.theme.bg_tertiary};
                border-radius: 2px;
            """
            )
            preview_layout.addWidget(line)

        preview_layout.addStretch()
        layout.addWidget(preview)

        # Tema adı
        name_label = QLabel(self.theme.display_name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet(
            """
            font-weight: bold;
            font-size: 12px;
            border: none;
            background: transparent;
        """
        )
        layout.addWidget(name_label)

        # Seçili işareti (her zaman oluştur, içeriği duruma göre ayarla)
        self._check_label = QLabel()
        self._check_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._check_label.setFixedHeight(16)
        if self._is_selected:
            self._check_label.setText("✓ Aktif")
            self._check_label.setStyleSheet(
                """
                color: #4ec9b0;
                font-size: 10px;
                border: none;
                background: transparent;
            """
            )
        else:
            self._check_label.setText("")
            self._check_label.setStyleSheet(
                """
                border: none;
                background: transparent;
            """
            )
        layout.addWidget(self._check_label)

    def _update_style(self):
        """Kart stilini güncelle"""
        border_color = "#007acc" if self._is_selected else "#3e3e42"
        border_width = 2 if self._is_selected else 1

        self.setStyleSheet(
            f"""
            ThemeCard {{
                background-color: #2d2d2d;
                border: {border_width}px solid {border_color};
                border-radius: 8px;
            }}
            ThemeCard:hover {{
                background-color: #3e3e42;
                border-color: #007acc;
            }}
        """
        )

    def set_selected(self, selected: bool):
        """Seçili durumunu güncelle"""
        if self._is_selected == selected:
            return  # Değişiklik yok

        self._is_selected = selected
        self._update_style()

        # Check label'ı güncelle
        if hasattr(self, "_check_label"):
            if selected:
                self._check_label.setText("✓ Aktif")
                self._check_label.setStyleSheet(
                    """
                    color: #4ec9b0;
                    font-size: 10px;
                    border: none;
                    background: transparent;
                """
                )
            else:
                self._check_label.setText("")


class FontScaleButton(QPushButton):
    """Font ölçeği seçim butonu"""

    def __init__(self, scale_key: str, label: str, sample_size: int, parent=None):
        super().__init__(parent)
        self.scale_key = scale_key
        self._is_selected = False

        self.setFixedSize(120, 80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Örnek metin
        sample = QLabel("Aa")
        font = QFont()
        font.setPointSize(sample_size)
        font.setBold(True)
        sample.setFont(font)
        sample.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sample.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(sample)

        # Etiket
        label_widget = QLabel(label)
        label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_widget.setStyleSheet(
            "font-size: 11px; border: none; background: transparent;"
        )
        layout.addWidget(label_widget)

        self._update_style()

    def _update_style(self):
        """Buton stilini güncelle"""
        if self._is_selected:
            self.setStyleSheet(
                """
                FontScaleButton {
                    background-color: #094771;
                    border: 2px solid #007acc;
                    border-radius: 8px;
                }
            """
            )
        else:
            self.setStyleSheet(
                """
                FontScaleButton {
                    background-color: #2d2d2d;
                    border: 1px solid #3e3e42;
                    border-radius: 8px;
                }
                FontScaleButton:hover {
                    background-color: #3e3e42;
                    border-color: #007acc;
                }
            """
            )

    def set_selected(self, selected: bool):
        """Seçili durumunu güncelle"""
        self._is_selected = selected
        self._update_style()


class ThemeSettingsPage(QWidget):
    """Tema ve yazı tipi ayarları sayfası"""

    page_title = "🎨 Tema Ayarları"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_cards = {}
        self.font_scale_buttons = {}
        self.setup_ui()

    def setup_ui(self):
        """Arayüzü oluştur"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Başlık
        title = QLabel("Tema ve Görünüm Ayarları")
        title.setStyleSheet(
            """
            font-size: 24px;
            font-weight: bold;
            color: #ffffff;
            border: none;
        """
        )
        main_layout.addWidget(title)

        description = QLabel(
            "Uygulama temasını ve yazı tipi boyutunu tercihlerinize göre ayarlayın. "
            "Değişiklikler anında uygulanır."
        )
        description.setStyleSheet("color: #808080; font-size: 13px; border: none;")
        description.setWordWrap(True)
        main_layout.addWidget(description)

        # Scroll alanı
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(30)

        # === TEMA SEÇİMİ ===
        theme_section = self._create_theme_section()
        scroll_layout.addWidget(theme_section)

        # === YAZI TİPİ BOYUTU ===
        font_section = self._create_font_section()
        scroll_layout.addWidget(font_section)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        # Alt butonlar
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        reset_btn = QPushButton("Varsayılana Sıfırla")
        reset_btn.setFixedSize(150, 36)
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #3e3e42;
                border: 1px solid #5a5a5a;
                border-radius: 6px;
                color: #cccccc;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4e4e52;
            }
        """
        )
        reset_btn.clicked.connect(self._reset_to_defaults)
        button_layout.addWidget(reset_btn)

        main_layout.addLayout(button_layout)

    def _create_theme_section(self) -> QFrame:
        """Tema seçimi bölümünü oluştur"""
        section = QFrame()
        section.setStyleSheet(
            """
            QFrame {
                background-color: #252526;
                border: 1px solid #3e3e42;
                border-radius: 10px;
            }
        """
        )

        layout = QVBoxLayout(section)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Başlık
        header = QLabel("🌙 Tema Seçimi")
        header.setStyleSheet(
            """
            font-size: 16px;
            font-weight: bold;
            color: #ffffff;
            border: none;
            background: transparent;
        """
        )
        layout.addWidget(header)

        # Light tema bölümü
        light_label = QLabel("Açık Tema")
        light_label.setStyleSheet(
            """
            font-size: 13px;
            color: #808080;
            border: none;
            background: transparent;
        """
        )
        layout.addWidget(light_label)

        light_layout = QHBoxLayout()
        light_layout.setSpacing(15)

        current_theme = ThemeManager.get_theme().name

        # Light tema kartı
        if "light" in THEMES:
            card = ThemeCard(
                "light", THEMES["light"], is_selected=(current_theme == "light")
            )
            card.mousePressEvent = lambda e, n="light": self._on_theme_selected(n)
            self.theme_cards["light"] = card
            light_layout.addWidget(card)

        light_layout.addStretch()
        layout.addLayout(light_layout)

        # Dark temalar bölümü
        dark_label = QLabel("Koyu Temalar")
        dark_label.setStyleSheet(
            """
            font-size: 13px;
            color: #808080;
            border: none;
            background: transparent;
            margin-top: 10px;
        """
        )
        layout.addWidget(dark_label)

        dark_layout = QHBoxLayout()
        dark_layout.setSpacing(15)

        # Dark temalar
        dark_themes = [name for name in THEMES.keys() if name != "light"]
        for theme_name in dark_themes:
            theme = THEMES[theme_name]
            card = ThemeCard(
                theme_name, theme, is_selected=(current_theme == theme_name)
            )
            card.mousePressEvent = lambda e, n=theme_name: self._on_theme_selected(n)
            self.theme_cards[theme_name] = card
            dark_layout.addWidget(card)

        dark_layout.addStretch()

        # Scroll için wrapper
        dark_scroll = QScrollArea()
        dark_scroll.setWidgetResizable(True)
        dark_scroll.setFrameShape(QFrame.Shape.NoFrame)
        dark_scroll.setFixedHeight(160)
        dark_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        dark_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        dark_scroll.setStyleSheet("background: transparent; border: none;")

        dark_container = QWidget()
        dark_container.setLayout(dark_layout)
        dark_scroll.setWidget(dark_container)

        layout.addWidget(dark_scroll)

        return section

    def _create_font_section(self) -> QFrame:
        """Yazı tipi boyutu bölümünü oluştur"""
        section = QFrame()
        section.setStyleSheet(
            """
            QFrame {
                background-color: #252526;
                border: 1px solid #3e3e42;
                border-radius: 10px;
            }
        """
        )

        layout = QVBoxLayout(section)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Başlık
        header = QLabel("📝 Yazı Tipi Boyutu")
        header.setStyleSheet(
            """
            font-size: 16px;
            font-weight: bold;
            color: #ffffff;
            border: none;
            background: transparent;
        """
        )
        layout.addWidget(header)

        description = QLabel(
            "Tüm uygulama genelinde kullanılacak yazı tipi boyutunu seçin."
        )
        description.setStyleSheet(
            """
            color: #808080;
            font-size: 12px;
            border: none;
            background: transparent;
        """
        )
        layout.addWidget(description)

        # Butonlar
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)

        current_scale = ThemeManager.get_font_scale()

        scale_configs = [
            ("small", "Küçük", 14),
            ("normal", "Normal", 18),
            ("large", "Büyük", 22),
        ]

        for scale_key, label, sample_size in scale_configs:
            btn = FontScaleButton(scale_key, label, sample_size)
            btn.set_selected(current_scale == scale_key)
            btn.clicked.connect(
                lambda checked, k=scale_key: self._on_font_scale_selected(k)
            )
            self.font_scale_buttons[scale_key] = btn
            buttons_layout.addWidget(btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        return section

    def _on_theme_selected(self, theme_name: str):
        """Tema seçildiğinde"""
        # Tüm kartları güncelle
        for name, card in self.theme_cards.items():
            card.set_selected(name == theme_name)

        # Temayı uygula
        ThemeManager.set_theme(theme_name)

        # Uygulamaya bildir
        app = QApplication.instance()
        if app:
            # Ana pencereyi bul ve güncelle
            for widget in app.topLevelWidgets():
                if hasattr(widget, "_apply_theme"):
                    widget._apply_theme()

    def _on_font_scale_selected(self, scale_key: str):
        """Yazı tipi boyutu seçildiğinde"""
        # Tüm butonları güncelle
        for key, btn in self.font_scale_buttons.items():
            btn.set_selected(key == scale_key)

        # Font ölçeğini uygula
        ThemeManager.set_font_scale(scale_key)

        # Kullanıcıya bilgi ver
        QMessageBox.information(
            self,
            "Yazı Tipi Boyutu",
            "Yazı tipi boyutu değiştirildi.\n\n"
            "Değişikliğin tam olarak uygulanması için uygulamayı "
            "yeniden başlatmanız gerekebilir.",
            QMessageBox.StandardButton.Ok,
        )

    def _reset_to_defaults(self):
        """Varsayılan ayarlara sıfırla"""
        reply = QMessageBox.question(
            self,
            "Varsayılana Sıfırla",
            "Tema ve yazı tipi ayarları varsayılan değerlere sıfırlanacak.\n\n"
            "Devam etmek istiyor musunuz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Varsayılanlara sıfırla
            self._on_theme_selected("dark")
            self._on_font_scale_selected("normal")

            QMessageBox.information(
                self,
                "Sıfırlandı",
                "Ayarlar varsayılan değerlere sıfırlandı.",
                QMessageBox.StandardButton.Ok,
            )
