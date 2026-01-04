"""
Akıllı İş - Mal Kabul Modülü
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QMessageBox
from PyQt6.QtCore import pyqtSignal

from .goods_receipt_list import GoodsReceiptListPage
from .goods_receipt_form import GoodsReceiptFormPage


class GoodsReceiptModule(QWidget):
    """Mal kabul modülü"""
    
    page_title = "Mal Kabul"
    
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
        self.list_page = GoodsReceiptListPage()
        self.list_page.add_clicked.connect(self._show_add_form)
        self.list_page.add_from_order_clicked.connect(self._show_order_selector)
        self.list_page.edit_clicked.connect(self._show_edit_form)
        self.list_page.delete_clicked.connect(self._delete_receipt)
        self.list_page.view_clicked.connect(self._show_view)
        self.list_page.complete_clicked.connect(self._complete_receipt)
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
                    GoodsReceiptService, SupplierService
                )
                self.service = GoodsReceiptService()
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
            receipts = self.service.get_all()
            data = []
            for r in receipts:
                data.append({
                    "id": r.id,
                    "receipt_no": r.receipt_no,
                    "receipt_date": r.receipt_date,
                    "supplier_name": r.supplier.name if r.supplier else "",
                    "order_no": r.purchase_order.order_no if r.purchase_order else "",
                    "warehouse_name": r.warehouse.name if r.warehouse else "",
                    "status": r.status.value if r.status else "draft",
                    "total_items": r.total_items,
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
            return [{"id": s.id, "code": s.code, "name": s.name} for s in suppliers]
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
        """Manuel mal kabul formu"""
        suppliers = self._get_suppliers()
        warehouses = self._get_warehouses()
        items = self._get_items()
        
        form = GoodsReceiptFormPage(
            suppliers=suppliers,
            warehouses=warehouses,
            items=items
        )
        form.saved.connect(self._save_receipt)
        form.cancelled.connect(self._back_to_list)
        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)
        
    def _show_order_selector(self):
        """Siparişten mal kabul - şimdilik bilgi mesajı"""
        QMessageBox.information(
            self, "Bilgi",
            "Siparişten mal kabul özelliği için önce Satın Alma Siparişleri modülü tamamlanmalıdır.\n\n"
            "Şimdilik manuel giriş yapabilirsiniz."
        )
        
    def _show_edit_form(self, receipt_id: int):
        if not self.service:
            return
            
        try:
            receipt = self.service.get_by_id(receipt_id)
            if receipt:
                items_data = []
                for item in receipt.items:
                    items_data.append({
                        "id": item.id,
                        "item_id": item.item_id,
                        "quantity": item.quantity,
                        "unit_id": item.unit_id,
                        "accepted_quantity": item.accepted_quantity,
                        "rejected_quantity": item.rejected_quantity,
                        "lot_number": item.lot_number,
                    })
                
                data = {
                    "id": receipt.id,
                    "receipt_no": receipt.receipt_no,
                    "receipt_date": receipt.receipt_date,
                    "supplier_id": receipt.supplier_id,
                    "warehouse_id": receipt.warehouse_id,
                    "supplier_invoice_no": receipt.supplier_invoice_no,
                    "supplier_delivery_no": receipt.supplier_delivery_no,
                    "notes": receipt.notes,
                    "status": receipt.status.value if receipt.status else "draft",
                    "items": items_data,
                }
                
                suppliers = self._get_suppliers()
                warehouses = self._get_warehouses()
                items = self._get_items()
                
                form = GoodsReceiptFormPage(
                    receipt_data=data,
                    suppliers=suppliers,
                    warehouses=warehouses,
                    items=items
                )
                form.saved.connect(self._save_receipt)
                form.cancelled.connect(self._back_to_list)
                self.stack.addWidget(form)
                self.stack.setCurrentWidget(form)
                
        except Exception as e:
            print(f"Düzenleme hatası: {e}")
            import traceback
            traceback.print_exc()
            
    def _show_view(self, receipt_id: int):
        self._show_edit_form(receipt_id)
        
    def _save_receipt(self, data: dict):
        if not self.service:
            return
            
        try:
            receipt_id = data.pop("id", None)
            items_data = data.pop("items", [])
            
            if receipt_id:
                # Güncelleme - items_data'yı ayrı parametre olarak gönder
                self._update_receipt(receipt_id, items_data, data)
                QMessageBox.information(self, "Başarılı", "Mal kabul güncellendi!")
            else:
                self.service.create(items_data, **data)
                QMessageBox.information(self, "Başarılı", "Yeni mal kabul oluşturuldu!")
            
            self._back_to_list()
            self._load_data()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {e}")
            import traceback
            traceback.print_exc()
            
    def _update_receipt(self, receipt_id: int, items_data: list, data: dict):
        """Mal kabul güncelle"""
        from database.base import get_session
        from database.models.purchasing import GoodsReceipt, GoodsReceiptItem
        
        session = get_session()
        try:
            receipt = session.query(GoodsReceipt).filter(GoodsReceipt.id == receipt_id).first()
            if not receipt:
                raise ValueError("Mal kabul bulunamadı")
            
            # Temel bilgileri güncelle
            for key, value in data.items():
                if hasattr(receipt, key):
                    setattr(receipt, key, value)
            
            # Mevcut kalemleri sil
            for item in receipt.items:
                session.delete(item)
            
            # Yeni kalemleri ekle
            for item_data in items_data:
                item = GoodsReceiptItem(receipt_id=receipt.id, **item_data)
                session.add(item)
            
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
            
    def _complete_receipt(self, receipt_id: int):
        """Mal kabul tamamla ve stok girişi yap"""
        if not self.service:
            return
            
        reply = QMessageBox.question(
            self, "Tamamla",
            "Bu mal kabul fişini tamamlamak istediğinize emin misiniz?\n\n"
            "Bu işlem stok girişi yapacak ve geri alınamaz.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                result = self.service.complete(receipt_id)
                if result:
                    QMessageBox.information(
                        self, "Başarılı",
                        "Mal kabul tamamlandı ve stok girişi yapıldı!"
                    )
                    self._load_data()
                else:
                    QMessageBox.warning(self, "Uyarı", "İşlem başarısız!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Hata: {e}")
                import traceback
                traceback.print_exc()
            
    def _delete_receipt(self, receipt_id: int):
        if not self.service:
            return
            
        try:
            if self.service.delete(receipt_id):
                QMessageBox.information(self, "Başarılı", "Mal kabul silindi!")
                self._load_data()
            else:
                QMessageBox.warning(self, "Uyarı", "Silinemedi! (Sadece taslak fişler silinebilir)")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")
            
    def _back_to_list(self):
        current = self.stack.currentWidget()
        if current != self.list_page:
            self.stack.setCurrentWidget(self.list_page)
            self.stack.removeWidget(current)
            current.deleteLater()
