"""
Akıllı İş ERP - Kullanıcı Yönetimi Ekranı
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
    QDialog,
    QLabel,
    QLineEdit,
    QFormLayout,
    QCheckBox,
    QScrollArea,
    QFrame,
    QTabWidget,
    QMessageBox,
    QCompleter,
    QComboBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from ui.components.toast import show_toast
import qtawesome as qta
from config.icons import ICONS
from config.themes import get_theme

from database.base import get_session
from database.models.user import User, Role, UserPagePermission
from core.permission_map import PAGE_DEFINITIONS
from modules.development.error_handler import ErrorHandler


class UserDialog(QDialog):
    """Kullanıcı Ekleme/Düzenleme Dialogu"""

    def __init__(self, parent=None, user_id=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle("Kullanıcı İşlemleri")
        self.setMinimumWidth(500)
        self.setMinimumHeight(600)

        self.setup_ui()
        if user_id:
            self.load_user_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Sekmeli yapı
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Genel Bilgiler Sekmesi
        self.general_tab = QWidget()
        self.setup_general_tab()
        self.tabs.addTab(self.general_tab, "Genel Bilgiler")

        # Roller Sekmesi
        self.roles_tab = QWidget()
        self.setup_roles_tab()
        self.tabs.addTab(self.roles_tab, "Roller")

        # Sayfa İzinleri Sekmesi
        self.pages_tab = QWidget()
        self.setup_page_permissions_tab()
        self.tabs.addTab(self.pages_tab, "Sayfa İzinleri")

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("İptal")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("Kaydet")
        self.btn_save.clicked.connect(self.save_user)
        self.btn_save.setStyleSheet("background-color: #2ecc71; color: white;")
        btn_layout.addWidget(self.btn_save)

        layout.addLayout(btn_layout)

    def setup_general_tab(self):
        layout = QFormLayout(self.general_tab)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Personel Seçimi (Sadece yeni kayıtta aktif)
        if not self.user_id:
            self.cmb_employee = QComboBox()
            self.cmb_employee.setEditable(True)  # Arama yapılabilir
            self.cmb_employee.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
            self.cmb_employee.setPlaceholderText("Personel Ara (İsim veya Sicil No)")
            self.cmb_employee.currentIndexChanged.connect(self.on_employee_selected)
            layout.addRow("Personel Seç:", self.cmb_employee)
            self.load_employees()

        self.inp_username = QLineEdit()
        layout.addRow("Kullanıcı Adı:", self.inp_username)

        self.inp_email = QLineEdit()
        layout.addRow("E-posta:", self.inp_email)

        self.inp_first_name = QLineEdit()
        layout.addRow("Ad:", self.inp_first_name)

        self.inp_last_name = QLineEdit()
        layout.addRow("Soyad:", self.inp_last_name)

        # Varolan kayıt düzenleniyorsa veya personel seçilirse bu alanları kilitleyeceğiz
        if self.user_id:
            self.inp_username.setReadOnly(True)

        self.inp_password = QLineEdit()
        self.inp_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_password.setPlaceholderText(
            "Değiştirmek için doldurun" if self.user_id else ""
        )
        layout.addRow("Şifre:", self.inp_password)

        self.chk_active = QCheckBox("Hesap Aktif")
        self.chk_active.setChecked(True)
        layout.addRow("", self.chk_active)

        self.chk_superuser = QCheckBox("Süper Admin")
        layout.addRow("", self.chk_superuser)

    def load_employees(self):
        """Kullanıcı hesabı olmayan personelleri yükle"""
        if self.user_id:
            return

        session = get_session()
        try:
            from database.models.hr import Employee

            # Kullanıcı hesabı olmayan aktif çalışanları getir
            employees = (
                session.query(Employee)
                .filter(Employee.user_id == None, Employee.is_active == True)
                .all()
            )

            self.cmb_employee.clear()
            self.cmb_employee.addItem("Seçiniz...", None)

            for emp in employees:
                display_text = f"{emp.full_name} ({emp.employee_no})"
                self.cmb_employee.addItem(display_text, emp.id)

            # Arama tamamlama özelliği
            completer = QCompleter(
                [
                    self.cmb_employee.itemText(i)
                    for i in range(self.cmb_employee.count())
                ]
            )
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self.cmb_employee.setCompleter(completer)

        finally:
            session.close()

    def on_employee_selected(self, index):
        """Personel seçildiğinde form alanlarını doldur"""
        emp_id = self.cmb_employee.currentData()
        if not emp_id:
            return

        session = get_session()
        try:
            from database.models.hr import Employee

            emp = session.query(Employee).get(emp_id)
            if emp:
                self.inp_first_name.setText(emp.first_name)
                self.inp_last_name.setText(emp.last_name)
                self.inp_email.setText(emp.email or "")

                # Kullanıcı adı önerisi: isim.soyisim
                username_base = f"{emp.first_name}.{emp.last_name}".lower()

                # Türkçe karakterleri değiştir
                tr_map = {
                    "ç": "c",
                    "ğ": "g",
                    "ı": "i",
                    "ö": "o",
                    "ş": "s",
                    "ü": "u",
                    " ": "",
                }
                username_clean = username_base
                for char, replacement in tr_map.items():
                    username_clean = username_clean.replace(char, replacement)

                self.inp_username.setText(username_clean)

                # Alanları salt okunur yap (tutarlılık için)
                self.inp_first_name.setReadOnly(True)
                self.inp_last_name.setReadOnly(True)
                if emp.email:
                    self.inp_email.setReadOnly(True)

        finally:
            session.close()

    def setup_roles_tab(self):
        layout = QVBoxLayout(self.roles_tab)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        self.role_layout = QVBoxLayout(content)

        # Rolleri veritabanından çek
        session = get_session()
        try:
            roles = session.query(Role).all()
            self.role_checks = {}
            for role in roles:
                chk = QCheckBox(f"{role.name} ({role.code})")
                chk.setToolTip(role.description)
                self.role_layout.addWidget(chk)
                self.role_checks[role.id] = chk
        finally:
            session.close()

        self.role_layout.addStretch()

    def setup_page_permissions_tab(self):
        """Sayfa izinleri sekmesini oluşturur - modüller gruplu, sayfalar checkbox"""
        layout = QVBoxLayout(self.pages_tab)

        # Açıklama
        info_label = QLabel(
            "Kullanıcının rolü dışında ek olarak erişim " "vereceğiniz sayfaları seçin:"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #888; margin-bottom: 10px;")
        layout.addWidget(info_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        self.page_layout = QVBoxLayout(content)

        # Modülleri ve sayfaları listele
        self.page_checks = {}  # page_id -> QCheckBox

        for module_key, module_data in PAGE_DEFINITIONS.items():
            # Modül başlığı
            module_label = QLabel(f"📁 {module_data['name']}")
            module_label.setStyleSheet(
                "font-weight: bold; font-size: 13px; margin-top: 10px; color: #3498db;"
            )
            self.page_layout.addWidget(module_label)

            # Sayfalar (girintili)
            for page_id, page_name in module_data["pages"]:
                chk = QCheckBox(f"    {page_name}")
                chk.setToolTip(f"Sayfa ID: {page_id}")
                self.page_layout.addWidget(chk)
                self.page_checks[page_id] = chk

        self.page_layout.addStretch()

    def load_user_data(self):
        if not self.user_id:
            return

        session = get_session()
        try:
            user = session.query(User).get(self.user_id)
            if user:
                self.inp_username.setText(user.username)
                self.inp_username.setReadOnly(True)  # Kullanıcı adı değişmez
                self.inp_email.setText(user.email)
                self.inp_first_name.setText(user.first_name)
                self.inp_last_name.setText(user.last_name)
                self.chk_active.setChecked(user.is_active)
                self.chk_superuser.setChecked(user.is_superuser)

                # Rolleri işaretle
                user_role_ids = [r.id for r in user.roles]
                for rid, chk in self.role_checks.items():
                    if rid in user_role_ids:
                        chk.setChecked(True)

                # Sayfa izinlerini işaretle
                user_page_ids = [p.page_id for p in user.page_permissions]
                for page_id, chk in self.page_checks.items():
                    if page_id in user_page_ids:
                        chk.setChecked(True)
        finally:
            session.close()

    def save_user(self):
        if not self.inp_username.text() or not self.inp_email.text():
            show_toast("Kullanıcı adı ve e-posta zorunludur.", "WARNING")
            return

        session = get_session()
        try:
            if self.user_id:
                user = session.query(User).get(self.user_id)
            else:
                # Yeni kullanıcı kontrolü
                existing = (
                    session.query(User)
                    .filter(User.username == self.inp_username.text())
                    .first()
                )
                if existing:
                    show_toast("Bu kullanıcı adı zaten kullanılıyor.", "WARNING")
                    return

                user = User(username=self.inp_username.text())
                session.add(user)

            # Bilgileri güncelle
            user.email = self.inp_email.text()
            user.first_name = self.inp_first_name.text()
            user.last_name = self.inp_last_name.text()
            user.is_active = self.chk_active.isChecked()
            user.is_superuser = self.chk_superuser.isChecked()

            # Şifre güncelleme
            password = self.inp_password.text()
            if password:
                if len(password) < 6:
                    show_toast("Şifre en az 6 karakter olmalıdır.", "WARNING")
                    return
                user.set_password(password)
            elif not self.user_id:
                show_toast("Yeni kullanıcı için şifre zorunludur.", "WARNING")
                return

            # Rolleri güncelle
            user.roles = []
            for rid, chk in self.role_checks.items():
                if chk.isChecked():
                    role = session.query(Role).get(rid)
                    user.roles.append(role)

            # Önce commit yaparak user.id'nin oluşmasını sağla
            session.flush()

            # Yeni kullanıcı ise personelle ilişkilendir
            if not self.user_id:
                emp_id = self.cmb_employee.currentData()
                if not emp_id:
                    show_toast("Lütfen bir personel seçiniz.", "WARNING")
                    return

                from database.models.hr import Employee

                employee = session.query(Employee).get(emp_id)
                if employee:
                    employee.user_id = user.id
                    session.add(employee)

            # Sayfa izinlerini güncelle
            # Mevcut izinleri sil
            session.query(UserPagePermission).filter(
                UserPagePermission.user_id == user.id
            ).delete()

            # Yeni izinleri ekle
            from core.user_context import get_current_user

            current_user = get_current_user()
            granter_id = current_user.user_id if current_user else None

            for page_id, chk in self.page_checks.items():
                if chk.isChecked():
                    perm = UserPagePermission(
                        user_id=user.id,
                        page_id=page_id,
                        granted_by=granter_id,
                    )
                    session.add(perm)

            session.commit()
            self.accept()

        except Exception as e:
            session.rollback()
            ErrorHandler.handle_error(
                e,
                module="system",
                screen="UserDialog",
                function="save_user",
                parent_widget=self,
            )
        finally:
            session.close()


class UserManagement(QWidget):
    """Kullanıcı Yönetimi Ana Ekranı"""

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.refresh_list()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Başlık ve Butonlar
        top_layout = QHBoxLayout()

        title = QLabel("Kullanıcı Yönetimi")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        top_layout.addWidget(title)

        top_layout.addStretch()

        self.btn_refresh = QPushButton("Yenile")
        self.btn_refresh.setIcon(qta.icon(ICONS.REFRESH))
        self.btn_refresh.clicked.connect(self.refresh_list)
        top_layout.addWidget(self.btn_refresh)

        self.btn_add = QPushButton("Yeni Kullanıcı")
        self.btn_add.setIcon(qta.icon(ICONS.PLUS))
        self.btn_add.setStyleSheet("background-color: #3498db; color: white;")
        self.btn_add.clicked.connect(self.add_user)
        top_layout.addWidget(self.btn_add)

        layout.addLayout(top_layout)

        # Liste
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Kullanıcı Adı", "Ad Soyad", "E-posta", "Roller", "Durum", "İşlem"]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 120)
        self.table.verticalHeader().setDefaultSectionSize(50)

        self.table.cellDoubleClicked.connect(self.edit_user_from_table)

        layout.addWidget(self.table)

    def refresh_list(self):
        self.table.setRowCount(0)
        session = get_session()
        try:
            users = session.query(User).all()
            self.table.setRowCount(len(users))

            for i, user in enumerate(users):
                self.table.setItem(i, 0, QTableWidgetItem(str(user.id)))
                self.table.setItem(i, 1, QTableWidgetItem(user.username))
                self.table.setItem(i, 2, QTableWidgetItem(user.full_name))
                self.table.setItem(i, 3, QTableWidgetItem(user.email))

                roles = ", ".join([r.name for r in user.roles])
                self.table.setItem(i, 4, QTableWidgetItem(roles))

                t = get_theme()
                status_item = QTableWidgetItem()
                if user.is_active:
                    status_item.setText("Aktif")
                    status_item.setIcon(
                        qta.icon(ICONS.STATUS_ICONS["active"], color=t.success)
                    )
                    status_item.setForeground(QColor(t.success))
                else:
                    status_item.setText("Pasif")
                    status_item.setIcon(
                        qta.icon(ICONS.STATUS_ICONS["passive"], color=t.text_muted)
                    )
                    status_item.setForeground(QColor(t.text_muted))
                self.table.setItem(i, 5, status_item)

                # İşlem butonları
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(0, 0, 0, 0)
                btn_layout.setSpacing(8)
                btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

                edit_btn = QPushButton()
                edit_btn.setIcon(qta.icon(ICONS.EDIT, color="#3498db"))
                edit_btn.setFixedSize(32, 32)
                edit_btn.setToolTip("Düzenle")
                edit_btn.clicked.connect(
                    lambda checked, uid=user.id: self.edit_user(uid)
                )
                btn_layout.addWidget(edit_btn)

                del_btn = QPushButton()
                del_btn.setIcon(qta.icon(ICONS.DELETE, color="#ef4444"))
                del_btn.setFixedSize(32, 32)
                del_btn.setToolTip("Sil")
                del_btn.clicked.connect(
                    lambda checked, uid=user.id, uname=user.username: self.delete_user(
                        uid, uname
                    )
                )
                btn_layout.addWidget(del_btn)

                self.table.setCellWidget(i, 6, btn_widget)

        finally:
            session.close()

    def add_user(self):
        dialog = UserDialog(self)
        if dialog.exec():
            self.refresh_list()

    def edit_user_from_table(self, row, col):
        user_id = int(self.table.item(row, 0).text())
        self.edit_user(user_id)

    def edit_user(self, user_id):
        dialog = UserDialog(self, user_id)
        if dialog.exec():
            self.refresh_list()

    def delete_user(self, user_id: int, username: str):
        """Kullanıcıyı sil"""
        # Mevcut kullanıcının kendisini silmesini engelle
        from core.user_context import get_current_user

        current_user = get_current_user()
        if current_user and current_user.user_id == user_id:
            show_toast("Kendinizi silemezsiniz!", "WARNING")
            return

        if username == "admin":
            show_toast("Admin kullanıcısı silinemez!", "WARNING")
            return

        session = get_session()
        try:
            # Çalışan ilişkisini kontrol et
            from database.models.hr import Employee

            linked_employee = (
                session.query(Employee).filter(Employee.user_id == user_id).first()
            )

            msg = f"'{username}' kullanıcısını silmek istediğinize emin misiniz?"
            if linked_employee:
                msg += (
                    f"\n\nUYARI: Bu kullanıcı '{linked_employee.full_name}' personeli ile ilişkilidir.\n"
                    "Silme işlemi onaylanırsa personel kaydının kullanıcı bağlantısı kaldırılacak, "
                    "ancak personel SİLİNMEYECEKTİR."
                )

            msg += "\n\nBu işlem geri alınamaz!"

            # Onay dialogu
            reply = QMessageBox.question(
                self,
                "Kullanıcı Silme",
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

            user = session.query(User).get(user_id)
            if not user:
                show_toast("Kullanıcı bulunamadı.", "WARNING")
                return

            # 1. Çalışan bağlantısını kaldır
            if linked_employee:
                linked_employee.user_id = None
                session.add(linked_employee)

            # 2. Üretim Modülü Referanslarını Temizle (Set Null)
            from database.models.production import (
                WorkOrderOperationPersonnel,
                ProductionDowntime,
            )

            session.query(WorkOrderOperationPersonnel).filter(
                WorkOrderOperationPersonnel.user_id == user_id
            ).update({WorkOrderOperationPersonnel.user_id: None})

            session.query(ProductionDowntime).filter(
                ProductionDowntime.operator_id == user_id
            ).update({ProductionDowntime.operator_id: None})

            # 3. Bakım Modülü Referanslarını Temizle (Set Null)
            from database.models.maintenance import (
                MaintenanceRequest,
                MaintenanceWorkOrder,
            )

            session.query(MaintenanceRequest).filter(
                MaintenanceRequest.reported_by_id == user_id
            ).update({MaintenanceRequest.reported_by_id: None})

            session.query(MaintenanceWorkOrder).filter(
                MaintenanceWorkOrder.assigned_to_id == user_id
            ).update({MaintenanceWorkOrder.assigned_to_id: None})

            # 4. Sayfa izinlerini sil
            session.query(UserPagePermission).filter(
                UserPagePermission.user_id == user_id
            ).delete()

            # 5. Kullanıcıyı sil
            session.delete(user)
            session.commit()

            show_toast(
                f"'{username}' kullanıcısı ve ilişkili veriler silindi.", "SUCCESS"
            )
            self.refresh_list()

        except Exception as e:
            session.rollback()
            ErrorHandler.handle_error(
                e,
                module="system",
                screen="UserManagement",
                function="delete_user",
                parent_widget=self,
            )
        finally:
            session.close()
