"""
Akıllı İş - Workflow Tanımları Listesi

Admin paneli için workflow tanımlarını listeler ve yönetir.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidgetItem,
    QMessageBox,
    QLabel,
)
from PyQt6.QtCore import Qt, pyqtSignal
import qtawesome as qta

from config.icons import ICONS
from config.styles import Colors
from ui.components.page_header import PageHeader
from ui.components.enhanced_table import EnhancedTableWidget, ColumnConfig


# Hedef tablo etiketleri
TARGET_TABLE_LABELS = {
    "purchase_requests": "Satın Alma Talepleri",
    "purchase_orders": "Satın Alma Siparişleri",
    "sales_orders": "Satış Siparişleri",
    "invoices": "Faturalar",
    "leaves": "İzin Talepleri",
    "work_orders": "İş Emirleri",
}


class WorkflowListPage(QWidget):
    """Workflow tanımları listesi"""

    page_title = "İş Akışı Tanımları"

    # Signals
    edit_requested = pyqtSignal(int)  # workflow_id
    create_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self.header = PageHeader(
            title="İş Akışı Tanımları",
            icon=ICONS.WORKFLOW if hasattr(ICONS, "WORKFLOW") else ICONS.SETTINGS,
            show_search=True,
            show_add=True,
            add_text="Yeni İş Akışı",
            parent=self,
        )
        self.header.add_clicked.connect(self._on_new)
        self.header.refresh_clicked.connect(self.load_data)
        self.header.search_changed.connect(self._on_search)
        layout.addWidget(self.header)

        # Tablo
        cols = [
            ColumnConfig("code", "Kod", width=120),
            ColumnConfig("name", "Ad", stretch=True),
            ColumnConfig("target_table", "Hedef Tablo", width=180),
            ColumnConfig("steps_count", "Adım Sayısı", width=100),
            ColumnConfig("is_default", "Varsayılan", width=100),
            ColumnConfig("is_active", "Aktif", width=80),
            ColumnConfig("actions", "İşlemler", width=150),
        ]
        self.table = EnhancedTableWidget(
            table_id="workflow_definitions",
            columns=cols,
            parent=self,
        )
        self.table.cellDoubleClicked.connect(self._on_row_double_click)
        layout.addWidget(self.table)

    def _get_service(self):
        if self.service is None:
            from modules.workflow.services import WorkflowService
            self.service = WorkflowService()
        return self.service

    def _close_service(self):
        if self.service:
            self.service.close()
            self.service = None

    def load_data(self, search_text: str = None):
        """Verileri yükle"""
        try:
            service = self._get_service()
            definitions = service.list_workflow_definitions()

            # Arama filtresi
            if search_text:
                search_lower = search_text.lower()
                definitions = [
                    d for d in definitions
                    if search_lower in (d.code or "").lower()
                    or search_lower in (d.name or "").lower()
                    or search_lower in (d.target_table or "").lower()
                ]

            self.table.setRowCount(len(definitions))
            vcols = self.table.get_visible_columns()

            for r, wf in enumerate(definitions):
                for c, key in enumerate(vcols):
                    if key == "code":
                        it = QTableWidgetItem(wf.code or "")
                        it.setData(Qt.ItemDataRole.UserRole, wf.id)
                        self.table.setItem(r, c, it)
                    elif key == "name":
                        self.table.setItem(r, c, QTableWidgetItem(wf.name or ""))
                    elif key == "target_table":
                        label = TARGET_TABLE_LABELS.get(wf.target_table, wf.target_table)
                        self.table.setItem(r, c, QTableWidgetItem(label))
                    elif key == "steps_count":
                        count = len(wf.steps) if wf.steps else 0
                        self.table.setItem(r, c, QTableWidgetItem(str(count)))
                    elif key == "is_default":
                        it = QTableWidgetItem("✓" if wf.is_default else "-")
                        if wf.is_default:
                            it.setForeground(Qt.GlobalColor.green)
                        self.table.setItem(r, c, it)
                    elif key == "is_active":
                        it = QTableWidgetItem("Aktif" if wf.is_active else "Pasif")
                        if wf.is_active:
                            it.setForeground(Qt.GlobalColor.green)
                        else:
                            it.setForeground(Qt.GlobalColor.red)
                        self.table.setItem(r, c, it)
                    elif key == "actions":
                        w = QWidget()
                        h_layout = QHBoxLayout(w)
                        h_layout.setContentsMargins(4, 4, 4, 4)
                        h_layout.setSpacing(4)

                        edit_btn = QPushButton("Düzenle")
                        edit_btn.setIcon(qta.icon(ICONS.EDIT, color="#ffffff"))
                        edit_btn.setProperty("class", "btn-primary")
                        edit_btn.setFixedHeight(28)
                        edit_btn.clicked.connect(
                            lambda _, wid=wf.id: self._on_edit(wid)
                        )
                        h_layout.addWidget(edit_btn)

                        del_btn = QPushButton()
                        del_btn.setIcon(qta.icon(ICONS.DELETE, color="#f44336"))
                        del_btn.setFixedSize(28, 28)
                        del_btn.setToolTip("Sil")
                        del_btn.clicked.connect(
                            lambda _, wid=wf.id: self._on_delete(wid)
                        )
                        h_layout.addWidget(del_btn)

                        self.table.setCellWidget(r, c, w)

        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Veri yüklenirken hata: {e}")
        finally:
            self._close_service()

    def _on_search(self, text: str):
        """Arama"""
        self.load_data(search_text=text)

    def _on_new(self):
        """Yeni workflow"""
        self.create_requested.emit()

    def _on_edit(self, workflow_id: int):
        """Düzenle"""
        self.edit_requested.emit(workflow_id)

    def _on_row_double_click(self, row: int, col: int):
        """Satıra çift tıklama"""
        item = self.table.item(row, 0)
        if item:
            workflow_id = item.data(Qt.ItemDataRole.UserRole)
            if workflow_id:
                self.edit_requested.emit(workflow_id)

    def _on_delete(self, workflow_id: int):
        """Sil"""
        reply = QMessageBox.question(
            self,
            "Silme Onayı",
            "Bu iş akışı tanımını silmek istediğinizden emin misiniz?\n\n"
            "Bu işlem geri alınamaz ve bu akışa bağlı tüm adımlar da silinecektir.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                service = self._get_service()
                service.delete_workflow_definition(workflow_id)
                QMessageBox.information(self, "Bilgi", "İş akışı silindi.")
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")
            finally:
                self._close_service()
