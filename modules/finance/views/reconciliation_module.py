"""
Akilli Is - Mutabakat Modulu
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QMessageBox

from .reconciliation_page import ReconciliationPage

try:
    from modules.development.services import ErrorHandler
except ImportError:
    ErrorHandler = None

class ReconciliationModule(QWidget):
    """Mutabakat modulu"""

    page_title = "Mutabakat"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.reconciliation_service = None
        self.customer_service = None
        self.supplier_service = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()

        # Ana sayfa
        self.main_page = ReconciliationPage()
        self.main_page.refresh_requested.connect(self._load_data)
        self.main_page.print_requested.connect(self._print_report)
        self.stack.addWidget(self.main_page)

        layout.addWidget(self.stack)

    def showEvent(self, event):
        super().showEvent(event)
        self._ensure_services()
        self._load_entities()

    def _ensure_services(self):
        if not self.reconciliation_service:
            try:
                from modules.finance.services import ReconciliationService
                self.reconciliation_service = ReconciliationService()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(e, "ReconciliationModule._ensure_services")
                print(f"Mutabakat servisi yukleme hatasi: {e}")

        if not self.customer_service:
            try:
                from modules.sales.services import CustomerService
                self.customer_service = CustomerService()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(e, "ReconciliationModule._ensure_services")
                print(f"Musteri servisi yukleme hatasi: {e}")

        if not self.supplier_service:
            try:
                from modules.purchasing.services import SupplierService
                self.supplier_service = SupplierService()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(e, "ReconciliationModule._ensure_services")
                print(f"Tedarikci servisi yukleme hatasi: {e}")

    def _load_entities(self):
        """Cari listesini yukle"""
        filter_data = self.main_page.get_filter_data()
        entity_type = filter_data.get("entity_type", "customer")

        entities = []
        try:
            if entity_type == "customer" and self.customer_service:
                customers = self.customer_service.get_all()
                entities = [{"id": c.id, "code": c.code, "name": c.name} for c in customers]
            elif entity_type == "supplier" and self.supplier_service:
                suppliers = self.supplier_service.get_all()
                entities = [{"id": s.id, "code": s.code, "name": s.name} for s in suppliers]
        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "ReconciliationModule._load_entities")
            print(f"Cari listesi yukleme hatasi: {e}")

        self.main_page.load_entities(entity_type, entities)

    def _load_data(self):
        """Mutabakat verilerini yukle"""
        filter_data = self.main_page.get_filter_data()
        entity_type = filter_data.get("entity_type")
        entity_id = filter_data.get("entity_id")

        # Cari tipi degistiyse listeyi yeniden yukle
        if entity_type != self.main_page.current_entity_type:
            self._load_entities()
            return

        if not entity_id:
            self.main_page.load_data({
                "balance": 0,
                "open_invoices": [],
                "total_open_amount": 0,
            })
            return

        if not self.reconciliation_service:
            return

        try:
            if entity_type == "customer":
                data = self.reconciliation_service.get_customer_open_items(entity_id)
            else:
                data = self.reconciliation_service.get_supplier_open_items(entity_id)

            self.main_page.load_data(data)

        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "ReconciliationModule._load_data")
            print(f"Veri yukleme hatasi: {e}")
            import traceback
            traceback.print_exc()
            self.main_page.load_data({
                "balance": 0,
                "open_invoices": [],
                "total_open_amount": 0,
            })

    def _print_report(self, data: dict):
        """Rapor yazdir"""
        try:
            QMessageBox.information(
                self, "Bilgi",
                "Yazdir ozelligi yakinda eklenecek."
            )
        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "ReconciliationModule._print_report")
            QMessageBox.critical(self, "Hata", f"Yazdirma hatasi: {e}")
