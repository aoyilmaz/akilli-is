"""
Akıllı İş - Satış Teklif Modülü
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget, QMessageBox, QDialog
)
from PyQt6.QtCore import pyqtSignal

from .sales_quote_list import SalesQuoteListPage
from .sales_quote_form import SalesQuoteFormPage

try:
    from modules.development.services import ErrorHandler
except ImportError:
    ErrorHandler = None

class SalesQuoteModule(QWidget):
    """Satış teklif modülü"""

    page_title = "Satış Teklifleri"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.customer_service = None
        self.item_service = None
        self.unit_service = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()

        # Liste sayfası
        self.list_page = SalesQuoteListPage()
        self.list_page.add_clicked.connect(self._show_add_form)
        self.list_page.edit_clicked.connect(self._show_edit_form)
        self.list_page.delete_clicked.connect(self._delete_quote)
        self.list_page.view_clicked.connect(self._show_view)
        self.list_page.send_clicked.connect(self._send_to_customer)
        self.list_page.accept_clicked.connect(self._accept_quote)
        self.list_page.reject_clicked.connect(self._reject_quote)
        self.list_page.convert_to_order_clicked.connect(self._convert_to_order)
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
                from modules.sales.services import SalesQuoteService, CustomerService
                self.service = SalesQuoteService()
                self.customer_service = CustomerService()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(e, "SalesQuoteModule._ensure_services")
                print(f"Satış teklif servisi yükleme hatası: {e}")

        if not self.item_service:
            try:
                from modules.inventory.services import ItemService
                self.item_service = ItemService()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(e, "SalesQuoteModule._ensure_services")
                print(f"Stok servisi yükleme hatası: {e}")

        if not self.unit_service:
            try:
                from modules.inventory.services import UnitService
                self.unit_service = UnitService()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(e, "SalesQuoteModule._ensure_services")
                print(f"Birim servisi yükleme hatası: {e}")

    def _load_data(self):
        if not self.service:
            return

        try:
            quotes = self.service.get_all()
            data = []
            for q in quotes:
                data.append({
                    "id": q.id,
                    "quote_no": q.quote_no,
                    "quote_date": q.quote_date,
                    "customer_name": q.customer.name if q.customer else "-",
                    "total_amount": q.total or 0,
                    "status": q.status.value if q.status else "draft",
                    "valid_until": q.valid_until,
                    "currency_code": q.currency or "TRY",
                    "total_items": len(q.items) if q.items else 0,
                })
            self.list_page.load_data(data)
        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "SalesQuoteModule._load_data")
            print(f"Veri yükleme hatası: {e}")
            import traceback
            traceback.print_exc()
            self.list_page.load_data([])

    def _get_items(self) -> list:
        """Stok kartlarını getir"""
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
                "sale_price": float(i.sale_price or 0),
                "vat_rate": float(i.vat_rate or 0),
                "stock": 0,
            } for i in items]
        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "SalesQuoteModule._get_items")
            return []

    def _get_customers(self) -> list:
        """Müşterileri getir"""
        if not self.customer_service:
            return []
        try:
            customers = self.customer_service.get_all()
            return [{
                "id": c.id,
                "code": c.code,
                "name": c.name,
                "phone": c.phone,
                "email": c.email,
            } for c in customers]
        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "SalesQuoteModule._get_customers")
            return []

    def _get_units(self) -> list:
        """Birimleri getir"""
        if not self.unit_service:
            return []
        try:
            units = self.unit_service.get_all()
            return [{"id": u.id, "name": u.name, "code": u.code} for u in units]
        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "SalesQuoteModule._get_units")
            return []

    def _show_add_form(self):
        items = self._get_items()
        customers = self._get_customers()
        units = self._get_units()

        form = SalesQuoteFormPage(
            items=items,
            customers=customers,
            units=units
        )
        form.saved.connect(self._save_quote)
        form.cancelled.connect(self._back_to_list)
        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)

    def _show_edit_form(self, quote_id: int):
        if not self.service:
            return

        try:
            quote = self.service.get_by_id(quote_id)
            if quote:
                items_data = []
                for item in quote.items:
                    items_data.append({
                        "id": item.id,
                        "item_id": item.item_id,
                        "quantity": item.quantity,
                        "unit_id": item.unit_id,
                        "unit_price": item.unit_price,
                        "discount_rate": item.discount_rate,
                    })

                data = {
                    "id": quote.id,
                    "quote_no": quote.quote_no,
                    "quote_date": quote.quote_date,
                    "customer_id": quote.customer_id,
                    "customer_name": quote.customer.name if quote.customer else "",
                    "customer_code": quote.customer.code if quote.customer else "",
                    "valid_until": quote.valid_until,
                    "currency": quote.currency or "TRY",
                    "status": quote.status.value if quote.status else "draft",
                    "notes": quote.notes,
                    "items": items_data,
                }

                items = self._get_items()
                customers = self._get_customers()
                units = self._get_units()

                form = SalesQuoteFormPage(
                    quote_data=data,
                    items=items,
                    customers=customers,
                    units=units
                )
                form.saved.connect(self._save_quote)
                form.cancelled.connect(self._back_to_list)
                form.send_to_customer.connect(self._send_to_customer)
                self.stack.addWidget(form)
                self.stack.setCurrentWidget(form)

        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "SalesQuoteModule._show_edit_form")
            print(f"Düzenleme hatası: {e}")
            import traceback
            traceback.print_exc()

    def _show_view(self, quote_id: int):
        self._show_edit_form(quote_id)

    def _save_quote(self, data: dict):
        if not self.service:
            return

        try:
            quote_id = data.pop("id", None)
            items_data = data.pop("items", [])

            if quote_id:
                self.service.update(quote_id, items_data, **data)
                QMessageBox.information(self, "Başarılı", "Teklif güncellendi!")
            else:
                self.service.create(items_data, **data)
                QMessageBox.information(self, "Başarılı", "Yeni teklif oluşturuldu!")

            self._back_to_list()
            self._load_data()

        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "SalesQuoteModule._save_quote")
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {e}")
            import traceback
            traceback.print_exc()

    def _send_to_customer(self, quote_id: int):
        """Müşteriye gönder"""
        if not self.service:
            return

        try:
            self.service.send_to_customer(quote_id)
            QMessageBox.information(self, "Başarılı", "Teklif müşteriye gönderildi!")
            self._back_to_list()
            self._load_data()
        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "SalesQuoteModule._send_to_customer")
            QMessageBox.critical(self, "Hata", f"Hata: {e}")

    def _accept_quote(self, quote_id: int):
        """Teklifi kabul et"""
        if not self.service:
            return

        reply = QMessageBox.question(
            self, "Onay",
            "Bu teklifi kabul etmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.service.accept(quote_id)
                QMessageBox.information(self, "Başarılı", "Teklif kabul edildi!")
                self._load_data()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(e, "SalesQuoteModule._accept_quote")
                QMessageBox.critical(self, "Hata", f"Hata: {e}")

    def _reject_quote(self, quote_id: int):
        """Teklifi reddet"""
        if not self.service:
            return

        reply = QMessageBox.question(
            self, "Onay",
            "Bu teklifi reddetmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.service.reject(quote_id)
                QMessageBox.information(self, "Başarılı", "Teklif reddedildi!")
                self._load_data()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(e, "SalesQuoteModule._reject_quote")
                QMessageBox.critical(self, "Hata", f"Hata: {e}")

    def _convert_to_order(self, quote_id: int):
        """Siparişe dönüştür"""
        if not self.service:
            return

        reply = QMessageBox.question(
            self, "Onay",
            "Bu teklifi satış siparişine dönüştürmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                order = self.service.convert_to_order(quote_id)
                QMessageBox.information(
                    self, "Başarılı",
                    f"Satış siparişi oluşturuldu!\nSipariş No: {order.order_no}"
                )
                self._load_data()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(e, "SalesQuoteModule._convert_to_order")
                QMessageBox.critical(self, "Hata", f"Hata: {e}")
                import traceback
                traceback.print_exc()

    def _delete_quote(self, quote_id: int):
        if not self.service:
            return

        try:
            if self.service.delete(quote_id):
                QMessageBox.information(self, "Başarılı", "Teklif silindi!")
                self._load_data()
            else:
                QMessageBox.warning(self, "Uyarı", "Teklif silinemedi! (Sadece taslak teklifler silinebilir)")
        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "SalesQuoteModule._delete_quote")
            QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")

    def _back_to_list(self):
        current = self.stack.currentWidget()
        if current != self.list_page:
            self.stack.setCurrentWidget(self.list_page)
            self.stack.removeWidget(current)
            current.deleteLater()
