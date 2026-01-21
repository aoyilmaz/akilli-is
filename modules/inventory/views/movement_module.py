"""
Akıllı İş - Stok Hareketleri Modülü
"""

from datetime import datetime
from PyQt6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QMessageBox
from PyQt6.QtCore import pyqtSignal

from modules.inventory.services import (
    StockMovementService,
    ItemService,
    WarehouseService,
    UnitService,
)
from modules.finance.services.currency_service import CurrencyService
from modules.inventory.views.movement_list import MovementListPage
from modules.inventory.views.movement_form import MovementFormPage


class MovementModule(QWidget):
    """Stok hareketleri modülü"""

    page_title = "Stok Hareketleri"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.movement_service = None
        self.item_service = None
        self.warehouse_service = None
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
        if self.currency_service:
            # CurrencyService session kullanıyor mu? Evet, basit init ile.
            # close metodu yoksa hata verebilir, ama service base kullanmıyor şimdilik.
            # Yine de kontrol edelim. base.py'deki ServiceBase close methoduna sahip.
            # Benim yazdığım CurrencyService ServiceBase inherit etmedi, ama session.close yapmalı.
            pass

    def load_data(self):
        try:
            self._get_services()

            filters = self.list_page.get_filters()

            # Hareket türü filtresi
            movement_type = None
            type_filter = filters.get("movement_type")
            if type_filter:
                from database.models import StockMovementType

                type_map = {
                    "giris": StockMovementType.GIRIS,
                    "cikis": StockMovementType.CIKIS,
                    "transfer": StockMovementType.TRANSFER,
                    "satin_alma": StockMovementType.SATIN_ALMA,
                    "satis": StockMovementType.SATIS,
                }
                movement_type = type_map.get(type_filter)

            movements = self.movement_service.get_movements(
                movement_type=movement_type,
                start_date=datetime.combine(
                    filters.get("start_date"), datetime.min.time()
                ),
                end_date=datetime.combine(filters.get("end_date"), datetime.max.time()),
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

            # Mevcut formu kaldır
            if self.stack.count() > 1:
                old = self.stack.widget(1)
                self.stack.removeWidget(old)
                old.deleteLater()

            # Yeni form
            form = MovementFormPage(movement_type)
            form.saved.connect(self.save_movement)
            form.cancelled.connect(self.show_list)

            # Stok kartlarını yükle
            items = self.item_service.get_all()
            form.load_items(items)

            # Depolari yükle
            warehouses = self.warehouse_service.get_all()
            form.load_warehouses(warehouses)

            # Birimleri yükle (Dual-Unit için)
            units = self.unit_service.get_all()
            form.load_units(units)

            # Dövizleri yükle
            currencies = self.currency_service.get_all()
            form.load_currencies(currencies)

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
            movement_type = data.pop("movement_type")
            from_warehouse_id = data.pop("from_warehouse_id", None)
            to_warehouse_id = data.pop("to_warehouse_id", None)

            # Her satır için hareket oluştur
            for line in lines:
                self.movement_service.create_movement(
                    item_id=line["item_id"],
                    movement_type=movement_type,
                    quantity=line["quantity"],
                    from_warehouse_id=from_warehouse_id,
                    to_warehouse_id=to_warehouse_id,
                    unit_price=line["unit_price"],
                    lot_number=line.get("lot_number"),
                    document_no=data.get("document_no"),
                    document_type="manual",
                    description=data.get("description"),
                    # Dual-Unit
                    secondary_quantity=line.get("secondary_quantity"),
                    secondary_unit_id=line.get("secondary_unit_id"),
                    # Currency
                    currency_id=line.get("currency_id"),
                    exchange_rate=line.get("exchange_rate"),
                )

            QMessageBox.information(self, "Başarılı", f"{len(lines)} satır kaydedildi!")
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
            QMessageBox.critical(self, "Hata", f"Detay görüntüleme hatası:\n{str(e)}")
        finally:
            self._close_services()


from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QDialogButtonBox,
    QScrollArea,
    QFrame,
)
from PyQt6.QtCore import Qt


class MovementDetailDialog(QDialog):
    """Hareket detay penceresi"""

    def __init__(self, movement, parent=None):
        super().__init__(parent)
        self.movement = movement
        self.setWindowTitle(f"Hareket Detayı - {movement.document_no or 'Belgesiz'}")
        self.setMinimumSize(450, 500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        form_layout = QFormLayout(content)
        form_layout.setSpacing(12)

        # Helper
        def add_row(label, value, color=None):
            lbl = QLabel(str(value) if value is not None else "-")
            if color:
                lbl.setStyleSheet(f"color: {color}; font-weight: bold;")
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            form_layout.addRow(QLabel(f"<b>{label}:</b>"), lbl)

        m = self.movement

        # Temel Bilgiler
        add_row("Tarih", m.movement_date.strftime("%d.%m.%Y %H:%M"))
        add_row("Belge No", m.document_no)
        add_row("Tür", m.movement_type.name)  # Enum name

        # Stok Bilgileri
        item_text = f"{m.item.code} - {m.item.name}" if m.item else (m.item_code or "-")
        add_row("Stok Kartı", item_text, "#818cf8")

        # Depo Bilgileri
        from_wh = m.from_warehouse.name if m.from_warehouse else "-"
        to_wh = m.to_warehouse.name if m.to_warehouse else "-"
        add_row("Kaynak Depo", from_wh)
        add_row("Hedef Depo", to_wh)

        # Miktar ve Fiyat
        quantity = f"{m.quantity:,.4f} {m.unit.code if m.unit else ''}"
        add_row("Miktar", quantity, "#10b981")

        if m.secondary_quantity:
            sec_qty = f"{m.secondary_quantity:,.4f} {m.secondary_unit.code if m.secondary_unit else ''}"
            add_row("İkincil Miktar", sec_qty)

        add_row("Birim Fiyat", f"₺{m.unit_price:,.2f}")
        add_row("Toplam Tutar", f"₺{m.total_price:,.2f}")

        if m.currency:
            add_row("Döviz", m.currency.code)
            add_row("Kur", m.exchange_rate)

        # Diğer
        if m.lot_number:
            add_row("Lot No", m.lot_number)

        if m.description:
            add_row("Açıklama", m.description)

        if m.created_by:
            add_row("Oluşturan ID", m.created_by)

        # Kapat butonu
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        layout.addWidget(buttons)
