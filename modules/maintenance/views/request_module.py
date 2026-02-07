"""
Bakım Modülü - Arıza/Bakım Talepleri
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QPushButton,
    QTableWidgetItem,
    QFormLayout,
    QTextEdit,
    QComboBox,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGroupBox,
)
from PyQt6.QtCore import Qt

from PyQt6.QtGui import QColor, QAction
from config.styles import SUCCESS, INFO, WARNING, ERROR
from config.icons import ICONS
from ui.components.base_list_page import BaseListPage
from ui.components.enhanced_table import ColumnConfig
from database.base import get_session
from modules.maintenance.services import MaintenanceService
from database.models.maintenance import (
    MaintenancePriority,
    MaintenanceType,
    MaintenanceStatus,
)


class MaintenanceRequestWidget(BaseListPage):
    """Bakım Talepleri Widget'ı"""

    def __init__(self, parent=None):
        self.db_session = get_session()
        self.service = MaintenanceService(self.db_session)

        columns = [
            ColumnConfig("request_no", "Talep No", width=100, filterable=True),
            ColumnConfig(
                "equipment", "Ekipman", width=150, filterable=True, stretch=True
            ),
            ColumnConfig("date", "Tarih", width=120),
            ColumnConfig("priority", "Öncelik", width=100, filter_type="enum"),
            ColumnConfig("type", "Tür", width=120, filter_type="enum"),
            ColumnConfig("status", "Durum", width=120, filter_type="enum"),
            ColumnConfig("reporter", "Bildiren", width=120),
        ]

        super().__init__(
            title="Arıza/Bakım Talepleri",
            icon=ICONS.MAINTENANCE,
            table_id="maintenance_requests",
            columns=columns,
            show_add=True,
            add_text="Yeni Arıza Bildirimi",
            parent=parent,
        )

        self._setup_extra_ui()
        self.add_clicked.connect(self.show_request_dialog)
        self.refresh_requested.connect(self.refresh_data)

    def closeEvent(self, event):
        if hasattr(self, "db_session") and self.db_session:
            self.db_session.close()
        super().closeEvent(event)

    def _setup_extra_ui(self):
        h_layout = self.header.header_layout()

        # Filtreler
        h_layout.addSpacing(16)
        h_layout.addWidget(QLabel("Durum:"))
        self.cmb_status = QComboBox()
        self.cmb_status.addItem("Bekleyenler", "pending")
        self.cmb_status.addItem("Tümü", "all")
        self.cmb_status.addItem("Çözülenler", "resolved")
        self.cmb_status.setFixedHeight(32)
        self.cmb_status.currentIndexChanged.connect(self.refresh_data)
        h_layout.addWidget(self.cmb_status)

        h_layout.addSpacing(10)
        h_layout.addWidget(QLabel("Öncelik:"))
        self.cmb_priority = QComboBox()
        self.cmb_priority.addItem("Tümü", None)
        for p in MaintenancePriority:
            self.cmb_priority.addItem(p.value.capitalize(), p)
        self.cmb_priority.setFixedHeight(32)
        self.cmb_priority.currentIndexChanged.connect(self.refresh_data)
        h_layout.addWidget(self.cmb_priority)

        # Context Menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # Filtre Seçenekleri
        self.table.set_filter_options(
            "priority", [p.value.capitalize() for p in MaintenancePriority]
        )
        self.table.set_filter_options(
            "type", [t.value.capitalize() for t in MaintenanceType]
        )
        self.table.set_filter_options(
            "status",
            [s.value.replace("_", " ").capitalize() for s in MaintenanceStatus],
        )

    def refresh_data(self):
        status_filter = self.cmb_status.currentData()
        priority_filter = self.cmb_priority.currentData()

        if status_filter == "pending":
            requests = self.service.get_pending_requests(priority=priority_filter)
        elif status_filter == "resolved":
            requests = self.service.get_resolved_requests(priority=priority_filter)
        else:
            requests = self.service.get_all_requests(priority=priority_filter)

        self.load_data(requests)

    def load_data(self, requests):
        self.table.setRowCount(len(requests))
        for i, req in enumerate(requests):
            # Request No
            item = QTableWidgetItem(req.request_no)
            item.setData(Qt.ItemDataRole.UserRole, req.id)
            self.table.setItem(i, 0, item)

            # Equipment
            self.table.setItem(
                i, 1, QTableWidgetItem(req.equipment.name if req.equipment else "-")
            )

            # Date
            self.table.setItem(
                i, 2, QTableWidgetItem(req.request_date.strftime("%d.%m.%Y %H:%M"))
            )

            # Priority
            priority_item = QTableWidgetItem(req.priority.value.capitalize())
            priority_colors = {
                MaintenancePriority.LOW: QColor(SUCCESS),
                MaintenancePriority.NORMAL: QColor(INFO),
                MaintenancePriority.HIGH: QColor(WARNING),
                MaintenancePriority.CRITICAL: QColor(ERROR),
            }
            priority_item.setForeground(priority_colors.get(req.priority, QColor(INFO)))
            self.table.setItem(i, 3, priority_item)

            # Type
            self.table.setItem(
                i, 4, QTableWidgetItem(req.maintenance_type.value.capitalize())
            )

            # Status
            status_item = QTableWidgetItem(
                req.status.value.replace("_", " ").capitalize()
            )
            if req.status == MaintenanceStatus.RESOLVED:
                status_item.setForeground(QColor(SUCCESS))
            elif req.status == MaintenanceStatus.IN_PROGRESS:
                status_item.setForeground(QColor(INFO))
            elif req.status == MaintenanceStatus.WAITING_PARTS:
                status_item.setForeground(QColor(WARNING))
            self.table.setItem(i, 5, status_item)

            # Reporter
            self.table.setItem(
                i,
                6,
                QTableWidgetItem(req.reported_by.full_name if req.reported_by else "-"),
            )

        self.update_count(len(requests))

    def get_selected_request_id(self) -> Optional[int]:
        return self.table.get_selected_id()

    def _show_context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0:
            return

        menu = self.table.create_standard_context_menu(pos)
        menu.addSeparator()

        wo_action = QAction("İş Emri Oluştur", self)
        wo_action.triggered.connect(self.create_work_order_from_request)
        menu.addAction(wo_action)

        close_action = QAction("Talebi Kapat", self)
        close_action.triggered.connect(self.close_request)
        menu.addAction(close_action)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def show_request_dialog(self):
        dialog = RequestDialog(self.service, self)
        if dialog.exec():
            self.refresh_data()

    def create_work_order_from_request(self):
        request_id = self.get_selected_request_id()
        if not request_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir talep seçiniz.")
            return

        # WorkOrderDialog'u import et ve request_id ile aç
        from modules.maintenance.views.work_order_module import WorkOrderDialog

        dialog = WorkOrderDialog(self.service, self, request_id=request_id)
        if dialog.exec():
            self.refresh_data()

    def close_request(self):
        request_id = self.get_selected_request_id()
        if not request_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir talep seçiniz.")
            return

        reply = QMessageBox.question(
            self,
            "Onay",
            "Bu talebi çözüldü olarak kapatmak istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.service.update_request_status(
                    request_id, MaintenanceStatus.RESOLVED, "Manuel olarak kapatıldı."
                )
                self.refresh_data()
                QMessageBox.information(self, "Bilgi", "Talep kapatıldı.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))

    # Interface Implementation
    def get_filters(self) -> dict:
        return {
            "status": self.cmb_status.currentData(),
            "priority": self.cmb_priority.currentData(),
        }

    def get_search_text(self) -> str:
        return self.header.get_search_text()


class RequestDialog(QDialog):
    """Arıza Bildirimi Oluşturma Dialogu"""

    def __init__(self, service, parent=None, request=None):
        super().__init__(parent)
        self.service = service
        self.request = request
        self.attachment_path = None

        self.setWindowTitle("Arıza Bildir" if not request else "Talep Düzenle")
        self.setMinimumSize(500, 500)

        main_layout = QVBoxLayout(self)

        # Form
        form = QFormLayout()

        self.cmb_equipment = QComboBox()
        self.cmb_equipment.setMinimumWidth(300)
        equipments = self.service.get_equipment_list(active_only=True)
        for eq in equipments:
            self.cmb_equipment.addItem(f"{eq.code} - {eq.name}", eq.id)
        form.addRow("Ekipman*:", self.cmb_equipment)

        self.cmb_category = QComboBox()
        self.cmb_category.addItem("- Kategori Seçin -", None)
        categories = self.service.get_all_categories()
        for cat in categories:
            self.cmb_category.addItem(cat.name, cat.id)
        form.addRow("Kategori:", self.cmb_category)

        self.cmb_type = QComboBox()
        for t in MaintenanceType:
            label = {
                MaintenanceType.BREAKDOWN: "Arıza Onarım",
                MaintenanceType.PREVENTIVE: "Periyodik Bakım",
                MaintenanceType.PREDICTIVE: "Kestirimci Bakım",
                MaintenanceType.CALIBRATION: "Kalibrasyon",
            }.get(t, t.value)
            self.cmb_type.addItem(label, t)
        form.addRow("Bakım Türü:", self.cmb_type)

        self.cmb_priority = QComboBox()
        for p in MaintenancePriority:
            label = {
                MaintenancePriority.LOW: "Düşük",
                MaintenancePriority.NORMAL: "Normal",
                MaintenancePriority.HIGH: "Yüksek",
                MaintenancePriority.CRITICAL: "Kritik (Acil)",
            }.get(p, p.value)
            self.cmb_priority.addItem(label, p)
        self.cmb_priority.setCurrentIndex(1)  # Normal seçili
        form.addRow("Öncelik:", self.cmb_priority)

        self.txt_desc = QTextEdit()
        self.txt_desc.setPlaceholderText(
            "Arıza/bakım açıklaması... Ne oldu? Ne zaman fark edildi?"
        )
        self.txt_desc.setMinimumHeight(100)
        form.addRow("Açıklama*:", self.txt_desc)

        main_layout.addLayout(form)

        # Fotoğraf Ekleme
        photo_group = QGroupBox("Fotoğraf (Opsiyonel)")
        photo_layout = QVBoxLayout(photo_group)

        self.lbl_photo = QLabel("Fotoğraf seçilmedi")
        self.lbl_photo.setStyleSheet("color: #6b7280;")
        photo_layout.addWidget(self.lbl_photo)

        btn_photo = QPushButton("Fotoğraf Seç")
        btn_photo.clicked.connect(self.select_photo)
        photo_layout.addWidget(btn_photo)

        main_layout.addWidget(photo_group)

        # Buttons
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        main_layout.addWidget(btns)

    def select_photo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Fotoğraf Seç", "", "Resim Dosyaları (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.attachment_path = file_path
            self.lbl_photo.setText(f"Seçilen: {file_path.split('/')[-1]}")

    def accept(self):
        # Validasyon
        equipment_id = self.cmb_equipment.currentData()
        description = self.txt_desc.toPlainText().strip()

        if not equipment_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir ekipman seçin.")
            return

        if not description:
            QMessageBox.warning(self, "Uyarı", "Lütfen açıklama girin.")
            return

        try:
            request = self.service.create_request(
                equipment_id=equipment_id,
                description=description,
                priority=self.cmb_priority.currentData(),
                category_id=self.cmb_category.currentData(),
                maintenance_type=self.cmb_type.currentData(),
            )

            # Fotoğraf varsa ekle
            if self.attachment_path:
                self.service.add_request_attachment(request.id, self.attachment_path)

            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
