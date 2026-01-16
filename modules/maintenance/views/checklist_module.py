"""
Bakım Modülü - Kontrol Listeleri
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFormLayout,
    QLineEdit,
    QTextEdit,
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

from modules.maintenance.views.base import MaintenanceBaseWidget
from database.models.maintenance import MaintenanceType


class ChecklistEditorWidget(MaintenanceBaseWidget):
    """Kontrol Listesi Editörü Widget'ı"""

    def __init__(self, parent=None):
        super().__init__("Kontrol Listesi Şablonları", parent)
        self.setup_ui()

    def setup_ui(self):
        # Üst Butonlar
        btn_layout = QHBoxLayout()

        self.btn_new = QPushButton("Yeni Şablon")
        self.btn_new.setStyleSheet(
            "background-color: #007acc; color: white; padding: 8px 16px; border-radius: 4px;"
        )
        self.btn_new.clicked.connect(self.create_checklist)
        btn_layout.addWidget(self.btn_new)

        self.btn_edit = QPushButton("Düzenle")
        self.btn_edit.clicked.connect(self.edit_checklist)
        btn_layout.addWidget(self.btn_edit)

        self.btn_duplicate = QPushButton("Kopyala")
        self.btn_duplicate.clicked.connect(self.duplicate_checklist)
        btn_layout.addWidget(self.btn_duplicate)

        self.btn_delete = QPushButton("Sil")
        self.btn_delete.setStyleSheet(
            "background-color: #ef4444; color: white; padding: 8px 16px; border-radius: 4px;"
        )
        self.btn_delete.clicked.connect(self.delete_checklist)
        btn_layout.addWidget(self.btn_delete)

        btn_layout.addStretch()
        self.layout.addLayout(btn_layout)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Şablon Adı", "Ekipman", "Bakım Türü", "Madde Sayısı"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self.edit_checklist)
        self.layout.addWidget(self.table)

        self.refresh_data()

    def refresh_data(self):
        checklists = self.service.get_all_checklists()

        self.table.setRowCount(len(checklists))
        for i, cl in enumerate(checklists):
            self.table.setItem(i, 0, QTableWidgetItem(cl.name))
            self.table.item(i, 0).setData(Qt.ItemDataRole.UserRole, cl.id)

            self.table.setItem(i, 1, QTableWidgetItem(
                cl.equipment.name if cl.equipment else "Genel"
            ))

            type_text = {
                MaintenanceType.BREAKDOWN: "Arıza",
                MaintenanceType.PREVENTIVE: "Periyodik",
                MaintenanceType.PREDICTIVE: "Kestirimci",
                MaintenanceType.CALIBRATION: "Kalibrasyon",
            }.get(cl.maintenance_type, "-") if cl.maintenance_type else "Tümü"
            self.table.setItem(i, 2, QTableWidgetItem(type_text))

            item_count = len(cl.items) if cl.items else 0
            self.table.setItem(i, 3, QTableWidgetItem(str(item_count)))

    def get_selected_checklist_id(self) -> Optional[int]:
        current_row = self.table.currentRow()
        if current_row < 0:
            return None
        return self.table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)

    def create_checklist(self):
        dialog = ChecklistDialog(self.service, self)
        if dialog.exec():
            self.refresh_data()

    def edit_checklist(self):
        checklist_id = self.get_selected_checklist_id()
        if not checklist_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir şablon seçin.")
            return

        checklist = self.service.get_checklist_by_id(checklist_id)
        dialog = ChecklistDialog(self.service, self, checklist=checklist)
        if dialog.exec():
            self.refresh_data()

    def duplicate_checklist(self):
        checklist_id = self.get_selected_checklist_id()
        if not checklist_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir şablon seçin.")
            return

        try:
            new_checklist = self.service.duplicate_checklist(checklist_id)
            QMessageBox.information(
                self, "Başarılı",
                f"Şablon kopyalandı: {new_checklist.name}"
            )
            self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def delete_checklist(self):
        checklist_id = self.get_selected_checklist_id()
        if not checklist_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir şablon seçin.")
            return

        reply = QMessageBox.question(
            self,
            "Onay",
            "Bu kontrol listesi şablonunu silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.service.delete_checklist(checklist_id)
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))


class ChecklistDialog(QDialog):
    """Kontrol Listesi Ekleme/Düzenleme Dialogu"""

    def __init__(self, service, parent=None, checklist=None):
        super().__init__(parent)
        self.service = service
        self.checklist = checklist

        self.setWindowTitle("Şablon Düzenle" if checklist else "Yeni Kontrol Listesi")
        self.setMinimumSize(600, 600)

        main_layout = QVBoxLayout(self)

        # Temel bilgiler
        info_group = QGroupBox("Şablon Bilgileri")
        info_layout = QFormLayout(info_group)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Örn: CNC Torna Periyodik Bakım Kontrolleri")
        info_layout.addRow("Şablon Adı*:", self.inp_name)

        self.cmb_equipment = QComboBox()
        self.cmb_equipment.addItem("- Genel (Tüm Ekipmanlar) -", None)
        equipments = self.service.get_equipment_list(active_only=True)
        for eq in equipments:
            self.cmb_equipment.addItem(f"{eq.code} - {eq.name}", eq.id)
        info_layout.addRow("Ekipman:", self.cmb_equipment)

        self.cmb_type = QComboBox()
        self.cmb_type.addItem("- Tüm Bakım Türleri -", None)
        for t in MaintenanceType:
            label = {
                MaintenanceType.BREAKDOWN: "Arıza Onarım",
                MaintenanceType.PREVENTIVE: "Periyodik Bakım",
                MaintenanceType.PREDICTIVE: "Kestirimci Bakım",
                MaintenanceType.CALIBRATION: "Kalibrasyon",
            }.get(t, t.value)
            self.cmb_type.addItem(label, t)
        info_layout.addRow("Bakım Türü:", self.cmb_type)

        main_layout.addWidget(info_group)

        # Kontrol maddeleri
        items_group = QGroupBox("Kontrol Maddeleri")
        items_layout = QVBoxLayout(items_group)

        # Madde ekleme
        add_layout = QHBoxLayout()
        self.inp_item = QLineEdit()
        self.inp_item.setPlaceholderText("Kontrol maddesi açıklaması...")
        add_layout.addWidget(self.inp_item)

        self.chk_required = QCheckBox("Zorunlu")
        self.chk_required.setChecked(True)
        add_layout.addWidget(self.chk_required)

        btn_add = QPushButton("Ekle")
        btn_add.clicked.connect(self.add_item)
        add_layout.addWidget(btn_add)

        items_layout.addLayout(add_layout)

        # Madde listesi
        self.items_list = QListWidget()
        self.items_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        items_layout.addWidget(self.items_list)

        # Madde işlemleri
        item_btn_layout = QHBoxLayout()
        btn_remove = QPushButton("Seçili Maddeyi Sil")
        btn_remove.clicked.connect(self.remove_item)
        item_btn_layout.addWidget(btn_remove)

        btn_edit_item = QPushButton("Düzenle")
        btn_edit_item.clicked.connect(self.edit_item)
        item_btn_layout.addWidget(btn_edit_item)

        item_btn_layout.addStretch()
        items_layout.addLayout(item_btn_layout)

        main_layout.addWidget(items_group)

        # Mevcut veriyi yükle
        if self.checklist:
            self.load_checklist_data()

        # Buttons
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        main_layout.addWidget(btns)

    def load_checklist_data(self):
        """Mevcut şablon verilerini forma yükle"""
        cl = self.checklist

        self.inp_name.setText(cl.name)

        if cl.equipment_id:
            idx = self.cmb_equipment.findData(cl.equipment_id)
            if idx >= 0:
                self.cmb_equipment.setCurrentIndex(idx)

        if cl.maintenance_type:
            idx = self.cmb_type.findData(cl.maintenance_type)
            if idx >= 0:
                self.cmb_type.setCurrentIndex(idx)

        # Maddeler
        if cl.items:
            for item in sorted(cl.items, key=lambda x: x.order_no or 0):
                list_item = QListWidgetItem(item.description)
                list_item.setData(Qt.ItemDataRole.UserRole, {
                    "id": item.id,
                    "is_required": item.is_required
                })
                if item.is_required:
                    list_item.setText(f"[Zorunlu] {item.description}")
                self.items_list.addItem(list_item)

    def add_item(self):
        """Yeni kontrol maddesi ekle"""
        text = self.inp_item.text().strip()
        if not text:
            return

        is_required = self.chk_required.isChecked()
        display_text = f"[Zorunlu] {text}" if is_required else text

        list_item = QListWidgetItem(display_text)
        list_item.setData(Qt.ItemDataRole.UserRole, {
            "id": None,  # Yeni madde
            "is_required": is_required,
            "description": text
        })
        self.items_list.addItem(list_item)
        self.inp_item.clear()

    def remove_item(self):
        """Seçili maddeyi sil"""
        current_row = self.items_list.currentRow()
        if current_row >= 0:
            self.items_list.takeItem(current_row)

    def edit_item(self):
        """Seçili maddeyi düzenle"""
        current_item = self.items_list.currentItem()
        if not current_item:
            return

        data = current_item.data(Qt.ItemDataRole.UserRole)

        # Basit düzenleme için input dialog
        from PyQt6.QtWidgets import QInputDialog
        text = data.get("description") or current_item.text().replace("[Zorunlu] ", "")
        new_text, ok = QInputDialog.getText(
            self, "Madde Düzenle", "Açıklama:", text=text
        )

        if ok and new_text:
            data["description"] = new_text
            current_item.setData(Qt.ItemDataRole.UserRole, data)
            display_text = f"[Zorunlu] {new_text}" if data.get("is_required") else new_text
            current_item.setText(display_text)

    def accept(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Uyarı", "Şablon adı zorunludur.")
            return

        if self.items_list.count() == 0:
            QMessageBox.warning(self, "Uyarı", "En az bir kontrol maddesi ekleyin.")
            return

        try:
            # Maddeleri topla
            items = []
            for i in range(self.items_list.count()):
                item = self.items_list.item(i)
                data = item.data(Qt.ItemDataRole.UserRole)
                items.append({
                    "description": data.get("description") or item.text().replace("[Zorunlu] ", ""),
                    "is_required": data.get("is_required", True),
                    "order_no": i + 1
                })

            checklist_data = {
                "name": name,
                "equipment_id": self.cmb_equipment.currentData(),
                "maintenance_type": self.cmb_type.currentData(),
                "items": items
            }

            if self.checklist:
                self.service.update_checklist(self.checklist.id, **checklist_data)
            else:
                self.service.create_checklist(**checklist_data)

            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
