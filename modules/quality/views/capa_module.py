"""
Akıllı İş - Düzeltici Önleyici Faaliyetler (CAPA) Modülü
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
    QTextEdit,
    QDateEdit,
    QLineEdit,
    QFrame,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
import qtawesome as qta

from config.icons import ICONS
from config.styles import COLORS
from ui.components.base_list_page import BaseListPage
from ui.components.enhanced_table import ColumnConfig
from modules.quality.services import QualityService
from database.models.quality import CAPAType, CAPASource, CAPAStatus

TYPE_LABELS = {
    CAPAType.CORRECTIVE: "Düzeltici",
    CAPAType.PREVENTIVE: "Önleyici",
}

SOURCE_LABELS = {
    CAPASource.NCR: "NCR",
    CAPASource.AUDIT: "Denetim",
    CAPASource.CUSTOMER_COMPLAINT: "Müşteri Şikayeti",
    CAPASource.INTERNAL: "İç Kaynak",
}

STATUS_LABELS = {
    CAPAStatus.OPEN: "Açık",
    CAPAStatus.IN_PROGRESS: "Devam Ediyor",
    CAPAStatus.VERIFICATION: "Doğrulama",
    CAPAStatus.CLOSED: "Kapalı",
}


class CAPAFormDialog(QDialog):
    """Yeni CAPA dialogu"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = QualityService()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Yeni CAPA Kaydı")
        self.setMinimumSize(500, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        form_frame = QFrame()
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(0, 0, 0, 0)

        self.capa_type = QComboBox()
        for t, label in TYPE_LABELS.items():
            self.capa_type.addItem(label, t)
        form_layout.addRow("CAPA Türü:", self.capa_type)

        self.source = QComboBox()
        for s, label in SOURCE_LABELS.items():
            self.source.addItem(label, s)
        self.source.setCurrentIndex(3)  # İç Kaynak
        form_layout.addRow("Kaynak:", self.source)

        self.description = QTextEdit()
        self.description.setPlaceholderText("Faaliyet gerektiren durum açıklaması...")
        self.description.setMaximumHeight(100)
        form_layout.addRow("Açıklama:", self.description)

        self.action_plan = QTextEdit()
        self.action_plan.setPlaceholderText("Planlanan aksiyonlar...")
        self.action_plan.setMaximumHeight(80)
        form_layout.addRow("Aksiyon Planı:", self.action_plan)

        self.target_date = QDateEdit()
        self.target_date.setCalendarPopup(True)
        self.target_date.setDate(QDate.currentDate().addDays(30))
        form_layout.addRow("Hedef Tarih:", self.target_date)

        layout.addWidget(form_frame)

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

        self.setStyleSheet(
            f"""
            QDialog {{ background-color: {COLORS['bg_primary']}; }}
            QLabel {{ color: {COLORS['text_secondary']}; font-weight: 500; }}
            QComboBox, QTextEdit, QDateEdit {{
                padding: 8px;
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
            }}
        """
        )

    def save(self):
        desc = self.description.toPlainText().strip()
        if not desc:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir açıklama giriniz.")
            return

        try:
            data = {
                "capa_type": self.capa_type.currentData(),
                "source": self.source.currentData(),
                "description": desc,
                "action_plan": self.action_plan.toPlainText().strip() or None,
                "target_date": self.target_date.date().toPyDate(),
            }
            self.service.create_capa(data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def closeEvent(self, event):
        self.service.close()
        super().closeEvent(event)


class CAPAModule(BaseListPage):
    """CAPA yönetim modülü"""

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("capa_no", "CAPA No", width=120, filterable=True),
            ColumnConfig("capa_type", "Tür", width=100, filter_type="enum"),
            ColumnConfig("source", "Kaynak", width=120, filter_type="enum"),
            ColumnConfig(
                "description", "Açıklama", width=300, stretch=True, filterable=True
            ),
            ColumnConfig("target_date", "Hedef Tarih", width=120, filterable=True),
            ColumnConfig("status", "Durum", width=120, filter_type="enum"),
        ]

        super().__init__(
            title="Düzeltici Önleyici Faaliyetler (CAPA)",
            icon=ICONS.PLANNING,
            table_id="quality_capa_list",
            columns=columns,
            add_text="Yeni CAPA",
            show_export=True,
            parent=parent,
        )

        self.service = None
        self._setup_additional_ui()
        self.load_data()

    def _setup_additional_ui(self):
        self.footer.add_stat("open", "Açık", ICONS.INFO, COLORS["error"])
        self.footer.add_stat("in_progress", "Devam Eden", ICONS.TIME, COLORS["warning"])
        self.footer.add_stat("closed", "Tamamlanan", ICONS.SUCCESS, COLORS["success"])

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
            capas = service.get_all_capas()

            self.table.setRowCount(len(capas))
            self.update_count(len(capas))

            stats = {"open": 0, "in_progress": 0, "closed": 0}

            for row, capa in enumerate(capas):
                # CAPA No
                item_no = QTableWidgetItem(capa.capa_no)
                item_no.setData(Qt.ItemDataRole.UserRole, capa.id)
                self.table.setItem(row, 0, item_no)

                # Tür
                self.table.setItem(
                    row,
                    1,
                    QTableWidgetItem(
                        TYPE_LABELS.get(capa.capa_type, str(capa.capa_type))
                    ),
                )

                # Kaynak
                self.table.setItem(
                    row,
                    2,
                    QTableWidgetItem(SOURCE_LABELS.get(capa.source, str(capa.source))),
                )

                # Açıklama
                desc_text = capa.description
                if len(desc_text) > 80:
                    desc_text = desc_text[:77] + "..."
                self.table.setItem(row, 3, QTableWidgetItem(desc_text))

                # Hedef Tarih
                date_str = (
                    capa.target_date.strftime("%d.%m.%Y") if capa.target_date else "-"
                )
                self.table.setItem(row, 4, QTableWidgetItem(date_str))

                # Durum
                status_text = STATUS_LABELS.get(capa.status, str(capa.status))
                status_item = QTableWidgetItem(status_text)
                if capa.status == CAPAStatus.CLOSED:
                    status_item.setForeground(QColor(COLORS["success"]))
                elif capa.status == CAPAStatus.OPEN:
                    status_item.setForeground(QColor(COLORS["error"]))
                elif capa.status == CAPAStatus.IN_PROGRESS:
                    status_item.setForeground(QColor(COLORS["warning"]))
                self.table.setItem(row, 5, status_item)

                # Stats
                if capa.status == CAPAStatus.OPEN:
                    stats["open"] += 1
                elif capa.status == CAPAStatus.CLOSED:
                    stats["closed"] += 1
                elif capa.status == CAPAStatus.IN_PROGRESS:
                    stats["in_progress"] += 1

            for key, val in stats.items():
                self.update_stat_card(key, str(val))

        except Exception as e:
            self.show_error("Veri Yükleme Hatası", str(e))
        finally:
            self._close_service()

    def _on_add(self):
        dialog = CAPAFormDialog(parent=self)
        if dialog.exec():
            self.load_data()
