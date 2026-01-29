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
    QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
import qtawesome as qta

from config.icons import ICONS
from ui.components.toast import show_toast
from ui.components import PageHeader
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
        self.header = PageHeader(
            title="Yeni Stok Talebi", icon=ICONS.INVENTORY, show_back=True, parent=self
        )
        self.header.back_clicked.connect(self.cancelled.emit)
        sb = QPushButton("Talebi Gönder")
        sb.setProperty("class", "btn-primary")
        sb.setFixedHeight(36)
        sb.setIcon(qta.icon(ICONS.CHECK, color="#ffffff"))
        sb.clicked.connect(self._on_save)
        self.header.header_layout().addWidget(sb)
        layout.addWidget(self.header)

        fg = QGroupBox("Stok Talep Bilgileri")
        fl = QFormLayout(fg)
        fl.setSpacing(16)
        fl.setContentsMargins(16, 24, 16, 24)
        rw = QWidget()
        rl = QHBoxLayout(rw)
        rl.setContentsMargins(0, 0, 0, 0)
        self.ref_in = QLineEdit()
        self.ref_in.setPlaceholderText(
            "Benzer bir ürün seçerek zaman kazanabilirsiniz..."
        )
        self.ref_in.setReadOnly(True)
        rl.addWidget(self.ref_in)
        srb = QPushButton("Seç")
        srb.setFixedSize(70, 36)
        srb.setIcon(qta.icon(ICONS.SEARCH, color="#475569"))
        srb.clicked.connect(self._select_reference_stock)
        rl.addWidget(srb)
        crb = QPushButton()
        crb.setFixedSize(36, 36)
        crb.setIcon(qta.icon(ICONS.CLOSE, color="#ef4444"))
        crb.setToolTip("Referansı Temizle")
        crb.clicked.connect(self._clear_ref)
        rl.addWidget(crb)
        fl.addRow("Referans Stok", rw)
        self.name_in = QLineEdit()
        self.name_in.setPlaceholderText("Talep edilen stok adı")
        fl.addRow("Stok Adı *", self.name_in)

        self.type_combo = QComboBox()
        for t, v in [
            ("Hammadde", ItemType.HAMMADDE),
            ("Mamül", ItemType.MAMUL),
            ("Yarı Mamül", ItemType.YARI_MAMUL),
            ("Ambalaj", ItemType.AMBALAJ),
            ("Sarf Malzeme", ItemType.SARF),
            ("Ticari Mal", ItemType.TICARI),
            ("Hizmet", ItemType.HIZMET),
            ("Diğer", ItemType.DIGER),
        ]:
            self.type_combo.addItem(t, v)
        fl.addRow("Stok Türü *", self.type_combo)
        self.cat_combo = QComboBox()
        fl.addRow("Kategori", self.cat_combo)
        self.uni_combo = QComboBox()
        fl.addRow("Birim", self.uni_combo)
        self.desc_in = QTextEdit()
        self.desc_in.setPlaceholderText(
            "Neden bu stoğa ihtiyaç var? Kullanım alanı vb."
        )
        self.desc_in.setMinimumHeight(100)
        fl.addRow("Açıklama / Gerekçe *", self.desc_in)
        layout.addWidget(fg)
        layout.addStretch()

    def set_items(self, items: list):
        self.items = items

    def load_units(self, units: list):
        self.uni_combo.clear()
        self.uni_combo.addItem("Seçiniz...", None)
        for u in units:
            self.uni_combo.addItem(f"{u.code} - {u.name}", u.id)

    def load_categories(self, cats: list):
        self.cat_combo.clear()
        self.cat_combo.addItem("Seçiniz...", None)
        for c in cats:
            self.cat_combo.addItem(c.name, c.id)

    def _select_reference_stock(self):
        if not self.items:
            show_toast("Seçilebilecek aktif stok bulunamadı.", "WARNING")
            return
        dialog = ItemSelectorDialog(self.items, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_item:
            itm = dialog.selected_item
            self.reference_item = itm
            self.ref_in.setText(f"{itm.code} - {itm.name}")
            self._prefill_form(itm)

    def _clear_ref(self):
        self.reference_item = None
        self.ref_in.clear()

    def _prefill_form(self, itm: Item):
        self.name_in.setText(itm.name + " (KOPYA)")
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == itm.item_type:
                self.type_combo.setCurrentIndex(i)
                break
        if itm.category_id:
            for i in range(self.cat_combo.count()):
                if self.cat_combo.itemData(i) == itm.category_id:
                    self.cat_combo.setCurrentIndex(i)
                    break
        if itm.unit_id:
            for i in range(self.uni_combo.count()):
                if self.uni_combo.itemData(i) == itm.unit_id:
                    self.uni_combo.setCurrentIndex(i)
                    break

    def _on_save(self):
        if not self.name_in.text().strip():
            show_toast("Stok adı zorunludur!", "WARNING")
            self.name_in.setFocus()
            return
        if not self.desc_in.toPlainText().strip():
            show_toast("Açıklama / Gerekçe zorunludur!", "WARNING")
            self.desc_in.setFocus()
            return
        self.saved.emit(
            {
                "proposed_name": self.name_in.text().strip(),
                "item_type": self.type_combo.currentData(),
                "category_id": self.cat_combo.currentData(),
                "unit_id": self.uni_combo.currentData(),
                "description": self.desc_in.toPlainText().strip(),
                "reference_stock_id": (
                    self.reference_item.id if self.reference_item else None
                ),
            }
        )
