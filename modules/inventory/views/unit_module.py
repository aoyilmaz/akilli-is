"""
Akıllı İş - Birim Yönetimi Modülü
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMessageBox

from modules.inventory.services import UnitService
from modules.inventory.views.unit_management import UnitManagementPage

class UnitModule(QWidget):
    """Birim yönetimi modülü"""
    
    page_title = "Birimler"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.unit_service = None
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.page = UnitManagementPage()
        self.page.refresh_requested.connect(self.load_data)
        layout.addWidget(self.page)
        
    def _get_service(self):
        if self.unit_service is None:
            self.unit_service = UnitService()
            
    def _close_service(self):
        if self.unit_service:
            self.unit_service.close()
            self.unit_service = None
            
    def load_data(self):
        try:
            self._get_service()
            
            # Birimleri yükle
            units = self.unit_service.get_all(active_only=False)
            self.page.load_units(units)
            
            # Dönüşümleri yükle (şimdilik boş)
            self.page.load_conversions([])
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veriler yüklenirken hata:\n{str(e)}")
        finally:
            self._close_service()
