"""
Akıllı İş - Müşteri Liste Sayfası
Yeni bileşen mimarisi kullanılarak yeniden yapılandırıldı.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QTableWidgetItem,
    QApplication,
    QStyle,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize

from config.icons import ICONS
from ui.components import (
    BaseListPage,
    ColumnConfig,
    create_view_button,
    create_edit_button,
    create_delete_button,
)


class CustomerListPage(BaseListPage):
    """
    Müşteri listesi sayfası.
    BaseListPage'den türetildi, yeni bileşen mimarisini kullanır.
    """

    # Ek sinyaller (BaseListPage'den miras alınanların dışında)
    # BaseListPage zaten: refresh_requested, add_clicked, edit_clicked,
    # delete_clicked, view_clicked, export_clicked sağlar

    def __init__(self, parent=None):
        # Sütun yapılandırması
        columns = [
            ColumnConfig("code", "Kod", width=100, stretch=False),
            ColumnConfig("name", "Müşteri Adı", width=200, stretch=True),
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
            title="Müşteriler",
            icon=ICONS.USERS,
            table_id="customers",
            columns=columns,
            show_stats=True,
            show_search=True,
            show_refresh=True,
            show_add=True,
            add_text="Yeni Müşteri",
            search_placeholder="Ara... (kod, ad, vergi no)",
            parent=parent,
        )

        # Müşteri verileri
        self.customers = []

        # İstatistik kartları ekle
        self._setup_stat_cards()

    def _setup_stat_cards(self):
        """İstatistik kartlarını oluştur"""
        self.add_stat_card("total", "Toplam", "0", "#6366f1", "📊")
        self.add_stat_card("active", "Aktif", "0", "#10b981", "✅")
        self.add_stat_card("with_orders", "Siparişli", "0", "#f59e0b", "🛒")
        self.add_stat_card("credit", "Toplam Limit", "₺0", "#3b82f6", "💳")

    def load_data(self, customers: list):
        """Verileri yükle"""
        self.customers = customers
        self.clear_table()

        # İstatistikleri hesapla
        total = len(customers)
        active = 0
        total_credit = 0

        for cust in customers:
            if cust.get("is_active", True):
                active += 1
            total_credit += float(cust.get("credit_limit", 0) or 0)

        # Kartları güncelle
        self.update_stat_card("total", str(total))
        self.update_stat_card("active", str(active))
        self.update_stat_card("credit", f"₺{total_credit:,.0f}")

        # Tabloyu doldur
        self.table.setRowCount(len(customers))

        for row, cust in enumerate(customers):
            self._populate_row(row, cust)

    def _populate_row(self, row: int, cust: dict):
        """Tek satırı verilerle doldur"""
        # Görünür sütunları al
        visible_cols = self.table.get_visible_columns()

        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "code":
                item = QTableWidgetItem(cust.get("code", ""))
                item.setData(Qt.ItemDataRole.UserRole, cust.get("id"))
                self.table.setItem(row, col_idx, item)

            elif col_key == "name":
                self.table.setItem(row, col_idx, QTableWidgetItem(cust.get("name", "")))

            elif col_key == "phone":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(cust.get("phone", "") or "-")
                )

            elif col_key == "email":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(cust.get("email", "") or "-")
                )

            elif col_key == "city":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(cust.get("city", "") or "-")
                )

            elif col_key == "payment_term":
                vade = cust.get("payment_term_days", 0) or 0
                self.table.setItem(row, col_idx, QTableWidgetItem(str(vade)))

            elif col_key == "rating":
                rating = cust.get("rating", 0) or 0
                stars = "⭐" * rating if rating > 0 else "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(stars))

            elif col_key == "actions":
                self._add_action_buttons(row, col_idx, cust.get("id"))

        self.table.setRowHeight(row, 52)

    def _add_action_buttons(self, row: int, col: int, customer_id: int):
        """İşlem butonlarını ekle"""
        btn_widget = QWidget()
        btn_widget.setProperty("class", "action-button-group")
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setContentsMargins(4, 4, 4, 4)
        btn_layout.setSpacing(4)

        # Görüntüle
        view_btn = create_view_button()
        view_btn.setProperty("class", "action-view")
        view_btn.clicked.connect(
            lambda checked, cid=customer_id: self.view_clicked.emit(cid)
        )
        btn_layout.addWidget(view_btn)

        # Düzenle
        edit_btn = create_edit_button()
        edit_btn.setProperty("class", "action-edit")
        edit_btn.clicked.connect(
            lambda checked, cid=customer_id: self.edit_clicked.emit(cid)
        )
        btn_layout.addWidget(edit_btn)

        # Sil
        del_btn = create_delete_button()
        del_btn.setProperty("class", "action-delete")
        del_btn.clicked.connect(
            lambda checked, cid=customer_id: self._confirm_delete(cid)
        )
        btn_layout.addWidget(del_btn)

        self.table.setCellWidget(row, col, btn_widget)

    def _confirm_delete(self, customer_id: int):
        """Silme onayı"""
        if self.confirm_delete("müşteri"):
            self.delete_clicked.emit(customer_id)
