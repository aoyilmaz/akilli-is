"""
Bakım Modülü - Ekipman Yönetimi
"""

from typing import Optional
from PyQt6.QtGui import QColor, QAction
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidgetItem,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QTabWidget,
    QGroupBox,
    QSpinBox,
    QDateEdit,
    QDoubleSpinBox,
    QMenu,
    QTableWidget,
    QHeaderView,
)
from PyQt6.QtCore import Qt, QDate
import qtawesome as qta
from config.icons import ICONS
from config.themes import get_theme

from ui.components.base_list_page import BaseListPage
from ui.components.enhanced_table import ColumnConfig

# MaintenanceBaseWidget functionality integrated or mixedin?
# BaseListPage inherits QWidget. MaintenanceBaseWidget also inherits QWidget.
# We can just use MaintenanceService directly or mixin.
# Let's import service here directly to avoid MRO complexity for now, or just use `self.service` if we were inheriting.
# Given BaseListPage assumes it owns the page, we should inherit BaseListPage.
# We can re-implement the db session logic or copy it.
from database.base import get_session
from modules.maintenance.services import MaintenanceService
from database.models.maintenance import (
    Equipment,
    CriticalityLevel,
)


class EquipmentListWidget(BaseListPage):
    """Ekipman Listesi ve Yönetimi"""

    def __init__(self, parent=None):
        self.db_session = get_session()
        self.service = MaintenanceService(self.db_session)

        columns = [
            ColumnConfig("code", "Kod", width=100, filterable=True),
            ColumnConfig("name", "İsim", width=150, filterable=True, stretch=True),
            ColumnConfig("brand_model", "Marka/Model", width=150, filterable=True),
            ColumnConfig("location", "Lokasyon", width=120, filterable=True),
            ColumnConfig("criticality", "Kritiklik", width=100, filter_type="enum"),
            ColumnConfig(
                "running_hours", "Çalışma Saati", width=100, filter_type="number"
            ),
            ColumnConfig("status", "Durum", width=100, filter_type="enum"),
            ColumnConfig("last_maintenance", "Son Bakım", width=100),
        ]

        super().__init__(
            title="Ekipman Yönetimi",
            icon=ICONS.PRODUCTION,
            table_id="equipment_list",
            columns=columns,
            show_add=True,
            add_text="Yeni Ekipman",
            parent=parent,
        )

        self._setup_extra_ui()
        self.add_clicked.connect(self.show_add_dialog)
        self.refresh_requested.connect(
            self.refresh_data
        )  # Overwrite default behavior if needed, standard calls load_data

    def closeEvent(self, event):
        if hasattr(self, "db_session") and self.db_session:
            self.db_session.close()
        super().closeEvent(event)

    def _setup_extra_ui(self):
        # Header'a ekstra butonlar
        h_layout = self.header.header_layout()

        # Filtre (Durum)
        h_layout.addSpacing(16)
        h_layout.addWidget(QLabel("Durum:"))
        self.cmb_filter = QComboBox()
        self.cmb_filter.addItem("Tümü", None)
        self.cmb_filter.addItem("Aktif", True)
        self.cmb_filter.addItem("Pasif", False)
        self.cmb_filter.setFixedWidth(100)
        self.cmb_filter.setFixedHeight(32)
        self.cmb_filter.currentIndexChanged.connect(self.refresh_data)
        h_layout.addWidget(self.cmb_filter)

        # Context Menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # Filtre seçenekleri
        self.table.set_filter_options("status", ["Aktif", "Pasif"])
        self.table.set_filter_options(
            "criticality", [c.value for c in CriticalityLevel]
        )

    def refresh_data(self):
        filter_active = self.cmb_filter.currentData()
        equipments = self.service.get_equipment_list(active_only=filter_active)
        self.load_data(equipments)

    def load_data(self, equipments: list):
        self.table.setRowCount(len(equipments))
        t = get_theme()

        for i, eq in enumerate(equipments):
            # Code
            item = QTableWidgetItem(eq.code)
            item.setData(Qt.ItemDataRole.UserRole, eq.id)
            self.table.setItem(i, 0, item)

            # Name
            self.table.setItem(i, 1, QTableWidgetItem(eq.name))

            # Brand/Model
            self.table.setItem(
                i, 2, QTableWidgetItem(f"{eq.brand or ''} {eq.model or ''}".strip())
            )

            # Location
            self.table.setItem(i, 3, QTableWidgetItem(eq.location or "-"))

            # Criticality
            crit_val = eq.criticality.value if eq.criticality else "-"
            crit_item = QTableWidgetItem(crit_val)
            if eq.criticality == CriticalityLevel.CRITICAL:
                crit_item.setForeground(QColor("#ef4444"))
            elif eq.criticality == CriticalityLevel.HIGH:
                crit_item.setForeground(QColor("#f59e0b"))
            self.table.setItem(i, 4, crit_item)

            # Hours
            hours = eq.running_hours or 0
            self.table.setItem(i, 5, QTableWidgetItem(f"{hours:.1f} saat"))

            # Status
            status_item = QTableWidgetItem()
            if eq.is_active:
                status_item.setText("Aktif")
                status_item.setForeground(QColor(t.success))
            else:
                status_item.setText("Pasif")
                status_item.setForeground(QColor(t.text_muted))
            self.table.setItem(i, 6, status_item)

            # Last Maintenance
            last_maintenance = self.service.get_last_maintenance_date(eq.id)
            date_str = (
                last_maintenance.strftime("%d.%m.%Y") if last_maintenance else "-"
            )
            self.table.setItem(i, 7, QTableWidgetItem(date_str))

        self.update_count(len(equipments))

    def get_selected_equipment_id(self) -> Optional[int]:
        return self.table.get_selected_id()

    def _show_context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0:
            return

        eq_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        menu = QMenu(self)

        detail_action = QAction(
            qta.icon(ICONS.INFO, color="#3b82f6"), "Detay Görüntüle", self
        )
        detail_action.triggered.connect(lambda: self.show_detail_dialog(eq_id))
        menu.addAction(detail_action)

        edit_action = QAction(qta.icon(ICONS.EDIT, color="#f59e0b"), "Düzenle", self)
        edit_action.triggered.connect(lambda: self.show_edit_dialog(eq_id))
        menu.addAction(edit_action)

        menu.addSeparator()

        delete_action = QAction(
            qta.icon(ICONS.DELETE, color="#ef4444"), "Pasife Al / Sil", self
        )
        delete_action.triggered.connect(lambda: self.delete_equipment(eq_id))
        menu.addAction(delete_action)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def show_add_dialog(self):
        dialog = EquipmentDialog(self.service, self)
        if dialog.exec():
            self.refresh_data()

    def show_edit_dialog(self, eq_id=None):
        equipment_id = eq_id or self.get_selected_equipment_id()
        if not equipment_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen düzenlenecek ekipmanı seçin.")
            return

        equipment = self.service.get_equipment_by_id(equipment_id)
        if not equipment:
            QMessageBox.critical(self, "Hata", "Ekipman bulunamadı.")
            return

        dialog = EquipmentDialog(self.service, self, equipment=equipment)
        if dialog.exec():
            self.refresh_data()

    def show_detail_dialog(self, eq_id=None):
        equipment_id = eq_id or self.get_selected_equipment_id()
        if not equipment_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir ekipman seçin.")
            return

        dialog = EquipmentDetailDialog(self.service, equipment_id, self)
        dialog.exec()

    def delete_equipment(self, eq_id=None):
        equipment_id = eq_id or self.get_selected_equipment_id()
        if not equipment_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen silinecek ekipmanı seçin.")
            return

        equipment = self.service.get_equipment_by_id(equipment_id)
        reply = QMessageBox.question(
            self,
            "Onay",
            f"'{equipment.code} - {equipment.name}' ekipmanını pasife almak istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.service.deactivate_equipment(equipment_id)
            self.refresh_data()

    # -- Missing Methods for BaseListPage interface if needed --
    def get_filters(self) -> dict:
        return {"status": self.cmb_filter.currentData()}

    def get_search_text(self) -> str:
        return self.header.get_search_text()


# Re-exporting Dialog classes unchanged (omitted for brevity in this replace block if possible,
# but replace_file overwrites. I must keep them.)


class EquipmentDialog(QDialog):
    """Ekipman Ekleme/Düzenleme Dialogu"""

    def __init__(self, service, parent=None, equipment: Equipment = None):
        super().__init__(parent)
        self.service = service
        self.equipment = equipment
        self.setWindowTitle("Ekipman Düzenle" if equipment else "Yeni Ekipman")
        self.setMinimumSize(600, 700)

        main_layout = QVBoxLayout(self)

        # Tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Tab 1: Temel Bilgiler
        self.tab_basic = QWidget()
        self.setup_basic_tab()
        self.tabs.addTab(self.tab_basic, "Temel Bilgiler")

        # Tab 2: Teknik Bilgiler
        self.tab_technical = QWidget()
        self.setup_technical_tab()
        self.tabs.addTab(self.tab_technical, "Teknik Bilgiler")

        # Tab 3: Satınalma/Garanti
        self.tab_purchase = QWidget()
        self.setup_purchase_tab()
        self.tabs.addTab(self.tab_purchase, "Satınalma/Garanti")

        # Buttons
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        main_layout.addWidget(btns)

        # Mevcut veriyi yükle
        if self.equipment:
            self.load_equipment_data()

    def setup_basic_tab(self):
        layout = QFormLayout(self.tab_basic)
        layout.setSpacing(10)

        self.inp_code = QLineEdit()
        self.inp_code.setPlaceholderText("EKP-001")
        layout.addRow("Ekipman Kodu*:", self.inp_code)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("CNC Torna Tezgahı")
        layout.addRow("Ekipman Adı*:", self.inp_name)

        self.txt_description = QTextEdit()
        self.txt_description.setMaximumHeight(80)
        self.txt_description.setPlaceholderText("Ekipman açıklaması...")
        layout.addRow("Açıklama:", self.txt_description)

        self.inp_location = QLineEdit()
        self.inp_location.setPlaceholderText("Üretim Hattı 1, A Blok")
        layout.addRow("Lokasyon:", self.inp_location)

        self.inp_department = QLineEdit()
        self.inp_department.setPlaceholderText("Üretim")
        layout.addRow("Departman:", self.inp_department)

        self.cmb_criticality = QComboBox()
        for c in CriticalityLevel:
            self.cmb_criticality.addItem(c.value.capitalize(), c)
        layout.addRow("Kritiklik Seviyesi:", self.cmb_criticality)

        # Üst Ekipman (Hiyerarşi)
        self.cmb_parent = QComboBox()
        self.cmb_parent.addItem("- Ana Ekipman (Üst yok) -", None)
        equipments = self.service.get_equipment_list(active_only=True)
        for eq in equipments:
            if not self.equipment or eq.id != self.equipment.id:
                self.cmb_parent.addItem(f"{eq.code} - {eq.name}", eq.id)
        layout.addRow("Üst Ekipman:", self.cmb_parent)

    def setup_technical_tab(self):
        layout = QFormLayout(self.tab_technical)
        layout.setSpacing(10)

        self.inp_brand = QLineEdit()
        self.inp_brand.setPlaceholderText("Marka adı")
        layout.addRow("Marka:", self.inp_brand)

        self.inp_model = QLineEdit()
        self.inp_model.setPlaceholderText("Model numarası")
        layout.addRow("Model:", self.inp_model)

        self.inp_serial = QLineEdit()
        self.inp_serial.setPlaceholderText("Seri numarası")
        layout.addRow("Seri No:", self.inp_serial)

        self.spin_year = QSpinBox()
        self.spin_year.setRange(1900, 2100)
        self.spin_year.setValue(2020)
        layout.addRow("Üretim Yılı:", self.spin_year)

        self.spin_running_hours = QDoubleSpinBox()
        self.spin_running_hours.setRange(0, 999999)
        self.spin_running_hours.setDecimals(1)
        self.spin_running_hours.setSuffix(" saat")
        layout.addRow("Çalışma Saati:", self.spin_running_hours)

        self.txt_specs = QTextEdit()
        self.txt_specs.setMaximumHeight(100)
        self.txt_specs.setPlaceholderText("Teknik özellikler, kapasiteler vb.")
        layout.addRow("Teknik Özellikler:", self.txt_specs)

    def setup_purchase_tab(self):
        layout = QFormLayout(self.tab_purchase)
        layout.setSpacing(10)

        self.date_purchase = QDateEdit()
        self.date_purchase.setCalendarPopup(True)
        self.date_purchase.setDate(QDate.currentDate())
        layout.addRow("Satın Alma Tarihi:", self.date_purchase)

        self.date_warranty = QDateEdit()
        self.date_warranty.setCalendarPopup(True)
        self.date_warranty.setDate(QDate.currentDate().addYears(2))
        layout.addRow("Garanti Bitiş:", self.date_warranty)

        # Tedarikçi seçimi
        self.cmb_supplier = QComboBox()
        self.cmb_supplier.addItem("- Tedarikçi Seçin -", None)
        suppliers = self.service.get_all_suppliers()
        for sup in suppliers:
            self.cmb_supplier.addItem(sup.name, sup.id)
        layout.addRow("Tedarikçi:", self.cmb_supplier)

        # WorkStation bağlantısı
        self.cmb_workstation = QComboBox()
        self.cmb_workstation.addItem("- İş İstasyonu Seçin -", None)
        workstations = self.service.get_all_workstations()
        for ws in workstations:
            self.cmb_workstation.addItem(ws.name, ws.id)
        layout.addRow("Bağlı İş İstasyonu:", self.cmb_workstation)

    def load_equipment_data(self):
        """Mevcut ekipman verilerini forma yükle"""
        eq = self.equipment

        # Temel
        self.inp_code.setText(eq.code)
        self.inp_code.setReadOnly(True)  # Kod değiştirilemez
        self.inp_name.setText(eq.name)
        self.txt_description.setPlainText(eq.description or "")
        self.inp_location.setText(eq.location or "")
        self.inp_department.setText(eq.department or "")

        idx = self.cmb_criticality.findData(eq.criticality)
        if idx >= 0:
            self.cmb_criticality.setCurrentIndex(idx)

        if eq.parent_id:
            idx = self.cmb_parent.findData(eq.parent_id)
            if idx >= 0:
                self.cmb_parent.setCurrentIndex(idx)

        # Teknik
        self.inp_brand.setText(eq.brand or "")
        self.inp_model.setText(eq.model or "")
        self.inp_serial.setText(eq.serial_number or "")
        if eq.manufacturing_year:
            self.spin_year.setValue(eq.manufacturing_year)
        if eq.running_hours:
            self.spin_running_hours.setValue(float(eq.running_hours))
        self.txt_specs.setPlainText(eq.specifications or "")

        # Satınalma
        if eq.purchase_date:
            self.date_purchase.setDate(
                QDate(
                    eq.purchase_date.year, eq.purchase_date.month, eq.purchase_date.day
                )
            )
        if eq.warranty_end_date:
            self.date_warranty.setDate(
                QDate(
                    eq.warranty_end_date.year,
                    eq.warranty_end_date.month,
                    eq.warranty_end_date.day,
                )
            )
        if eq.supplier_id:
            idx = self.cmb_supplier.findData(eq.supplier_id)
            if idx >= 0:
                self.cmb_supplier.setCurrentIndex(idx)
        if eq.work_station_id:
            idx = self.cmb_workstation.findData(eq.work_station_id)
            if idx >= 0:
                self.cmb_workstation.setCurrentIndex(idx)

    def accept(self):
        # Validasyon
        code = self.inp_code.text().strip()
        name = self.inp_name.text().strip()

        if not code or not name:
            QMessageBox.warning(self, "Uyarı", "Ekipman kodu ve adı zorunludur.")
            return

        try:
            data = {
                "code": code,
                "name": name,
                "description": self.txt_description.toPlainText().strip() or None,
                "location": self.inp_location.text().strip() or None,
                "department": self.inp_department.text().strip() or None,
                "criticality": self.cmb_criticality.currentData(),
                "parent_id": self.cmb_parent.currentData(),
                "brand": self.inp_brand.text().strip() or None,
                "model": self.inp_model.text().strip() or None,
                "serial_number": self.inp_serial.text().strip() or None,
                "manufacturing_year": self.spin_year.value(),
                "running_hours": self.spin_running_hours.value(),
                "specifications": self.txt_specs.toPlainText().strip() or None,
                "purchase_date": self.date_purchase.date().toPyDate(),
                "warranty_end_date": self.date_warranty.date().toPyDate(),
                "supplier_id": self.cmb_supplier.currentData(),
                "work_station_id": self.cmb_workstation.currentData(),
            }

            if self.equipment:
                self.service.update_equipment(self.equipment.id, **data)
            else:
                self.service.create_equipment(**data)

            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class EquipmentDetailDialog(QDialog):
    """Ekipman Detay Dialogu - Bakım geçmişi, KPI'lar, yedek parçalar"""

    def __init__(self, service, equipment_id: int, parent=None):
        super().__init__(parent)
        self.service = service
        self.equipment_id = equipment_id
        self.equipment = service.get_equipment_by_id(equipment_id)

        self.setWindowTitle(f"Ekipman Detayı - {self.equipment.code}")
        self.setMinimumSize(900, 700)

        main_layout = QVBoxLayout(self)

        # Başlık
        header = QHBoxLayout()
        title = QLabel(f"{self.equipment.code} - {self.equipment.name}")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header.addWidget(title)

        # Kritiklik badge
        crit_label = QLabel(self.equipment.criticality.value.upper())
        crit_colors = {
            CriticalityLevel.LOW: "#22c55e",
            CriticalityLevel.MEDIUM: "#eab308",
            CriticalityLevel.HIGH: "#f97316",
            CriticalityLevel.CRITICAL: "#ef4444",
        }
        crit_label.setStyleSheet(
            f"""
            background-color: {crit_colors.get(self.equipment.criticality, '#gray')};
            color: white;
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: bold;
        """
        )
        header.addWidget(crit_label)
        header.addStretch()
        main_layout.addLayout(header)

        # Tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Tab 1: Genel Bilgiler & KPI
        self.tab_overview = QWidget()
        self.setup_overview_tab()
        self.tabs.addTab(self.tab_overview, "Genel Bakış")

        # Tab 2: Bakım Geçmişi
        self.tab_history = QWidget()
        self.setup_history_tab()
        self.tabs.addTab(self.tab_history, "Bakım Geçmişi")

        # Tab 3: Yedek Parçalar
        self.tab_parts = QWidget()
        self.setup_parts_tab()
        self.tabs.addTab(self.tab_parts, "Yedek Parçalar")

        # Tab 4: Duruş Kayıtları
        self.tab_downtime = QWidget()
        self.setup_downtime_tab()
        self.tabs.addTab(self.tab_downtime, "Duruş Kayıtları")

        # Kapat butonu
        btn_close = QPushButton("Kapat")
        btn_close.clicked.connect(self.close)
        main_layout.addWidget(btn_close)

    def setup_overview_tab(self):
        layout = QVBoxLayout(self.tab_overview)

        # KPI Kartları
        kpi_layout = QHBoxLayout()

        kpis = self.service.get_equipment_kpis(self.equipment_id)

        kpi_layout.addWidget(
            self._create_kpi_card(
                "MTBF",
                f"{kpis.get('mtbf', 0):.1f} saat",
                "Arızalar Arası Ortalama Süre",
                "#3b82f6",
            )
        )
        kpi_layout.addWidget(
            self._create_kpi_card(
                "MTTR",
                f"{kpis.get('mttr', 0):.1f} saat",
                "Ortalama Onarım Süresi",
                "#f97316",
            )
        )
        kpi_layout.addWidget(
            self._create_kpi_card(
                "Kullanılabilirlik",
                f"{kpis.get('availability', 100):.1f}%",
                "Son 30 Gün",
                "#22c55e",
            )
        )
        kpi_layout.addWidget(
            self._create_kpi_card(
                "Toplam Maliyet",
                f"₺{kpis.get('total_cost', 0):,.2f}",
                "Tüm Zamanlar",
                "#8b5cf6",
            )
        )

        layout.addLayout(kpi_layout)

        # Ekipman Bilgileri
        info_group = QGroupBox("Ekipman Bilgileri")
        info_layout = QFormLayout(info_group)
        info_layout.addRow(
            "Marka/Model:",
            QLabel(f"{self.equipment.brand or '-'} / {self.equipment.model or '-'}"),
        )
        info_layout.addRow("Seri No:", QLabel(self.equipment.serial_number or "-"))
        info_layout.addRow("Lokasyon:", QLabel(self.equipment.location or "-"))
        info_layout.addRow(
            "Çalışma Saati:", QLabel(f"{self.equipment.running_hours or 0:.1f} saat")
        )
        info_layout.addRow(
            "Garanti Bitiş:",
            QLabel(
                self.equipment.warranty_end_date.strftime("%d.%m.%Y")
                if self.equipment.warranty_end_date
                else "-"
            ),
        )
        layout.addWidget(info_group)

        layout.addStretch()

    def _create_kpi_card(
        self, title: str, value: str, subtitle: str, color: str
    ) -> QWidget:
        """KPI kartı widget'ı oluşturur"""
        card = QWidget()
        card.setStyleSheet(
            f"""
            QWidget {{
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 16px;
            }}
        """
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #6b7280; font-size: 12px;")
        card_layout.addWidget(lbl_title)

        lbl_value = QLabel(value)
        lbl_value.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")
        card_layout.addWidget(lbl_value)

        lbl_subtitle = QLabel(subtitle)
        lbl_subtitle.setStyleSheet("color: #9ca3af; font-size: 11px;")
        card_layout.addWidget(lbl_subtitle)

        return card

    def setup_history_tab(self):
        layout = QVBoxLayout(self.tab_history)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels(
            ["İş Emri No", "Tarih", "Tür", "Açıklama", "Teknisyen", "Maliyet"]
        )
        self.history_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.history_table)

        # Veri yükle
        history = self.service.get_equipment_maintenance_history(self.equipment_id)
        self.history_table.setRowCount(len(history))
        for i, wo in enumerate(history):
            self.history_table.setItem(i, 0, QTableWidgetItem(wo.order_no))
            self.history_table.setItem(
                i,
                1,
                QTableWidgetItem(
                    wo.completed_date.strftime("%d.%m.%Y") if wo.completed_date else "-"
                ),
            )
            self.history_table.setItem(
                i,
                2,
                QTableWidgetItem(
                    wo.request.maintenance_type.value if wo.request else "-"
                ),
            )
            self.history_table.setItem(i, 3, QTableWidgetItem(wo.description or "-"))
            self.history_table.setItem(
                i,
                4,
                QTableWidgetItem(wo.assigned_to.full_name if wo.assigned_to else "-"),
            )
            self.history_table.setItem(
                i, 5, QTableWidgetItem(f"₺{wo.total_cost or 0:,.2f}")
            )

    def setup_parts_tab(self):
        layout = QVBoxLayout(self.tab_parts)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Yedek Parça Ekle")
        btn_add.clicked.connect(self.add_spare_part)
        btn_layout.addWidget(btn_add)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.parts_table = QTableWidget()
        self.parts_table.setColumnCount(4)
        self.parts_table.setHorizontalHeaderLabels(
            ["Parça Kodu", "Parça Adı", "Min. Miktar", "Mevcut Stok"]
        )
        self.parts_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.parts_table)

        self.refresh_parts()

    def refresh_parts(self):
        parts = self.service.get_equipment_spare_parts(self.equipment_id)
        self.parts_table.setRowCount(len(parts))
        for i, part in enumerate(parts):
            self.parts_table.setItem(
                i, 0, QTableWidgetItem(part.item.code if part.item else "-")
            )
            self.parts_table.setItem(
                i, 1, QTableWidgetItem(part.item.name if part.item else "-")
            )
            self.parts_table.setItem(i, 2, QTableWidgetItem(str(part.min_quantity)))
            # Mevcut stok
            stock = (
                self.service.get_item_total_stock(part.item_id) if part.item_id else 0
            )
            stock_item = QTableWidgetItem(str(stock))
            if stock < float(part.min_quantity):
                stock_item.setForeground(Qt.GlobalColor.red)
            self.parts_table.setItem(i, 3, stock_item)

    def add_spare_part(self):
        # TODO: Implement spare part add dialog
        QMessageBox.information(
            self, "Bilgi", "Yedek parça ekleme ekranı henüz hazır değil."
        )

    def setup_downtime_tab(self):
        layout = QVBoxLayout(self.tab_downtime)

        self.downtime_table = QTableWidget()
        self.downtime_table.setColumnCount(5)
        self.downtime_table.setHorizontalHeaderLabels(
            ["Başlangıç", "Bitiş", "Süre (dk)", "Sebep", "İş Emri"]
        )
        self.downtime_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.downtime_table)

        # Veri yükle
        downtimes = self.service.get_equipment_downtimes(self.equipment_id)
        self.downtime_table.setRowCount(len(downtimes))
        for i, dt in enumerate(downtimes):
            self.downtime_table.setItem(
                i, 0, QTableWidgetItem(dt.start_time.strftime("%d.%m.%Y %H:%M"))
            )
            self.downtime_table.setItem(
                i,
                1,
                QTableWidgetItem(
                    dt.end_time.strftime("%d.%m.%Y %H:%M")
                    if dt.end_time
                    else "Devam Ediyor"
                ),
            )
            duration = dt.duration_minutes
            self.downtime_table.setItem(
                i, 2, QTableWidgetItem(f"{duration:.0f}" if duration else "-")
            )
            self.downtime_table.setItem(i, 3, QTableWidgetItem(dt.reason or "-"))
            self.downtime_table.setItem(
                i, 4, QTableWidgetItem(dt.work_order.order_no if dt.work_order else "-")
            )
