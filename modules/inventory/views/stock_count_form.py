"""
Akıllı İş - Stok Sayımı Form Sayfası
"""

from typing import Optional
from decimal import Decimal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QMessageBox,
    QTableWidgetItem,
    QDateTimeEdit,
    QCheckBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDateTime
import qtawesome as qta

from config.icons import ICONS
from ui.components import (
    PageHeader,
    EnhancedTableWidget,
    ColumnConfig,
)


class StockCountFormPage(QWidget):
    """Stok sayımı formu"""

    saved, cancelled, completed = pyqtSignal(dict), pyqtSignal(), pyqtSignal(dict)

    def __init__(self, count_data: Optional[dict] = None, parent=None):
        super().__init__(parent)
        self.count_data = count_data
        self.is_edit_mode = count_data is not None
        self.items_data = []
        self.count_lines = []
        self.setup_ui()
        if self.is_edit_mode:
            self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        title_text = "Sayım Düzenle" if self.is_edit_mode else "Yeni Stok Sayımı"
        self.header = PageHeader(
            title=title_text, icon=ICONS.INVENTORY, show_back=True, parent=self
        )
        self.header.back_clicked.connect(self.cancelled.emit)
        db = QPushButton("Taslak Kaydet")
        db.setProperty("class", "btn-secondary")
        db.setFixedHeight(36)
        db.setIcon(qta.icon(ICONS.SAVE, color="#ffffff"))
        db.clicked.connect(lambda: self._on_save("draft"))
        cb = QPushButton("Tamamla")
        cb.setProperty("class", "btn-primary")
        cb.setFixedHeight(36)
        cb.setIcon(qta.icon(ICONS.CHECK, color="#ffffff"))
        cb.clicked.connect(lambda: self._on_save("completed"))
        h = self.header.header_layout()
        h.addWidget(db)
        h.addWidget(cb)
        layout.addWidget(self.header)

        inf = QFrame()
        il = QHBoxLayout(inf)
        il.setContentsMargins(16, 16, 16, 16)
        il.setSpacing(24)
        for t, widget, key in [
            ("Sayım No", QLineEdit(), "no"),
            ("Sayım Tarihi", QDateTimeEdit(), "dt"),
            ("Depo *", QComboBox(), "wh"),
            ("Kategori", QComboBox(), "cat"),
        ]:
            vl = QVBoxLayout()
            vl.addWidget(QLabel(t))
            vl.addWidget(widget)
            il.addLayout(vl)
            if key == "no":
                self.count_no_in = widget
                widget.setPlaceholderText("Otomatik")
            elif key == "dt":
                self.dt_in = widget
                widget.setDateTime(QDateTime.currentDateTime())
                widget.setCalendarPopup(True)
            elif key == "wh":
                self.wh_combo = widget
                widget.currentIndexChanged.connect(self._on_warehouse_changed)
            elif key == "cat":
                self.cat_combo = widget
                widget.addItem("Tüm Kategoriler", None)
        il.addStretch()
        layout.addWidget(inf)

        lf = QFrame()
        ll = QHBoxLayout(lf)
        ll.setContentsMargins(16, 12, 16, 12)
        ll.addWidget(QLabel("Ürünleri depodan yükle:"))
        lb = QPushButton("Ürünleri Yükle")
        lb.setIcon(qta.icon(ICONS.REFRESH, color="#ffffff"))
        lb.setProperty("class", "btn-primary")
        lb.clicked.connect(self._load_items_from_warehouse)
        ll.addWidget(lb)
        ll.addStretch()
        self.zero_check = QCheckBox("Sıfır stokları dahil et")
        ll.addWidget(self.zero_check)
        layout.addWidget(lf)

        cols = [
            ColumnConfig("code", "Stok Kodu", width=120),
            ColumnConfig("name", "Stok Adı", stretch=True),
            ColumnConfig("unit", "Birim", width=70),
            ColumnConfig("sys", "Sistem Stoku", width=110),
            ColumnConfig("cnt", "Sayılan Miktar", width=120),
            ColumnConfig("diff", "Fark", width=100),
            ColumnConfig("cost", "Birim Maliyet", width=110),
            ColumnConfig("tot", "Fark Tutarı", width=120),
            ColumnConfig("note", "Not", width=150),
        ]
        self.table = EnhancedTableWidget(
            table_id="stock_count_lines", columns=cols, parent=self
        )
        layout.addWidget(self.table)

        ff = QFrame()
        fl = QHBoxLayout(ff)
        fl.setContentsMargins(16, 12, 16, 12)
        dl = QVBoxLayout()
        dl.addWidget(QLabel("Açıklama"))
        self.desc_in = QTextEdit()
        self.desc_in.setMaximumHeight(60)
        self.desc_in.setPlaceholderText("Sayım notu...")
        dl.addWidget(self.desc_in)
        fl.addLayout(dl, 2)
        fl.addStretch()
        sl = QVBoxLayout()
        sl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.cnt_lbl = QLabel("Toplam Ürün: 0")
        sl.addWidget(self.cnt_lbl)
        self.res_lbl = QLabel("Sayılan: 0")
        sl.addWidget(self.res_lbl)
        self.diff_lbl = QLabel("Fark: ₺0,00")
        sl.addWidget(self.diff_lbl)
        fl.addLayout(sl)
        layout.addWidget(ff)

    def load_warehouses(self, whs):
        self.wh_combo.clear()
        self.wh_combo.addItem("Seçiniz...", None)
        for w in whs:
            self.wh_combo.addItem(f"{w.code} - {w.name}", w.id)

    def load_categories(self, cats):
        self.cat_combo.clear()
        self.cat_combo.addItem("Tüm Kategoriler", None)
        for c in cats:
            self.cat_combo.addItem(c.name, c.id)

    def set_items_data(self, items):
        self.items_data = [
            {
                "id": i.id,
                "code": i.code,
                "name": i.name,
                "unit_code": i.unit.code if i.unit else "ADET",
                "unit_cost": float(i.purchase_price or 0),
            }
            for i in items
        ]

    def _on_warehouse_changed(self):
        self.count_lines = []
        self._refresh_table()

    def _load_items_from_warehouse(self):
        wid = self.wh_combo.currentData()
        if not wid:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir depo seçin!")
            return
        iz = self.zero_check.isChecked()
        self.count_lines = []
        for itm in self.items_data:
            sq = 0  # TODO: Service'den gelecek
            if not iz and sq == 0:
                continue
            self.count_lines.append(
                {
                    "item_id": itm["id"],
                    "item_code": itm["code"],
                    "item_name": itm["name"],
                    "unit_code": itm["unit_code"],
                    "system_quantity": Decimal(str(sq)),
                    "counted_quantity": None,
                    "unit_cost": Decimal(str(itm["unit_cost"])),
                    "note": "",
                }
            )
        self._refresh_table()
        QMessageBox.information(
            self, "Bilgi", f"{len(self.count_lines)} ürün yüklendi."
        )

    def _refresh_table(self):
        self.table.setRowCount(len(self.count_lines))
        ti, ci, td = len(self.count_lines), 0, Decimal(0)
        vc = self.table.get_visible_columns()
        for r, ln in enumerate(self.count_lines):
            for col_idx, k in enumerate(vc):
                if k == "code":
                    it = QTableWidgetItem(ln["item_code"])
                    it.setForeground(QColor("#818cf8"))
                    self.table.setItem(r, col_idx, it)
                elif k == "name":
                    self.table.setItem(r, col_idx, QTableWidgetItem(ln["item_name"]))
                elif k == "unit":
                    self.table.setItem(r, col_idx, QTableWidgetItem(ln["unit_code"]))
                elif k == "sys":
                    v = ln["system_quantity"]
                    it = QTableWidgetItem(f"{v:,.2f}")
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    self.table.setItem(r, col_idx, it)
                elif k == "cnt":
                    sp = QDoubleSpinBox()
                    sp.setRange(0, 999999999)
                    sp.setDecimals(4)
                    if ln["counted_quantity"] is not None:
                        sp.setValue(float(ln["counted_quantity"]))
                        ci += 1
                    sp.valueChanged.connect(
                        lambda v, row=r: self._on_counted_changed(row, v)
                    )
                    self.table.setCellWidget(r, col_idx, sp)
                elif k == "diff":
                    if ln["counted_quantity"] is not None:
                        df = ln["counted_quantity"] - ln["system_quantity"]
                        it = QTableWidgetItem(f"{df:+,.2f}")
                        it.setTextAlignment(
                            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                        )
                        if df < 0:
                            it.setForeground(QColor("#ef4444"))
                        elif df > 0:
                            it.setForeground(QColor("#10b981"))
                        self.table.setItem(r, col_idx, it)
                    else:
                        self.table.setItem(r, col_idx, QTableWidgetItem("-"))
                elif k == "cost":
                    it = QTableWidgetItem(f"₺{ln['unit_cost']:,.2f}")
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    self.table.setItem(r, col_idx, it)
                elif k == "tot":
                    if ln["counted_quantity"] is not None:
                        da = (ln["counted_quantity"] - ln["system_quantity"]) * ln[
                            "unit_cost"
                        ]
                        td += da
                        it = QTableWidgetItem(f"₺{da:+,.2f}")
                        it.setTextAlignment(
                            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                        )
                        if da < 0:
                            it.setForeground(QColor("#ef4444"))
                        elif da > 0:
                            it.setForeground(QColor("#10b981"))
                        self.table.setItem(r, col_idx, it)
                    else:
                        self.table.setItem(r, col_idx, QTableWidgetItem("-"))
                elif k == "note":
                    ni = QLineEdit()
                    ni.setText(ln.get("note", ""))
                    ni.setPlaceholderText("Not...")
                    ni.textChanged.connect(
                        lambda t, row=r: self._on_note_changed(row, t)
                    )
                    self.table.setCellWidget(r, col_idx, ni)
        self.cnt_lbl.setText(f"Toplam Ürün: {ti}")
        self.res_lbl.setText(f"Sayılan: {ci}")
        self.diff_lbl.setText(f"Fark: ₺{td:+,.2f}")

    def _on_counted_changed(self, row, v):
        if 0 <= row < len(self.count_lines):
            self.count_lines[row]["counted_quantity"] = Decimal(str(v))
            self._refresh_table()

    def _on_note_changed(self, row, t):
        if 0 <= row < len(self.count_lines):
            self.count_lines[row]["note"] = t

    def load_data(self):
        if not self.count_data:
            return
        self.count_no_in.setText(self.count_data.get("count_no", ""))
        self.desc_in.setPlainText(self.count_data.get("description", ""))
        self.count_lines = self.count_data.get("lines", [])
        self._refresh_table()

    def _on_save(self, status):
        if not self.wh_combo.currentData():
            QMessageBox.warning(self, "Uyarı", "Lütfen bir depo seçin!")
            return
        data = self.get_form_data()
        data["status"] = status
        if status == "completed":
            self.completed.emit(data)
        else:
            self.saved.emit(data)

    def get_form_data(self) -> dict:
        return {
            "count_no": self.count_no_in.text().strip() or None,
            "count_date": self.dt_in.dateTime().toPyDateTime(),
            "warehouse_id": self.wh_combo.currentData(),
            "description": self.desc_in.toPlainText().strip() or None,
            "lines": self.count_lines,
        }
