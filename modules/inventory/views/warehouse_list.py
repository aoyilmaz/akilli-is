"""
Akıllı İş - Depo Listesi Sayfası
"""

from PyQt6.QtWidgets import (
    QTableWidgetItem,
    QMenu,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QAction
import qtawesome as qta

from config.icons import ICONS
from config.themes import get_theme
from ui.components import (
    BaseListPage,
    ColumnConfig,
)


class WarehouseListPage(BaseListPage):
    """
    Depo listesi sayfası.
    BaseListPage kullanarak Excel tipi sütun filtreleme destekler.
    """

    # Ek sinyaller
    locations_clicked = pyqtSignal(int)

    TYPE_NAMES = {
        "general": "Genel",
        "raw": "Hammadde",
        "finished": "Mamül",
        "cold": "Soğuk",
        "bonded": "Antrepo",
    }

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("code", "Kod", width=100),
            ColumnConfig("name", "Depo Adı", width=200, stretch=True),
            ColumnConfig("type", "Tür", width=120, filter_type="enum"),
            ColumnConfig("city", "Şehir", width=120),
            ColumnConfig("manager", "Yetkili", width=150),
            ColumnConfig("phone", "Telefon", width=120),
            ColumnConfig("locations", "Lokasyon", width=80, filter_type="number"),
            ColumnConfig("is_default", "Varsayılan", width=90, filter_type="enum"),
            ColumnConfig("status", "Durum", width=90, filter_type="enum"),
        ]

        super().__init__(
            title="Depolar",
            icon=ICONS.WAREHOUSE,
            table_id="warehouses",
            columns=columns,
            show_stats=False,
            show_search=True,
            show_add=True,
            add_text="Yeni Depo",
            search_placeholder="Depo kodu veya adı ile ara...",
            count_label_text="depo",
            parent=parent,
        )

        self.warehouses = []

        # Context menu için
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

    def load_data(self, warehouses: list):
        """Verileri yükle"""
        self.warehouses = warehouses
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(warehouses))
        vcols = self.table.get_visible_columns()

        for r, wh in enumerate(warehouses):
            self._populate_row(r, wh, vcols)

        self.table.setSortingEnabled(True)
        self.update_count(len(warehouses))

    def _populate_row(self, r, wh, vcols):
        """Tek satırı doldur"""
        try:
            t = get_theme()
            default_color = QColor(t.text_primary)

            for ci, key in enumerate(vcols):
                if key == "code":
                    it = QTableWidgetItem(str(wh.code or ""))
                    it.setData(Qt.ItemDataRole.UserRole, wh.id)
                    it.setForeground(QColor("#818cf8"))
                    self.table.setItem(r, ci, it)
                elif key == "name":
                    it = QTableWidgetItem(str(wh.name or ""))
                    it.setForeground(default_color)
                    self.table.setItem(r, ci, it)
                elif key == "type":
                    t_name = self.TYPE_NAMES.get(wh.warehouse_type, "Genel")
                    it = QTableWidgetItem(t_name)
                    it.setForeground(default_color)
                    self.table.setItem(r, ci, it)
                elif key == "city":
                    it = QTableWidgetItem(str(wh.city or "-"))
                    it.setForeground(default_color)
                    self.table.setItem(r, ci, it)
                elif key == "manager":
                    it = QTableWidgetItem(str(wh.manager_name or "-"))
                    it.setForeground(default_color)
                    self.table.setItem(r, ci, it)
                elif key == "phone":
                    it = QTableWidgetItem(str(wh.phone or "-"))
                    it.setForeground(default_color)
                    self.table.setItem(r, ci, it)
                elif key == "locations":
                    locs = wh.locations if wh.locations else []
                    it = QTableWidgetItem(str(len(locs)))
                    it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    it.setForeground(default_color)
                    self.table.setItem(r, ci, it)
                elif key == "is_default":
                    it = QTableWidgetItem("Varsayılan" if wh.is_default else "")
                    it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if wh.is_default:
                        it.setForeground(QColor("#10b981"))
                    else:
                        it.setForeground(default_color)
                    self.table.setItem(r, ci, it)
                elif key == "status":
                    act, it = wh.is_active, QTableWidgetItem()
                    if act:
                        it.setText("Aktif")
                        it.setIcon(qta.icon(ICONS.CHECK, color=t.success))
                        it.setForeground(QColor(t.success))
                    else:
                        it.setText("Pasif")
                        it.setIcon(qta.icon(ICONS.CLOSE, color=t.text_muted))
                        it.setForeground(QColor(t.text_muted))
                    self.table.setItem(r, ci, it)
        except Exception as e:
            print(f"Error populating row {r}: {e}")

    def _show_context_menu(self, pos):
        """Context menu göster"""
        row = self.table.rowAt(pos.y())
        if row < 0:
            return

        wh_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)

        ed = QAction("Düzenle", self)
        ed.setIcon(qta.icon(ICONS.EDIT, color="#3498db"))
        ed.triggered.connect(lambda: self.edit_clicked.emit(wh_id))
        menu.addAction(ed)

        lo = QAction("Lokasyonlar", self)
        lo.setIcon(qta.icon(ICONS.TAG, color="#8b5cf6"))
        lo.triggered.connect(lambda: self.locations_clicked.emit(wh_id))
        menu.addAction(lo)

        menu.addSeparator()

        de = QAction("Sil", self)
        de.setIcon(qta.icon(ICONS.DELETE, color="#ef4444"))
        de.triggered.connect(lambda: self._confirm_delete(wh_id))
        menu.addAction(de)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _confirm_delete(self, wh_id: int):
        """Silme onayı"""
        if self.confirm_delete("depo"):
            self.delete_clicked.emit(wh_id)
