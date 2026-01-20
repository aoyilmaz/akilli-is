"""
Akıllı İş - SSCC (Taşıma Birimi) Modülü
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMessageBox

from modules.inventory.services import SSCCService, ItemService, WarehouseService
from database.base import get_session
from .sscc_list import SSCCListPage
from .sscc_form import SSCCFormPage


class SSCCModule(QWidget):
    """Taşıma Birimi (SSCC) Yönetim Modülü"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = get_session()
        self.sscc_service = SSCCService(self.session)
        self.item_service = ItemService()
        self.item_service.session = self.session
        self.warehouse_service = WarehouseService()
        self.warehouse_service.session = self.session

        # Sayfaları tutmak için dictionary
        self.pages = {}
        self.current_page = None

        self._setup_ui()

    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Liste Sayfası
        self.list_page = SSCCListPage(self)
        self.list_page.add_clicked.connect(self.show_form)
        self.list_page.edit_clicked.connect(self.show_form)
        self.list_page.refresh_requested.connect(self.refresh_list)
        # self.list_page.delete_clicked.connect(self.delete_unit) # Silme yok, iptal var
        self.pages["list"] = self.list_page

        # Form Sayfası
        self.form_page = SSCCFormPage(self)
        self.form_page.save_clicked.connect(self.save_unit)
        self.form_page.cancel_clicked.connect(self.show_list)
        self.form_page.add_item_clicked.connect(self.add_item_to_unit)
        self.form_page.remove_item_clicked.connect(self.remove_item_from_unit)
        self.form_page.close_unit_clicked.connect(self.close_unit)
        self.pages["form"] = self.form_page

        # İlk açılışta listeyi göster
        self.show_list()

    def show_list(self):
        self._set_page("list")
        self.refresh_list()

    def show_form(self, unit_id=None):
        self._set_page("form")

        # Gerekli verileri yükle
        warehouses = self.warehouse_service.get_all()
        items = self.item_service.get_all()

        self.form_page.set_warehouses(warehouses)
        self.form_page.set_items(items)

        if unit_id:
            # Düzenleme modu
            unit = self.sscc_service.get_by_id(
                unit_id
            )  # get_by_id ServiceBase'den gelir
            if unit:
                items_content = self.sscc_service.get_unit_items(unit_id)
                self.form_page.load_unit(unit, items_content)
        else:
            # Yeni kayıt
            self.form_page.load_unit(None)

    def _set_page(self, page_name):
        if self.current_page:
            self.current_page.hide()
            self.layout.removeWidget(self.current_page)

        page = self.pages[page_name]
        self.layout.addWidget(page)
        page.show()
        self.current_page = page

    def refresh_list(self):
        filters = self.list_page.get_filters()
        # Filtreleme mantığı servise eklenebilir, şimdilik tümünü çekiyoruz
        # Gerçek uygulamada search parametreleri servise iletilmeli
        units = self.sscc_service.get_all()

        # Filtreleme (Client-side şimdilik)
        filtered_units = []
        keyword = filters.get("keyword", "").lower()
        u_type = filters.get("unit_type")
        status = filters.get("status")

        for u in units:
            if u_type and u.unit_type != u_type:
                continue
            if status and u.status != status:
                continue
            if keyword:
                if not (
                    keyword in u.sscc.lower()
                    or (u.notes and keyword in u.notes.lower())
                ):
                    continue
            filtered_units.append(u)

        self.list_page.load_data(filtered_units)

    def save_unit(self, data):
        try:
            if self.form_page.unit_id:
                # Güncelleme
                # self.sscc_service.update(self.form_page.unit_id, data) # Base serviste var mı?
                # ServiceBase.update genellikle generic, ama SSCC özel iş mantığı olabilir
                # Şimdilik manuel update
                unit = self.sscc_service.get_by_id(self.form_page.unit_id)
                if unit:
                    unit.unit_type = data["unit_type"]
                    unit.warehouse_id = data["warehouse_id"]
                    unit.notes = data["notes"]
                    unit.gross_weight_kg = data["gross_weight_kg"]
                    unit.length_cm = data["length_cm"]
                    unit.width_cm = data["width_cm"]
                    unit.height_cm = data["height_cm"]
                    self.session.commit()
                    QMessageBox.information(self, "Başarılı", "Birim güncellendi.")
            else:
                # Yeni Kayıt
                self.sscc_service.create_transport_unit(
                    unit_type=data["unit_type"],
                    warehouse_id=data["warehouse_id"],
                    notes=data["notes"],
                    # Boyutlar create metoduna eklenmeli mi? veya sonradan update
                )
                # Create metoduna boyutları eklemediysek, sonradan update edelim
                # Veya create metodunu güncelleyelim.
                # Şimdilik create methodu boyut almıyor, o yüzden son oluşturulanı alıp update edebiliriz
                # En temizi create_transport_unit metodunu güncellemek ama şimdilik ID'den bulup update edelim
                # SSCCService.create_transport_unit SSCC dönüyor.

                # Ancak create_transport_unit parametrelerini hatırlayalım: (self, unit_type, warehouse_id, location_id, notes, sscc)
                # Boyutları almıyor. O zaman önce oluşturup sonra update edelim.
                # Fakat serviste son oluşturulanı almak yerine create metodunun return değerini kullanmak lazım.
                # Ancak create metodunun return değerini (unit objesini) form sayfasında alamayız çünkü bu method (save_unit) çağırıyor.
                # Burada şöyle yapalım: create ettiğimiz birimi alıp boyutlarını set edelim.

                # NOT: SSCCService.create_transport_unit'e boyut parametreleri eklemek daha doğru olurdu.
                # Ancak service kodu şu an değişmeyecekse;
                # Mevcut create_transport_unit object return ediyor.

                # Fakat bu method (save_unit) SSCCService metodunu çağırırken data'yı kullanıyor.
                # Servis metoduna bakalım:
                # def create_transport_unit(self, unit_type, warehouse_id, location_id, notes, sscc) -> TransportUnit

                # O zaman:
                new_unit = self.sscc_service.create_transport_unit(
                    unit_type=data["unit_type"],
                    warehouse_id=data["warehouse_id"],
                    notes=data["notes"],
                )
                # Boyutları set et
                new_unit.gross_weight_kg = data["gross_weight_kg"]
                new_unit.length_cm = data["length_cm"]
                new_unit.width_cm = data["width_cm"]
                new_unit.height_cm = data["height_cm"]
                self.session.commit()

                QMessageBox.information(
                    self, "Başarılı", "Yeni taşıma birimi oluşturuldu."
                )

            self.show_list()

        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {str(e)}")

    def add_item_to_unit(self, data):
        if not self.form_page.unit_id:
            return

        try:
            self.sscc_service.add_item_to_unit(
                transport_unit_id=self.form_page.unit_id,
                item_id=data["item_id"],
                quantity=data["quantity"],
            )
            # Listeyi yenile
            self.show_form(self.form_page.unit_id)  # Formu reload et

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ürün ekleme hatası: {str(e)}")

    def remove_item_from_unit(self, item_id):
        try:
            self.sscc_service.remove_item_from_unit(item_id)
            self.show_form(self.form_page.unit_id)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ürün çıkarma hatası: {str(e)}")

    def close_unit(self, unit_id):
        try:
            self.sscc_service.close_unit(unit_id)
            QMessageBox.information(self, "Başarılı", "Birim kapatıldı ve paketlendi.")
            self.show_form(unit_id)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kapatma hatası: {str(e)}")
