"""
Akıllı İş - Stok Raporları Modülü
"""

from decimal import Decimal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMessageBox

from modules.inventory.services import ItemService, CategoryService, WarehouseService
from modules.inventory.views.reports_page import StockReportsPage

class StockReportsModule(QWidget):
    """Stok raporları modülü"""
    
    page_title = "Stok Raporları"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.item_service = None
        self.category_service = None
        self.warehouse_service = None
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.reports_page = StockReportsPage()
        self.reports_page.refresh_requested.connect(self.load_data)
        layout.addWidget(self.reports_page)
        
    def _get_services(self):
        if self.item_service is None:
            self.item_service = ItemService()
        if self.category_service is None:
            self.category_service = CategoryService()
        if self.warehouse_service is None:
            self.warehouse_service = WarehouseService()
            
    def _close_services(self):
        if self.item_service:
            self.item_service.close()
            self.item_service = None
        if self.category_service:
            self.category_service.close()
            self.category_service = None
        if self.warehouse_service:
            self.warehouse_service.close()
            self.warehouse_service = None
            
    def load_data(self):
        try:
            self._get_services()
            
            # Ürünleri al
            items = self.item_service.get_all()
            
            # Kategorileri yükle
            categories = self.category_service.get_all()
            self.reports_page.load_categories(categories)
            
            # Depoları yükle
            warehouses = self.warehouse_service.get_all()
            self.reports_page.load_warehouses(warehouses)
            
            # Rapor verilerini hazırla
            report_data = self._prepare_report_data(items)
            self.reports_page.load_data(report_data)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veriler yüklenirken hata:\n{str(e)}")
        finally:
            self._close_services()
            
    def _prepare_report_data(self, items: list) -> dict:
        """Rapor verilerini hazırla"""
        total_value = Decimal(0)
        low_stock_count = 0
        out_of_stock_count = 0
        
        items_data = []
        critical_items = []
        
        for item in items:
            total_stock = item.total_stock or Decimal(0)
            min_stock = item.min_stock or Decimal(0)
            
            # Birim maliyet ve toplam değer
            unit_cost = Decimal(0)
            if item.stock_balances:
                for balance in item.stock_balances:
                    if balance.unit_cost:
                        unit_cost = balance.unit_cost
                        break
            if unit_cost == 0:
                unit_cost = item.purchase_price or Decimal(0)
            
            item_value = total_stock * unit_cost
            total_value += item_value
            
            # Durum
            status = item.stock_status
            if status == "out_of_stock":
                out_of_stock_count += 1
            elif status in ["low", "critical"]:
                low_stock_count += 1
            
            item_data = {
                "code": item.code,
                "name": item.name,
                "category": item.category.name if item.category else "-",
                "unit": item.unit.code if item.unit else "",
                "quantity": float(total_stock),
                "min_stock": float(min_stock),
                "unit_cost": float(unit_cost),
                "total_value": float(item_value),
                "status": status,
                "reorder_qty": float(item.reorder_quantity or 0),
                "lead_time": item.lead_time_days or 0,
            }
            items_data.append(item_data)
            
            # Kritik ürünler
            if status in ["out_of_stock", "critical", "low"]:
                critical_items.append(item_data)
        
        return {
            "total_items": len(items),
            "total_value": float(total_value),
            "low_stock": low_stock_count,
            "out_of_stock": out_of_stock_count,
            "items": items_data,
            "critical_items": critical_items,
        }
