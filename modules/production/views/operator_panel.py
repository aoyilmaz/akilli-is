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


# === STİLLER ===
MAIN_BG = "#0f172a"
CARD_BG = "#1e293b"
BORDER_COLOR = "#334155"
TEXT_PRIMARY = "#f8fafc"
TEXT_SECONDARY = "#94a3b8"
TEXT_MUTED = "#64748b"

# Buton renkleri
GREEN = "#10b981"
GREEN_HOVER = "#059669"
YELLOW = "#f59e0b"
YELLOW_HOVER = "#d97706"
RED = "#ef4444"
RED_HOVER = "#dc2626"
BLUE = "#3b82f6"
BLUE_HOVER = "#2563eb"
TEAL = "#0d9488"
TEAL_HOVER = "#0f766e"


def make_btn_style(bg, hover):
    return f"""
    QPushButton {{
        background-color: {bg};
        color: white;
        border: none;
        border-radius: 12px;
        font-size: 20px;
        font-weight: bold;
        padding: 16px;
    }}
    QPushButton:hover {{ background-color: {hover}; }}
    QPushButton:pressed {{ background-color: {hover}; }}
    QPushButton:disabled {{ background-color: #475569; color: #94a3b8; }}
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

        title = QLabel("🏭 İstasyon Seçin")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        self.station_list = QListWidget()
        self.station_list.setStyleSheet(
            """
            QListWidget { 
                background: #1e293b; border: none; font-size: 16px; 
            }
            QListWidget::item { 
                padding: 16px; margin: 4px; 
                background: #334155; border-radius: 8px; 
            }
            QListWidget::item:selected { background: #3b82f6; }
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

    Düzen:
    ┌─────────────────────────────────────────────────────┐
    │ [Makine: XXX] [İş Emri: YYY]  [Personel: ZZZ]  [?] │  <- Header
    ├─────────────────────────────────────────────────────┤
    │  ┌─────────────┐  ┌──────────────────────────────┐ │
    │  │ İŞ LİSTESİ  │  │      AKTİF OPERASYON         │ │
    │  │             │  │                              │ │
    │  │ • İş 1      │  │   ⏱ 00:45:30                 │ │
    │  │ • İş 2      │  │                              │ │
    │  │ • İş 3      │  │  [BAŞLAT] [DURAKLAT]         │ │
    │  │             │  │  [HURDA]  [BİTİR]            │ │
    │  └─────────────┘  └──────────────────────────────┘ │
    └─────────────────────────────────────────────────────┘
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
        self.setStyleSheet(f"background-color: {MAIN_BG}; color: {TEXT_PRIMARY};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(8)

        # === HEADER BAR ===
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet(
            f"""
            QFrame {{ 
                background-color: {CARD_BG}; 
                border-radius: 10px; 
            }}
        """
        )
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 0, 16, 0)

        # Makine bilgisi
        self.station_label = QLabel("🏭 Makine: -")
        self.station_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.station_label.setStyleSheet(f"color: {BLUE};")
        h_layout.addWidget(self.station_label)

        # İş emri bilgisi
        self.order_label = QLabel("📋 İş Emri: -")
        self.order_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.order_label.setStyleSheet(f"color: {GREEN};")
        h_layout.addWidget(self.order_label)

        h_layout.addStretch()

        # Barkod girişi
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("📷 Barkod / İş Emri No")
        self.barcode_input.setFixedWidth(200)
        self.barcode_input.setStyleSheet(
            f"""
            QLineEdit {{ 
                background: {MAIN_BG}; 
                border: 1px solid {BORDER_COLOR}; 
                border-radius: 6px;
                padding: 8px 12px;
                color: white;
                font-size: 13px;
            }}
        """
        )
        self.barcode_input.returnPressed.connect(self._on_barcode_scan)
        h_layout.addWidget(self.barcode_input)

        # İstasyon değiştir
        change_btn = QPushButton("⚙")
        change_btn.setFixedSize(36, 36)
        change_btn.setStyleSheet(
            f"""
            QPushButton {{ 
                background: {BORDER_COLOR}; 
                border-radius: 18px; 
                font-size: 16px;
            }}
            QPushButton:hover {{ background: #475569; }}
        """
        )
        change_btn.clicked.connect(self._select_station)
        h_layout.addWidget(change_btn)

        main_layout.addWidget(header)

        # === CONTENT AREA ===
        content = QHBoxLayout()
        content.setSpacing(8)

        # --- SOL: İş Listesi ---
        left_panel = QFrame()
        left_panel.setFixedWidth(280)
        left_panel.setStyleSheet(
            f"""
            QFrame {{ 
                background-color: {CARD_BG}; 
                border-radius: 12px; 
            }}
        """
        )
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(8)

        left_title = QLabel("📋 Bekleyen İşler")
        left_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        left_layout.addWidget(left_title)

        self.job_list = QListWidget()
        self.job_list.setStyleSheet(
            f"""
            QListWidget {{ 
                background: transparent; 
                border: none; 
            }}
            QListWidget::item {{ 
                padding: 12px; 
                margin: 2px 0; 
                background: {MAIN_BG}; 
                border-radius: 8px;
                font-size: 13px;
            }}
            QListWidget::item:selected {{ 
                background: {BLUE}; 
            }}
        """
        )
        self.job_list.itemClicked.connect(self._on_job_selected)
        left_layout.addWidget(self.job_list)

        content.addWidget(left_panel)

        # --- ORTA: Aktif Operasyon ---
        center_panel = QFrame()
        center_panel.setStyleSheet(
            f"""
            QFrame {{ 
                background-color: {CARD_BG}; 
                border-radius: 12px; 
            }}
        """
        )
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(16, 12, 16, 12)
        center_layout.setSpacing(8)

        # Operasyon başlığı
        self.op_title = QLabel("Operasyon seçin...")
        self.op_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.op_title.setStyleSheet(f"color: {TEXT_SECONDARY};")
        center_layout.addWidget(self.op_title)

        # Operasyon detay
        self.op_detail = QLabel("")
        self.op_detail.setFont(QFont("Segoe UI", 12))
        self.op_detail.setStyleSheet(f"color: {TEXT_MUTED};")
        self.op_detail.setWordWrap(True)
        center_layout.addWidget(self.op_detail)

        # Uyarı kutusu
        self.warning_box = QLabel()
        self.warning_box.setStyleSheet(
            f"""
            background: rgba(245, 158, 11, 0.15);
            border: 2px solid {YELLOW};
            border-radius: 8px;
            padding: 10px;
            color: {YELLOW};
            font-size: 12px;
        """
        )
        self.warning_box.setWordWrap(True)
        self.warning_box.hide()
        center_layout.addWidget(self.warning_box)

        center_layout.addStretch()

        # Timer
        timer_frame = QFrame()
        timer_frame.setStyleSheet(
            f"""
            background: {MAIN_BG}; 
            border-radius: 12px;
        """
        )
        timer_layout = QVBoxLayout(timer_frame)
        timer_layout.setContentsMargins(20, 12, 20, 12)

        self.timer_label = QLabel("00:00:00")
        self.timer_label.setFont(QFont("Segoe UI", 56, QFont.Weight.Bold))
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet(f"color: {RED};")
        timer_layout.addWidget(self.timer_label)

        center_layout.addWidget(timer_frame)

        center_layout.addStretch()

        # Butonlar - 2x2 Grid
        btn_grid = QGridLayout()
        btn_grid.setSpacing(10)

        self.btn_start = QPushButton("▶ BAŞLAT")
        self.btn_start.setStyleSheet(make_btn_style(GREEN, GREEN_HOVER))
        self.btn_start.setMinimumHeight(55)
        self.btn_start.clicked.connect(self._start_operation)
        btn_grid.addWidget(self.btn_start, 0, 0)

        self.btn_pause = QPushButton("⏸ DURAKLAT")
        self.btn_pause.setStyleSheet(make_btn_style(YELLOW, YELLOW_HOVER))
        self.btn_pause.setMinimumHeight(55)
        self.btn_pause.clicked.connect(self._pause_operation)
        self.btn_pause.hide()
        btn_grid.addWidget(self.btn_pause, 0, 0)

        self.btn_scrap = QPushButton("🗑 HURDA")
        self.btn_scrap.setStyleSheet(make_btn_style(RED, RED_HOVER))
        self.btn_scrap.setMinimumHeight(55)
        self.btn_scrap.clicked.connect(self._report_scrap)
        btn_grid.addWidget(self.btn_scrap, 0, 1)

        self.btn_finish = QPushButton("✅ BİTİR")
        self.btn_finish.setStyleSheet(make_btn_style(TEAL, TEAL_HOVER))
        self.btn_finish.setMinimumHeight(55)
        self.btn_finish.clicked.connect(self._finish_operation)
        btn_grid.addWidget(self.btn_finish, 1, 0, 1, 2)

        center_layout.addLayout(btn_grid)

        content.addWidget(center_panel, stretch=1)

        # --- SAĞ: Personel ---
        right_panel = QFrame()
        right_panel.setFixedWidth(220)
        right_panel.setStyleSheet(
            f"""
            QFrame {{ 
                background-color: {CARD_BG}; 
                border-radius: 12px; 
            }}
        """
        )
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(8)

        right_title = QLabel("👥 Personel")
        right_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        right_layout.addWidget(right_title)

        # Personel sicil girişi
        self.personnel_input = QLineEdit()
        self.personnel_input.setPlaceholderText("Sicil No...")
        self.personnel_input.setStyleSheet(
            f"""
            QLineEdit {{ 
                background: {MAIN_BG}; 
                border: 1px solid {BORDER_COLOR}; 
                border-radius: 6px;
                padding: 10px;
                color: white;
                font-size: 14px;
            }}
        """
        )
        self.personnel_input.returnPressed.connect(self._add_personnel_by_id)
        right_layout.addWidget(self.personnel_input)

        # Personel listesi
        self.personnel_list = QListWidget()
        self.personnel_list.setStyleSheet(
            f"""
            QListWidget {{ 
                background: transparent; 
                border: none; 
            }}
            QListWidget::item {{ 
                padding: 10px; 
                margin: 2px 0; 
                background: {MAIN_BG}; 
                border-radius: 6px;
                font-size: 12px;
            }}
            QListWidget::item:selected {{ 
                background: {BLUE}; 
            }}
        """
        )
        right_layout.addWidget(self.personnel_list)

        # Personel çıkar butonu
        remove_btn = QPushButton("➖ Çıkar")
        remove_btn.setStyleSheet(
            f"""
            QPushButton {{ 
                background: {BORDER_COLOR}; 
                color: white;
                border-radius: 8px; 
                padding: 10px;
                font-size: 13px;
            }}
            QPushButton:hover {{ background: #475569; }}
        """
        )
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
