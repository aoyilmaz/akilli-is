"""
Akıllı İş ERP - Sayfa Başlığı Bileşeni
Tüm sayfalarda tutarlı başlık görünümü sağlar.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QFrame,
    QSizePolicy,
)
from PyQt6.QtCore import pyqtSignal, QTimer, Qt, QSize
import qtawesome as qta
from config.icons import ICONS
from config.menu_data import MENU_DATA


class PageHeader(QWidget):
    """
    Tüm sayfalarda kullanılacak standart sayfa başlığı bileşeni.

    Özellikler:
    - Sayfa başlığı (emoji + metin)
    - Arama kutusu (opsiyonel)
    - Standart aksiyon butonları (Yenile, Ekle, vb.)
    - QSS class-based stillendirme (inline style yok)
    - Depocu paneli tarzı çubuk tasarım
    """

    # Sinyaller
    back_clicked = pyqtSignal()
    refresh_clicked = pyqtSignal()
    add_clicked = pyqtSignal()
    search_changed = pyqtSignal(str)
    export_clicked = pyqtSignal()
    filter_clicked = pyqtSignal()

    def __init__(
        self,
        title: str,
        icon: str = "",
        show_back: bool = False,
        show_search: bool = True,
        show_refresh: bool = True,
        show_add: bool = True,
        add_text: str = "Yeni Ekle",
        show_export: bool = False,
        show_filter: bool = False,
        search_placeholder: str = "Ara...",
        subtitle: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self.setProperty("class", "page-header")
        self.setFixedHeight(42)  # Ana widget yüksekliğini sabitle
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._setup_ui(
            title,
            icon,
            show_back,
            show_search,
            show_refresh,
            show_add,
            add_text,
            show_export,
            show_filter,
            search_placeholder,
            subtitle,
        )

        # Arama için debounce timer
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(self._emit_search)

    def _setup_ui(
        self,
        title,
        icon,
        show_back,
        show_search,
        show_refresh,
        show_add,
        add_text,
        show_export,
        show_filter,
        search_placeholder,
        subtitle,
    ):
        # Doğru ikonu MENU_DATA'dan bulmaya çalış (Fuzzy Matching)
        best_match_icon = None
        max_score = 0

        # Unidecode veya basit normalizasyon için yardımcı fonksiyon
        def normalize(text):
            return text.lower().replace("İ", "i").replace("I", "ı").strip()

        search_title = normalize(title)

        for group in MENU_DATA.values():
            for m_name, m_icon, m_id in group["items"]:
                m_norm = normalize(m_name)
                score = 0

                # 1. Tam Eşleşme
                if search_title == m_norm:
                    score = 100

                # 2. Menü öğesi başlıkta geçiyor (Örn: "Stok Kartları" başlık, "Kartlar" menü - pek olası değil)
                #    Daha ziyade: "Stok Kategorileri" (Başlık) -> "Kategoriler" (Menü)
                elif m_norm in search_title:
                    score = 80 + len(m_norm)  # Uzun eşleşmeleri tercih et

                # 3. Başlık menü öğesinde geçiyor (Örn: "Leads" başlık, "Aday Müşteriler (Leads)" menü)
                elif search_title in m_norm:
                    score = 60 + len(search_title)

                if score > max_score:
                    max_score = score
                    best_match_icon = m_icon

        # Eğer yeterince iyi bir eşleşme bulunduysa kullan
        # Eşik değer: 50
        resolved_icon = best_match_icon if max_score > 50 else icon

        # Eğer özel bir icon bulunamadıysa ve parametre boşsa, varsayılan bir şeyler yapılabilir
        # Ancak şimdilik bulunan iconu veya parametreyi kullanıyoruz.

        # Ana layout - margin olmadan
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header çubuğu (frame)
        self.header_frame = QFrame()
        self.header_frame.setProperty("class", "header-bar")
        self.header_frame.setFixedHeight(42)

        # Header içi layout
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(16, 0, 16, 0)
        header_layout.setSpacing(12)

        # Geri butonu
        if show_back:
            self.back_btn = QPushButton()
            self.back_btn.setIcon(qta.icon(ICONS.BACK, color="#64748b"))
            self.back_btn.setIconSize(QSize(20, 20))
            self.back_btn.setFixedSize(36, 36)
            self.back_btn.setProperty("class", "btn-secondary")
            self.back_btn.clicked.connect(self.back_clicked.emit)
            self.back_btn.setToolTip("Geri Dön")
            header_layout.addWidget(self.back_btn)
        else:
            self.back_btn = None

        # Başlık ve Alt Başlık
        self.title_label = QLabel(title)
        self.title_label = QLabel(title)
        # Icon handling is done below to support subtitle layout correctly

        self.title_label.setProperty("class", "page-title")

        if subtitle:
            title_container = QWidget()
            title_layout = QVBoxLayout(title_container)
            title_layout.setContentsMargins(0, 0, 0, 0)
            title_layout.setSpacing(0)
            title_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

            if resolved_icon and resolved_icon.startswith("ph."):
                h_title = QHBoxLayout()
                h_title.setContentsMargins(0, 0, 0, 0)
                h_title.setSpacing(8)

                icon_lbl = QLabel()
                icon_lbl.setPixmap(
                    qta.icon(resolved_icon, color="#475569").pixmap(24, 24)
                )
                h_title.addWidget(icon_lbl)
                h_title.addWidget(self.title_label)
                h_title.addStretch()
                title_layout.addLayout(h_title)
            else:
                title_layout.addWidget(self.title_label)

            self.subtitle_label = QLabel(subtitle)
            self.subtitle_label.setProperty("class", "page-subtitle")
            self.subtitle_label.setStyleSheet(
                "color: #94a3b8; font-size: 12px; margin-top: 2px;"
            )
            title_layout.addWidget(self.subtitle_label)

            header_layout.addWidget(title_container)
        else:
            if resolved_icon and resolved_icon.startswith("ph."):
                icon_lbl = QLabel()
                icon_lbl.setPixmap(
                    qta.icon(resolved_icon, color="#475569").pixmap(24, 24)
                )
                header_layout.addWidget(icon_lbl)

            header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        # Standart yükseklik
        BTN_HEIGHT = 30

        # Arama kutusu
        if show_search:
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText(f"{search_placeholder}")
            self.search_input.addAction(
                qta.icon(ICONS.SEARCH, color="#94a3b8"),
                QLineEdit.ActionPosition.LeadingPosition,
            )
            self.search_input.setProperty("class", "search-input")
            self.search_input.setFixedSize(280, BTN_HEIGHT)
            self.search_input.textChanged.connect(self._on_search_text_changed)
            header_layout.addWidget(self.search_input)
        else:
            self.search_input = None

        # Filtre butonu
        if show_filter:
            self.filter_btn = QPushButton("Filtrele")
            # self.filter_btn.setIcon(qta.icon("ph.funnel", color="#64748b")) # CSS class ile ikon rengi çakışabilir
            # Buton text only veya ikonlu. Tasarım tercihi: İkon + Text
            self.filter_btn.setIcon(qta.icon(ICONS.FILTER))
            self.filter_btn.setIconSize(QSize(16, 16))
            self.filter_btn.setProperty("class", "btn-filter")
            self.filter_btn.setFixedHeight(BTN_HEIGHT)
            self.filter_btn.clicked.connect(self.filter_clicked.emit)
            header_layout.addWidget(self.filter_btn)
        else:
            self.filter_btn = None

        # Export butonu
        if show_export:
            self.export_btn = QPushButton("Dışa Aktar")
            self.export_btn.setIcon(qta.icon(ICONS.EXPORT))
            self.export_btn.setIconSize(QSize(16, 16))
            self.export_btn.setProperty("class", "btn-export")
            self.export_btn.setFixedHeight(BTN_HEIGHT)
            self.export_btn.clicked.connect(self.export_clicked.emit)
            header_layout.addWidget(self.export_btn)
        else:
            self.export_btn = None

        # Yenile butonu
        if show_refresh:
            self.refresh_btn = QPushButton("Yenile")
            self.refresh_btn.setIcon(qta.icon(ICONS.REFRESH))
            self.refresh_btn.setIconSize(QSize(16, 16))
            self.refresh_btn.setProperty("class", "btn-refresh")
            self.refresh_btn.setFixedHeight(BTN_HEIGHT)
            self.refresh_btn.clicked.connect(self.refresh_clicked.emit)
            header_layout.addWidget(self.refresh_btn)
        else:
            self.refresh_btn = None

        # Ekle butonu
        if show_add:
            self.add_btn = QPushButton(f"{add_text}")
            self.add_btn.setIcon(qta.icon(ICONS.PLUS))
            self.add_btn.setIconSize(QSize(16, 16))
            self.add_btn.setProperty("class", "btn-add")
            self.add_btn.setFixedHeight(BTN_HEIGHT)
            self.add_btn.clicked.connect(self.add_clicked.emit)
            header_layout.addWidget(self.add_btn)
        else:
            self.add_btn = None

        main_layout.addWidget(self.header_frame)

    def _on_search_text_changed(self, text: str):
        """Arama metni değiştiğinde debounce uygula"""
        self._search_timer.start()

    def _emit_search(self):
        """Arama sinyalini yayınla"""
        if self.search_input:
            self.search_changed.emit(self.search_input.text())

    def set_title(self, title: str, icon: str = ""):
        """Başlık metnini güncelle"""
        # Burada ikonu güncellemek zor olabilir çünkü widget yapısı dinamik.
        # Basitçe title'ı güncelleyelim.
        self.title_label.setText(title)

    def get_search_text(self) -> str:
        """Arama metnini döndür"""
        return self.search_input.text() if self.search_input else ""

    def clear_search(self):
        """Arama kutusunu temizle"""
        if self.search_input:
            self.search_input.clear()

    def set_add_enabled(self, enabled: bool):
        """Ekle butonunu etkinleştir/devre dışı bırak"""
        if self.add_btn:
            self.add_btn.setEnabled(enabled)

    def set_refresh_enabled(self, enabled: bool):
        """Yenile butonunu etkinleştir/devre dışı bırak"""
        if self.refresh_btn:
            self.refresh_btn.setEnabled(enabled)

    def set_add_text(self, text: str):
        """Ekle butonu metnini güncelle"""
        if self.add_btn:
            self.add_btn.setText(text)

    def header_layout(self):
        """Header frame içindeki layout'u döndür (widget ekleme için)"""
        return self.header_frame.layout()

    def add_action_button(self, widget: QWidget):
        """Header'a özel aksiyon butonu ekle"""
        # Layout'un sonundaki butonların önüne ekle
        self.header_frame.layout().addWidget(widget)
