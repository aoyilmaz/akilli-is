"""
Akilli Is - Stok Yaslandirma Raporu Modulu (Bagimsiz)
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMessageBox

from modules.reports.services import ReportsService
from modules.reports.views.stock_aging import StockAgingPage

try:
    from modules.inventory.services import WarehouseService
except ImportError:
    WarehouseService = None

class StockAgingModule(QWidget):
    """Stok yaslandirma raporu modulu - bagimsiz calisir"""

    page_title = "Stok Yaslandirma"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.reports_service = None
        self.setup_ui()
        self.load_warehouses()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.page = StockAgingPage()
        self.page.refresh_requested.connect(self.load_data)
        layout.addWidget(self.page)

    def _get_service(self):
        if self.reports_service is None:
            self.reports_service = ReportsService()
        return self.reports_service

    def _close_service(self):
        if self.reports_service:
            self.reports_service.close()
            self.reports_service = None

    def load_warehouses(self):
        """Depolari yukle"""
        if WarehouseService:
            try:
                with WarehouseService() as ws:
                    warehouses = ws.get_all()
                    self.page.load_warehouses(warehouses)
            except Exception:
                pass

    def load_data(self):
        """Stok yaslandirma raporunu yukle"""
        try:
            service = self._get_service()
            warehouse_id = self.page.get_warehouse_id()
            data = service.get_stock_aging(warehouse_id)
            self.page.load_data(data)
        except Exception as e:
            QMessageBox.warning(
                self, "Uyari", f"Stok yaslandirma raporu yuklenirken hata:\n{str(e)}"
            )
        finally:
            self._close_service()
