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
    QTableWidgetItem,
    QFormLayout,
    QTextEdit,
    QComboBox,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QDateTimeEdit,
    QGroupBox,
)
from PyQt6.QtCore import Qt, QDateTime, QTimer
import qtawesome as qta

from config.icons import ICONS
from modules.maintenance.views.base import MaintenanceBaseWidget
from ui.components.page_header import PageHeader
from ui.components.stat_cards import MiniStatCard
from ui.components.enhanced_table import EnhancedTableWidget, ColumnConfig


class DowntimeTrackerWidget(MaintenanceBaseWidget):
    """Duruş Takibi Widget'ı"""

    def __init__(self, parent=None):
        super().__init__("Duruş Takibi", parent)
        self.setup_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_active_downtimes)
        self.timer.start(60000)

    def setup_ui(self):
        # Header
        self.header = PageHeader(
            title="Duruş Takibi",
            icon=ICONS.TIME,
            show_search=False,
            show_add=True,
            add_text="Duruş Başlat",
            parent=self,
        )
        self.header.add_clicked.connect(self.start_downtime)
        self.header.refresh_clicked.connect(self.refresh_data)

        h_layout = self.header.header_layout()
        h_layout.addWidget(QLabel("Göster:"))
        self.cmb_filter = QComboBox()
        self.cmb_filter.addItems(["Aktif Duruşlar", "Bugün", "Bu Hafta", "Tümü"])
        self.cmb_filter.setItemData(0, "active")
        self.cmb_filter.setItemData(1, "today")
        self.cmb_filter.setItemData(2, "week")
        self.cmb_filter.setItemData(3, "all")
        self.cmb_filter.setFixedHeight(36)
        self.cmb_filter.currentIndexChanged.connect(self.refresh_data)
        h_layout.addWidget(self.cmb_filter)
        h_layout.addStretch()

        self.btn_end = QPushButton("Duruşu Bitir")
        self.btn_end.setIcon(qta.icon(ICONS.CHECK, color="#ffffff"))
        self.btn_end.setProperty("class", "btn-success")
        self.btn_end.setFixedHeight(36)
        self.btn_end.clicked.connect(self.end_downtime)
        h_layout.addWidget(self.btn_end)

        self.layout.addWidget(self.header)

        # Active Summary
        self.summary_layout = QHBoxLayout()
        self.layout.addLayout(self.summary_layout)

        # Table
        cols = [
            ColumnConfig("equipment", "Ekipman", width=200, stretch=True),
            ColumnConfig("start", "Başlangıç", width=150),
            ColumnConfig("end", "Bitiş", width=150),
            ColumnConfig("duration", "Süre", width=100),
            ColumnConfig("reason", "Sebep", width=150),
            ColumnConfig("wo", "İş Emri", width=120),
            ColumnConfig("status", "Durum", width=120),
        ]
        self.table = EnhancedTableWidget(
            table_id="maint_downtime", columns=cols, parent=self
        )
        self.layout.addWidget(self.table)
        self.refresh_data()

    def refresh_data(self):
        f = self.cmb_filter.currentData()
        if f == "active":
            d = self.service.get_active_downtimes()
        elif f == "today":
            d = self.service.get_today_downtimes()
        elif f == "week":
            d = self.service.get_week_downtimes()
        else:
            d = self.service.get_all_downtimes()
        self._refresh_summary()
        self._populate_table(d)

    def _refresh_summary(self):
        while self.summary_layout.count():
            w = self.summary_layout.takeAt(0).widget()
            if w:
                w.deleteLater()
        actives = self.service.get_active_downtimes()
        if not actives:
            lbl = QLabel("Aktif duruş yok")
            lbl.setStyleSheet("color: #10b981; font-weight: bold; padding: 10px;")
            self.summary_layout.addWidget(lbl)
        else:
            for dt in actives[:4]:
                dur = datetime.now() - dt.start_time
                txt = f"{int(dur.total_seconds() // 3600)}s {int((dur.total_seconds() % 3600) // 60)}dk"
                card = MiniStatCard(
                    dt.equipment.code if dt.equipment else "??",
                    txt,
                    "error",
                    icon=ICONS.TIME,
                )
                self.summary_layout.addWidget(card)
            if len(actives) > 4:
                self.summary_layout.addWidget(QLabel(f"+{len(actives)-4} daha"))
        self.summary_layout.addStretch()

    def _populate_table(self, items):
        self.table.setRowCount(len(items))
        vcols = self.table.get_visible_columns()
        for i, dt in enumerate(items):
            for c, key in enumerate(vcols):
                if key == "equipment":
                    it = QTableWidgetItem(dt.equipment.name if dt.equipment else "-")
                    it.setData(Qt.ItemDataRole.UserRole, dt.id)
                    self.table.setItem(i, c, it)
                elif key == "start":
                    self.table.setItem(
                        i, c, QTableWidgetItem(dt.start_time.strftime("%d.%m.%Y %H:%M"))
                    )
                elif key == "end":
                    self.table.setItem(
                        i,
                        c,
                        QTableWidgetItem(
                            dt.end_time.strftime("%d.%m.%Y %H:%M")
                            if dt.end_time
                            else "-"
                        ),
                    )
                elif key == "duration":
                    dur = (dt.end_time or datetime.now()) - dt.start_time
                    val = f"{int(dur.total_seconds()//3600)}s {int((dur.total_seconds()%3600)//60)}dk"
                    it = QTableWidgetItem(val)
                    if not dt.end_time:
                        it.setForeground(Qt.GlobalColor.red)
                    self.table.setItem(i, c, it)
                elif key == "reason":
                    r_map = {
                        "breakdown": "Arıza",
                        "maintenance": "Bakım",
                        "setup": "Ayar",
                        "no_material": "Eksik Malzeme",
                        "no_operator": "Operatör Yok",
                        "quality_issue": "Kalite",
                        "other": "Diğer",
                    }
                    self.table.setItem(
                        i, c, QTableWidgetItem(r_map.get(dt.reason, dt.reason or "-"))
                    )
                elif key == "wo":
                    self.table.setItem(
                        i,
                        c,
                        QTableWidgetItem(
                            dt.work_order.order_no if dt.work_order else "-"
                        ),
                    )
                elif key == "status":
                    it = QTableWidgetItem(
                        "Devam Ediyor" if not dt.end_time else "Tamamlandı"
                    )
                    it.setForeground(
                        Qt.GlobalColor.red
                        if not dt.end_time
                        else Qt.GlobalColor.darkGreen
                    )
                    self.table.setItem(i, c, it)

    def update_active_downtimes(self):
        if self.cmb_filter.currentData() == "active":
            self._refresh_summary()
            self.refresh_data()

    def get_selected_downtime_id(self) -> Optional[int]:
        row = self.table.currentRow()
        return (
            self.table.item(row, 0).data(Qt.ItemDataRole.UserRole) if row >= 0 else None
        )

    def start_downtime(self):
        if DowntimeStartDialog(self.service, self).exec():
            self.refresh_data()

    def end_downtime(self):
        did = self.get_selected_downtime_id()
        if not did:
            return
        dt = self.service.get_downtime_by_id(did)
        if dt.end_time:
            return
        if (
            QMessageBox.question(
                self,
                "Onay",
                "Duruşu sonlandırılsın mı?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        ):
            try:
                self.service.end_downtime(did)
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))

    def closeEvent(self, e):
        self.timer.stop()
        super().closeEvent(e)


class DowntimeStartDialog(QDialog):
    """Duruş Başlatma Dialogu"""

    def __init__(self, service, parent=None):
        super().__init__(parent)
        self.service = service
        self.setWindowTitle("Duruş Başlat")
        self.setMinimumSize(400, 350)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.cmb_eq = QComboBox()
        for eq in self.service.get_equipment_list(active_only=True):
            self.cmb_eq.addItem(f"{eq.code} - {eq.name}", eq.id)
        form.addRow("Ekipman*:", self.cmb_eq)

        self.cmb_reason = QComboBox()
        reasons = [
            ("breakdown", "Arıza"),
            ("maintenance", "Bakım"),
            ("setup", "Ayar"),
            ("no_material", "Eksik Malzeme"),
            ("no_operator", "Operatör Yok"),
            ("quality_issue", "Kalite Sorunu"),
            ("other", "Diğer"),
        ]
        for c, l in reasons:
            self.cmb_reason.addItem(l, c)
        form.addRow("Sebep*:", self.cmb_reason)

        self.dt_start = QDateTimeEdit()
        self.dt_start.setCalendarPopup(True)
        self.dt_start.setDateTime(QDateTime.currentDateTime())
        form.addRow("Başlangıç:", self.dt_start)

        self.cmb_wo = QComboBox()
        self.cmb_wo.addItem("- İş Emri Yok -", None)
        for wo in self.service.get_active_work_orders():
            self.cmb_wo.addItem(
                f"{wo.order_no} - {wo.equipment.name if wo.equipment else ''}", wo.id
            )
        form.addRow("Bağlı İş Emri:", self.cmb_wo)

        self.txt_notes = QTextEdit()
        self.txt_notes.setMaximumHeight(80)
        self.txt_notes.setPlaceholderText("Ek notlar...")
        form.addRow("Notlar:", self.txt_notes)
        layout.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def accept(self):
        eid = self.cmb_eq.currentData()
        if not eid:
            return
        try:
            self.service.start_downtime(
                equipment_id=eid,
                reason=self.cmb_reason.currentData(),
                start_time=self.dt_start.dateTime().toPyDateTime(),
                work_order_id=self.cmb_wo.currentData(),
                notes=self.txt_notes.toPlainText().strip() or None,
            )
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
