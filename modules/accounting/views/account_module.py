"""
Akıllı İş - Hesap Planı Ana Modülü
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFrame,
    QMessageBox,
    QLabel,
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
    SUCCESS,
    get_button_style,
    get_title_style,
    BTN_HEIGHT_NORMAL,
    ICONS,
)
from modules.accounting.services import AccountingService
from modules.accounting.views.account_tree import AccountTreeWidget
from modules.accounting.views.account_form import AccountFormDialog


class AccountModule(QWidget):
    """Hesap planı yönetim modülü"""

    page_title = "Hesap Planı"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Baslik
        header = QHBoxLayout()

        title = QLabel("Hesap Plani")
        header.addWidget(title)

        header.addStretch()

        # Seed butonu
        seed_btn = QPushButton(f"{ICONS['import']} Tekdüzen Hesap Planı Yükle")
        seed_btn.setStyleSheet(get_button_style("import"))
        seed_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        seed_btn.clicked.connect(self._seed_accounts)
        header.addWidget(seed_btn)

        # Yeni hesap
        new_btn = QPushButton(f"{ICONS['add']} Yeni Hesap")
        new_btn.setStyleSheet(get_button_style("add"))
        new_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        new_btn.clicked.connect(self._new_account)
        header.addWidget(new_btn)

        layout.addLayout(header)

        # Ağaç widget
        self.tree_widget = AccountTreeWidget()
        self.tree_widget.account_double_clicked.connect(self._edit_account)
        layout.addWidget(self.tree_widget)

    def _get_service(self):
        if self.service is None:
            self.service = AccountingService()
        return self.service

    def _close_service(self):
        if self.service:
            self.service.close()
            self.service = None

    def load_data(self):
        """Verileri yükle"""
        try:
            service = self._get_service()
            accounts = service.get_all_accounts()
            self.tree_widget.load_accounts(accounts)
        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Hesaplar yüklenirken hata:\n{str(e)}")
        finally:
            self._close_service()

    def _new_account(self):
        """Yeni hesap"""
        dialog = AccountFormDialog(parent=self)
        if dialog.exec():
            self.load_data()

    def _edit_account(self, account_id: int):
        """Hesap düzenle"""
        dialog = AccountFormDialog(account_id=account_id, parent=self)
        if dialog.exec():
            self.load_data()

    def _seed_accounts(self):
        """Tekdüzen hesap planı yükle"""
        reply = QMessageBox.question(
            self,
            "Onay",
            "Türkiye Tekdüzen Hesap Planı temel hesapları yüklenecek.\n\n"
            "Mevcut hesaplar varsa atlanır.\n\nDevam edilsin mi?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                service = self._get_service()
                service.seed_chart_of_accounts()
                self.load_data()
                QMessageBox.information(
                    self, "Bilgi", "Hesap planı başarıyla yüklendi!"
                )
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Yükleme sırasında hata:\n{str(e)}")
            finally:
                self._close_service()
