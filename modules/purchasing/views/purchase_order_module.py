"""
Akıllı İş - Satın Alma Sipariş Modülü
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget, QMessageBox,
    QDialog, QVBoxLayout as QVBox, QLabel, QHBoxLayout,
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QLineEdit
)
from PyQt6.QtCore import pyqtSignal, Qt

from .purchase_order_list import PurchaseOrderListPage
from .purchase_order_form import PurchaseOrderFormPage

class CreateReceiptDialog(QDialog):
    """Siparişten mal kabul oluşturma dialogu"""

    def __init__(self, order_data: dict, warehouses: list, parent=None):
        super().__init__(parent)
        self.order_data = order_data
        self.warehouses = warehouses
        self.setWindowTitle(f"Mal Kabul Oluştur - {order_data.get('order_no', '')}")
        self.setMinimumSize(900, 700)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBox(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Başlık
        title = QLabel("📥 Mal Kabul Oluştur")
        layout.addWidget(title)

        # Sipariş bilgileri
        info_label = QLabel(
            f"Sipariş: {self.order_data.get('order_no', '')} | "
            f"Tedarikçi: {self.order_data.get('supplier_name', '')}"
        )
        layout.addWidget(info_label)

        # Depo seçimi
        warehouse_layout = QHBoxLayout()
        warehouse_label = QLabel("Hedef Depo:")
        warehouse_layout.addWidget(warehouse_label)

        self.warehouse_combo = QComboBox()
        self.warehouse_combo.addItem("Depo Seçin...", None)
        for warehouse in self.warehouses:
            self.warehouse_combo.addItem(
                f"{warehouse['code']} - {warehouse['name']}", warehouse['id']
            )
        self.warehouse_combo.setStyleSheet(self._combo_style())
        warehouse_layout.addWidget(self.warehouse_combo, 1)
        layout.addLayout(warehouse_layout)

        # Kalemler tablosu
        items_label = QLabel("Sipariş Kalemleri:")
        layout.addWidget(items_label)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels([
            "Seç", "Ürün Kodu", "Ürün Adı", "Sipariş Miktarı",
            "Teslim Alınan", "Kabul Miktarı", "Birim"
        ])
        self.items_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.items_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.items_table.setStyleSheet(self._table_style())
        layout.addWidget(self.items_table)

        self._load_items()

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.setStyleSheet(self._button_style("#334155", "#475569"))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        create_btn = QPushButton("Mal Kabul Oluştur")
        create_btn.setStyleSheet(self._button_style("#8b5cf6", "#7c3aed"))
        create_btn.clicked.connect(self.accept)
        btn_layout.addWidget(create_btn)

        layout.addLayout(btn_layout)

    def _load_items(self):
        """Sipariş kalemlerini tabloya yükle"""
        items = self.order_data.get('items', [])
        self.items_table.setRowCount(len(items))

        for row, item in enumerate(items):
            # Seç checkbox (varsayılan seçili)
            check_item = QTableWidgetItem()
            check_item.setFlags(
                Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled
            )
            check_item.setCheckState(Qt.CheckState.Checked)
            check_item.setData(Qt.ItemDataRole.UserRole, item)
            self.items_table.setItem(row, 0, check_item)

            # Ürün bilgileri
            self.items_table.setItem(row, 1, QTableWidgetItem(item.get('item_code', '')))
            self.items_table.setItem(row, 2, QTableWidgetItem(item.get('item_name', '')))
            self.items_table.setItem(
                row, 3, QTableWidgetItem(str(item.get('quantity', 0)))
            )
            self.items_table.setItem(
                row, 4, QTableWidgetItem(str(item.get('received_quantity', 0)))
            )

            # Kabul miktarı (editable)
            remaining = float(item.get('quantity', 0)) - float(
                item.get('received_quantity', 0)
            )
            qty_input = QLineEdit(str(remaining if remaining > 0 else 0))
            self.items_table.setCellWidget(row, 5, qty_input)

            self.items_table.setItem(row, 6, QTableWidgetItem(item.get('unit_name', '')))

    def get_selected_items(self) -> list:
        """Seçili kalemleri ve kabul miktarlarını döndür"""
        selected = []
        for row in range(self.items_table.rowCount()):
            check_item = self.items_table.item(row, 0)
            if check_item and check_item.checkState() == Qt.CheckState.Checked:
                item_data = check_item.data(Qt.ItemDataRole.UserRole)
                qty_widget = self.items_table.cellWidget(row, 5)
                if qty_widget:
                    try:
                        accepted_qty = float(qty_widget.text() or 0)
                        if accepted_qty > 0:
                            item_data['accepted_quantity'] = accepted_qty
                            selected.append(item_data)
                    except ValueError:
                        pass
        return selected

    def get_warehouse_id(self) -> int:
        """Seçili depo ID'sini döndür"""
        return self.warehouse_combo.currentData()

    def _combo_style(self):
        return """
            QComboBox {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
                color: #f8fafc;
                font-size: 14px;
            }
            QComboBox:focus { border-color: #6366f1; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #0f172a;
                border: 1px solid #334155;
                selection-background-color: #6366f1;
                color: #f8fafc;
            }
        """

    def _table_style(self):
        return """
            QTableWidget {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #f8fafc;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #f8fafc;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item { padding: 8px; }
        """

    def _button_style(self, bg_color, hover_color):
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {hover_color}; }}
        """

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
        self.list_page.create_receipt_clicked.connect(self._create_receipt_from_order)
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
                
    def _create_receipt_from_order(self, order_id: int):
        """Siparişten mal kabul oluştur"""
        if not self.service:
            return

        try:
            # Sipariş verilerini getir
            order = self.service.get_by_id(order_id)
            if not order:
                QMessageBox.warning(self, "Uyarı", "Sipariş bulunamadı!")
                return

            if order.status.value not in ["sent", "confirmed", "partial"]:
                QMessageBox.warning(
                    self, "Uyarı",
                    "Sadece gönderilmiş, onaylanmış veya kısmi teslim edilmiş "
                    "siparişler için mal kabul oluşturulabilir!"
                )
                return

            # Sipariş kalemlerini hazırla
            items_data = []
            for item in order.items:
                items_data.append({
                    'po_item_id': item.id,
                    'item_id': item.item_id,
                    'item_code': item.item.code if item.item else '',
                    'item_name': item.item.name if item.item else '',
                    'quantity': item.quantity,
                    'received_quantity': item.received_quantity or 0,
                    'unit_id': item.unit_id,
                    'unit_name': item.unit.name if item.unit else '',
                    'unit_price': item.unit_price,
                })

            order_data = {
                'id': order.id,
                'order_no': order.order_no,
                'supplier_name': order.supplier.name if order.supplier else '',
                'items': items_data,
            }

            # Dialog'u göster
            warehouses = self._get_warehouses()
            dialog = CreateReceiptDialog(order_data, warehouses, self)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                warehouse_id = dialog.get_warehouse_id()
                if not warehouse_id:
                    QMessageBox.warning(self, "Uyarı", "Lütfen bir depo seçin!")
                    return

                selected_items = dialog.get_selected_items()
                if not selected_items:
                    QMessageBox.warning(self, "Uyarı", "Lütfen en az bir kalem seçin!")
                    return

                # Mal kabul oluştur
                from modules.purchasing.services import GoodsReceiptService
                receipt_service = GoodsReceiptService()

                receipt_items = []
                for item in selected_items:
                    receipt_items.append({
                        'po_item_id': item.get('po_item_id'),
                        'item_id': item['item_id'],
                        'quantity': item['quantity'],
                        'accepted_quantity': item.get('accepted_quantity', 0),
                        'unit_id': item['unit_id'],
                    })

                receipt = receipt_service.create_from_order(
                    order_id=order_id,
                    warehouse_id=warehouse_id,
                    items_data=receipt_items
                )

                QMessageBox.information(
                    self,
                    "Başarılı",
                    f"Mal kabul oluşturuldu!\nMal Kabul No: {receipt.receipt_no}"
                )
                self._load_data()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Mal kabul oluşturma hatası: {e}")
            import traceback
            traceback.print_exc()
            
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
