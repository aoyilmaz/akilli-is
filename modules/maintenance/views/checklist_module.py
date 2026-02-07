"""
Bakım Modülü - Kontrol Listeleri
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidgetItem,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QListWidget,
    QListWidgetItem,
    QGroupBox,
    QCheckBox,
    QMenu,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
import qtawesome as qta

from config.icons import ICONS
from ui.components.base_list_page import BaseListPage
from ui.components.enhanced_table import ColumnConfig
from database.base import get_session
from modules.maintenance.services import MaintenanceService
from database.models.maintenance import MaintenanceType


class ChecklistEditorWidget(BaseListPage):
    """Kontrol Listesi Editörü Widget'ı"""

    def __init__(self, parent=None):
        self.db_session = get_session()
        self.service = MaintenanceService(self.db_session)

        columns = [
            ColumnConfig(
                "name", "Şablon Adı", width=250, filterable=True, stretch=True
            ),
            ColumnConfig("equipment", "Ekipman", width=200, filterable=True),
            ColumnConfig("type", "Bakım Türü", width=120, filterable=True),
            ColumnConfig("items", "Madde Sayısı", width=120),
        ]

        super().__init__(
            title="Kontrol Listesi Şablonları",
            icon=ICONS.LIST,
            table_id="maintenance_checklists",
            columns=columns,
            show_add=True,
            add_text="Yeni Şablon",
            parent=parent,
        )

        self._setup_extra_ui()
        self.add_clicked.connect(self.create_checklist)
        self.refresh_requested.connect(self.refresh_data)

    def closeEvent(self, event):
        if hasattr(self, "db_session") and self.db_session:
            self.db_session.close()
        super().closeEvent(event)

    def _setup_extra_ui(self):
        # Context Menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # Filters (Maintenance Type) - Manual population for now as enum handling is basic
        t_map = {
            MaintenanceType.BREAKDOWN: "Arıza",
            MaintenanceType.PREVENTIVE: "Periyodik",
            MaintenanceType.PREDICTIVE: "Kestirimci",
            MaintenanceType.CALIBRATION: "Kalibrasyon",
        }
        self.table.set_filter_options("type", list(t_map.values()))

    def refresh_data(self):
        checklists = self.service.get_all_checklists()
        self.load_data(checklists)

    def load_data(self, checklists):
        self.table.setRowCount(len(checklists))

        for i, cl in enumerate(checklists):
            # Name
            item = QTableWidgetItem(cl.name)
            item.setData(Qt.ItemDataRole.UserRole, cl.id)
            self.table.setItem(i, 0, item)

            # Equipment
            val = cl.equipment.name if cl.equipment else "Genel"
            self.table.setItem(i, 1, QTableWidgetItem(val))

            # Type
            t_map = {
                MaintenanceType.BREAKDOWN: "Arıza",
                MaintenanceType.PREVENTIVE: "Periyodik",
                MaintenanceType.PREDICTIVE: "Kestirimci",
                MaintenanceType.CALIBRATION: "Kalibrasyon",
            }
            val = t_map.get(cl.maintenance_type, "-") if cl.maintenance_type else "Tümü"
            self.table.setItem(i, 2, QTableWidgetItem(val))

            # Items
            val = str(len(cl.items)) if cl.items else "0"
            self.table.setItem(i, 3, QTableWidgetItem(val))

        self.update_count(len(checklists))

    def get_selected_checklist_id(self) -> Optional[int]:
        return self.table.get_selected_id()

    def _show_context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0:
            return

        menu = QMenu(self)

        edit_action = QAction(qta.icon(ICONS.EDIT, color="#f59e0b"), "Düzenle", self)
        edit_action.triggered.connect(self.edit_checklist)
        menu.addAction(edit_action)

        dup_action = QAction(qta.icon(ICONS.INVOICE, color="#3b82f6"), "Kopyala", self)
        dup_action.triggered.connect(self.duplicate_checklist)
        menu.addAction(dup_action)

        del_action = QAction(qta.icon(ICONS.DELETE, color="#ef4444"), "Sil", self)
        del_action.triggered.connect(self.delete_checklist)
        menu.addAction(del_action)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def create_checklist(self):
        if ChecklistDialog(self.service, self).exec():
            self.refresh_data()

    def edit_checklist(self, cl_id=None):
        if cl_id is None or isinstance(cl_id, bool):  # Handle signal specific arg
            cl_id = self.get_selected_checklist_id()
        if not cl_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir şablon seçin.")
            return
        cl = self.service.get_checklist_by_id(cl_id)
        if ChecklistDialog(self.service, self, checklist=cl).exec():
            self.refresh_data()

    def duplicate_checklist(self):
        cl_id = self.get_selected_checklist_id()
        if not cl_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir şablon seçin.")
            return
        try:
            new_cl = self.service.duplicate_checklist(cl_id)
            QMessageBox.information(
                self, "Başarılı", f"Şablon kopyalandı: {new_cl.name}"
            )
            self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def delete_checklist(self):
        cl_id = self.get_selected_checklist_id()
        if not cl_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir şablon seçin.")
            return
        rep = QMessageBox.question(
            self,
            "Onay",
            "Bu kontrol listesi şablonunu silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if rep == QMessageBox.StandardButton.Yes:
            try:
                self.service.delete_checklist(cl_id)
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))

    # Interface Implementation
    def get_search_text(self) -> str:
        return self.header.get_search_text()


class ChecklistDialog(QDialog):
    """Kontrol Listesi Ekleme/Düzenleme Dialogu"""

    def __init__(self, service, parent=None, checklist=None):
        super().__init__(parent)
        self.service, self.checklist = service, checklist
        self.setWindowTitle("Şablon Düzenle" if checklist else "Yeni Kontrol Listesi")
        self.setMinimumSize(600, 600)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        info_group = QGroupBox("Şablon Bilgileri")
        info_layout = QFormLayout(info_group)
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Örn: CNC Torna Periyodik Bakım Kontrolleri")
        info_layout.addRow("Şablon Adı*:", self.inp_name)

        self.cmb_eq = QComboBox()
        self.cmb_eq.addItem("- Genel (Tüm Ekipmanlar) -", None)
        for eq in self.service.get_equipment_list(active_only=True):
            self.cmb_eq.addItem(f"{eq.code} - {eq.name}", eq.id)
        info_layout.addRow("Ekipman:", self.cmb_eq)

        self.cmb_type = QComboBox()
        self.cmb_type.addItem("- Tüm Bakım Türleri -", None)
        t_map = {
            MaintenanceType.BREAKDOWN: "Arıza Onarım",
            MaintenanceType.PREVENTIVE: "Periyodik Bakım",
            MaintenanceType.PREDICTIVE: "Kestirimci Bakım",
            MaintenanceType.CALIBRATION: "Kalibrasyon",
        }
        for t in MaintenanceType:
            self.cmb_type.addItem(t_map.get(t, t.value), t)
        info_layout.addRow("Bakım Türü:", self.cmb_type)
        layout.addWidget(info_group)

        items_group = QGroupBox("Kontrol Maddeleri")
        items_layout = QVBoxLayout(items_group)
        add_layout = QHBoxLayout()
        self.inp_item = QLineEdit()
        self.inp_item.setPlaceholderText("Kontrol maddesi açıklaması...")
        add_layout.addWidget(self.inp_item)
        self.chk_req = QCheckBox("Zorunlu")
        self.chk_req.setChecked(True)
        add_layout.addWidget(self.chk_req)
        btn_add = QPushButton("Ekle")
        btn_add.clicked.connect(self.add_item)
        add_layout.addWidget(btn_add)
        items_layout.addLayout(add_layout)

        self.items_list = QListWidget()
        self.items_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        items_layout.addWidget(self.items_list)

        item_btn_layout = QHBoxLayout()
        btn_rem = QPushButton("Seçili Maddeyi Sil")
        btn_rem.clicked.connect(self.remove_item)
        item_btn_layout.addWidget(btn_rem)
        btn_edt = QPushButton("Düzenle")
        btn_edt.clicked.connect(self.edit_item)
        item_btn_layout.addWidget(btn_edt)
        item_btn_layout.addStretch()
        items_layout.addLayout(item_btn_layout)
        layout.addWidget(items_group)

        if self.checklist:
            self.load_data()

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def load_data(self):
        cl = self.checklist
        self.inp_name.setText(cl.name)
        if cl.equipment_id:
            self.cmb_eq.setCurrentIndex(self.cmb_eq.findData(cl.equipment_id))
        if cl.maintenance_type:
            self.cmb_type.setCurrentIndex(self.cmb_type.findData(cl.maintenance_type))
        if cl.items:
            for item in sorted(cl.items, key=lambda x: x.order_no or 0):
                l_item = QListWidgetItem(
                    f"[Zorunlu] {item.description}"
                    if item.is_required
                    else item.description
                )
                l_item.setData(
                    Qt.ItemDataRole.UserRole,
                    {"id": item.id, "is_required": item.is_required},
                )
                self.items_list.addItem(l_item)

    def add_item(self):
        text = self.inp_item.text().strip()
        if not text:
            return
        is_req = self.chk_req.isChecked()
        list_item = QListWidgetItem(f"[Zorunlu] {text}" if is_req else text)
        list_item.setData(
            Qt.ItemDataRole.UserRole,
            {"id": None, "is_required": is_req, "description": text},
        )
        self.items_list.addItem(list_item)
        self.inp_item.clear()

    def remove_item(self):
        row = self.items_list.currentRow()
        if row >= 0:
            self.items_list.takeItem(row)

    def edit_item(self):
        item = self.items_list.currentItem()
        if not item:
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        from PyQt6.QtWidgets import QInputDialog

        text = data.get("description") or item.text().replace("[Zorunlu] ", "")
        nt, ok = QInputDialog.getText(self, "Madde Düzenle", "Açıklama:", text=text)
        if ok and nt:
            data["description"] = nt
            item.setData(Qt.ItemDataRole.UserRole, data)
            item.setText(f"[Zorunlu] {nt}" if data.get("is_required") else nt)

    def accept(self):
        name = self.inp_name.text().strip()
        if not name or self.items_list.count() == 0:
            QMessageBox.warning(
                self, "Uyarı", "Şablon adı ve en az bir kontrol maddesi zorunludur."
            )
            return
        try:
            items = []
            for i in range(self.items_list.count()):
                it = self.items_list.item(i)
                d = it.data(Qt.ItemDataRole.UserRole)
                items.append(
                    {
                        "description": d.get("description")
                        or it.text().replace("[Zorunlu] ", ""),
                        "is_required": d.get("is_required", True),
                        "order_no": i + 1,
                    }
                )
            data = {
                "name": name,
                "equipment_id": self.cmb_eq.currentData(),
                "maintenance_type": self.cmb_type.currentData(),
                "items": items,
            }
            if self.checklist:
                self.service.update_checklist(self.checklist.id, **data)
            else:
                self.service.create_checklist(**data)
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
