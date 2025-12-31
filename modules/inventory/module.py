"""
Akıllı İş - Stok Modülü Ana Widget
"""

from PyQt6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QMessageBox
from PyQt6.QtCore import pyqtSignal

from .services import ItemService, UnitService, CategoryService
from .views import StockListPage, StockFormPage


class InventoryModule(QWidget):
    """Stok modülü ana widget'ı"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.item_service = None
        self.unit_service = None
        self.category_service = None
        self.current_item = None
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked widget (liste ve form arası geçiş)
        self.stack = QStackedWidget()
        
        # Liste sayfası
        self.list_page = StockListPage()
        self.list_page.add_clicked.connect(self.show_add_form)
        self.list_page.edit_clicked.connect(self.show_edit_form)
        self.list_page.delete_clicked.connect(self.delete_item)
        self.list_page.refresh_requested.connect(self.load_data)
        self.stack.addWidget(self.list_page)
        
        layout.addWidget(self.stack)
        
    def _get_services(self):
        """Servisleri al (lazy loading)"""
        if self.item_service is None:
            self.item_service = ItemService()
        if self.unit_service is None:
            self.unit_service = UnitService()
        if self.category_service is None:
            self.category_service = CategoryService()
            
    def _close_services(self):
        """Servisleri kapat"""
        if self.item_service:
            self.item_service.close()
            self.item_service = None
        if self.unit_service:
            self.unit_service.close()
            self.unit_service = None
        if self.category_service:
            self.category_service.close()
            self.category_service = None
            
    def load_data(self):
        """Verileri yükle"""
        try:
            self._get_services()
            
            # Filtreleri al
            filters = self.list_page.get_filters()
            
            # Stok kartlarını getir
            items = self.item_service.search(
                keyword=filters.get("keyword", ""),
                item_type=filters.get("item_type"),
            )
            
            self.list_page.load_data(items)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veriler yüklenirken hata oluştu:\n{str(e)}")
        finally:
            self._close_services()
            
    def show_add_form(self):
        """Yeni stok kartı formu göster"""
        self.current_item = None
        self._show_form(None)
        
    def show_edit_form(self, item_id: int):
        """Düzenleme formu göster"""
        try:
            self._get_services()
            item = self.item_service.get_by_id(item_id)
            if item:
                self.current_item = item
                self._show_form(item)
            else:
                QMessageBox.warning(self, "Uyarı", "Stok kartı bulunamadı!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Stok kartı yüklenirken hata:\n{str(e)}")
        finally:
            self._close_services()
            
    def _show_form(self, item):
        """Form sayfasını göster"""
        try:
            self._get_services()
            
            # Mevcut form varsa kaldır
            if self.stack.count() > 1:
                old_form = self.stack.widget(1)
                self.stack.removeWidget(old_form)
                old_form.deleteLater()
            
            # Yeni form oluştur
            form = StockFormPage(item)
            form.saved.connect(self.save_item)
            form.cancelled.connect(self.show_list)
            
            # Birimleri yükle
            units = self.unit_service.get_all()
            form.load_units(units)
            
            # Kategorileri yükle
            categories = self.category_service.get_all()
            form.load_categories(categories)
            
            # Otomatik kod üretme
            if item is None:
                next_code = self.item_service.get_next_code()
                form.set_generated_code(next_code)
            
            # Birim ve kategori seçimlerini ayarla (düzenleme modunda)
            if item:
                # Birim
                for i in range(form.unit_combo.count()):
                    if form.unit_combo.itemData(i) == item.unit_id:
                        form.unit_combo.setCurrentIndex(i)
                        break
                # Kategori
                for i in range(form.category_combo.count()):
                    if form.category_combo.itemData(i) == item.category_id:
                        form.category_combo.setCurrentIndex(i)
                        break
            
            self.stack.addWidget(form)
            self.stack.setCurrentIndex(1)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Form açılırken hata:\n{str(e)}")
        finally:
            self._close_services()
            
    def show_list(self):
        """Liste sayfasına dön"""
        self.stack.setCurrentIndex(0)
        self.load_data()
        
    def save_item(self, data: dict):
        """Stok kartını kaydet"""
        try:
            self._get_services()
            
            if self.current_item:
                # Güncelleme
                self.item_service.update(self.current_item.id, **data)
                QMessageBox.information(self, "Başarılı", "Stok kartı güncellendi!")
            else:
                # Yeni kayıt
                self.item_service.create(**data)
                QMessageBox.information(self, "Başarılı", "Stok kartı oluşturuldu!")
            
            self.show_list()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası:\n{str(e)}")
        finally:
            self._close_services()
            
    def delete_item(self, item_id: int):
        """Stok kartını sil"""
        try:
            self._get_services()
            
            if self.item_service.delete(item_id):
                QMessageBox.information(self, "Başarılı", "Stok kartı silindi!")
                self.load_data()
            else:
                QMessageBox.warning(self, "Uyarı", "Stok kartı silinemedi!")
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Silme hatası:\n{str(e)}")
        finally:
            self._close_services()
