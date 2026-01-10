"""
Akilli Is - Satis Raporlari Modulu (Bagimsiz)
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMessageBox

from modules.reports.services import ReportsService
from modules.reports.views.sales_reports import SalesReportsPage


class SalesReportsModule(QWidget):
    """Satis raporlari modulu - bagimsiz calisir"""

    page_title = "Satis Raporlari"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.reports_service = None
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.page = SalesReportsPage()
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

    def load_data(self):
        """Satis raporlarini yukle"""
        try:
            service = self._get_service()
            start_date, end_date = self.page.get_date_range()

            # Musteri bazli
            customer_data = service.get_sales_by_customer(start_date, end_date)
            self.page.load_customer_data(customer_data)

            # Urun bazli
            product_data = service.get_sales_by_product(start_date, end_date)
            self.page.load_product_data(product_data)

            # Donemsel
            period = self.page.get_period()
            period_data = service.get_sales_by_period(period)
            self.page.load_period_data(period_data)

            # Ozet
            total = sum(c.get("total_amount", 0) for c in customer_data)
            count = sum(c.get("invoice_count", 0) for c in customer_data)
            customers = len([c for c in customer_data if c["invoice_count"] > 0])
            avg = total / count if count > 0 else 0
            self.page.update_summary(total, count, customers, avg)

        except Exception as e:
            QMessageBox.warning(
                self, "Uyari", f"Satis raporlari yuklenirken hata:\n{str(e)}"
            )
        finally:
            self._close_service()
