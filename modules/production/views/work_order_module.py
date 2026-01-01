"""
Akıllı İş - İş Emirleri Modülü
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QMessageBox

from .work_order_list import WorkOrderListPage
from .work_order_form import WorkOrderFormPage


class WorkOrderModule(QWidget):
    """İş Emirleri modülü"""
    
    page_title = "İş Emirleri"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.wo_service = None
        self.bom_service = None
        self.item_service = None
        self.warehouse_service = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        
        # Liste sayfası
        self.list_page = WorkOrderListPage()
        self.list_page.new_clicked.connect(self._show_new_form)
        self.list_page.edit_clicked.connect(self._show_edit_form)
        self.list_page.view_clicked.connect(self._show_edit_form)
        self.list_page.delete_clicked.connect(self._delete_work_order)
        self.list_page.status_change_requested.connect(self._change_status)
        self.list_page.refresh_requested.connect(self._load_data)
        self.stack.addWidget(self.list_page)
        
        layout.addWidget(self.stack)
        
    def showEvent(self, event):
        super().showEvent(event)
        self._ensure_services()
        self._load_data()
        
    def _ensure_services(self):
        """Servisleri yükle"""
        if not self.wo_service:
            try:
                from modules.production.services import WorkOrderService, BOMService
                from modules.inventory.services import ItemService, WarehouseService
                self.wo_service = WorkOrderService()
                self.bom_service = BOMService()
                self.item_service = ItemService()
                self.warehouse_service = WarehouseService()
            except Exception as e:
                print(f"Servis yükleme hatası: {e}")
                
    def _load_data(self):
        """Verileri yükle"""
        if not self.wo_service:
            return
            
        try:
            status_filter = self.list_page.get_status_filter()
            
            from database.models.production import WorkOrderStatus
            status = WorkOrderStatus(status_filter) if status_filter else None
            
            work_orders = self.wo_service.get_all(status=status)
            
            wo_list = []
            for wo in work_orders:
                wo_list.append({
                    "id": wo.id,
                    "order_no": wo.order_no,
                    "item_name": wo.item.name if wo.item else "-",
                    "planned_quantity": float(wo.planned_quantity or 0),
                    "completed_quantity": float(wo.completed_quantity or 0),
                    "planned_start": wo.planned_start,
                    "planned_end": wo.planned_end,
                    "progress_rate": float(wo.progress_rate or 0),
                    "priority": wo.priority.value if wo.priority else "normal",
                    "status": wo.status.value if wo.status else "draft",
                })
            
            self.list_page.load_data(wo_list)
            
        except Exception as e:
            print(f"Veri yükleme hatası: {e}")
            self.list_page.load_data([])
            
    def _show_new_form(self):
        """Yeni iş emri formu göster"""
        self._ensure_services()
        
        form = WorkOrderFormPage()
        form.saved.connect(self._save_work_order)
        form.cancelled.connect(self._show_list)
        form.order_no_requested.connect(lambda: self._generate_order_no(form))
        form.bom_selected.connect(lambda item_id: self._load_boms_for_product(form, item_id))
        
        self._load_form_data(form)
        self._generate_order_no(form)
        
        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)
        
    def _show_edit_form(self, wo_id: int):
        """Düzenleme formu göster"""
        self._ensure_services()
        
        wo = self.wo_service.get_by_id(wo_id)
        if not wo:
            QMessageBox.warning(self, "Hata", "İş emri bulunamadı!")
            return
        
        wo_data = {
            "id": wo.id,
            "order_no": wo.order_no,
            "description": wo.description,
            "item_id": wo.item_id,
            "bom_id": wo.bom_id,
            "planned_quantity": float(wo.planned_quantity or 1),
            "priority": wo.priority.value if wo.priority else "normal",
            "source_warehouse_id": wo.source_warehouse_id,
            "target_warehouse_id": wo.target_warehouse_id,
            "planned_start": wo.planned_start,
            "planned_end": wo.planned_end,
            "status": wo.status.value if wo.status else "draft",
        }
        
        form = WorkOrderFormPage(wo_data)
        form.saved.connect(self._save_work_order)
        form.cancelled.connect(self._show_list)
        form.bom_selected.connect(lambda item_id: self._load_boms_for_product(form, item_id))
        
        self._load_form_data(form)
        
        # Seçimleri ayarla
        for i in range(form.product_combo.count()):
            if form.product_combo.itemData(i) == wo.item_id:
                form.product_combo.setCurrentIndex(i)
                break
        
        self._load_boms_for_product(form, wo.item_id)
        for i in range(form.bom_combo.count()):
            if form.bom_combo.itemData(i) == wo.bom_id:
                form.bom_combo.setCurrentIndex(i)
                break
        
        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)
        
    def _load_form_data(self, form: WorkOrderFormPage):
        """Form verilerini yükle"""
        try:
            # Mamul ürünleri
            products = self.item_service.get_all()
            mamul_products = [p for p in products if p.item_type and p.item_type.value == "mamul"]
            form.set_products(mamul_products if mamul_products else products)
            
            # Depolar
            warehouses = self.warehouse_service.get_all()
            form.set_warehouses(warehouses)
            
        except Exception as e:
            print(f"Form veri yükleme hatası: {e}")
            
    def _load_boms_for_product(self, form: WorkOrderFormPage, item_id: int):
        """Mamule ait reçeteleri yükle"""
        try:
            boms = self.bom_service.get_by_item(item_id, active_only=False)
            form.set_boms_for_product(boms)
            
            # İlk aktif reçeteyi seç ve malzemeleri yükle
            if boms:
                active_boms = [b for b in boms if b.status.value == "active"]
                if active_boms:
                    self._load_bom_materials(form, active_boms[0])
                    for i in range(form.bom_combo.count()):
                        if form.bom_combo.itemData(i) == active_boms[0].id:
                            form.bom_combo.setCurrentIndex(i)
                            break
                            
        except Exception as e:
            print(f"Reçete yükleme hatası: {e}")
            
    def _load_bom_materials(self, form: WorkOrderFormPage, bom):
        """Reçete malzemelerini yükle"""
        try:
            materials = []
            for line in bom.lines:
                # Stok bilgisini al
                stock = 0
                try:
                    balances = self.item_service.session.execute(
                        f"SELECT COALESCE(SUM(quantity), 0) FROM stock_balances WHERE item_id = {line.item_id}"
                    ).scalar() or 0
                    stock = float(balances)
                except:
                    stock = 0
                
                materials.append({
                    "item_id": line.item_id,
                    "item_code": line.item.code if line.item else "",
                    "item_name": line.item.name if line.item else "",
                    "quantity": line.effective_quantity,
                    "unit_code": line.unit.code if line.unit else "ADET",
                    "unit_cost": float(line.item.purchase_price or 0) if line.item else 0,
                    "stock": stock,
                })
            
            form.set_bom_materials(materials)
            
        except Exception as e:
            print(f"Malzeme yükleme hatası: {e}")
            
    def _generate_order_no(self, form: WorkOrderFormPage):
        """Otomatik iş emri numarası üret"""
        try:
            order_no = self.wo_service.generate_order_no()
            form.set_generated_order_no(order_no)
        except Exception as e:
            print(f"Numara üretme hatası: {e}")
            
    def _save_work_order(self, data: dict):
        """İş emrini kaydet"""
        try:
            wo_id = data.pop("id", None)
            
            # Priority'yi enum'a dönüştür
            from database.models.production import WorkOrderPriority
            priority_val = data.get("priority", "normal")
            data["priority"] = WorkOrderPriority(priority_val)
            
            if wo_id:
                self.wo_service.update(wo_id, **data)
                QMessageBox.information(self, "Başarılı", "İş emri güncellendi!")
            else:
                self.wo_service.create(**data)
                QMessageBox.information(self, "Başarılı", "İş emri oluşturuldu!")
            
            self._show_list()
            self._load_data()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası: {str(e)}")
            
    def _change_status(self, wo_id: int, new_status: str):
        """İş emri durumunu değiştir"""
        try:
            from database.models.production import WorkOrderStatus
            status = WorkOrderStatus(new_status)
            self.wo_service.change_status(wo_id, status)
            
            status_names = {
                "planned": "planlandı",
                "released": "serbest bırakıldı",
                "in_progress": "üretime başlandı",
                "completed": "tamamlandı",
                "closed": "kapatıldı",
            }
            QMessageBox.information(self, "Başarılı", f"İş emri {status_names.get(new_status, 'güncellendi')}!")
            self._load_data()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Durum değişikliği hatası: {str(e)}")
            
    def _delete_work_order(self, wo_id: int):
        """İş emrini sil"""
        try:
            if self.wo_service.delete(wo_id):
                QMessageBox.information(self, "Başarılı", "İş emri silindi!")
                self._load_data()
            else:
                QMessageBox.warning(self, "Uyarı", "İş emri silinemedi! Sadece taslak durumundaki emirler silinebilir.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Silme hatası: {str(e)}")
            
    def _show_list(self):
        """Liste sayfasına dön"""
        current = self.stack.currentWidget()
        if current != self.list_page:
            self.stack.removeWidget(current)
            current.deleteLater()
        
        self.stack.setCurrentWidget(self.list_page)
