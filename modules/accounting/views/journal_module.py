"""
Akıllı İş - Yevmiye Modülü
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QMessageBox,
)
import qtawesome as qta

from config.icons import ICONS
from modules.accounting.services import AccountingService
from modules.accounting.views.journal_list import JournalListWidget
from modules.accounting.views.journal_form import JournalFormDialog
from ui.components.page_header import PageHeader


class JournalModule(QWidget):
    """Yevmiye fişi modülü"""

    page_title = "Yevmiye Fişleri"

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
            title="Yevmiye Fişleri",
            icon=ICONS.INVOICE,
            show_search=False,
            show_refresh=True,
            show_add=True,
            add_text="Yeni Yevmiye",
            parent=self,
        )
        self.header.refresh_clicked.connect(self.load_data)
        self.header.add_clicked.connect(self._new_journal)
        layout.addWidget(self.header)

        # Liste
        self.list_widget = JournalListWidget()
        self.list_widget.journal_double_clicked.connect(self._view_journal)
        self.list_widget.refresh_requested.connect(self.load_data)
        layout.addWidget(self.list_widget)

        # Alt butonlar
        footer = QHBoxLayout()
        post_btn = QPushButton("Deftere İşle")
        post_btn.setIcon(qta.icon(ICONS.CHECK, color="#ffffff"))
        post_btn.setProperty("class", "btn-primary")
        post_btn.setFixedHeight(36)
        post_btn.clicked.connect(self._post_journal)
        footer.addWidget(post_btn)

        cancel_btn = QPushButton("İptal Et")
        cancel_btn.setIcon(qta.icon(ICONS.CLOSE, color="#ffffff"))
        cancel_btn.setProperty("class", "btn-danger")
        cancel_btn.setFixedHeight(36)
        cancel_btn.clicked.connect(self._cancel_journal)
        footer.addWidget(cancel_btn)

        footer.addStretch()
        layout.addLayout(footer)

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
            filters = self.list_widget.get_filters()
            journals = service.get_all_journals(**filters)
            self.list_widget.load_journals(journals)
        except Exception as e:
            QMessageBox.warning(
                self, "Uyarı", f"Yevmiyeler yüklenirken hata:\n{str(e)}"
            )
        finally:
            self._close_service()

    def _new_journal(self):
        """Yeni yevmiye"""
        dialog = JournalFormDialog(parent=self)
        if dialog.exec():
            self.load_data()

    def _view_journal(self, journal_id: int):
        """Yevmiye görüntüle"""
        dialog = JournalFormDialog(journal_id=journal_id, parent=self)
        if dialog.exec():
            self.load_data()

    def _post_journal(self):
        """Deftere işle"""
        journal_id = self.list_widget.get_selected_journal_id()
        if not journal_id:
            QMessageBox.warning(self, "Uyarı", "Bir yevmiye seçin!")
            return

        msg = "Seçili yevmiye fişi deftere işlenecek.\n\nİşlendikten sonra değiştirilemez. Devam edilsin mi?"
        reply = QMessageBox.question(
            self,
            "Onay",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                service = self._get_service()
                service.post_journal(journal_id)
                self.load_data()
                QMessageBox.information(self, "Bilgi", "Yevmiye fişi deftere işlendi!")
            except ValueError as e:
                QMessageBox.warning(self, "Uyarı", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"İşlem sırasında hata:\n{str(e)}")
            finally:
                self._close_service()

    def _cancel_journal(self):
        """İptal et"""
        journal_id = self.list_widget.get_selected_journal_id()
        if not journal_id:
            QMessageBox.warning(self, "Uyarı", "Bir yevmiye seçin!")
            return

        msg = "Seçili yevmiye fişi iptal edilecek.\n\nDevam edilsin mi?"
        reply = QMessageBox.question(
            self,
            "Onay",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                service = self._get_service()
                service.cancel_journal(journal_id, "Kullanıcı tarafından iptal")
                self.load_data()
                QMessageBox.information(self, "Bilgi", "Yevmiye fişi iptal edildi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"İptal sırasında hata:\n{str(e)}")
            finally:
                self._close_service()
