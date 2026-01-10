"""
Akıllı İş - Raporlama Modülü Views
"""

from .reports_module import ReportsModule
from .sales_reports import SalesReportsPage
from .stock_aging import StockAgingPage
from .production_oee import ProductionOEEPage
from .supplier_performance import SupplierPerformancePage
from .receivables_aging import ReceivablesAgingPage

__all__ = [
    "ReportsModule",
    "SalesReportsPage",
    "StockAgingPage",
    "ProductionOEEPage",
    "SupplierPerformancePage",
    "ReceivablesAgingPage",
]
