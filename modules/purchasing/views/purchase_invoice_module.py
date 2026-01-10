"""
Akıllı İş - Satınalma Faturası Modülü
"""

from decimal import Decimal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QStackedWidget,
    QMessageBox,
    QDialog,
    QVBoxLayout as QVBox,
    QLabel,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QDoubleSpinBox,
    QLineEdit,
)
from PyQt6.QtCore import Qt

from .purchase_invoice_list import PurchaseInvoiceListPage
from .purchase_invoice_form import PurchaseInvoiceFormPage


class ReceiptSelectorDialog(QDialog):
    """Mal kabul seçim dialogu"""

    def __init__(self, receipts: list, parent=None):
        super().__init__(parent)
        self.receipts = receipts
        self.selected_receipt_id = None
        self.setWindowTitle("Mal Kabul Seç")
        self.setMinimumSize(800, 500)
        self.setStyleSheet("QDialog { background-color: #1e293b; }")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBox(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("📦 Mal Kabul Seçin")
        title.setStyleSheet("color: #f8fafc; font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        info_label = QLabel("Fatura oluşturmak için tamamlanmış bir mal kabul seçin:")
        info_label.setStyleSheet("color: #94a3b8; font-size: 14px;")
        layout.addWidget(info_label)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Seç", "Fiş No", "Tarih", "Tedarikçi", "Kalem"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setStyleSheet(self._table_style())
        layout.addWidget(self.table)

        self._load_receipts()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.setStyleSheet(self._button_style("#334155", "#475569"))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        select_btn = QPushButton("Seçili Mal Kabulden Fatura Oluştur")
        select_btn.setStyleSheet(self._button_style("#8b5cf6", "#7c3aed"))
        select_btn.clicked.connect(self._on_select)
        btn_layout.addWidget(select_btn)

        layout.addLayout(btn_layout)

    def _load_receipts(self):
        self.table.setRowCount(len(self.receipts))

        for row, rec in enumerate(self.receipts):
            check_item = QTableWidgetItem()
            check_item.setFlags(
                Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled
            )
            check_item.setCheckState(Qt.CheckState.Unchecked)
            check_item.setData(Qt.ItemDataRole.UserRole, rec["id"])
            self.table.setItem(row, 0, check_item)

            self.table.setItem(row, 1, QTableWidgetItem(rec.get("receipt_no", "")))
            self.table.setItem(
                row,
                2,
                QTableWidgetItem(
                    rec.get("receipt_date").strftime("%d.%m.%Y")
                    if rec.get("receipt_date")
                    else "-"
                ),
            )
            self.table.setItem(row, 3, QTableWidgetItem(rec.get("supplier_name", "")))
            self.table.setItem(row, 4, QTableWidgetItem(str(rec.get("total_items", 0))))

    def _on_select(self):
        for row in range(self.table.rowCount()):
            check_item = self.table.item(row, 0)
            if check_item and check_item.checkState() == Qt.CheckState.Checked:
                self.selected_receipt_id = check_item.data(Qt.ItemDataRole.UserRole)
                self.accept()
                return

        QMessageBox.warning(self, "Uyarı", "Lütfen bir mal kabul seçin!")

    def get_selected_receipt_id(self) -> int:
        return self.selected_receipt_id

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


class PaymentDialog(QDialog):
    """Ödeme kaydetme dialogu"""

    def __init__(self, invoice_data: dict, parent=None):
        super().__init__(parent)
        self.invoice_data = invoice_data
        self.payment_amount = Decimal("0")
        self.payment_method = None
        self.payment_notes = None
        self.setWindowTitle("Ödeme Kaydet")
        self.setMinimumSize(400, 300)
        self.setStyleSheet("QDialog { background-color: #1e293b; }")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBox(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("💳 Ödeme Kaydet")
        title.setStyleSheet("color: #f8fafc; font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # Fatura bilgisi
        inv_no = self.invoice_data.get("invoice_no", "")
        balance = float(self.invoice_data.get("balance", 0) or 0)
        info = QLabel(f"Fatura: {inv_no}\nKalan Borç: ₺{balance:,.2f}")
        info.setStyleSheet("color: #94a3b8; font-size: 14px;")
        layout.addWidget(info)

        # Ödeme tutarı
        amount_row = QHBoxLayout()
        amount_label = QLabel("Ödeme Tutarı:")
        amount_label.setStyleSheet("color: #f8fafc;")
        amount_row.addWidget(amount_label)

        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0.01, balance)
        self.amount_input.setDecimals(2)
        self.amount_input.setValue(balance)
        self.amount_input.setPrefix("₺")
        self.amount_input.setStyleSheet(
            """
            QDoubleSpinBox {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
                color: #f8fafc;
                font-size: 16px;
            }
        """
        )
        amount_row.addWidget(self.amount_input)
        layout.addLayout(amount_row)

        # Ödeme yöntemi
        method_row = QHBoxLayout()
        method_label = QLabel("Ödeme Yöntemi:")
        method_label.setStyleSheet("color: #f8fafc;")
        method_row.addWidget(method_label)

        self.method_combo = QComboBox()
        self.method_combo.addItems(
            ["Nakit", "Banka Transferi", "Kredi Kartı", "Çek", "Senet"]
        )
        self.method_combo.setStyleSheet(
            """
            QComboBox {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
                color: #f8fafc;
            }
        """
        )
        method_row.addWidget(self.method_combo)
        layout.addLayout(method_row)

        # Not
        notes_label = QLabel("Açıklama:")
        notes_label.setStyleSheet("color: #f8fafc;")
        layout.addWidget(notes_label)

        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Ödeme açıklaması (opsiyonel)")
        self.notes_input.setStyleSheet(
            """
            QLineEdit {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
                color: #f8fafc;
            }
        """
        )
        layout.addWidget(self.notes_input)

        layout.addStretch()

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #334155;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #475569; }
        """
        )
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Ödemeyi Kaydet")
        save_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #059669; }
        """
        )
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _on_save(self):
        self.payment_amount = Decimal(str(self.amount_input.value()))
        self.payment_method = self.method_combo.currentText()
        self.payment_notes = self.notes_input.text().strip() or None
        self.accept()

    def get_payment_data(self):
        return {
            "amount": self.payment_amount,
            "method": self.payment_method,
            "notes": self.payment_notes,
        }


class PurchaseInvoiceModule(QWidget):
    """Satınalma faturası modülü"""

    page_title = "Satınalma Faturaları"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.supplier_service = None
        self.item_service = None
        self.gr_service = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()

        # Liste sayfası
        self.list_page = PurchaseInvoiceListPage()
        self.list_page.add_clicked.connect(self._show_add_form)
        self.list_page.add_from_receipt_clicked.connect(self._show_receipt_selector)
        self.list_page.edit_clicked.connect(self._show_edit_form)
        self.list_page.delete_clicked.connect(self._delete_invoice)
        self.list_page.view_clicked.connect(self._show_view)
        self.list_page.confirm_clicked.connect(self._confirm_invoice)
        self.list_page.pay_clicked.connect(self._show_payment_dialog)
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
                    PurchaseInvoiceService,
                    SupplierService,
                    GoodsReceiptService,
                )

                self.service = PurchaseInvoiceService()
                self.supplier_service = SupplierService()
                self.gr_service = GoodsReceiptService()
            except Exception as e:
                print(f"Satın alma servisi yükleme hatası: {e}")

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
            invoices = self.service.get_all()
            data = []
            for inv in invoices:
                data.append(
                    {
                        "id": inv.id,
                        "invoice_no": inv.invoice_no,
                        "invoice_date": inv.invoice_date,
                        "due_date": inv.due_date,
                        "supplier_name": (inv.supplier.name if inv.supplier else ""),
                        "status": inv.status.value if inv.status else "draft",
                        "total": inv.total,
                        "paid_amount": inv.paid_amount,
                        "balance": inv.balance,
                    }
                )
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
        except Exception:
            return []

    def _get_items(self) -> list:
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
                }
                for i in items
            ]
        except Exception:
            return []

    def _get_completed_receipts(self) -> list:
        if not self.gr_service:
            return []
        try:
            from database.models.purchasing import GoodsReceiptStatus

            receipts = self.gr_service.get_all(status=GoodsReceiptStatus.COMPLETED)
            return [
                {
                    "id": r.id,
                    "receipt_no": r.receipt_no,
                    "receipt_date": r.receipt_date,
                    "supplier_name": r.supplier.name if r.supplier else "",
                    "total_items": r.total_items,
                }
                for r in receipts
            ]
        except Exception:
            return []

    def _show_add_form(self):
        """Manuel fatura formu"""
        suppliers = self._get_suppliers()
        items = self._get_items()

        form = PurchaseInvoiceFormPage(suppliers=suppliers, items=items)
        form.saved.connect(self._save_invoice)
        form.cancelled.connect(self._back_to_list)
        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)

    def _show_receipt_selector(self):
        """Mal kabulden fatura oluştur"""
        try:
            receipts = self._get_completed_receipts()

            if not receipts:
                QMessageBox.information(
                    self,
                    "Bilgi",
                    "Fatura oluşturmak için tamamlanmış mal kabul bulunamadı.",
                )
                return

            dialog = ReceiptSelectorDialog(receipts, self)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                receipt_id = dialog.get_selected_receipt_id()
                if not receipt_id:
                    return

                # Fatura oluştur
                invoice = self.service.create_from_goods_receipt(receipt_id)

                QMessageBox.information(
                    self,
                    "Başarılı",
                    f"Fatura oluşturuldu!\nFatura No: {invoice.invoice_no}",
                )
                self._load_data()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Fatura oluşturma hatası: {e}")
            import traceback

            traceback.print_exc()

    def _show_edit_form(self, invoice_id: int):
        if not self.service:
            return

        try:
            invoice = self.service.get_by_id(invoice_id)
            if invoice:
                items_data = []
                for item in invoice.items:
                    items_data.append(
                        {
                            "id": item.id,
                            "item_id": item.item_id,
                            "quantity": item.quantity,
                            "unit_id": item.unit_id,
                            "unit_price": item.unit_price,
                            "tax_rate": item.tax_rate,
                        }
                    )

                data = {
                    "id": invoice.id,
                    "invoice_no": invoice.invoice_no,
                    "invoice_date": invoice.invoice_date,
                    "due_date": invoice.due_date,
                    "supplier_id": invoice.supplier_id,
                    "supplier_invoice_no": invoice.supplier_invoice_no,
                    "supplier_invoice_date": invoice.supplier_invoice_date,
                    "notes": invoice.notes,
                    "status": (invoice.status.value if invoice.status else "draft"),
                    "items": items_data,
                }

                suppliers = self._get_suppliers()
                items = self._get_items()

                form = PurchaseInvoiceFormPage(
                    invoice_data=data, suppliers=suppliers, items=items
                )
                form.saved.connect(self._save_invoice)
                form.cancelled.connect(self._back_to_list)
                self.stack.addWidget(form)
                self.stack.setCurrentWidget(form)

        except Exception as e:
            print(f"Düzenleme hatası: {e}")
            import traceback

            traceback.print_exc()

    def _show_view(self, invoice_id: int):
        self._show_edit_form(invoice_id)

    def _save_invoice(self, data: dict):
        if not self.service:
            return

        try:
            invoice_id = data.pop("id", None)
            items_data = data.pop("items", [])

            if invoice_id:
                self.service.update(invoice_id, items_data, **data)
                QMessageBox.information(self, "Başarılı", "Fatura güncellendi!")
            else:
                self.service.create(items_data, **data)
                QMessageBox.information(self, "Başarılı", "Yeni fatura oluşturuldu!")

            self._back_to_list()
            self._load_data()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {e}")
            import traceback

            traceback.print_exc()

    def _confirm_invoice(self, invoice_id: int):
        """Faturayı onayla"""
        if not self.service:
            return

        reply = QMessageBox.question(
            self,
            "Onay",
            "Bu faturayı onaylamak istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                result = self.service.confirm(invoice_id)
                if result:
                    QMessageBox.information(self, "Başarılı", "Fatura onaylandı!")
                    self._load_data()
                else:
                    QMessageBox.warning(self, "Uyarı", "İşlem başarısız!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Hata: {e}")

    def _show_payment_dialog(self, invoice_id: int):
        """Ödeme dialogunu göster"""
        if not self.service:
            return

        try:
            invoice = self.service.get_by_id(invoice_id)
            if not invoice:
                QMessageBox.warning(self, "Uyarı", "Fatura bulunamadı!")
                return

            inv_data = {
                "id": invoice.id,
                "invoice_no": invoice.invoice_no,
                "balance": invoice.balance,
            }

            dialog = PaymentDialog(inv_data, self)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                payment_data = dialog.get_payment_data()

                self.service.record_payment(
                    invoice_id,
                    payment_data["amount"],
                    payment_data["method"],
                    payment_data["notes"],
                )

                QMessageBox.information(self, "Başarılı", "Ödeme kaydedildi!")
                self._load_data()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ödeme hatası: {e}")
            import traceback

            traceback.print_exc()

    def _delete_invoice(self, invoice_id: int):
        if not self.service:
            return

        try:
            if self.service.delete(invoice_id):
                QMessageBox.information(self, "Başarılı", "Fatura silindi!")
                self._load_data()
            else:
                QMessageBox.warning(
                    self, "Uyarı", "Silinemedi! (Sadece taslak faturalar silinebilir)"
                )
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")

    def _back_to_list(self):
        current = self.stack.currentWidget()
        if current != self.list_page:
            self.stack.setCurrentWidget(self.list_page)
            self.stack.removeWidget(current)
            current.deleteLater()
