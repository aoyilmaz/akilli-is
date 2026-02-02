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
import qtawesome as qta

from config.icons import ICONS
from modules.accounting.services import AccountingService
from modules.accounting.views.account_tree import AccountTreeWidget
from modules.accounting.views.account_form import AccountFormDialog
from ui.components.page_header import PageHeader


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

        # Header
        self.header = PageHeader(
            title="Hesap Planı",
            icon=ICONS.FINANCE,
            show_search=False,
            show_add=True,
            add_text="Yeni Hesap",
            parent=self,
        )
        self.header.refresh_clicked.connect(self.load_data)
        self.header.add_clicked.connect(self._new_account)

        # Custom Action Buttons (Seed)
        h_layout = self.header.header_layout()
        seed_btn = QPushButton("Tekdüzen Yükle")
        seed_btn.setIcon(qta.icon(ICONS.INVOICE, color="#ffffff"))
        seed_btn.setProperty("class", "btn-secondary")
        seed_btn.setToolTip("Tekdüzen Hesap Planı Yükle")
        seed_btn.setFixedHeight(36)
        seed_btn.clicked.connect(self._seed_accounts)

        # Add before standard buttons
        target_idx = h_layout.count() - 2
        h_layout.insertWidget(max(0, target_idx), seed_btn)

        layout.addWidget(self.header)

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
        msg = "Türkiye Tekdüzen Hesap Planı temel hesapları yüklenecek.\n\nMevcut hesaplar varsa atlanır.\n\nDevam edilsin mi?"
        reply = QMessageBox.question(
            self,
            "Onay",
            msg,
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
