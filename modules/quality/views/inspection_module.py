"""
Akıllı İş - Kalite Kontrol Modülü
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QComboBox,
    QMessageBox,
    QLabel,
    QDialog,
    QFormLayout,
    QLineEdit,
    QDateEdit,
    QTextEdit,
    QFrame,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
import qtawesome as qta

from config.icons import ICONS
from config.styles import COLORS
from ui.components.base_list_page import BaseListPage
from ui.components.enhanced_table import ColumnConfig, NumericTableWidgetItem
from modules.quality.services import QualityService
from database.models.quality import InspectionStatus

STATUS_LABELS = {
    InspectionStatus.PENDING: "Beklemede",
    InspectionStatus.PASSED: "Geçti",
    InspectionStatus.FAILED: "Kaldı",
    InspectionStatus.CONDITIONAL: "Şartlı",
}

STATUS_COLORS = {
    InspectionStatus.PENDING: COLORS["info"],
    InspectionStatus.PASSED: COLORS["success"],
    InspectionStatus.FAILED: COLORS["error"],
    InspectionStatus.CONDITIONAL: COLORS["warning"],
}


class InspectionFormDialog(QDialog):
    """Yeni kontrol dialogu"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = QualityService()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Yeni Kalite Kontrol")
        self.setMinimumSize(500, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Form kartı efekti için frame
        form_frame = QFrame()
        form_frame.setObjectName("form_frame")
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.template = QComboBox()
        self.template.setHeight = 35
        self.template.addItem("Şablon Seçiniz...", None)
        for t in self.service.get_all_templates():
            self.template.addItem(f"{t.code} - {t.name}", t.id)
        form_layout.addRow("Kontrol Şablonu:", self.template)

        self.lot_no = QLineEdit()
        self.lot_no.setPlaceholderText("Parti/Lot numarası...")
        form_layout.addRow("Parti No:", self.lot_no)

        self.quantity = QLineEdit()
        self.quantity.setPlaceholderText("0.00")
        form_layout.addRow("Miktar:", self.quantity)

        self.sample_size = QLineEdit()
        self.sample_size.setPlaceholderText("0.00")
        form_layout.addRow("Numune Miktarı:", self.sample_size)

        self.inspection_date = QDateEdit()
        self.inspection_date.setCalendarPopup(True)
        self.inspection_date.setDate(QDate.currentDate())
        form_layout.addRow("Kontrol Tarihi:", self.inspection_date)

        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Ek açıklamalar...")
        self.notes.setMaximumHeight(100)
        form_layout.addRow("Notlar:", self.notes)

        layout.addWidget(form_frame)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.setMinimumSize(100, 35)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Kaydet")
        save_btn.setMinimumSize(100, 35)
        save_btn.setProperty("class", "primary")
        save_btn.setIcon(qta.icon(ICONS.SAVE, color="white"))
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

        # Basit stil
        self.setStyleSheet(
            f"""
            QDialog {{ background-color: {COLORS['bg_primary']}; }}
            QLabel {{ color: {COLORS['text_secondary']}; font-weight: 500; }}
            QLineEdit, QComboBox, QDateEdit, QTextEdit {{
                padding: 8px;
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
            }}
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {{
                border: 1px solid {COLORS['accent']};
            }}
        """
        )

    def save(self):
        try:
            if not self.template.currentData():
                raise ValueError("Lütfen bir kontrol şablonu seçiniz.")

            data = {
                "template_id": self.template.currentData(),
                "lot_no": self.lot_no.text().strip() or None,
                "inspection_date": self.inspection_date.date().toPyDate(),
                "result_summary": self.notes.toPlainText().strip() or None,
            }

            if self.quantity.text().strip():
                data["quantity"] = float(self.quantity.text().replace(",", "."))
            if self.sample_size.text().strip():
                data["sample_size"] = float(self.sample_size.text().replace(",", "."))

            self.service.create_inspection(data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def closeEvent(self, event):
        self.service.close()
        super().closeEvent(event)


class InspectionModule(BaseListPage):
    """Kalite kontrol modülü"""

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("inspection_no", "Kontrol No", width=130, filterable=True),
            ColumnConfig(
                "template", "Şablon", width=200, stretch=True, filterable=True
            ),
            ColumnConfig("lot_no", "Parti No", width=150, filterable=True),
            ColumnConfig("inspection_date", "Tarih", width=120, filterable=True),
            ColumnConfig("quantity", "Miktar", width=100, filterable=True),
            ColumnConfig("status", "Durum", width=120, filter_type="enum"),
        ]

        super().__init__(
            title="Kalite Kontroller",
            icon=ICONS.FLASK,
            table_id="quality_inspection_list",
            columns=columns,
            add_text="Yeni Kontrol",
            show_export=True,
            parent=parent,
        )

        self.service = None
        self._setup_additional_ui()
        self.load_data()

    def _setup_additional_ui(self):
        """Ekstra UI öğeleri (istatistik kartları vb.)"""
        self.footer.add_stat("pending", "Bekleyen", ICONS.TIME, COLORS["info"])
        self.footer.add_stat("passed", "Geçti", ICONS.SUCCESS, COLORS["success"])
        self.footer.add_stat("failed", "Reddedildi", ICONS.ERROR, COLORS["error"])

        # Sinyal bağlantıları
        self.add_clicked.connect(self._on_add)
        self.refresh_requested.connect(self.load_data)

    def _get_service(self):
        if self.service is None:
            self.service = QualityService()
        return self.service

    def _close_service(self):
        if self.service:
            self.service.close()
            self.service = None

    def load_data(self):
        try:
            service = self._get_service()
            inspections = service.get_all_inspections()

            self.table.setRowCount(len(inspections))
            self.update_count(len(inspections))

            stats = {"pending": 0, "passed": 0, "failed": 0}

            for row, ins in enumerate(inspections):
                # Kontrol No
                item_no = QTableWidgetItem(ins.inspection_no)
                item_no.setData(Qt.ItemDataRole.UserRole, ins.id)
                self.table.setItem(row, 0, item_no)

                # Şablon
                self.table.setItem(
                    row, 1, QTableWidgetItem(ins.template.name if ins.template else "-")
                )

                # Parti No
                self.table.setItem(row, 2, QTableWidgetItem(ins.lot_no or "-"))

                # Tarih
                date_str = (
                    ins.inspection_date.strftime("%d.%m.%Y")
                    if ins.inspection_date
                    else "-"
                )
                self.table.setItem(row, 3, QTableWidgetItem(date_str))

                # Miktar
                qty = ins.quantity or 0
                self.table.setItem(row, 4, NumericTableWidgetItem(qty, f"{qty:,.2f}"))

                # Durum
                status_text = STATUS_LABELS.get(ins.status, str(ins.status))
                status_item = QTableWidgetItem(status_text)
                color = STATUS_COLORS.get(ins.status, COLORS["text_primary"])
                status_item.setForeground(QColor(color))
                status_item.setIcon(
                    qta.icon(
                        ICONS.STATUS_ICONS.get(ins.status.value, ICONS.INFO),
                        color=color,
                    )
                )
                self.table.setItem(row, 5, status_item)

                # İstatistikleri güncelle
                if ins.status == InspectionStatus.PENDING:
                    stats["pending"] += 1
                elif ins.status == InspectionStatus.PASSED:
                    stats["passed"] += 1
                elif ins.status == InspectionStatus.FAILED:
                    stats["failed"] += 1

            for key, val in stats.items():
                self.update_stat_card(key, str(val))

        except Exception as e:
            self.show_error("Veri Yükleme Hatası", str(e))
        finally:
            self._close_service()

    def _on_add(self):
        dialog = InspectionFormDialog(parent=self)
        if dialog.exec():
            self.load_data()
