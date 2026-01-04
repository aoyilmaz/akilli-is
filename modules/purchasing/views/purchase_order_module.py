"""
Akıllı İş - Satın Alma Sipariş Modülü
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QMessageBox
from PyQt6.QtCore import pyqtSignal

from .purchase_order_list import PurchaseOrderListPage
from .purchase_order_form import PurchaseOrderFormPage


class PurchaseOrderModule(QWidget):
    """Satın alma sipariş modülü"""
    
    page_title = "Satın Alma Siparişleri"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.supplier_service = None
        self.warehouse_service = None
        self.item_service = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        
        # Liste sayfası
        self.list_page = PurchaseOrderListPage()
        self.list_page.add_clicked.connect(self._show_add_form)
        self.list_page.edit_clicked.connect(self._show_edit_form)
        self.list_page.delete_clicked.connect(self._delete_order)
        self.list_page.view_clicked.connect(self._show_view)
        self.list_page.send_clicked.connect(self._send_order)
        self.list_page.receive_clicked.connect(self._create_receipt)
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
                    PurchaseOrderService, SupplierService
                )
                self.service = PurchaseOrderService()
                self.supplier_service = SupplierService()
            except Exception as e:
                print(f"Satın alma servisi yükleme hatası: {e}")
                
        if not self.warehouse_service:
            try:
                from modules.inventory.services import WarehouseService
                self.warehouse_service = WarehouseService()
            except Exception as e:
                print(f"Depo servisi yükleme hatası: {e}")
                
        if not self.item_service:
            try:
                from modules.inventory.services import ItemService
                self.item_service = ItemService()
            except Exception as e:
                print(f"Stok servisi yükleme hatası: {e}")
                
    def _load_data(self):
        if not self.service:
            return
            
        try:
            orders = self.service.get_all()
            data = []
            for o in orders:
                data.append({
                    "id": o.id,
                    "order_no": o.order_no,
                    "order_date": o.order_date,
                    "supplier_name": o.supplier.name if o.supplier else "",
                    "delivery_date": o.delivery_date,
                    "status": o.status.value if o.status else "draft",
                    "total_items": o.total_items,
                    "total": o.total,
                    "currency": o.currency.value if o.currency else "TRY",
                    "received_rate": o.received_rate,
                })
            self.list_page.load_data(data)
        except Exception as e:
            print(f"Veri yükleme hatası: {e}")
            import traceback
            traceback.print_exc()
            self.list_page.load_data([])
            
    def _get_suppliers(self) -> list:
        if not self.supplier_service:
            return []
        try:
            suppliers = self.supplier_service.get_all()
            return [{
                "id": s.id, 
                "code": s.code, 
                "name": s.name,
                "payment_term_days": s.payment_term_days,
                "currency": s.currency.value if s.currency else "TRY",
            } for s in suppliers]
        except:
            return []
            
    def _get_warehouses(self) -> list:
        if not self.warehouse_service:
            return []
        try:
            warehouses = self.warehouse_service.get_all()
            return [{"id": w.id, "name": w.name, "code": w.code} for w in warehouses]
        except:
            return []
            
    def _get_items(self) -> list:
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
            } for i in items]
        except:
            return []
            
    def _show_add_form(self):
        suppliers = self._get_suppliers()
        warehouses = self._get_warehouses()
        items = self._get_items()
        
        form = PurchaseOrderFormPage(
            suppliers=suppliers,
            warehouses=warehouses,
            items=items
        )
        form.saved.connect(self._save_order)
        form.cancelled.connect(self._back_to_list)
        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)
        
    def _show_edit_form(self, order_id: int):
        if not self.service:
            return
            
        try:
            order = self.service.get_by_id(order_id)
            if order:
                items_data = []
                for item in order.items:
                    items_data.append({
                        "id": item.id,
                        "item_id": item.item_id,
                        "quantity": item.quantity,
                        "unit_id": item.unit_id,
                        "unit_price": item.unit_price,
                        "tax_rate": item.tax_rate,
                    })
                
                data = {
                    "id": order.id,
                    "order_no": order.order_no,
                    "order_date": order.order_date,
                    "supplier_id": order.supplier_id,
                    "delivery_date": order.delivery_date,
                    "delivery_warehouse_id": order.delivery_warehouse_id,
                    "payment_term_days": order.payment_term_days,
                    "currency": order.currency.value if order.currency else "TRY",
                    "exchange_rate": order.exchange_rate,
                    "notes": order.notes,
                    "status": order.status.value if order.status else "draft",
                    "items": items_data,
                }
                
                suppliers = self._get_suppliers()
                warehouses = self._get_warehouses()
                items = self._get_items()
                
                form = PurchaseOrderFormPage(
                    order_data=data,
                    suppliers=suppliers,
                    warehouses=warehouses,
                    items=items
                )
                form.saved.connect(self._save_order)
                form.cancelled.connect(self._back_to_list)
                self.stack.addWidget(form)
                self.stack.setCurrentWidget(form)
                
        except Exception as e:
            print(f"Düzenleme hatası: {e}")
            import traceback
            traceback.print_exc()
            
    def _show_view(self, order_id: int):
        self._show_edit_form(order_id)
        
    def _save_order(self, data: dict):
        if not self.service:
            return
            
        try:
            order_id = data.pop("id", None)
            items_data = data.pop("items", [])
            
            if order_id:
                self.service.update(order_id, items_data, **data)
                QMessageBox.information(self, "Başarılı", "Sipariş güncellendi!")
            else:
                self.service.create(items_data, **data)
                QMessageBox.information(self, "Başarılı", "Yeni sipariş oluşturuldu!")
            
            self._back_to_list()
            self._load_data()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {e}")
            import traceback
            traceback.print_exc()
            
    def _send_order(self, order_id: int):
        """Siparişi tedarikçiye gönder"""
        if not self.service:
            return
            
        reply = QMessageBox.question(
            self, "Gönder",
            "Bu siparişi tedarikçiye göndermek istediğinize emin misiniz?\n\n"
            "Gönderildikten sonra düzenleme yapılamaz.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.service.send_to_supplier(order_id)
                QMessageBox.information(self, "Başarılı", "Sipariş gönderildi!")
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Hata: {e}")
                
    def _create_receipt(self, order_id: int):
        """Siparişten mal kabul oluştur"""
        QMessageBox.information(
            self, "Bilgi",
            "Mal kabul sayfasından 'Siparişten' butonunu kullanarak\n"
            "bu sipariş için mal kabul oluşturabilirsiniz.\n\n"
            "(Tam entegrasyon yakında eklenecek)"
        )
            
    def _delete_order(self, order_id: int):
        if not self.service:
            return
            
        try:
            if self.service.delete(order_id):
                QMessageBox.information(self, "Başarılı", "Sipariş silindi!")
                self._load_data()
            else:
                QMessageBox.warning(self, "Uyarı", "Silinemedi! (Sadece taslak siparişler silinebilir)")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")
            
    def _back_to_list(self):
        current = self.stack.currentWidget()
        if current != self.list_page:
            self.stack.setCurrentWidget(self.list_page)
            self.stack.removeWidget(current)
            current.deleteLater()
