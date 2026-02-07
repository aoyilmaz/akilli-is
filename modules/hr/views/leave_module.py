"""
Akıllı İş - İzin Yönetim Modülü
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidgetItem,
    QMessageBox,
    QLabel,
    QComboBox,
    QFrame,
)
from PyQt6.QtCore import Qt

from config.icons import ICONS
from config.themes import get_theme
from modules.hr.services import HRService
from database.models.hr import LeaveType, LeaveStatus
from modules.hr.views.leave_form import LeaveFormDialog
from ui.components import PageHeader
from ui.components.enhanced_table import EnhancedTableWidget, ColumnConfig


LEAVE_STATUS_LABELS = {
    LeaveStatus.PENDING: "Bekliyor",
    LeaveStatus.APPROVED: "Onaylandı",
    LeaveStatus.REJECTED: "Reddedildi",
    LeaveStatus.CANCELLED: "İptal Edildi",
}

LEAVE_TYPE_LABELS = {
    LeaveType.ANNUAL: "Yıllık İzin",
    LeaveType.SICK: "Hastalık İzni",
    LeaveType.MATERNITY: "Doğum İzni",
    LeaveType.PATERNITY: "Babalık İzni",
    LeaveType.MARRIAGE: "Evlilik İzni",
    LeaveType.BEREAVEMENT: "Vefat İzni",
    LeaveType.UNPAID: "Ücretsiz İzin",
    LeaveType.OTHER: "Diğer",
}


class LeaveModule(QWidget):
    """İzin Yönetim Modülü"""

    page_title = "İzinler"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # === Header ===
        self.header = PageHeader(
            title="İzin Listesi",
            icon=ICONS.CALENDAR,
            show_search=True,
            show_add=True,
            add_text="Yeni İzin Talebi",
            parent=self,
        )
        self.header.add_clicked.connect(self._add_leave)
        self.header.refresh_clicked.connect(self.load_data)
        self.header.search_changed.connect(self.load_data)
        layout.addWidget(self.header)

        # === Filtreler Card Kaldırıldı (Tablodan yapılabilir) ===

        # === Tablo ===
        columns = [
            ColumnConfig("employee", "Çalışan", width=200, stretch=True),
            ColumnConfig("type", "İzin Türü", width=150),
            ColumnConfig("start_date", "Başlangıç", width=120),
            ColumnConfig("end_date", "Bitiş", width=120),
            ColumnConfig("duration", "Süre (Gün)", width=100),
            ColumnConfig("status", "Durum", width=120),
        ]

        self.table = EnhancedTableWidget(
            table_id="hr_leaves",
            columns=columns,
            parent=self,
        )
        self.table.row_double_clicked.connect(self._edit_leave)
        layout.addWidget(self.table)

    def _get_service(self):
        if self.service is None:
            self.service = HRService()
        return self.service

    def _close_service(self):
        if self.service:
            self.service.close()
            self.service = None

    def load_data(self):
        """Verileri yükle"""
        try:
            service = self._get_service()
            # Durum filtresi kaldırıldı, sadece arama metni ile filtreleme yapılabilir
            # veya tablo kendi içinde filtreleyebilir. Service tarafında default None gidecek.
            search = self.header.search_input.text().strip() or None

            leaves = service.get_leaves(search=search, limit=500)
            self.table.setRowCount(len(leaves))

            visible_cols = self.table.get_visible_columns()
            for row, leaf in enumerate(leaves):
                self._populate_row(row, leaf, visible_cols)

        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Veriler yüklenirken hata:\n{str(e)}")
        finally:
            self._close_service()

    def _populate_row(self, row, leaf, visible_cols):
        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "employee":
                item = QTableWidgetItem(
                    leaf.employee.full_name if leaf.employee else "-"
                )
                item.setData(Qt.ItemDataRole.UserRole, leaf.id)
                self.table.setItem(row, col_idx, item)
            elif col_key == "type":
                type_text = LEAVE_TYPE_LABELS.get(leaf.leave_type, str(leaf.leave_type))
                self.table.setItem(row, col_idx, QTableWidgetItem(type_text))
            elif col_key == "start_date":
                val = leaf.start_date.strftime("%d.%m.%Y") if leaf.start_date else "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(val))
            elif col_key == "end_date":
                val = leaf.end_date.strftime("%d.%m.%Y") if leaf.end_date else "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(val))
            elif col_key == "duration":
                self.table.setItem(row, col_idx, QTableWidgetItem(str(leaf.days)))
            elif col_key == "status":
                status_text = LEAVE_STATUS_LABELS.get(leaf.status, str(leaf.status))
                item = QTableWidgetItem(status_text)
                if leaf.status == LeaveStatus.APPROVED:
                    item.setForeground(Qt.GlobalColor.green)
                elif leaf.status == LeaveStatus.REJECTED:
                    item.setForeground(Qt.GlobalColor.red)
                elif leaf.status == LeaveStatus.PENDING:
                    item.setForeground(Qt.GlobalColor.yellow)
                self.table.setItem(row, col_idx, item)

    def _add_leave(self):
        """Yeni izin talebi"""
        dialog = LeaveFormDialog(parent=self)
        if dialog.exec():
            self.load_data()
            QMessageBox.information(self, "Başarılı", "İzin talebi oluşturuldu.")

    def _edit_leave(self):
        """İzin düzenle"""
        row = self.table.currentRow()
        if row < 0:
            return
        leaf_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        # Düzenleme işlemi...
