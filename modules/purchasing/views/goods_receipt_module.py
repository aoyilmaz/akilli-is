"""
Akıllı İş - Mal Kabul Modülü
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget, QMessageBox,
    QDialog, QVBoxLayout as QVBox, QLabel, QHBoxLayout,
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QLineEdit
)
from PyQt6.QtCore import pyqtSignal, Qt

from .goods_receipt_list import GoodsReceiptListPage
from .goods_receipt_form import GoodsReceiptFormPage
from .purchase_order_module import CreateReceiptDialog


class OrderSelectorDialog(QDialog):
    """Sipariş seçim dialogu"""

    def __init__(self, orders: list, parent=None):
        super().__init__(parent)
        self.orders = orders
        self.selected_order_id = None
        self.setWindowTitle("Sipariş Seç")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("QDialog { background-color: #1e293b; }")

        self.setup_ui()

    def setup_ui(self):
        layout = QVBox(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Başlık
        title = QLabel("📦 Sipariş Seçin")
        title.setStyleSheet("color: #f8fafc; font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        info_label = QLabel("Mal kabul oluşturmak için bir sipariş seçin:")
        info_label.setStyleSheet("color: #94a3b8; font-size: 14px;")
        layout.addWidget(info_label)

        # Siparişler tablosu
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(6)
        self.orders_table.setHorizontalHeaderLabels([
            "Seç", "Sipariş No", "Tarih", "Tedarikçi", "Durum", "Toplam"
        ])
        self.orders_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.orders_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.orders_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.orders_table.setStyleSheet(self._table_style())
        layout.addWidget(self.orders_table)

        self._load_orders()

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.setStyleSheet(self._button_style("#334155", "#475569"))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        select_btn = QPushButton("Seçili Siparişten Mal Kabul Oluştur")
        select_btn.setStyleSheet(self._button_style("#8b5cf6", "#7c3aed"))
        select_btn.clicked.connect(self._on_select)
        btn_layout.addWidget(select_btn)

        layout.addLayout(btn_layout)

    def _load_orders(self):
        """Siparişleri tabloya yükle"""
        self.orders_table.setRowCount(len(self.orders))

        status_labels = {
            "sent": "📤 Gönderildi",
            "confirmed": "✅ Onaylandı",
            "partial": "🟡 Kısmi Teslim",
        }

        for row, order in enumerate(self.orders):
            # Seç radio button
            check_item = QTableWidgetItem()
            check_item.setFlags(
                Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled
            )
            check_item.setCheckState(Qt.CheckState.Unchecked)
            check_item.setData(Qt.ItemDataRole.UserRole, order['id'])
            self.orders_table.setItem(row, 0, check_item)

            # Sipariş bilgileri
            self.orders_table.setItem(
                row, 1, QTableWidgetItem(order.get('order_no', ''))
            )
            self.orders_table.setItem(
                row, 2, QTableWidgetItem(
                    order.get('order_date').strftime('%d.%m.%Y')
                    if order.get('order_date') else '-'
                )
            )
            self.orders_table.setItem(
                row, 3, QTableWidgetItem(order.get('supplier_name', ''))
            )

            status = order.get('status', 'draft')
            status_text = status_labels.get(status, status)
            self.orders_table.setItem(row, 4, QTableWidgetItem(status_text))

            total = order.get('total', 0) or 0
            currency = order.get('currency', 'TRY')
            symbol = {"TRY": "₺", "USD": "$", "EUR": "€"}.get(currency, "₺")
            self.orders_table.setItem(
                row, 5, QTableWidgetItem(f"{symbol}{float(total):,.2f}")
            )

    def _on_select(self):
        """Seçili siparişi al"""
        for row in range(self.orders_table.rowCount()):
            check_item = self.orders_table.item(row, 0)
            if check_item and check_item.checkState() == Qt.CheckState.Checked:
                self.selected_order_id = check_item.data(Qt.ItemDataRole.UserRole)
                self.accept()
                return

        QMessageBox.warning(self, "Uyarı", "Lütfen bir sipariş seçin!")

    def get_selected_order_id(self) -> int:
        """Seçili sipariş ID'sini döndür"""
        return self.selected_order_id

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
        """Siparişten mal kabul oluştur"""
        try:
            # Açık siparişleri getir
            from modules.purchasing.services import PurchaseOrderService
            order_service = PurchaseOrderService()

            # Sadece gönderilmiş, onaylanmış veya kısmi teslim edilmiş siparişler
            all_orders = order_service.get_all()
            open_orders = [
                o for o in all_orders
                if o.status.value in ["sent", "confirmed", "partial"]
            ]

            if not open_orders:
                QMessageBox.information(
                    self, "Bilgi",
                    "Mal kabul oluşturmak için uygun sipariş bulunamadı.\n\n"
                    "Siparişlerin durumu: Gönderildi, Onaylandı veya Kısmi Teslim olmalıdır."
                )
                return

            # Sipariş listesini hazırla
            orders_data = []
            for o in open_orders:
                orders_data.append({
                    'id': o.id,
                    'order_no': o.order_no,
                    'order_date': o.order_date,
                    'supplier_name': o.supplier.name if o.supplier else '',
                    'status': o.status.value if o.status else 'draft',
                    'total': o.total,
                    'currency': o.currency.value if o.currency else 'TRY',
                })

            # Sipariş seçim dialog'unu göster
            selector_dialog = OrderSelectorDialog(orders_data, self)

            if selector_dialog.exec() == QDialog.DialogCode.Accepted:
                selected_order_id = selector_dialog.get_selected_order_id()
                if not selected_order_id:
                    return

                # Seçili siparişi getir
                order = order_service.get_by_id(selected_order_id)
                if not order:
                    QMessageBox.warning(self, "Uyarı", "Sipariş bulunamadı!")
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
                    })

                order_data = {
                    'id': order.id,
                    'order_no': order.order_no,
                    'supplier_name': order.supplier.name if order.supplier else '',
                    'items': items_data,
                }

                # Mal kabul dialog'unu göster
                warehouses = self._get_warehouses()
                receipt_dialog = CreateReceiptDialog(order_data, warehouses, self)

                if receipt_dialog.exec() == QDialog.DialogCode.Accepted:
                    warehouse_id = receipt_dialog.get_warehouse_id()
                    if not warehouse_id:
                        QMessageBox.warning(self, "Uyarı", "Lütfen bir depo seçin!")
                        return

                    selected_items = receipt_dialog.get_selected_items()
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
                        order_id=order.id,
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
