"""
Akıllı İş - BOM (Ürün Reçeteleri) Modülü
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QMessageBox

from .bom_list import BOMListPage
from .bom_form import BOMFormPage

class BOMModule(QWidget):
    """Ürün Reçeteleri modülü"""
    
    page_title = "Ürün Reçeteleri"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bom_service = None
        self.item_service = None
        self.unit_service = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        
        # Liste sayfası
        self.list_page = BOMListPage()
        self.list_page.new_clicked.connect(self._show_new_form)
        self.list_page.edit_clicked.connect(self._show_edit_form)
        self.list_page.view_clicked.connect(self._show_edit_form)
        self.list_page.delete_clicked.connect(self._delete_bom)
        self.list_page.copy_clicked.connect(self._copy_bom)
        self.list_page.activate_clicked.connect(self._activate_bom)
        self.list_page.refresh_requested.connect(self._load_data)
        self.stack.addWidget(self.list_page)
        
        layout.addWidget(self.stack)
        
    def showEvent(self, event):
        super().showEvent(event)
        self._ensure_services()
        self._load_data()
        
    def _ensure_services(self):
        """Servisleri yükle"""
        if not self.bom_service:
            try:
                from modules.production.services import BOMService
                from modules.inventory.services import ItemService, UnitService
                self.bom_service = BOMService()
                self.item_service = ItemService()
                self.unit_service = UnitService()
            except Exception as e:
                print(f"Servis yükleme hatası: {e}")
                
    def _load_data(self):
        """Verileri yükle"""
        if not self.bom_service:
            return
            
        try:
            status_filter = self.list_page.get_status_filter()
            
            # BOM Durumunu import et
            from database.models.production import BOMStatus
            status = BOMStatus(status_filter) if status_filter else None
            
            boms = self.bom_service.get_all(status=status)
            
            # Liste için veri dönüştür
            bom_list = []
            for bom in boms:
                bom_list.append({
                    "id": bom.id,
                    "code": bom.code,
                    "name": bom.name,
                    "item_id": bom.item_id,
                    "item_name": bom.item.name if bom.item else "-",
                    "version": bom.version,
                    "revision": bom.revision,
                    "status": bom.status.value if bom.status else "draft",
                    "line_count": len(bom.lines),
                    "total_cost": float(bom.total_cost or 0),
                })
            
            self.list_page.load_data(bom_list)
            
        except Exception as e:
            print(f"Veri yükleme hatası: {e}")
            # Boş liste göster
            self.list_page.load_data([])
            
    def _show_new_form(self):
        """Yeni reçete formu göster"""
        self._ensure_services()
        
        form = BOMFormPage()
        form.saved.connect(self._save_bom)
        form.cancelled.connect(self._show_list)
        form.code_requested.connect(lambda: self._generate_code(form))
        
        # Ürünleri ve malzemeleri yükle
        self._load_form_data(form)
        
        # Otomatik kod üret
        self._generate_code(form)
        
        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)
        
    def _show_edit_form(self, bom_id: int):
        """Düzenleme formu göster"""
        self._ensure_services()
        
        bom = self.bom_service.get_by_id(bom_id)
        if not bom:
            QMessageBox.warning(self, "Hata", "Reçete bulunamadı!")
            return
        
        # Veriyi dict'e dönüştür
        bom_data = {
            "id": bom.id,
            "code": bom.code,
            "name": bom.name,
            "description": bom.description,
            "item_id": bom.item_id,
            "base_quantity": float(bom.base_quantity or 1),
            "unit_id": bom.unit_id,
            "version": bom.version,
            "revision": bom.revision,
            "status": bom.status.value if bom.status else "draft",
            "labor_cost": float(bom.labor_cost or 0),
            "overhead_cost": float(bom.overhead_cost or 0),
            "lines": [
                {
                    "item_id": line.item_id,
                    "item_code": line.item.code if line.item else "",
                    "item_name": line.item.name if line.item else "",
                    "quantity": line.quantity,
                    "unit_code": line.unit.code if line.unit else "ADET",
                    "unit_id": line.unit_id,
                    "scrap_rate": line.scrap_rate or 0,
                    "unit_cost": line.unit_cost or 0,
                }
                for line in bom.lines
            ]
        }
        
        form = BOMFormPage(bom_data)
        form.saved.connect(self._save_bom)
        form.cancelled.connect(self._show_list)
        
        self._load_form_data(form)
        
        # Mamul seçimini ayarla
        for i in range(form.product_combo.count()):
            if form.product_combo.itemData(i) == bom.item_id:
                form.product_combo.setCurrentIndex(i)
                break
        
        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)
        
    def _load_form_data(self, form: BOMFormPage):
        """Form verilerini yükle"""
        try:
            # Mamul ürünleri (item_type = MAMUL)
            products = self.item_service.get_all()
            mamul_products = [p for p in products if p.item_type and p.item_type.value == "mamul"]
            form.set_products(mamul_products if mamul_products else products)
            
            # Tüm malzemeler
            form.set_items(products)
            
            # Birimler
            units = self.unit_service.get_all()
            form.set_units(units)
            
        except Exception as e:
            print(f"Form veri yükleme hatası: {e}")
            
    def _generate_code(self, form: BOMFormPage):
        """Otomatik kod üret"""
        try:
            code = self.bom_service.generate_code()
            form.set_generated_code(code)
        except Exception as e:
            print(f"Kod üretme hatası: {e}")
            
    def _save_bom(self, data: dict):
        """Reçeteyi kaydet"""
        try:
            bom_id = data.pop("id", None)
            
            # Status'u enum'a dönüştür
            from database.models.production import BOMStatus
            status_val = data.get("status", "draft")
            data["status"] = BOMStatus(status_val)
            
            if bom_id:
                self.bom_service.update(bom_id, **data)
                QMessageBox.information(self, "Başarılı", "Reçete güncellendi!")
            else:
                self.bom_service.create(**data)
                QMessageBox.information(self, "Başarılı", "Reçete oluşturuldu!")
            
            self._show_list()
            self._load_data()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası: {str(e)}")
            
    def _delete_bom(self, bom_id: int):
        """Reçeteyi sil"""
        try:
            self.bom_service.delete(bom_id)
            QMessageBox.information(self, "Başarılı", "Reçete silindi!")
            self._load_data()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Silme hatası: {str(e)}")
            
    def _copy_bom(self, bom_id: int):
        """Reçeteyi kopyala"""
        try:
            new_bom = self.bom_service.copy(bom_id)
            if new_bom:
                QMessageBox.information(self, "Başarılı", f"Reçete kopyalandı: {new_bom.code}")
                self._load_data()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kopyalama hatası: {str(e)}")
            
    def _activate_bom(self, bom_id: int):
        """Reçeteyi aktifleştir"""
        try:
            self.bom_service.activate(bom_id)
            QMessageBox.information(self, "Başarılı", "Reçete aktifleştirildi!")
            self._load_data()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Aktifleştirme hatası: {str(e)}")
            
    def _show_list(self):
        """Liste sayfasına dön"""
        # Form widget'ını kaldır
        current = self.stack.currentWidget()
        if current != self.list_page:
            self.stack.removeWidget(current)
            current.deleteLater()
        
        self.stack.setCurrentWidget(self.list_page)
