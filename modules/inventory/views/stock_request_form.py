"""
Akıllı İş - Stok Talep Formu
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QFormLayout,
    QDialog,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QDialogButtonBox,
    QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from ui.components.toast import show_toast
from ui.components.page_header import PageHeader
from database.models import ItemType, Item


from .item_selector import ItemSelectorDialog


class StockRequestFormPage(QWidget):
    """Stok kartı talep formu"""

    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()

    def __init__(self, items: list = None, parent=None):
        super().__init__(parent)
        self.items = items or []
        self.reference_item = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # === Header ===
        self.header = PageHeader(
            title="Yeni Stok Talebi",
            show_back=True,
            show_search=False,
            show_refresh=False,
            show_add=False,
            parent=self,
        )
        self.header.back_clicked.connect(self.cancelled.emit)

        # Kaydet butonu
        save_btn = QPushButton("💾 Talebi Gönder")
        save_btn.setProperty("class", "btn-primary")
        save_btn.setFixedHeight(36)
        save_btn.clicked.connect(self._on_save)

        self.header.header_layout().addWidget(save_btn)
        layout.addWidget(self.header)

        # === Form ===
        form_group = QGroupBox("Stok Talep Bilgileri")
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(16)
        form_layout.setContentsMargins(16, 24, 16, 24)

        # Referans Stok
        ref_widget = QWidget()
        ref_layout = QHBoxLayout(ref_widget)
        ref_layout.setContentsMargins(0, 0, 0, 0)

        self.ref_stock_input = QLineEdit()
        self.ref_stock_input.setPlaceholderText(
            "Benzer bir ürün seçerek zaman kazanabilirsiniz..."
        )
        self.ref_stock_input.setReadOnly(True)
        ref_layout.addWidget(self.ref_stock_input)

        select_ref_btn = QPushButton("🔍 Seç")
        select_ref_btn.setFixedSize(60, 36)
        select_ref_btn.clicked.connect(self._select_reference_stock)
        ref_layout.addWidget(select_ref_btn)

        clear_ref_btn = QPushButton("❌")
        clear_ref_btn.setFixedSize(36, 36)
        clear_ref_btn.setToolTip("Referansı Temizle")
        clear_ref_btn.clicked.connect(self._clear_reference)
        ref_layout.addWidget(clear_ref_btn)

        form_layout.addRow("Referans Stok", ref_widget)

        # Stok Adı
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Talep edilen stok adı")
        form_layout.addRow("Stok Adı *", self.name_input)

        # Stok Türü
        self.type_combo = QComboBox()
        self.type_combo.addItem("🧱 Hammadde", ItemType.HAMMADDE)
        self.type_combo.addItem("📦 Mamül", ItemType.MAMUL)
        self.type_combo.addItem("⚙️ Yarı Mamül", ItemType.YARI_MAMUL)
        self.type_combo.addItem("🎁 Ambalaj", ItemType.AMBALAJ)
        self.type_combo.addItem("🔧 Sarf Malzeme", ItemType.SARF)
        self.type_combo.addItem("🏷️ Ticari Mal", ItemType.TICARI)
        self.type_combo.addItem("💼 Hizmet", ItemType.HIZMET)
        self.type_combo.addItem("📋 Diğer", ItemType.DIGER)
        form_layout.addRow("Stok Türü *", self.type_combo)

        # Kategori (Opsiyonel)
        self.category_combo = QComboBox()
        form_layout.addRow("Kategori", self.category_combo)

        # Birim (Opsiyonel)
        self.unit_combo = QComboBox()
        form_layout.addRow("Birim", self.unit_combo)

        # Gerekçe / Açıklama
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText(
            "Neden bu stoğa ihtiyaç var? Kullanım alanı vb."
        )
        self.description_input.setMinimumHeight(100)
        form_layout.addRow("Açıklama / Gerekçe *", self.description_input)

        layout.addWidget(form_group)
        layout.addStretch()

    def set_items(self, items: list):
        """Stok listesini güncelle (Referans seçimi için)"""
        self.items = items

    def load_units(self, units: list):
        """Birimleri yükle"""
        self.unit_combo.clear()
        self.unit_combo.addItem("Seçiniz...", None)
        for unit in units:
            self.unit_combo.addItem(f"{unit.code} - {unit.name}", unit.id)

    def load_categories(self, categories: list):
        """Kategorileri yükle"""
        self.category_combo.clear()
        self.category_combo.addItem("Seçiniz...", None)
        for cat in categories:
            self.category_combo.addItem(cat.name, cat.id)

    def _select_reference_stock(self):
        """Referans stok seçimi"""
        if not self.items:
            show_toast("Seçilebilecek aktif stok bulunamadı.", "WARNING")
            return

        dialog = ItemSelectorDialog(self.items, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_item:
            item = dialog.selected_item
            self.reference_item = item
            self.ref_stock_input.setText(f"{item.code} - {item.name}")

            # Formu ön doldur
            self._prefill_form(item)

    def _clear_reference(self):
        """Referansı temizle"""
        self.reference_item = None
        self.ref_stock_input.clear()

        # Alanları sıfırla (isteğe bağlı, kullanıcı girdisi kalabilir)
        # self.name_input.clear()

    def _prefill_form(self, item: Item):
        """Form alanlarını referans stoktan doldur"""
        # Adı aynen koymayalım, kullanıcı yeni ad yazmalı.
        # Ama ipucu olarak placeholder'a koyabiliriz veya boş bırakabiliriz.
        # Kullanıcı sadece "boyut farkı" var dediyse adı kopyalayıp editlemesi kolaylık olabilir.
        self.name_input.setText(item.name + " (KOPYA)")

        # Tür
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == item.item_type:
                self.type_combo.setCurrentIndex(i)
                break

        # Kategori
        if item.category_id:
            for i in range(self.category_combo.count()):
                if self.category_combo.itemData(i) == item.category_id:
                    self.category_combo.setCurrentIndex(i)
                    break

        # Birim
        if item.unit_id:
            for i in range(self.unit_combo.count()):
                if self.unit_combo.itemData(i) == item.unit_id:
                    self.unit_combo.setCurrentIndex(i)
                    break

    def _on_save(self):
        """Kaydet"""
        if not self.name_input.text().strip():
            show_toast("Stok adı zorunludur!", "WARNING")
            self.name_input.setFocus()
            return

        if not self.description_input.toPlainText().strip():
            show_toast("Açıklama / Gerekçe zorunludur!", "WARNING")
            self.description_input.setFocus()
            return

        data = {
            "proposed_name": self.name_input.text().strip(),
            "item_type": self.type_combo.currentData(),
            "category_id": self.category_combo.currentData(),
            "unit_id": self.unit_combo.currentData(),
            "description": self.description_input.toPlainText().strip(),
            "reference_stock_id": (
                self.reference_item.id if self.reference_item else None
            ),
        }

        self.saved.emit(data)
