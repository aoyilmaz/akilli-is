"""
Akıllı İş - Tedarikçi Liste Sayfası
Yeni bileşen mimarisi kullanılarak yeniden yapılandırıldı.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QTableWidgetItem,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from config.icons import ICONS
from ui.components import (
    BaseListPage,
    ColumnConfig,
    create_view_button,
    create_edit_button,
    create_delete_button,
)


class SupplierListPage(BaseListPage):
    """Tedarikçi listesi sayfası."""

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("code", "Kod", width=100),
            ColumnConfig("name", "Tedarikçi Adı", width=200, stretch=True),
            ColumnConfig("phone", "Telefon", width=130),
            ColumnConfig("email", "E-posta", width=180),
            ColumnConfig("city", "Şehir", width=100),
            ColumnConfig("payment_term", "Vade (Gün)", width=80),
            ColumnConfig("rating", "Puan", width=80),
            ColumnConfig(
                "actions",
                "İşlemler",
                width=120,
                resizable=False,
                movable=False,
                hideable=False,
            ),
        ]

        super().__init__(
            title="Tedarikçiler",
            icon=ICONS.BUILDING,
            table_id="suppliers",
            columns=columns,
            show_stats=True,
            show_search=True,
            show_refresh=True,
            show_add=True,
            add_text="Yeni Tedarikçi",
            search_placeholder="Ara... (kod, ad, vergi no)",
            parent=parent,
        )

        self.suppliers = []
        self._setup_stat_cards()

    def _setup_stat_cards(self):
        self.add_stat_card("total", "Toplam", "0", "#6366f1", "📊")
        self.add_stat_card("active", "Aktif", "0", "#10b981", "✅")
        self.add_stat_card("with_orders", "Siparişli", "0", "#f59e0b", "📦")
        self.add_stat_card("credit", "Toplam Limit", "₺0", "#3b82f6", "💳")

    def load_data(self, suppliers: list):
        self.suppliers = suppliers
        self.clear_table()

        total = len(suppliers)
        active = 0
        total_credit = 0

        for sup in suppliers:
            if sup.get("is_active", True):
                active += 1
            total_credit += float(sup.get("credit_limit", 0) or 0)

        self.update_stat_card("total", str(total))
        self.update_stat_card("active", str(active))
        self.update_stat_card("credit", f"₺{total_credit:,.0f}")

        self.table.setRowCount(len(suppliers))
        for row, sup in enumerate(suppliers):
            self._populate_row(row, sup)

    def _populate_row(self, row: int, sup: dict):
        visible_cols = self.table.get_visible_columns()

        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "code":
                item = QTableWidgetItem(sup.get("code", ""))
                item.setData(Qt.ItemDataRole.UserRole, sup.get("id"))
                self.table.setItem(row, col_idx, item)

            elif col_key == "name":
                self.table.setItem(row, col_idx, QTableWidgetItem(sup.get("name", "")))

            elif col_key == "phone":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(sup.get("phone", "") or "-")
                )

            elif col_key == "email":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(sup.get("email", "") or "-")
                )

            elif col_key == "city":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(sup.get("city", "") or "-")
                )

            elif col_key == "payment_term":
                vade = sup.get("payment_term_days", 0) or 0
                self.table.setItem(row, col_idx, QTableWidgetItem(str(vade)))

            elif col_key == "rating":
                rating = sup.get("rating", 0) or 0
                stars = "⭐" * rating if rating > 0 else "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(stars))

            elif col_key == "actions":
                self._add_action_buttons(row, col_idx, sup.get("id"))

        self.table.setRowHeight(row, 52)

    def _add_action_buttons(self, row: int, col: int, supplier_id: int):
        btn_widget = QWidget()
        btn_widget.setProperty("class", "action-button-group")
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setContentsMargins(4, 4, 4, 4)
        btn_layout.setSpacing(4)

        view_btn = create_view_button()
        view_btn.clicked.connect(
            lambda checked, sid=supplier_id: self.view_clicked.emit(sid)
        )
        btn_layout.addWidget(view_btn)

        edit_btn = create_edit_button()
        edit_btn.clicked.connect(
            lambda checked, sid=supplier_id: self.edit_clicked.emit(sid)
        )
        btn_layout.addWidget(edit_btn)

        del_btn = create_delete_button()
        del_btn.clicked.connect(
            lambda checked, sid=supplier_id: self._confirm_delete(sid)
        )
        btn_layout.addWidget(del_btn)

        self.table.setCellWidget(row, col, btn_widget)

    def _confirm_delete(self, supplier_id: int):
        if self.confirm_delete("tedarikçi"):
            self.delete_clicked.emit(supplier_id)
