"""
Akıllı İş - Stok Hareketleri Modülü
"""

from datetime import datetime
from PyQt6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QMessageBox
from PyQt6.QtCore import pyqtSignal

from modules.inventory.services import StockMovementService, ItemService, WarehouseService
from modules.inventory.views.movement_list import MovementListPage
from modules.inventory.views.movement_form import MovementFormPage

class MovementModule(QWidget):
    """Stok hareketleri modülü"""
    
    page_title = "Stok Hareketleri"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.movement_service = None
        self.item_service = None
        self.warehouse_service = None
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        
        # Liste sayfası
        self.list_page = MovementListPage()
        self.list_page.add_entry_clicked.connect(lambda: self.show_form("entry"))
        self.list_page.add_exit_clicked.connect(lambda: self.show_form("exit"))
        self.list_page.add_transfer_clicked.connect(lambda: self.show_form("transfer"))
        self.list_page.refresh_requested.connect(self.load_data)
        self.stack.addWidget(self.list_page)
        
        layout.addWidget(self.stack)
        
    def _get_services(self):
        if self.movement_service is None:
            self.movement_service = StockMovementService()
        if self.item_service is None:
            self.item_service = ItemService()
        if self.warehouse_service is None:
            self.warehouse_service = WarehouseService()
            
    def _close_services(self):
        if self.movement_service:
            self.movement_service.close()
            self.movement_service = None
        if self.item_service:
            self.item_service.close()
            self.item_service = None
        if self.warehouse_service:
            self.warehouse_service.close()
            self.warehouse_service = None
            
    def load_data(self):
        try:
            self._get_services()
            
            filters = self.list_page.get_filters()
            
            # Hareket türü filtresi
            movement_type = None
            type_filter = filters.get("movement_type")
            if type_filter:
                from database.models import StockMovementType
                type_map = {
                    "giris": StockMovementType.GIRIS,
                    "cikis": StockMovementType.CIKIS,
                    "transfer": StockMovementType.TRANSFER,
                    "satin_alma": StockMovementType.SATIN_ALMA,
                    "satis": StockMovementType.SATIS,
                }
                movement_type = type_map.get(type_filter)
            
            movements = self.movement_service.get_movements(
                movement_type=movement_type,
                start_date=datetime.combine(filters.get("start_date"), datetime.min.time()),
                end_date=datetime.combine(filters.get("end_date"), datetime.max.time()),
                limit=500
            )
            
            # Keyword filtresi
            keyword = filters.get("keyword", "").lower()
            if keyword:
                movements = [m for m in movements 
                            if keyword in (m.item_code or "").lower()
                            or keyword in (m.document_no or "").lower()
                            or keyword in (m.item_name or "").lower()]
            
            self.list_page.load_data(movements)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veriler yüklenirken hata:\n{str(e)}")
        finally:
            self._close_services()
            
    def show_form(self, movement_type: str):
        """Form göster"""
        try:
            self._get_services()
            
            # Mevcut formu kaldır
            if self.stack.count() > 1:
                old = self.stack.widget(1)
                self.stack.removeWidget(old)
                old.deleteLater()
            
            # Yeni form
            form = MovementFormPage(movement_type)
            form.saved.connect(self.save_movement)
            form.cancelled.connect(self.show_list)
            
            # Stok kartlarını yükle
            items = self.item_service.get_all()
            form.load_items(items)
            
            # Depoları yükle
            warehouses = self.warehouse_service.get_all()
            form.load_warehouses(warehouses)
            
            self.stack.addWidget(form)
            self.stack.setCurrentIndex(1)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Form açılırken hata:\n{str(e)}")
        finally:
            self._close_services()
            
    def show_list(self):
        self.stack.setCurrentIndex(0)
        self.load_data()
        
    def save_movement(self, data: dict):
        """Hareketi kaydet"""
        try:
            self._get_services()
            
            lines = data.pop("lines", [])
            movement_type = data.pop("movement_type")
            from_warehouse_id = data.pop("from_warehouse_id", None)
            to_warehouse_id = data.pop("to_warehouse_id", None)
            
            # Her satır için hareket oluştur
            for line in lines:
                self.movement_service.create_movement(
                    item_id=line["item_id"],
                    movement_type=movement_type,
                    quantity=line["quantity"],
                    from_warehouse_id=from_warehouse_id,
                    to_warehouse_id=to_warehouse_id,
                    unit_price=line["unit_price"],
                    lot_number=line.get("lot_number"),
                    document_no=data.get("document_no"),
                    document_type="manual",
                    description=data.get("description"),
                )
            
            QMessageBox.information(self, "Başarılı", f"{len(lines)} satır kaydedildi!")
            self.show_list()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası:\n{str(e)}")
        finally:
            self._close_services()
