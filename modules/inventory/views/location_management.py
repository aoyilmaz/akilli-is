"""
Akıllı İş - Lokasyon Yönetim Ekranı
"""

from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QDialog,
    QFormLayout,
    QSpinBox,
    QCheckBox,
    QMenu,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QColor

from database.models.inventory import LocationType
from config.icons import ICONS
from config.styles import COLORS
import qtawesome as qta

# BaseListPage ve ColumnConfig importları
from ui.components.base_list_page import BaseListPage
from ui.components.enhanced_table import ColumnConfig


class LocationManagementPage(BaseListPage):
    """Depo lokasyon yönetim sayfası"""

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("code", "Kod", width=100, filterable=True, sortable=True),
            ColumnConfig("barcode", "Barkod", width=120, filterable=True),
            ColumnConfig("name", "Ad", width=200, stretch=True, filterable=True),
            ColumnConfig("aisle", "Koridor", width=70, filterable=True),
            ColumnConfig("rack", "Raf", width=60, filterable=True),
            ColumnConfig("shelf", "Kat", width=60, filterable=True),
            ColumnConfig("type", "Tip", width=100, filter_type="enum"),
            ColumnConfig("zone", "Bölge", width=80, filterable=True),
            ColumnConfig("priority", "Öncelik", width=70, filter_type="number"),
            ColumnConfig("status", "Durum", width=80, filter_type="enum"),
        ]

        super().__init__(
            title="Lokasyon Yönetimi",
            icon=ICONS.LOCATION,  # "ph.map-pin" yerine ICONS.LOCATION kullanıyoruz
            table_id="location_management",
            columns=columns,
            show_add=True,
            add_text="Yeni Lokasyon",
            search_placeholder="Kod veya barkod...",
            parent=parent,
        )

        self.current_warehouse_id = None
        self.warehouses = []
        self.locations = []

        # Ekstra UI bileşenlerini ekle
        self._setup_extra_ui()

        self.load_warehouses()

    def _setup_extra_ui(self):
        """Header'a depo seçimi ve toplu oluştur butonu ekle"""

        # Depo seçimi combobox
        self.warehouse_combo = QComboBox()
        self.warehouse_combo.setMinimumWidth(200)
        self.warehouse_combo.setFixedHeight(36)
        self.warehouse_combo.currentIndexChanged.connect(self.on_warehouse_changed)

        # Toplu oluştur butonu
        self.bulk_btn = QPushButton("Toplu Oluştur")
        self.bulk_btn.setProperty("class", "btn-secondary")
        self.bulk_btn.setFixedHeight(36)
        self.bulk_btn.setIcon(qta.icon(ICONS.GRID, color="#475569"))
        self.bulk_btn.clicked.connect(self.bulk_create)

        # Header layout'una ekle
        h_layout = self.header.header_layout()

        # Arama kutusunun olduğu yere ekle (genellikle index 1 veya 2)
        # Search input widget'ını bul
        idx = -1
        if self.header.search_input:
            idx = h_layout.indexOf(self.header.search_input)

        if idx != -1:
            h_layout.insertWidget(idx, QLabel("Depo:"))
            h_layout.insertWidget(idx + 1, self.warehouse_combo)
        else:
            # Bulamazsa başa ekle
            h_layout.insertWidget(0, QLabel("Depo:"))
            h_layout.insertWidget(1, self.warehouse_combo)

        # Toplu oluştur butonunu Ekle butonunun yanına (varsa) veya sona ekle
        if self.header.add_btn:
            idx = h_layout.indexOf(self.header.add_btn)
            h_layout.insertWidget(idx, self.bulk_btn)
        else:
            h_layout.addWidget(self.bulk_btn)

        # BaseListPage sinyallerini bağla
        self.add_clicked.connect(self.add_location)
        self.refresh_requested.connect(self.load_locations)

        # Context Menü
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        # Filtre seçeneklerini tanımla
        self.table.set_filter_options("type", [t.value for t in LocationType])
        self.table.set_filter_options("status", ["Aktif", "Pasif"])

    def load_warehouses(self):
        """Depoları yükle"""
        try:
            from database.base import get_session
            from database.models.inventory import Warehouse

            session = get_session()
            self.warehouses = (
                session.query(Warehouse).filter(Warehouse.is_active == True).all()
            )

            self.warehouse_combo.blockSignals(True)
            self.warehouse_combo.clear()
            self.warehouse_combo.addItem("- Depo Seçin -", None)
            for wh in self.warehouses:
                self.warehouse_combo.addItem(f"{wh.code} - {wh.name}", wh.id)
            self.warehouse_combo.blockSignals(False)

            session.close()
        except Exception as e:
            self.show_error("Hata", f"Depolar yüklenemedi: {e}")

    def on_warehouse_changed(self, index: int):
        """Depo değiştiğinde lokasyonları yükle"""
        self.current_warehouse_id = self.warehouse_combo.currentData()
        if self.current_warehouse_id:
            self.load_locations()
        else:
            self.table.setRowCount(0)
            self.update_count(0)

    def load_locations(self):
        """Lokasyonları yükle"""
        if not self.current_warehouse_id:
            return

        try:
            from modules.inventory.services.location_service import LocationService

            # BaseListPage search entegrasyonu (BaseListPage _on_search içinde yapıyor ama
            # data load sırasında da filtreleyebiliriz veya tümünü çekip client-side filtreleriz)
            # Şimdilik hepsini çekiyoruz, BaseListPage client-side filtreliyor.

            self.locations = LocationService.get_all(
                warehouse_id=self.current_warehouse_id,
                is_active=None,  # Hepsini getir
            )
            self.refresh_table()
        except Exception as e:
            self.show_error("Hata", f"Lokasyonlar yüklenemedi: {e}")

    def refresh_table(self):
        """Tabloyu yenile"""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(self.locations))

        for row, loc in enumerate(self.locations):
            # Kod
            item = QTableWidgetItem(loc.code or "")
            item.setData(Qt.ItemDataRole.UserRole, loc.id)
            self.table.setItem(row, 0, item)

            # Barkod
            self.table.setItem(row, 1, QTableWidgetItem(loc.barcode or ""))

            # Ad
            self.table.setItem(row, 2, QTableWidgetItem(loc.name or ""))

            # Koridor
            self.table.setItem(row, 3, QTableWidgetItem(loc.aisle or ""))

            # Raf
            self.table.setItem(row, 4, QTableWidgetItem(loc.rack or ""))

            # Kat
            self.table.setItem(row, 5, QTableWidgetItem(loc.shelf or ""))

            # Tip
            type_text = loc.location_type.value if loc.location_type else ""
            self.table.setItem(row, 6, QTableWidgetItem(type_text))

            # Bölge
            self.table.setItem(row, 7, QTableWidgetItem(loc.zone or ""))

            # Öncelik
            from ui.components.enhanced_table import NumericTableWidgetItem

            self.table.setItem(row, 8, NumericTableWidgetItem(loc.priority or 0))

            # Durum
            status_item = QTableWidgetItem("Aktif" if loc.is_active else "Pasif")
            if loc.is_active:
                status_item.setForeground(QColor(COLORS.get("success", "#10b981")))
                status_item.setIcon(
                    qta.icon(ICONS.CHECK, color=COLORS.get("success", "#10b981"))
                )
            else:
                status_item.setForeground(QColor(COLORS.get("text_muted", "#64748b")))
                status_item.setIcon(
                    qta.icon(ICONS.CANCEL, color=COLORS.get("text_muted", "#64748b"))
                )
            self.table.setItem(row, 9, status_item)

        self.table.setSortingEnabled(True)
        self.update_count(len(self.locations))

        # Filtreleri uygula (BaseListPage özelliği)
        # self.table.apply_saved_filters() # BaseListPage load sonrası otomatik yapmıyor olabilir, kontrol edelim
        # BaseListPage otomatik yapmıyor,manuel çağıralım:
        self.table.apply_saved_filters()

    def show_context_menu(self, pos):
        """Sağ tık menüsü"""
        row = self.table.rowAt(pos.y())
        if row < 0:
            return

        item = self.table.item(row, 0)
        if not item:
            return

        loc_id = item.data(Qt.ItemDataRole.UserRole)

        menu = QMenu(self)

        edit_action = menu.addAction("✏️ Düzenle")
        edit_action.triggered.connect(lambda: self.edit_location(loc_id))

        delete_action = menu.addAction("🗑 Sil")
        delete_action.triggered.connect(lambda: self.delete_location(loc_id))

        menu.addSeparator()

        print_action = menu.addAction("🖨 Barkod Yazdır")
        # loc nesnesini bulmamız lazım
        loc = next((l for l in self.locations if l.id == loc_id), None)
        if loc:
            print_action.triggered.connect(lambda: self.print_barcode(loc))

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def add_location(self):
        """Yeni lokasyon ekle"""
        if not self.current_warehouse_id:
            self.show_info("Uyarı", "Lütfen önce bir depo seçin!")
            return

        dialog = LocationDialog(warehouse_id=self.current_warehouse_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_locations()

    def edit_location(self, location_id: int):
        """Lokasyon düzenle"""
        # loc_id int olarak geliyor
        loc = next((l for l in self.locations if l.id == location_id), None)
        if not loc:
            return

        dialog = LocationDialog(
            warehouse_id=self.current_warehouse_id, location=loc, parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_locations()

    def delete_location(self, location_id: int):
        """Lokasyon sil"""
        if self.confirm_delete("lokasyonu"):
            try:
                from modules.inventory.services.location_service import LocationService

                LocationService.delete(location_id)
                self.load_locations()
                self.show_info("Başarılı", "Lokasyon silindi.")
            except ValueError as e:
                self.show_info("Uyarı", str(e))
            except Exception as e:
                self.show_error("Hata", f"Silinemedi: {e}")

    def bulk_create(self):
        """Toplu lokasyon oluşturma"""
        if not self.current_warehouse_id:
            self.show_info("Uyarı", "Lütfen önce bir depo seçin!")
            return

        dialog = BulkLocationDialog(warehouse_id=self.current_warehouse_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_locations()

    def print_barcode(self, location):
        """Lokasyon barkodunu yazdır"""
        self.show_info(
            "Barkod Yazdırma",
            f"Lokasyon: {location.code}\n"
            f"Barkod: {location.barcode}\n\n"
            "(Yazdırma özelliği henüz eklenmedi)",
        )


class LocationDialog(QDialog):
    """Lokasyon ekleme/düzenleme dialog'u"""

    def __init__(self, warehouse_id: int, location=None, parent=None):
        super().__init__(parent)
        self.warehouse_id = warehouse_id
        self.location = location
        self.is_edit = location is not None

        self.setWindowTitle("Lokasyon Düzenle" if self.is_edit else "Yeni Lokasyon")
        self.setMinimumWidth(400)
        self.setup_ui()

        if self.is_edit:
            self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Kod
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Örn: A-01-03")
        form.addRow("Kod *:", self.code_input)

        # Ad
        self.name_input = QLineEdit()
        form.addRow("Ad *:", self.name_input)

        # Koridor
        self.aisle_input = QLineEdit()
        self.aisle_input.setPlaceholderText("Örn: A")
        form.addRow("Koridor:", self.aisle_input)

        # Raf
        self.rack_input = QLineEdit()
        self.rack_input.setPlaceholderText("Örn: 01")
        form.addRow("Raf:", self.rack_input)

        # Kat
        self.shelf_input = QLineEdit()
        self.shelf_input.setPlaceholderText("Örn: 03")
        form.addRow("Kat:", self.shelf_input)

        # Tip
        self.type_combo = QComboBox()
        for lt in LocationType:
            self.type_combo.addItem(lt.value, lt)
        form.addRow("Tip:", self.type_combo)

        # Bölge
        self.zone_input = QLineEdit()
        self.zone_input.setPlaceholderText("Örn: Normal, Soğuk, Tehlikeli")
        form.addRow("Bölge:", self.zone_input)

        # Öncelik
        self.priority_input = QSpinBox()
        self.priority_input.setRange(0, 999)
        form.addRow("Öncelik:", self.priority_input)

        # Aktif
        self.active_check = QCheckBox("Aktif")
        self.active_check.setChecked(True)
        form.addRow("", self.active_check)

        layout.addLayout(form)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("💾 Kaydet")
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def load_data(self):
        """Düzenleme modunda verileri yükle"""
        self.code_input.setText(self.location.code or "")
        self.name_input.setText(self.location.name or "")
        self.aisle_input.setText(self.location.aisle or "")
        self.rack_input.setText(self.location.rack or "")
        self.shelf_input.setText(self.location.shelf or "")
        self.zone_input.setText(self.location.zone or "")
        self.priority_input.setValue(self.location.priority or 0)
        self.active_check.setChecked(self.location.is_active)

        # Tip
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == self.location.location_type:
                self.type_combo.setCurrentIndex(i)
                break

    def save(self):
        """Kaydet"""
        code = self.code_input.text().strip()
        name = self.name_input.text().strip()

        if not code or not name:
            QMessageBox.warning(self, "Uyarı", "Kod ve Ad zorunludur!")
            return

        data = {
            "warehouse_id": self.warehouse_id,
            "code": code,
            "name": name,
            "aisle": self.aisle_input.text().strip() or None,
            "rack": self.rack_input.text().strip() or None,
            "shelf": self.shelf_input.text().strip() or None,
            "location_type": self.type_combo.currentData(),
            "zone": self.zone_input.text().strip() or None,
            "priority": self.priority_input.value(),
            "is_active": self.active_check.isChecked(),
        }

        try:
            from modules.inventory.services.location_service import LocationService

            if self.is_edit:
                LocationService.update(self.location.id, data)
            else:
                LocationService.create(data)

            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydedilemedi: {e}")


class BulkLocationDialog(QDialog):
    """Toplu lokasyon oluşturma dialog'u"""

    def __init__(self, warehouse_id: int, parent=None):
        super().__init__(parent)
        self.warehouse_id = warehouse_id
        self.setWindowTitle("Toplu Lokasyon Oluşturma")
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        info = QLabel(
            "Belirtilen aralıkta otomatik lokasyonlar oluşturulacaktır.\n"
            "Örnek: A-E koridorları, 1-10 raflar, 1-5 katlar = 250 lokasyon"
        )
        layout.addWidget(info)

        form = QFormLayout()

        # Koridor aralığı
        aisle_layout = QHBoxLayout()
        self.aisle_start = QLineEdit("A")
        self.aisle_start.setMaximumWidth(50)
        aisle_layout.addWidget(self.aisle_start)
        aisle_layout.addWidget(QLabel("-"))
        self.aisle_end = QLineEdit("C")
        self.aisle_end.setMaximumWidth(50)
        aisle_layout.addWidget(self.aisle_end)
        aisle_layout.addStretch()
        form.addRow("Koridor (A-Z):", aisle_layout)

        # Raf aralığı
        rack_layout = QHBoxLayout()
        self.rack_start = QSpinBox()
        self.rack_start.setRange(1, 99)
        self.rack_start.setValue(1)
        rack_layout.addWidget(self.rack_start)
        rack_layout.addWidget(QLabel("-"))
        self.rack_end = QSpinBox()
        self.rack_end.setRange(1, 99)
        self.rack_end.setValue(5)
        rack_layout.addWidget(self.rack_end)
        rack_layout.addStretch()
        form.addRow("Raf (1-99):", rack_layout)

        # Kat aralığı
        shelf_layout = QHBoxLayout()
        self.shelf_start = QSpinBox()
        self.shelf_start.setRange(1, 99)
        self.shelf_start.setValue(1)
        shelf_layout.addWidget(self.shelf_start)
        shelf_layout.addWidget(QLabel("-"))
        self.shelf_end = QSpinBox()
        self.shelf_end.setRange(1, 99)
        self.shelf_end.setValue(3)
        shelf_layout.addWidget(self.shelf_end)
        shelf_layout.addStretch()
        form.addRow("Kat (1-99):", shelf_layout)

        # Bölge
        self.zone_input = QLineEdit()
        self.zone_input.setPlaceholderText("Normal")
        form.addRow("Bölge:", self.zone_input)

        # Tip
        self.type_combo = QComboBox()
        for lt in LocationType:
            self.type_combo.addItem(lt.value, lt)
        form.addRow("Tip:", self.type_combo)

        layout.addLayout(form)

        # Önizleme
        self.preview_label = QLabel("Oluşturulacak: 0 lokasyon")
        layout.addWidget(self.preview_label)

        # Değişikliklerde önizleme güncelle
        self.aisle_start.textChanged.connect(self.update_preview)
        self.aisle_end.textChanged.connect(self.update_preview)
        self.rack_start.valueChanged.connect(self.update_preview)
        self.rack_end.valueChanged.connect(self.update_preview)
        self.shelf_start.valueChanged.connect(self.update_preview)
        self.shelf_end.valueChanged.connect(self.update_preview)
        self.update_preview()

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        create_btn = QPushButton("📦 Oluştur")
        create_btn.clicked.connect(self.create)
        btn_layout.addWidget(create_btn)

        layout.addLayout(btn_layout)

    def update_preview(self):
        """Önizleme güncelle"""
        try:
            aisle_count = (
                ord(self.aisle_end.text().upper())
                - ord(self.aisle_start.text().upper())
                + 1
            )
            rack_count = self.rack_end.value() - self.rack_start.value() + 1
            shelf_count = self.shelf_end.value() - self.shelf_start.value() + 1
            total = max(0, aisle_count * rack_count * shelf_count)
            self.preview_label.setText(f"Oluşturulacak: {total} lokasyon")
        except Exception:
            self.preview_label.setText("Oluşturulacak: ? lokasyon")

    def create(self):
        """Toplu oluştur"""
        try:
            from modules.inventory.services.location_service import LocationService

            locations = LocationService.create_bulk(
                warehouse_id=self.warehouse_id,
                aisle_start=self.aisle_start.text().upper(),
                aisle_end=self.aisle_end.text().upper(),
                rack_start=self.rack_start.value(),
                rack_end=self.rack_end.value(),
                shelf_start=self.shelf_start.value(),
                shelf_end=self.shelf_end.value(),
                zone=self.zone_input.text().strip() or None,
                location_type=self.type_combo.currentData(),
            )

            QMessageBox.information(
                self, "Başarılı", f"{len(locations)} lokasyon oluşturuldu."
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Oluşturulamadı: {e}")
