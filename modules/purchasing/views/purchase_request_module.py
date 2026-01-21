"""
Akıllı İş - Satın Alma Talep Modülü
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QStackedWidget,
    QMessageBox,
    QDialog,
    QVBoxLayout as QVBox,
    QLabel,
    QTextEdit,
    QPushButton,
    QHBoxLayout,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
)
from PyQt6.QtCore import pyqtSignal, Qt

from .purchase_request_list import PurchaseRequestListPage
from .purchase_request_form import PurchaseRequestFormPage


class CreateOrderDialog(QDialog):
    """Talepten sipariş oluşturma dialogu"""

    def __init__(self, request_data: dict, suppliers: list, parent=None):
        super().__init__(parent)
        self.request_data = request_data
        self.suppliers = suppliers
        self.setWindowTitle(f"Sipariş Oluştur - {request_data.get('request_no', '')}")
        self.requestId = request_data.get("id")
        self.setMinimumSize(900, 650)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Başlık ve Bilgi
        header_widget = QWidget()
        header_widget.setProperty("class", "card")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("📦 Sipariş Oluştur")
        title.setProperty("class", "h2")
        header_layout.addWidget(title)

        desc = QLabel(
            "Onaylanan talep kalemleri için tedarikçi seçerek sipariş oluşturun."
        )
        desc.setProperty("class", "text-secondary")
        header_layout.addWidget(desc)

        # Tedarikçi Seçimi (Searchable ComboBox)
        form_layout = QHBoxLayout()
        form_layout.setSpacing(12)

        lbl = QLabel("Tedarikçi Seçimi:")
        lbl.setProperty("class", "form-label")
        form_layout.addWidget(lbl)

        self.supplier_combo = QComboBox()
        self.supplier_combo.setEditable(True)  # Arama için editable
        self.supplier_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.supplier_combo.addItem("Tedarikçi Ara...", None)

        for supplier in self.suppliers:
            self.supplier_combo.addItem(
                f"{supplier['code']} - {supplier['name']}", supplier["id"]
            )

        # Completer ayarı (Case insensitive arama)
        self.supplier_combo.completer().setCompletionMode(
            self.supplier_combo.completer().CompletionMode.PopupCompletion
        )
        self.supplier_combo.completer().setFilterMode(Qt.MatchFlag.MatchContains)

        form_layout.addWidget(self.supplier_combo, 1)
        header_layout.addLayout(form_layout)

        layout.addWidget(header_widget)

        # Kalemler Tablosu
        table_container = QWidget()
        table_container.setProperty("class", "card")
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(16, 16, 16, 16)
        table_layout.setSpacing(12)

        table_header = QLabel("Sipariş Kalemleri")
        table_header.setProperty("class", "h3")
        table_layout.addWidget(table_header)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels(
            ["Seç", "Ürün Kodu", "Ürün Adı", "Miktar", "Birim", "Önerilen Tedarikçi"]
        )

        # Tablo stil ayarları global temadan gelecek
        self.items_table.setProperty("class", "enhanced-table")
        self.items_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.items_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setAlternatingRowColors(True)

        # Checkbox column width
        self.items_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Fixed
        )
        self.items_table.setColumnWidth(0, 50)

        table_layout.addWidget(self.items_table)
        layout.addWidget(table_container)

        self._load_items()

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.setFixedSize(100, 40)
        cancel_btn.setProperty("class", "btn-secondary")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        create_btn = QPushButton("Sipariş Oluştur")
        create_btn.setFixedSize(140, 40)
        create_btn.setProperty("class", "btn-primary")
        create_btn.clicked.connect(self.accept)
        btn_layout.addWidget(create_btn)

        layout.addLayout(btn_layout)

    def _load_items(self):
        """Talep kalemlerini tabloya yükle"""
        items = self.request_data.get("items", [])
        self.items_table.setRowCount(len(items))

        for row, item in enumerate(items):
            # Seç checkbox
            check_item = QTableWidgetItem()
            check_item.setFlags(
                Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled
            )
            check_item.setCheckState(Qt.CheckState.Checked)
            check_item.setData(Qt.ItemDataRole.UserRole, item)
            self.items_table.setItem(row, 0, check_item)

            # Ürün bilgileri - Salt okunur
            def create_readonly_item(text):
                it = QTableWidgetItem(text)
                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                return it

            self.items_table.setItem(
                row, 1, create_readonly_item(item.get("item_code", ""))
            )
            self.items_table.setItem(
                row, 2, create_readonly_item(item.get("item_name", ""))
            )
            self.items_table.setItem(
                row, 3, create_readonly_item(str(item.get("quantity", 0)))
            )
            self.items_table.setItem(
                row, 4, create_readonly_item(item.get("unit_name", ""))
            )
            self.items_table.setItem(
                row, 5, create_readonly_item(item.get("suggested_supplier_name", "-"))
            )

            self.items_table.setRowHeight(row, 44)

    def get_selected_items(self) -> list:
        """Seçili kalemleri döndür"""
        selected = []
        for row in range(self.items_table.rowCount()):
            check_item = self.items_table.item(row, 0)
            if check_item and check_item.checkState() == Qt.CheckState.Checked:
                selected.append(check_item.data(Qt.ItemDataRole.UserRole))
        return selected

    def get_supplier_id(self) -> int:
        """Seçili tedarikçi ID'sini döndür"""
        # Editable combo olduğu için currentData() bazen çalışmayabilir,
        # emin olmak için index kontrolü yapalım
        idx = self.supplier_combo.currentIndex()
        if idx >= 0:
            return self.supplier_combo.itemData(idx)
        return None


class RejectReasonDialog(QDialog):
    """Red nedeni dialogu"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Red Nedeni")
        self.setMinimumWidth(400)
        layout = QVBox(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        label = QLabel("Lütfen red nedenini belirtin:")
        layout.addWidget(label)

        self.reason_input = QTextEdit()
        self.reason_input.setPlaceholderText("Red nedeni...")
        self.reason_input.setMinimumHeight(100)
        layout.addWidget(self.reason_input)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        confirm_btn = QPushButton("Reddet")
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
        self.list_page.create_order_clicked.connect(self._create_order_from_request)
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
                    PurchaseRequestService,
                    SupplierService,
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
                data.append(
                    {
                        "id": r.id,
                        "request_no": r.request_no,
                        "request_date": r.request_date,
                        "requested_by": r.requested_by,
                        "department": r.department,
                        "status": r.status.value if r.status else "draft",
                        "priority": r.priority,
                        "required_date": r.required_date,
                        "total_items": r.total_items,
                    }
                )
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
            return [
                {
                    "id": i.id,
                    "code": i.code,
                    "name": i.name,
                    "unit_id": i.unit_id,
                    "unit_name": i.unit.name if i.unit else "",
                    "stock": 0,  # TODO: Stok miktarı
                }
                for i in items
            ]
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

        form = PurchaseRequestFormPage(items=items, suppliers=suppliers, units=units)
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
                    items_data.append(
                        {
                            "id": item.id,
                            "item_id": item.item_id,
                            "quantity": item.quantity,
                            "unit_id": item.unit_id,
                            "estimated_price": item.estimated_price,
                            "suggested_supplier_id": item.suggested_supplier_id,
                        }
                    )

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
                    request_data=data, items=items, suppliers=suppliers, units=units
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
            self,
            "Onay",
            "Bu talebi onaylamak istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
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
                QMessageBox.warning(
                    self,
                    "Uyarı",
                    "Talep silinemedi! (Sadece taslak talepler silinebilir)",
                )
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")

    def _create_order_from_request(self, request_id: int):
        """Talepten sipariş oluştur"""
        if not self.service:
            return

        try:
            # Talep verilerini getir
            request = self.service.get_by_id(request_id)
            if not request:
                QMessageBox.warning(self, "Uyarı", "Talep bulunamadı!")
                return

            if request.status.value != "approved":
                QMessageBox.warning(
                    self,
                    "Uyarı",
                    "Sadece onaylanmış talepler için sipariş oluşturulabilir!",
                )
                return

            # Talep kalemlerini hazırla
            items_data = []
            for item in request.items:
                items_data.append(
                    {
                        "item_id": item.item_id,
                        "item_code": item.item.code if item.item else "",
                        "item_name": item.item.name if item.item else "",
                        "quantity": item.quantity,
                        "unit_id": item.unit_id,
                        "unit_name": item.unit.name if item.unit else "",
                        "estimated_price": item.estimated_price,
                        "suggested_supplier_id": item.suggested_supplier_id,
                        "suggested_supplier_name": (
                            item.suggested_supplier.name
                            if item.suggested_supplier
                            else "-"
                        ),
                    }
                )

            request_data = {
                "id": request.id,
                "request_no": request.request_no,
                "items": items_data,
            }

            # Dialog'u göster
            suppliers = self._get_suppliers()
            dialog = CreateOrderDialog(request_data, suppliers, self)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                supplier_id = dialog.get_supplier_id()
                if not supplier_id:
                    QMessageBox.warning(self, "Uyarı", "Lütfen bir tedarikçi seçin!")
                    return

                selected_items = dialog.get_selected_items()
                if not selected_items:
                    QMessageBox.warning(self, "Uyarı", "Lütfen en az bir kalem seçin!")
                    return

                # Sipariş oluştur
                from modules.purchasing.services import PurchaseOrderService

                order_service = PurchaseOrderService()

                order_items = []
                for item in selected_items:
                    order_items.append(
                        {
                            "item_id": item["item_id"],
                            "quantity": item["quantity"],
                            "unit_id": item["unit_id"],
                            "unit_price": item.get("estimated_price", 0),
                        }
                    )

                order = order_service.create_from_request(
                    request_id=request_id,
                    supplier_id=supplier_id,
                    items_data=order_items,
                )

                QMessageBox.information(
                    self,
                    "Başarılı",
                    f"Sipariş oluşturuldu!\nSipariş No: {order.order_no}",
                )
                self._load_data()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Sipariş oluşturma hatası: {e}")
            import traceback

            traceback.print_exc()

    def _back_to_list(self):
        current = self.stack.currentWidget()
        if current != self.list_page:
            self.stack.setCurrentWidget(self.list_page)
            self.stack.removeWidget(current)
            current.deleteLater()
