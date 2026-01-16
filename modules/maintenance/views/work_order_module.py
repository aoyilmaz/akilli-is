"""
Bakım Modülü - İş Emri Yönetimi
"""

from typing import Optional
from datetime import datetime
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
    QTabWidget,
    QGroupBox,
    QSpinBox,
    QDoubleSpinBox,
    QDateTimeEdit,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QCheckBox,
)
from PyQt6.QtCore import Qt, QDateTime

from modules.maintenance.views.base import MaintenanceBaseWidget
from database.models.maintenance import (
    MaintenancePriority,
    MaintenanceType,
    MaintenanceStatus,
    WorkOrderStatus,
)


class WorkOrderManagerWidget(MaintenanceBaseWidget):
    """İş Emri Yönetimi Widget'ı"""

    def __init__(self, parent=None):
        super().__init__("İş Emri Yönetimi", parent)
        self.setup_ui()

    def setup_ui(self):
        # Üst Butonlar
        btn_layout = QHBoxLayout()

        self.btn_new = QPushButton("Yeni İş Emri")
        self.btn_new.setStyleSheet(
            "background-color: #007acc; color: white; padding: 8px 16px; border-radius: 4px;"
        )
        self.btn_new.clicked.connect(self.show_create_dialog)
        btn_layout.addWidget(self.btn_new)

        self.btn_detail = QPushButton("Detay / İşlem Yap")
        self.btn_detail.setStyleSheet(
            "background-color: #6366f1; color: white; padding: 8px 16px; border-radius: 4px;"
        )
        self.btn_detail.clicked.connect(self.open_details)
        btn_layout.addWidget(self.btn_detail)

        btn_layout.addStretch()

        # Filtreler
        self.cmb_status = QComboBox()
        self.cmb_status.addItem("Aktifler", "active")
        self.cmb_status.addItem("Tümü", "all")
        self.cmb_status.addItem("Tamamlananlar", "completed")
        self.cmb_status.currentIndexChanged.connect(self.refresh_data)
        btn_layout.addWidget(QLabel("Durum:"))
        btn_layout.addWidget(self.cmb_status)

        self.layout.addLayout(btn_layout)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "İş Emri No", "Ekipman", "Talep No", "Öncelik", "Durum",
            "Planlanan", "Atanan", "Maliyet"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self.open_details)
        self.layout.addWidget(self.table)

        self.refresh_data()

    def refresh_data(self):
        status_filter = self.cmb_status.currentData()

        if status_filter == "active":
            orders = self.service.get_active_work_orders()
        elif status_filter == "completed":
            orders = self.service.get_completed_work_orders()
        else:
            orders = self.service.get_all_work_orders()

        self.table.setRowCount(len(orders))
        for i, wo in enumerate(orders):
            self.table.setItem(i, 0, QTableWidgetItem(wo.order_no))
            self.table.item(i, 0).setData(Qt.ItemDataRole.UserRole, wo.id)

            self.table.setItem(i, 1, QTableWidgetItem(
                wo.equipment.name if wo.equipment else "-"
            ))
            self.table.setItem(i, 2, QTableWidgetItem(
                wo.request.request_no if wo.request else "-"
            ))

            # Öncelik - renkli
            priority_item = QTableWidgetItem(wo.priority.value.capitalize())
            priority_colors = {
                MaintenancePriority.LOW: Qt.GlobalColor.darkGreen,
                MaintenancePriority.NORMAL: Qt.GlobalColor.blue,
                MaintenancePriority.HIGH: Qt.GlobalColor.darkYellow,
                MaintenancePriority.CRITICAL: Qt.GlobalColor.red,
            }
            priority_item.setForeground(priority_colors.get(wo.priority, Qt.GlobalColor.black))
            self.table.setItem(i, 3, priority_item)

            # Durum - renkli
            status_text = {
                WorkOrderStatus.DRAFT: "Taslak",
                WorkOrderStatus.ASSIGNED: "Atandı",
                WorkOrderStatus.IN_PROGRESS: "Devam Ediyor",
                WorkOrderStatus.COMPLETED: "Tamamlandı",
                WorkOrderStatus.CLOSED: "Kapandı",
                WorkOrderStatus.CANCELLED: "İptal",
            }.get(wo.status, wo.status.value)
            status_item = QTableWidgetItem(status_text)
            if wo.status == WorkOrderStatus.COMPLETED:
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            elif wo.status == WorkOrderStatus.IN_PROGRESS:
                status_item.setForeground(Qt.GlobalColor.blue)
            elif wo.status == WorkOrderStatus.CANCELLED:
                status_item.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(i, 4, status_item)

            self.table.setItem(i, 5, QTableWidgetItem(
                wo.planned_start_date.strftime("%d.%m.%Y") if wo.planned_start_date else "-"
            ))

            self.table.setItem(i, 6, QTableWidgetItem(
                wo.assigned_to.full_name if wo.assigned_to else "-"
            ))

            self.table.setItem(i, 7, QTableWidgetItem(f"₺{wo.total_cost or 0:,.2f}"))

    def get_selected_work_order_id(self) -> Optional[int]:
        current_row = self.table.currentRow()
        if current_row < 0:
            return None
        return self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)

    def show_create_dialog(self):
        dialog = WorkOrderDialog(self.service, self)
        if dialog.exec():
            self.refresh_data()

    def open_details(self):
        work_order_id = self.get_selected_work_order_id()
        if not work_order_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir iş emri seçin.")
            return

        dialog = WorkOrderDetailsDialog(self.service, work_order_id, self)
        if dialog.exec():
            self.refresh_data()


class WorkOrderDialog(QDialog):
    """İş Emri Oluşturma Dialogu"""

    def __init__(self, service, parent=None, request_id: int = None):
        super().__init__(parent)
        self.service = service
        self.request_id = request_id

        self.setWindowTitle("Yeni İş Emri Oluştur")
        self.setMinimumSize(550, 600)

        main_layout = QVBoxLayout(self)

        # Eğer bir talepten gelindiyse bilgilendirme
        if request_id:
            request = service.get_request_by_id(request_id)
            if request:
                info_label = QLabel(f"Talep No: {request.request_no} - {request.equipment.name}")
                info_label.setStyleSheet(
                    "background-color: #dbeafe; padding: 8px; border-radius: 4px; color: #1e40af;"
                )
                main_layout.addWidget(info_label)

        # Form
        form = QFormLayout()

        self.cmb_equipment = QComboBox()
        self.cmb_equipment.setMinimumWidth(300)
        equipments = self.service.get_equipment_list(active_only=True)
        for eq in equipments:
            self.cmb_equipment.addItem(f"{eq.code} - {eq.name}", eq.id)
        form.addRow("Ekipman*:", self.cmb_equipment)

        self.cmb_priority = QComboBox()
        for p in MaintenancePriority:
            label = {
                MaintenancePriority.LOW: "Düşük",
                MaintenancePriority.NORMAL: "Normal",
                MaintenancePriority.HIGH: "Yüksek",
                MaintenancePriority.CRITICAL: "Kritik (Acil)",
            }.get(p, p.value)
            self.cmb_priority.addItem(label, p)
        self.cmb_priority.setCurrentIndex(1)
        form.addRow("Öncelik:", self.cmb_priority)

        self.cmb_user = QComboBox()
        self.cmb_user.addItem("- Atama Yapılmadı -", None)
        technicians = self.service.get_maintenance_technicians()
        for u in technicians:
            self.cmb_user.addItem(u.full_name, u.id)
        form.addRow("Atanan Teknisyen:", self.cmb_user)

        self.dt_planned = QDateTimeEdit()
        self.dt_planned.setCalendarPopup(True)
        self.dt_planned.setDateTime(QDateTime.currentDateTime())
        form.addRow("Planlanan Başlangıç:", self.dt_planned)

        self.dt_due = QDateTimeEdit()
        self.dt_due.setCalendarPopup(True)
        self.dt_due.setDateTime(QDateTime.currentDateTime().addDays(1))
        form.addRow("Bitiş Tarihi:", self.dt_due)

        self.spin_estimated = QDoubleSpinBox()
        self.spin_estimated.setRange(0, 1000)
        self.spin_estimated.setDecimals(1)
        self.spin_estimated.setSuffix(" saat")
        self.spin_estimated.setValue(1)
        form.addRow("Tahmini Süre:", self.spin_estimated)

        # Kontrol listesi seçimi
        self.cmb_checklist = QComboBox()
        self.cmb_checklist.addItem("- Kontrol Listesi Yok -", None)
        checklists = self.service.get_all_checklists()
        for cl in checklists:
            self.cmb_checklist.addItem(cl.name, cl.id)
        form.addRow("Kontrol Listesi:", self.cmb_checklist)

        self.txt_desc = QTextEdit()
        self.txt_desc.setPlaceholderText("Yapılacak işler, notlar...")
        self.txt_desc.setMinimumHeight(100)
        form.addRow("Açıklama:", self.txt_desc)

        main_layout.addLayout(form)

        # Talep bilgilerini yükle
        if request_id:
            self._load_request_data(request_id)

        # Buttons
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        main_layout.addWidget(btns)

    def _load_request_data(self, request_id: int):
        """Talep bilgilerini forma yükle"""
        request = self.service.get_request_by_id(request_id)
        if not request:
            return

        # Ekipman seçimi
        idx = self.cmb_equipment.findData(request.equipment_id)
        if idx >= 0:
            self.cmb_equipment.setCurrentIndex(idx)

        # Öncelik
        idx = self.cmb_priority.findData(request.priority)
        if idx >= 0:
            self.cmb_priority.setCurrentIndex(idx)

        # Açıklama
        self.txt_desc.setText(f"[Talep: {request.request_no}]\n{request.description}")

    def accept(self):
        equipment_id = self.cmb_equipment.currentData()
        if not equipment_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir ekipman seçin.")
            return

        try:
            wo = self.service.create_work_order(
                equipment_id=equipment_id,
                request_id=self.request_id,
                assigned_to_id=self.cmb_user.currentData(),
                priority=self.cmb_priority.currentData(),
                planned_start_date=self.dt_planned.dateTime().toPyDateTime(),
                due_date=self.dt_due.dateTime().toPyDateTime(),
                estimated_hours=self.spin_estimated.value(),
                checklist_id=self.cmb_checklist.currentData(),
                description=self.txt_desc.toPlainText().strip(),
            )

            QMessageBox.information(
                self, "Başarılı",
                f"İş emri oluşturuldu: {wo.order_no}"
            )
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))


class WorkOrderDetailsDialog(QDialog):
    """İş Emri Detay ve İşlem Dialogu"""

    def __init__(self, service, work_order_id: int, parent=None):
        super().__init__(parent)
        self.service = service
        self.work_order_id = work_order_id
        self.wo = service.get_work_order_by_id(work_order_id)

        self.setWindowTitle(f"İş Emri - {self.wo.order_no}")
        self.setMinimumSize(900, 700)

        main_layout = QVBoxLayout(self)

        # Başlık ve durum
        header = QHBoxLayout()
        title = QLabel(f"{self.wo.order_no} - {self.wo.equipment.name if self.wo.equipment else ''}")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header.addWidget(title)

        status_text = {
            WorkOrderStatus.DRAFT: ("Taslak", "#6b7280"),
            WorkOrderStatus.ASSIGNED: ("Atandı", "#3b82f6"),
            WorkOrderStatus.IN_PROGRESS: ("Devam Ediyor", "#f97316"),
            WorkOrderStatus.COMPLETED: ("Tamamlandı", "#22c55e"),
            WorkOrderStatus.CLOSED: ("Kapandı", "#6b7280"),
            WorkOrderStatus.CANCELLED: ("İptal", "#ef4444"),
        }.get(self.wo.status, (self.wo.status.value, "#gray"))

        status_label = QLabel(status_text[0])
        status_label.setStyleSheet(f"""
            background-color: {status_text[1]};
            color: white;
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: bold;
        """)
        header.addWidget(status_label)
        header.addStretch()
        main_layout.addLayout(header)

        # Tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Tab 1: Genel Bilgiler
        self.tab_general = QWidget()
        self.setup_general_tab()
        self.tabs.addTab(self.tab_general, "Genel Bilgiler")

        # Tab 2: Kontrol Listesi
        self.tab_checklist = QWidget()
        self.setup_checklist_tab()
        self.tabs.addTab(self.tab_checklist, "Kontrol Listesi")

        # Tab 3: Yedek Parçalar
        self.tab_parts = QWidget()
        self.setup_parts_tab()
        self.tabs.addTab(self.tab_parts, "Yedek Parçalar")

        # Tab 4: Dosya Ekleri
        self.tab_attachments = QWidget()
        self.setup_attachments_tab()
        self.tabs.addTab(self.tab_attachments, "Dosya Ekleri")

        # Alt butonlar
        btn_layout = QHBoxLayout()

        if self.wo.status in [WorkOrderStatus.DRAFT, WorkOrderStatus.ASSIGNED]:
            btn_start = QPushButton("İşi Başlat")
            btn_start.setStyleSheet("background-color: #007acc; color: white; padding: 10px 20px;")
            btn_start.clicked.connect(self.start_work)
            btn_layout.addWidget(btn_start)

        if self.wo.status == WorkOrderStatus.IN_PROGRESS:
            btn_complete = QPushButton("İşi Tamamla")
            btn_complete.setStyleSheet("background-color: #22c55e; color: white; padding: 10px 20px;")
            btn_complete.clicked.connect(self.complete_work)
            btn_layout.addWidget(btn_complete)

        btn_layout.addStretch()

        btn_close = QPushButton("Kapat")
        btn_close.clicked.connect(self.close)
        btn_layout.addWidget(btn_close)

        main_layout.addLayout(btn_layout)

    def setup_general_tab(self):
        layout = QVBoxLayout(self.tab_general)

        # Bilgi formu
        info_group = QGroupBox("İş Emri Bilgileri")
        form = QFormLayout(info_group)

        form.addRow("Ekipman:", QLabel(self.wo.equipment.name if self.wo.equipment else "-"))
        form.addRow("Bağlı Talep:", QLabel(
            self.wo.request.request_no if self.wo.request else "-"
        ))
        form.addRow("Atanan:", QLabel(
            self.wo.assigned_to.full_name if self.wo.assigned_to else "-"
        ))
        form.addRow("Öncelik:", QLabel(self.wo.priority.value.capitalize()))

        # Tarihler
        form.addRow("Planlanan Başlangıç:", QLabel(
            self.wo.planned_start_date.strftime("%d.%m.%Y %H:%M") if self.wo.planned_start_date else "-"
        ))
        form.addRow("Gerçek Başlangıç:", QLabel(
            self.wo.actual_start_date.strftime("%d.%m.%Y %H:%M") if self.wo.actual_start_date else "-"
        ))
        form.addRow("Tamamlanma:", QLabel(
            self.wo.completed_date.strftime("%d.%m.%Y %H:%M") if self.wo.completed_date else "-"
        ))

        # Süre bilgileri
        form.addRow("Tahmini Süre:", QLabel(f"{self.wo.estimated_hours or 0:.1f} saat"))
        form.addRow("Gerçekleşen Süre:", QLabel(f"{self.wo.actual_hours or 0:.1f} saat"))

        layout.addWidget(info_group)

        # Notlar
        notes_group = QGroupBox("Notlar")
        notes_layout = QVBoxLayout(notes_group)
        self.txt_notes = QTextEdit()
        self.txt_notes.setPlainText(self.wo.notes or "")
        self.txt_notes.setPlaceholderText("Çalışma notları, gözlemler...")
        notes_layout.addWidget(self.txt_notes)

        if self.wo.status == WorkOrderStatus.IN_PROGRESS:
            btn_save_notes = QPushButton("Notları Kaydet")
            btn_save_notes.clicked.connect(self.save_notes)
            notes_layout.addWidget(btn_save_notes)

        layout.addWidget(notes_group)

        # Maliyet özeti
        cost_group = QGroupBox("Maliyet Özeti")
        cost_layout = QFormLayout(cost_group)
        cost_layout.addRow("Malzeme Maliyeti:", QLabel(f"₺{self.wo.material_cost or 0:,.2f}"))
        cost_layout.addRow("İşçilik Maliyeti:", QLabel(f"₺{self.wo.labor_cost or 0:,.2f}"))
        cost_layout.addRow("Toplam:", QLabel(f"₺{self.wo.total_cost or 0:,.2f}"))
        layout.addWidget(cost_group)

    def setup_checklist_tab(self):
        layout = QVBoxLayout(self.tab_checklist)

        if not self.wo.checklist_id:
            layout.addWidget(QLabel("Bu iş emrine kontrol listesi atanmamış."))
            return

        self.checklist_widget = QListWidget()
        checklist_results = self.service.get_work_order_checklist_results(self.work_order_id)

        for result in checklist_results:
            item = QListWidgetItem(result.checklist_item.description)
            item.setData(Qt.ItemDataRole.UserRole, result.id)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if result.is_checked else Qt.CheckState.Unchecked)
            self.checklist_widget.addItem(item)

        self.checklist_widget.itemChanged.connect(self.on_checklist_item_changed)
        layout.addWidget(self.checklist_widget)

    def on_checklist_item_changed(self, item: QListWidgetItem):
        result_id = item.data(Qt.ItemDataRole.UserRole)
        is_checked = item.checkState() == Qt.CheckState.Checked
        try:
            self.service.update_checklist_result(result_id, is_checked)
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def setup_parts_tab(self):
        layout = QVBoxLayout(self.tab_parts)

        # Butonlar
        if self.wo.status not in [WorkOrderStatus.COMPLETED, WorkOrderStatus.CANCELLED, WorkOrderStatus.CLOSED]:
            btn_layout = QHBoxLayout()
            btn_add = QPushButton("Stoktan Parça Ekle")
            btn_add.clicked.connect(self.show_add_part_dialog)
            btn_layout.addWidget(btn_add)

            btn_purchase = QPushButton("Satınalma Talebi Oluştur")
            btn_purchase.setStyleSheet("background-color: #eab308; color: black;")
            btn_purchase.clicked.connect(self.create_purchase_request)
            btn_layout.addWidget(btn_purchase)

            btn_layout.addStretch()
            layout.addLayout(btn_layout)

        # Parça tablosu
        self.parts_table = QTableWidget()
        self.parts_table.setColumnCount(5)
        self.parts_table.setHorizontalHeaderLabels([
            "Parça Kodu", "Parça Adı", "Miktar", "Birim Maliyet", "Toplam"
        ])
        self.parts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.parts_table)

        self.refresh_parts()

    def refresh_parts(self):
        parts = self.wo.parts
        self.parts_table.setRowCount(len(parts))
        for i, part in enumerate(parts):
            self.parts_table.setItem(i, 0, QTableWidgetItem(
                part.item.code if part.item else "-"
            ))
            self.parts_table.setItem(i, 1, QTableWidgetItem(
                part.item.name if part.item else "-"
            ))
            self.parts_table.setItem(i, 2, QTableWidgetItem(
                f"{part.quantity} {part.unit.code if part.unit else ''}"
            ))
            self.parts_table.setItem(i, 3, QTableWidgetItem(f"₺{part.unit_cost or 0:,.2f}"))
            self.parts_table.setItem(i, 4, QTableWidgetItem(f"₺{part.total_cost or 0:,.2f}"))

    def setup_attachments_tab(self):
        layout = QVBoxLayout(self.tab_attachments)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Dosya Ekle")
        btn_add.clicked.connect(self.add_attachment)
        btn_layout.addWidget(btn_add)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Dosya listesi
        self.attachments_list = QListWidget()
        attachments = self.service.get_work_order_attachments(self.work_order_id)
        for att in attachments:
            item = QListWidgetItem(f"{att.file_name} ({att.file_type})")
            item.setData(Qt.ItemDataRole.UserRole, att.id)
            self.attachments_list.addItem(item)
        layout.addWidget(self.attachments_list)

    def start_work(self):
        try:
            self.service.start_work_order(self.work_order_id)
            QMessageBox.information(self, "Bilgi", "İş emri başlatıldı.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def complete_work(self):
        # İşçilik saati sor
        hours, ok = self._get_labor_hours()
        if not ok:
            return

        notes = self.txt_notes.toPlainText()
        try:
            self.service.complete_work_order(
                self.work_order_id,
                notes=notes,
                actual_hours=hours
            )
            QMessageBox.information(self, "Bilgi", "İş emri tamamlandı.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _get_labor_hours(self):
        """İşçilik saati giriş dialogu"""
        from PyQt6.QtWidgets import QInputDialog
        hours, ok = QInputDialog.getDouble(
            self, "İşçilik Saati",
            "Toplam çalışma süresi (saat):",
            value=1.0, min=0.1, max=100, decimals=1
        )
        return hours, ok

    def save_notes(self):
        try:
            self.service.update_work_order_notes(
                self.work_order_id,
                self.txt_notes.toPlainText()
            )
            QMessageBox.information(self, "Bilgi", "Notlar kaydedildi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def show_add_part_dialog(self):
        dialog = AddPartDialog(self.service, self.work_order_id, self)
        if dialog.exec():
            self.service.db.refresh(self.wo)
            self.refresh_parts()

    def create_purchase_request(self):
        QMessageBox.information(self, "Bilgi", "Satınalma talebi oluşturma ekranı açılacak.")
        # TODO: Implement

    def add_attachment(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Dosya Seç", "",
            "Tüm Dosyalar (*.*)"
        )
        if file_path:
            try:
                file_name = file_path.split('/')[-1]
                file_type = file_name.split('.')[-1] if '.' in file_name else 'unknown'
                self.service.add_work_order_attachment(
                    self.work_order_id, file_path, file_name, file_type
                )
                # Listeyi güncelle
                item = QListWidgetItem(f"{file_name} ({file_type})")
                self.attachments_list.addItem(item)
                QMessageBox.information(self, "Bilgi", "Dosya eklendi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))


class AddPartDialog(QDialog):
    """Yedek Parça Ekleme Dialogu"""

    def __init__(self, service, work_order_id: int, parent=None):
        super().__init__(parent)
        self.service = service
        self.work_order_id = work_order_id

        self.setWindowTitle("Yedek Parça Ekle")
        self.setMinimumSize(400, 300)

        main_layout = QVBoxLayout(self)

        form = QFormLayout()

        self.cmb_warehouse = QComboBox()
        warehouses = self.service.get_all_warehouses()
        for w in warehouses:
            self.cmb_warehouse.addItem(w.name, w.id)
        self.cmb_warehouse.currentIndexChanged.connect(self.load_items)
        form.addRow("Depo:", self.cmb_warehouse)

        self.cmb_item = QComboBox()
        form.addRow("Parça:", self.cmb_item)

        self.spin_qty = QDoubleSpinBox()
        self.spin_qty.setRange(0.01, 9999)
        self.spin_qty.setDecimals(2)
        self.spin_qty.setValue(1)
        form.addRow("Miktar:", self.spin_qty)

        main_layout.addLayout(form)

        # İlk deponun parçalarını yükle
        if warehouses:
            self.load_items()

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        main_layout.addWidget(btns)

    def load_items(self):
        self.cmb_item.clear()
        warehouse_id = self.cmb_warehouse.currentData()
        if not warehouse_id:
            return

        items = self.service.get_items_with_stock(warehouse_id)
        for item, qty in items:
            self.cmb_item.addItem(f"{item.code} - {item.name} (Stok: {qty})", item.id)

    def accept(self):
        item_id = self.cmb_item.currentData()
        warehouse_id = self.cmb_warehouse.currentData()
        quantity = self.spin_qty.value()

        if not item_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir parça seçin.")
            return

        try:
            self.service.add_part_to_work_order(
                self.work_order_id, item_id, quantity, warehouse_id
            )
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
