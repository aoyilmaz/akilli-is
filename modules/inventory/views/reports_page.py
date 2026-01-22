"""
Akıllı İş - Stok Raporları Sayfası
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QTabWidget,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QTextDocument
from PyQt6.QtPrintSupport import QPrinter, QPrintPreviewDialog
import csv
import datetime
from ui.components.stat_cards import MiniStatCard

from config import COLORS


class StockReportsPage(QWidget):
    """Stok raporları sayfası"""

    page_title = "Stok Raporları"
    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_items = []
        self.all_warehouse_balances = []
        self.all_movements = []
        self.movement_stats = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # === Header - PageHeader kullanarak ===
        from ui.components.page_header import PageHeader

        self.header = PageHeader(
            title="Stok Raporları",
            icon="📊",
            show_search=False,
            show_refresh=True,
            show_add=False,
            show_export=True,
            parent=self,
        )

        # Yazdır butonu
        print_btn = QPushButton("🖨 Yazdır")
        print_btn.setProperty("class", "btn-secondary")
        print_btn.setFixedHeight(36)

        # Header'a yazdır butonunu ekle
        h_layout = self.header.header_layout()
        if self.header.refresh_btn:
            # Refresh butonundan önce ekle
            idx = h_layout.indexOf(self.header.refresh_btn)
            h_layout.insertWidget(idx, print_btn)
        else:
            h_layout.addWidget(print_btn)

        # Sinyalleri bağla
        # Sinyalleri bağla
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        self.header.export_clicked.connect(self.export_current_tab)
        print_btn.clicked.connect(self.print_current_tab)

        layout.addWidget(self.header)

        # === Özet Kartlar ===
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        self.total_items_card = self._create_card("📦 Toplam Ürün", "0", "#6366f1")
        cards_layout.addWidget(self.total_items_card)

        self.total_value_card = self._create_card("💰 Toplam Değer", "₺0", "#10b981")
        cards_layout.addWidget(self.total_value_card)

        self.low_stock_card = self._create_card("⚠️ Düşük Stok", "0", "#f59e0b")
        cards_layout.addWidget(self.low_stock_card)

        self.out_of_stock_card = self._create_card("❌ Stok Yok", "0", "#ef4444")
        cards_layout.addWidget(self.out_of_stock_card)

        layout.addLayout(cards_layout)

        # === Tab Widget ===
        tabs = QTabWidget()
        # Stok Durum Raporu
        tabs.addTab(self._create_stock_status_tab(), "📋 Stok Durumu")

        # Kritik Stok Raporu
        tabs.addTab(self._create_critical_stock_tab(), "⚠️ Kritik Stoklar")

        # Hareket Özeti
        tabs.addTab(self._create_movement_summary_tab(), "📊 Hareket Özeti")

        # Depo Bazlı Rapor
        tabs.addTab(self._create_warehouse_report_tab(), "🏭 Depo Raporu")

        layout.addWidget(tabs)

        # Filtre sinyalleri (Widgetlar oluşturulduktan sonra bağlanmalı)
        self.status_category_combo.currentIndexChanged.connect(
            self._filter_status_table
        )
        self.status_warehouse_combo.currentIndexChanged.connect(
            self._filter_status_table
        )
        self.wh_report_combo.currentIndexChanged.connect(self._filter_warehouse_table)

    def _create_card(self, title: str, value: str, color: str) -> MiniStatCard:
        """Dashboard tarzı istatistik kartı"""
        return MiniStatCard(title, value, color)

    def _create_stock_status_tab(self) -> QWidget:
        """Stok durum raporu"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)

        # Filtreler
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Kategori:"))
        self.status_category_combo = QComboBox()
        self.status_category_combo.addItem("Tümü", None)
        filter_layout.addWidget(self.status_category_combo)

        filter_layout.addWidget(QLabel("Depo:"))
        self.status_warehouse_combo = QComboBox()
        self.status_warehouse_combo.addItem("Tümü", None)
        filter_layout.addWidget(self.status_warehouse_combo)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Tablo
        self.status_table = QTableWidget()
        self._setup_table(
            self.status_table,
            [
                ("Stok Kodu", 100),
                ("Stok Adı", 250),
                ("Kategori", 120),
                ("Birim", 60),
                ("Miktar", 100),
                ("Min. Stok", 90),
                ("Birim Maliyet", 110),
                ("Toplam Değer", 120),
                ("Durum", 100),
            ],
        )
        layout.addWidget(self.status_table)

        return widget

    def _create_critical_stock_tab(self) -> QWidget:
        """Kritik stok raporu"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)

        info_label = QLabel(
            "⚠️ Minimum stok seviyesinin altında veya stokta olmayan ürünler"
        )
        layout.addWidget(info_label)

        self.critical_table = QTableWidget()
        self._setup_table(
            self.critical_table,
            [
                ("Stok Kodu", 100),
                ("Stok Adı", 250),
                ("Mevcut", 90),
                ("Min. Stok", 90),
                ("Eksik", 90),
                ("Sipariş Miktarı", 110),
                ("Temin Süresi", 100),
                ("Durum", 100),
            ],
        )
        layout.addWidget(self.critical_table)

        return widget

    def _create_movement_summary_tab(self) -> QWidget:
        """Hareket özeti"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)

        # Özet kartlar
        summary_layout = QHBoxLayout()

        self.entry_card = self._create_mini_card("📥 Toplam Giriş", "0", "#10b981")
        summary_layout.addWidget(self.entry_card)

        self.exit_card = self._create_mini_card("📤 Toplam Çıkış", "0", "#ef4444")
        summary_layout.addWidget(self.exit_card)

        self.transfer_card = self._create_mini_card("🔄 Transfer", "0", "#6366f1")
        summary_layout.addWidget(self.transfer_card)

        summary_layout.addStretch()
        layout.addLayout(summary_layout)

        # Tablo
        self.movement_table = QTableWidget()
        self._setup_table(
            self.movement_table,
            [
                ("Stok Kodu", 100),
                ("Stok Adı", 200),
                ("Giriş", 100),
                ("Çıkış", 100),
                ("Transfer", 100),
                ("Net Değişim", 100),
                ("Son Hareket", 140),
            ],
        )
        layout.addWidget(self.movement_table)

        return widget

    def _create_warehouse_report_tab(self) -> QWidget:
        """Depo bazlı rapor"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)

        # Depo seçimi
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Depo:"))
        self.wh_report_combo = QComboBox()
        self.wh_report_combo.addItem("Tüm Depolar", None)
        filter_layout.addWidget(self.wh_report_combo)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Tablo
        self.warehouse_table = QTableWidget()
        self._setup_table(
            self.warehouse_table,
            [
                ("Depo", 150),
                ("Stok Kodu", 100),
                ("Stok Adı", 200),
                ("Miktar", 100),
                ("Birim", 60),
                ("Birim Maliyet", 110),
                ("Toplam Değer", 120),
                ("Lokasyon", 100),
            ],
        )
        layout.addWidget(self.warehouse_table)

        return widget

    def _create_mini_card(self, title: str, value: str, color: str) -> QFrame:
        """Mini özet kartı"""
        card = QFrame()
        card.setFixedWidth(180)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        title_label = QLabel(title)
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setObjectName("value")
        layout.addWidget(value_label)

        return card

    def _setup_table(self, table: QTableWidget, columns: list):
        """Tablo ayarla"""
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels([c[0] for c in columns])

        header = table.horizontalHeader()
        for i, (_, width) in enumerate(columns):
            if i == 1:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                table.setColumnWidth(i, width)

        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)

    def load_data(self, data: dict):
        """Rapor verilerini yükle"""
        # Ham verileri sakla
        self.all_items = data.get("items", [])
        self.all_warehouse_balances = data.get("warehouse_balances", [])
        self.all_movements = data.get("movements", [])
        self.movement_stats = data.get("movement_stats", {})

        # Özet kartları güncelle
        self._update_card(self.total_items_card, str(data.get("total_items", 0)))
        self._update_card(self.total_value_card, f"₺{data.get('total_value', 0):,.2f}")
        self._update_card(self.low_stock_card, str(data.get("low_stock", 0)))
        self._update_card(self.out_of_stock_card, str(data.get("out_of_stock", 0)))

        # Tabloları yükle (Filtreleri uygula)
        self._filter_status_table()

        # Kritik stok tablosu
        self._load_critical_table(data.get("critical_items", []))

        # Depo raporu
        self._filter_warehouse_table()

        # Hareket özeti
        self._load_movement_table()

    def _filter_status_table(self):
        """Stok durum tablosunu filtrele"""
        category_id = self.status_category_combo.currentData()
        warehouse_id = self.status_warehouse_combo.currentData()

        filtered_items = []

        # Depo bakiyeleri için lookup map hazırla: {(item_code, warehouse_id): quantity}
        wh_balances = {}
        if warehouse_id:
            for b in self.all_warehouse_balances:
                if b["warehouse_id"] == warehouse_id:
                    wh_balances[b["item_code"]] = b

        for item in self.all_items:
            # Kategori filtresi
            if category_id is not None and item.get("category_id") != category_id:
                continue

            # Depo filtresi
            # Eğer depo seçiliyse, o depodaki miktarı göster.
            # Eğer o depoda hiç kaydı yoksa (veya miktar 0 ise) listeye ekle ama miktar 0 görünsün?
            # Genellikle depo seçilince sadece o depoda var olanlar listelenir.

            display_item = item.copy()

            if warehouse_id:
                balance = wh_balances.get(item["code"])
                if balance:
                    # Depodaki miktarı ve değeri kullan
                    display_item["quantity"] = balance["quantity"]
                    display_item["total_value"] = balance["total_value"]
                    # Eğer miktar 0 ise ve stokta yoksa gösterme (opsiyonel, şimdilik gösterelim)
                else:
                    # Bu depoda kaydı yok
                    display_item["quantity"] = 0
                    display_item["total_value"] = 0

            filtered_items.append(display_item)

        self._load_status_table(filtered_items)

    def _filter_warehouse_table(self):
        """Depo tablosunu filtrele"""
        warehouse_id = self.wh_report_combo.currentData()

        if warehouse_id:
            filtered = [
                b
                for b in self.all_warehouse_balances
                if b["warehouse_id"] == warehouse_id
            ]
        else:
            filtered = self.all_warehouse_balances

        self._load_warehouse_table(filtered)

    def _load_warehouse_table(self, items: list):
        """Depo tablosunu doldur"""
        self.warehouse_table.setRowCount(len(items))
        for row, item in enumerate(items):
            self.warehouse_table.setItem(
                row, 0, QTableWidgetItem(item.get("warehouse_name", ""))
            )
            self.warehouse_table.setItem(
                row, 1, QTableWidgetItem(item.get("item_code", ""))
            )
            self.warehouse_table.setItem(
                row, 2, QTableWidgetItem(item.get("item_name", ""))
            )

            qty = item.get("quantity", 0)
            qty_item = QTableWidgetItem(f"{qty:,.2f}")
            qty_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.warehouse_table.setItem(row, 3, qty_item)

            self.warehouse_table.setItem(row, 4, QTableWidgetItem(item.get("unit", "")))

            cost = item.get("unit_cost", 0)
            cost_item = QTableWidgetItem(f"₺{cost:,.2f}")
            cost_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.warehouse_table.setItem(row, 5, cost_item)

            total = item.get("total_value", 0)
            total_item = QTableWidgetItem(f"₺{total:,.2f}")
            total_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.warehouse_table.setItem(row, 6, total_item)

            self.warehouse_table.setItem(
                row, 7, QTableWidgetItem(str(item.get("location", "-")))
            )

    def _load_movement_table(self):
        """Hareket tablosunu doldur"""
        # Kartları güncelle
        stats = self.movement_stats
        self._update_card(self.entry_card, str(stats.get("total_in", 0)))
        self._update_card(self.exit_card, str(stats.get("total_out", 0)))
        self._update_card(self.transfer_card, str(stats.get("total_transfer", 0)))

        # Tabloyu doldur
        items = self.all_movements
        self.movement_table.setRowCount(len(items))

        for row, item in enumerate(items):
            self.movement_table.setItem(
                row, 0, QTableWidgetItem(item.get("item_code", ""))
            )
            self.movement_table.setItem(
                row, 1, QTableWidgetItem(item.get("item_name", ""))
            )

            m_type = item.get("type", "")
            qty = item.get("quantity", 0)

            # Giriş/Çıkış sütunlarına ayır
            in_qty = "-"
            out_qty = "-"
            transfer_qty = "-"

            if "Giriş" in m_type or "Alış" in m_type:
                in_qty = f"{qty:,.2f}"
            elif "Çıkış" in m_type or "Satış" in m_type:
                out_qty = f"{qty:,.2f}"
            else:
                transfer_qty = f"{qty:,.2f}"

            self.movement_table.setItem(row, 2, QTableWidgetItem(in_qty))
            self.movement_table.setItem(row, 3, QTableWidgetItem(out_qty))
            self.movement_table.setItem(row, 4, QTableWidgetItem(transfer_qty))

            # Net değişim (basitçe miktar ve yön)
            # Todo: Gerçek kümülatif değişim hesaplanabilir ama şimdilik miktar.
            net_change = (
                f"+{qty}"
                if in_qty != "-"
                else (f"-{qty}" if out_qty != "-" else str(qty))
            )
            self.movement_table.setItem(row, 5, QTableWidgetItem(net_change))

            self.movement_table.setItem(row, 6, QTableWidgetItem(item.get("date", "")))

    def export_current_tab(self):
        """Aktif sekmeyi dışa aktar"""
        current_tab_idx = self.findChild(QTabWidget).currentIndex()

        if current_tab_idx == 0:
            table = self.status_table
            filename = "stok_durumu"
        elif current_tab_idx == 1:
            table = self.critical_table
            filename = "kritik_stoklar"
        elif current_tab_idx == 2:
            table = self.movement_table
            filename = "hareket_ozeti"
        elif current_tab_idx == 3:
            table = self.warehouse_table
            filename = "depo_raporu"
        else:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Dışa Aktar",
            f"{filename}_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
            "CSV Dosyası (*.csv)",
        )

        if path:
            try:
                with open(path, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)

                    # Başlıklar
                    headers = []
                    for col in range(table.columnCount()):
                        headers.append(table.horizontalHeaderItem(col).text())
                    writer.writerow(headers)

                    # Veriler
                    for row in range(table.rowCount()):
                        row_data = []
                        for col in range(table.columnCount()):
                            item = table.item(row, col)
                            row_data.append(item.text() if item else "")
                        writer.writerow(row_data)

                QMessageBox.information(self, "Başarılı", "Rapor dışa aktarıldı.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Dosya kaydedilemedi:\n{str(e)}")

    def print_current_tab(self):
        """Aktif sekmeyi yazdır"""
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        preview = QPrintPreviewDialog(printer, self)
        preview.paintRequested.connect(self._handle_print_request)
        preview.exec()

    def _handle_print_request(self, printer):
        """Yazdırma içeriğini oluştur"""
        current_tab_idx = self.findChild(QTabWidget).currentIndex()
        if current_tab_idx == 0:
            title = "Stok Durum Raporu"
            table = self.status_table
        elif current_tab_idx == 1:
            title = "Kritik Stok Raporu"
            table = self.critical_table
        elif current_tab_idx == 2:
            title = "Hareket Özeti Raporu"
            table = self.movement_table
        elif current_tab_idx == 3:
            title = "Depo Raporu"
            table = self.warehouse_table
        else:
            return

        # HTML oluştur
        html = f"""
        <h1>{title}</h1>
        <p>Tarih: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
        <table border="1" cellspacing="0" cellpadding="4" style="width:100%; border-collapse: collapse;">
            <thead>
                <tr>
        """

        # Başlıklar
        for col in range(table.columnCount()):
            html += f'<th style="background-color: #f0f0f0;">{table.horizontalHeaderItem(col).text()}</th>'

        html += """
                </tr>
            </thead>
            <tbody>
        """

        # Veriler
        for row in range(table.rowCount()):
            html += "<tr>"
            for col in range(table.columnCount()):
                item = table.item(row, col)
                text = item.text() if item else ""
                html += f"<td>{text}</td>"
            html += "</tr>"

        html += """
            </tbody>
        </table>
        """

        doc = QTextDocument()
        doc.setHtml(html)
        doc.print(printer)

    def _update_card(self, card, value: str):
        """Kart değerini güncelle"""
        if hasattr(card, "update_value"):
            card.update_value(value)
        else:
            # Mini card (QFrame) durumu
            lbl = card.findChild(QLabel, "value")
            if lbl:
                lbl.setText(str(value))

    def _load_status_table(self, items: list):
        """Stok durum tablosunu yükle"""
        self.status_table.setRowCount(len(items))

        for row, item in enumerate(items):
            self.status_table.setItem(row, 0, QTableWidgetItem(item.get("code", "")))
            self.status_table.setItem(row, 1, QTableWidgetItem(item.get("name", "")))
            self.status_table.setItem(
                row, 2, QTableWidgetItem(item.get("category", "-"))
            )
            self.status_table.setItem(row, 3, QTableWidgetItem(item.get("unit", "")))

            qty = item.get("quantity", 0)
            qty_item = QTableWidgetItem(f"{qty:,.2f}")
            qty_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.status_table.setItem(row, 4, qty_item)

            min_stock = item.get("min_stock", 0)
            min_item = QTableWidgetItem(f"{min_stock:,.2f}")
            min_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.status_table.setItem(row, 5, min_item)

            cost = item.get("unit_cost", 0)
            cost_item = QTableWidgetItem(f"₺{cost:,.2f}")
            cost_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.status_table.setItem(row, 6, cost_item)

            total = item.get("total_value", 0)
            total_item = QTableWidgetItem(f"₺{total:,.2f}")
            total_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.status_table.setItem(row, 7, total_item)

            status = item.get("status", "normal")
            status_text = {
                "normal": "✅ Normal",
                "low": "⚠️ Düşük",
                "critical": "🔴 Kritik",
                "out_of_stock": "❌ Yok",
            }
            status_colors = {
                "normal": COLORS["success"],
                "low": COLORS["warning"],
                "critical": COLORS["error"],
                "out_of_stock": COLORS["error"],
            }
            status_item = QTableWidgetItem(status_text.get(status, ""))
            status_item.setForeground(QColor(status_colors.get(status, "#ffffff")))
            self.status_table.setItem(row, 8, status_item)

    def _load_critical_table(self, items: list):
        """Kritik stok tablosunu yükle"""
        self.critical_table.setRowCount(len(items))

        for row, item in enumerate(items):
            self.critical_table.setItem(row, 0, QTableWidgetItem(item.get("code", "")))
            self.critical_table.setItem(row, 1, QTableWidgetItem(item.get("name", "")))

            qty = item.get("quantity", 0)
            qty_item = QTableWidgetItem(f"{qty:,.2f}")
            qty_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.critical_table.setItem(row, 2, qty_item)

            min_stock = item.get("min_stock", 0)
            self.critical_table.setItem(row, 3, QTableWidgetItem(f"{min_stock:,.2f}"))

            shortage = max(0, min_stock - qty)
            shortage_item = QTableWidgetItem(f"{shortage:,.2f}")
            shortage_item.setForeground(QColor(COLORS["error"]))
            self.critical_table.setItem(row, 4, shortage_item)

            self.critical_table.setItem(
                row, 5, QTableWidgetItem(f"{item.get('reorder_qty', 0):,.2f}")
            )
            self.critical_table.setItem(
                row, 6, QTableWidgetItem(f"{item.get('lead_time', 0)} gün")
            )

            status = "❌ Stok Yok" if qty <= 0 else "⚠️ Kritik"
            status_item = QTableWidgetItem(status)
            status_item.setForeground(
                QColor(COLORS["error"] if qty <= 0 else COLORS["warning"])
            )
            self.critical_table.setItem(row, 7, status_item)

    def load_categories(self, categories: list):
        """Kategori combolarını yükle"""
        self.status_category_combo.clear()
        self.status_category_combo.addItem("Tümü", None)
        for cat in categories:
            self.status_category_combo.addItem(cat.name, cat.id)

    def load_warehouses(self, warehouses: list):
        """Depo combolarını yükle"""
        self.status_warehouse_combo.clear()
        self.status_warehouse_combo.addItem("Tümü", None)

        self.wh_report_combo.clear()
        self.wh_report_combo.addItem("Tüm Depolar", None)

        for wh in warehouses:
            self.status_warehouse_combo.addItem(wh.name, wh.id)
            self.wh_report_combo.addItem(wh.name, wh.id)
