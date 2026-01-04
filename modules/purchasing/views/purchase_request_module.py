"""
Akıllı İş - Satın Alma Talep Modülü
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget, QMessageBox,
    QDialog, QVBoxLayout as QVBox, QLabel, QTextEdit, 
    QPushButton, QHBoxLayout
)
from PyQt6.QtCore import pyqtSignal

from .purchase_request_list import PurchaseRequestListPage
from .purchase_request_form import PurchaseRequestFormPage


class RejectReasonDialog(QDialog):
    """Red nedeni dialogu"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Red Nedeni")
        self.setMinimumWidth(400)
        self.setStyleSheet("QDialog { background-color: #1e293b; }")
        
        layout = QVBox(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        label = QLabel("Lütfen red nedenini belirtin:")
        label.setStyleSheet("color: #f8fafc; font-size: 14px;")
        layout.addWidget(label)
        
        self.reason_input = QTextEdit()
        self.reason_input.setPlaceholderText("Red nedeni...")
        self.reason_input.setMinimumHeight(100)
        self.reason_input.setStyleSheet("""
            QTextEdit {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
                color: #f8fafc;
            }
        """)
        layout.addWidget(self.reason_input)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #f8fafc;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #475569; }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        confirm_btn = QPushButton("Reddet")
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #dc2626; }
        """)
        confirm_btn.clicked.connect(self.accept)
        btn_layout.addWidget(confirm_btn)
        
        layout.addLayout(btn_layout)
        
    def get_reason(self) -> str:
        return self.reason_input.toPlainText().strip()


class PurchaseRequestModule(QWidget):
    """Satın alma talep modülü"""
    
    page_title = "Satın Alma Talepleri"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.item_service = None
        self.supplier_service = None
        self.unit_service = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        
        # Liste sayfası
        self.list_page = PurchaseRequestListPage()
        self.list_page.add_clicked.connect(self._show_add_form)
        self.list_page.edit_clicked.connect(self._show_edit_form)
        self.list_page.delete_clicked.connect(self._delete_request)
        self.list_page.view_clicked.connect(self._show_view)
        self.list_page.approve_clicked.connect(self._approve_request)
        self.list_page.reject_clicked.connect(self._reject_request)
        self.list_page.refresh_requested.connect(self._load_data)
        self.stack.addWidget(self.list_page)
        
        layout.addWidget(self.stack)
        
    def showEvent(self, event):
        super().showEvent(event)
        self._ensure_services()
        self._load_data()
        
    def _ensure_services(self):
        if not self.service:
            try:
                from modules.purchasing.services import (
                    PurchaseRequestService, SupplierService
                )
                self.service = PurchaseRequestService()
                self.supplier_service = SupplierService()
            except Exception as e:
                print(f"Satın alma servisi yükleme hatası: {e}")
                
        if not self.item_service:
            try:
                from modules.inventory.services import ItemService
                self.item_service = ItemService()
            except Exception as e:
                print(f"Stok servisi yükleme hatası: {e}")
                
        if not self.unit_service:
            try:
                from modules.inventory.services import UnitService
                self.unit_service = UnitService()
            except Exception as e:
                print(f"Birim servisi yükleme hatası: {e}")
                
    def _load_data(self):
        if not self.service:
            return
            
        try:
            requests = self.service.get_all()
            data = []
            for r in requests:
                data.append({
                    "id": r.id,
                    "request_no": r.request_no,
                    "request_date": r.request_date,
                    "requested_by": r.requested_by,
                    "department": r.department,
                    "status": r.status.value if r.status else "draft",
                    "priority": r.priority,
                    "required_date": r.required_date,
                    "total_items": r.total_items,
                })
            self.list_page.load_data(data)
        except Exception as e:
            print(f"Veri yükleme hatası: {e}")
            import traceback
            traceback.print_exc()
            self.list_page.load_data([])
            
    def _get_items(self) -> list:
        """Stok kartlarını getir"""
        if not self.item_service:
            return []
        try:
            items = self.item_service.get_all()
            return [{
                "id": i.id,
                "code": i.code,
                "name": i.name,
                "unit_id": i.unit_id,
                "unit_name": i.unit.name if i.unit else "",
                "stock": 0,  # TODO: Stok miktarı
            } for i in items]
        except:
            return []
            
    def _get_suppliers(self) -> list:
        """Tedarikçileri getir"""
        if not self.supplier_service:
            return []
        try:
            suppliers = self.supplier_service.get_all()
            return [{"id": s.id, "name": s.name, "code": s.code} for s in suppliers]
        except:
            return []
            
    def _get_units(self) -> list:
        """Birimleri getir"""
        if not self.unit_service:
            return []
        try:
            units = self.unit_service.get_all()
            return [{"id": u.id, "name": u.name, "code": u.code} for u in units]
        except:
            return []
            
    def _show_add_form(self):
        items = self._get_items()
        suppliers = self._get_suppliers()
        units = self._get_units()
        
        form = PurchaseRequestFormPage(
            items=items, 
            suppliers=suppliers, 
            units=units
        )
        form.saved.connect(self._save_request)
        form.cancelled.connect(self._back_to_list)
        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)
        
    def _show_edit_form(self, request_id: int):
        if not self.service:
            return
            
        try:
            request = self.service.get_by_id(request_id)
            if request:
                # Kalemleri de dahil et
                items_data = []
                for item in request.items:
                    items_data.append({
                        "id": item.id,
                        "item_id": item.item_id,
                        "quantity": item.quantity,
                        "unit_id": item.unit_id,
                        "estimated_price": item.estimated_price,
                        "suggested_supplier_id": item.suggested_supplier_id,
                    })
                
                data = {
                    "id": request.id,
                    "request_no": request.request_no,
                    "request_date": request.request_date,
                    "requested_by": request.requested_by,
                    "department": request.department,
                    "status": request.status.value if request.status else "draft",
                    "priority": request.priority,
                    "required_date": request.required_date,
                    "notes": request.notes,
                    "items": items_data,
                }
                
                items = self._get_items()
                suppliers = self._get_suppliers()
                units = self._get_units()
                
                form = PurchaseRequestFormPage(
                    request_data=data,
                    items=items,
                    suppliers=suppliers,
                    units=units
                )
                form.saved.connect(self._save_request)
                form.cancelled.connect(self._back_to_list)
                form.submit_for_approval.connect(self._submit_for_approval)
                self.stack.addWidget(form)
                self.stack.setCurrentWidget(form)
                
        except Exception as e:
            print(f"Düzenleme hatası: {e}")
            import traceback
            traceback.print_exc()
            
    def _show_view(self, request_id: int):
        # Şimdilik düzenleme formunu göster
        self._show_edit_form(request_id)
        
    def _save_request(self, data: dict):
        if not self.service:
            return
            
        try:
            request_id = data.pop("id", None)
            items_data = data.pop("items", [])
            
            if request_id:
                self.service.update(request_id, items_data, **data)
                QMessageBox.information(self, "Başarılı", "Talep güncellendi!")
            else:
                self.service.create(items_data, **data)
                QMessageBox.information(self, "Başarılı", "Yeni talep oluşturuldu!")
            
            self._back_to_list()
            self._load_data()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {e}")
            import traceback
            traceback.print_exc()
            
    def _submit_for_approval(self, request_id: int):
        """Onaya gönder"""
        if not self.service:
            return
            
        try:
            self.service.submit_for_approval(request_id)
            QMessageBox.information(self, "Başarılı", "Talep onaya gönderildi!")
            self._back_to_list()
            self._load_data()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Hata: {e}")
            
    def _approve_request(self, request_id: int):
        """Talebi onayla"""
        if not self.service:
            return
            
        reply = QMessageBox.question(
            self, "Onay",
            "Bu talebi onaylamak istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.service.approve(request_id, "Admin")  # TODO: Gerçek kullanıcı
                QMessageBox.information(self, "Başarılı", "Talep onaylandı!")
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Onaylama hatası: {e}")
                
    def _reject_request(self, request_id: int):
        """Talebi reddet"""
        if not self.service:
            return
            
        dialog = RejectReasonDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            reason = dialog.get_reason()
            if not reason:
                QMessageBox.warning(self, "Uyarı", "Red nedeni belirtmelisiniz!")
                return
                
            try:
                self.service.reject(request_id, reason)
                QMessageBox.information(self, "Başarılı", "Talep reddedildi!")
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Reddetme hatası: {e}")
            
    def _delete_request(self, request_id: int):
        if not self.service:
            return
            
        try:
            if self.service.delete(request_id):
                QMessageBox.information(self, "Başarılı", "Talep silindi!")
                self._load_data()
            else:
                QMessageBox.warning(self, "Uyarı", "Talep silinemedi! (Sadece taslak talepler silinebilir)")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")
            
    def _back_to_list(self):
        current = self.stack.currentWidget()
        if current != self.list_page:
            self.stack.setCurrentWidget(self.list_page)
            self.stack.removeWidget(current)
            current.deleteLater()
