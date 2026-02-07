"""
Akıllı İş - Kontrol Şablonu Modülü
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
from database.models.quality import InspectionType

TYPE_LABELS = {
    InspectionType.INCOMING: "Giriş Kontrolü",
    InspectionType.IN_PROCESS: "Proses Kontrolü",
    InspectionType.FINAL: "Final Kontrol",
    InspectionType.PERIODIC: "Periyodik Kontrol",
}


class TemplateFormDialog(QDialog):
    """Yeni şablon dialogu"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = QualityService()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Yeni Kontrol Şablonu")
        self.setMinimumSize(450, 400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        form_frame = QFrame()
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(0, 0, 0, 0)

        self.code = QLineEdit()
        self.code.setPlaceholderText("Şablon kodu (örn: INSP-001)...")
        form_layout.addRow("Kod:", self.code)

        self.name = QLineEdit()
        self.name.setPlaceholderText("Şablon adı...")
        form_layout.addRow("Ad:", self.name)

        self.inspection_type = QComboBox()
        for t, label in TYPE_LABELS.items():
            self.inspection_type.addItem(label, t)
        form_layout.addRow("Kontrol Türü:", self.inspection_type)

        self.description = QTextEdit()
        self.description.setPlaceholderText("Şablon açıklaması...")
        self.description.setMaximumHeight(80)
        form_layout.addRow("Açıklama:", self.description)

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
        code = self.code.text().strip()
        name = self.name.text().strip()
        if not code or not name:
            QMessageBox.warning(self, "Uyarı", "Kod ve Ad alanları zorunludur.")
            return

        try:
            data = {
                "code": code,
                "name": name,
                "inspection_type": self.inspection_type.currentData(),
                "description": self.description.toPlainText().strip() or None,
            }
            self.service.create_template(data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def closeEvent(self, event):
        self.service.close()
        super().closeEvent(event)


class TemplateModule(BaseListPage):
    """Kontrol şablonu modülü"""

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("code", "Kod", width=120, filterable=True),
            ColumnConfig("name", "Ad", width=200, stretch=True, filterable=True),
            ColumnConfig("inspection_type", "Tür", width=150, filter_type="enum"),
            ColumnConfig("description", "Açıklama", width=300, filterable=True),
        ]

        super().__init__(
            title="Kontrol Şablonları",
            icon=ICONS.GRID,
            table_id="quality_template_list",
            columns=columns,
            add_text="Yeni Şablon",
            show_export=True,
            parent=parent,
        )

        self.service = None
        self._setup_additional_ui()
        self.load_data()

    def _setup_additional_ui(self):
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
            templates = service.get_all_templates()

            self.table.setRowCount(len(templates))
            self.update_count(len(templates))

            for row, t in enumerate(templates):
                # Kod
                item_code = QTableWidgetItem(t.code)
                item_code.setData(Qt.ItemDataRole.UserRole, t.id)
                self.table.setItem(row, 0, item_code)

                # Ad
                self.table.setItem(row, 1, QTableWidgetItem(t.name))

                # Tür
                type_text = TYPE_LABELS.get(t.inspection_type, str(t.inspection_type))
                self.table.setItem(row, 2, QTableWidgetItem(type_text))

                # Açıklama
                self.table.setItem(row, 3, QTableWidgetItem(t.description or "-"))

        except Exception as e:
            self.show_error("Veri Yükleme Hatası", str(e))
        finally:
            self._close_service()

    def _on_add(self):
        dialog = TemplateFormDialog(parent=self)
        if dialog.exec():
            self.load_data()
