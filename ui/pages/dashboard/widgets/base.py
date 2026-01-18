"""
Akıllı İş - Dashboard BaseWidget

Tüm dashboard widget'larının temel sınıfı.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Tuple

from PyQt6.QtWidgets import (
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from config.styles import COLORS, FONT_FAMILY_QT


@dataclass
class WidgetConfig:
    """Widget yapılandırma sınıfı"""
    widget_code: str
    position: Dict[str, int] = field(default_factory=lambda: {"row": 0, "col": 0})
    size: Dict[str, int] = field(default_factory=lambda: {"width": 1, "height": 1})
    config: Dict[str, Any] = field(default_factory=dict)


class BaseWidget(QFrame):
    """
    Tüm dashboard widget'larının temel sınıfı

    Her widget bu sınıftan türetilmeli ve aşağıdaki abstract metodları implement etmelidir:
    - create_content(): Widget içeriğini oluşturur
    - refresh_data(): Veriyi yeniler

    Signals:
        refresh_requested: Widget yenileme isteği
        config_changed: Widget yapılandırması değişti
        remove_requested: Widget kaldırma isteği
    """

    # Sınıf özellikleri - her widget sınıfında override edilmeli
    widget_code: str = ""
    widget_name: str = ""
    widget_type: str = "generic"  # stat, chart, external, list, action
    min_size: Tuple[int, int] = (1, 1)
    default_size: Tuple[int, int] = (1, 1)
    max_size: Tuple[int, int] = (2, 2)
    required_permission: Optional[str] = None
    refresh_interval: int = 0  # Saniye cinsinden (0 = otomatik yenileme yok)

    # Signals
    refresh_requested = pyqtSignal()
    config_changed = pyqtSignal(dict)
    remove_requested = pyqtSignal()

    def __init__(
        self,
        config: Optional[WidgetConfig] = None,
        edit_mode: bool = False,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._config = config or WidgetConfig(widget_code=self.widget_code)
        self._edit_mode = edit_mode
        self._refresh_timer: Optional[QTimer] = None
        self._is_loading = False

        self._setup_ui()
        self._setup_style()
        self._setup_refresh_timer()

    def _setup_ui(self):
        """Widget temel UI yapısını oluşturur"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(8)

        # Header
        self._create_header()

        # Content area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(4)
        self.main_layout.addWidget(self.content_widget, 1)

        # Alt sınıfın içerik oluşturması
        self.create_content()

    def _create_header(self):
        """Widget başlık çubuğunu oluşturur"""
        self.header_layout = QHBoxLayout()
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.setSpacing(8)

        # Başlık
        self.title_label = QLabel(self.widget_name)
        self.title_label.setFont(QFont(FONT_FAMILY_QT, 11, QFont.Weight.DemiBold))
        self.title_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        self.header_layout.addWidget(self.title_label)

        self.header_layout.addStretch()

        # Yenile butonu
        self.refresh_btn = QPushButton("↻")
        self.refresh_btn.setFixedSize(24, 24)
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.setToolTip("Yenile")
        self.refresh_btn.clicked.connect(self._on_refresh_clicked)
        self.refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
                color: {COLORS['text_secondary']};
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: {COLORS['bg_hover']};
                color: {COLORS['primary']};
            }}
        """)
        self.header_layout.addWidget(self.refresh_btn)

        # Düzenleme modunda kaldır butonu
        self.remove_btn = QPushButton("×")
        self.remove_btn.setFixedSize(24, 24)
        self.remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_btn.setToolTip("Kaldır")
        self.remove_btn.clicked.connect(self._on_remove_clicked)
        self.remove_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
                color: {COLORS['text_secondary']};
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {COLORS['danger']};
                color: white;
            }}
        """)
        self.remove_btn.setVisible(self._edit_mode)
        self.header_layout.addWidget(self.remove_btn)

        self.main_layout.addLayout(self.header_layout)

    def _setup_style(self):
        """Widget stilini ayarlar"""
        self.setStyleSheet(f"""
            BaseWidget, QFrame {{
                background: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def _setup_refresh_timer(self):
        """Otomatik yenileme timer'ını ayarlar"""
        if self.refresh_interval > 0:
            self._refresh_timer = QTimer(self)
            self._refresh_timer.timeout.connect(self.refresh_data)
            self._refresh_timer.start(self.refresh_interval * 1000)

    def _on_refresh_clicked(self):
        """Yenile butonuna tıklandığında"""
        self.refresh_requested.emit()
        self.refresh_data()

    def _on_remove_clicked(self):
        """Kaldır butonuna tıklandığında"""
        self.remove_requested.emit()

    def set_edit_mode(self, enabled: bool):
        """Düzenleme modunu ayarlar"""
        self._edit_mode = enabled
        self.remove_btn.setVisible(enabled)

        # Düzenleme modunda farklı stil
        if enabled:
            self.setStyleSheet(f"""
                BaseWidget, QFrame {{
                    background: {COLORS['bg_card']};
                    border: 2px dashed {COLORS['primary']};
                    border-radius: 8px;
                }}
            """)
        else:
            self._setup_style()

    def set_loading(self, loading: bool):
        """Yükleniyor durumunu ayarlar"""
        self._is_loading = loading
        self.refresh_btn.setEnabled(not loading)
        if loading:
            self.refresh_btn.setText("⟳")
        else:
            self.refresh_btn.setText("↻")

    def get_config(self) -> WidgetConfig:
        """Widget yapılandırmasını döner"""
        return self._config

    def set_config(self, config: WidgetConfig):
        """Widget yapılandırmasını ayarlar"""
        self._config = config
        self.on_config_changed()

    def on_config_changed(self):
        """Yapılandırma değiştiğinde çağrılır (override edilebilir)"""
        pass

    def create_content(self):
        """
        Widget içeriğini oluşturur

        Bu metod, self.content_layout içine widget'a özgü
        bileşenleri eklemeli. Alt sınıflar bu metodu override etmeli.
        """
        raise NotImplementedError("Alt sınıf create_content() metodunu implement etmeli")

    def refresh_data(self):
        """
        Widget verilerini yeniler

        Bu metod, widget'ın gösterdiği verileri güncellemeli.
        Örneğin: API'den veri çekme, veritabanı sorgusu vb.
        Alt sınıflar bu metodu override etmeli.
        """
        raise NotImplementedError("Alt sınıf refresh_data() metodunu implement etmeli")

    @classmethod
    def can_user_access(cls, user_context) -> bool:
        """
        Kullanıcının bu widget'a erişip erişemeyeceğini kontrol eder

        Args:
            user_context: Mevcut kullanıcı bağlamı

        Returns:
            True eğer erişebiliyorsa
        """
        if not cls.required_permission:
            return True

        if not user_context:
            return False

        # Admin her şeye erişebilir
        if user_context.is_superuser:
            return True

        # İzin kontrolü
        return cls.required_permission in (user_context.permissions or [])

    def stop_timer(self):
        """Otomatik yenileme timer'ını durdurur"""
        if self._refresh_timer:
            self._refresh_timer.stop()

    def start_timer(self):
        """Otomatik yenileme timer'ını başlatır"""
        if self._refresh_timer and self.refresh_interval > 0:
            self._refresh_timer.start(self.refresh_interval * 1000)

    def cleanup(self):
        """Widget temizliği (kapatılırken çağrılır)"""
        self.stop_timer()
