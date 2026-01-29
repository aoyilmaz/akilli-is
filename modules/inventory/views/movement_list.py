"""
Akıllı İş - Stok Hareketleri Listesi
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
import qtawesome as qta

from config.icons import ICONS
from database.models import StockMovementType
from ui.components import (
    PageHeader,
    EnhancedTableWidget,
    ColumnConfig,
    MiniStatCard,
    ScrollableCardContainer,
)


class MovementListPage(QWidget):
    """Stok hareketleri listesi."""

    add_entry_clicked, add_exit_clicked = pyqtSignal(), pyqtSignal()
    add_transfer_clicked, view_clicked = pyqtSignal(), pyqtSignal(int)
    refresh_requested = pyqtSignal()

    TYPE_NAMES = {
        StockMovementType.GIRIS: ("Giriş", "#10b981"),
        StockMovementType.CIKIS: ("Çıkış", "#ef4444"),
        StockMovementType.SATIN_ALMA: ("Satın Alma", "#10b981"),
        StockMovementType.SATIS: ("Satış", "#ef4444"),
        StockMovementType.URETIM_GIRIS: ("Üretim Giriş", "#10b981"),
        StockMovementType.URETIM_CIKIS: ("Üretim Çıkış", "#ef4444"),
        StockMovementType.TRANSFER: ("Transfer", "#3b82f6"),
        StockMovementType.SAYIM_FAZLA: ("Sayım Fazla", "#10b981"),
        StockMovementType.SAYIM_EKSIK: ("Sayım Eksik", "#ef4444"),
        StockMovementType.FIRE: ("Fire", "#f59e0b"),
        StockMovementType.IADE_ALIS: ("Alış İade", "#ef4444"),
        StockMovementType.IADE_SATIS: ("Satış İade", "#10b981"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        self.header = PageHeader(
            title="Stok Hareketleri",
            icon=ICONS.INVENTORY,
            show_search=True,
            show_refresh=True,
            search_placeholder="Stok kodu, belge no ile ara...",
            parent=self,
        )
        h = self.header.header_layout()
        for txt, cls, icon, sig in [
            ("Giriş Fişi", "btn-add", ICONS.ARROW_DOWN, self.add_entry_clicked),
            ("Çıkış Fişi", "btn-danger", ICONS.ARROW_UP, self.add_exit_clicked),
            ("Transfer", "btn-primary", ICONS.MOVEMENT, self.add_transfer_clicked),
        ]:
            btn = QPushButton(txt)
            btn.setIcon(qta.icon(icon, color="#ffffff"))
            btn.setProperty("class", cls)
            btn.setFixedHeight(36)
            btn.clicked.connect(sig.emit)
            h.addWidget(btn)
        layout.addWidget(self.header)

        fl = QHBoxLayout()
        fl.setSpacing(12)
        fl.addWidget(QLabel("Tür:"))
        self.type_combo = QComboBox()
        self.type_combo.addItem("Tümü", None)
        for t in ["Giriş", "Çıkış", "Transfer", "Satın Alma", "Satış"]:
            self.type_combo.addItem(t, t.lower().replace(" ", "_"))
        self.type_combo.setMinimumWidth(130)
        self.type_combo.setFixedHeight(36)
        fl.addWidget(self.type_combo)
        fl.addWidget(QLabel("Tarih:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        fl.addWidget(self.start_date)
        fl.addWidget(QLabel("-"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        fl.addWidget(self.end_date)
        fb = QPushButton("Filtrele")
        fb.setIcon(qta.icon(ICONS.FILTER, color="#ffffff"))
        fb.setProperty("class", "btn-filter")
        fb.clicked.connect(self.refresh_requested.emit)
        fl.addWidget(fb)
        fl.addStretch()
        layout.addLayout(fl)

        stats_container = ScrollableCardContainer()
        self.stat_cards = {
            "total": MiniStatCard("Toplam", "0", "info", icon=ICONS.INVENTORY),
            "in": MiniStatCard("Giriş", "₺0", "success", icon=ICONS.ARROW_DOWN),
            "out": MiniStatCard("Çıkış", "₺0", "error", icon=ICONS.ARROW_UP),
        }
        for card in self.stat_cards.values():
            stats_container.add_card(card)
        stats_container.add_stretch()
        layout.addWidget(stats_container)

        cols = [
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
            table_id="stock_movements", columns=cols, parent=self
        )
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.table)

        st = QHBoxLayout()
        self.count_label = QLabel("Toplam: 0 hareket")
        st.addWidget(self.count_label)
        st.addStretch()
        self.total_label = QLabel("Giriş: ₺0 | Çıkış: ₺0")
        st.addWidget(self.total_label)
        layout.addLayout(st)

    def _connect_signals(self):
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        self.header.search_changed.connect(lambda: self.refresh_requested.emit())
        self.table.row_double_clicked.connect(self.view_clicked.emit)

    def load_data(self, movements: list):
        self.table.setRowCount(len(movements))
        vcols = self.table.get_visible_columns()
        tin, tout = Decimal(0), Decimal(0)
        for r, mov in enumerate(movements):
            self._populate_row(r, mov, vcols)
            tot = mov.total_price or Decimal(0)
            ex = mov.exchange_rate or Decimal(1)
            ttl = tot * ex
            if mov.movement_type in [
                StockMovementType.GIRIS,
                StockMovementType.SATIN_ALMA,
                StockMovementType.URETIM_GIRIS,
                StockMovementType.SAYIM_FAZLA,
                StockMovementType.IADE_SATIS,
            ]:
                tin += ttl
            else:
                tout += ttl
        self.stat_cards["total"].update_value(str(len(movements)))
        self.stat_cards["in"].update_value(f"₺{tin:,.2f}")
        self.stat_cards["out"].update_value(f"₺{tout:,.2f}")
        self.count_label.setText(f"Toplam: {len(movements)} hareket")
        self.total_label.setText(f"Giriş: ₺{tin:,.2f} | Çıkış: ₺{tout:,.2f}")

    def _populate_row(self, r, mov, vcols):
        for ci, key in enumerate(vcols):
            if key == "date":
                ds = (
                    mov.movement_date.strftime("%d.%m.%Y %H:%M")
                    if mov.movement_date
                    else "-"
                )
                it = QTableWidgetItem(ds)
                it.setData(Qt.ItemDataRole.UserRole, mov.id)
                self.table.setItem(r, ci, it)
            elif key == "document_no":
                self.table.setItem(r, ci, QTableWidgetItem(mov.document_no or "-"))
            elif key == "type":
                txt, color = self.TYPE_NAMES.get(mov.movement_type, ("?", "#ffffff"))
                it = QTableWidgetItem(txt)
                it.setForeground(QColor(color))
                self.table.setItem(r, ci, it)
            elif key == "item_code":
                cd = mov.item.code if mov.item else (mov.item_code or "-")
                it = QTableWidgetItem(cd)
                it.setForeground(QColor("#818cf8"))
                self.table.setItem(r, ci, it)
            elif key == "item_name":
                self.table.setItem(
                    r,
                    ci,
                    QTableWidgetItem(
                        mov.item.name if mov.item else (mov.item_name or "-")
                    ),
                )
            elif key == "quantity":
                it = QTableWidgetItem(f"{mov.quantity or 0:,.2f}")
                it.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.table.setItem(r, ci, it)
            elif key == "unit":
                self.table.setItem(
                    r, ci, QTableWidgetItem(mov.unit.code if mov.unit else "-")
                )
            elif key in ["unit_price", "total"]:
                v = mov.unit_price if key == "unit_price" else mov.total_price
                sym = mov.currency.symbol if mov.currency else "₺"
                it = QTableWidgetItem(f"{sym}{v or 0:,.2f}")
                it.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.table.setItem(r, ci, it)
            elif key in ["from_wh", "to_wh"]:
                self.table.setItem(
                    r,
                    ci,
                    QTableWidgetItem(
                        (
                            mov.from_warehouse if key == "from_wh" else mov.to_warehouse
                        ).code
                        if (
                            mov.from_warehouse if key == "from_wh" else mov.to_warehouse
                        )
                        else "-"
                    ),
                )

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

    def _show_context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0:
            return
        it = self.table.item(row, 0)
        if not it:
            return
        mid = it.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        vi = QAction("Detay Görüntüle", self)
        vi.setIcon(qta.icon(ICONS.VIEW, color="#cccccc"))
        vi.triggered.connect(lambda: self.view_clicked.emit(mid))
        menu.addAction(vi)
        menu.exec(self.table.viewport().mapToGlobal(pos))
