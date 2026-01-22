"""
Akıllı İş - Sevkiyat Form Sayfası
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QTextEdit,
    QLabel,
    QPushButton,
    QTabWidget,
    QDoubleSpinBox,
    QSpinBox,
    QMessageBox,
    QDialog,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QCheckBox,
    QGroupBox,
)
from PyQt6.QtCore import pyqtSignal, QDate, Qt
from PyQt6.QtGui import QColor
from datetime import datetime


class DeliveryNoteSelectionDialog(QDialog):
    """İrsaliye seçim diyaloğu"""

    def __init__(self, shipment_service, parent=None):
        super().__init__(parent)
        self.setWindowTitle("İrsaliye Seçimi")
        self.resize(800, 500)
        self.service = shipment_service
        self.selected_notes = []
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Liste
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Seç", "İrsaliye No", "Tarih", "Müşteri", "Toplam Kalem", "Açıklama"]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Seçilenleri Ekle")
        save_btn.clicked.connect(self.accept_selection)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def load_data(self):
        notes = self.service.get_available_delivery_notes()
        self.table.setRowCount(len(notes))

        for i, note in enumerate(notes):
            # Checkbox
            chk_widget = QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.setContentsMargins(0, 0, 0, 0)
            chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk = QCheckBox()
            chk.setProperty("note_data", note)  # Nesneyi sakla
            chk_layout.addWidget(chk)
            self.table.setCellWidget(i, 0, chk_widget)

            # Bilgiler
            self.table.setItem(i, 1, QTableWidgetItem(note.delivery_no))
            self.table.setItem(
                i, 2, QTableWidgetItem(note.delivery_date.strftime("%d.%m.%Y"))
            )
            customer_name = note.customer.name if note.customer else "-"
            self.table.setItem(i, 3, QTableWidgetItem(customer_name))
            self.table.setItem(i, 4, QTableWidgetItem(str(len(note.items))))
            self.table.setItem(i, 5, QTableWidgetItem(note.notes or ""))

    def accept_selection(self):
        self.selected_notes = []
        for i in range(self.table.rowCount()):
            widget = self.table.cellWidget(i, 0)
            chk = widget.findChild(QCheckBox)
            if chk and chk.isChecked():
                self.selected_notes.append(chk.property("note_data"))
        self.accept()


class ShipmentFormPage(QWidget):
    """Sevkiyat ekleme/düzenleme formu"""

    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()

    def __init__(
        self,
        shipment_service,
        shipment_data: dict = None,
        vehicles: list = None,
        drivers: list = None,
        parent=None,
    ):
        super().__init__(parent)
        self.service = shipment_service
        self.shipment_data = shipment_data
        self.vehicles = vehicles or []
        self.drivers = drivers or []
        self.selected_delivery_notes = []  # Seçilen irsaliyeler
        self.is_edit = shipment_data is not None

        # Yükleme verileri
        self.shipment_loads = []
        if self.shipment_data and "loads" in self.shipment_data:
            self.shipment_loads = self.shipment_data["loads"]

        self.setup_ui()
        if self.is_edit:
            self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        title_text = "📦 Sevkiyat Düzenle" if self.is_edit else "📦 Yeni Sevkiyat"
        title = QLabel(title_text)
        title.setObjectName("formTitle")
        header_layout.addWidget(title)
        header_layout.addStretch()

        cancel_btn = QPushButton("❌ İptal")
        cancel_btn.clicked.connect(self.cancelled.emit)
        header_layout.addWidget(cancel_btn)

        save_btn = QPushButton("💾 Kaydet")
        save_btn.clicked.connect(self._save)
        header_layout.addWidget(save_btn)

        layout.addLayout(header_layout)

        # Tab Widget
        self.tabs = QTabWidget()

        # Tab 1: Temel Bilgiler
        tab1 = self._create_basic_tab()
        self.tabs.addTab(tab1, "📋 Temel Bilgiler")

        # Tab 2: Yük Bilgileri
        tab2 = self._create_load_tab()
        self.tabs.addTab(tab2, "📦 Yük Bilgileri")

        # Tab 3: Notlar
        tab3 = self._create_notes_tab()
        self.tabs.addTab(tab3, "📝 Notlar")

        # Tab 4: Barkodlu Yükleme (Operasyon)
        tab4 = self._create_loading_tab()
        self.tabs.addTab(tab4, "📲 Barkodlu Yükleme")

        layout.addWidget(self.tabs)

    def _create_label(self, text: str) -> QLabel:
        """Standart form etiketi"""
        label = QLabel(text)
        label.setMinimumWidth(140)
        return label

    def _create_basic_tab(self) -> QWidget:
        """Temel bilgiler sekmesi"""
        tab = QWidget()
        layout = QGridLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        layout.setColumnMinimumWidth(0, 150)

        row = 0

        # Sevkiyat No
        layout.addWidget(self._create_label("Sevkiyat No"), row, 0)
        self.shipment_no_input = QLineEdit()
        self.shipment_no_input.setPlaceholderText("Otomatik oluşturulur")
        self.shipment_no_input.setEnabled(False)
        layout.addWidget(self.shipment_no_input, row, 1)
        row += 1

        # Sevkiyat Tarihi
        layout.addWidget(self._create_label("Sevkiyat Tarihi *"), row, 0)
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("dd.MM.yyyy")
        self.date_input.setDate(QDate.currentDate())
        layout.addWidget(self.date_input, row, 1)
        row += 1

        # Durum
        layout.addWidget(self._create_label("Durum"), row, 0)
        self.status_combo = QComboBox()
        self.status_combo.addItem("Planlandı", "planlandi")
        self.status_combo.addItem("Yükleniyor", "yukleniyor")
        self.status_combo.addItem("Yolda", "yolda")
        self.status_combo.addItem("Teslim Edildi", "teslim")
        self.status_combo.addItem("İptal", "iptal")
        layout.addWidget(self.status_combo, row, 1)
        row += 1

        # Araç
        layout.addWidget(self._create_label("Araç"), row, 0)
        self.vehicle_combo = QComboBox()
        self.vehicle_combo.addItem("-- Araç Seçiniz --", None)
        for v in self.vehicles:
            display = f"{v.get('plate_no')} - {v.get('vehicle_type_display', '')}"
            if v.get("capacity_kg"):
                display += f" ({v.get('capacity_kg'):,.0f} kg)"
            self.vehicle_combo.addItem(display, v.get("id"))
        self.vehicle_combo.currentIndexChanged.connect(self._on_vehicle_changed)
        layout.addWidget(self.vehicle_combo, row, 1)
        row += 1

        # Sürücü
        layout.addWidget(self._create_label("Sürücü"), row, 0)
        self.driver_combo = QComboBox()
        self.driver_combo.addItem("-- Sürücü Seçiniz --", None)
        for d in self.drivers:
            display = f"{d.get('name')}"
            if d.get("default_vehicle"):
                display += f" ({d.get('default_vehicle')})"
            self.driver_combo.addItem(display, d.get("id"))
        layout.addWidget(self.driver_combo, row, 1)
        row += 1

        layout.setRowStretch(row, 1)
        return tab

    def _create_load_tab(self) -> QWidget:
        """Yük bilgileri sekmesi"""
        tab = QWidget()
        layout = QGridLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # --- İrsaliye Seçimi ---
        dn_group = QWidget()
        dn_layout = QVBoxLayout(dn_group)
        dn_layout.setContentsMargins(0, 0, 0, 0)

        dn_header = QHBoxLayout()
        dn_header.addWidget(QLabel("<b>Seçili İrsaliyeler</b>"))
        dn_header.addStretch()
        add_dn_btn = QPushButton("➕ İrsaliye Ekle")
        add_dn_btn.clicked.connect(self._open_delivery_note_selection)
        dn_header.addWidget(add_dn_btn)
        dn_layout.addLayout(dn_header)

        self.dn_table = QTableWidget()
        self.dn_table.setColumnCount(4)
        self.dn_table.setHorizontalHeaderLabels(
            ["İrsaliye No", "Müşteri", "Tarih", "İşlem"]
        )
        self.dn_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.dn_table.setMaximumHeight(200)
        dn_layout.addWidget(self.dn_table)

        layout.addWidget(dn_group, 0, 0, 1, 2)

        # --- Toplamlar ---
        row = 1
        layout.addWidget(self._create_label("Toplam Ağırlık"), row, 0)
        self.weight_input = QDoubleSpinBox()
        self.weight_input.setRange(0, 100000)
        self.weight_input.setDecimals(1)
        self.weight_input.setSuffix(" kg")
        self.weight_input.valueChanged.connect(self._check_capacity)
        layout.addWidget(self.weight_input, row, 1)
        row += 1

        layout.addWidget(self._create_label("Toplam Hacim"), row, 0)
        self.volume_input = QDoubleSpinBox()
        self.volume_input.setRange(0, 200)
        self.volume_input.setDecimals(2)
        self.volume_input.setSuffix(" m³")
        self.volume_input.valueChanged.connect(self._check_capacity)
        layout.addWidget(self.volume_input, row, 1)
        row += 1

        layout.addWidget(self._create_label("Toplam Palet"), row, 0)
        self.pallet_input = QSpinBox()
        self.pallet_input.setRange(0, 100)
        self.pallet_input.setSuffix(" palet")
        self.pallet_input.valueChanged.connect(self._check_capacity)
        layout.addWidget(self.pallet_input, row, 1)
        row += 1

        # Kapasite uyarısı
        self.capacity_warning = QLabel("")
        self.capacity_warning.setStyleSheet("color: #ef4444; font-weight: bold;")
        self.capacity_warning.hide()
        layout.addWidget(self.capacity_warning, row, 0, 1, 2)
        row += 1

        layout.setRowStretch(row, 1)
        return tab

    def _open_delivery_note_selection(self):
        """İrsaliye seçim diyaloğunu aç"""
        dialog = DeliveryNoteSelectionDialog(self.service, self)
        if dialog.exec():
            # Yeni seçilenleri mevcut listeye ekle (tekrarı önle)
            current_ids = {dn.id for dn in self.selected_delivery_notes}
            for note in dialog.selected_notes:
                if note.id not in current_ids:
                    self.selected_delivery_notes.append(note)

            self._update_dn_table()
            self._calculate_totals_from_notes()

    def _update_dn_table(self):
        """İrsaliye tablosunu güncelle"""
        self.dn_table.setRowCount(len(self.selected_delivery_notes))
        for i, dn in enumerate(self.selected_delivery_notes):
            self.dn_table.setItem(i, 0, QTableWidgetItem(dn.delivery_no))
            c_name = dn.customer.name if dn.customer else "-"
            self.dn_table.setItem(i, 1, QTableWidgetItem(c_name))
            d_date = dn.delivery_date.strftime("%d.%m.%Y") if dn.delivery_date else "-"
            self.dn_table.setItem(i, 2, QTableWidgetItem(d_date))

            # Sil butonu
            remove_btn = QPushButton("🗑️")
            remove_btn.setFixedSize(30, 24)
            remove_btn.clicked.connect(lambda checked, idx=i: self._remove_note(idx))
            self.dn_table.setCellWidget(i, 3, remove_btn)

    def _remove_note(self, index):
        """Listeden irsaliye çıkar"""
        if 0 <= index < len(self.selected_delivery_notes):
            self.selected_delivery_notes.pop(index)
            self._update_dn_table()
            self._calculate_totals_from_notes()

    def _calculate_totals_from_notes(self):
        """Seçili irsaliyelerden toplamları hesapla"""
        total_weight = 0.0
        # Not: Şu an DeliveryNoteItem'da weight alanı yok, ileride eklenmeli.
        # Şimdilik miktar üzerinden yapay bir hesaplama veya manuel girişe izin verilmeli.
        # Eğer item.weight varsa: total_weight += item.quantity * item.item.weight

        # Kullanıcı manuel düzeltebilsin diye sadece 0 ise dokunmuyoruz,
        # ama burada otomatik hesaplama mantığı olmalıydı.
        # Şimdilik kullanıcıya bırakıyoruz veya basit mantık ekleyebiliriz.
        pass

    def _create_notes_tab(self) -> QWidget:
        """Notlar sekmesi"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)

        layout.addWidget(
            QLabel("Sevkiyat hakkında ek notlar, teslimat adresi detayları:")
        )
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Sevkiyat hakkında ek notlar...")
        layout.addWidget(self.notes_input)

        return tab

    def _on_vehicle_changed(self, index):
        """Araç değiştiğinde sürücüyü otomatik seç"""
        vehicle_id = self.vehicle_combo.currentData()
        if vehicle_id:
            # Bu araç için varsayılan sürücüyü bul
            for d in self.drivers:
                if d.get("default_vehicle_id") == vehicle_id:
                    driver_index = self.driver_combo.findData(d.get("id"))
                    if driver_index >= 0:
                        self.driver_combo.setCurrentIndex(driver_index)
                    break
        self._check_capacity()

    def _check_capacity(self):
        """Kapasite kontrolü"""
        vehicle_id = self.vehicle_combo.currentData()
        if not vehicle_id:
            self.capacity_warning.hide()
            return

        # Seçili aracı bul
        vehicle = None
        for v in self.vehicles:
            if v.get("id") == vehicle_id:
                vehicle = v
                break

        if not vehicle:
            self.capacity_warning.hide()
            return

        warnings = []

        # Ağırlık kontrolü
        if vehicle.get("capacity_kg") and self.weight_input.value() > vehicle.get(
            "capacity_kg"
        ):
            warnings.append(
                f"⚠️ Ağırlık kapasitesi aşıldı! (Max: {vehicle.get('capacity_kg'):,.0f} kg)"
            )

        # Hacim kontrolü
        if vehicle.get("capacity_m3") and self.volume_input.value() > vehicle.get(
            "capacity_m3"
        ):
            warnings.append(
                f"⚠️ Hacim kapasitesi aşıldı! (Max: {vehicle.get('capacity_m3'):,.1f} m³)"
            )

        # Palet kontrolü
        if vehicle.get("pallet_capacity") and self.pallet_input.value() > vehicle.get(
            "pallet_capacity"
        ):
            warnings.append(
                f"⚠️ Palet kapasitesi aşıldı! (Max: {vehicle.get('pallet_capacity')} palet)"
            )

        if warnings:
            self.capacity_warning.setText("\n".join(warnings))
            self.capacity_warning.show()
        else:
            self.capacity_warning.hide()

    def load_data(self):
        """Mevcut sevkiyat verisini forma yükle"""
        if not self.shipment_data:
            return

        self.shipment_no_input.setText(self.shipment_data.get("shipment_no", ""))

        # Tarih
        shipment_date = self.shipment_data.get("shipment_date")
        if shipment_date:
            self.date_input.setDate(QDate.fromString(shipment_date, "yyyy-MM-dd"))

        # Durum
        status = self.shipment_data.get("status", "planlandi")
        index = self.status_combo.findData(status)
        if index >= 0:
            self.status_combo.setCurrentIndex(index)

        # Araç
        vehicle_id = self.shipment_data.get("vehicle_id")
        if vehicle_id:
            index = self.vehicle_combo.findData(vehicle_id)
            if index >= 0:
                self.vehicle_combo.setCurrentIndex(index)

        # Sürücü
        driver_id = self.shipment_data.get("driver_id")
        if driver_id:
            index = self.driver_combo.findData(driver_id)
            if index >= 0:
                self.driver_combo.setCurrentIndex(index)

        # Yük bilgileri
        self.weight_input.setValue(float(self.shipment_data.get("total_weight_kg", 0)))
        self.volume_input.setValue(float(self.shipment_data.get("total_volume_m3", 0)))
        self.pallet_input.setValue(self.shipment_data.get("total_pallets", 0))

        self.notes_input.setText(self.shipment_data.get("notes", ""))

        # Yükleme tablosunu güncelle
        self._update_loading_table()

    def _save(self):
        """Form verisini kaydet"""
        data = {
            "shipment_date": self.date_input.date().toString("yyyy-MM-dd"),
            "status": self.status_combo.currentData(),
            "vehicle_id": self.vehicle_combo.currentData(),
            "driver_id": self.driver_combo.currentData(),
            "total_weight_kg": self.weight_input.value() or 0,
            "total_volume_m3": self.volume_input.value() or 0,
            "total_pallets": self.pallet_input.value() or 0,
            "notes": self.notes_input.toPlainText().strip() or None,
            "loads": self.shipment_loads,  # Yükleme verileri
        }

        if self.is_edit and self.shipment_data:
            data["id"] = self.shipment_data.get("id")
            data["shipment_no"] = self.shipment_data.get("shipment_no")

        # İrsaliye ID'leri
        dn_ids = [dn.id for dn in self.selected_delivery_notes]
        data["delivery_note_ids"] = dn_ids

    def _create_loading_tab(self) -> QWidget:
        """Barkodlu yükleme sekmesi"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # 1. Barkod Girişi ve Kiosk Butonu
        input_group = QGroupBox("Barkod Okutma")
        input_layout = QHBoxLayout(input_group)

        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("SSCC Barkodunu okutunuz...")
        self.barcode_input.returnPressed.connect(self._check_barcode)
        input_layout.addWidget(self.barcode_input, stretch=3)

        kiosk_btn = QPushButton("📱 Kiosk Modunu Aç")
        kiosk_btn.setStyleSheet(
            "background-color: #3b82f6; color: white; font-weight: bold; padding: 5px;"
        )
        kiosk_btn.clicked.connect(self._open_kiosk)
        input_layout.addWidget(kiosk_btn, stretch=1)

        layout.addWidget(input_group)

        # 2. Yükleme Listesi
        list_group = QGroupBox("Yükleme Durumu")
        list_layout = QVBoxLayout(list_group)

        self.loading_table = QTableWidget()
        self.loading_table.setColumnCount(3)
        self.loading_table.setHorizontalHeaderLabels(
            ["SSCC / Palet", "Durum", "Yükleme Zamanı"]
        )
        self.loading_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        list_layout.addWidget(self.loading_table)

        layout.addWidget(list_group)

        # 3. İlerleme
        self.progress_label = QLabel("Bekleniyor...")
        self.progress_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.progress_label)

        return tab

    def _open_kiosk(self):
        """Kiosk modunu aç"""
        from modules.shipping.views.kiosk import ShipmentLoadingKiosk

        shipment_no = self.shipment_no_input.text() or "Yeni Sevkiyat"
        dialog = ShipmentLoadingKiosk(shipment_no, self.shipment_loads, self)
        dialog.exec()

        # Kiosk kapanınca tabloyu güncelle
        self._update_loading_table()

    def _check_barcode(self):
        """Barkod kontrolü"""
        barcode = self.barcode_input.text().strip()
        if not barcode:
            return

        self.barcode_input.clear()

        # Beklenen yükler içinde ara
        found = False
        for load in self.shipment_loads:
            # SSCC eşleşmesi (veya transport_unit_id üzerinden)
            # load verisi: {'id': ..., 'sscc': ..., 'loaded_at': ...}
            if load.get("sscc") == barcode:
                found = True
                if load.get("loaded_at"):
                    QMessageBox.warning(
                        self, "Uyarı", f"Bu palet zaten yüklendi: {barcode}"
                    )
                else:
                    # Yüklendi olarak işaretle
                    load["loaded_at"] = datetime.now().isoformat()
                    # UI Güncelle
                    self._update_loading_table()
                    # Başarılı ses/toast eklenebilir
                break

        if not found:
            # Hatalı barkod
            QMessageBox.critical(
                self, "Hata", f"Bu sevkiyata ait olmayan barkod: {barcode}"
            )

        self.barcode_input.setFocus()

    def _update_loading_table(self):
        """Yükleme tablosunu güncelle"""
        self.loading_table.setRowCount(len(self.shipment_loads))

        loaded_count = 0
        total_count = len(self.shipment_loads)

        for i, load in enumerate(self.shipment_loads):
            sscc = load.get("sscc", "-")
            loaded_at = load.get("loaded_at")

            self.loading_table.setItem(i, 0, QTableWidgetItem(sscc))

            if loaded_at:
                status_item = QTableWidgetItem("YÜKLENDİ")
                status_item.setBackground(QColor("#dcfce7"))  # Yeşil
                date_str = (
                    datetime.fromisoformat(loaded_at).strftime("%H:%M:%S")
                    if isinstance(loaded_at, str)
                    else str(loaded_at)
                )
                loaded_count += 1
            else:
                status_item = QTableWidgetItem("BEKLİYOR")
                status_item.setBackground(QColor("#fee2e2"))  # Kırmızı
                date_str = "-"

            self.loading_table.setItem(i, 1, status_item)
            self.loading_table.setItem(i, 2, QTableWidgetItem(date_str))

        # İlerleme güncelle
        if total_count > 0:
            percentage = int((loaded_count / total_count) * 100)
            self.progress_label.setText(
                f"Yüklenen: {loaded_count} / {total_count} (%{percentage})"
            )
            if loaded_count == total_count:
                self.progress_label.setStyleSheet(
                    "color: green; font-weight: bold; font-size: 16px;"
                )
            else:
                self.progress_label.setStyleSheet(
                    "color: orange; font-weight: bold; font-size: 14px;"
                )
