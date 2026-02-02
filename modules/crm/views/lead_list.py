"""
Akıllı İş - Aday Müşteri Liste Sayfası
Yeni bileşen mimarisi kullanılarak yeniden yapılandırıldı.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QTableWidgetItem,
    QMessageBox,
)
import qtawesome as qta
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from ui.components import (
    BaseListPage,
    ColumnConfig,
)
from database.models.crm import LeadStatus
from config.icons import ICONS


class LeadListPage(BaseListPage):
    """Aday Müşteri (Lead) listesi sayfası."""

    # Sinyaller (Ek sinyaller)
    convert_clicked = pyqtSignal(int)

    STATUS_DISPLAY = {
        "new": ("Yeni", "#3b82f6", ICONS.SPARKLE),
        "contacted": ("İletişim", "#f59e0b", ICONS.PHONE),
        "qualified": ("Kalifiye", "#10b981", ICONS.CHECK),
        "unqualified": ("Uygun Değil", "#ef4444", ICONS.DANGER),
        "converted": ("Dönüştürüldü", "#8b5cf6", ICONS.SUCCESS),
    }

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("full_name", "Ad Soyad", stretch=True),
            ColumnConfig("company_name", "Şirket", stretch=True),
            ColumnConfig("status", "Durum", width=110),
            ColumnConfig("phone", "Telefon", width=130),
            ColumnConfig("email", "E-posta", width=180),
            ColumnConfig("source", "Kaynak", width=100),
            ColumnConfig("actions", "İşlemler", width=140),
        ]

        super().__init__(
            title="Aday Müşteriler (Leads)",
            icon=ICONS.ROCKET,
            table_id="lead_list",
            columns=columns,
            show_stats=True,
            show_search=True,
            show_add=True,
            add_text="Yeni Aday",
            search_placeholder="Ad, şirket ara...",
            parent=parent,
        )

        self.leads = []
        self._setup_stat_cards()

    def _setup_stat_cards(self):
        self.add_stat_card("total", "Toplam", "0", "info", ICONS.CRM)
        self.add_stat_card("new", "Yeni", "0", "info", ICONS.SPARKLE)
        self.add_stat_card("contacted", "Görüşüldü", "0", "warning", ICONS.PHONE)
        self.add_stat_card("qualified", "Kalifiye", "0", "success", ICONS.CHECK)

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
        self.update_stat_card("total", str(len(leads)))
        self.update_stat_card("new", str(new_count))
        self.update_stat_card("contacted", str(contacted_count))
        self.update_stat_card("qualified", str(qualified_count))

        self.update_count(len(leads), "aday")

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
                val = lead.get("company_name", "") or "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(val))

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
                val = lead.get("phone", "") or "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(val))

            elif col_key == "email":
                val = lead.get("email", "") or "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(val))

            elif col_key == "source":
                val = lead.get("source", "") or "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(val))

            elif col_key == "actions":
                actions = ["edit", "delete"]
                if status != LeadStatus.CONVERTED.value:
                    actions.insert(0, "convert")

                callbacks = {
                    "edit": lambda sid=lead_id: self.edit_clicked.emit(sid),
                    "delete": lambda sid=lead_id: self._confirm_delete(sid),
                    "convert": lambda sid=lead_id: self.convert_clicked.emit(sid),
                }

                # BaseListPage'teki create_action_widget'ı özelleştirelim
                # veya burda manuel kuralım.

                widget = QWidget()
                layout = QHBoxLayout(widget)
                layout.setContentsMargins(4, 2, 4, 2)
                layout.setSpacing(4)

                # Convert (Özel)
                if "convert" in actions:
                    from ui.components.action_buttons import create_custom_button

                    c_btn = create_custom_button(
                        widget, ICONS.TARGET, "Dönüştür", "purple"
                    )
                    c_btn.clicked.connect(callbacks["convert"])
                    layout.addWidget(c_btn)

                # Edit & Delete (Standart)
                from ui.components.action_buttons import (
                    create_edit_button,
                    create_delete_button,
                )

                e_btn = create_edit_button(widget)
                e_btn.clicked.connect(callbacks["edit"])
                layout.addWidget(e_btn)

                d_btn = create_delete_button(widget)
                d_btn.clicked.connect(callbacks["delete"])
                layout.addWidget(d_btn)

                layout.addStretch()
                self.table.setCellWidget(row, col_idx, widget)

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
