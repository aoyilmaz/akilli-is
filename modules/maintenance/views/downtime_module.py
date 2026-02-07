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
from ui.components.base_list_page import BaseListPage
from ui.components.page_header import PageHeader
from ui.components.stat_cards import MiniStatCard
from ui.components.enhanced_table import ColumnConfig
from database.base import get_session
from modules.maintenance.services import MaintenanceService


class DowntimeTrackerWidget(BaseListPage):
    """Duruş Takibi Widget'ı"""

    def __init__(self, parent=None):
        self.db_session = get_session()
        self.service = MaintenanceService(self.db_session)

        columns = [
            ColumnConfig(
                "equipment", "Ekipman", width=200, filterable=True, stretch=True
            ),
            ColumnConfig("start", "Başlangıç", width=150),
            ColumnConfig("end", "Bitiş", width=150),
            ColumnConfig("duration", "Süre", width=100),
            ColumnConfig("reason", "Sebep", width=150, filterable=True),
            ColumnConfig("wo", "İş Emri", width=120, filterable=True),
            ColumnConfig("status", "Durum", width=120, filterable=True),
        ]

        super().__init__(
            title="Duruş Takibi",
            icon=ICONS.TIME,
            table_id="maintenance_downtime",
            columns=columns,
            show_add=True,
            add_text="Duruş Başlat",
            parent=parent,
        )

        self._setup_extra_ui()
        self.add_clicked.connect(self.start_downtime)
        self.refresh_requested.connect(self.refresh_data)

        # Override auto-refresh timer to update active downtimes if filter is set
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_active_downtimes)
        self.timer.start(60000)

    def closeEvent(self, e):
        self.timer.stop()
        if hasattr(self, "db_session") and self.db_session:
            self.db_session.close()
        super().closeEvent(e)

    def _setup_extra_ui(self):
        # Inject custom stats summary into header layout or above table
        # BaseListPage adds header then table. We can insert a layout between them or adding to layout.
        # But layout is not directly accessible easily if we want to INSERT.
        # Luckily BaseListPage uses a QVBoxLayout (self.layout()).

        # We'll add the stats layout right after the header (index 1)
        self.summary_widget = QWidget()
        self.summary_layout = QHBoxLayout(self.summary_widget)
        self.summary_layout.setContentsMargins(0, 0, 0, 0)
        self.layout().insertWidget(1, self.summary_widget)

        h_layout = self.header.header_layout()
        h_layout.addSpacing(16)
        h_layout.addWidget(QLabel("Göster:"))
        self.cmb_filter = QComboBox()
        self.cmb_filter.addItems(["Aktif Duruşlar", "Bugün", "Bu Hafta", "Tümü"])
        self.cmb_filter.setItemData(0, "active")
        self.cmb_filter.setItemData(1, "today")
        self.cmb_filter.setItemData(2, "week")
        self.cmb_filter.setItemData(3, "all")
        self.cmb_filter.setFixedHeight(32)
        self.cmb_filter.currentIndexChanged.connect(self.refresh_data)
        h_layout.addWidget(self.cmb_filter)
        h_layout.addStretch()

        self.btn_end = QPushButton("Duruşu Bitir")
        self.btn_end.setIcon(qta.icon(ICONS.CHECK, color="#ffffff"))
        self.btn_end.setProperty("class", "btn-success")
        self.btn_end.setFixedHeight(32)
        self.btn_end.clicked.connect(self.end_downtime)
        h_layout.addWidget(self.btn_end)

        # Filters options for table
        self.table.set_filter_options("status", ["Devam Ediyor", "Tamamlandı"])
        self.table.set_filter_options(
            "reason",
            [
                "Arıza",
                "Bakım",
                "Ayar",
                "Eksik Malzeme",
                "Operatör Yok",
                "Kalite",
                "Diğer",
            ],
        )

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
        self.load_data(d)

    def _refresh_summary(self):
        while self.summary_layout.count():
            w = self.summary_layout.takeAt(0).widget()
            if w:
                w.deleteLater()

        actives = self.service.get_active_downtimes()
        if not actives:
            # Optional: Hide widget if empty or show "No Active Downtime"
            pass
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
                lbl = QLabel(f"+{len(actives)-4} daha")
                lbl.setStyleSheet("font-weight: bold; color: #6b7280;")
                self.summary_layout.addWidget(lbl)
        self.summary_layout.addStretch()

    def load_data(self, items):
        self.table.setRowCount(len(items))

        for i, dt in enumerate(items):
            # Equipment
            it = QTableWidgetItem(dt.equipment.name if dt.equipment else "-")
            it.setData(Qt.ItemDataRole.UserRole, dt.id)
            self.table.setItem(i, 0, it)

            # Start
            self.table.setItem(
                i, 1, QTableWidgetItem(dt.start_time.strftime("%d.%m.%Y %H:%M"))
            )

            # End
            self.table.setItem(
                i,
                2,
                QTableWidgetItem(
                    dt.end_time.strftime("%d.%m.%Y %H:%M") if dt.end_time else "-"
                ),
            )

            # Duration
            dur = (dt.end_time or datetime.now()) - dt.start_time
            val = f"{int(dur.total_seconds()//3600)}s {int((dur.total_seconds()%3600)//60)}dk"
            it = QTableWidgetItem(val)
            if not dt.end_time:
                it.setForeground(Qt.GlobalColor.red)
            self.table.setItem(i, 3, it)

            # Reason
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
                i, 4, QTableWidgetItem(r_map.get(dt.reason, dt.reason or "-"))
            )

            # Work Order
            self.table.setItem(
                i,
                5,
                QTableWidgetItem(dt.work_order.order_no if dt.work_order else "-"),
            )

            # Status
            it = QTableWidgetItem("Devam Ediyor" if not dt.end_time else "Tamamlandı")
            it.setForeground(
                Qt.GlobalColor.red if not dt.end_time else Qt.GlobalColor.darkGreen
            )
            self.table.setItem(i, 6, it)

        self.update_count(len(items))

    def update_active_downtimes(self):
        if self.cmb_filter.currentData() == "active":
            self.refresh_data()
        else:
            self._refresh_summary()

    def get_selected_downtime_id(self) -> Optional[int]:
        return self.table.get_selected_id()

    def start_downtime(self):
        if DowntimeStartDialog(self.service, self).exec():
            self.refresh_data()

    def end_downtime(self):
        did = self.get_selected_downtime_id()
        if not did:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir duruş seçin.")
            return
        dt = self.service.get_downtime_by_id(did)
        if dt.end_time:
            QMessageBox.information(self, "Bilgi", "Bu duruş zaten sonlandırılmış.")
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

    # Interface Implementation
    def get_search_text(self) -> str:
        return self.header.get_search_text()


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
            QMessageBox.warning(self, "Uyarı", "Lütfen bir ekipman seçin.")
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
