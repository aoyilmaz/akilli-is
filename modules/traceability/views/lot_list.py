"""
Akıllı İş - Lot (Parti) Liste Sayfası
"""

from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ui.components.base_list_page import BaseListPage
from ui.components.enhanced_table import ColumnConfig
from config.icons import ICONS
from database.base import get_session
from database.models.traceability import Lot, LotStatus


class LotListPage(BaseListPage):
    """Lotların listelendiği ana sayfa"""

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("lot_number", "Lot Numarası", width=150),
            ColumnConfig("product_name", "Ürün", width=200),
            ColumnConfig(
                "quantity",
                "Başlangıç Mik.",
                width=100,
                align=Qt.AlignmentFlag.AlignRight,
            ),
            ColumnConfig(
                "remaining_qty",
                "Kalan Mik.",
                width=100,
                align=Qt.AlignmentFlag.AlignRight,
            ),
            ColumnConfig("status", "Durum", width=120),
            ColumnConfig("production_date", "Üretim Tarihi", width=120),
            ColumnConfig("expiry_date", "SKT", width=120),
        ]

        super().__init__(
            title="Lot (Parti) Yönetimi",
            icon=ICONS.LIST,
            table_id="traceability_lot_list",
            columns=columns,
            parent=parent,
        )

        # Sinyalleri bağla
        self.refresh_requested.connect(self.load_data)
        self.add_clicked.connect(self._on_add)
        self.view_clicked.connect(self._on_view)

        # Durum filtrelerini ayarla
        self.table.set_filter_options(
            "status", ["Aktif", "Karantina", "Blokeli", "Miadı Dolmuş", "Tüketilmiş"]
        )

        self.load_data()

    def load_data(self):
        """Veritabanından verileri yükle"""
        db = get_session()
        try:
            lots = db.query(Lot).all()
            self.clear_table()
            self.set_row_count(len(lots))

            for i, lot in enumerate(lots):
                self.table.setItem(i, 0, self._create_item(lot.lot_number, lot.id))
                p_name = lot.product.name if lot.product else "N/A"
                self.table.setItem(i, 1, self._create_item(p_name))

                qty_val = f"{lot.quantity:.3f}" if lot.quantity else "0.000"
                rem_val = f"{lot.remaining_qty:.3f}" if lot.remaining_qty else "0.000"

                self.table.setItem(
                    i, 2, self._create_item(qty_val, align=Qt.AlignmentFlag.AlignRight)
                )
                self.table.setItem(
                    i, 3, self._create_item(rem_val, align=Qt.AlignmentFlag.AlignRight)
                )

                st_display = self._get_status_display(lot.status)
                st_item = self._create_item(st_display)
                st_item.setForeground(Qt.GlobalColor.white)
                st_item.setBackground(self._get_status_color(lot.status))
                self.table.setItem(i, 4, st_item)

                p_date = (
                    lot.production_date.strftime("%d.%m.%Y")
                    if lot.production_date
                    else ""
                )
                e_date = lot.expiry_date.strftime("%d.%m.%Y") if lot.expiry_date else ""

                self.table.setItem(i, 5, self._create_item(p_date))
                self.table.setItem(i, 6, self._create_item(e_date))

            self.update_count(len(lots))

            # İstatistikleri güncelle
            active_c = sum(1 for lot in lots if lot.status == LotStatus.ACTIVE)
            quar_c = sum(1 for lot in lots if lot.status == LotStatus.QUARANTINE)

            self.update_stat_card("total_records", str(len(lots)))
            self.add_stat_card(
                "active_lots", "Aktif", str(active_c), "#2ecc71", ICONS.CHECK
            )
            self.add_stat_card(
                "quarantine", "Karantina", str(quar_c), "#f1c40f", ICONS.REFRESH
            )

        except Exception as e:
            self.show_error("Hata", f"Yükleme hatası: {str(e)}")
        finally:
            db.close()

    def _create_item(self, text, item_id=None, align=None):
        item = QTableWidgetItem(str(text))
        if item_id is not None:
            item.setData(Qt.ItemDataRole.UserRole, item_id)
        if align:
            item.setTextAlignment(align | Qt.AlignmentFlag.AlignVCenter)
        else:
            item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
        return item

    def _get_status_display(self, status: LotStatus) -> str:
        mapping = {
            LotStatus.ACTIVE: "Aktif",
            LotStatus.QUARANTINE: "Karantina",
            LotStatus.BLOCKED: "Blokeli",
            LotStatus.EXPIRED: "Miadı Dolmuş",
            LotStatus.CONSUMED: "Tüketilmiş",
        }
        return mapping.get(status, str(status))

    def _get_status_color(self, status: LotStatus):
        mapping = {
            LotStatus.ACTIVE: "#2ecc71",
            LotStatus.QUARANTINE: "#f1c40f",
            LotStatus.BLOCKED: "#e67e22",
            LotStatus.EXPIRED: "#e74c3c",
            LotStatus.CONSUMED: "#95a5a6",
        }
        return QColor(mapping.get(status, "#7f8c8d"))

    def _on_add(self):
        self.show_info("Bilgi", "Lot oluşturma özelliği yakında eklenecektir.")

    def _on_view(self, lot_id):
        from modules.traceability.views.trace_tree import TraceDialog

        dialog = TraceDialog(lot_id, self)
        dialog.exec()
