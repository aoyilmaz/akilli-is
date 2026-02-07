from datetime import datetime
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QTableWidgetItem
from PyQt6.QtCore import pyqtSignal

from config.icons import ICONS
from ui.components import BaseListPage, ColumnConfig
from database.models.fixed_asset import AssetStatus, AssetCategory


class FixedAssetList(BaseListPage):
    """
    Sabit Kıymetler listesi sayfası.
    """

    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    depreciate_clicked = pyqtSignal(int)

    CATEGORY_LABELS = {
        AssetCategory.BUILDING: "Bina",
        AssetCategory.VEHICLE: "Taşıt",
        AssetCategory.EQUIPMENT: "Teçhizat",
        AssetCategory.FURNITURE: "Demirbaş",
        AssetCategory.SOFTWARE: "Yazılım",
        AssetCategory.LAND: "Arazi",
        AssetCategory.OTHER: "Diğer",
    }

    STATUS_LABELS = {
        AssetStatus.ACTIVE: ("Aktif", "#10b981"),
        AssetStatus.SOLD: ("Satıldı", "#3b82f6"),
        AssetStatus.SCRAPPED: ("Hurda", "#ef4444"),
        AssetStatus.RETIRED: ("Emekli", "#6b7280"),
    }

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("id", "ID", width=60),
            ColumnConfig("name", "Adı", width=200, stretch=True),
            ColumnConfig("category", "Kategori", width=120, filter_type="enum"),
            ColumnConfig("purchase_date", "Alım Tarihi", width=100, filter_type="date"),
            ColumnConfig("purchase_price", "Alış Fiyatı", width=100),
            ColumnConfig("current_value", "Net Değer", width=100),
            ColumnConfig("status", "Durum", width=100, filter_type="enum"),
            ColumnConfig(
                "actions", "İşlemler", width=150, resizable=False, movable=False
            ),
        ]

        super().__init__(
            title="Sabit Kıymetler",
            icon=ICONS.INVENTORY,  # TODO: Better icon?
            table_id="fixed_assets",
            columns=columns,
            show_stats=True,
            show_search=True,
            show_add=True,
            search_placeholder="Ara... (isim, seri no)",
            parent=parent,
        )
        self.assets = []
        self._setup_stat_cards()

    def _setup_stat_cards(self):
        self.add_stat_card("total_count", "Toplam Varlık", "0", "info", ICONS.INVENTORY)
        self.add_stat_card("active_count", "Aktif", "0", "success", ICONS.CHECK)
        self.add_stat_card("total_value", "Toplam Değer", "₺0", "primary", ICONS.MONEY)
        self.add_stat_card(
            "depreciation", "Birikmiş Amort.", "₺0", "warning", ICONS.TREND_DOWN
        )

    def load_data(self, data: list):
        self.assets = data
        self._display_data(data)
        self._update_stats()

    def _display_data(self, data: list):
        self.table.setRowCount(len(data))
        visible_cols = self.table.get_visible_columns()
        for row, item in enumerate(data):
            self._populate_row(row, item, visible_cols)

    def _populate_row(self, row: int, item: dict, visible_cols: list):
        asset_id = item.get("id")

        for col_idx, col_key in enumerate(visible_cols):
            val = item.get(col_key, "")

            if col_key == "category":
                display_text = self.CATEGORY_LABELS.get(val, str(val))
                self.table.setItem(row, col_idx, QTableWidgetItem(display_text))

            elif col_key == "status":
                status = val
                text, _ = self.STATUS_LABELS.get(status, (str(status), "#000"))
                self.table.setItem(row, col_idx, QTableWidgetItem(text))

            elif col_key == "purchase_date":
                # Date handling might differ if it comes as string or date object
                if isinstance(val, str):
                    try:
                        val = datetime.fromisoformat(val).strftime("%d.%m.%Y")
                    except:
                        pass
                elif hasattr(val, "strftime"):
                    val = val.strftime("%d.%m.%Y")
                self.table.setItem(row, col_idx, QTableWidgetItem(str(val)))

            elif col_key in ["purchase_price", "current_value"]:
                # Format as currency
                try:
                    formatted = f"{float(val or 0):,.2f} ₺"
                    self.table.setItem(row, col_idx, QTableWidgetItem(formatted))
                except:
                    self.table.setItem(row, col_idx, QTableWidgetItem(str(val)))

            elif col_key == "actions":
                self._add_actions(row, col_idx, item)

            else:
                self.table.setItem(row, col_idx, QTableWidgetItem(str(val)))

    def _add_actions(self, row, col, item):
        from ui.components.action_buttons import create_custom_button

        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)

        asset_id = item.get("id")

        # Amortisman Hesapla
        calc_btn = create_custom_button(widget, ICONS.CALCULATOR, "Amort.", "secondary")
        calc_btn.clicked.connect(lambda: self.depreciate_clicked.emit(asset_id))
        layout.addWidget(calc_btn)

        # Düzenle
        edit_btn = create_custom_button(widget, ICONS.EDIT, "", "primary")
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(asset_id))
        layout.addWidget(edit_btn)

        # Sil
        delete_btn = create_custom_button(widget, ICONS.DELETE, "", "danger")
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(asset_id))
        layout.addWidget(delete_btn)

        layout.addStretch()
        self.table.setCellWidget(row, col, widget)

    def _update_stats(self):
        total_count = len(self.assets)
        active_count = sum(
            1 for a in self.assets if a.get("status") == AssetStatus.ACTIVE
        )
        total_value = sum(float(a.get("current_value") or 0) for a in self.assets)

        # For accumulated depreciation, we might need more data or calculate diff between purchase and current
        # Assuming current_value is net book value
        total_purchase = sum(float(a.get("purchase_price") or 0) for a in self.assets)
        total_depreciation = total_purchase - total_value

        self.update_stat_card("total_count", str(total_count))
        self.update_stat_card("active_count", str(active_count))
        self.update_stat_card("total_value", f"₺{total_value:,.0f}")
        self.update_stat_card("depreciation", f"₺{total_depreciation:,.0f}")
