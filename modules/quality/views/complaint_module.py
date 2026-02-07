"""
Akıllı İş - Müşteri Şikayeti Modülü
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
    QTextEdit,
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
from database.models.quality import (
    ComplaintCategory,
    ComplaintPriority,
    ComplaintStatus,
)

CATEGORY_LABELS = {
    ComplaintCategory.QUALITY: "Kalite",
    ComplaintCategory.DELIVERY: "Teslimat",
    ComplaintCategory.SERVICE: "Servis",
    ComplaintCategory.DOCUMENTATION: "Dokümantasyon",
    ComplaintCategory.OTHER: "Diğer",
}

PRIORITY_LABELS = {
    ComplaintPriority.LOW: "Düşük",
    ComplaintPriority.MEDIUM: "Orta",
    ComplaintPriority.HIGH: "Yüksek",
    ComplaintPriority.CRITICAL: "Kritik",
}

PRIORITY_COLORS = {
    ComplaintPriority.LOW: COLORS["info"],
    ComplaintPriority.MEDIUM: COLORS["text_secondary"],
    ComplaintPriority.HIGH: COLORS["warning"],
    ComplaintPriority.CRITICAL: COLORS["error"],
}

STATUS_LABELS = {
    ComplaintStatus.OPEN: "Açık",
    ComplaintStatus.INVESTIGATION: "İnceleme",
    ComplaintStatus.RESOLUTION: "Çözüm",
    ComplaintStatus.CLOSED: "Kapalı",
}


class ComplaintFormDialog(QDialog):
    """Yeni şikayet dialogu"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = QualityService()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Yeni Müşteri Şikayeti")
        self.setMinimumSize(500, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        form_frame = QFrame()
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(0, 0, 0, 0)

        self.category = QComboBox()
        for c, label in CATEGORY_LABELS.items():
            self.category.addItem(label, c)
        form_layout.addRow("Kategori:", self.category)

        self.priority = QComboBox()
        for p, label in PRIORITY_LABELS.items():
            self.priority.addItem(label, p)
        self.priority.setCurrentIndex(1)  # Orta
        form_layout.addRow("Öncelik:", self.priority)

        self.product_info = QLineEdit()
        self.product_info.setPlaceholderText("Ürün kodu/adı...")
        form_layout.addRow("Ürün Bilgisi:", self.product_info)

        self.lot_no = QLineEdit()
        self.lot_no.setPlaceholderText("Parti/Lot numarası...")
        form_layout.addRow("Parti No:", self.lot_no)

        self.description = QTextEdit()
        self.description.setPlaceholderText("Şikayet detayları...")
        self.description.setMaximumHeight(100)
        form_layout.addRow("Şikayet Açıklaması:", self.description)

        self.immediate_action = QTextEdit()
        self.immediate_action.setPlaceholderText("Alınan ilk aksiyon...")
        self.immediate_action.setMaximumHeight(80)
        form_layout.addRow("Acil Aksiyon:", self.immediate_action)

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
            QLineEdit, QComboBox, QTextEdit {{
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
            QMessageBox.warning(self, "Uyarı", "Şikayet açıklaması zorunludur.")
            return

        try:
            data = {
                "category": self.category.currentData(),
                "priority": self.priority.currentData(),
                "product_info": self.product_info.text().strip() or None,
                "lot_no": self.lot_no.text().strip() or None,
                "description": desc,
                "immediate_action": self.immediate_action.toPlainText().strip() or None,
            }
            self.service.create_complaint(data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def closeEvent(self, event):
        self.service.close()
        super().closeEvent(event)


class ComplaintModule(BaseListPage):
    """Müşteri şikayetleri modülü"""

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("complaint_no", "Şikayet No", width=120, filterable=True),
            ColumnConfig("category", "Kategori", width=120, filter_type="enum"),
            ColumnConfig("priority", "Öncelik", width=100, filter_type="enum"),
            ColumnConfig(
                "description", "Açıklama", width=300, stretch=True, filterable=True
            ),
            ColumnConfig("status", "Durum", width=120, filter_type="enum"),
            ColumnConfig("complaint_date", "Tarih", width=120, filterable=True),
        ]

        super().__init__(
            title="Müşteri Şikayetleri",
            icon=ICONS.CUSTOMER,
            table_id="quality_complaint_list",
            columns=columns,
            add_text="Yeni Şikayet",
            show_export=True,
            parent=parent,
        )

        self.service = None
        self._setup_additional_ui()
        self.load_data()

    def _setup_additional_ui(self):
        self.footer.add_stat("open", "Açık", ICONS.INFO, COLORS["error"])
        self.footer.add_stat(
            "investigation", "İncelemede", ICONS.CHART, COLORS["warning"]
        )
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
            complaints = service.get_all_complaints()

            self.table.setRowCount(len(complaints))
            self.update_count(len(complaints))

            stats = {"open": 0, "investigation": 0, "closed": 0}

            for row, c in enumerate(complaints):
                # Şikayet No
                item_no = QTableWidgetItem(c.complaint_no)
                item_no.setData(Qt.ItemDataRole.UserRole, c.id)
                self.table.setItem(row, 0, item_no)

                # Kategori
                self.table.setItem(
                    row, 1, QTableWidgetItem(CATEGORY_LABELS.get(c.category, "-"))
                )

                # Öncelik
                pri_text = PRIORITY_LABELS.get(c.priority, str(c.priority))
                pri_item = QTableWidgetItem(pri_text)
                pri_item.setForeground(
                    QColor(PRIORITY_COLORS.get(c.priority, COLORS["text_primary"]))
                )
                self.table.setItem(row, 2, pri_item)

                # Açıklama
                desc_text = c.description
                if len(desc_text) > 80:
                    desc_text = desc_text[:77] + "..."
                self.table.setItem(row, 3, QTableWidgetItem(desc_text))

                # Durum
                status_text = STATUS_LABELS.get(c.status, str(c.status))
                status_item = QTableWidgetItem(status_text)
                if c.status == ComplaintStatus.CLOSED:
                    status_item.setForeground(QColor(COLORS["success"]))
                elif c.status == ComplaintStatus.OPEN:
                    status_item.setForeground(QColor(COLORS["error"]))
                self.table.setItem(row, 4, status_item)

                # Tarih
                date_str = (
                    c.complaint_date.strftime("%d.%m.%Y") if c.complaint_date else "-"
                )
                self.table.setItem(row, 5, QTableWidgetItem(date_str))

                # Stats
                if c.status == ComplaintStatus.OPEN:
                    stats["open"] += 1
                elif c.status == ComplaintStatus.CLOSED:
                    stats["closed"] += 1
                elif c.status == ComplaintStatus.INVESTIGATION:
                    stats["investigation"] += 1

            for key, val in stats.items():
                self.update_stat_card(key, str(val))

        except Exception as e:
            self.show_error("Veri Yükleme Hatası", str(e))
        finally:
            self._close_service()

    def _on_add(self):
        dialog = ComplaintFormDialog(parent=self)
        if dialog.exec():
            self.load_data()
