"""
Akıllı İş - Stok Hareketleri Modülü
"""

from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget,
    QStackedWidget,
    QVBoxLayout,
    QMessageBox,
    QDialog,
    QFormLayout,
    QLabel,
    QDialogButtonBox,
    QScrollArea,
    QFrame,
)
from PyQt6.QtCore import Qt

from modules.inventory.services import (
    StockMovementService,
    ItemService,
    WarehouseService,
    UnitService,
)
from modules.finance.services.currency_service import CurrencyService
from modules.inventory.views.movement_list import MovementListPage
from modules.inventory.views.movement_form import MovementFormPage
from database.models import StockMovementType


class MovementModule(QWidget):
    """Stok hareketleri modülü"""

    page_title = "Stok Hareketleri"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.movement_service = None
        self.item_service = None
        self.warehouse_service = None
        self.unit_service = None  # Dual-Unit için
        self.currency_service = None
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()

        # Liste sayfası
        self.list_page = MovementListPage()
        self.list_page.add_entry_clicked.connect(lambda: self.show_form("entry"))
        self.list_page.add_exit_clicked.connect(lambda: self.show_form("exit"))
        self.list_page.add_transfer_clicked.connect(lambda: self.show_form("transfer"))
        self.list_page.refresh_requested.connect(self.load_data)
        self.list_page.view_clicked.connect(self.show_detail)
        self.stack.addWidget(self.list_page)
        layout.addWidget(self.stack)

    def _get_services(self):
        if self.movement_service is None:
            self.movement_service = StockMovementService()
        if self.item_service is None:
            self.item_service = ItemService()
        if self.warehouse_service is None:
            self.warehouse_service = WarehouseService()
        if self.unit_service is None:
            self.unit_service = UnitService()
        if self.currency_service is None:
            self.currency_service = CurrencyService()

    def _close_services(self):
        if self.movement_service:
            self.movement_service.close()
            self.movement_service = None
        if self.item_service:
            self.item_service.close()
            self.item_service = None
        if self.warehouse_service:
            self.warehouse_service.close()
            self.warehouse_service = None
        if self.unit_service:
            self.unit_service.close()
            self.unit_service = None

    def load_data(self):
        try:
            self._get_services()
            filters = self.list_page.get_filters()

            # Hareket türü filtresi
            movement_type = None
            type_filter = filters.get("movement_type")
            if type_filter:
                type_map = {
                    "giris": StockMovementType.GIRIS,
                    "cikis": StockMovementType.CIKIS,
                    "transfer": StockMovementType.TRANSFER,
                    "sarin_alma": StockMovementType.SATIN_ALMA,
                    "satis": StockMovementType.SATIS,
                }
                movement_type = type_map.get(type_filter)

            start_dt = datetime.combine(filters.get("start_date"), datetime.min.time())
            end_dt = datetime.combine(filters.get("end_date"), datetime.max.time())

            movements = self.movement_service.get_movements(
                movement_type=movement_type,
                start_date=start_dt,
                end_date=end_dt,
                limit=500,
            )

            # Keyword filtresi
            keyword = filters.get("keyword", "").lower()
            if keyword:
                movements = [
                    m
                    for m in movements
                    if keyword in (m.item_code or "").lower()
                    or keyword in (m.document_no or "").lower()
                    or keyword in (m.item_name or "").lower()
                ]

            self.list_page.load_data(movements)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veriler yüklenirken hata:\n{str(e)}")
        finally:
            self._close_services()

    def show_form(self, movement_type: str):
        """Form göster"""
        try:
            self._get_services()
            if self.stack.count() > 1:
                old = self.stack.widget(1)
                self.stack.removeWidget(old)
                old.deleteLater()

            form = MovementFormPage(movement_type)
            form.saved.connect(self.save_movement)
            form.cancelled.connect(self.show_list)

            form.load_items(self.item_service.get_all())
            form.load_warehouses(self.warehouse_service.get_all())
            form.load_units(self.unit_service.get_all())
            form.load_currencies(self.currency_service.get_all())

            self.stack.addWidget(form)
            self.stack.setCurrentIndex(1)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Form açılırken hata:\n{str(e)}")
        finally:
            self._close_services()

    def show_list(self):
        self.stack.setCurrentIndex(0)
        self.load_data()

    def save_movement(self, data: dict):
        """Hareketi kaydet"""
        try:
            self._get_services()
            lines = data.pop("lines", [])
            m_type = data.pop("movement_type")
            f_wh = data.pop("from_warehouse_id", None)
            t_wh = data.pop("to_warehouse_id", None)

            for ln in lines:
                self.movement_service.create_movement(
                    item_id=ln["item_id"],
                    movement_type=m_type,
                    quantity=ln["quantity"],
                    from_warehouse_id=f_wh,
                    to_warehouse_id=t_wh,
                    unit_price=ln["unit_price"],
                    lot_number=ln.get("lot_number"),
                    document_no=data.get("document_no"),
                    document_type="manual",
                    description=data.get("description"),
                    secondary_quantity=ln.get("secondary_quantity"),
                    secondary_unit_id=ln.get("secondary_unit_id"),
                    currency_id=ln.get("currency_id"),
                    exchange_rate=ln.get("exchange_rate"),
                )

            msg = f"{len(lines)} satır kaydedildi!"
            QMessageBox.information(self, "Başarılı", msg)
            self.show_list()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası:\n{str(e)}")
        finally:
            self._close_services()

    def show_detail(self, movement_id: int):
        """Hareket detayını göster"""
        try:
            self._get_services()
            movement = self.movement_service.get_by_id(movement_id)
            if not movement:
                QMessageBox.warning(self, "Hata", "Hareket bulunamadı!")
                return
            dialog = MovementDetailDialog(movement, self)
            dialog.exec()
        except Exception as e:
            err_msg = f"Detay görüntüleme hatası:\n{str(e)}"
            QMessageBox.critical(self, "Hata", err_msg)
        finally:
            self._close_services()


class MovementDetailDialog(QDialog):
    """Hareket detay penceresi"""

    def __init__(self, movement, parent=None):
        super().__init__(parent)
        self.movement = movement
        doc = movement.document_no or "Belgesiz"
        self.setWindowTitle(f"Hareket Detayı - {doc}")
        self.setMinimumSize(450, 500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        form_layout = QFormLayout(content)
        form_layout.setSpacing(12)

        def add_row(label, value, color=None):
            val_str = str(value) if value is not None else "-"
            lbl = QLabel(val_str)
            if color:
                lbl.setStyleSheet(f"color: {color}; font-weight: bold;")
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            form_layout.addRow(QLabel(f"<b>{label}:</b>"), lbl)

        m = self.movement
        dt_str = m.movement_date.strftime("%d.%m.%Y %H:%M")
        add_row("Tarih", dt_str)
        add_row("Belge No", m.document_no)
        add_row("Tür", m.movement_type.name)

        it_text = f"{m.item.code} - {m.item.name}" if m.item else (m.item_code or "-")
        add_row("Stok Kartı", it_text, "#818cf8")

        f_wh = m.from_warehouse.name if m.from_warehouse else "-"
        t_wh = m.to_warehouse.name if m.to_warehouse else "-"
        add_row("Kaynak Depo", f_wh)
        add_row("Hedef Depo", t_wh)

        u_code = m.unit.code if m.unit else ""
        qty_str = f"{m.quantity:,.4f} {u_code}"
        add_row("Miktar", qty_str, "#10b981")

        if m.secondary_quantity:
            su_code = m.secondary_unit.code if m.secondary_unit else ""
            sq = f"{m.secondary_quantity:,.4f} {su_code}"
            add_row("İkincil Miktar", sq)

        add_row("Birim Fiyat", f"₺{m.unit_price:,.2f}")
        add_row("Toplam Tutar", f"₺{m.total_price:,.2f}")

        if m.currency:
            add_row("Döviz", m.currency.code)
            add_row("Kur", m.exchange_rate)

        if m.lot_number:
            add_row("Lot No", m.lot_number)
        if m.description:
            add_row("Açıklama", m.description)
        if m.created_by:
            add_row("Oluşturan ID", m.created_by)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(self.accept)
        layout.addWidget(btns)
