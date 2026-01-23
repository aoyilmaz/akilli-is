"""
Akıllı İş - BOM (Ürün Reçeteleri) Modülü
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QMessageBox

from .bom_list import BOMListPage
from .bom_form import BOMFormPage


class BOMModule(QWidget):
    """Ürün Reçeteleri modülü"""

    page_title = "Ürün Reçeteleri"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bom_service = None
        self.item_service = None
        self.unit_service = None
        self.station_service = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()

        # Liste sayfası
        self.list_page = BOMListPage()
        self.list_page.add_clicked.connect(self._show_new_form)
        self.list_page.edit_clicked.connect(self._show_edit_form)
        self.list_page.delete_clicked.connect(self._delete_bom)
        self.list_page.refresh_requested.connect(self._load_data)

        self.stack.addWidget(self.list_page)
        layout.addWidget(self.stack)

    def showEvent(self, event):
        super().showEvent(event)
        self._ensure_services()
        self._load_data()

    def _ensure_services(self):
        """Servisleri yükle"""
        if not self.bom_service:
            try:
                from modules.production.services import BOMService, WorkStationService
                from modules.inventory.services import ItemService, UnitService

                self.bom_service = BOMService()
                self.item_service = ItemService()
                self.unit_service = UnitService()
                self.station_service = WorkStationService()
            except Exception as e:
                print(f"Servis yükleme hatası: {e}")

    def _load_data(self):
        """Verileri yükle"""
        if not self.bom_service:
            return

        try:
            filters = self.list_page.get_filters()
            status = filters.get("status")

            boms = self.bom_service.get_all(status=status)
            self.list_page.load_data(boms)

        except Exception as e:
            print(f"Veri yükleme hatası: {e}")
            self.list_page.load_data([])

    def _show_new_form(self):
        """Yeni reçete formu göster"""
        self._ensure_services()

        form = BOMFormPage(bom=None)
        form.saved.connect(self._save_bom)
        form.cancelled.connect(self._show_list)

        # Gerekli verileri yükle
        self._load_form_resources(form)

        # Kod üretimi
        try:
            code = self.bom_service.generate_code()
            # BOMFormPage code_input public
            form.code_input.setText(code)
        except Exception as e:
            print(f"Kod üretme hatası: {e}")

        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)

    def _show_edit_form(self, bom_id: int):
        """Düzenleme formu göster"""
        self._ensure_services()

        bom = self.bom_service.get_by_id(bom_id)
        if not bom:
            QMessageBox.warning(self, "Hata", "Reçete bulunamadı!")
            return

        form = BOMFormPage(bom=bom)
        form.saved.connect(self._save_bom)
        form.cancelled.connect(self._show_list)

        self._load_form_resources(form)

        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)

    def _load_form_resources(self, form: BOMFormPage):
        """Form için gerekli kaynakları yükle (items, units, stations)"""
        try:
            items = self.item_service.get_all()
            units = self.unit_service.get_all()
            if self.station_service:
                stations = self.station_service.get_all()
            else:
                stations = []

            form.load_data_sources(items, units, stations)
        except Exception as e:
            print(f"Form kaynakları yüklenirken hata: {e}")

    def _save_bom(self, data: dict):
        """Reçeteyi vakydet"""
        try:
            current_form = self.stack.currentWidget()
            if isinstance(current_form, BOMFormPage) and current_form.is_edit:
                self.bom_service.update(current_form.bom.id, **data)
                QMessageBox.information(self, "Başarılı", "Reçete güncellendi!")
            else:
                self.bom_service.create(**data)
                QMessageBox.information(self, "Başarılı", "Reçete oluşturuldu!")

            self._show_list()
            self._load_data()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası: {str(e)}")

    def _delete_bom(self, bom_id: int):
        """Reçeteyi sil"""
        try:
            success = self.bom_service.delete(bom_id)
            if success:
                QMessageBox.information(self, "Başarılı", "Reçete silindi!")
                self._load_data()
            else:
                QMessageBox.warning(self, "Uyarı", "Reçete silinemedi!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Silme hatası: {str(e)}")

    def _show_list(self):
        """Liste sayfasına dön"""
        current = self.stack.currentWidget()
        if current != self.list_page:
            self.stack.removeWidget(current)
            current.deleteLater()

        self.stack.setCurrentWidget(self.list_page)
