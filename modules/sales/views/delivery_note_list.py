"""
Akıllı İş - Teslimat İrsaliyeleri Liste Sayfası
Yeni bileşen mimarisi kullanılarak yeniden yapılandırıldı.
"""

from datetime import date
from PyQt6.QtWidgets import (
    QTableWidgetItem,
)
from PyQt6.QtCore import Qt, pyqtSignal

from config.icons import ICONS
from ui.components import (
    BaseListPage,
    ColumnConfig,
)


class DeliveryNoteListPage(BaseListPage):
    """
    Teslimat irsaliyeleri listesi sayfası.
    BaseListPage kullanarak Excel tipi sütun filtreleme destekler.
    """

    # Ek sinyaller
    ship_clicked = pyqtSignal(int)
    complete_clicked = pyqtSignal(int)
    cancel_clicked = pyqtSignal(int)
    create_invoice_clicked = pyqtSignal(int)

    STATUS_LABELS = {
        "draft": ("Taslak", "#64748b"),
        "shipped": ("Sevk Edildi", "#f59e0b"),
        "delivered": ("Teslim Edildi", "#10b981"),
        "cancelled": ("İptal", "#475569"),
    }

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("note_no", "İrsaliye No", width=120),
            ColumnConfig("date", "Tarih", width=100, filter_type="date"),
            ColumnConfig("customer", "Müşteri", width=200, stretch=True),
            ColumnConfig("order_no", "Sipariş No", width=120),
            ColumnConfig("items", "Kalem", width=60, filter_type="number"),
            ColumnConfig("ship_date", "Sevk Tarihi", width=100, filter_type="date"),
            ColumnConfig("status", "Durum", width=130, filter_type="enum"),
            ColumnConfig(
                "actions",
                "İşlemler",
                width=200,
                resizable=False,
                movable=False,
                hideable=False,
                filterable=False,
            ),
        ]

        super().__init__(
            title="Teslimat İrsaliyeleri",
            icon=ICONS.TRUCK,
            table_id="delivery_notes",
            columns=columns,
            show_stats=True,
            show_search=True,
            show_add=True,
            add_text="Yeni İrsaliye",
            search_placeholder="Ara... (irsaliye no, müşteri)",
            parent=parent,
        )

        self.notes = []
        self._setup_stat_cards()

    def _setup_stat_cards(self):
        """İstatistik kartlarını oluştur"""
        self.add_stat_card("total", "Toplam", "0", "info", ICONS.INVOICE)
        self.add_stat_card("draft", "Taslak", "0", "info", ICONS.TIME)
        self.add_stat_card("shipped", "Sevk", "0", "warning", ICONS.TRUCK)
        self.add_stat_card("delivered", "Teslim", "0", "success", ICONS.CHECK)

    def load_data(self, notes: list):
        """Verileri yükle"""
        self.notes = notes
        self._display_data(notes)
        self._update_stats()

    def _display_data(self, notes: list):
        """Tabloya verileri yükle"""
        self.table.setRowCount(len(notes))
        visible_cols = self.table.get_visible_columns()

        for row, note in enumerate(notes):
            self._populate_row(row, note, visible_cols)

    def _populate_row(self, row: int, note: dict, visible_cols: list):
        """Tek satırı doldur"""
        note_id = note.get("id")

        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "note_no":
                item = QTableWidgetItem(note.get("note_no", ""))
                item.setData(Qt.ItemDataRole.UserRole, note_id)
                self.table.setItem(row, col_idx, item)

            elif col_key == "date":
                dt = self._format_date(note.get("note_date"))
                self.table.setItem(row, col_idx, QTableWidgetItem(dt))

            elif col_key == "customer":
                name = note.get("customer_name", "") or "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(name))

            elif col_key == "order_no":
                no = note.get("order_no", "") or "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(no))

            elif col_key == "items":
                item_count = str(note.get("total_items", 0))
                self.table.setItem(row, col_idx, QTableWidgetItem(item_count))

            elif col_key == "ship_date":
                dt = self._format_date(note.get("ship_date"))
                self.table.setItem(row, col_idx, QTableWidgetItem(dt))

            elif col_key == "status":
                status = note.get("status", "draft")
                label, _ = self.STATUS_LABELS.get(status, ("Taslak", "#64748b"))
                self.table.setItem(row, col_idx, QTableWidgetItem(label))

            elif col_key == "actions":
                self._add_action_buttons(row, col_idx, note)

    def _format_date(self, dt) -> str:
        """Tarihi formatla"""
        if dt:
            if isinstance(dt, date):
                return dt.strftime("%d.%m.%Y")
            return str(dt)
        return "-"

    def _add_action_buttons(self, row: int, col: int, note: dict):
        """İşlem butonlarını ekle"""
        note_id = note.get("id")
        status = note.get("status", "draft")

        actions = ["view"]
        callbacks = {"view": lambda nid=note_id: self.view_clicked.emit(nid)}

        if status == "draft":
            actions.append("edit")
            callbacks["edit"] = lambda nid=note_id: self.edit_clicked.emit(nid)

        widget = self.table.create_action_widget(note_id, actions, callbacks)
        layout = widget.layout()

        from ui.components.action_buttons import create_custom_button

        if status == "draft":
            ship_btn = create_custom_button(widget, ICONS.TRUCK, "Sevk Et", "warning")
            ship_btn.clicked.connect(lambda nid=note_id: self.ship_clicked.emit(nid))
            layout.insertWidget(layout.count() - 1, ship_btn)

        if status == "shipped":
            complete_btn = create_custom_button(
                widget, ICONS.CHECK, "Teslim Et", "success"
            )
            complete_btn.clicked.connect(
                lambda nid=note_id: self.complete_clicked.emit(nid)
            )
            layout.insertWidget(layout.count() - 1, complete_btn)

        if status == "delivered":
            invoice_btn = create_custom_button(
                widget, ICONS.INVOICE, "Fatura Oluştur", "info"
            )
            invoice_btn.clicked.connect(
                lambda nid=note_id: self.create_invoice_clicked.emit(nid)
            )
            layout.insertWidget(layout.count() - 1, invoice_btn)

        if status in ["draft", "shipped"]:
            cancel_btn = create_custom_button(widget, ICONS.CLOSE, "İptal Et", "error")
            cancel_btn.clicked.connect(
                lambda nid=note_id: self.cancel_clicked.emit(nid)
            )
            layout.insertWidget(layout.count() - 1, cancel_btn)

        if status == "draft":
            del_btn = create_custom_button(widget, ICONS.DELETE, "Sil", "error")
            del_btn.clicked.connect(lambda nid=note_id: self._confirm_delete(nid))
            layout.insertWidget(layout.count() - 1, del_btn)

        self.table.setCellWidget(row, col, widget)

    def _update_stats(self):
        """İstatistikleri güncelle"""
        total = len(self.notes)
        draft = sum(1 for n in self.notes if n.get("status") == "draft")
        shipped = sum(1 for n in self.notes if n.get("status") == "shipped")
        delivered = sum(1 for n in self.notes if n.get("status") == "delivered")

        self.update_stat_card("total", str(total))
        self.update_stat_card("draft", str(draft))
        self.update_stat_card("shipped", str(shipped))
        self.update_stat_card("delivered", str(delivered))

    def _confirm_delete(self, note_id: int):
        """Silme onayı"""
        if self.confirm_delete("irsaliye"):
            self.delete_clicked.emit(note_id)
