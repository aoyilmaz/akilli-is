"""
Akıllı İş - Hesap Kartı Formu
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QTextEdit,
    QCheckBox,
    QPushButton,
    QLabel,
    QMessageBox,
    QFrame,
)
from PyQt6.QtCore import Qt

from config.styles import (
    BG_PRIMARY,
    BG_SECONDARY,
    BG_TERTIARY,
    BG_HOVER,
    BORDER,
    TEXT_PRIMARY,
    TEXT_MUTED,
    ACCENT,
    INPUT_BG,
    INPUT_BORDER,
    get_button_style,
    get_input_style,
    get_dialog_style,
    BTN_HEIGHT_NORMAL,
    ICONS,
)
from database.models.accounting import Account, AccountType
from modules.accounting.services import AccountingService


class AccountFormDialog(QDialog):
    """Hesap kartı formu"""

    def __init__(self, account_id: int = None, parent=None):
        super().__init__(parent)
        self.account_id = account_id
        self.account = None
        self.service = AccountingService()
        self.setup_ui()

        if account_id:
            self.load_account()

    def setup_ui(self):
        self.setWindowTitle("Hesap Duzenle" if self.account_id else "Yeni Hesap")
        self.setMinimumWidth(500)
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Form
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Hesap Kodu
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Örn: 120, 320.01")
        form.addRow("Hesap Kodu:", self.code_input)

        # Hesap Adı
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Hesap adı")
        form.addRow("Hesap Adı:", self.name_input)

        # Hesap Türü
        self.type_combo = QComboBox()
        self.type_combo.addItem("Varlık (1-2)", AccountType.ASSET)
        self.type_combo.addItem("Borç (3-4)", AccountType.LIABILITY)
        self.type_combo.addItem("Özkaynak (5)", AccountType.EQUITY)
        self.type_combo.addItem("Gelir (6)", AccountType.REVENUE)
        self.type_combo.addItem("Gider (6)", AccountType.EXPENSE)
        self.type_combo.addItem("Maliyet (7)", AccountType.COST)
        form.addRow("Hesap Türü:", self.type_combo)

        # Üst Hesap
        self.parent_combo = QComboBox()
        self.parent_combo.addItem("-- Üst Hesap Yok --", None)
        self._load_parent_accounts()
        form.addRow("Üst Hesap:", self.parent_combo)

        # Seviye
        self.level_combo = QComboBox()
        self.level_combo.addItem("1 - Ana Grup", 1)
        self.level_combo.addItem("2 - Alt Grup", 2)
        self.level_combo.addItem("3 - Detay Hesap", 3)
        form.addRow("Seviye:", self.level_combo)

        # Detay hesap mı?
        self.detail_check = QCheckBox("Bakiye kaydı yapılabilir (Detay)")
        self.detail_check.setChecked(True)
        form.addRow("", self.detail_check)

        # Aktif mi?
        self.active_check = QCheckBox("Aktif")
        self.active_check.setChecked(True)
        form.addRow("", self.active_check)

        # Açıklama
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(80)
        self.desc_input.setPlaceholderText("Açıklama (opsiyonel)")
        form.addRow("Açıklama:", self.desc_input)

        layout.addLayout(form)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton(f"{ICONS['cancel']} İptal")
        cancel_btn.setStyleSheet(get_button_style("cancel"))
        cancel_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton(f"{ICONS['save']} Kaydet")
        save_btn.setStyleSheet(get_button_style("save"))
        save_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _load_parent_accounts(self):
        """Üst hesap listesi"""
        accounts = self.service.get_all_accounts()
        for account in accounts:
            if not account.is_detail:  # Sadece grup hesapları
                self.parent_combo.addItem(
                    f"{account.code} - {account.name}", account.id
                )

    def load_account(self):
        """Hesap verilerini yükle"""
        self.account = self.service.get_account_by_id(self.account_id)
        if not self.account:
            return

        self.code_input.setText(self.account.code)
        self.name_input.setText(self.account.name)

        # Tür
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == self.account.account_type:
                self.type_combo.setCurrentIndex(i)
                break

        # Üst hesap
        if self.account.parent_id:
            for i in range(self.parent_combo.count()):
                if self.parent_combo.itemData(i) == self.account.parent_id:
                    self.parent_combo.setCurrentIndex(i)
                    break

        # Seviye
        self.level_combo.setCurrentIndex(self.account.level - 1)

        self.detail_check.setChecked(self.account.is_detail)
        self.active_check.setChecked(self.account.is_active)
        self.desc_input.setPlainText(self.account.description or "")

    def save(self):
        """Kaydet"""
        code = self.code_input.text().strip()
        name = self.name_input.text().strip()

        if not code:
            QMessageBox.warning(self, "Uyarı", "Hesap kodu zorunludur!")
            return

        if not name:
            QMessageBox.warning(self, "Uyarı", "Hesap adı zorunludur!")
            return

        # Kod kontrolü
        existing = self.service.get_account_by_code(code)
        if existing and (not self.account_id or existing.id != self.account_id):
            QMessageBox.warning(self, "Uyarı", f"'{code}' kodlu hesap zaten mevcut!")
            return

        data = {
            "code": code,
            "name": name,
            "account_type": self.type_combo.currentData(),
            "parent_id": self.parent_combo.currentData(),
            "level": self.level_combo.currentData(),
            "is_detail": self.detail_check.isChecked(),
            "is_active": self.active_check.isChecked(),
            "description": self.desc_input.toPlainText().strip() or None,
        }

        try:
            if self.account_id:
                self.service.update_account(self.account_id, data)
            else:
                self.service.create_account(data)

            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt sırasında hata:\n{str(e)}")
        finally:
            self.service.close()
