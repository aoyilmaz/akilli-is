"""
Akıllı İş - Kategori Form Sayfası
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
    QCheckBox,
    QFrame,
    QFormLayout,
    QMessageBox,
    QGridLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal
import qtawesome as qta

from config.icons import ICONS
from ui.components import PageHeader
from database.models import ItemCategory

CATEGORY_ICONS = [
    "📁",
    "📂",
    "🗂️",
    "📦",
    "📋",
    "🏷️",
    "🧱",
    "⚙️",
    "🔧",
    "🔩",
    "🛠️",
    "⚡",
    "🎨",
    "🧪",
    "💊",
    "🧴",
    "🧹",
    "📱",
    "💻",
    "🖥️",
    "⌨️",
    "🖨️",
    "📷",
    "🔌",
    "🍎",
    "🥤",
    "🍞",
    "🧀",
    "🥩",
    "🐟",
    "👕",
    "👖",
    "👟",
    "👜",
    "💍",
    "⌚",
    "🚗",
    "✈️",
    "🚢",
    "🏠",
    "🏢",
    "🏭",
]


class CategoryFormPage(QWidget):
    """Kategori ekleme/düzenleme formu"""

    saved, cancelled = pyqtSignal(dict), pyqtSignal()

    def __init__(
        self,
        category: Optional[ItemCategory] = None,
        parent_id: Optional[int] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.category = category
        self.parent_id = parent_id
        self.is_edit_mode = category is not None
        self.selected_icon = "📁"
        self.setup_ui()
        if self.is_edit_mode:
            self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        tt = "Kategori Düzenle" if self.is_edit_mode else "Yeni Kategori"
        self.header = PageHeader(
            title=tt, icon=ICONS.INVENTORY, show_back=True, parent=self
        )
        self.header.back_clicked.connect(self.cancelled.emit)
        sb = QPushButton("Kaydet")
        sb.setProperty("class", "btn-primary")
        sb.setFixedHeight(36)
        sb.setIcon(qta.icon(ICONS.SAVE, color="#ffffff"))
        sb.clicked.connect(self._on_save)
        self.header.header_layout().addWidget(sb)
        layout.addWidget(self.header)

        ff = QFrame()
        fl = QVBoxLayout(ff)
        fl.setContentsMargins(24, 24, 24, 24)
        fl.setSpacing(20)
        isec = QVBoxLayout()
        isec.addWidget(QLabel("📂 Kategori İkonu"))
        ig = QGridLayout()
        ig.setSpacing(8)
        self.icon_btns = []
        for i, icon in enumerate(CATEGORY_ICONS):
            btn = QPushButton(icon)
            btn.setFixedSize(48, 48)
            btn.setCheckable(True)
            btn.clicked.connect(lambda chk, ic=icon, b=btn: self._select_icon(ic, b))
            ig.addWidget(btn, i // 12, i % 12)
            self.icon_btns.append(btn)
            if i == 0:
                btn.setChecked(True)
        isec.addLayout(ig)
        fl.addLayout(isec)
        bl = QHBoxLayout()
        bl.setSpacing(24)
        lf = QFormLayout()
        lf.setSpacing(16)
        cl = QHBoxLayout()
        self.code_in = QLineEdit()
        self.code_in.setPlaceholderText("KAT001")
        ab = QPushButton()
        ab.setFixedWidth(40)
        ab.setIcon(qta.icon(ICONS.REFRESH, color="#475569"))
        ab.clicked.connect(self._generate_code)
        cl.addWidget(self.code_in)
        cl.addWidget(ab)
        lf.addRow("Kategori Kodu *", cl)
        self.name_in = QLineEdit()
        self.name_in.setPlaceholderText("Kategori adı")
        lf.addRow("Kategori Adı *", self.name_in)
        self.parent_combo = QComboBox()
        self.parent_combo.addItem("— Ana Kategori —", None)
        lf.addRow("Üst Kategori", self.parent_combo)
        bl.addLayout(lf)
        rf = QFormLayout()
        rf.setSpacing(16)
        self.color_in = QLineEdit()
        self.color_in.setPlaceholderText("#6366f1")
        self.color_in.setMaxLength(7)
        rf.addRow("Renk (Hex)", self.color_in)
        self.desc_in = QTextEdit()
        self.desc_in.setPlaceholderText("Kategori açıklaması...")
        self.desc_in.setMaximumHeight(80)
        rf.addRow("Açıklama", self.desc_in)
        self.active_chk = QCheckBox("Aktif")
        self.active_chk.setChecked(True)
        rf.addRow("", self.active_chk)
        bl.addLayout(rf)
        fl.addLayout(bl)
        layout.addWidget(ff)
        layout.addStretch()

    def load_categories(self, cats: list):
        self.parent_combo.clear()
        self.parent_combo.addItem("— Ana Kategori —", None)
        for c in cats:
            if self.category and (c.id == self.category.id):
                continue
            ind = "  " * (c.level or 0)
            ic = c.icon or "📁"
            self.parent_combo.addItem(f"{ind}{ic} {c.name}", c.id)
        if self.parent_id:
            for i in range(self.parent_combo.count()):
                if self.parent_combo.itemData(i) == self.parent_id:
                    self.parent_combo.setCurrentIndex(i)
                    break

    def load_data(self):
        if not self.category:
            return
        self.code_in.setText(self.category.code)
        self.name_in.setText(self.category.name)
        self.desc_in.setPlainText(self.category.description or "")
        self.color_in.setText(self.category.color or "")
        self.active_chk.setChecked(self.category.is_active)
        if self.category.icon:
            self.selected_icon = self.category.icon
            for b in self.icon_btns:
                b.setChecked(b.text() == self.category.icon)
        if self.category.parent_id:
            self.parent_id = self.category.parent_id

    def _select_icon(self, ic, b):
        self.selected_icon = ic
        for btn in self.icon_btns:
            btn.setChecked(btn == b)

    def _generate_code(self):
        import random

        self.code_in.setText(f"KAT{random.randint(100, 999)}")

    def _on_save(self):
        if not self.code_in.text().strip():
            QMessageBox.warning(self, "Uyarı", "Kategori kodu zorunludur!")
            self.code_in.setFocus()
            return
        if not self.name_in.text().strip():
            QMessageBox.warning(self, "Uyarı", "Kategori adı zorunludur!")
            self.name_in.setFocus()
            return
        self.saved.emit(
            {
                "code": self.code_in.text().strip(),
                "name": self.name_in.text().strip(),
                "description": self.desc_in.toPlainText().strip() or None,
                "parent_id": self.parent_combo.currentData(),
                "level": 1 if self.parent_combo.currentData() else 0,
                "icon": self.selected_icon,
                "color": self.color_in.text().strip() or None,
                "is_active": self.active_chk.isChecked(),
            }
        )
