"""
Akıllı İş - Stok Sayımı Modülü
"""

from datetime import datetime
from decimal import Decimal
from PyQt6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QMessageBox

from modules.inventory.services import ItemService, WarehouseService, CategoryService, StockMovementService
from modules.inventory.views.stock_count_list import StockCountListPage
from modules.inventory.views.stock_count_form import StockCountFormPage
from database.models import StockMovementType

class StockCountModule(QWidget):
    """Stok sayımı modülü"""
    
    page_title = "Stok Sayımı"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.item_service = None
        self.warehouse_service = None
        self.category_service = None
        self.movement_service = None
        
        # Geçici sayım verileri (normalde veritabanında olur)
        self.counts = []
        self.next_count_id = 1
        
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        
        # Liste sayfası
        self.list_page = StockCountListPage()
        self.list_page.new_count_clicked.connect(self.show_new_form)
        self.list_page.edit_clicked.connect(self.show_edit_form)
        self.list_page.view_clicked.connect(self.show_view_form)
        self.list_page.delete_clicked.connect(self.delete_count)
        self.list_page.apply_clicked.connect(self.apply_count)
        self.list_page.refresh_requested.connect(self.load_data)
        self.stack.addWidget(self.list_page)
        
        layout.addWidget(self.stack)
        
    def _get_services(self):
        if self.item_service is None:
            self.item_service = ItemService()
        if self.warehouse_service is None:
            self.warehouse_service = WarehouseService()
        if self.category_service is None:
            self.category_service = CategoryService()
        if self.movement_service is None:
            self.movement_service = StockMovementService()
            
    def _close_services(self):
        if self.item_service:
            self.item_service.close()
            self.item_service = None
        if self.warehouse_service:
            self.warehouse_service.close()
            self.warehouse_service = None
        if self.category_service:
            self.category_service.close()
            self.category_service = None
        if self.movement_service:
            self.movement_service.close()
            self.movement_service = None
            
    def load_data(self):
        """Sayım listesini yükle"""
        status_filter = self.list_page.get_status_filter()
        
        # Filtrelenmiş sayımlar
        filtered = self.counts
        if status_filter:
            filtered = [c for c in self.counts if c.get("status") == status_filter]
        
        self.list_page.load_data(filtered)
        
    def show_new_form(self):
        """Yeni sayım formu"""
        self._show_form(None)
        
    def show_edit_form(self, count_id: int):
        """Düzenleme formu"""
        count_data = next((c for c in self.counts if c.get("id") == count_id), None)
        if count_data:
            self._show_form(count_data)
        else:
            QMessageBox.warning(self, "Uyarı", "Sayım bulunamadı!")
            
    def show_view_form(self, count_id: int):
        """Görüntüleme (şimdilik düzenleme ile aynı)"""
        self.show_edit_form(count_id)
        
    def _show_form(self, count_data):
        """Form göster"""
        try:
            self._get_services()
            
            if self.stack.count() > 1:
                old = self.stack.widget(1)
                self.stack.removeWidget(old)
                old.deleteLater()
            
            form = StockCountFormPage(count_data)
            form.saved.connect(self.save_count)
            form.completed.connect(self.complete_count)
            form.cancelled.connect(self.show_list)
            
            # Depoları yükle
            warehouses = self.warehouse_service.get_all()
            form.load_warehouses(warehouses)
            
            # Kategorileri yükle
            categories = self.category_service.get_all()
            form.load_categories(categories)
            
            # Stok kartlarını yükle
            items = self.item_service.get_all()
            form.set_items_data(items)
            
            self.stack.addWidget(form)
            self.stack.setCurrentIndex(1)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Form açılırken hata:\n{str(e)}")
        finally:
            self._close_services()
            
    def show_list(self):
        self.stack.setCurrentIndex(0)
        self.load_data()
        
    def save_count(self, data: dict):
        """Sayımı kaydet (taslak)"""
        try:
            # ID varsa güncelle, yoksa yeni oluştur
            existing = next((c for c in self.counts if c.get("id") == data.get("id")), None)
            
            if existing:
                existing.update(data)
                QMessageBox.information(self, "Başarılı", "Sayım güncellendi!")
            else:
                data["id"] = self.next_count_id
                data["count_no"] = data.get("count_no") or f"SYM{self.next_count_id:06d}"
                data["status"] = data.get("status", "draft")
                data["item_count"] = len(data.get("lines", []))
                data["counted_items"] = sum(1 for l in data.get("lines", []) if l.get("counted_quantity") is not None)
                data["difference_amount"] = self._calc_difference(data.get("lines", []))
                
                # Depo adını ekle
                self._get_services()
                wh = self.warehouse_service.get_by_id(data.get("warehouse_id"))
                data["warehouse_name"] = wh.name if wh else "-"
                self._close_services()
                
                self.counts.append(data)
                self.next_count_id += 1
                QMessageBox.information(self, "Başarılı", "Sayım kaydedildi!")
            
            self.show_list()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası:\n{str(e)}")
            
    def complete_count(self, data: dict):
        """Sayımı tamamla"""
        data["status"] = "completed"
        self.save_count(data)
        
    def delete_count(self, count_id: int):
        """Sayımı sil"""
        self.counts = [c for c in self.counts if c.get("id") != count_id]
        QMessageBox.information(self, "Başarılı", "Sayım silindi!")
        self.load_data()
        
    def apply_count(self, count_id: int):
        """Sayım farklarını stoklara uygula"""
        count_data = next((c for c in self.counts if c.get("id") == count_id), None)
        if not count_data:
            return
        
        try:
            self._get_services()
            
            warehouse_id = count_data.get("warehouse_id")
            lines = count_data.get("lines", [])
            
            applied_count = 0
            
            for line in lines:
                if line.get("counted_quantity") is None:
                    continue
                
                system_qty = line.get("system_quantity", Decimal(0))
                counted_qty = line.get("counted_quantity", Decimal(0))
                diff = counted_qty - system_qty
                
                if diff == 0:
                    continue
                
                item_id = line.get("item_id")
                unit_cost = line.get("unit_cost", Decimal(0))
                
                if diff > 0:
                    # Sayım fazlası - giriş yap
                    self.movement_service.create_movement(
                        item_id=item_id,
                        movement_type=StockMovementType.SAYIM_FAZLA,
                        quantity=abs(diff),
                        to_warehouse_id=warehouse_id,
                        unit_price=unit_cost,
                        document_no=count_data.get("count_no"),
                        document_type="stock_count",
                        description=f"Sayım fazlası: {line.get('note', '')}",
                    )
                else:
                    # Sayım eksiği - çıkış yap
                    self.movement_service.create_movement(
                        item_id=item_id,
                        movement_type=StockMovementType.SAYIM_EKSIK,
                        quantity=abs(diff),
                        from_warehouse_id=warehouse_id,
                        unit_price=unit_cost,
                        document_no=count_data.get("count_no"),
                        document_type="stock_count",
                        description=f"Sayım eksiği: {line.get('note', '')}",
                    )
                
                applied_count += 1
            
            # Durumu güncelle
            count_data["status"] = "applied"
            
            QMessageBox.information(
                self, "Başarılı", 
                f"Sayım farkları stoklara uygulandı!\n{applied_count} hareket oluşturuldu."
            )
            self.load_data()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Uygulama hatası:\n{str(e)}")
        finally:
            self._close_services()
            
    def _calc_difference(self, lines: list) -> float:
        """Fark tutarını hesapla"""
        total = Decimal(0)
        for line in lines:
            if line.get("counted_quantity") is not None:
                diff = line.get("counted_quantity", Decimal(0)) - line.get("system_quantity", Decimal(0))
                total += diff * line.get("unit_cost", Decimal(0))
        return float(total)
