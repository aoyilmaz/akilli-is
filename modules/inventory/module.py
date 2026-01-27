"""
Akıllı İş - Stok Modülü Ana Widget
"""

from PyQt6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QMessageBox
from PyQt6.QtCore import Qt

from core.user_context import get_current_user
from database.models import StockRequestStatus

from .services import ItemService, UnitService, CategoryService
from .services.stock_request_service import StockRequestService
from .views import (
    StockListPage,
    StockFormPage,
    StockRequestFormPage,
    StockRequestListPage,
)


class InventoryModule(QWidget):
    """Stok modülü ana widget'ı"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.item_service = None
        self.unit_service = None
        self.category_service = None
        self.request_service = None
        self.current_item = None

        # Sayfalama
        self.current_page = 1
        self.page_size = 50
        self.total_records = 0
        self.total_pages = 0

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Stacked widget (liste ve form arası geçiş)
        self.stack = QStackedWidget()

        # Liste sayfası
        self.list_page = StockListPage()
        self.list_page.add_clicked.connect(self.show_add_form)
        self.list_page.edit_clicked.connect(self.show_edit_form)
        self.list_page.duplicate_clicked.connect(self.duplicate_item)
        self.list_page.delete_clicked.connect(self.delete_item)
        self.list_page.refresh_requested.connect(self.load_data)
        self.list_page.next_page_clicked.connect(self.next_page)
        self.list_page.prev_page_clicked.connect(self.prev_page)
        self.stack.addWidget(self.list_page)

        # Talep listesi sayfası
        self.request_list_page = StockRequestListPage()
        self.request_list_page.request_approved.connect(self.approve_request)
        self.request_list_page.request_rejected.connect(self.reject_request)
        self.request_list_page.refresh_requested.connect(self.load_requests)
        self.header = self.request_list_page.header
        self.header.back_clicked.connect(self.show_list)
        self.stack.addWidget(self.request_list_page)  # Index 1

        layout.addWidget(self.stack)

    def _get_services(self):
        """Servisleri al (lazy loading)"""
        if self.item_service is None:
            self.item_service = ItemService()
        if self.unit_service is None:
            self.unit_service = UnitService()
        if self.category_service is None:
            self.category_service = CategoryService()
        if self.request_service is None:
            self.request_service = StockRequestService()

    def _close_services(self):
        """Servisleri kapat"""
        if self.item_service:
            self.item_service.close()
            self.item_service = None
        if self.unit_service:
            self.unit_service.close()
            self.unit_service = None
        if self.category_service:
            self.category_service.close()
            self.category_service = None
        if self.request_service:
            self.request_service.close()
            self.request_service = None

    def load_data(self):
        """Verileri yükle"""
        try:
            self._get_services()

            # Filtreleri al
            filters = self.list_page.get_filters()

            # Sayfalama için offset hesapla
            offset = (self.current_page - 1) * self.page_size

            # Toplam kayıt sayısını al
            self.total_records = self.item_service.count_search(
                keyword=filters.get("keyword", ""),
                item_type=filters.get("item_type"),
                is_active=filters.get("is_active"),
                stock_status=filters.get("stock_status"),
            )

            # Toplam sayfa sayısını hesapla
            import math

            self.total_pages = math.ceil(self.total_records / self.page_size) or 1
            if self.current_page > self.total_pages:
                self.current_page = self.total_pages

            # Stok kartlarını getir
            items = self.item_service.search(
                keyword=filters.get("keyword", ""),
                item_type=filters.get("item_type"),
                is_active=filters.get("is_active"),
                limit=self.page_size,
                offset=offset,
                stock_status=filters.get("stock_status"),
            )

            # İstatistikleri getir ve güncelle
            stats = self.item_service.get_stats(
                keyword=filters.get("keyword", ""),
                item_type=filters.get("item_type"),
                is_active=filters.get("is_active"),
                stock_status=filters.get("stock_status"),
            )
            self.list_page.update_stats(stats)

            self.list_page.load_data(items)
            self.list_page.update_pagination(
                self.current_page, self.total_pages, self.total_records
            )

            # Yetki kontrolü ve UI ayarlamaları
            user = get_current_user()
            if user and user.has_permission("inventory.create"):
                # Yetkili kullanıcı: Talep butonu ekle/göster
                self.list_page.header.set_add_text("Yeni Stok Kartı")

                # Header'a "Talepler" butonu ekle (eğer yoksa)
                if not hasattr(self.list_page, "requests_btn"):
                    from PyQt6.QtWidgets import QPushButton

                    btn = QPushButton("📨 Talepler")
                    btn.setProperty("class", "btn-secondary")
                    btn.setFixedHeight(30)
                    btn.clicked.connect(self.show_requests)

                    # Add butonu soluna ekle
                    h_layout = self.list_page.header.header_layout()
                    add_btn = self.list_page.header.add_btn
                    if add_btn:
                        idx = h_layout.indexOf(add_btn)
                        if idx >= 0:
                            h_layout.insertWidget(idx, btn)
                        else:
                            h_layout.insertWidget(2, btn)
                    else:
                        h_layout.insertWidget(2, btn)

                    self.list_page.requests_btn = btn

                # Bekleyen talep sayısını kontrol et
                pending_count = len(
                    self.request_service.get_all(status=StockRequestStatus.PENDING)
                )
                if pending_count > 0:
                    self.list_page.requests_btn.setText(
                        f"📨 Talepler ({pending_count})"
                    )
                    self.list_page.requests_btn.setStyleSheet(
                        "background-color: #f59e0b; color: white;"
                    )
                else:
                    self.list_page.requests_btn.setText("📨 Talepler")
                    self.list_page.requests_btn.setStyleSheet("")
            else:
                # Standart kullanıcı: Sadece talep butonu
                self.list_page.header.set_add_text("Stok Talebi Oluştur")

        except Exception as e:
            import traceback

            traceback.print_exc()
            QMessageBox.critical(
                self, "Hata", f"Veriler yüklenirken hata oluştu:\n{str(e)}"
            )
        finally:
            self._close_services()

    def next_page(self):
        """Sonraki sayfa"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_data()

    def prev_page(self):
        """Önceki sayfa"""
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data()

    def show_add_form(self):
        """Yeni stok kartı veya talep formu göster"""
        user = get_current_user()

        # Eğer kullanıcının stok oluşturma yetkisi yoksa -> Talep Formu
        if user and not user.has_permission("inventory.create"):
            self._show_request_form()
        else:
            # Yetkisi varsa -> Stok Formu
            self.current_item = None
            self._show_form(None)

    def show_edit_form(self, item_id: int):
        """Düzenleme formu göster"""
        try:
            self._get_services()
            item = self.item_service.get_by_id(item_id)
            if item:
                self.current_item = item
                self._show_form(item)
            else:
                QMessageBox.warning(self, "Uyarı", "Stok kartı bulunamadı!")
        except Exception as e:
            QMessageBox.critical(
                self, "Hata", f"Stok kartı yüklenirken hata:\n{str(e)}"
            )
        finally:
            self._close_services()

    def duplicate_item(self, item_id: int):
        """Stok kartını kopyala ve yeni oluştur"""
        try:
            self._get_services()
            item = self.item_service.get_by_id(item_id)
            if item:
                # Formu mevcut item ile aç
                self.current_item = item  # Geçici referans, form içinde null yapacağız
                self._show_form(item)

                # Formu duplicate moduna sok
                if self.stack.count() > 2:
                    form = self.stack.widget(2)
                    if isinstance(form, StockFormPage):
                        form.set_duplicate_mode()
                        self.current_item = None  # Artık yeni kayıt modundayız
            else:
                QMessageBox.warning(
                    self, "Uyarı", "Kopyalanacak stok kartı bulunamadı!"
                )
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kopyalama hatası:\n{str(e)}")
        finally:
            self._close_services()

    def _show_form(self, item):
        """Form sayfasını göster"""
        try:
            self._get_services()

            # Mevcut form varsa kaldır (index 2'deki)
            if self.stack.count() > 2:
                old_form = self.stack.widget(2)
                self.stack.removeWidget(old_form)
                old_form.deleteLater()

            # Yeni form oluştur
            form = StockFormPage(item)
            form.saved.connect(self.save_item)
            form.cancelled.connect(self.show_list)
            form.generate_code_requested.connect(self.generate_new_code)

            # Birimleri yükle
            units = self.unit_service.get_all()
            form.load_units(units)

            # Kategorileri yükle
            categories = self.category_service.get_all()
            form.load_categories(categories)

            # Referans seçimi için stok listesini yükle
            all_items = self.item_service.get_all()
            form.set_items(all_items)

            # Otomatik kod üretme
            if item is None:
                next_code = self.item_service.get_next_code()
                form.set_generated_code(next_code)

            # Birim ve kategori seçimlerini ayarla (düzenleme modunda)
            if item:
                # Birim
                for i in range(form.unit_combo.count()):
                    if form.unit_combo.itemData(i) == item.unit_id:
                        form.unit_combo.setCurrentIndex(i)
                        break
                # Kategori
                for i in range(form.category_combo.count()):
                    if form.category_combo.itemData(i) == item.category_id:
                        form.category_combo.setCurrentIndex(i)
                        break

            self.stack.addWidget(form)
            self.stack.setCurrentWidget(form)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Form açılırken hata:\n{str(e)}")
        finally:
            self._close_services()

    def show_list(self):
        """Liste sayfasına dön"""
        self.stack.setCurrentIndex(0)
        self.load_data()

    def save_item(self, data: dict):
        """Stok kartını kaydet"""
        try:
            self._get_services()

            if self.current_item:
                # Güncelleme
                self.item_service.update(self.current_item.id, **data)
                QMessageBox.information(self, "Başarılı", "Stok kartı güncellendi!")
            else:
                # Yeni kayıt
                new_item = self.item_service.create(**data)

                # Eğer bir talepten geliyorsa, talebi onayla
                if hasattr(self, "current_request") and self.current_request:
                    try:
                        self.request_service.approve_request(
                            self.current_request.id, new_item.id
                        )
                        delattr(self, "current_request")
                    except Exception as e:
                        print(f"Talep onaylanırken hata: {e}")

                QMessageBox.information(self, "Başarılı", "Stok kartı oluşturuldu!")

            self.show_list()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası:\n{str(e)}")
        finally:
            self._close_services()

    def delete_item(self, item_id: int):
        """Stok kartını sil"""
        try:
            self._get_services()

            if self.item_service.delete(item_id):
                QMessageBox.information(self, "Başarılı", "Stok kartı silindi!")
                self.load_data()
            else:
                QMessageBox.warning(self, "Uyarı", "Stok kartı silinemedi!")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Silme hatası:\n{str(e)}")
        finally:
            self._close_services()

    def generate_new_code(self):
        """Yeni kod üret ve forma set et"""
        try:
            self._get_services()
            next_code = self.item_service.get_next_code()

            # Formu bul ve kodu set et
            if self.stack.count() > 2:
                form = self.stack.widget(2)
                if isinstance(form, StockFormPage):
                    form.set_generated_code(next_code)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kod üretilirken hata:\n{str(e)}")
        finally:
            self._close_services()

    # === Stok Talep İşlemleri ===

    def _show_request_form(self):
        """Stok talep formunu göster"""
        try:
            self._get_services()

            # Formu stack'e ekle
            form = StockRequestFormPage()
            form.cancelled.connect(self.show_list)
            form.saved.connect(self.save_request)

            # Stok listesini referans için yükle
            items = self.item_service.get_all()
            form.set_items(items)

            # Birim ve kategorileri yükle
            units = self.unit_service.get_all()
            form.load_units(units)
            categories = self.category_service.get_all()
            form.load_categories(categories)

            # Stack'e ekle ve göster (varsa eskini sil)
            if self.stack.count() > 2:  # 0: List, 1: RequestList
                widget = self.stack.widget(2)
                self.stack.removeWidget(widget)
                widget.deleteLater()

            self.stack.addWidget(form)
            self.stack.setCurrentWidget(form)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Talep formu açılırken hata:\n{str(e)}")
        finally:
            self._close_services()

    def save_request(self, data: dict):
        """Talebi kaydet"""
        try:
            self._get_services()
            user = get_current_user()

            self.request_service.create_request(requester_id=user.user_id, **data)

            QMessageBox.information(
                self,
                "Başarılı",
                "Stok talebiniz oluşturuldu ve yetkili onayına sunuldu.",
            )
            self.show_list()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Talep kaydedilirken hata:\n{str(e)}")
        finally:
            self._close_services()

    def show_requests(self):
        """Talep listesini göster"""
        self.stack.setCurrentWidget(self.request_list_page)
        self.load_requests()

    def load_requests(self):
        """Talepleri yükle"""
        try:
            self._get_services()
            requests = self.request_service.get_all()
            self.request_list_page.load_data(requests)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Talepler yüklenirken hata:\n{str(e)}")
        finally:
            self._close_services()

    def approve_request(self, request):
        """Talebi onayla ve stok formunu aç"""
        try:
            # Onaylanan talebi sakla (kayıt sonrası güncellemek için)
            self.current_request = request

            # Yeni stok kartı için hazırlık yap
            self.current_item = None
            self._show_form(None)  # Boş form aç

            # Formu bul ve talep verileriyle doldur
            form = self.stack.currentWidget()
            if isinstance(form, StockFormPage):
                form.name_input.setText(request.proposed_name)
                form.description_input.setPlainText(request.description)

                # Tür
                for i in range(form.type_combo.count()):
                    if form.type_combo.itemData(i) == request.item_type:
                        form.type_combo.setCurrentIndex(i)
                        break

                # Kategori
                if request.category_id:
                    for i in range(form.category_combo.count()):
                        if form.category_combo.itemData(i) == request.category_id:
                            form.category_combo.setCurrentIndex(i)
                            break

                # Birim
                if request.unit_id:
                    for i in range(form.unit_combo.count()):
                        if form.unit_combo.itemData(i) == request.unit_id:
                            form.unit_combo.setCurrentIndex(i)
                            break

                # Referans stok varsa diğer bilgileri kopyala
                if request.reference_stock_id:
                    ref_item = request.reference_stock
                    # Burada ref_item bilgilerini forma doldurabiliriz
                    # Ancak StockFormPage.load_item_data metodunu item olmadan kullanamıyoruz
                    # Bu yüzden StockFormPage'e yeni bir metod eklememiz gerekebilir veya alanları tek tek set edebiliriz.
                    # Basitlik için şimdilik temel alanlar yeterli.
                    pass

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Onay işlemi sırasında hata:\n{str(e)}")

    def reject_request(self, request_id: int, reason: str):
        """Talebi reddet"""
        try:
            self._get_services()
            self.request_service.reject_request(request_id, reason)
            QMessageBox.information(self, "Bilgi", "Talep reddedildi.")
            self.load_requests()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Red işlemi sırasında hata:\n{str(e)}")
        finally:
            self._close_services()
