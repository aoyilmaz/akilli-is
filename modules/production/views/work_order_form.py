"""
Akıllı İş - İş Emri Form Sayfası
V4 - Makine seçilince otomatik operasyon değerleri
"""

from typing import Optional
from decimal import Decimal
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QDoubleSpinBox,
    QSpinBox,
    QFrame,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QTabWidget,
    QGridLayout,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QScrollArea,
    QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDateTime, QDate
from PyQt6.QtGui import QColor, QFont


class OperationDialog(QDialog):
    """Operasyon ekleme/düzenleme dialogu"""

    def __init__(self, work_stations: list, operation_data: dict = None, parent=None):
        super().__init__(parent)
        self.work_stations = work_stations
        self.operation_data = operation_data
        self.setWindowTitle(
            "Operasyon Ekle" if not operation_data else "Operasyon Düzenle"
        )
        self.setMinimumWidth(450)
        self.setup_ui()
        if operation_data:
            self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Form
        form_layout = QGridLayout()
        form_layout.setSpacing(12)

        # İş İstasyonu (En üstte - seçilince diğerleri dolacak)
        form_layout.addWidget(QLabel("İş İstasyonu *"), 0, 0)
        self.station_combo = QComboBox()
        self.station_combo.addItem("Seçiniz...", None)
        for ws in self.work_stations:
            type_icons = {
                "machine": "⚙️",
                "workstation": "🔧",
                "assembly": "🏭",
                "manual": "👷",
            }
            icon = type_icons.get(ws.get("station_type", "machine"), "⚙️")
            self.station_combo.addItem(
                f"{icon} {ws.get('code', '')} - {ws.get('name', '')}", ws.get("id")
            )
        self.station_combo.currentIndexChanged.connect(self._on_station_changed)
        form_layout.addWidget(self.station_combo, 0, 1)

        # Operasyon No
        form_layout.addWidget(QLabel("Operasyon No *"), 1, 0)
        self.op_no_input = QSpinBox()
        self.op_no_input.setRange(1, 999)
        self.op_no_input.setValue(10)
        form_layout.addWidget(self.op_no_input, 1, 1)

        # Operasyon Adı
        form_layout.addWidget(QLabel("Operasyon Adı *"), 2, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Makine seçilince otomatik dolar")
        form_layout.addWidget(self.name_input, 2, 1)

        # Kurulum Süresi
        form_layout.addWidget(QLabel("Kurulum Süresi (dk)"), 3, 0)
        self.setup_time_input = QSpinBox()
        self.setup_time_input.setRange(0, 9999)
        self.setup_time_input.setValue(0)
        form_layout.addWidget(self.setup_time_input, 3, 1)

        # Birim Çalışma Süresi
        form_layout.addWidget(QLabel("Birim Çalışma Süresi (dk)"), 4, 0)
        self.run_time_input = QDoubleSpinBox()
        self.run_time_input.setRange(0, 9999)
        self.run_time_input.setDecimals(4)
        self.run_time_input.setValue(0)
        form_layout.addWidget(self.run_time_input, 4, 1)

        # Açıklama
        form_layout.addWidget(QLabel("Açıklama"), 5, 0)
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(60)
        form_layout.addWidget(self.description_input, 5, 1)

        layout.addLayout(form_layout)

        # Bilgi kutusu
        info_frame = QFrame()
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(12, 8, 12, 8)
        self.info_label = QLabel(
            "ℹ️ İş istasyonu seçildiğinde varsayılan değerler otomatik doldurulur"
        )
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)
        layout.addWidget(info_frame)

        # Butonlar
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("💾 Kaydet")
        save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _on_station_changed(self):
        """İş istasyonu değiştiğinde varsayılan değerleri doldur"""
        station_id = self.station_combo.currentData()
        if not station_id:
            return

        # Seçilen istasyonu bul
        for ws in self.work_stations:
            if ws.get("id") == station_id:
                # Varsayılan değerleri doldur
                default_name = ws.get("default_operation_name", "")
                default_setup = ws.get("default_setup_time", 0)
                default_run = ws.get("default_run_time_per_unit", 0)

                # Debug log
                print(f"\n=== İş İstasyonu Değişti ===")
                print(f"Kod: {ws.get('code')}, Ad: {ws.get('name')}")
                print(f"Varsayılan operasyon: '{default_name}'")
                print(f"Varsayılan kurulum: {default_setup} dk")
                print(f"Varsayılan birim süre: {default_run} dk")
                print(f"Mevcut operasyon adı: '{self.name_input.text()}'")
                print(f"Mevcut kurulum: {self.setup_time_input.value()} dk")
                print(f"Mevcut birim süre: {self.run_time_input.value()} dk")

                if default_name and not self.name_input.text():
                    print(f"-> Operasyon adı dolduruldu: '{default_name}'")
                    self.name_input.setText(default_name)
                if default_setup and self.setup_time_input.value() == 0:
                    print(f"-> Kurulum süresi dolduruldu: {default_setup} dk")
                    self.setup_time_input.setValue(int(default_setup))
                if default_run and self.run_time_input.value() == 0:
                    print(f"-> Birim süre dolduruldu: {default_run} dk")
                    self.run_time_input.setValue(float(default_run))

                # Bilgi güncelle
                self.info_label.setText(
                    f"✅ {ws.get('name', '')} seçildi\n"
                    f"Varsayılan: {default_name or '-'}, "
                    f"Kurulum: {default_setup} dk, "
                    f"Birim süre: {default_run} dk"
                )
                break

    def load_data(self):
        """Mevcut operasyon verilerini yükle"""
        if not self.operation_data:
            return
        self.op_no_input.setValue(self.operation_data.get("operation_no", 10))
        self.name_input.setText(self.operation_data.get("name", ""))
        self.setup_time_input.setValue(int(self.operation_data.get("setup_time", 0)))
        self.run_time_input.setValue(float(self.operation_data.get("run_time", 0)))
        self.description_input.setPlainText(self.operation_data.get("description", ""))

        # İş istasyonu seç
        station_id = self.operation_data.get("work_station_id")
        if station_id:
            for i in range(self.station_combo.count()):
                if self.station_combo.itemData(i) == station_id:
                    self.station_combo.setCurrentIndex(i)
                    break

    def _on_save(self):
        """Kaydet"""
        station_id = self.station_combo.currentData()
        if not station_id:
            QMessageBox.warning(self, "Uyarı", "İş istasyonu seçimi zorunludur!")
            return

        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Uyarı", "Operasyon adı zorunludur!")
            return

        self.accept()

    def get_data(self) -> dict:
        """Operasyon verilerini döndür"""
        return {
            "operation_no": self.op_no_input.value(),
            "name": self.name_input.text().strip(),
            "work_station_id": self.station_combo.currentData(),
            "setup_time": self.setup_time_input.value(),
            "run_time": self.run_time_input.value(),
            "description": self.description_input.toPlainText().strip(),
        }


class WorkOrderFormPage(QWidget):
    """İş emri formu"""

    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()
    order_no_requested = pyqtSignal()
    bom_selected = pyqtSignal(int)

    def __init__(self, wo_data: Optional[dict] = None, parent=None):
        super().__init__(parent)
        self.wo_data = wo_data
        self.is_edit_mode = wo_data is not None
        self.materials = []
        self.operations = []
        self.work_stations = []
        self.setup_ui()
        if self.is_edit_mode:
            self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Başlık
        header_layout = QHBoxLayout()

        back_btn = QPushButton("← Geri")
        back_btn.clicked.connect(self.cancelled.emit)
        header_layout.addWidget(back_btn)

        title_text = "İş Emri Düzenle" if self.is_edit_mode else "Yeni İş Emri"
        title = QLabel(f"📋 {title_text}")
        header_layout.addWidget(title)
        header_layout.addStretch()

        save_btn = QPushButton("💾 Kaydet")
        save_btn.clicked.connect(self._on_save)
        header_layout.addWidget(save_btn)

        layout.addLayout(header_layout)

        # Tab Widget
        tabs = QTabWidget()
        tabs.addTab(self._create_general_tab(), "📝 Genel Bilgiler")
        tabs.addTab(self._create_materials_tab(), "📦 Malzemeler")
        tabs.addTab(self._create_operations_tab(), "⚙️ Operasyonlar")
        tabs.addTab(self._create_notes_tab(), "📝 Notlar")
        tabs.addTab(self._create_schedule_tab(), "📅 Planlama")

        layout.addWidget(tabs)

    def _create_general_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)

        form_frame = QFrame()
        form_frame.setStyleSheet(
            "QFrame { background-color: rgba(30, 41, 59, 0.3); border: 1px solid #334155; border-radius: 12px; }"
        )
        form_layout = QGridLayout(form_frame)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(16)

        # İş Emri No
        form_layout.addWidget(QLabel("İş Emri No *"), 0, 0)
        no_layout = QHBoxLayout()
        self.order_no_input = QLineEdit()
        self.order_no_input.setPlaceholderText("WO202501001")
        no_layout.addWidget(self.order_no_input)

        auto_btn = QPushButton("🔄")
        auto_btn.setFixedSize(40, 40)
        auto_btn.clicked.connect(self.order_no_requested.emit)
        no_layout.addWidget(auto_btn)
        form_layout.addLayout(no_layout, 0, 1)

        # Mamul Seçimi
        form_layout.addWidget(QLabel("Mamul *"), 1, 0)
        self.product_combo = QComboBox()
        self.product_combo.currentIndexChanged.connect(self._on_product_changed)
        form_layout.addWidget(self.product_combo, 1, 1)

        # Reçete Seçimi
        form_layout.addWidget(QLabel("Reçete *"), 2, 0)
        self.bom_combo = QComboBox()
        self.bom_combo.currentIndexChanged.connect(self._on_bom_changed)
        form_layout.addWidget(self.bom_combo, 2, 1)

        # Üretim Miktarı
        form_layout.addWidget(QLabel("Üretim Miktarı *"), 3, 0)
        qty_layout = QHBoxLayout()
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setRange(0.0001, 999999999)
        self.quantity_input.setDecimals(4)
        self.quantity_input.setValue(1)
        self.quantity_input.valueChanged.connect(self._update_materials)
        self.quantity_input.valueChanged.connect(self._update_operations_table)
        qty_layout.addWidget(self.quantity_input)

        self.unit_label = QLabel("ADET")
        qty_layout.addWidget(self.unit_label)
        form_layout.addLayout(qty_layout, 3, 1)

        # Öncelik
        form_layout.addWidget(QLabel("Öncelik"), 4, 0)
        self.priority_combo = QComboBox()
        self.priority_combo.addItem("Düşük", "low")
        self.priority_combo.addItem("Normal", "normal")
        self.priority_combo.addItem("Yüksek", "high")
        self.priority_combo.addItem("Acil", "urgent")
        self.priority_combo.setCurrentIndex(1)
        form_layout.addWidget(self.priority_combo, 4, 1)

        # Parti No (Batch)
        form_layout.addWidget(QLabel("Parti No"), 5, 0)
        self.batch_input = QLineEdit()
        self.batch_input.setPlaceholderText("Otomatik üretilir veya manuel girin")
        self.batch_input.setToolTip(
            "Boş bırakılırsa ve ürün lot takipli ise otomatik üretilir"
        )
        form_layout.addWidget(self.batch_input, 5, 1)

        # Kaynak Depo
        form_layout.addWidget(QLabel("Hammadde Deposu"), 6, 0)
        self.source_warehouse_combo = QComboBox()
        form_layout.addWidget(self.source_warehouse_combo, 6, 1)

        # Hedef Depo
        form_layout.addWidget(QLabel("Mamul Deposu"), 7, 0)
        self.target_warehouse_combo = QComboBox()
        form_layout.addWidget(self.target_warehouse_combo, 7, 1)

        # Açıklama
        form_layout.addWidget(QLabel("Açıklama"), 8, 0)
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        form_layout.addWidget(self.description_input, 8, 1)

        layout.addWidget(form_frame)

        # Maliyet özeti
        cost_frame = QFrame()
        cost_frame.setStyleSheet(
            "QFrame { background-color: rgba(16, 185, 129, 0.1); border: 1px solid #10b98140; border-radius: 12px; }"
        )
        cost_layout = QHBoxLayout(cost_frame)
        cost_layout.setContentsMargins(20, 16, 20, 16)

        self.material_cost_label = QLabel("Malzeme: ₺0")
        cost_layout.addWidget(self.material_cost_label)

        cost_layout.addStretch()

        self.total_cost_label = QLabel("Toplam Tahmini Maliyet: ₺0")
        cost_layout.addWidget(self.total_cost_label)

        layout.addWidget(cost_frame)
        layout.addStretch()

        return tab

    def _create_materials_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Bilgi
        info_label = QLabel("ℹ️ Malzemeler seçilen reçeteye göre otomatik hesaplanır")
        layout.addWidget(info_label)

        # Tablo
        self.materials_table = QTableWidget()
        columns = [
            ("Malzeme Kodu", 120),
            ("Malzeme Adı", 200),
            ("Gerekli Miktar", 120),
            ("Birim", 80),
            ("Mevcut Stok", 120),
            ("Eksik", 100),
            ("Birim Maliyet", 110),
            ("Toplam Maliyet", 120),
        ]

        self.materials_table.setColumnCount(len(columns))
        self.materials_table.setHorizontalHeaderLabels([c[0] for c in columns])

        header = self.materials_table.horizontalHeader()
        for i, (_, width) in enumerate(columns):
            if i == 1:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                self.materials_table.setColumnWidth(i, width)

        self.materials_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.materials_table.verticalHeader().setVisible(False)
        layout.addWidget(self.materials_table)

        # Özet
        summary_layout = QHBoxLayout()

        self.materials_count_label = QLabel("Toplam: 0 malzeme")
        summary_layout.addWidget(self.materials_count_label)

        summary_layout.addStretch()

        self.shortage_label = QLabel("")
        summary_layout.addWidget(self.shortage_label)

        layout.addLayout(summary_layout)

        return tab

    def _create_notes_tab(self) -> QWidget:
        """Özel notlar tabı"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # Üretim Notları
        prod_group = QGroupBox("🔧 Üretim Açıklaması")
        prod_layout = QVBoxLayout(prod_group)
        self.production_notes_input = QTextEdit()
        self.production_notes_input.setPlaceholderText(
            "Üretim bandı için özel talimatlar..."
        )
        prod_layout.addWidget(self.production_notes_input)
        scroll_layout.addWidget(prod_group)

        # Kalite Notları
        qual_group = QGroupBox("🛡️ Kalite ve Kontrol Notları")
        qual_layout = QVBoxLayout(qual_group)
        self.quality_notes_input = QTextEdit()
        self.quality_notes_input.setPlaceholderText(
            "Kritik kontrol noktaları ve kalite standartları..."
        )
        qual_layout.addWidget(self.quality_notes_input)
        scroll_layout.addWidget(qual_group)

        # Sevkiyat Notları
        ship_group = QGroupBox("📦 Sevkiyat ve Paketleme Talimatı")
        ship_layout = QVBoxLayout(ship_group)
        self.shipping_notes_input = QTextEdit()
        self.shipping_notes_input.setPlaceholderText(
            "Paketleme şekli ve sevkiyat özel istekleri..."
        )
        ship_layout.addWidget(self.shipping_notes_input)
        scroll_layout.addWidget(ship_group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        return tab

    def _create_operations_tab(self) -> QWidget:
        """Operasyonlar sekmesi"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Üst toolbar
        toolbar_layout = QHBoxLayout()

        info_label = QLabel("⚙️ Üretim operasyonlarını ve makineleri tanımlayın")
        toolbar_layout.addWidget(info_label)

        toolbar_layout.addStretch()

        # Operasyon Ekle butonu
        add_op_btn = QPushButton("➕ Operasyon Ekle")
        add_op_btn.clicked.connect(self._add_operation)
        toolbar_layout.addWidget(add_op_btn)

        layout.addLayout(toolbar_layout)

        # Tablo
        self.operations_table = QTableWidget()
        columns = [
            ("No", 50),
            ("Operasyon Adı", 180),
            ("İş İstasyonu", 200),
            ("Kurulum (dk)", 90),
            ("Birim Süre (dk)", 100),
            ("Toplam Süre", 100),
            ("İşlem", 80),
        ]

        self.operations_table.setColumnCount(len(columns))
        self.operations_table.setHorizontalHeaderLabels([c[0] for c in columns])

        header = self.operations_table.horizontalHeader()
        for i, (_, width) in enumerate(columns):
            if i == 1 or i == 2:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                self.operations_table.setColumnWidth(i, width)

        self.operations_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.operations_table.verticalHeader().setVisible(False)
        layout.addWidget(self.operations_table)

        # Özet
        summary_layout = QHBoxLayout()

        self.operations_count_label = QLabel("Toplam: 0 operasyon")
        summary_layout.addWidget(self.operations_count_label)

        summary_layout.addStretch()

        self.total_time_label = QLabel("Toplam Süre: 0 dakika")
        summary_layout.addWidget(self.total_time_label)

        layout.addLayout(summary_layout)

        return tab

    def _create_schedule_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)

        form_frame = QFrame()
        form_frame.setStyleSheet(
            "QFrame { background-color: rgba(30, 41, 59, 0.3); border: 1px solid #334155; border-radius: 12px; }"
        )
        form_layout = QGridLayout(form_frame)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(16)

        # Planlanan Başlangıç
        form_layout.addWidget(QLabel("Planlanan Başlangıç"), 0, 0)
        self.planned_start_input = QDateTimeEdit()
        self.planned_start_input.setDateTime(QDateTime.currentDateTime())
        self.planned_start_input.setCalendarPopup(True)
        form_layout.addWidget(self.planned_start_input, 0, 1)

        # Planlanan Bitiş
        form_layout.addWidget(QLabel("Planlanan Bitiş"), 1, 0)
        self.planned_end_input = QDateTimeEdit()
        self.planned_end_input.setDateTime(QDateTime.currentDateTime().addDays(1))
        self.planned_end_input.setCalendarPopup(True)
        form_layout.addWidget(self.planned_end_input, 1, 1)

        # Tahmini Süre (bilgi)
        form_layout.addWidget(QLabel("Tahmini Süre"), 2, 0)
        self.estimated_time_label = QLabel("Operasyonlardan hesaplanacak")
        form_layout.addWidget(self.estimated_time_label, 2, 1)

        # Otomatik hesapla butonu
        auto_calc_btn = QPushButton("🔄 Bitiş Tarihini Otomatik Hesapla")
        auto_calc_btn.clicked.connect(self._auto_calculate_end_time)
        form_layout.addWidget(auto_calc_btn, 3, 1)

        layout.addWidget(form_frame)
        layout.addStretch()

        return tab

    def set_products(self, products: list):
        """Mamul listesini ayarla"""
        self.product_combo.clear()
        self.product_combo.addItem("Seçiniz...", None)
        for p in products:
            self.product_combo.addItem(f"{p.code} - {p.name}", p.id)

    def set_boms_for_product(self, boms: list):
        """Seçilen mamulün reçetelerini ayarla"""
        self.bom_combo.clear()
        self.bom_combo.addItem("Seçiniz...", None)
        for b in boms:
            status_icon = "✅" if b.status.value == "active" else "🟡"
            self.bom_combo.addItem(f"{status_icon} {b.code} - {b.name}", b.id)

    def set_warehouses(self, warehouses: list):
        """Depoları ayarla"""
        self.source_warehouse_combo.clear()
        self.target_warehouse_combo.clear()
        self.source_warehouse_combo.addItem("Seçiniz...", None)
        self.target_warehouse_combo.addItem("Seçiniz...", None)
        for w in warehouses:
            self.source_warehouse_combo.addItem(f"{w.code} - {w.name}", w.id)
            self.target_warehouse_combo.addItem(f"{w.code} - {w.name}", w.id)

    def set_work_stations(self, stations: list):
        """İş istasyonlarını ayarla"""
        self.work_stations = stations

    def set_generated_order_no(self, order_no: str):
        self.order_no_input.setText(order_no)

    def set_bom_materials(self, materials: list):
        """Reçeteden gelen malzemeleri ayarla"""
        self.materials = materials
        self._update_materials()

    def set_bom_operations(self, operations: list):
        """Operasyonları ayarla"""
        self.operations = operations
        self._update_operations_table()

    def _on_product_changed(self):
        """Mamul değiştiğinde"""
        product_id = self.product_combo.currentData()
        if product_id:
            self.bom_selected.emit(product_id)
        else:
            self.bom_combo.clear()
            self.bom_combo.addItem("Önce mamul seçin...", None)
            self.materials = []
            self.operations = []
            self._update_materials()
            self._update_operations_table()

    def _on_bom_changed(self):
        """Reçete değiştiğinde"""
        pass

    def _add_operation(self):
        """Yeni operasyon ekle"""
        if not self.work_stations:
            QMessageBox.warning(
                self,
                "Uyarı",
                "Önce iş istasyonu tanımlamalısınız!\n\n"
                "Üretim → İş İstasyonları menüsünden ekleyebilirsiniz.",
            )
            return

        # Yeni operasyon no'su belirle
        max_no = 0
        for op in self.operations:
            op_no = op.get("operation_no", 0)
            if op_no > max_no:
                max_no = op_no

        dialog = OperationDialog(
            self.work_stations, {"operation_no": max_no + 10}, self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_op = dialog.get_data()
            new_op["id"] = None
            self.operations.append(new_op)
            self._update_operations_table()

    def _edit_operation(self, row: int):
        """Operasyon düzenle"""
        if row < 0 or row >= len(self.operations):
            return

        dialog = OperationDialog(self.work_stations, self.operations[row], self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated = dialog.get_data()
            updated["id"] = self.operations[row].get("id")
            self.operations[row] = updated
            self._update_operations_table()

    def _delete_operation(self, row: int):
        """Operasyon sil"""
        if row < 0 or row >= len(self.operations):
            return

        reply = QMessageBox.question(
            self,
            "Onay",
            f"'{self.operations[row].get('name', '')}' operasyonunu silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            del self.operations[row]
            self._update_operations_table()

    def _update_materials(self):
        """Malzeme tablosunu güncelle"""
        quantity = Decimal(str(self.quantity_input.value()))

        self.materials_table.setRowCount(len(self.materials))

        total_cost = Decimal(0)
        shortage_count = 0

        for row, mat in enumerate(self.materials):
            # Malzeme Kodu
            code_item = QTableWidgetItem(mat.get("item_code", ""))
            code_item.setForeground(QColor("#818cf8"))
            self.materials_table.setItem(row, 0, code_item)

            # Malzeme Adı
            self.materials_table.setItem(
                row, 1, QTableWidgetItem(mat.get("item_name", ""))
            )

            # Gerekli Miktar
            base_qty = mat.get("quantity", Decimal(0))
            if not isinstance(base_qty, Decimal):
                base_qty = Decimal(str(base_qty))
            required_qty = base_qty * quantity
            req_item = QTableWidgetItem(f"{required_qty:,.4f}")
            req_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.materials_table.setItem(row, 2, req_item)

            # Birim
            self.materials_table.setItem(
                row, 3, QTableWidgetItem(mat.get("unit_code", "ADET"))
            )

            # Mevcut Stok
            stock = mat.get("stock", 0)
            if not isinstance(stock, Decimal):
                stock = Decimal(str(stock))
            stock_item = QTableWidgetItem(f"{stock:,.4f}")
            stock_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.materials_table.setItem(row, 4, stock_item)

            # Eksik
            shortage = max(Decimal(0), required_qty - stock)
            shortage_item = QTableWidgetItem(
                f"{shortage:,.4f}" if shortage > 0 else "-"
            )
            shortage_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            if shortage > 0:
                shortage_item.setForeground(QColor("#ef4444"))
                shortage_count += 1
            self.materials_table.setItem(row, 5, shortage_item)

            # Birim Maliyet
            unit_cost = mat.get("unit_cost", 0)
            if not isinstance(unit_cost, Decimal):
                unit_cost = Decimal(str(unit_cost))
            cost_item = QTableWidgetItem(f"₺{unit_cost:,.2f}")
            cost_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.materials_table.setItem(row, 6, cost_item)

            # Toplam Maliyet
            line_cost = required_qty * unit_cost
            total_cost += line_cost
            line_cost_item = QTableWidgetItem(f"₺{line_cost:,.2f}")
            line_cost_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            line_cost_item.setForeground(QColor("#10b981"))
            self.materials_table.setItem(row, 7, line_cost_item)

        self.materials_count_label.setText(f"Toplam: {len(self.materials)} malzeme")
        self.material_cost_label.setText(f"Malzeme: ₺{total_cost:,.2f}")
        self.total_cost_label.setText(f"Toplam Tahmini Maliyet: ₺{total_cost:,.2f}")

        if shortage_count > 0:
            self.shortage_label.setText(f"⚠️ {shortage_count} malzemede stok eksik!")
        else:
            self.shortage_label.setText("")

    def _update_operations_table(self):
        """Operasyon tablosunu güncelle"""
        quantity = Decimal(str(self.quantity_input.value()))

        self.operations_table.setRowCount(len(self.operations))

        total_time = 0

        for row, op in enumerate(self.operations):
            # No
            no_item = QTableWidgetItem(str(op.get("operation_no", row + 1)))
            no_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.operations_table.setItem(row, 0, no_item)

            # Operasyon Adı
            name_item = QTableWidgetItem(op.get("name", ""))
            name_item.setForeground(QColor("#818cf8"))
            self.operations_table.setItem(row, 1, name_item)

            # İş İstasyonu
            station_id = op.get("work_station_id")
            station_name = "❌ Atanmamış"
            for ws in self.work_stations:
                if ws.get("id") == station_id:
                    type_icons = {
                        "machine": "⚙️",
                        "workstation": "🔧",
                        "assembly": "🏭",
                        "manual": "👷",
                    }
                    icon = type_icons.get(ws.get("station_type", "machine"), "⚙️")

                    # Fason kontrolü
                    if ws.get("is_external"):
                        icon = "🚚"  # Kamyon ikonu
                        station_name = f"{icon} [FASON] {ws.get('code', '')} - {ws.get('name', '')}"
                    else:
                        station_name = (
                            f"{icon} {ws.get('code', '')} - {ws.get('name', '')}"
                        )
                    break

            station_item = QTableWidgetItem(station_name)
            if station_id:
                station_item.setForeground(QColor("#10b981"))
            else:
                station_item.setForeground(QColor("#ef4444"))
            self.operations_table.setItem(row, 2, station_item)

            # Kurulum süresi
            setup_time = op.get("setup_time", 0)
            setup_item = QTableWidgetItem(str(setup_time))
            setup_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.operations_table.setItem(row, 3, setup_item)

            # Birim çalışma süresi
            run_time = op.get("run_time", 0)
            run_item = QTableWidgetItem(
                f"{run_time:.4f}" if isinstance(run_time, float) else str(run_time)
            )
            run_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.operations_table.setItem(row, 4, run_item)

            # Toplam süre
            op_total = float(setup_time) + (float(run_time) * float(quantity))
            total_time += op_total
            total_item = QTableWidgetItem(f"{op_total:.1f}")
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            total_item.setForeground(QColor("#10b981"))
            self.operations_table.setItem(row, 5, total_item)

            # İşlem butonları
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(4)

            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(28, 28)
            edit_btn.setToolTip("Düzenle")
            edit_btn.clicked.connect(lambda checked, r=row: self._edit_operation(r))
            btn_layout.addWidget(edit_btn)

            del_btn = QPushButton("🗑")
            del_btn.setFixedSize(28, 28)
            del_btn.setToolTip("Sil")
            del_btn.clicked.connect(lambda checked, r=row: self._delete_operation(r))
            btn_layout.addWidget(del_btn)

            self.operations_table.setCellWidget(row, 6, btn_widget)

        self.operations_count_label.setText(f"Toplam: {len(self.operations)} operasyon")

        # Süreyi formatla
        hours = int(total_time // 60)
        minutes = int(total_time % 60)
        if hours > 0:
            time_str = f"{hours} saat {minutes} dakika"
        else:
            time_str = f"{int(total_time)} dakika"

        self.total_time_label.setText(f"Toplam Süre: {time_str}")
        self.estimated_time_label.setText(time_str)

    def _auto_calculate_end_time(self):
        """Bitiş tarihini hesapla"""
        quantity = float(self.quantity_input.value())
        total_minutes = 0

        for op in self.operations:
            setup_time = float(op.get("setup_time", 0))
            run_time = float(op.get("run_time", 0)) * quantity
            total_minutes += setup_time + run_time

        if total_minutes > 0:
            start = self.planned_start_input.dateTime()
            # 8 saat/gün varsayımı
            work_days = total_minutes / (8 * 60)
            calendar_days = int(work_days * 7 / 5) + 1
            end = start.addDays(max(1, calendar_days))
            self.planned_end_input.setDateTime(end)

            hours = int(total_minutes // 60)
            mins = int(total_minutes % 60)
            QMessageBox.information(
                self,
                "Hesaplandı",
                f"Toplam süre: {hours} saat {mins} dakika\n"
                f"Tahmini bitiş: {end.toString('dd.MM.yyyy HH:mm')}",
            )
        else:
            QMessageBox.warning(
                self, "Uyarı", "Hesaplama için en az bir operasyon ekleyin!"
            )

    def load_data(self):
        """Düzenleme modunda verileri yükle"""
        if not self.wo_data:
            return

        self.order_no_input.setText(self.wo_data.get("order_no", ""))
        self.batch_input.setText(self.wo_data.get("batch_number", "") or "")
        self.description_input.setPlainText(self.wo_data.get("description", "") or "")

        # Özel Notlar
        if hasattr(self, "production_notes_input"):
            self.production_notes_input.setPlainText(
                self.wo_data.get("production_notes", "") or ""
            )
        if hasattr(self, "quality_notes_input"):
            self.quality_notes_input.setPlainText(
                self.wo_data.get("quality_notes", "") or ""
            )
        if hasattr(self, "shipping_notes_input"):
            self.shipping_notes_input.setPlainText(
                self.wo_data.get("shipping_notes", "") or ""
            )

        self.quantity_input.setValue(float(self.wo_data.get("planned_quantity", 1)))

        if self.wo_data.get("planned_start"):
            self.planned_start_input.setDateTime(
                QDateTime(self.wo_data["planned_start"])
            )
        if self.wo_data.get("planned_end"):
            self.planned_end_input.setDateTime(QDateTime(self.wo_data["planned_end"]))

    def _on_save(self):
        """Kaydet"""
        order_no = self.order_no_input.text().strip()
        if not order_no:
            QMessageBox.warning(self, "Uyarı", "İş emri numarası zorunludur!")
            return

        product_id = self.product_combo.currentData()
        if not product_id:
            QMessageBox.warning(self, "Uyarı", "Mamul seçimi zorunludur!")
            return

        bom_id = self.bom_combo.currentData()
        if not bom_id:
            QMessageBox.warning(self, "Uyarı", "Reçete seçimi zorunludur!")
            return

        if not self.operations:
            reply = QMessageBox.question(
                self,
                "Onay",
                "Hiç operasyon tanımlanmadı. Devam etmek istiyor musunuz?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return

        data = {
            "order_no": order_no,
            "description": self.description_input.toPlainText().strip(),
            "production_notes": self.production_notes_input.toPlainText().strip(),
            "quality_notes": self.quality_notes_input.toPlainText().strip(),
            "shipping_notes": self.shipping_notes_input.toPlainText().strip(),
            "item_id": product_id,
            "bom_id": bom_id,
            "batch_number": self.batch_input.text().strip() or None,
            "planned_quantity": Decimal(str(self.quantity_input.value())),
            "priority": self.priority_combo.currentData(),
            "source_warehouse_id": self.source_warehouse_combo.currentData(),
            "target_warehouse_id": self.target_warehouse_combo.currentData(),
            "planned_start": self.planned_start_input.dateTime().toPyDateTime(),
            "planned_end": self.planned_end_input.dateTime().toPyDateTime(),
            "operations": self.operations,
        }

        if self.is_edit_mode and self.wo_data:
            data["id"] = self.wo_data.get("id")

        self.saved.emit(data)
