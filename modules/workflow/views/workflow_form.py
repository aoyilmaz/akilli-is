"""
Akıllı İş - Workflow Tanım Formu

Workflow tanımlarını oluşturma ve düzenleme formu.
Adımlar da bu formda yönetilir.
"""

from typing import List, Dict, Optional
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGridLayout,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QFrame,
    QScrollArea,
    QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
import qtawesome as qta

from config.icons import ICONS
from config.styles import Colors


# Hedef tablo seçenekleri
TARGET_TABLES = [
    ("purchase_requests", "Satın Alma Talepleri"),
    ("purchase_orders", "Satın Alma Siparişleri"),
    ("sales_orders", "Satış Siparişleri"),
    ("invoices", "Faturalar"),
    ("leaves", "İzin Talepleri"),
    ("work_orders", "İş Emirleri"),
]


class StepFormDialog(QDialog):
    """Workflow adımı düzenleme dialogu"""

    def __init__(self, step_data: Dict = None, roles: List = None, users: List = None, parent=None):
        super().__init__(parent)
        self.step_data = step_data or {}
        self.roles = roles or []
        self.users = users or []
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        self.setWindowTitle("Adım Düzenle" if self.step_data.get("id") else "Yeni Adım")
        self.setMinimumSize(500, 450)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BACKGROUND};
            }}
            QLabel {{
                color: {Colors.TEXT};
            }}
            QLineEdit, QTextEdit, QComboBox, QSpinBox {{
                background-color: {Colors.SECONDARY};
                color: {Colors.TEXT};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                padding: 8px;
            }}
            QCheckBox {{
                color: {Colors.TEXT};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Adım sırası
        self.order_input = QSpinBox()
        self.order_input.setRange(1, 99)
        self.order_input.setValue(1)
        form.addRow("Sıra No:", self.order_input)

        # Adım adı
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Örn: Departman Müdürü Onayı")
        form.addRow("Adım Adı *:", self.name_input)

        # Açıklama
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(60)
        self.desc_input.setPlaceholderText("Adım açıklaması (opsiyonel)")
        form.addRow("Açıklama:", self.desc_input)

        # Onaylayıcı türü
        self.approver_type = QComboBox()
        self.approver_type.addItem("Rol Bazlı", "role")
        self.approver_type.addItem("Belirli Kullanıcı", "user")
        self.approver_type.addItem("Dinamik Alan", "dynamic")
        self.approver_type.currentIndexChanged.connect(self._on_approver_type_changed)
        form.addRow("Onaylayıcı Türü:", self.approver_type)

        # Rol seçimi
        self.role_combo = QComboBox()
        self.role_combo.addItem("Seçiniz...", None)
        for role in self.roles:
            self.role_combo.addItem(role.get("name", ""), role.get("id"))
        form.addRow("Gerekli Rol:", self.role_combo)

        # Kullanıcı seçimi
        self.user_combo = QComboBox()
        self.user_combo.addItem("Seçiniz...", None)
        for user in self.users:
            self.user_combo.addItem(user.get("name", ""), user.get("id"))
        self.user_combo.setVisible(False)
        form.addRow("Onaylayıcı Kullanıcı:", self.user_combo)

        # Dinamik alan
        self.dynamic_field = QLineEdit()
        self.dynamic_field.setPlaceholderText("Örn: requested_by.manager_id")
        self.dynamic_field.setVisible(False)
        form.addRow("Dinamik Alan:", self.dynamic_field)

        # Koşul
        self.condition_input = QLineEdit()
        self.condition_input.setPlaceholderText("Örn: total_amount > 10000")
        form.addRow("Koşul (opsiyonel):", self.condition_input)

        # Zaman aşımı
        self.timeout_input = QSpinBox()
        self.timeout_input.setRange(0, 720)
        self.timeout_input.setValue(0)
        self.timeout_input.setSuffix(" saat")
        self.timeout_input.setSpecialValueText("Yok")
        form.addRow("Zaman Aşımı:", self.timeout_input)

        # Son adım mı?
        self.is_final = QCheckBox("Bu son adımdır")
        form.addRow("", self.is_final)

        layout.addLayout(form)

        # Butonlar
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_approver_type_changed(self, index: int):
        """Onaylayıcı türü değiştiğinde"""
        approver_type = self.approver_type.currentData()
        self.role_combo.setVisible(approver_type == "role")
        self.user_combo.setVisible(approver_type == "user")
        self.dynamic_field.setVisible(approver_type == "dynamic")

    def load_data(self):
        """Mevcut veriyi yükle"""
        if not self.step_data:
            return

        self.order_input.setValue(self.step_data.get("step_order", 1))
        self.name_input.setText(self.step_data.get("name", ""))
        self.desc_input.setPlainText(self.step_data.get("description", "") or "")
        self.condition_input.setText(self.step_data.get("condition_script", "") or "")
        self.timeout_input.setValue(self.step_data.get("timeout_hours", 0) or 0)
        self.is_final.setChecked(self.step_data.get("is_final_step", False))

        # Onaylayıcı türünü belirle
        if self.step_data.get("approver_user_id"):
            self.approver_type.setCurrentIndex(1)  # user
            for i in range(self.user_combo.count()):
                if self.user_combo.itemData(i) == self.step_data.get("approver_user_id"):
                    self.user_combo.setCurrentIndex(i)
                    break
        elif self.step_data.get("dynamic_approver_field"):
            self.approver_type.setCurrentIndex(2)  # dynamic
            self.dynamic_field.setText(self.step_data.get("dynamic_approver_field", ""))
        else:
            self.approver_type.setCurrentIndex(0)  # role
            for i in range(self.role_combo.count()):
                if self.role_combo.itemData(i) == self.step_data.get("required_role_id"):
                    self.role_combo.setCurrentIndex(i)
                    break

        self._on_approver_type_changed(self.approver_type.currentIndex())

    def get_data(self) -> Dict:
        """Form verilerini al"""
        data = {
            "step_order": self.order_input.value(),
            "name": self.name_input.text().strip(),
            "description": self.desc_input.toPlainText().strip() or None,
            "condition_script": self.condition_input.text().strip() or None,
            "timeout_hours": self.timeout_input.value() or None,
            "is_final_step": self.is_final.isChecked(),
            "required_role_id": None,
            "approver_user_id": None,
            "dynamic_approver_field": None,
        }

        approver_type = self.approver_type.currentData()
        if approver_type == "role":
            data["required_role_id"] = self.role_combo.currentData()
        elif approver_type == "user":
            data["approver_user_id"] = self.user_combo.currentData()
        elif approver_type == "dynamic":
            data["dynamic_approver_field"] = self.dynamic_field.text().strip()

        if self.step_data.get("id"):
            data["id"] = self.step_data["id"]

        return data

    def accept(self):
        """Kaydet"""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Uyarı", "Adım adı zorunludur.")
            return

        approver_type = self.approver_type.currentData()
        if approver_type == "role" and not self.role_combo.currentData():
            QMessageBox.warning(self, "Uyarı", "Lütfen bir rol seçin.")
            return
        elif approver_type == "user" and not self.user_combo.currentData():
            QMessageBox.warning(self, "Uyarı", "Lütfen bir kullanıcı seçin.")
            return
        elif approver_type == "dynamic" and not self.dynamic_field.text().strip():
            QMessageBox.warning(self, "Uyarı", "Lütfen dinamik alan girin.")
            return

        super().accept()


class WorkflowFormPage(QWidget):
    """Workflow tanım formu"""

    # Signals
    saved = pyqtSignal()
    cancelled = pyqtSignal()

    def __init__(self, workflow_id: int = None, parent=None):
        super().__init__(parent)
        self.workflow_id = workflow_id
        self.workflow_data = None
        self.steps_data: List[Dict] = []
        self.service = None
        self.roles = []
        self.users = []
        self.setup_ui()
        self.load_lookup_data()
        if workflow_id:
            self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        back_btn = QPushButton("← Geri")
        back_btn.clicked.connect(self.cancelled.emit)
        header_layout.addWidget(back_btn)

        title_text = "İş Akışı Düzenle" if self.workflow_id else "Yeni İş Akışı"
        title = QLabel(f"⚙️ {title_text}")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {Colors.TEXT};")
        header_layout.addWidget(title)
        header_layout.addStretch()

        save_btn = QPushButton("💾 Kaydet")
        save_btn.setProperty("class", "btn-primary")
        save_btn.clicked.connect(self._on_save)
        header_layout.addWidget(save_btn)

        layout.addLayout(header_layout)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)

        # === GENEL BİLGİLER ===
        general_group = QGroupBox("📝 Genel Bilgiler")
        general_layout = QFormLayout()
        general_layout.setSpacing(12)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Örn: PURCHASE_APPROVAL")
        general_layout.addRow("Kod *:", self.code_input)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Örn: Satın Alma Onay Akışı")
        general_layout.addRow("Ad *:", self.name_input)

        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(60)
        self.desc_input.setPlaceholderText("İş akışı açıklaması")
        general_layout.addRow("Açıklama:", self.desc_input)

        self.target_combo = QComboBox()
        self.target_combo.addItem("Seçiniz...", None)
        for code, label in TARGET_TABLES:
            self.target_combo.addItem(label, code)
        general_layout.addRow("Hedef Tablo *:", self.target_combo)

        self.condition_input = QLineEdit()
        self.condition_input.setPlaceholderText("Örn: total_amount > 50000")
        general_layout.addRow("Aktivasyon Koşulu:", self.condition_input)

        self.priority_input = QSpinBox()
        self.priority_input.setRange(0, 100)
        self.priority_input.setValue(0)
        general_layout.addRow("Öncelik:", self.priority_input)

        checkbox_layout = QHBoxLayout()
        self.is_default = QCheckBox("Varsayılan")
        self.is_active = QCheckBox("Aktif")
        self.is_active.setChecked(True)
        checkbox_layout.addWidget(self.is_default)
        checkbox_layout.addWidget(self.is_active)
        checkbox_layout.addStretch()
        general_layout.addRow("", checkbox_layout)

        general_group.setLayout(general_layout)
        scroll_layout.addWidget(general_group)

        # === ADIMLAR ===
        steps_group = QGroupBox("📋 Onay Adımları")
        steps_layout = QVBoxLayout()

        # Adım butonları
        steps_btn_layout = QHBoxLayout()
        add_step_btn = QPushButton("+ Adım Ekle")
        add_step_btn.setProperty("class", "btn-success")
        add_step_btn.clicked.connect(self._on_add_step)
        steps_btn_layout.addWidget(add_step_btn)
        steps_btn_layout.addStretch()
        steps_layout.addLayout(steps_btn_layout)

        # Adımlar tablosu
        self.steps_table = QTableWidget()
        self.steps_table.setColumnCount(6)
        self.steps_table.setHorizontalHeaderLabels([
            "Sıra", "Ad", "Onaylayıcı", "Koşul", "Son Adım", "İşlemler"
        ])
        self.steps_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.steps_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.steps_table.setMinimumHeight(200)
        self.steps_table.setAlternatingRowColors(True)
        steps_layout.addWidget(self.steps_table)

        steps_group.setLayout(steps_layout)
        scroll_layout.addWidget(steps_group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

    def _get_service(self):
        if self.service is None:
            from modules.workflow.services import WorkflowService
            self.service = WorkflowService()
        return self.service

    def _close_service(self):
        if self.service:
            self.service.close()
            self.service = None

    def load_lookup_data(self):
        """Rol ve kullanıcı verilerini yükle"""
        try:
            from database.base import get_session
            from database.models.user import Role, User

            session = get_session()

            # Roller
            roles = session.query(Role).filter(Role.is_active == True).all()
            self.roles = [{"id": r.id, "name": r.name} for r in roles]

            # Kullanıcılar
            users = session.query(User).filter(User.is_active == True).all()
            self.users = [{"id": u.id, "name": u.full_name or u.username} for u in users]

            session.close()
        except Exception as e:
            print(f"Lookup data yükleme hatası: {e}")

    def load_data(self):
        """Mevcut workflow'u yükle"""
        if not self.workflow_id:
            return

        try:
            service = self._get_service()
            wf = service.get_workflow_definition(self.workflow_id)

            if not wf:
                QMessageBox.warning(self, "Uyarı", "İş akışı bulunamadı.")
                return

            self.workflow_data = wf
            self.code_input.setText(wf.code or "")
            self.name_input.setText(wf.name or "")
            self.desc_input.setPlainText(wf.description or "")
            self.condition_input.setText(wf.activation_condition or "")
            self.priority_input.setValue(wf.priority or 0)
            self.is_default.setChecked(wf.is_default or False)
            self.is_active.setChecked(wf.is_active if wf.is_active is not None else True)

            # Hedef tablo
            for i in range(self.target_combo.count()):
                if self.target_combo.itemData(i) == wf.target_table:
                    self.target_combo.setCurrentIndex(i)
                    break

            # Adımlar
            self.steps_data = []
            for step in (wf.steps or []):
                self.steps_data.append({
                    "id": step.id,
                    "step_order": step.step_order,
                    "name": step.name,
                    "description": step.description,
                    "required_role_id": step.required_role_id,
                    "approver_user_id": step.approver_user_id,
                    "dynamic_approver_field": step.dynamic_approver_field,
                    "condition_script": step.condition_script,
                    "timeout_hours": step.timeout_hours,
                    "is_final_step": step.is_final_step,
                })

            self._render_steps()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yükleme hatası: {e}")
        finally:
            self._close_service()

    def _render_steps(self):
        """Adımları tabloya render et"""
        self.steps_table.setRowCount(len(self.steps_data))

        for r, step in enumerate(sorted(self.steps_data, key=lambda x: x.get("step_order", 0))):
            # Sıra
            self.steps_table.setItem(r, 0, QTableWidgetItem(str(step.get("step_order", ""))))

            # Ad
            self.steps_table.setItem(r, 1, QTableWidgetItem(step.get("name", "")))

            # Onaylayıcı
            approver = "-"
            if step.get("required_role_id"):
                role = next((r for r in self.roles if r["id"] == step["required_role_id"]), None)
                approver = f"Rol: {role['name']}" if role else f"Rol ID: {step['required_role_id']}"
            elif step.get("approver_user_id"):
                user = next((u for u in self.users if u["id"] == step["approver_user_id"]), None)
                approver = f"Kullanıcı: {user['name']}" if user else f"User ID: {step['approver_user_id']}"
            elif step.get("dynamic_approver_field"):
                approver = f"Dinamik: {step['dynamic_approver_field']}"
            self.steps_table.setItem(r, 2, QTableWidgetItem(approver))

            # Koşul
            condition = step.get("condition_script") or "-"
            self.steps_table.setItem(r, 3, QTableWidgetItem(condition))

            # Son adım
            is_final = "✓" if step.get("is_final_step") else "-"
            self.steps_table.setItem(r, 4, QTableWidgetItem(is_final))

            # İşlemler
            w = QWidget()
            h_layout = QHBoxLayout(w)
            h_layout.setContentsMargins(4, 4, 4, 4)
            h_layout.setSpacing(4)

            edit_btn = QPushButton("Düzenle")
            edit_btn.setFixedHeight(26)
            edit_btn.clicked.connect(lambda _, idx=r: self._on_edit_step(idx))
            h_layout.addWidget(edit_btn)

            del_btn = QPushButton("Sil")
            del_btn.setFixedHeight(26)
            del_btn.setStyleSheet("background-color: #f44336; color: white;")
            del_btn.clicked.connect(lambda _, idx=r: self._on_delete_step(idx))
            h_layout.addWidget(del_btn)

            self.steps_table.setCellWidget(r, 5, w)

    def _on_add_step(self):
        """Yeni adım ekle"""
        # Varsayılan sıra numarası
        max_order = max([s.get("step_order", 0) for s in self.steps_data], default=0)
        default_data = {"step_order": max_order + 1}

        dialog = StepFormDialog(default_data, self.roles, self.users, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            step_data = dialog.get_data()
            self.steps_data.append(step_data)
            self._render_steps()

    def _on_edit_step(self, index: int):
        """Adım düzenle"""
        sorted_steps = sorted(self.steps_data, key=lambda x: x.get("step_order", 0))
        if 0 <= index < len(sorted_steps):
            step = sorted_steps[index]
            dialog = StepFormDialog(step, self.roles, self.users, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_data = dialog.get_data()
                # Güncelle
                for i, s in enumerate(self.steps_data):
                    if s.get("id") == step.get("id") or (not s.get("id") and s == step):
                        self.steps_data[i] = new_data
                        break
                self._render_steps()

    def _on_delete_step(self, index: int):
        """Adım sil"""
        sorted_steps = sorted(self.steps_data, key=lambda x: x.get("step_order", 0))
        if 0 <= index < len(sorted_steps):
            step = sorted_steps[index]
            reply = QMessageBox.question(
                self,
                "Silme Onayı",
                f"'{step.get('name', '')}' adımını silmek istediğinizden emin misiniz?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.steps_data = [s for s in self.steps_data if s != step]
                self._render_steps()

    def _on_save(self):
        """Kaydet"""
        # Validasyon
        code = self.code_input.text().strip()
        name = self.name_input.text().strip()
        target = self.target_combo.currentData()

        if not code:
            QMessageBox.warning(self, "Uyarı", "Kod alanı zorunludur.")
            return
        if not name:
            QMessageBox.warning(self, "Uyarı", "Ad alanı zorunludur.")
            return
        if not target:
            QMessageBox.warning(self, "Uyarı", "Hedef tablo seçimi zorunludur.")
            return
        if not self.steps_data:
            QMessageBox.warning(self, "Uyarı", "En az bir onay adımı eklemelisiniz.")
            return

        try:
            service = self._get_service()

            workflow_data = {
                "code": code,
                "name": name,
                "description": self.desc_input.toPlainText().strip() or None,
                "target_table": target,
                "activation_condition": self.condition_input.text().strip() or None,
                "priority": self.priority_input.value(),
                "is_default": self.is_default.isChecked(),
                "is_active": self.is_active.isChecked(),
            }

            if self.workflow_id:
                # Güncelle
                service.update_workflow_definition(self.workflow_id, workflow_data, self.steps_data)
            else:
                # Yeni oluştur
                service.create_workflow_definition(workflow_data, self.steps_data)

            QMessageBox.information(self, "Bilgi", "İş akışı kaydedildi.")
            self.saved.emit()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {e}")
        finally:
            self._close_service()
