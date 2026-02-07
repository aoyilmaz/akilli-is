"""
Akıllı İş - Uygunsuzluk (NCR) Modülü
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
    QLineEdit,
    QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import qtawesome as qta

from config.icons import ICONS
from config.styles import COLORS
from ui.components.base_list_page import BaseListPage
from ui.components.enhanced_table import ColumnConfig
from modules.quality.services import QualityService
from database.models.quality import NCRSeverity, NCRStatus

SEVERITY_LABELS = {
    NCRSeverity.MINOR: "Küçük",
    NCRSeverity.MAJOR: "Büyük",
    NCRSeverity.CRITICAL: "Kritik",
}

SEVERITY_COLORS = {
    NCRSeverity.MINOR: COLORS["info"],
    NCRSeverity.MAJOR: COLORS["warning"],
    NCRSeverity.CRITICAL: COLORS["error"],
}

STATUS_LABELS = {
    NCRStatus.OPEN: "Açık",
    NCRStatus.ANALYSIS: "Analiz",
    NCRStatus.ACTION: "Aksiyon",
    NCRStatus.VERIFICATION: "Doğrulama",
    NCRStatus.CLOSED: "Kapalı",
}


class NCRFormDialog(QDialog):
    """Yeni NCR dialogu"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = QualityService()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Yeni Uygunsuzluk Kaydı (NCR)")
        self.setMinimumSize(500, 450)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        form_frame = QFrame()
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(0, 0, 0, 0)

        self.severity = QComboBox()
        for s, label in SEVERITY_LABELS.items():
            self.severity.addItem(label, s)
        form_layout.addRow("Şiddet Derecesi:", self.severity)

        self.description = QTextEdit()
        self.description.setPlaceholderText("Uygunsuzluk detayları...")
        self.description.setMaximumHeight(100)
        form_layout.addRow("Açıklama:", self.description)

        self.root_cause = QTextEdit()
        self.root_cause.setPlaceholderText("Tespit edilen kök neden (isteğe bağlı)...")
        self.root_cause.setMaximumHeight(100)
        form_layout.addRow("Kök Neden:", self.root_cause)

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
            QComboBox, QTextEdit {{
                padding: 8px;
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
            }}
        """
        )

    def save(self):
        desc_text = self.description.toPlainText().strip()
        if not desc_text:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir açıklama giriniz.")
            return

        try:
            data = {
                "severity": self.severity.currentData(),
                "description": desc_text,
                "root_cause": self.root_cause.toPlainText().strip() or None,
            }
            self.service.create_ncr(data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def closeEvent(self, event):
        self.service.close()
        super().closeEvent(event)


class NCRModule(BaseListPage):
    """NCR yönetim modülü"""

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("ncr_no", "NCR No", width=120, filterable=True),
            ColumnConfig("severity", "Şiddet", width=100, filter_type="enum"),
            ColumnConfig(
                "description", "Açıklama", width=300, stretch=True, filterable=True
            ),
            ColumnConfig("status", "Durum", width=120, filter_type="enum"),
            ColumnConfig("created_at", "Tarih", width=120, filterable=True),
        ]

        super().__init__(
            title="Uygunsuzluklar (NCR)",
            icon=ICONS.WARNING,
            table_id="quality_ncr_list",
            columns=columns,
            add_text="Yeni NCR",
            show_export=True,
            parent=parent,
        )

        self.service = None
        self._setup_additional_ui()
        self.load_data()

    def _setup_additional_ui(self):
        self.footer.add_stat("open", "Açık", ICONS.INFO, COLORS["error"])
        self.footer.add_stat("analysis", "Analizde", ICONS.CHART, COLORS["warning"])
        self.footer.add_stat("closed", "Kapalı", ICONS.SUCCESS, COLORS["success"])

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
            ncrs = service.get_all_ncrs()

            self.table.setRowCount(len(ncrs))
            self.update_count(len(ncrs))

            stats = {"open": 0, "analysis": 0, "closed": 0}

            for row, ncr in enumerate(ncrs):
                # NCR No
                item_no = QTableWidgetItem(ncr.ncr_no)
                item_no.setData(Qt.ItemDataRole.UserRole, ncr.id)
                self.table.setItem(row, 0, item_no)

                # Şiddet
                sev_text = SEVERITY_LABELS.get(ncr.severity, str(ncr.severity))
                sev_item = QTableWidgetItem(sev_text)
                sev_item.setForeground(
                    QColor(SEVERITY_COLORS.get(ncr.severity, COLORS["text_primary"]))
                )
                self.table.setItem(row, 1, sev_item)

                # Açıklama
                desc_text = ncr.description
                if len(desc_text) > 100:
                    desc_text = desc_text[:97] + "..."
                self.table.setItem(row, 2, QTableWidgetItem(desc_text))

                # Durum
                status_text = STATUS_LABELS.get(ncr.status, str(ncr.status))
                status_item = QTableWidgetItem(status_text)
                if ncr.status == NCRStatus.CLOSED:
                    status_item.setForeground(QColor(COLORS["success"]))
                elif ncr.status == NCRStatus.OPEN:
                    status_item.setForeground(QColor(COLORS["error"]))
                self.table.setItem(row, 3, status_item)

                # Tarih
                date_str = (
                    ncr.created_at.strftime("%d.%m.%Y") if ncr.created_at else "-"
                )
                self.table.setItem(row, 4, QTableWidgetItem(date_str))

                # Stats
                if ncr.status == NCRStatus.OPEN:
                    stats["open"] += 1
                elif ncr.status == NCRStatus.CLOSED:
                    stats["closed"] += 1
                else:
                    stats["analysis"] += 1

            for key, val in stats.items():
                self.update_stat_card(key, str(val))

        except Exception as e:
            self.show_error("Veri Yükleme Hatası", str(e))
        finally:
            self._close_service()

    def _on_add(self):
        dialog = NCRFormDialog(parent=self)
        if dialog.exec():
            self.load_data()
