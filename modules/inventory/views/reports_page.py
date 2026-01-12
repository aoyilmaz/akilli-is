"""
Akıllı İş - Stok Raporları Sayfası
"""

from decimal import Decimal
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
    QGridLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from ui.components.stat_cards import MiniStatCard

from config import COLORS
from config.styles import get_button_style, BTN_HEIGHT_NORMAL, ICONS


class StockReportsPage(QWidget):
    """Stok raporları sayfası"""

    page_title = "Stok Raporları"
    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # === Başlık ===
        header_layout = QHBoxLayout()

        title = QLabel("📊 Stok Raporları")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Dışa aktar
        export_btn = QPushButton(f"{ICONS['export']} Excel'e Aktar")
        export_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        export_btn.setStyleSheet(get_button_style("export"))
        header_layout.addWidget(export_btn)

        # Yazdır
        print_btn = QPushButton(f"{ICONS['print']} Yazdır")
        print_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        print_btn.setStyleSheet(get_button_style("print"))
        header_layout.addWidget(print_btn)

        # Yenile
        refresh_btn = QPushButton(f"{ICONS['refresh']} Yenile")
        refresh_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        refresh_btn.setStyleSheet(get_button_style("refresh"))
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

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
        # Özet kartları güncelle
        self._update_card(self.total_items_card, str(data.get("total_items", 0)))
        self._update_card(self.total_value_card, f"₺{data.get('total_value', 0):,.2f}")
        self._update_card(self.low_stock_card, str(data.get("low_stock", 0)))
        self._update_card(self.out_of_stock_card, str(data.get("out_of_stock", 0)))

        # Stok durum tablosu
        self._load_status_table(data.get("items", []))

        # Kritik stok tablosu
        self._load_critical_table(data.get("critical_items", []))

    def _update_card(self, card: MiniStatCard, value: str):
        """Kart değerini güncelle"""
        card.update_value(value)

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
