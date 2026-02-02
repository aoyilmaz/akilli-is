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
)
from PyQt6.QtCore import Qt
import qtawesome as qta

from config.icons import ICONS
from modules.maintenance.views.base import MaintenanceBaseWidget
from database.models.maintenance import MaintenanceType
from ui.components.page_header import PageHeader
from ui.components.enhanced_table import EnhancedTableWidget, ColumnConfig


class ChecklistEditorWidget(MaintenanceBaseWidget):
    """Kontrol Listesi Editörü Widget'ı"""

    def __init__(self, parent=None):
        super().__init__("Kontrol Listesi Şablonları", parent)
        self.setup_ui()

    def setup_ui(self):
        # Header
        self.header = PageHeader(
            title="Kontrol Listesi Şablonları",
            icon=ICONS.LIST,
            show_search=False,
            show_add=True,
            add_text="Yeni Şablon",
            parent=self,
        )
        self.header.add_clicked.connect(self.create_checklist)
        self.header.refresh_clicked.connect(self.refresh_data)

        h_layout = self.header.header_layout()
        h_layout.addStretch()

        self.btn_edit = QPushButton("Düzenle")
        self.btn_edit.setIcon(qta.icon(ICONS.EDIT, color="#ffffff"))
        self.btn_edit.setProperty("class", "btn-secondary")
        self.btn_edit.setFixedHeight(36)
        self.btn_edit.clicked.connect(self.edit_checklist)
        h_layout.addWidget(self.btn_edit)

        self.btn_duplicate = QPushButton("Kopyala")
        self.btn_duplicate.setIcon(qta.icon(ICONS.INVOICE, color="#ffffff"))
        self.btn_duplicate.setFixedHeight(36)
        self.btn_duplicate.clicked.connect(self.duplicate_checklist)
        h_layout.addWidget(self.btn_duplicate)

        self.btn_delete = QPushButton("Sil")
        self.btn_delete.setIcon(qta.icon(ICONS.DELETE, color="#ffffff"))
        self.btn_delete.setProperty("class", "btn-danger")
        self.btn_delete.setFixedHeight(36)
        self.btn_delete.clicked.connect(self.delete_checklist)
        h_layout.addWidget(self.btn_delete)

        self.layout.addWidget(self.header)

        # Tablo
        cols = [
            ColumnConfig("name", "Şablon Adı", width=250, stretch=True),
            ColumnConfig("equipment", "Ekipman", width=200),
            ColumnConfig("type", "Bakım Türü", width=120),
            ColumnConfig("items", "Madde Sayısı", width=120),
        ]
        self.table = EnhancedTableWidget(
            table_id="maint_checklists", columns=cols, parent=self
        )
        self.table.row_double_clicked.connect(self.edit_checklist)
        self.layout.addWidget(self.table)

        self.refresh_data()

    def refresh_data(self):
        checklists = self.service.get_all_checklists()
        self.table.setRowCount(len(checklists))
        visible_cols = self.table.get_visible_columns()
        for i, cl in enumerate(checklists):
            self._populate_row(i, cl, visible_cols)

    def _populate_row(self, row, cl, visible_cols):
        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "name":
                item = QTableWidgetItem(cl.name)
                item.setData(Qt.ItemDataRole.UserRole, cl.id)
                self.table.setItem(row, col_idx, item)
            elif col_key == "equipment":
                val = cl.equipment.name if cl.equipment else "Genel"
                self.table.setItem(row, col_idx, QTableWidgetItem(val))
            elif col_key == "type":
                t_map = {
                    MaintenanceType.BREAKDOWN: "Arıza",
                    MaintenanceType.PREVENTIVE: "Periyodik",
                    MaintenanceType.PREDICTIVE: "Kestirimci",
                    MaintenanceType.CALIBRATION: "Kalibrasyon",
                }
                val = (
                    t_map.get(cl.maintenance_type, "-")
                    if cl.maintenance_type
                    else "Tümü"
                )
                self.table.setItem(row, col_idx, QTableWidgetItem(val))
            elif col_key == "items":
                val = str(len(cl.items)) if cl.items else "0"
                self.table.setItem(row, col_idx, QTableWidgetItem(val))

    def get_selected_checklist_id(self) -> Optional[int]:
        row = self.table.currentRow()
        if row < 0:
            return None
        return self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

    def create_checklist(self):
        if ChecklistDialog(self.service, self).exec():
            self.refresh_data()

    def edit_checklist(self, cl_id=None):
        if cl_id is None:
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
