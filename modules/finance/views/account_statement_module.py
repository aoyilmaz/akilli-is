"""
Akilli Is - Cari Hesap Ekstresi Modulu
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QMessageBox

from .account_statement_list import AccountStatementListPage

try:
    from modules.development.services import ErrorHandler
except ImportError:
    ErrorHandler = None


class AccountStatementModule(QWidget):
    """Cari hesap ekstresi modulu"""

    page_title = "Cari Hesaplar"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.transaction_service = None
        self.reconciliation_service = None
        self.customer_service = None
        self.supplier_service = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()

        # Liste sayfasi
        self.list_page = AccountStatementListPage()
        self.list_page.refresh_requested.connect(self._load_data)
        self.list_page.export_requested.connect(self._export_to_excel)
        self.stack.addWidget(self.list_page)

        layout.addWidget(self.stack)

    def showEvent(self, event):
        super().showEvent(event)
        self._ensure_services()
        self._load_entities()

    def _ensure_services(self):
        if not self.transaction_service:
            try:
                from modules.finance.services import (
                    AccountTransactionService,
                    ReconciliationService
                )
                self.transaction_service = AccountTransactionService()
                self.reconciliation_service = ReconciliationService()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(e, "AccountStatementModule._ensure_services")
                print(f"Finans servisi yukleme hatasi: {e}")

        if not self.customer_service:
            try:
                from modules.sales.services import CustomerService
                self.customer_service = CustomerService()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(e, "AccountStatementModule._ensure_services")
                print(f"Musteri servisi yukleme hatasi: {e}")

        if not self.supplier_service:
            try:
                from modules.purchasing.services import SupplierService
                self.supplier_service = SupplierService()
            except Exception as e:
                if ErrorHandler:
                    ErrorHandler.log_error(e, "AccountStatementModule._ensure_services")
                print(f"Tedarikci servisi yukleme hatasi: {e}")

    def _load_entities(self):
        """Cari listesini yukle"""
        filter_data = self.list_page.get_filter_data()
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
                ErrorHandler.log_error(e, "AccountStatementModule._load_entities")
            print(f"Cari listesi yukleme hatasi: {e}")

        self.list_page.load_entities(entity_type, entities)

    def _load_data(self):
        """Hareket verilerini yukle"""
        filter_data = self.list_page.get_filter_data()
        entity_type = filter_data.get("entity_type")
        entity_id = filter_data.get("entity_id")
        date_from = filter_data.get("date_from")
        date_to = filter_data.get("date_to")

        # Cari tipi degistiyse listeyi yeniden yukle
        if entity_type != self.list_page.current_entity_type:
            self._load_entities()
            return

        if not entity_id:
            self.list_page.load_data([], {})
            return

        if not self.reconciliation_service:
            return

        try:
            # Mutabakat raporu al
            report = self.reconciliation_service.get_reconciliation_report(
                customer_id=entity_id if entity_type == "customer" else None,
                supplier_id=entity_id if entity_type == "supplier" else None,
                date_from=date_from,
                date_to=date_to
            )

            movements = report.get("movements", [])
            summary = {
                "total_debit": report.get("total_debit", 0),
                "total_credit": report.get("total_credit", 0),
                "closing_balance": report.get("closing_balance", 0),
            }

            self.list_page.load_data(movements, summary)

        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "AccountStatementModule._load_data")
            print(f"Veri yukleme hatasi: {e}")
            import traceback
            traceback.print_exc()
            self.list_page.load_data([], {})

    def _export_to_excel(self, data: dict):
        """Excel'e aktar"""
        try:
            # Basit bir mesaj goster (gercek uygulama icin openpyxl kullanilabilir)
            QMessageBox.information(
                self, "Bilgi",
                "Excel disa aktarma ozelligi yaklnda eklenecek."
            )
        except Exception as e:
            if ErrorHandler:
                ErrorHandler.log_error(e, "AccountStatementModule._export_to_excel")
            QMessageBox.critical(self, "Hata", f"Disa aktarma hatasi: {e}")
