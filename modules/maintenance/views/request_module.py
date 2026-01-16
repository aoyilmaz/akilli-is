"""
Bakım Modülü - Arıza/Bakım Talepleri
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGroupBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from modules.maintenance.views.base import MaintenanceBaseWidget
from database.models.maintenance import (
    MaintenancePriority,
    MaintenanceType,
    MaintenanceStatus,
)


class MaintenanceRequestWidget(MaintenanceBaseWidget):
    """Bakım Talepleri Widget'ı"""

    def __init__(self, parent=None):
        super().__init__("Arıza/Bakım Talepleri", parent)
        self.setup_ui()

    def setup_ui(self):
        # Üst Butonlar
        btn_layout = QHBoxLayout()

        self.btn_new = QPushButton("Yeni Arıza Bildirimi")
        self.btn_new.setStyleSheet(
            "background-color: #eab308; color: black; padding: 8px 16px; border-radius: 4px;"
        )
        self.btn_new.clicked.connect(self.show_request_dialog)
        btn_layout.addWidget(self.btn_new)

        self.btn_new_wo = QPushButton("Seçiliden İş Emri Oluştur")
        self.btn_new_wo.setStyleSheet(
            "background-color: #007acc; color: white; padding: 8px 16px; border-radius: 4px;"
        )
        self.btn_new_wo.clicked.connect(self.create_work_order_from_request)
        btn_layout.addWidget(self.btn_new_wo)

        self.btn_close = QPushButton("Talebi Kapat")
        self.btn_close.setStyleSheet(
            "background-color: #22c55e; color: white; padding: 8px 16px; border-radius: 4px;"
        )
        self.btn_close.clicked.connect(self.close_request)
        btn_layout.addWidget(self.btn_close)

        btn_layout.addStretch()

        # Filtreler
        self.cmb_status = QComboBox()
        self.cmb_status.addItem("Bekleyenler", "pending")
        self.cmb_status.addItem("Tümü", "all")
        self.cmb_status.addItem("Çözülenler", "resolved")
        self.cmb_status.currentIndexChanged.connect(self.refresh_data)
        btn_layout.addWidget(QLabel("Durum:"))
        btn_layout.addWidget(self.cmb_status)

        self.cmb_priority = QComboBox()
        self.cmb_priority.addItem("Tüm Öncelikler", None)
        for p in MaintenancePriority:
            self.cmb_priority.addItem(p.value.capitalize(), p)
        self.cmb_priority.currentIndexChanged.connect(self.refresh_data)
        btn_layout.addWidget(QLabel("Öncelik:"))
        btn_layout.addWidget(self.cmb_priority)

        self.layout.addLayout(btn_layout)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Talep No", "Ekipman", "Tarih", "Öncelik", "Tür", "Durum", "Bildiren"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.layout.addWidget(self.table)

        self.refresh_data()

    def refresh_data(self):
        status_filter = self.cmb_status.currentData()
        priority_filter = self.cmb_priority.currentData()

        if status_filter == "pending":
            requests = self.service.get_pending_requests(priority=priority_filter)
        elif status_filter == "resolved":
            requests = self.service.get_resolved_requests(priority=priority_filter)
        else:
            requests = self.service.get_all_requests(priority=priority_filter)

        self.table.setRowCount(len(requests))
        for i, req in enumerate(requests):
            self.table.setItem(i, 0, QTableWidgetItem(req.request_no))
            self.table.item(i, 0).setData(Qt.ItemDataRole.UserRole, req.id)

            self.table.setItem(i, 1, QTableWidgetItem(
                req.equipment.name if req.equipment else "-"
            ))
            self.table.setItem(i, 2, QTableWidgetItem(
                req.request_date.strftime("%d.%m.%Y %H:%M")
            ))

            # Öncelik - renkli
            priority_item = QTableWidgetItem(req.priority.value.capitalize())
            priority_colors = {
                MaintenancePriority.LOW: Qt.GlobalColor.darkGreen,
                MaintenancePriority.NORMAL: Qt.GlobalColor.blue,
                MaintenancePriority.HIGH: Qt.GlobalColor.darkYellow,
                MaintenancePriority.CRITICAL: Qt.GlobalColor.red,
            }
            priority_item.setForeground(priority_colors.get(req.priority, Qt.GlobalColor.black))
            self.table.setItem(i, 3, priority_item)

            self.table.setItem(i, 4, QTableWidgetItem(req.maintenance_type.value.capitalize()))

            # Durum - renkli
            status_item = QTableWidgetItem(req.status.value.replace("_", " ").capitalize())
            if req.status == MaintenanceStatus.RESOLVED:
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            elif req.status == MaintenanceStatus.IN_PROGRESS:
                status_item.setForeground(Qt.GlobalColor.blue)
            elif req.status == MaintenanceStatus.WAITING_PARTS:
                status_item.setForeground(Qt.GlobalColor.darkYellow)
            self.table.setItem(i, 5, status_item)

            self.table.setItem(i, 6, QTableWidgetItem(
                req.reported_by.full_name if req.reported_by else "-"
            ))

    def get_selected_request_id(self) -> Optional[int]:
        current_row = self.table.currentRow()
        if current_row < 0:
            return None
        return self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)

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
        self.txt_desc.setPlaceholderText("Arıza/bakım açıklaması... Ne oldu? Ne zaman fark edildi?")
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
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        main_layout.addWidget(btns)

    def select_photo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Fotoğraf Seç", "",
            "Resim Dosyaları (*.png *.jpg *.jpeg *.bmp)"
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
