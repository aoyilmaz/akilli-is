"""
Akıllı İş - Depo Modülü
"""

from PyQt6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QMessageBox
from PyQt6.QtCore import pyqtSignal

from modules.inventory.services import WarehouseService
from modules.inventory.views.warehouse_list import WarehouseListPage
from modules.inventory.views.warehouse_form import WarehouseFormPage


class WarehouseModule(QWidget):
    """Depo modülü ana widget'ı"""
    
    page_title = "Depolar"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.warehouse_service = None
        self.current_warehouse = None
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        
        # Liste sayfası
        self.list_page = WarehouseListPage()
        self.list_page.add_clicked.connect(self.show_add_form)
        self.list_page.edit_clicked.connect(self.show_edit_form)
        self.list_page.delete_clicked.connect(self.delete_warehouse)
        self.list_page.refresh_requested.connect(self.load_data)
        self.stack.addWidget(self.list_page)
        
        layout.addWidget(self.stack)
        
    def _get_service(self):
        if self.warehouse_service is None:
            self.warehouse_service = WarehouseService()
            
    def _close_service(self):
        if self.warehouse_service:
            self.warehouse_service.close()
            self.warehouse_service = None
            
    def load_data(self):
        try:
            self._get_service()
            search = self.list_page.get_search_text()
            
            warehouses = self.warehouse_service.get_all()
            
            # Arama filtresi
            if search:
                search_lower = search.lower()
                warehouses = [w for w in warehouses 
                             if search_lower in w.code.lower() 
                             or search_lower in w.name.lower()]
            
            self.list_page.load_data(warehouses)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veriler yüklenirken hata:\n{str(e)}")
        finally:
            self._close_service()
            
    def show_add_form(self):
        self.current_warehouse = None
        self._show_form(None)
        
    def show_edit_form(self, warehouse_id: int):
        try:
            self._get_service()
            warehouse = self.warehouse_service.get_by_id(warehouse_id)
            if warehouse:
                self.current_warehouse = warehouse
                self._show_form(warehouse)
            else:
                QMessageBox.warning(self, "Uyarı", "Depo bulunamadı!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Depo yüklenirken hata:\n{str(e)}")
        finally:
            self._close_service()
            
    def _show_form(self, warehouse):
        if self.stack.count() > 1:
            old_form = self.stack.widget(1)
            self.stack.removeWidget(old_form)
            old_form.deleteLater()
        
        form = WarehouseFormPage(warehouse)
        form.saved.connect(self.save_warehouse)
        form.cancelled.connect(self.show_list)
        
        self.stack.addWidget(form)
        self.stack.setCurrentIndex(1)
        
    def show_list(self):
        self.stack.setCurrentIndex(0)
        self.load_data()
        
    def save_warehouse(self, data: dict):
        try:
            self._get_service()
            
            if self.current_warehouse:
                self.warehouse_service.update(self.current_warehouse.id, **data)
                QMessageBox.information(self, "Başarılı", "Depo güncellendi!")
            else:
                self.warehouse_service.create(**data)
                QMessageBox.information(self, "Başarılı", "Depo oluşturuldu!")
            
            self.show_list()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası:\n{str(e)}")
        finally:
            self._close_service()
            
    def delete_warehouse(self, warehouse_id: int):
        try:
            self._get_service()
            if self.warehouse_service.delete(warehouse_id):
                QMessageBox.information(self, "Başarılı", "Depo silindi!")
                self.load_data()
            else:
                QMessageBox.warning(self, "Uyarı", "Depo silinemedi!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Silme hatası:\n{str(e)}")
        finally:
            self._close_service()
