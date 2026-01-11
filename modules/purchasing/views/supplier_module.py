"""
Akıllı İş - Tedarikçi Modülü
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QMessageBox
from PyQt6.QtCore import pyqtSignal

from .supplier_list import SupplierListPage
from .supplier_form import SupplierFormPage

class SupplierModule(QWidget):
    """Tedarikçi yönetimi modülü"""
    
    page_title = "Tedarikçiler"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        
        # Liste sayfası
        self.list_page = SupplierListPage()
        self.list_page.add_clicked.connect(self._show_add_form)
        self.list_page.edit_clicked.connect(self._show_edit_form)
        self.list_page.delete_clicked.connect(self._delete_supplier)
        self.list_page.view_clicked.connect(self._show_view)
        self.list_page.refresh_requested.connect(self._load_data)
        self.stack.addWidget(self.list_page)
        
        layout.addWidget(self.stack)
        
    def showEvent(self, event):
        super().showEvent(event)
        self._ensure_service()
        self._load_data()
        
    def _ensure_service(self):
        if not self.service:
            try:
                from modules.purchasing.services import SupplierService
                self.service = SupplierService()
            except Exception as e:
                print(f"Servis yükleme hatası: {e}")
                
    def _load_data(self):
        if not self.service:
            return
            
        try:
            suppliers = self.service.get_all(active_only=False)
            data = []
            for s in suppliers:
                data.append({
                    "id": s.id,
                    "code": s.code,
                    "name": s.name,
                    "phone": s.phone,
                    "email": s.email,
                    "city": s.city,
                    "payment_term_days": s.payment_term_days,
                    "credit_limit": s.credit_limit,
                    "rating": s.rating,
                    "is_active": s.is_active,
                })
            self.list_page.load_data(data)
        except Exception as e:
            print(f"Veri yükleme hatası: {e}")
            self.list_page.load_data([])
            
    def _show_add_form(self):
        form = SupplierFormPage()
        form.saved.connect(self._save_supplier)
        form.cancelled.connect(self._back_to_list)
        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)
        
    def _show_edit_form(self, supplier_id: int):
        if not self.service:
            return
            
        try:
            supplier = self.service.get_by_id(supplier_id)
            if supplier:
                data = {
                    "id": supplier.id,
                    "code": supplier.code,
                    "name": supplier.name,
                    "short_name": supplier.short_name,
                    "tax_number": supplier.tax_number,
                    "tax_office": supplier.tax_office,
                    "contact_person": supplier.contact_person,
                    "phone": supplier.phone,
                    "mobile": supplier.mobile,
                    "fax": supplier.fax,
                    "email": supplier.email,
                    "website": supplier.website,
                    "address": supplier.address,
                    "city": supplier.city,
                    "district": supplier.district,
                    "postal_code": supplier.postal_code,
                    "country": supplier.country,
                    "payment_term_days": supplier.payment_term_days,
                    "credit_limit": supplier.credit_limit,
                    "currency": supplier.currency.value if supplier.currency else "TRY",
                    "rating": supplier.rating,
                    "bank_name": supplier.bank_name,
                    "bank_branch": supplier.bank_branch,
                    "bank_account_no": supplier.bank_account_no,
                    "iban": supplier.iban,
                    "notes": supplier.notes,
                }
                form = SupplierFormPage(data)
                form.saved.connect(self._save_supplier)
                form.cancelled.connect(self._back_to_list)
                self.stack.addWidget(form)
                self.stack.setCurrentWidget(form)
        except Exception as e:
            print(f"Düzenleme hatası: {e}")
            
    def _show_view(self, supplier_id: int):
        # Şimdilik düzenleme formunu göster
        self._show_edit_form(supplier_id)
        
    def _save_supplier(self, data: dict):
        if not self.service:
            return
            
        try:
            supplier_id = data.pop("id", None)
            
            # Kod yoksa otomatik oluştur
            if not data.get("code"):
                data["code"] = self.service.generate_code()
            
            if supplier_id:
                self.service.update(supplier_id, **data)
                QMessageBox.information(self, "Başarılı", "Tedarikçi güncellendi!")
            else:
                self.service.create(**data)
                QMessageBox.information(self, "Başarılı", "Yeni tedarikçi oluşturuldu!")
            
            self._back_to_list()
            self._load_data()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {e}")
            
    def _delete_supplier(self, supplier_id: int):
        if not self.service:
            return
            
        try:
            if self.service.delete(supplier_id):
                QMessageBox.information(self, "Başarılı", "Tedarikçi silindi!")
                self._load_data()
            else:
                QMessageBox.warning(self, "Uyarı", "Tedarikçi silinemedi!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")
            
    def _back_to_list(self):
        # Mevcut formu kaldır
        current = self.stack.currentWidget()
        if current != self.list_page:
            self.stack.setCurrentWidget(self.list_page)
            self.stack.removeWidget(current)
            current.deleteLater()
