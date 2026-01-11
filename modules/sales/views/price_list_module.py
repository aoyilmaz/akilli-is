"""
Akilli Is - Fiyat Listesi Modulu
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget, QMessageBox
)

from .price_list_list import PriceListListPage
from .price_list_form import PriceListFormPage

try:
    from modules.development.services import ErrorHandler
except ImportError:
    ErrorHandler = None

class PriceListModule(QWidget):
    """Fiyat listesi modulu"""

    page_title = "Fiyat Listeleri"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.item_service = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()

        # Liste sayfasi
        self.list_page = PriceListListPage()
        self.list_page.add_clicked.connect(self._show_add_form)
        self.list_page.edit_clicked.connect(self._show_edit_form)
        self.list_page.delete_clicked.connect(self._delete_price_list)
        self.list_page.view_clicked.connect(self._show_view)
        self.list_page.refresh_requested.connect(self._load_data)
        self.stack.addWidget(self.list_page)

        layout.addWidget(self.stack)

    def showEvent(self, event):
        super().showEvent(event)
        self._ensure_services()
        self._load_data()

    def _ensure_services(self):
        if not self.service:
            try:
                from modules.sales.services import PriceListService
                self.service = PriceListService()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(
                        e, "PriceListModule._ensure_services"
                    )
                print(f"Fiyat listesi servisi yukleme hatasi: {e}")

        if not self.item_service:
            try:
                from modules.inventory.services import ItemService
                self.item_service = ItemService()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(
                        e, "PriceListModule._ensure_services"
                    )
                print(f"Stok servisi yukleme hatasi: {e}")

    def _load_data(self):
        if not self.service:
            return

        try:
            price_lists = self.service.get_all()
            data = []
            for pl in price_lists:
                data.append({
                    "id": pl.id,
                    "code": pl.code,
                    "name": pl.name,
                    "list_type": pl.list_type.value if pl.list_type else "sales",
                    "currency": pl.currency,
                    "valid_from": pl.valid_from,
                    "valid_until": pl.valid_until,
                    "is_default": pl.is_default,
                    "priority": pl.priority,
                    "item_count": len(pl.items) if pl.items else 0,
                })
            self.list_page.load_data(data)
        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "PriceListModule._load_data")
            print(f"Veri yukleme hatasi: {e}")
            import traceback
            traceback.print_exc()
            self.list_page.load_data([])

    def _get_items(self) -> list:
        """Stok kartlarini getir"""
        if not self.item_service:
            return []
        try:
            items = self.item_service.get_all()
            return [{
                "id": i.id,
                "code": i.code,
                "name": i.name,
                "unit_id": i.unit_id,
                "unit_name": i.unit.name if i.unit else "",
                "sale_price": i.sale_price,
            } for i in items]
        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "PriceListModule._get_items")
            return []

    def _show_add_form(self):
        items = self._get_items()

        # Otomatik kod olustur
        code = self.service.generate_code() if self.service else "FL0001"

        form = PriceListFormPage(
            price_list_data={"code": code},
            items=items
        )
        form.saved.connect(self._save_price_list)
        form.cancelled.connect(self._back_to_list)
        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)

    def _show_edit_form(self, price_list_id: int):
        if not self.service:
            return

        try:
            pl = self.service.get_by_id(price_list_id)
            if pl:
                items_data = []
                for item in pl.items:
                    items_data.append({
                        "id": item.id,
                        "item_id": item.item_id,
                        "item_code": item.item.code if item.item else "",
                        "item_name": item.item.name if item.item else "",
                        "unit_price": item.unit_price,
                        "min_quantity": item.min_quantity,
                        "discount_rate": item.discount_rate,
                    })

                data = {
                    "id": pl.id,
                    "code": pl.code,
                    "name": pl.name,
                    "description": pl.description,
                    "list_type": pl.list_type.value if pl.list_type else "sales",
                    "currency": pl.currency,
                    "valid_from": pl.valid_from,
                    "valid_until": pl.valid_until,
                    "is_default": pl.is_default,
                    "priority": pl.priority,
                    "items": items_data,
                }

                items = self._get_items()

                form = PriceListFormPage(
                    price_list_data=data,
                    items=items
                )
                form.saved.connect(self._save_price_list)
                form.cancelled.connect(self._back_to_list)
                self.stack.addWidget(form)
                self.stack.setCurrentWidget(form)

        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "PriceListModule._show_edit_form")
            print(f"Duzenleme hatasi: {e}")
            import traceback
            traceback.print_exc()

    def _show_view(self, price_list_id: int):
        self._show_edit_form(price_list_id)

    def _save_price_list(self, data: dict):
        if not self.service:
            return

        try:
            pl_id = data.pop("id", None)
            items_data = data.pop("items", [])

            if pl_id:
                self.service.update(pl_id, items_data, **data)
                QMessageBox.information(
                    self, "Basarili", "Fiyat listesi guncellendi!"
                )
            else:
                self.service.create(items_data, **data)
                QMessageBox.information(
                    self, "Basarili", "Yeni fiyat listesi olusturuldu!"
                )

            self._back_to_list()
            self._load_data()

        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "PriceListModule._save_price_list")
            QMessageBox.critical(self, "Hata", f"Kaydetme hatasi: {e}")
            import traceback
            traceback.print_exc()

    def _delete_price_list(self, price_list_id: int):
        if not self.service:
            return

        try:
            if self.service.delete(price_list_id):
                QMessageBox.information(
                    self, "Basarili", "Fiyat listesi silindi!"
                )
                self._load_data()
            else:
                QMessageBox.warning(
                    self, "Uyari", "Fiyat listesi silinemedi!"
                )
        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "PriceListModule._delete_price_list")
            QMessageBox.critical(self, "Hata", f"Silme hatasi: {e}")

    def _back_to_list(self):
        current = self.stack.currentWidget()
        if current != self.list_page:
            self.stack.setCurrentWidget(self.list_page)
            self.stack.removeWidget(current)
            current.deleteLater()
