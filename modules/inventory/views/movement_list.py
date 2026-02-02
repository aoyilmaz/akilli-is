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
    QMenu,
    QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QAction
import qtawesome as qta

from config.icons import ICONS
from config.themes import get_theme
from database.models import StockMovementType
from ui.components import (
    PageHeader,
    EnhancedTableWidget,
    ColumnConfig,
    MiniStatCard,
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
        self._total_count = 0
        self._setup_ui()
        self._connect_signals()

        # Otomatik yenileme
        self._auto_refresh_timer = QTimer(self)
        self._auto_refresh_timer.timeout.connect(lambda: self.refresh_requested.emit())
        self._auto_refresh_timer.start(30000)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        self.header = PageHeader(
            title="Stok Hareketleri",
            icon=ICONS.INVENTORY,
            show_search=True,
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

        # Tablo
        cols = [
            ColumnConfig("date", "Tarih", width=140),
            ColumnConfig("document_no", "Belge No", width=120),
            ColumnConfig("type", "Tür", width=100, filter_type="enum"),
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
        self.table.set_standard_row_height(48)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self.table)

        # Footer
        self._setup_footer(layout)

    def _setup_footer(self, layout: QVBoxLayout):
        """Footer - kayıt sayısı ve istatistikler"""
        footer = QFrame()
        footer.setProperty("class", "table-footer")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(0, 8, 0, 0)
        footer_layout.setSpacing(16)

        # Sol: Kayıt sayısı
        self.count_label = QLabel("Toplam: 0 hareket")
        self.count_label.setProperty("class", "footer-count")
        footer_layout.addWidget(self.count_label)

        # İstatistik kartları (horizontal)
        self.stat_cards = {
            "total": MiniStatCard(
                "Toplam", "0", "info", orientation="horizontal", icon=ICONS.INVENTORY
            ),
            "in": MiniStatCard(
                "Giriş", "₺0", "success", orientation="horizontal", icon=ICONS.ARROW_DOWN
            ),
            "out": MiniStatCard(
                "Çıkış", "₺0", "error", orientation="horizontal", icon=ICONS.ARROW_UP
            ),
        }
        for card in self.stat_cards.values():
            footer_layout.addWidget(card)

        footer_layout.addStretch()

        # Sağ: Otomatik yenileme göstergesi
        refresh_indicator = QLabel("⟳")
        refresh_indicator.setProperty("class", "refresh-indicator")
        refresh_indicator.setToolTip("Otomatik yenileme: 30s")
        footer_layout.addWidget(refresh_indicator)

        layout.addWidget(footer)

    def _connect_signals(self):
        self.header.search_changed.connect(lambda: self.refresh_requested.emit())
        self.table.row_double_clicked.connect(self.view_clicked.emit)
        self.table.filter_changed.connect(self._update_visible_count)

    def load_data(self, movements: list):
        self.table.setSortingEnabled(False)
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
        self.table.setSortingEnabled(True)
        self.stat_cards["total"].update_value(str(len(movements)))
        self.stat_cards["in"].update_value(f"₺{tin:,.2f}")
        self.stat_cards["out"].update_value(f"₺{tout:,.2f}")
        self._total_count = len(movements)
        self.count_label.setText(f"Toplam: {self._total_count} hareket")

    def _update_visible_count(self, filters: dict = None):
        """Görünen satır sayısını güncelle"""
        visible_count = sum(
            1 for row in range(self.table.rowCount())
            if not self.table.isRowHidden(row)
        )
        if visible_count == self._total_count:
            self.count_label.setText(f"Toplam: {self._total_count} hareket")
        else:
            self.count_label.setText(
                f"Gösterilen: {visible_count} / {self._total_count} hareket"
            )

    def _populate_row(self, r, mov, vcols):
        t = get_theme()
        default_color = QColor(t.text_primary)

        for ci, key in enumerate(vcols):
            if key == "date":
                ds = (
                    mov.movement_date.strftime("%d.%m.%Y %H:%M")
                    if mov.movement_date
                    else "-"
                )
                it = QTableWidgetItem(ds)
                it.setData(Qt.ItemDataRole.UserRole, mov.id)
                it.setForeground(default_color)
                self.table.setItem(r, ci, it)
            elif key == "document_no":
                it = QTableWidgetItem(mov.document_no or "-")
                it.setForeground(default_color)
                self.table.setItem(r, ci, it)
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
                nm = mov.item.name if mov.item else (mov.item_name or "-")
                it = QTableWidgetItem(nm)
                it.setForeground(default_color)
                self.table.setItem(r, ci, it)
            elif key == "quantity":
                it = QTableWidgetItem(f"{mov.quantity or 0:,.2f}")
                it.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                it.setForeground(default_color)
                self.table.setItem(r, ci, it)
            elif key == "unit":
                it = QTableWidgetItem(mov.unit.code if mov.unit else "-")
                it.setForeground(default_color)
                self.table.setItem(r, ci, it)
            elif key in ["unit_price", "total"]:
                v = mov.unit_price if key == "unit_price" else mov.total_price
                sym = mov.currency.symbol if mov.currency else "₺"
                it = QTableWidgetItem(f"{sym}{v or 0:,.2f}")
                it.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                it.setForeground(default_color)
                self.table.setItem(r, ci, it)
            elif key in ["from_wh", "to_wh"]:
                wh = mov.from_warehouse if key == "from_wh" else mov.to_warehouse
                txt = wh.code if wh else "-"
                it = QTableWidgetItem(txt)
                it.setForeground(default_color)
                self.table.setItem(r, ci, it)

    def get_filters(self) -> dict:
        return {"keyword": self.header.get_search_text()}

    def get_search_text(self) -> str:
        return self.header.get_search_text()

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

    def showEvent(self, event):
        super().showEvent(event)
        self._auto_refresh_timer.start(30000)

    def hideEvent(self, event):
        super().hideEvent(event)
        self._auto_refresh_timer.stop()
