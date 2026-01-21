"""
Akıllı İş - Stok Hareketleri Listesi
Yeni bileşen mimarisi kullanılarak yeniden yapılandırıldı.
"""

from datetime import datetime
from decimal import Decimal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidgetItem,
    QComboBox,
    QDateEdit,
    QMenu,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor, QAction

from config import COLORS
from database.models import StockMovementType
from ui.components import (
    PageHeader,
    EnhancedTableWidget,
    ColumnConfig,
    MiniStatCard,
)


class MovementListPage(QWidget):
    """Stok hareketleri listesi."""

    # Sinyaller
    add_entry_clicked = pyqtSignal()
    add_exit_clicked = pyqtSignal()
    add_transfer_clicked = pyqtSignal()
    view_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()

    TYPE_NAMES = {
        StockMovementType.GIRIS: ("📥 Giriş", COLORS["success"]),
        StockMovementType.CIKIS: ("📤 Çıkış", COLORS["error"]),
        StockMovementType.SATIN_ALMA: ("🛒 Satın Alma", COLORS["success"]),
        StockMovementType.SATIS: ("💰 Satış", COLORS["error"]),
        StockMovementType.URETIM_GIRIS: ("🏭 Üretim Giriş", COLORS["success"]),
        StockMovementType.URETIM_CIKIS: ("🏭 Üretim Çıkış", COLORS["error"]),
        StockMovementType.TRANSFER: ("🔄 Transfer", COLORS["info"]),
        StockMovementType.SAYIM_FAZLA: ("➕ Sayım Fazla", COLORS["success"]),
        StockMovementType.SAYIM_EKSIK: ("➖ Sayım Eksik", COLORS["error"]),
        StockMovementType.FIRE: ("🔥 Fire", COLORS["warning"]),
        StockMovementType.IADE_ALIS: ("↩️ Alış İade", COLORS["error"]),
        StockMovementType.IADE_SATIS: ("↩️ Satış İade", COLORS["success"]),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header - özel butonlar gerektiği için manuel oluşturulacak
        header_layout = QHBoxLayout()

        self.header = PageHeader(
            title="Stok Hareketleri",
            icon="📦",
            show_search=True,
            show_refresh=True,
            search_placeholder="Stok kodu, belge no ile ara...",
            parent=self,
        )

        # Özel butonları ekle
        entry_btn = QPushButton("📥 Giriş Fişi")
        entry_btn.setProperty("class", "btn-add")
        entry_btn.setFixedHeight(36)
        entry_btn.clicked.connect(self.add_entry_clicked.emit)

        exit_btn = QPushButton("📤 Çıkış Fişi")
        exit_btn.setProperty("class", "btn-danger")
        exit_btn.setFixedHeight(36)
        exit_btn.clicked.connect(self.add_exit_clicked.emit)

        transfer_btn = QPushButton("🔄 Transfer")
        transfer_btn.setProperty("class", "btn-primary")
        transfer_btn.setFixedHeight(36)
        transfer_btn.clicked.connect(self.add_transfer_clicked.emit)

        # Header'a butonları ekle
        h_layout = self.header.header_layout()
        h_layout.addWidget(entry_btn)
        h_layout.addWidget(exit_btn)
        h_layout.addWidget(transfer_btn)

        layout.addWidget(self.header)

        # Filtreler
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(12)

        filter_layout.addWidget(QLabel("Tür:"))
        self.type_combo = QComboBox()
        self.type_combo.addItem("Tümü", None)
        self.type_combo.addItem("📥 Giriş", "giris")
        self.type_combo.addItem("📤 Çıkış", "cikis")
        self.type_combo.addItem("🔄 Transfer", "transfer")
        self.type_combo.addItem("🛒 Satın Alma", "satin_alma")
        self.type_combo.addItem("💰 Satış", "satis")
        self.type_combo.setMinimumWidth(130)
        self.type_combo.setFixedHeight(36)
        filter_layout.addWidget(self.type_combo)

        filter_layout.addWidget(QLabel("Tarih:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        filter_layout.addWidget(self.start_date)

        filter_layout.addWidget(QLabel("-"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        filter_layout.addWidget(self.end_date)

        filter_btn = QPushButton("🔍 Filtrele")
        filter_btn.setProperty("class", "btn-filter")
        filter_btn.clicked.connect(self.refresh_requested.emit)
        filter_layout.addWidget(filter_btn)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # İstatistik kartları
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.stat_cards = {}
        self.stat_cards["total"] = MiniStatCard("📊 Toplam", "0", "#6366f1")
        self.stat_cards["in"] = MiniStatCard("📥 Giriş", "₺0", "#10b981")
        self.stat_cards["out"] = MiniStatCard("📤 Çıkış", "₺0", "#ef4444")

        for card in self.stat_cards.values():
            stats_layout.addWidget(card)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Tablo
        columns = [
            ColumnConfig("date", "Tarih", width=140),
            ColumnConfig("document_no", "Belge No", width=120),
            ColumnConfig("type", "Tür", width=100),
            ColumnConfig("item_code", "Stok Kodu", width=100),
            ColumnConfig("item_name", "Stok Adı", width=200, stretch=True),
            ColumnConfig("quantity", "Miktar", width=90),
            ColumnConfig("unit", "Birim", width=60),
            ColumnConfig("unit_price", "Birim Fiyat", width=100),
            ColumnConfig("total", "Toplam", width=110),
            ColumnConfig("from_wh", "Kaynak", width=100),
            ColumnConfig("to_wh", "Hedef", width=100),
        ]

        self.table = EnhancedTableWidget(
            table_id="stock_movements",
            columns=columns,
            parent=self,
        )
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.table)

        # Alt bilgi
        footer_layout = QHBoxLayout()
        self.count_label = QLabel("Toplam: 0 hareket")
        footer_layout.addWidget(self.count_label)
        footer_layout.addStretch()
        self.total_label = QLabel("Giriş: ₺0 | Çıkış: ₺0")
        footer_layout.addWidget(self.total_label)
        layout.addLayout(footer_layout)

    def _connect_signals(self):
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        self.header.search_changed.connect(lambda: self.refresh_requested.emit())
        self.table.row_double_clicked.connect(self.view_clicked.emit)

    def load_data(self, movements: list):
        self.table.setRowCount(len(movements))
        visible_cols = self.table.get_visible_columns()

        total_in = Decimal(0)
        total_out = Decimal(0)

        for row, mov in enumerate(movements):
            self._populate_row(row, mov, visible_cols)

            # Toplamları hesapla (TL Dönüşümü ile)
            total = mov.total_price or Decimal(0)
            exchange_rate = mov.exchange_rate or Decimal(1)
            total_tl = total * exchange_rate

            if mov.movement_type in [
                StockMovementType.GIRIS,
                StockMovementType.SATIN_ALMA,
                StockMovementType.URETIM_GIRIS,
                StockMovementType.SAYIM_FAZLA,
                StockMovementType.IADE_SATIS,
            ]:
                total_in += total_tl
            else:
                total_out += total_tl

        # Kartları güncelle
        self.stat_cards["total"].update_value(str(len(movements)))
        self.stat_cards["in"].update_value(f"₺{total_in:,.2f}")
        self.stat_cards["out"].update_value(f"₺{total_out:,.2f}")

        self.count_label.setText(f"Toplam: {len(movements)} hareket")
        self.total_label.setText(f"Giriş: ₺{total_in:,.2f} | Çıkış: ₺{total_out:,.2f}")

    def _populate_row(self, row: int, mov, visible_cols: list):
        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "date":
                date_str = (
                    mov.movement_date.strftime("%d.%m.%Y %H:%M")
                    if mov.movement_date
                    else "-"
                )
                cell = QTableWidgetItem(date_str)
                cell.setData(Qt.ItemDataRole.UserRole, mov.id)
                self.table.setItem(row, col_idx, cell)

            elif col_key == "document_no":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(mov.document_no or "-")
                )

            elif col_key == "type":
                type_text, type_color = self.TYPE_NAMES.get(
                    mov.movement_type, ("?", "#ffffff")
                )
                cell = QTableWidgetItem(type_text)
                cell.setForeground(QColor(type_color))
                self.table.setItem(row, col_idx, cell)

            elif col_key == "item_code":
                # Modelden relationship ile gelen veriyi tercih et
                code = mov.item.code if mov.item else (mov.item_code or "-")
                cell = QTableWidgetItem(code)
                cell.setForeground(QColor("#818cf8"))
                self.table.setItem(row, col_idx, cell)

            elif col_key == "item_name":
                name = mov.item.name if mov.item else (mov.item_name or "-")
                self.table.setItem(row, col_idx, QTableWidgetItem(name))

            elif col_key == "quantity":
                qty = mov.quantity or Decimal(0)
                cell = QTableWidgetItem(f"{qty:,.2f}")
                cell.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.table.setItem(row, col_idx, cell)

            elif col_key == "unit":
                # Birim
                unit_text = mov.unit.code if mov.unit else "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(unit_text))

            elif col_key == "unit_price":
                price = mov.unit_price or Decimal(0)
                symbol = mov.currency.symbol if mov.currency else "₺"
                cell = QTableWidgetItem(f"{symbol}{price:,.2f}")
                cell.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.table.setItem(row, col_idx, cell)

            elif col_key == "total":
                total = mov.total_price or Decimal(0)
                symbol = mov.currency.symbol if mov.currency else "₺"
                cell = QTableWidgetItem(f"{symbol}{total:,.2f}")
                cell.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.table.setItem(row, col_idx, cell)

            elif col_key == "from_wh":
                # Kaynak Depo
                wh_code = mov.from_warehouse.code if mov.from_warehouse else "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(wh_code))

            elif col_key == "to_wh":
                # Hedef Depo
                wh_code = mov.to_warehouse.code if mov.to_warehouse else "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(wh_code))

        self.table.setRowHeight(row, 48)

    def get_filters(self) -> dict:
        return {
            "keyword": (
                self.header.search_input.text().strip()
                if self.header.search_input
                else ""
            ),
            "movement_type": self.type_combo.currentData(),
            "start_date": self.start_date.date().toPyDate(),
            "end_date": self.end_date.date().toPyDate(),
        }

    def _show_context_menu(self, position):
        row = self.table.rowAt(position.y())
        if row < 0:
            return

        mov_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        menu = QMenu(self)
        view_action = QAction("👁 Detay Görüntüle", self)
        view_action.triggered.connect(lambda: self.view_clicked.emit(mov_id))
        menu.addAction(view_action)

        menu.exec(self.table.viewport().mapToGlobal(position))
