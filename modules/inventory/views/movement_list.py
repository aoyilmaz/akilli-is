"""
Akıllı İş - Stok Hareketleri Listesi
"""

from decimal import Decimal
from datetime import date, timedelta
from PyQt6.QtWidgets import (
    QPushButton,
    QTableWidgetItem,
    QMenu,
    QDateEdit,
    QLabel,
    QHBoxLayout,
    QWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor, QAction
import qtawesome as qta

from config.icons import ICONS
from config.themes import get_theme
from database.models import StockMovementType

# BaseListPage ve bileşenler
from ui.components.base_list_page import BaseListPage
from ui.components.enhanced_table import ColumnConfig, NumericTableWidgetItem


class MovementListPage(BaseListPage):
    """Stok hareketleri listesi."""

    add_entry_clicked = pyqtSignal()
    add_exit_clicked = pyqtSignal()
    add_transfer_clicked = pyqtSignal()
    # view_clicked zaten BaseListPage'de var

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
        cols = [
            ColumnConfig("date", "Tarih", width=140, sortable=True),
            ColumnConfig("document_no", "Belge No", width=120, filterable=True),
            ColumnConfig("type", "Tür", width=100, filter_type="enum"),
            ColumnConfig("item_code", "Stok Kodu", width=100, filterable=True),
            ColumnConfig(
                "item_name", "Stok Adı", width=200, stretch=True, filterable=True
            ),
            ColumnConfig("quantity", "Miktar", width=90, filter_type="number"),
            ColumnConfig("unit", "Birim", width=60),
            ColumnConfig("unit_price", "Birim Fiyat", width=100, filter_type="number"),
            ColumnConfig("total", "Toplam", width=110, filter_type="number"),
            ColumnConfig("from_wh", "Kaynak", width=100, filterable=True),
            ColumnConfig("to_wh", "Hedef", width=100, filterable=True),
        ]

        super().__init__(
            title="Stok Hareketleri",
            icon=ICONS.INVENTORY,
            table_id="stock_movements",
            columns=cols,
            show_add=False,  # Kendi butonlarımızı ekleyeceğiz
            search_placeholder="Stok kodu, belge no ile ara...",
            parent=parent,
        )

        self._setup_extra_ui()

    def _setup_extra_ui(self):
        """Özel butonlar, tarih filtreleri ve footer istatistikleri"""

        # Header'a özel butonlar
        h = self.header.header_layout()

        # Tarih aralığı filtresi
        self._setup_date_filters(h)

        # Standart Add butonu yerine 3 farklı işlem butonu
        buttons = [
            ("Giriş Fişi", "btn-add", ICONS.ARROW_DOWN, self.add_entry_clicked),
            ("Çıkış Fişi", "btn-danger", ICONS.ARROW_UP, self.add_exit_clicked),
            ("Transfer", "btn-primary", ICONS.MOVEMENT, self.add_transfer_clicked),
        ]

        # Export butonundan önce ekleyelim (varsa)
        idx = h.count()
        if self.header.export_btn:
            idx = h.indexOf(self.header.export_btn)

        # Tersten ekleyelim ki sıralama doğru olsun (insertWidget index'i kaydırmazsak)
        # Ama burada basitçe sona eklesek de olur, PageHeader layout'u esnek.
        # Button container kullansak daha iyi olurdu ama PageHeader yapısı flat.

        # Mevcut yapıya uyalım:
        for txt, cls, icon, sig in buttons:
            btn = QPushButton(txt)
            btn.setIcon(qta.icon(icon, color="#ffffff"))
            btn.setProperty("class", cls)
            btn.setFixedHeight(36)
            btn.clicked.connect(sig.emit)
            # Layout'a ekle (export varsa ondan önce, yoksa sona)
            if idx != -1:
                h.insertWidget(idx, btn)
                idx += 1
            else:
                h.addWidget(btn)

        # Footer İstatistikleri
        # BaseListPage zaten total_records ekliyor. Biz ek istatistikleri ekleyelim.
        # total_records key'i "total_records"

        self.footer.add_stat("in", "Giriş", ICONS.ARROW_DOWN, "#10b981")
        self.footer.add_stat("out", "Çıkış", ICONS.ARROW_UP, "#ef4444")

        # Context Menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # Filtre seçenekleri
        self.table.set_filter_options("type", [n[0] for n in self.TYPE_NAMES.values()])

    def load_data(self, movements: list):
        """Verileri yükle"""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(movements))

        tin, tout = Decimal(0), Decimal(0)

        # Cache theme colors
        t = get_theme()
        default_color = QColor(t.text_primary)
        blue_color = QColor("#818cf8")

        vcols = (
            self.table.get_visible_columns()
        )  # Optimization? BaseListPage handles visibility internaly but we need keys
        # Actually our EnhancedTableWidget handles column mapping via setItem(row, col_idx...) if we iterate columns.
        # Let's iterate rows and use column keys.

        for r, mov in enumerate(movements):
            self._populate_row(r, mov, default_color, blue_color)

            # Hesaplamalar
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
        self.update_count(len(movements))

        # İstatistikleri güncelle
        self.update_stat_card("in", f"₺{tin:,.2f}")
        self.update_stat_card("out", f"₺{tout:,.2f}")

        # Filtreleri uygula
        self.table.apply_saved_filters()

    def _populate_row(self, r, mov, default_color, blue_color):

        # date
        ds = mov.movement_date.strftime("%d.%m.%Y %H:%M") if mov.movement_date else "-"
        # Sortable date -> UserRole
        # Display format string, data timestamp/sortable string
        # EnhancedTable handles standard Items. For date sorting, usually ISO string is better for data
        # but let's stick to existing logic or NumericTableWidgetItem logic?
        # EnhancedTable has generic sorter. Date string sorting dd.mm.yyyy is wrong.
        # Use simple Item but set Data UserRole if needed or DisplayRole.
        # Standard QTableWidgetItem sorts by text.
        # Let's use custom sort widget or setData(Qt.ItemDataRole.EditRole, timestamp).
        # Base implementation used UserRole for ID.

        it = QTableWidgetItem(ds)
        it.setData(Qt.ItemDataRole.UserRole, mov.id)  # ID sakla
        it.setForeground(default_color)
        self.table.setItem(r, 0, it)

        # document_no
        it = QTableWidgetItem(mov.document_no or "-")
        it.setForeground(default_color)
        self.table.setItem(r, 1, it)

        # type
        txt, color = self.TYPE_NAMES.get(mov.movement_type, ("?", "#ffffff"))
        it = QTableWidgetItem(txt)
        it.setForeground(QColor(color))
        self.table.setItem(r, 2, it)

        # item_code
        cd = mov.item.code if mov.item else (mov.item_code or "-")
        it = QTableWidgetItem(cd)
        it.setForeground(blue_color)
        self.table.setItem(r, 3, it)

        # item_name
        nm = mov.item.name if mov.item else (mov.item_name or "-")
        it = QTableWidgetItem(nm)
        it.setForeground(default_color)
        self.table.setItem(r, 4, it)

        # quantity
        qty = mov.quantity or 0
        it = NumericTableWidgetItem(qty, f"{qty:,.2f}")
        it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        it.setForeground(default_color)
        self.table.setItem(r, 5, it)

        # unit
        it = QTableWidgetItem(mov.unit.code if mov.unit else "-")
        it.setForeground(default_color)
        self.table.setItem(r, 6, it)

        # unit_price
        price = mov.unit_price
        sym = mov.currency.symbol if mov.currency else "₺"
        it = NumericTableWidgetItem(price, f"{sym}{price or 0:,.2f}")
        it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        it.setForeground(default_color)
        self.table.setItem(r, 7, it)

        # total
        total = mov.total_price
        it = NumericTableWidgetItem(total, f"{sym}{total or 0:,.2f}")
        it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        it.setForeground(default_color)
        self.table.setItem(r, 8, it)

        # from_wh
        wh = mov.from_warehouse
        txt = wh.code if wh else "-"
        it = QTableWidgetItem(txt)
        it.setForeground(default_color)
        self.table.setItem(r, 9, it)

        # to_wh
        wh = mov.to_warehouse
        txt = wh.code if wh else "-"
        it = QTableWidgetItem(txt)
        it.setForeground(default_color)
        self.table.setItem(r, 10, it)

    def get_filters(self) -> dict:
        """Filtre değerlerini döndür"""
        start = self.start_date.date().toPyDate() if hasattr(self, 'start_date') else None
        end = self.end_date.date().toPyDate() if hasattr(self, 'end_date') else None

        return {
            "keyword": self.header.get_search_text(),
            "start_date": start,
            "end_date": end,
        }

    def get_search_text(self) -> str:
        return self.header.get_search_text()

    def _show_context_menu(self, pos):
        """Sağ tık menüsü"""
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

    def _setup_date_filters(self, layout):
        """Tarih aralığı filtreleri oluştur"""
        from config.themes import get_theme

        t = get_theme()

        # Container widget
        date_container = QWidget()
        date_layout = QHBoxLayout(date_container)
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.setSpacing(8)

        # Başlangıç tarihi
        start_label = QLabel("Başlangıç:")
        start_label.setStyleSheet(f"color: {t.text_muted}; font-size: 12px;")
        date_layout.addWidget(start_label)

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("dd.MM.yyyy")
        self.start_date.setDate(QDate.currentDate().addDays(-30))  # Son 30 gün
        self.start_date.setFixedWidth(120)
        self.start_date.setFixedHeight(32)
        self.start_date.dateChanged.connect(self._on_date_filter_changed)
        date_layout.addWidget(self.start_date)

        # Bitiş tarihi
        end_label = QLabel("Bitiş:")
        end_label.setStyleSheet(f"color: {t.text_muted}; font-size: 12px;")
        date_layout.addWidget(end_label)

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("dd.MM.yyyy")
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setFixedWidth(120)
        self.end_date.setFixedHeight(32)
        self.end_date.dateChanged.connect(self._on_date_filter_changed)
        date_layout.addWidget(self.end_date)

        # Hızlı seçim butonu
        quick_btn = QPushButton("Bugün")
        quick_btn.setIcon(qta.icon(ICONS.CALENDAR, color="#cccccc"))
        quick_btn.setFixedHeight(32)
        quick_btn.setProperty("class", "btn-secondary")
        quick_btn.clicked.connect(self._set_today)
        date_layout.addWidget(quick_btn)

        # Header layout'a ekle (arama kutusundan sonra)
        layout.insertWidget(2, date_container)

    def _on_date_filter_changed(self):
        """Tarih değiştiğinde yenile"""
        self.refresh_requested.emit()

    def _set_today(self):
        """Bugünün tarihini ayarla"""
        today = QDate.currentDate()
        self.start_date.setDate(today)
        self.end_date.setDate(today)
        self.refresh_requested.emit()
