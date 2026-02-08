"""
Akıllı İş - Seri Numarası Liste Sayfası
"""

from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtCore import Qt

from ui.components.base_list_page import BaseListPage
from ui.components.enhanced_table import ColumnConfig
from config.icons import ICONS
from database.base import get_session
from database.models.traceability import SerialNumber


class SerialListPage(BaseListPage):
    """Seri numaralarının listelendiği sayfa"""

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("serial", "Seri Numarası", width=200),
            ColumnConfig("product_name", "Ürün", width=250),
            ColumnConfig("lot_number", "Bağlı Lot", width=150),
            ColumnConfig("status", "Durum", width=120),
            ColumnConfig("customer_name", "Müşteri", width=200),
            ColumnConfig("sale_date", "Satış Tarihi", width=120),
        ]

        super().__init__(
            title="Seri Numarası Takibi",
            icon=ICONS.CHART,
            table_id="traceability_serial_list",
            columns=columns,
            parent=parent,
        )

        self.refresh_requested.connect(self.load_data)
        self.load_data()

    def load_data(self):
        """Veritabanından seri numaralarını yükle"""
        db = get_session()
        try:
            serials = db.query(SerialNumber).all()
            self.clear_table()
            self.set_row_count(len(serials))

            for i, sn in enumerate(serials):
                self.table.setItem(i, 0, self._create_item(sn.serial, sn.id))
                self.table.setItem(
                    i, 1, self._create_item(sn.product.name if sn.product else "N/A")
                )
                self.table.setItem(
                    i, 2, self._create_item(sn.lot.lot_number if sn.lot else "-")
                )

                status_map = {
                    "in_stock": "Stokta",
                    "sold": "Satıldı",
                    "returned": "İade",
                    "scrapped": "Hurda",
                }
                status_text = status_map.get(sn.status, str(sn.status))
                self.table.setItem(i, 3, self._create_item(status_text))

                customer_name = sn.customer.name if sn.customer else "-"
                self.table.setItem(i, 4, self._create_item(customer_name))

                sale_date = sn.sale_date.strftime("%d.%m.%Y") if sn.sale_date else "-"
                self.table.setItem(i, 5, self._create_item(sale_date))

            self.update_count(len(serials))
        except Exception as e:
            self.show_error("Veri Yükleme Hatası", str(e))
        finally:
            db.close()

    def _create_item(self, text, item_id=None):
        item = QTableWidgetItem(str(text))
        if item_id is not None:
            item.setData(Qt.ItemDataRole.UserRole, item_id)
        return item
