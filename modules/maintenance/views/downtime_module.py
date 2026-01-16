"""
Bakım Modülü - Duruş Takibi
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
    QDateTimeEdit,
    QGroupBox,
)
from PyQt6.QtCore import Qt, QDateTime, QTimer

from modules.maintenance.views.base import MaintenanceBaseWidget


class DowntimeTrackerWidget(MaintenanceBaseWidget):
    """Duruş Takibi Widget'ı"""

    def __init__(self, parent=None):
        super().__init__("Duruş Takibi", parent)
        self.setup_ui()

        # Aktif duruşları periyodik güncelle
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_active_downtimes)
        self.timer.start(60000)  # Her dakika

    def setup_ui(self):
        # Üst Butonlar
        btn_layout = QHBoxLayout()

        self.btn_start = QPushButton("Duruş Başlat")
        self.btn_start.setStyleSheet(
            "background-color: #ef4444; color: white; padding: 8px 16px; border-radius: 4px;"
        )
        self.btn_start.clicked.connect(self.start_downtime)
        btn_layout.addWidget(self.btn_start)

        self.btn_end = QPushButton("Seçili Duruşu Bitir")
        self.btn_end.setStyleSheet(
            "background-color: #22c55e; color: white; padding: 8px 16px; border-radius: 4px;"
        )
        self.btn_end.clicked.connect(self.end_downtime)
        btn_layout.addWidget(self.btn_end)

        btn_layout.addStretch()

        # Filtre
        self.cmb_filter = QComboBox()
        self.cmb_filter.addItem("Aktif Duruşlar", "active")
        self.cmb_filter.addItem("Bugün", "today")
        self.cmb_filter.addItem("Bu Hafta", "week")
        self.cmb_filter.addItem("Tümü", "all")
        self.cmb_filter.currentIndexChanged.connect(self.refresh_data)
        btn_layout.addWidget(QLabel("Göster:"))
        btn_layout.addWidget(self.cmb_filter)

        self.layout.addLayout(btn_layout)

        # Aktif duruş özet kartları
        self.active_summary_layout = QHBoxLayout()
        self.layout.addLayout(self.active_summary_layout)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Ekipman", "Başlangıç", "Bitiş", "Süre", "Sebep", "İş Emri", "Durum"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.layout.addWidget(self.table)

        self.refresh_data()

    def refresh_data(self):
        filter_type = self.cmb_filter.currentData()

        if filter_type == "active":
            downtimes = self.service.get_active_downtimes()
        elif filter_type == "today":
            downtimes = self.service.get_today_downtimes()
        elif filter_type == "week":
            downtimes = self.service.get_week_downtimes()
        else:
            downtimes = self.service.get_all_downtimes()

        self._refresh_active_summary()
        self._populate_table(downtimes)

    def _refresh_active_summary(self):
        """Aktif duruş özet kartlarını güncelle"""
        # Temizle
        while self.active_summary_layout.count():
            item = self.active_summary_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        active_downtimes = self.service.get_active_downtimes()
        if not active_downtimes:
            label = QLabel("Aktif duruş yok")
            label.setStyleSheet("color: #22c55e; font-weight: bold;")
            self.active_summary_layout.addWidget(label)
            return

        for dt in active_downtimes[:5]:  # Max 5 kart göster
            card = self._create_active_downtime_card(dt)
            self.active_summary_layout.addWidget(card)

        if len(active_downtimes) > 5:
            more_label = QLabel(f"+{len(active_downtimes) - 5} daha")
            more_label.setStyleSheet("color: #6b7280;")
            self.active_summary_layout.addWidget(more_label)

        self.active_summary_layout.addStretch()

    def _create_active_downtime_card(self, downtime) -> QWidget:
        """Aktif duruş kartı oluştur"""
        card = QGroupBox()
        card.setStyleSheet("""
            QGroupBox {
                background-color: #fef2f2;
                border: 2px solid #ef4444;
                border-radius: 8px;
                padding: 8px;
            }
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(8, 8, 8, 8)

        # Ekipman adı
        lbl_equipment = QLabel(downtime.equipment.code if downtime.equipment else "-")
        lbl_equipment.setStyleSheet("font-weight: bold; color: #dc2626;")
        card_layout.addWidget(lbl_equipment)

        # Süre
        duration = datetime.now() - downtime.start_time
        minutes = int(duration.total_seconds() / 60)
        hours = minutes // 60
        mins = minutes % 60
        lbl_duration = QLabel(f"{hours}s {mins}dk")
        lbl_duration.setStyleSheet("font-size: 18px; font-weight: bold;")
        card_layout.addWidget(lbl_duration)

        # Sebep
        lbl_reason = QLabel(downtime.reason or "-")
        lbl_reason.setStyleSheet("color: #6b7280; font-size: 11px;")
        card_layout.addWidget(lbl_reason)

        return card

    def _populate_table(self, downtimes):
        """Tabloyu doldur"""
        self.table.setRowCount(len(downtimes))

        for i, dt in enumerate(downtimes):
            self.table.setItem(i, 0, QTableWidgetItem(
                dt.equipment.name if dt.equipment else "-"
            ))
            self.table.item(i, 0).setData(Qt.ItemDataRole.UserRole, dt.id)

            self.table.setItem(i, 1, QTableWidgetItem(
                dt.start_time.strftime("%d.%m.%Y %H:%M")
            ))

            self.table.setItem(i, 2, QTableWidgetItem(
                dt.end_time.strftime("%d.%m.%Y %H:%M") if dt.end_time else "-"
            ))

            # Süre hesapla
            if dt.end_time:
                duration = dt.end_time - dt.start_time
            else:
                duration = datetime.now() - dt.start_time
            minutes = int(duration.total_seconds() / 60)
            hours = minutes // 60
            mins = minutes % 60
            duration_item = QTableWidgetItem(f"{hours}s {mins}dk")
            if not dt.end_time:
                duration_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(i, 3, duration_item)

            # Sebep
            reason_labels = {
                "breakdown": "Arıza",
                "maintenance": "Bakım",
                "setup": "Kurulum/Ayar",
                "no_material": "Malzeme Yok",
                "no_operator": "Operatör Yok",
                "quality_issue": "Kalite Sorunu",
                "other": "Diğer",
            }
            self.table.setItem(i, 4, QTableWidgetItem(
                reason_labels.get(dt.reason, dt.reason or "-")
            ))

            self.table.setItem(i, 5, QTableWidgetItem(
                dt.work_order.order_no if dt.work_order else "-"
            ))

            # Durum
            status_item = QTableWidgetItem("Devam Ediyor" if not dt.end_time else "Tamamlandı")
            if not dt.end_time:
                status_item.setForeground(Qt.GlobalColor.red)
            else:
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            self.table.setItem(i, 6, status_item)

    def update_active_downtimes(self):
        """Aktif duruşları güncelle (timer callback)"""
        if self.cmb_filter.currentData() == "active":
            self._refresh_active_summary()
            # Süre sütunlarını güncelle
            for i in range(self.table.rowCount()):
                status_item = self.table.item(i, 6)
                if status_item and status_item.text() == "Devam Ediyor":
                    # Başlangıç zamanından süreyi yeniden hesapla
                    start_text = self.table.item(i, 1).text()
                    try:
                        start_time = datetime.strptime(start_text, "%d.%m.%Y %H:%M")
                        duration = datetime.now() - start_time
                        minutes = int(duration.total_seconds() / 60)
                        hours = minutes // 60
                        mins = minutes % 60
                        self.table.item(i, 3).setText(f"{hours}s {mins}dk")
                    except:
                        pass

    def get_selected_downtime_id(self) -> Optional[int]:
        current_row = self.table.currentRow()
        if current_row < 0:
            return None
        return self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)

    def start_downtime(self):
        dialog = DowntimeStartDialog(self.service, self)
        if dialog.exec():
            self.refresh_data()

    def end_downtime(self):
        downtime_id = self.get_selected_downtime_id()
        if not downtime_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir duruş seçin.")
            return

        downtime = self.service.get_downtime_by_id(downtime_id)
        if downtime.end_time:
            QMessageBox.warning(self, "Uyarı", "Bu duruş zaten sonlandırılmış.")
            return

        reply = QMessageBox.question(
            self,
            "Onay",
            "Bu duruşu şimdi sonlandırmak istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.service.end_downtime(downtime_id)
                QMessageBox.information(self, "Bilgi", "Duruş sonlandırıldı.")
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))

    def closeEvent(self, event):
        self.timer.stop()
        super().closeEvent(event)


class DowntimeStartDialog(QDialog):
    """Duruş Başlatma Dialogu"""

    def __init__(self, service, parent=None):
        super().__init__(parent)
        self.service = service

        self.setWindowTitle("Duruş Başlat")
        self.setMinimumSize(400, 350)

        main_layout = QVBoxLayout(self)

        form = QFormLayout()

        self.cmb_equipment = QComboBox()
        equipments = self.service.get_equipment_list(active_only=True)
        for eq in equipments:
            self.cmb_equipment.addItem(f"{eq.code} - {eq.name}", eq.id)
        form.addRow("Ekipman*:", self.cmb_equipment)

        self.cmb_reason = QComboBox()
        reasons = [
            ("breakdown", "Arıza"),
            ("maintenance", "Bakım"),
            ("setup", "Kurulum/Ayar"),
            ("no_material", "Malzeme Yok"),
            ("no_operator", "Operatör Yok"),
            ("quality_issue", "Kalite Sorunu"),
            ("other", "Diğer"),
        ]
        for code, label in reasons:
            self.cmb_reason.addItem(label, code)
        form.addRow("Sebep*:", self.cmb_reason)

        self.dt_start = QDateTimeEdit()
        self.dt_start.setCalendarPopup(True)
        self.dt_start.setDateTime(QDateTime.currentDateTime())
        form.addRow("Başlangıç:", self.dt_start)

        # İş emri bağlantısı (opsiyonel)
        self.cmb_work_order = QComboBox()
        self.cmb_work_order.addItem("- İş Emri Yok -", None)
        work_orders = self.service.get_active_work_orders()
        for wo in work_orders:
            self.cmb_work_order.addItem(
                f"{wo.order_no} - {wo.equipment.name if wo.equipment else ''}",
                wo.id
            )
        form.addRow("Bağlı İş Emri:", self.cmb_work_order)

        self.txt_notes = QTextEdit()
        self.txt_notes.setMaximumHeight(80)
        self.txt_notes.setPlaceholderText("Ek notlar...")
        form.addRow("Notlar:", self.txt_notes)

        main_layout.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        main_layout.addWidget(btns)

    def accept(self):
        equipment_id = self.cmb_equipment.currentData()
        reason = self.cmb_reason.currentData()

        if not equipment_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir ekipman seçin.")
            return

        try:
            self.service.start_downtime(
                equipment_id=equipment_id,
                reason=reason,
                start_time=self.dt_start.dateTime().toPyDateTime(),
                work_order_id=self.cmb_work_order.currentData(),
                notes=self.txt_notes.toPlainText().strip() or None
            )
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
