"""
Akıllı İş - Ana Raporlama Modülü
VS Code Dark Theme
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QStackedWidget,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
)
from PyQt6.QtCore import Qt

from config.styles import (
    BG_PRIMARY, BG_SECONDARY, BORDER, TEXT_PRIMARY, TEXT_MUTED, ACCENT,
)
from modules.reports.services import ReportsService
from modules.reports.views.sales_reports import SalesReportsPage
from modules.reports.views.stock_aging import StockAgingPage
from modules.reports.views.production_oee import ProductionOEEPage
from modules.reports.views.supplier_performance import SupplierPerformancePage
from modules.reports.views.receivables_aging import ReceivablesAgingPage

try:
    from modules.inventory.services import WarehouseService
except ImportError:
    WarehouseService = None

class ReportsModule(QWidget):
    """Ana raporlama modülü"""

    page_title = "Raporlar"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.reports_service = None
        self.setup_ui()
        self.load_initial_data()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sol menü
        menu_frame = QFrame()
        menu_frame.setFixedWidth(240)
        menu_layout = QVBoxLayout(menu_frame)
        menu_layout.setContentsMargins(0, 0, 0, 0)
        menu_layout.setSpacing(0)

        # Başlık
        title = QLabel("Raporlar")
        menu_layout.addWidget(title)

        # Rapor listesi
        self.report_list = QListWidget()
        reports = [
            ("Satış Raporları", "sales"),
            ("Stok Yaşlandırma", "stock_aging"),
            ("Üretim OEE", "production_oee"),
            ("Tedarikçi Performans", "supplier_perf"),
            ("Alacak Yaşlandırma", "receivables"),
        ]

        for name, key in reports:
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.report_list.addItem(item)

        self.report_list.currentRowChanged.connect(self._on_report_changed)
        menu_layout.addWidget(self.report_list)
        menu_layout.addStretch()

        layout.addWidget(menu_frame)

        # İçerik alanı
        content_frame = QFrame()
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(24, 24, 24, 24)

        self.stack = QStackedWidget()

        # Rapor sayfalarını oluştur
        self.sales_page = SalesReportsPage()
        self.sales_page.refresh_requested.connect(self._load_sales_reports)
        self.stack.addWidget(self.sales_page)

        self.stock_aging_page = StockAgingPage()
        self.stock_aging_page.refresh_requested.connect(self._load_stock_aging)
        self.stack.addWidget(self.stock_aging_page)

        self.oee_page = ProductionOEEPage()
        self.oee_page.refresh_requested.connect(self._load_oee)
        self.stack.addWidget(self.oee_page)

        self.supplier_page = SupplierPerformancePage()
        self.supplier_page.refresh_requested.connect(
            self._load_supplier_performance
        )
        self.stack.addWidget(self.supplier_page)

        self.receivables_page = ReceivablesAgingPage()
        self.receivables_page.refresh_requested.connect(self._load_receivables)
        self.stack.addWidget(self.receivables_page)

        content_layout.addWidget(self.stack)
        layout.addWidget(content_frame, 1)

        # İlk raporu seç
        self.report_list.setCurrentRow(0)

    def _get_service(self):
        if self.reports_service is None:
            self.reports_service = ReportsService()
        return self.reports_service

    def _close_service(self):
        if self.reports_service:
            self.reports_service.close()
            self.reports_service = None

    def load_initial_data(self):
        """Başlangıç verilerini yükle"""
        # Depoları yükle
        if WarehouseService:
            try:
                with WarehouseService() as ws:
                    warehouses = ws.get_all()
                    self.stock_aging_page.load_warehouses(warehouses)
            except Exception:
                pass

        # İlk raporu yükle
        self._load_sales_reports()

    def _on_report_changed(self, index: int):
        """Rapor değiştiğinde"""
        self.stack.setCurrentIndex(index)

        # İlgili raporu yükle
        if index == 0:
            self._load_sales_reports()
        elif index == 1:
            self._load_stock_aging()
        elif index == 2:
            self._load_oee()
        elif index == 3:
            self._load_supplier_performance()
        elif index == 4:
            self._load_receivables()

    def _load_sales_reports(self):
        """Satış raporlarını yükle"""
        try:
            service = self._get_service()
            start_date, end_date = self.sales_page.get_date_range()

            # Müşteri bazlı
            customer_data = service.get_sales_by_customer(start_date, end_date)
            self.sales_page.load_customer_data(customer_data)

            # Ürün bazlı
            product_data = service.get_sales_by_product(start_date, end_date)
            self.sales_page.load_product_data(product_data)

            # Dönemsel
            period = self.sales_page.get_period()
            period_data = service.get_sales_by_period(period)
            self.sales_page.load_period_data(period_data)

            # Özet
            total = sum(c.get("total_amount", 0) for c in customer_data)
            count = sum(c.get("invoice_count", 0) for c in customer_data)
            customers = len(
                [c for c in customer_data if c["invoice_count"] > 0]
            )
            avg = total / count if count > 0 else 0
            self.sales_page.update_summary(total, count, customers, avg)

        except Exception as e:
            QMessageBox.warning(
                self, "Uyarı", f"Satış raporları yüklenirken hata:\n{str(e)}"
            )
        finally:
            self._close_service()

    def _load_stock_aging(self):
        """Stok yaşlandırma raporunu yükle"""
        try:
            service = self._get_service()
            warehouse_id = self.stock_aging_page.get_warehouse_id()
            data = service.get_stock_aging(warehouse_id)
            self.stock_aging_page.load_data(data)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Uyarı",
                f"Stok yaşlandırma raporu yüklenirken hata:\n{str(e)}"
            )
        finally:
            self._close_service()

    def _load_oee(self):
        """OEE raporunu yükle"""
        try:
            service = self._get_service()
            start_date, end_date = self.oee_page.get_date_range()
            data = service.get_production_oee(start_date, end_date)
            self.oee_page.load_data(data)
        except Exception as e:
            QMessageBox.warning(
                self, "Uyarı", f"OEE raporu yüklenirken hata:\n{str(e)}"
            )
        finally:
            self._close_service()

    def _load_supplier_performance(self):
        """Tedarikçi performans raporunu yükle"""
        try:
            service = self._get_service()
            data = service.get_supplier_performance()
            self.supplier_page.load_data(data)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Uyarı",
                f"Tedarikçi performans raporu yüklenirken hata:\n{str(e)}",
            )
        finally:
            self._close_service()

    def _load_receivables(self):
        """Alacak yaşlandırma raporunu yükle"""
        try:
            service = self._get_service()
            data = service.get_receivables_aging()
            self.receivables_page.load_data(data)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Uyarı",
                f"Alacak yaşlandırma raporu yüklenirken hata:\n{str(e)}"
            )
        finally:
            self._close_service()
