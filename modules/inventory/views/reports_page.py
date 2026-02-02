"""
Akıllı İş - Stok Raporları Sayfası
"""

from decimal import Decimal
import csv
import datetime
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QTableWidgetItem,
    QTabWidget,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QTextDocument
from PyQt6.QtPrintSupport import QPrinter, QPrintPreviewDialog
import qtawesome as qta

from config.icons import ICONS
from config.themes import get_theme
from ui.components import (
    PageHeader,
    EnhancedTableWidget,
    ColumnConfig,
    MiniStatCard,
    ScrollableCardContainer,
)


class StockReportsPage(QWidget):
    """Stok raporları sayfası"""

    page_title = "Stok Raporları"
    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self.wh_balances = []
        self.movements = []
        self.mov_stats = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        self.header = PageHeader(
            title="Stok Raporları",
            icon=ICONS.CHART,
            show_search=False,
            show_add=False,
            show_export=True,
            parent=self,
        )
        pb = QPushButton("Yazdır")
        pb.setProperty("class", "btn-secondary")
        pb.setFixedHeight(36)
        pb.setIcon(qta.icon(ICONS.PRINT, color="#ffffff"))
        h = self.header.header_layout()
        if self.header.refresh_btn:
            h.insertWidget(h.indexOf(self.header.refresh_btn), pb)
        else:
            h.addWidget(pb)
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        self.header.export_clicked.connect(self.export_current_tab)
        pb.clicked.connect(self.print_current_tab)
        layout.addWidget(self.header)

        stats_container = ScrollableCardContainer()
        self.cards = {
            "total": MiniStatCard("Toplam Ürün", "0", "info", icon=ICONS.INVENTORY),
            "val": MiniStatCard("Toplam Değer", "₺0", "success", icon=ICONS.MONEY),
            "low": MiniStatCard("Düşük Stok", "0", "warning", icon=ICONS.WARNING),
            "none": MiniStatCard("Stok Yok", "0", "error", icon=ICONS.CLOSE),
        }
        for card in self.cards.values():
            stats_container.add_card(card)
        stats_container.add_stretch()
        layout.addWidget(stats_container)

        self.tabs = QTabWidget()
        self._setup_status_tab()
        self._setup_critical_tab()
        self._setup_movement_tab()
        self._setup_warehouse_tab()
        layout.addWidget(self.tabs)
        self.cat_combo.currentIndexChanged.connect(self._filter_status_table)
        self.wh_combo.currentIndexChanged.connect(self._filter_status_table)
        self.wh_rep_combo.currentIndexChanged.connect(self._filter_warehouse_table)

    def _setup_status_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        l.setContentsMargins(16, 16, 16, 16)
        fl = QHBoxLayout()
        fl.addWidget(QLabel("Kategori:"))
        self.cat_combo = QComboBox()
        self.cat_combo.addItem("Tümü", None)
        fl.addWidget(self.cat_combo)
        fl.addWidget(QLabel("Depo:"))
        self.wh_combo = QComboBox()
        self.wh_combo.addItem("Tümü", None)
        fl.addWidget(self.wh_combo)
        fl.addStretch()
        l.addLayout(fl)
        cols = [
            ColumnConfig("code", "Stok Kodu", width=120),
            ColumnConfig("name", "Stok Adı", stretch=True),
            ColumnConfig("cat", "Kategori", width=120),
            ColumnConfig("unit", "Birim", width=70),
            ColumnConfig("qty", "Miktar", width=100),
            ColumnConfig("min", "Min. Stok", width=100),
            ColumnConfig("cost", "Birim Maliyet", width=120),
            ColumnConfig("val", "Toplam Değer", width=120),
            ColumnConfig("status", "Durum", width=100),
        ]
        self.status_table = EnhancedTableWidget(
            table_id="report_stock_status", columns=cols, parent=tab
        )
        l.addWidget(self.status_table)
        self.tabs.addTab(tab, "Stok Durumu")

    def _setup_critical_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        l.setContentsMargins(16, 16, 16, 16)
        l.addWidget(
            QLabel("Minimum stok seviyesinin altında veya stokta olmayan ürünler")
        )
        cols = [
            ColumnConfig("code", "Stok Kodu", width=120),
            ColumnConfig("name", "Stok Adı", stretch=True),
            ColumnConfig("qty", "Mevcut", width=100),
            ColumnConfig("min", "Min. Stok", width=100),
            ColumnConfig("diff", "Eksik", width=100),
            ColumnConfig("ord", "Sipariş Mik.", width=120),
            ColumnConfig("lead", "Temin Süresi", width=120),
            ColumnConfig("status", "Durum", width=120),
        ]
        self.critical_table = EnhancedTableWidget(
            table_id="report_critical_stock", columns=cols, parent=tab
        )
        l.addWidget(self.critical_table)
        self.tabs.addTab(tab, "Kritik Stoklar")

    def _setup_movement_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        l.setContentsMargins(16, 16, 16, 16)
        sl = QHBoxLayout()
        self.m_cards = {
            "in": MiniStatCard("Toplam Giriş", "0", "success", icon=ICONS.ARROW_DOWN),
            "out": MiniStatCard("Toplam Çıkış", "0", "error", icon=ICONS.ARROW_UP),
            "tr": MiniStatCard("Transfer", "0", "info", icon=ICONS.MOVEMENT),
        }
        for c in self.m_cards.values():
            sl.addWidget(c)
        sl.addStretch()
        l.addLayout(sl)
        cols = [
            ColumnConfig("code", "Stok Kodu", width=120),
            ColumnConfig("name", "Stok Adı", stretch=True),
            ColumnConfig("in", "Giriş", width=100),
            ColumnConfig("out", "Çıkış", width=100),
            ColumnConfig("tr", "Transfer", width=100),
            ColumnConfig("net", "Net Değişim", width=100),
            ColumnConfig("last", "Son Hareket", width=150),
        ]
        self.movements_table = EnhancedTableWidget(
            table_id="report_stock_movements", columns=cols, parent=tab
        )
        l.addWidget(self.movements_table)
        self.tabs.addTab(tab, "Hareket Özeti")

    def _setup_warehouse_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        l.setContentsMargins(16, 16, 16, 16)
        fl = QHBoxLayout()
        fl.addWidget(QLabel("Depo:"))
        self.wh_rep_combo = QComboBox()
        self.wh_rep_combo.addItem("Tüm Depolar", None)
        fl.addWidget(self.wh_rep_combo)
        fl.addStretch()
        l.addLayout(fl)
        cols = [
            ColumnConfig("wh", "Depo", width=150),
            ColumnConfig("code", "Stok Kodu", width=120),
            ColumnConfig("name", "Stok Adı", stretch=True),
            ColumnConfig("qty", "Miktar", width=100),
            ColumnConfig("unit", "Birim", width=70),
            ColumnConfig("cost", "Birim Maliyet", width=120),
            ColumnConfig("val", "Toplam Değer", width=120),
            ColumnConfig("loc", "Lokasyon", width=120),
        ]
        self.wh_table = EnhancedTableWidget(
            table_id="report_warehouse_stock", columns=cols, parent=tab
        )
        l.addWidget(self.wh_table)
        self.tabs.addTab(tab, "Depo Raporu")

    def load_data(self, data: dict):
        self.items = data.get("items", [])
        self.wh_balances = data.get("warehouse_balances", [])
        self.movements = data.get("movements", [])
        self.mov_stats = data.get("movement_stats", {})
        self.cards["total"].update_value(str(data.get("total_items", 0)))
        self.cards["val"].update_value(f"₺{data.get('total_value', 0):,.2f}")
        self.cards["low"].update_value(str(data.get("low_stock", 0)))
        self.cards["none"].update_value(str(data.get("out_of_stock", 0)))
        self._filter_status_table()
        self._load_critical(data.get("critical_items", []))
        self._filter_warehouse_table()
        self._load_movements()

    def _filter_status_table(self):
        self.status_table.setSortingEnabled(False)
        cid, wid = self.cat_combo.currentData(), self.wh_combo.currentData()
        res = []
        whm = {}
        if wid:
            for b in self.wh_balances:
                if b["warehouse_id"] == wid:
                    whm[b["item_code"]] = b
        for itm in self.items:
            if cid is not None and itm.get("category_id") != cid:
                continue
            di = itm.copy()
            if wid:
                bl = whm.get(itm["code"])
                di["quantity"] = bl["quantity"] if bl else 0
                di["total_value"] = bl["total_value"] if bl else 0
            res.append(di)
        self.status_table.setRowCount(len(res))

        t = get_theme()
        default_color = QColor(t.text_primary)
        vc = self.status_table.get_visible_columns()

        for r, itm in enumerate(res):
            for c, k in enumerate(vc):
                if k == "code":
                    it = QTableWidgetItem(itm.get("code", ""))
                    it.setForeground(default_color)
                    self.status_table.setItem(r, c, it)
                elif k == "name":
                    it = QTableWidgetItem(itm.get("name", ""))
                    it.setForeground(default_color)
                    self.status_table.setItem(r, c, it)
                elif k == "cat":
                    it = QTableWidgetItem(itm.get("category", "-"))
                    it.setForeground(default_color)
                    self.status_table.setItem(r, c, it)
                elif k == "unit":
                    it = QTableWidgetItem(itm.get("unit", ""))
                    it.setForeground(default_color)
                    self.status_table.setItem(r, c, it)
                elif k == "qty":
                    v = itm.get("quantity", 0)
                    it = QTableWidgetItem(f"{v:,.2f}")
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    it.setForeground(default_color)
                    self.status_table.setItem(r, c, it)
                elif k == "min":
                    v = itm.get("min_stock", 0)
                    it = QTableWidgetItem(f"{v:,.2f}")
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    it.setForeground(default_color)
                    self.status_table.setItem(r, c, it)
                elif k == "cost":
                    v = itm.get("unit_cost", 0)
                    it = QTableWidgetItem(f"₺{v:,.2f}")
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    it.setForeground(default_color)
                    self.status_table.setItem(r, c, it)
                elif k == "val":
                    v = itm.get("total_value", 0)
                    it = QTableWidgetItem(f"₺{v:,.2f}")
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    it.setForeground(default_color)
                    self.status_table.setItem(r, c, it)
                elif k == "status":
                    st = itm.get("status", "normal")
                    txts = {
                        "normal": "Normal",
                        "low": "Düşük",
                        "critical": "Kritik",
                        "out_of_stock": "Yok",
                    }
                    clrs = {
                        "normal": "#10b981",
                        "low": "#f59e0b",
                        "critical": "#ef4444",
                        "out_of_stock": "#ef4444",
                    }
                    it = QTableWidgetItem(txts.get(st, ""))
                    it.setForeground(QColor(clrs.get(st, "#fff")))
                    self.status_table.setItem(r, c, it)
        self.status_table.setSortingEnabled(True)

    def _load_critical(self, items: list):
        self.critical_table.setSortingEnabled(False)
        self.critical_table.setRowCount(len(items))

        t = get_theme()
        default_color = QColor(t.text_primary)
        vc = self.critical_table.get_visible_columns()

        for r, itm in enumerate(items):
            for c, k in enumerate(vc):
                if k == "code":
                    it = QTableWidgetItem(itm.get("code", ""))
                    it.setForeground(default_color)
                    self.critical_table.setItem(r, c, it)
                elif k == "name":
                    it = QTableWidgetItem(itm.get("name", ""))
                    it.setForeground(default_color)
                    self.critical_table.setItem(r, c, it)
                elif k == "qty":
                    v = itm.get("quantity", 0)
                    it = QTableWidgetItem(f"{v:,.2f}")
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    it.setForeground(default_color)
                    self.critical_table.setItem(r, c, it)
                elif k == "min":
                    v = itm.get("min_stock", 0)
                    it = QTableWidgetItem(f"{v:,.2f}")
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    it.setForeground(default_color)
                    self.critical_table.setItem(r, c, it)
                elif k == "diff":
                    v = max(0, itm.get("min_stock", 0) - itm.get("quantity", 0))
                    it = QTableWidgetItem(f"{v:,.2f}")
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    it.setForeground(QColor("#ef4444"))
                    self.critical_table.setItem(r, c, it)
                elif k == "ord":
                    v = itm.get("reorder_qty", 0)
                    it = QTableWidgetItem(f"{v:,.2f}")
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    it.setForeground(default_color)
                    self.critical_table.setItem(r, c, it)
                elif k == "lead":
                    v = itm.get("lead_time", 0)
                    it = QTableWidgetItem(f"{v} gün")
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    it.setForeground(default_color)
                    self.critical_table.setItem(r, c, it)
                elif k == "status":
                    v = itm.get("quantity", 0)
                    txt = "Stok Yok" if v <= 0 else "Kritik"
                    it = QTableWidgetItem(txt)
                    it.setForeground(QColor("#ef4444" if v <= 0 else "#f59e0b"))
                    self.critical_table.setItem(r, c, it)
        self.critical_table.setSortingEnabled(True)

    def _load_movements(self):
        self.movements_table.setSortingEnabled(False)
        self.m_cards["in"].update_value(str(self.mov_stats.get("total_in", 0)))
        self.m_cards["out"].update_value(str(self.mov_stats.get("total_out", 0)))
        self.m_cards["tr"].update_value(str(self.mov_stats.get("total_transfer", 0)))
        self.movements_table.setRowCount(len(self.movements))

        t = get_theme()
        default_color = QColor(t.text_primary)
        vc = self.movements_table.get_visible_columns()

        for r, itm in enumerate(self.movements):
            mt, qty = itm.get("type", ""), itm.get("quantity", 0)
            iq, oq, tq = ("-", "-", "-")
            if "Giriş" in mt or "Alış" in mt:
                iq = f"{qty:,.2f}"
            elif "Çıkış" in mt or "Satış" in mt:
                oq = f"{qty:,.2f}"
            else:
                tq = f"{qty:,.2f}"
            for c, k in enumerate(vc):
                if k == "code":
                    it = QTableWidgetItem(itm.get("item_code", ""))
                    it.setForeground(default_color)
                    self.movements_table.setItem(r, c, it)
                elif k == "name":
                    it = QTableWidgetItem(itm.get("item_name", ""))
                    it.setForeground(default_color)
                    self.movements_table.setItem(r, c, it)
                elif k == "in":
                    it = QTableWidgetItem(iq)
                    it.setForeground(default_color)
                    self.movements_table.setItem(r, c, it)
                elif k == "out":
                    it = QTableWidgetItem(oq)
                    it.setForeground(default_color)
                    self.movements_table.setItem(r, c, it)
                elif k == "tr":
                    it = QTableWidgetItem(tq)
                    it.setForeground(default_color)
                    self.movements_table.setItem(r, c, it)
                elif k == "net":
                    nc = (
                        f"+{qty}"
                        if iq != "-"
                        else (f"-{qty}" if oq != "-" else str(qty))
                    )
                    it = QTableWidgetItem(nc)
                    it.setForeground(default_color)
                    self.movements_table.setItem(r, c, it)
                elif k == "last":
                    it = QTableWidgetItem(itm.get("date", ""))
                    it.setForeground(default_color)
                    self.movements_table.setItem(r, c, it)
        self.movements_table.setSortingEnabled(True)

    def _filter_warehouse_table(self):
        self.wh_table.setSortingEnabled(False)
        wid = self.wh_rep_combo.currentData()
        res = (
            [b for b in self.wh_balances if b["warehouse_id"] == wid]
            if wid
            else self.wh_balances
        )
        self.wh_table.setRowCount(len(res))

        t = get_theme()
        default_color = QColor(t.text_primary)
        vc = self.wh_table.get_visible_columns()

        for r, itm in enumerate(res):
            for c, k in enumerate(vc):
                if k == "wh":
                    it = QTableWidgetItem(itm.get("warehouse_name", ""))
                    it.setForeground(default_color)
                    self.wh_table.setItem(r, c, it)
                elif k == "code":
                    it = QTableWidgetItem(itm.get("item_code", ""))
                    it.setForeground(default_color)
                    self.wh_table.setItem(r, c, it)
                elif k == "name":
                    it = QTableWidgetItem(itm.get("item_name", ""))
                    it.setForeground(default_color)
                    self.wh_table.setItem(r, c, it)
                elif k == "qty":
                    v = itm.get("quantity", 0)
                    it = QTableWidgetItem(f"{v:,.2f}")
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    it.setForeground(default_color)
                    self.wh_table.setItem(r, c, it)
                elif k == "unit":
                    it = QTableWidgetItem(itm.get("unit", ""))
                    it.setForeground(default_color)
                    self.wh_table.setItem(r, c, it)
                elif k == "cost":
                    v = itm.get("unit_cost", 0)
                    it = QTableWidgetItem(f"₺{v:,.2f}")
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    it.setForeground(default_color)
                    self.wh_table.setItem(r, c, it)
                elif k == "val":
                    v = itm.get("total_value", 0)
                    it = QTableWidgetItem(f"₺{v:,.2f}")
                    it.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    it.setForeground(default_color)
                    self.wh_table.setItem(r, c, it)
                elif k == "loc":
                    it = QTableWidgetItem(str(itm.get("location", "-")))
                    it.setForeground(default_color)
                    self.wh_table.setItem(r, c, it)
        self.wh_table.setSortingEnabled(True)

    def export_current_tab(self):
        idx = self.tabs.currentIndex()
        tbl = [
            self.status_table,
            self.critical_table,
            self.movements_table,
            self.wh_table,
        ][idx]
        name = ["stok_durumu", "kritik_stoklar", "hareket_ozeti", "depo_raporu"][idx]
        p, _ = QFileDialog.getSaveFileName(
            self,
            "Dışa Aktar",
            f"{name}_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
            "CSV Dosyası (*.csv)",
        )
        if p:
            try:
                with open(p, "w", newline="", encoding="utf-8-sig") as f:
                    w = csv.writer(f)
                    w.writerow(
                        [
                            tbl.horizontalHeaderItem(c).text()
                            for c in range(tbl.columnCount())
                        ]
                    )
                    for r in range(tbl.rowCount()):
                        w.writerow(
                            [
                                tbl.item(r, c).text() if tbl.item(r, c) else ""
                                for c in range(tbl.columnCount())
                            ]
                        )
                QMessageBox.information(self, "Başarılı", "Rapor dışa aktarıldı.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Dosya kaydedilemedi:\n{str(e)}")

    def print_current_tab(self):
        pr = QPrinter(QPrinter.PrinterMode.HighResolution)
        pre = QPrintPreviewDialog(pr, self)
        pre.paintRequested.connect(self._handle_print_request)
        pre.exec()

    def _handle_print_request(self, pr):
        idx = self.tabs.currentIndex()
        title = [
            "Stok Durum Raporu",
            "Kritik Stok Raporu",
            "Hareket Özeti Raporu",
            "Depo Raporu",
        ][idx]
        tbl = [
            self.status_table,
            self.critical_table,
            self.movements_table,
            self.wh_table,
        ][idx]
        html = f"<h1>{title}</h1><p>Tarih: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}</p><table border='1' cellspacing='0' cellpadding='4' style='width:100%; border-collapse: collapse;'><thead><tr>"
        for c in range(tbl.columnCount()):
            html += f"<th style='background-color: #f0f0f0;'>{tbl.horizontalHeaderItem(c).text()}</th>"
        html += "</tr></thead><tbody>"
        for r in range(tbl.rowCount()):
            html += "<tr>"
            for c in range(tbl.columnCount()):
                it = tbl.item(r, c)
                html += f"<td>{it.text() if it else ''}</td>"
            html += "</tr>"
        html += "</tbody></table>"
        doc = QTextDocument()
        doc.setHtml(html)
        doc.print(pr)

    def load_categories(self, cats: list):
        self.cat_combo.clear()
        self.cat_combo.addItem("Tümü", None)
        for c in cats:
            self.cat_combo.addItem(c.name, c.id)

    def load_warehouses(self, whs: list):
        self.wh_combo.clear()
        self.wh_combo.addItem("Tümü", None)
        self.wh_rep_combo.clear()
        self.wh_rep_combo.addItem("Tüm Depolar", None)
        for w in whs:
            self.wh_combo.addItem(w.name, w.id)
            self.wh_rep_combo.addItem(w.name, w.id)
