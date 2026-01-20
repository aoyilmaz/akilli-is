"""
Akıllı İş - Operatör Paneli (Tablet Optimized)
Dokunmatik ekran ve tablet için optimize edilmiş üretim paneli
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGridLayout,
    QFrame,
    QMessageBox,
    QInputDialog,
    QDialog,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from modules.production.services import WorkOrderService, WorkStationService


from config.styles import (
    BG_PRIMARY,
    BG_SECONDARY,
    BG_TERTIARY,
    BORDER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    ACCENT,
    SUCCESS,
    WARNING,
    ERROR,
)


# Compatibility Mappings
MAIN_BG = BG_PRIMARY
CARD_BG = BG_SECONDARY
BORDER_COLOR = BORDER
# TEXT_PRIMARY, TEXT_MUTED are imported
TEXT_SECONDARY = TEXT_MUTED

GREEN = SUCCESS
GREEN_HOVER = SUCCESS
YELLOW = WARNING
YELLOW_HOVER = WARNING
RED = ERROR
RED_HOVER = ERROR
BLUE = ACCENT
BLUE_HOVER = ACCENT
TEAL = "#0d9488"  # Keeping specific teal if needed, or map to ACCENT
TEAL_HOVER = "#0f766e"


def make_btn_style(bg, hover):
    return f"""
    QPushButton {{
        background-color: {bg};
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 16px;
        font-weight: bold;
        padding: 10px;
    }}
    QPushButton:hover {{ background-color: {hover}; }}
    """


class StationSelectDialog(QDialog):
    """İş istasyonu seçim dialogu"""

    def __init__(self, stations, parent=None):
        super().__init__(parent)
        self.setWindowTitle("İş İstasyonu Seçimi")
        self.setMinimumSize(400, 300)
        self.stations = stations
        self.selected_station = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Dialog styling
        self.setStyleSheet(f"background-color: {BG_PRIMARY}; color: {TEXT_PRIMARY};")

        title = QLabel("🏭 İstasyon Seçin")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        self.station_list = QListWidget()
        self.station_list.setStyleSheet(
            f"""
            QListWidget {{ 
                background: {BG_SECONDARY}; border: 1px solid {BORDER}; font-size: 16px; 
            }}
            QListWidget::item {{ 
                padding: 16px; margin: 4px; 
                background: {BG_TERTIARY}; border-radius: 8px; 
            }}
            QListWidget::item:selected {{ background: {ACCENT}; }}
        """
        )
        for s in self.stations:
            self.station_list.addItem(f"{s.code} - {s.name}")
        layout.addWidget(self.station_list)

        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        select_btn = QPushButton("Seç")
        select_btn.setStyleSheet(make_btn_style(BLUE, BLUE_HOVER))
        select_btn.clicked.connect(self._on_select)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(select_btn)
        layout.addLayout(btn_layout)

    def _on_select(self):
        idx = self.station_list.currentRow()
        if idx >= 0:
            self.selected_station = self.stations[idx]
            self.accept()


class OperatorPanel(QWidget):
    """
    Operatör Paneli - Tablet Optimize
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = WorkOrderService()
        self.station_service = WorkStationService()
        self.current_station = None
        self.active_operation = None
        self.active_personnel = []
        self.elapsed_seconds = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self._update_timer)

        self._setup_ui()

    def _setup_ui(self):
        # Inject custom styles for this panel
        self.setStyleSheet(
            f"""
            QWidget {{ background-color: {BG_PRIMARY}; color: {TEXT_PRIMARY}; }}
            
            QFrame[class="panel-header"] {{ background-color: {BG_SECONDARY}; border-bottom: 1px solid {BORDER}; }}
            QFrame[class="panel-card"] {{ background-color: {BG_SECONDARY}; border: 1px solid {BORDER}; border-radius: 12px; }}
            QListWidget[class="panel-list"] {{ background-color: {BG_PRIMARY}; border: none; border-radius: 8px; }}
            
            /* Buttons */
            QPushButton[class="btn-large-green"] {{ background-color: {SUCCESS}; color: white; border-radius: 8px; font-weight: bold; font-size: 18px; }}
            QPushButton[class="btn-large-yellow"] {{ background-color: {WARNING}; color: white; border-radius: 8px; font-weight: bold; font-size: 18px; }}
            QPushButton[class="btn-large-red"] {{ background-color: {ERROR}; color: white; border-radius: 8px; font-weight: bold; font-size: 18px; }}
            QPushButton[class="btn-large-teal"] {{ background-color: {ACCENT}; color: white; border-radius: 8px; font-weight: bold; font-size: 18px; }}
            QPushButton[class="btn-secondary"] {{ background-color: {BG_TERTIARY}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER}; border-radius: 8px; padding: 8px; }}
            QPushButton[class="btn-icon-circle"] {{ background-color: {BG_TERTIARY}; border-radius: 18px; border: 1px solid {BORDER}; }}
            
            QLabel[class="label-blue"] {{ color: {ACCENT}; font-weight: bold; }}
            QLabel[class="label-green"] {{ color: {SUCCESS}; font-weight: bold; }}
            QLabel[class="label-muted"] {{ color: {TEXT_MUTED}; }}
            QLabel[class="warning-box"] {{ background-color: {ERROR}20; color: {ERROR}; padding: 10px; border-radius: 6px; }}
            QFrame[class="timer-frame"] {{ background-color: {BG_TERTIARY}; border-radius: 12px; border: 1px solid {BORDER}; }}
            QLabel[class="timer-label"] {{ color: {TEXT_PRIMARY}; font-weight: bold; }}
            
            QLineEdit[class="barcode-input"] {{ 
                background-color: {BG_TERTIARY}; 
                border: 1px solid {BORDER}; 
                border-radius: 6px; 
                padding: 8px; 
                color: {TEXT_PRIMARY};
            }}
        """
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(8)

        # === HEADER BAR ===
        header = QFrame()
        header.setFixedHeight(50)
        header.setProperty("class", "panel-header")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 0, 16, 0)

        # Makine bilgisi
        self.station_label = QLabel("🏭 Makine: -")
        self.station_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.station_label.setProperty("class", "label-blue")
        h_layout.addWidget(self.station_label)

        # İş emri bilgisi
        self.order_label = QLabel("📋 İş Emri: -")
        self.order_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.order_label.setProperty("class", "label-green")
        h_layout.addWidget(self.order_label)

        h_layout.addStretch()

        # Barkod girişi
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("📷 Barkod / İş Emri No")
        self.barcode_input.setFixedWidth(200)
        self.barcode_input.setProperty("class", "barcode-input")
        self.barcode_input.returnPressed.connect(self._on_barcode_scan)
        h_layout.addWidget(self.barcode_input)

        # İstasyon değiştir
        change_btn = QPushButton("⚙")
        change_btn.setFixedSize(36, 36)
        change_btn.setProperty("class", "btn-icon-circle")
        change_btn.clicked.connect(self._select_station)
        h_layout.addWidget(change_btn)

        main_layout.addWidget(header)

        # === CONTENT AREA ===
        content = QHBoxLayout()
        content.setSpacing(8)

        # --- SOL: İş Listesi ---
        left_panel = QFrame()
        left_panel.setFixedWidth(280)
        left_panel.setProperty("class", "panel-card")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(8)

        left_title = QLabel("📋 Bekleyen İşler")
        left_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        left_layout.addWidget(left_title)

        self.job_list = QListWidget()
        self.job_list.setProperty("class", "panel-list")
        self.job_list.itemClicked.connect(self._on_job_selected)
        left_layout.addWidget(self.job_list)

        content.addWidget(left_panel)

        # --- ORTA: Aktif Operasyon ---
        center_panel = QFrame()
        center_panel.setProperty("class", "panel-card")
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(16, 12, 16, 12)
        center_layout.setSpacing(8)

        # Operasyon başlığı
        self.op_title = QLabel("Operasyon seçin...")
        self.op_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.op_title.setProperty("class", "label-muted")
        center_layout.addWidget(self.op_title)

        # Operasyon detay
        self.op_detail = QLabel("")
        self.op_detail.setFont(QFont("Segoe UI", 12))
        self.op_detail.setProperty("class", "label-muted")
        self.op_detail.setWordWrap(True)
        center_layout.addWidget(self.op_detail)

        # Uyarı kutusu
        self.warning_box = QLabel()
        self.warning_box.setProperty("class", "warning-box")
        self.warning_box.setWordWrap(True)
        self.warning_box.hide()
        center_layout.addWidget(self.warning_box)

        center_layout.addStretch()

        # Timer
        timer_frame = QFrame()
        timer_frame.setProperty("class", "timer-frame")
        timer_layout = QVBoxLayout(timer_frame)
        timer_layout.setContentsMargins(20, 12, 20, 12)

        self.timer_label = QLabel("00:00:00")
        self.timer_label.setFont(QFont("Segoe UI", 56, QFont.Weight.Bold))
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setProperty("class", "timer-label")
        timer_layout.addWidget(self.timer_label)

        center_layout.addWidget(timer_frame)

        center_layout.addStretch()

        # Butonlar - 2x2 Grid
        btn_grid = QGridLayout()
        btn_grid.setSpacing(10)

        self.btn_start = QPushButton("▶ BAŞLAT")
        self.btn_start.setProperty("class", "btn-large-green")
        self.btn_start.setMinimumHeight(55)
        self.btn_start.clicked.connect(self._start_operation)
        btn_grid.addWidget(self.btn_start, 0, 0)

        self.btn_pause = QPushButton("⏸ DURAKLAT")
        self.btn_pause.setProperty("class", "btn-large-yellow")
        self.btn_pause.setMinimumHeight(55)
        self.btn_pause.clicked.connect(self._pause_operation)
        self.btn_pause.hide()
        btn_grid.addWidget(self.btn_pause, 0, 0)

        self.btn_scrap = QPushButton("🗑 HURDA")
        self.btn_scrap.setProperty("class", "btn-large-red")
        self.btn_scrap.setMinimumHeight(55)
        self.btn_scrap.clicked.connect(self._report_scrap)
        btn_grid.addWidget(self.btn_scrap, 0, 1)

        self.btn_finish = QPushButton("✅ BİTİR")
        self.btn_finish.setProperty("class", "btn-large-teal")
        self.btn_finish.setMinimumHeight(55)
        self.btn_finish.clicked.connect(self._finish_operation)
        btn_grid.addWidget(self.btn_finish, 1, 0, 1, 2)

        center_layout.addLayout(btn_grid)

        content.addWidget(center_panel, stretch=1)

        # --- SAĞ: Personel ---
        right_panel = QFrame()
        right_panel.setFixedWidth(220)
        right_panel.setProperty("class", "panel-card")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(8)

        right_title = QLabel("👥 Personel")
        right_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        right_layout.addWidget(right_title)

        # Personel sicil girişi
        self.personnel_input = QLineEdit()
        self.personnel_input.setPlaceholderText("Sicil No...")
        self.personnel_input.setProperty("class", "barcode-input")
        self.personnel_input.returnPressed.connect(self._add_personnel_by_id)
        right_layout.addWidget(self.personnel_input)

        # Personel listesi
        self.personnel_list = QListWidget()
        self.personnel_list.setProperty("class", "panel-list")
        right_layout.addWidget(self.personnel_list)

        # Personel çıkar butonu
        remove_btn = QPushButton("➖ Çıkar")
        remove_btn.setProperty("class", "btn-secondary")
        remove_btn.clicked.connect(self._remove_personnel)
        right_layout.addWidget(remove_btn)

        content.addWidget(right_panel)

        main_layout.addLayout(content)

        # İlk durumu ayarla
        self._set_ui_state("idle")

    def _set_ui_state(self, state: str):
        """UI durumunu ayarla: idle, selected, running"""
        if state == "idle":
            self.btn_start.setEnabled(False)
            self.btn_pause.hide()
            self.btn_start.show()
            self.btn_scrap.setEnabled(False)
            self.btn_finish.setEnabled(False)
        elif state == "selected":
            self.btn_start.setEnabled(True)
            self.btn_pause.hide()
            self.btn_start.show()
            self.btn_scrap.setEnabled(False)
            self.btn_finish.setEnabled(False)
        elif state == "running":
            self.btn_start.hide()
            self.btn_pause.show()
            self.btn_scrap.setEnabled(True)
            self.btn_finish.setEnabled(True)

    def _select_station(self):
        """İstasyon seçim dialogunu göster"""
        stations = self.station_service.get_all()
        if not stations:
            QMessageBox.warning(self, "Uyarı", "Tanımlı iş istasyonu yok!")
            return

        dialog = StationSelectDialog(stations, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if dialog.selected_station:
                self.current_station = dialog.selected_station
                self.station_label.setText(f"🏭 {self.current_station.code}")
                self._load_jobs()

    def _load_jobs(self):
        """Bekleyen işleri yükle"""
        self.job_list.clear()
        if not self.current_station:
            return

        # İstasyona atanmış pending/in_progress operasyonları getir
        from database.models.production import (
            WorkOrderOperation,
            WorkOrder,
            WorkOrderStatus,
        )

        operations = (
            self.service.session.query(WorkOrderOperation)
            .join(WorkOrder)
            .filter(
                WorkOrderOperation.work_station_id == self.current_station.id,
                WorkOrderOperation.status.in_(["pending", "in_progress"]),
                WorkOrder.status.in_(
                    [WorkOrderStatus.RELEASED, WorkOrderStatus.IN_PROGRESS]
                ),
            )
            .order_by(WorkOrderOperation.operation_no)
            .all()
        )

        for op in operations:
            status_icon = "🔄" if op.status == "in_progress" else "⏳"
            text = f"{status_icon} {op.work_order.order_no}\n   {op.name}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, op)
            self.job_list.addItem(item)

    def _on_job_selected(self, item: QListWidgetItem):
        """İş seçildiğinde"""
        op = item.data(Qt.ItemDataRole.UserRole)
        if not op:
            return

        self.active_operation = op
        self.order_label.setText(f"📋 {op.work_order.order_no}")
        self.op_title.setText(f"{op.name}")
        self.op_title.setStyleSheet(f"color: {TEXT_PRIMARY};")

        # Detay bilgisi
        wo = op.work_order
        detail = (
            f"Ürün: {wo.item.code if wo.item else '-'}\n"
            f"Miktar: {wo.planned_quantity} {wo.unit.code if wo.unit else ''}"
        )
        self.op_detail.setText(detail)

        # Öncül kontrolü
        if op.predecessor_id:
            pred = self.service.get_operation_by_id(op.predecessor_id)
            if pred and pred.status != "completed":
                self.warning_box.setText(
                    f"⚠ Önceki operasyon tamamlanmadı: {pred.name}"
                )
                self.warning_box.show()
            else:
                self.warning_box.hide()
        else:
            self.warning_box.hide()

        # Durum
        if op.status == "in_progress":
            self._set_ui_state("running")
            self._start_timer_from_operation()
        else:
            self._set_ui_state("selected")
            self.timer_label.setText("00:00:00")

    def _on_barcode_scan(self):
        """Barkod ile iş emri ara"""
        barcode = self.barcode_input.text().strip()
        if not barcode:
            return
        self.barcode_input.clear()

        # İş listesinde ara
        for i in range(self.job_list.count()):
            item = self.job_list.item(i)
            op = item.data(Qt.ItemDataRole.UserRole)
            if op and (barcode in op.work_order.order_no or str(op.id) == barcode):
                self.job_list.setCurrentItem(item)
                self._on_job_selected(item)
                return

        QMessageBox.information(
            self, "Bulunamadı", f"'{barcode}' ile eşleşen iş bulunamadı."
        )

    def _start_operation(self):
        """Operasyonu başlat"""
        if not self.active_operation:
            return

        try:
            self.service.start_operation(self.active_operation.id)
            self.elapsed_seconds = 0
            self.timer.start(1000)
            self._set_ui_state("running")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _pause_operation(self):
        """Operasyonu duraklat"""
        if not self.active_operation:
            return

        try:
            self.service.pause_operation(self.active_operation.id)
            self.timer.stop()
            self._set_ui_state("selected")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _report_scrap(self):
        """Hurda girişi"""
        if not self.active_operation:
            return

        qty, ok = QInputDialog.getDouble(
            self, "Hurda", "Hurda miktarı:", 0, 0, 100000, 2
        )
        if ok and qty > 0:
            reason, ok2 = QInputDialog.getText(self, "Hurda Nedeni", "Açıklama:")
            if ok2:
                try:
                    self.service.report_scrap(self.active_operation.id, qty, reason)
                    QMessageBox.information(self, "OK", "Hurda kaydedildi.")
                except Exception as e:
                    QMessageBox.critical(self, "Hata", str(e))

    def _finish_operation(self):
        """Operasyonu bitir"""
        if not self.active_operation:
            return

        reply = QMessageBox.question(
            self,
            "Onayla",
            "Bu operasyonu tamamlamak istiyor musunuz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.service.complete_operation(self.active_operation.id)
                self.timer.stop()
                self.active_operation = None
                self.order_label.setText("📋 İş Emri: -")
                self.op_title.setText("Operasyon seçin...")
                self.op_title.setStyleSheet(f"color: {TEXT_SECONDARY};")
                self.op_detail.setText("")
                self.timer_label.setText("00:00:00")
                self._set_ui_state("idle")
                self._load_jobs()
                QMessageBox.information(self, "OK", "Operasyon tamamlandı.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))

    def _update_timer(self):
        """Timer güncelle"""
        self.elapsed_seconds += 1
        h = self.elapsed_seconds // 3600
        m = (self.elapsed_seconds % 3600) // 60
        s = self.elapsed_seconds % 60
        self.timer_label.setText(f"{h:02d}:{m:02d}:{s:02d}")

    def _start_timer_from_operation(self):
        """Operasyonun başlangıç zamanından timer başlat"""
        if self.active_operation and self.active_operation.actual_start:
            from datetime import datetime

            delta = datetime.now() - self.active_operation.actual_start
            self.elapsed_seconds = int(delta.total_seconds())
            self._update_timer()
            self.timer.start(1000)

    def _add_personnel_by_id(self):
        """Sicil no (barkod) ile personel ekle"""
        if not self.active_operation:
            QMessageBox.warning(self, "Uyarı", "Önce operasyon seçin!")
            return

        sicil = self.personnel_input.text().strip().upper()
        if not sicil:
            return
        self.personnel_input.clear()

        try:
            from database.models.hr import Employee
            from database.models.production import WorkOrderOperationPersonnel

            # SADECE employee_no ile ara (barkod/QR okutma)
            employee = (
                self.service.session.query(Employee)
                .filter(Employee.employee_no == sicil)
                .first()
            )

            if not employee:
                QMessageBox.warning(
                    self, "Bulunamadı", f"'{sicil}' sicil numarası bulunamadı."
                )
                return

            # Zaten AKTİF olarak atanmış mı kontrol et (end_time=None)
            existing = (
                self.service.session.query(WorkOrderOperationPersonnel)
                .filter(
                    WorkOrderOperationPersonnel.operation_id
                    == (self.active_operation.id),
                    WorkOrderOperationPersonnel.employee_id == employee.id,
                    WorkOrderOperationPersonnel.end_time.is_(None),
                )
                .first()
            )

            if existing:
                QMessageBox.warning(
                    self,
                    "Uyarı",
                    f"{employee.first_name} {employee.last_name} "
                    "zaten bu operasyona atanmış.",
                )
                return

            # Yeni atama oluştur (employee_id ile)
            personnel = WorkOrderOperationPersonnel(
                operation_id=self.active_operation.id,
                employee_id=employee.id,
                user_id=employee.user_id,  # Varsa user_id de ekle
                role="operator",
            )
            self.service.session.add(personnel)
            self.service.session.commit()

            self._update_personnel_list()
            QMessageBox.information(
                self, "Eklendi", f"✓ {employee.first_name} {employee.last_name}"
            )

        except Exception as e:
            self.service.session.rollback()
            QMessageBox.critical(self, "Hata", str(e))

    def _update_personnel_list(self):
        """Personel listesini güncelle"""
        self.personnel_list.clear()
        if not self.active_operation:
            return

        try:
            from database.models.production import WorkOrderOperationPersonnel

            personnel = (
                self.service.session.query(WorkOrderOperationPersonnel)
                .filter(
                    WorkOrderOperationPersonnel.operation_id
                    == (self.active_operation.id),
                    WorkOrderOperationPersonnel.end_time.is_(None),
                )
                .all()
            )

            for p in personnel:
                # Employee veya User'dan isim al
                if p.employee:
                    name = f"{p.employee.first_name} {p.employee.last_name}"
                elif p.user:
                    name = f"{p.user.first_name} {p.user.last_name}"
                else:
                    name = "Bilinmeyen"

                item = QListWidgetItem(f"👤 {name}")
                item.setData(Qt.ItemDataRole.UserRole, p.id)
                self.personnel_list.addItem(item)

        except Exception as e:
            print(f"Personel listesi hatası: {e}")

    def _remove_personnel(self):
        """Seçili personeli çıkar"""
        current = self.personnel_list.currentItem()
        if not current:
            return

        assignment_id = current.data(Qt.ItemDataRole.UserRole)
        if assignment_id:
            try:
                from database.models.production import WorkOrderOperationPersonnel

                assignment = self.service.session.query(
                    WorkOrderOperationPersonnel
                ).get(assignment_id)
                if assignment:
                    self.service.remove_personnel(
                        self.active_operation.id, assignment.user_id
                    )
                    self._update_personnel_list()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
