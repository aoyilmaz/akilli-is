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
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QDialog,
    QFormLayout,
    QSpinBox,
    QCheckBox,
    QAbstractItemView,
    QMenu,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction

from database.models.inventory import LocationType


class LocationManagementPage(QWidget):
    """Depo lokasyon yönetim sayfası"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_warehouse_id = None
        self.warehouses = []
        self.locations = []
        self.setup_ui()
        self.load_warehouses()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Başlık
        header = QHBoxLayout()
        title = QLabel("📍 Lokasyon Yönetimi")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Filtre bar
        filter_frame = QFrame()
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(16, 12, 16, 12)
        filter_layout.setSpacing(12)

        # Depo seçimi
        filter_layout.addWidget(QLabel("Depo:"))
        self.warehouse_combo = QComboBox()
        self.warehouse_combo.setMinimumWidth(200)
        self.warehouse_combo.currentIndexChanged.connect(self.on_warehouse_changed)
        filter_layout.addWidget(self.warehouse_combo)

        # Arama
        filter_layout.addWidget(QLabel("Ara:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Kod veya barkod...")
        self.search_input.setMaximumWidth(200)
        self.search_input.textChanged.connect(self.filter_locations)
        filter_layout.addWidget(self.search_input)

        filter_layout.addStretch()

        # Butonlar
        self.add_btn = QPushButton("➕ Yeni Lokasyon")
        self.add_btn.clicked.connect(self.add_location)
        filter_layout.addWidget(self.add_btn)

        self.bulk_btn = QPushButton("📦 Toplu Oluştur")
        self.bulk_btn.clicked.connect(self.bulk_create)
        filter_layout.addWidget(self.bulk_btn)

        layout.addWidget(filter_frame)

        # Tablo
        self.table = QTableWidget()
        self.setup_table()
        layout.addWidget(self.table)

        # Alt bilgi
        self.status_label = QLabel("Toplam: 0 lokasyon")
        layout.addWidget(self.status_label)

    def setup_table(self):
        columns = [
            ("Kod", 100),
            ("Barkod", 120),
            ("Ad", 200),
            ("Koridor", 70),
            ("Raf", 60),
            ("Kat", 60),
            ("Tip", 100),
            ("Bölge", 80),
            ("Öncelik", 70),
            ("Durum", 70),
            ("", 80),
        ]

        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels([c[0] for c in columns])

        header = self.table.horizontalHeader()
        for i, (_, width) in enumerate(columns):
            if i == 2:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                self.table.setColumnWidth(i, width)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

    def load_warehouses(self):
        """Depoları yükle"""
        try:
            from database.base import get_session
            from database.models.inventory import Warehouse

            session = get_session()
            self.warehouses = (
                session.query(Warehouse).filter(Warehouse.is_active == True).all()
            )

            self.warehouse_combo.clear()
            self.warehouse_combo.addItem("- Depo Seçin -", None)
            for wh in self.warehouses:
                self.warehouse_combo.addItem(f"{wh.code} - {wh.name}", wh.id)

            session.close()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Depolar yüklenemedi: {e}")

    def on_warehouse_changed(self, index: int):
        """Depo değiştiğinde lokasyonları yükle"""
        self.current_warehouse_id = self.warehouse_combo.currentData()
        if self.current_warehouse_id:
            self.load_locations()
        else:
            self.table.setRowCount(0)
            self.status_label.setText("Toplam: 0 lokasyon")

    def load_locations(self):
        """Lokasyonları yükle"""
        if not self.current_warehouse_id:
            return

        try:
            from modules.inventory.services.location_service import LocationService

            self.locations = LocationService.get_all(
                warehouse_id=self.current_warehouse_id,
                is_active=None,  # Hepsini getir
            )
            self.refresh_table()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Lokasyonlar yüklenemedi: {e}")

    def refresh_table(self):
        """Tabloyu yenile"""
        self.table.setRowCount(len(self.locations))

        for row, loc in enumerate(self.locations):
            # Kod
            self.table.setItem(row, 0, QTableWidgetItem(loc.code or ""))

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
            self.table.setItem(row, 8, QTableWidgetItem(str(loc.priority or 0)))

            # Durum
            status = "✅ Aktif" if loc.is_active else "❌ Pasif"
            self.table.setItem(row, 9, QTableWidgetItem(status))

            # İşlem butonları
            btn_layout = QHBoxLayout()
            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(30, 30)
            edit_btn.setProperty("location_id", loc.id)
            edit_btn.clicked.connect(
                lambda checked, lid=loc.id: self.edit_location(lid)
            )

            del_btn = QPushButton("🗑")
            del_btn.setFixedSize(30, 30)
            del_btn.clicked.connect(
                lambda checked, lid=loc.id: self.delete_location(lid)
            )

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 0, 4, 0)
            btn_layout.setSpacing(4)
            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)
            self.table.setCellWidget(row, 10, btn_widget)

        self.status_label.setText(f"Toplam: {len(self.locations)} lokasyon")

    def filter_locations(self, text: str):
        """Lokasyonları filtrele"""
        text = text.lower()
        for row in range(self.table.rowCount()):
            code = self.table.item(row, 0).text().lower()
            barcode = self.table.item(row, 1).text().lower()
            match = text in code or text in barcode
            self.table.setRowHidden(row, not match)

    def show_context_menu(self, pos):
        """Sağ tık menüsü"""
        menu = QMenu(self)
        edit_action = menu.addAction("✏️ Düzenle")
        delete_action = menu.addAction("🗑 Sil")
        menu.addSeparator()
        print_action = menu.addAction("🖨 Barkod Yazdır")

        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        row = self.table.currentRow()
        if row >= 0 and row < len(self.locations):
            loc = self.locations[row]
            if action == edit_action:
                self.edit_location(loc.id)
            elif action == delete_action:
                self.delete_location(loc.id)
            elif action == print_action:
                self.print_barcode(loc)

    def add_location(self):
        """Yeni lokasyon ekle"""
        if not self.current_warehouse_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir depo seçin!")
            return

        dialog = LocationDialog(warehouse_id=self.current_warehouse_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_locations()

    def edit_location(self, location_id: int):
        """Lokasyon düzenle"""
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
        reply = QMessageBox.question(
            self,
            "Onay",
            "Bu lokasyonu silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                from modules.inventory.services.location_service import LocationService

                LocationService.delete(location_id)
                self.load_locations()
                QMessageBox.information(self, "Başarılı", "Lokasyon silindi.")
            except ValueError as e:
                QMessageBox.warning(self, "Uyarı", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silinemedi: {e}")

    def bulk_create(self):
        """Toplu lokasyon oluşturma"""
        if not self.current_warehouse_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir depo seçin!")
            return

        dialog = BulkLocationDialog(warehouse_id=self.current_warehouse_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_locations()

    def print_barcode(self, location):
        """Lokasyon barkodunu yazdır"""
        QMessageBox.information(
            self,
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
