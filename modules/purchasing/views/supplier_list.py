"""
Akıllı İş - Tedarikçi Liste Sayfası
Yeni bileşen mimarisi kullanılarak yeniden yapılandırıldı.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QTableWidgetItem,
    QPushButton,
)
from PyQt6.QtCore import Qt

try:
    import qtawesome as qta
except ImportError:
    qta = None

from modules.purchasing.views.vendor_rating_dialog import VendorRatingDialog
from config.icons import ICONS
from ui.components import (
    BaseListPage,
    ColumnConfig,
)


class SupplierListPage(BaseListPage):
    """Tedarikçi listesi sayfası."""

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("code", "Kod", width=100),
            ColumnConfig("name", "Tedarikçi Adı", width=200, stretch=True),
            ColumnConfig("tax_number", "Vergi No", width=120, visible=False),
            ColumnConfig("tax_office", "Vergi Dairesi", width=120, visible=False),
            ColumnConfig("phone", "Telefon", width=130),
            ColumnConfig("mobile", "Mobil", width=130, visible=False),
            ColumnConfig("email", "E-posta", width=180),
            ColumnConfig("contact_person", "Yetkili", width=150, visible=False),
            ColumnConfig("city", "Şehir", width=100),
            ColumnConfig("district", "İlçe", width=100, visible=False),
            ColumnConfig("address", "Adres", width=250, visible=False),
            ColumnConfig("website", "Web Sitesi", width=150, visible=False),
            ColumnConfig("payment_term", "Vade (Gün)", width=80),
            ColumnConfig("currency", "Döviz", width=60, visible=False),
            ColumnConfig("credit_limit", "Limit", width=100, visible=False),
            ColumnConfig("rating", "Puan", width=80),
            ColumnConfig("notes", "Notlar", width=200, visible=False),
            ColumnConfig("created_at", "Kayıt Tarihi", width=140, visible=False),
            ColumnConfig("updated_at", "Güncelleme", width=140, visible=False),
            ColumnConfig(
                "actions",
                "İşlemler",
                width=140,
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
            show_add=True,
            add_text="Yeni Tedarikçi",
            search_placeholder="Ara... (kod, ad, vergi no)",
            parent=parent,
        )

        self.suppliers = []
        self._setup_stat_cards()

    def _setup_stat_cards(self):
        self.add_stat_card("total", "Toplam", "0", "info", ICONS.BUILDING)
        self.add_stat_card("active", "Aktif", "0", "success", ICONS.CHECK)
        self.add_stat_card("with_orders", "Siparişli", "0", "warning", ICONS.CART)
        self.add_stat_card("credit", "Toplam Limit", "₺0", "info", ICONS.MONEY)

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
        visible_cols = self.table.get_visible_columns()
        for row, sup in enumerate(suppliers):
            self._populate_row(row, sup, visible_cols)

    def _populate_row(self, row: int, sup: dict, visible_cols: list):
        sup_id = sup.get("id")

        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "code":
                item = QTableWidgetItem(sup.get("code", ""))
                item.setData(Qt.ItemDataRole.UserRole, sup_id)
                self.table.setItem(row, col_idx, item)

            elif col_key == "name":
                self.table.setItem(row, col_idx, QTableWidgetItem(sup.get("name", "")))

            elif col_key == "phone":
                val = sup.get("phone", "") or "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(val))

            elif col_key == "email":
                val = sup.get("email", "") or "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(val))

            elif col_key == "city":
                val = sup.get("city", "") or "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(val))

            elif col_key == "payment_term":
                vade = sup.get("payment_term_days", 0) or 0
                self.table.setItem(row, col_idx, QTableWidgetItem(str(vade)))

            elif col_key == "rating":
                rating_val = sup.get("rating", 0) or 0
                # 0-100 arası puanı 5 yıldıza çevir
                num_stars = (
                    max(1, min(5, round(rating_val / 20))) if rating_val > 0 else 0
                )
                stars = "⭐" * num_stars if num_stars > 0 else "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(stars))

            elif col_key == "actions":
                callbacks = {
                    "view": lambda rid=sup_id: self.view_clicked.emit(rid),
                    "edit": lambda rid=sup_id: self.edit_clicked.emit(rid),
                    "delete": lambda rid=sup_id: self._confirm_delete(rid),
                }

                # GRUPLAMA
                widget = QWidget()
                layout = QHBoxLayout(widget)
                layout.setContentsMargins(4, 2, 4, 2)
                layout.setSpacing(4)

                from ui.components.action_buttons import (
                    create_view_button,
                    create_edit_button,
                    create_delete_button,
                )

                btn_view = create_view_button(widget)
                btn_view.clicked.connect(callbacks["view"])
                layout.addWidget(btn_view)

                btn_edit = create_edit_button(widget)
                btn_edit.clicked.connect(callbacks["edit"])
                layout.addWidget(btn_edit)

                btn_perf = QPushButton()
                btn_perf.setToolTip("Performans Değerlendirme")
                if qta:
                    btn_perf.setIcon(qta.icon("fa5s.chart-line", color="#2196F3"))
                btn_perf.clicked.connect(lambda _, rid=sup_id: self._open_rating(rid))
                layout.addWidget(btn_perf)

                btn_del = create_delete_button(widget)
                btn_del.clicked.connect(callbacks["delete"])
                layout.addWidget(btn_del)

                layout.addStretch()
                self.table.setCellWidget(row, col_idx, widget)

    def _open_rating(self, supplier_id: int):
        from database.base import get_session
        from database.models.purchasing import Supplier

        session = get_session()
        supplier = session.query(Supplier).get(supplier_id)
        if supplier:
            dlg = VendorRatingDialog(supplier, self)
            if dlg.exec():
                self.refresh_clicked.emit()
        session.close()

    def _confirm_delete(self, supplier_id: int):
        if self.confirm_delete("tedarikçi"):
            self.delete_clicked.emit(supplier_id)
