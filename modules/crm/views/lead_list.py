"""
Akıllı İş - Aday Müşteri Liste Sayfası
Yeni bileşen mimarisi kullanılarak yeniden yapılandırıldı.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidgetItem,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from ui.components import (
    PageHeader,
    EnhancedTableWidget,
    ColumnConfig,
    MiniStatCard,
)
from database.models.crm import LeadStatus
from config.icons import ICONS
import qtawesome as qta


class LeadListPage(QWidget):
    """Aday Müşteri (Lead) listesi sayfası."""

    # Sinyaller
    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    convert_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()

    STATUS_DISPLAY = {
        "new": ("Yeni", "#3b82f6", ICONS.SPARKLE),
        "contacted": ("İletişim", "#f59e0b", ICONS.PHONE),
        "qualified": ("Kalifiye", "#10b981", ICONS.CHECK),
        "unqualified": ("Uygun Değil", "#ef4444", ICONS.DANGER),
        "converted": ("Dönüştürüldü", "#8b5cf6", ICONS.SUCCESS),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.leads = []
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        self.header = PageHeader(
            title="Aday Müşteriler (Leads)",
            icon=ICONS.ROCKET,
            show_search=True,
            show_refresh=True,
            show_add=True,
            add_text="Yeni Aday",
            search_placeholder="Ad, şirket ara...",
            parent=self,
        )
        layout.addWidget(self.header)

        # İstatistik kartları
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.stat_cards = {}
        self.stat_cards["total"] = MiniStatCard(
            "Toplam", "0", "#6366f1", icon=ICONS.CRM
        )
        self.stat_cards["new"] = MiniStatCard(
            "Yeni", "0", "#3b82f6", icon=ICONS.SPARKLE
        )
        self.stat_cards["contacted"] = MiniStatCard(
            "Görüşüldü", "0", "#f59e0b", icon=ICONS.PHONE
        )
        self.stat_cards["qualified"] = MiniStatCard(
            "Kalifiye", "0", "#10b981", icon=ICONS.CHECK
        )

        for card in self.stat_cards.values():
            stats_layout.addWidget(card)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Tablo
        columns = [
            ColumnConfig("full_name", "Ad Soyad", stretch=True),
            ColumnConfig("company_name", "Şirket", stretch=True),
            ColumnConfig("status", "Durum", width=110),
            ColumnConfig("phone", "Telefon", width=130),
            ColumnConfig("email", "E-posta", width=180),
            ColumnConfig("source", "Kaynak", width=100),
            ColumnConfig("actions", "İşlemler", width=140),
        ]

        self.table = EnhancedTableWidget(
            table_id="lead_list",
            columns=columns,
            parent=self,
        )
        layout.addWidget(self.table)

        # Alt bilgi
        self.count_label = QLabel("Toplam: 0 aday")
        layout.addWidget(self.count_label)

    def _connect_signals(self):
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        self.header.add_clicked.connect(self.add_clicked.emit)
        self.header.search_changed.connect(self._on_search)
        self.table.row_double_clicked.connect(self.edit_clicked.emit)

    def load_data(self, leads: list):
        self.leads = leads
        self.table.setRowCount(len(leads))
        visible_cols = self.table.get_visible_columns()

        new_count = contacted_count = qualified_count = 0

        for row, lead in enumerate(leads):
            self._populate_row(row, lead, visible_cols)

            status = lead.get("status")
            if status == LeadStatus.NEW.value:
                new_count += 1
            elif status == LeadStatus.CONTACTED.value:
                contacted_count += 1
            elif status == LeadStatus.QUALIFIED.value:
                qualified_count += 1

        # Kartları güncelle
        self.stat_cards["total"].update_value(str(len(leads)))
        self.stat_cards["new"].update_value(str(new_count))
        self.stat_cards["contacted"].update_value(str(contacted_count))
        self.stat_cards["qualified"].update_value(str(qualified_count))

        self.count_label.setText(f"Toplam: {len(leads)} aday")

    def _populate_row(self, row: int, lead: dict, visible_cols: list):
        lead_id = lead.get("id")

        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "full_name":
                name = f"{lead.get('first_name', '')} {lead.get('last_name', '')}"
                item = QTableWidgetItem(name.strip())
                item.setData(Qt.ItemDataRole.UserRole, lead_id)
                item.setForeground(QColor("#818cf8"))
                self.table.setItem(row, col_idx, item)

            elif col_key == "company_name":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(lead.get("company_name", "") or "-")
                )

            elif col_key == "status":
                status = lead.get("status", "")
                display_info = self.STATUS_DISPLAY.get(
                    status, (status, "#ffffff", None)
                )
                if len(display_info) == 3:
                    text, color, icon_name = display_info
                else:
                    text, color = display_info
                    icon_name = None

                item = QTableWidgetItem(text)
                if icon_name:
                    item.setIcon(qta.icon(icon_name, color=color))
                item.setForeground(QColor(color))
                self.table.setItem(row, col_idx, item)

            elif col_key == "phone":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(lead.get("phone", "") or "-")
                )

            elif col_key == "email":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(lead.get("email", "") or "-")
                )

            elif col_key == "source":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(lead.get("source", "") or "-")
                )

            elif col_key == "actions":
                self._add_action_buttons(row, col_idx, lead)

        self.table.setRowHeight(row, 48)

    def _add_action_buttons(self, row: int, col: int, lead: dict):
        lead_id = lead.get("id")
        status = lead.get("status")

        btn_widget = QWidget()
        btn_widget.setProperty("class", "action-button-group")
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setContentsMargins(4, 4, 4, 4)
        btn_layout.setSpacing(4)

        # Dönüştür butonu
        if status != LeadStatus.CONVERTED.value:
            convert_btn = QPushButton("Dönüştür")
            convert_btn.setIcon(qta.icon(ICONS.TARGET, color="#8b5cf6"))
            convert_btn.setFixedSize(90, 26)
            convert_btn.setToolTip("Müşteriye Dönüştür")
            convert_btn.clicked.connect(lambda: self.convert_clicked.emit(lead_id))
            btn_layout.addWidget(convert_btn)

        # Düzenle butonu
        edit_btn = QPushButton()
        edit_btn.setIcon(qta.icon(ICONS.EDIT, color="#3b82f6"))
        edit_btn.setFixedSize(28, 26)
        edit_btn.setProperty("class", "action-edit")
        edit_btn.setToolTip("Düzenle")
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(lead_id))
        btn_layout.addWidget(edit_btn)

        # Sil butonu
        del_btn = QPushButton()
        del_btn.setIcon(qta.icon(ICONS.DELETE, color="#ef4444"))
        del_btn.setFixedSize(28, 26)
        del_btn.setProperty("class", "action-delete")
        del_btn.setToolTip("Sil")
        del_btn.clicked.connect(lambda: self._confirm_delete(lead_id))
        btn_layout.addWidget(del_btn)

        btn_layout.addStretch()
        self.table.setCellWidget(row, col, btn_widget)

    def _on_search(self, text: str):
        text = text.lower()
        for row in range(self.table.rowCount()):
            match = any(
                self.table.item(row, col)
                and text in self.table.item(row, col).text().lower()
                for col in range(self.table.columnCount())
            )
            self.table.setRowHidden(row, not match)

    def _confirm_delete(self, lead_id: int):
        reply = QMessageBox.question(
            self,
            "Silme Onayı",
            "Bu aday müşteriyi silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(lead_id)
