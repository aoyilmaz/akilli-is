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
    QComboBox,
    QFormLayout,
    QMessageBox,
    QCheckBox,
    QScrollArea,
    QFrame,
    QTabWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
import qtawesome as qta

from database.base import get_session
from database.models.user import User, Role
from config.themes import get_theme


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

        self.inp_username = QLineEdit()
        layout.addRow("Kullanıcı Adı:", self.inp_username)

        self.inp_email = QLineEdit()
        layout.addRow("E-posta:", self.inp_email)

        self.inp_first_name = QLineEdit()
        layout.addRow("Ad:", self.inp_first_name)

        self.inp_last_name = QLineEdit()
        layout.addRow("Soyad:", self.inp_last_name)

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
        finally:
            session.close()

    def save_user(self):
        if not self.inp_username.text() or not self.inp_email.text():
            QMessageBox.warning(self, "Hata", "Kullanıcı adı ve e-posta zorunludur.")
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
                    QMessageBox.warning(
                        self, "Hata", "Bu kullanıcı adı zaten kullanılıyor."
                    )
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
                    QMessageBox.warning(
                        self, "Hata", "Şifre en az 6 karakter olmalıdır."
                    )
                    return
                user.set_password(password)
            elif not self.user_id:
                QMessageBox.warning(
                    self, "Hata", "Yeni kullanıcı için şifre zorunludur."
                )
                return

            # Rolleri güncelle
            user.roles = []
            for rid, chk in self.role_checks.items():
                if chk.isChecked():
                    role = session.query(Role).get(rid)
                    user.roles.append(role)

            session.commit()
            self.accept()

        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Hata", f"Kayıt hatası: {str(e)}")
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
        self.btn_refresh.setIcon(qta.icon("fa5s.sync"))
        self.btn_refresh.clicked.connect(self.refresh_list)
        top_layout.addWidget(self.btn_refresh)

        self.btn_add = QPushButton("Yeni Kullanıcı")
        self.btn_add.setIcon(qta.icon("fa5s.plus"))
        self.btn_add.setStyleSheet("background-color: #3498db; color: white;")
        self.btn_add.clicked.connect(self.add_user)
        top_layout.addWidget(self.btn_add)

        layout.addLayout(top_layout)

        # Liste
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Kullanıcı Adı", "Ad Soyad", "E-posta", "Roller", "Durum"]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

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

                status = "Aktif" if user.is_active else "Pasif"
                item = QTableWidgetItem(status)
                if user.is_active:
                    item.setForeground(Qt.GlobalColor.green)
                else:
                    item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(i, 5, item)

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
