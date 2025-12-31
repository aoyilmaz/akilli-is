"""
Akıllı İş - Kategori Modülü
"""

from PyQt6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QMessageBox

from modules.inventory.services import CategoryService
from modules.inventory.views.category_list import CategoryListPage
from modules.inventory.views.category_form import CategoryFormPage


class CategoryModule(QWidget):
    """Kategori modülü"""
    
    page_title = "Kategoriler"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.category_service = None
        self.current_category = None
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        
        # Liste
        self.list_page = CategoryListPage()
        self.list_page.add_clicked.connect(self.show_add_form)
        self.list_page.add_child_clicked.connect(self.show_add_child_form)
        self.list_page.edit_clicked.connect(self.show_edit_form)
        self.list_page.delete_clicked.connect(self.delete_category)
        self.list_page.refresh_requested.connect(self.load_data)
        self.stack.addWidget(self.list_page)
        
        layout.addWidget(self.stack)
        
    def _get_service(self):
        if self.category_service is None:
            self.category_service = CategoryService()
            
    def _close_service(self):
        if self.category_service:
            self.category_service.close()
            self.category_service = None
            
    def load_data(self):
        try:
            self._get_service()
            categories = self.category_service.get_all()
            self.list_page.load_data(categories)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veriler yüklenirken hata:\n{str(e)}")
        finally:
            self._close_service()
            
    def show_add_form(self):
        self.current_category = None
        self._show_form(None, None)
        
    def show_add_child_form(self, parent_id: int):
        """Alt kategori ekleme formu"""
        self.current_category = None
        self._show_form(None, parent_id)
        
    def show_edit_form(self, category_id: int):
        try:
            self._get_service()
            category = self.category_service.get_by_id(category_id)
            if category:
                self.current_category = category
                self._show_form(category, None)
            else:
                QMessageBox.warning(self, "Uyarı", "Kategori bulunamadı!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kategori yüklenirken hata:\n{str(e)}")
        finally:
            self._close_service()
            
    def _show_form(self, category, parent_id):
        try:
            self._get_service()
            
            if self.stack.count() > 1:
                old = self.stack.widget(1)
                self.stack.removeWidget(old)
                old.deleteLater()
            
            form = CategoryFormPage(category, parent_id)
            form.saved.connect(self.save_category)
            form.cancelled.connect(self.show_list)
            
            # Kategorileri yükle
            categories = self.category_service.get_all()
            form.load_categories(categories)
            
            # Düzenleme modunda üst kategoriyi seç
            if category and category.parent_id:
                for i in range(form.parent_combo.count()):
                    if form.parent_combo.itemData(i) == category.parent_id:
                        form.parent_combo.setCurrentIndex(i)
                        break
            
            self.stack.addWidget(form)
            self.stack.setCurrentIndex(1)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Form açılırken hata:\n{str(e)}")
        finally:
            self._close_service()
            
    def show_list(self):
        self.stack.setCurrentIndex(0)
        self.load_data()
        
    def save_category(self, data: dict):
        try:
            self._get_service()
            
            if self.current_category:
                self.category_service.update(self.current_category.id, **data)
                QMessageBox.information(self, "Başarılı", "Kategori güncellendi!")
            else:
                self.category_service.create(**data)
                QMessageBox.information(self, "Başarılı", "Kategori oluşturuldu!")
            
            self.show_list()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası:\n{str(e)}")
        finally:
            self._close_service()
            
    def delete_category(self, category_id: int):
        try:
            self._get_service()
            if self.category_service.delete(category_id):
                QMessageBox.information(self, "Başarılı", "Kategori silindi!")
                self.load_data()
            else:
                QMessageBox.warning(self, "Uyarı", "Kategori silinemedi!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Silme hatası:\n{str(e)}")
        finally:
            self._close_service()
