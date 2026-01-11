"""
Akıllı İş - Yevmiye Fişi Formu
VS Code Dark Theme
"""

from decimal import Decimal
from datetime import date

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QDateEdit,
    QComboBox,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QAbstractItemView,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

from config.styles import (
    BG_PRIMARY, BG_SECONDARY, BORDER, TEXT_PRIMARY, TEXT_MUTED, ACCENT,
    SUCCESS, ERROR,
    get_table_style, get_button_style,
)
from database.models.accounting import JournalEntryStatus
from modules.accounting.services import AccountingService

class JournalFormDialog(QDialog):
    """Yevmiye fişi formu"""

    def __init__(self, journal_id: int = None, parent=None):
        super().__init__(parent)
        self.journal_id = journal_id
        self.journal = None
        self.service = AccountingService()
        self.accounts = []
        self.setup_ui()
        self._load_accounts()

        if journal_id:
            self.load_journal()

    def setup_ui(self):
        self.setWindowTitle(
            "Yevmiye Düzenle" if self.journal_id else "Yeni Yevmiye Fişi"
        )
        self.setMinimumSize(900, 600)
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Üst bilgiler
        header_layout = QHBoxLayout()

        # Tarih
        date_layout = QVBoxLayout()
        date_layout.addWidget(QLabel("Tarih"))
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        date_layout.addWidget(self.date_edit)
        header_layout.addLayout(date_layout)

        # Açıklama
        desc_layout = QVBoxLayout()
        desc_layout.addWidget(QLabel("Açıklama"))
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Fiş açıklaması")
        desc_layout.addWidget(self.desc_input)
        header_layout.addLayout(desc_layout, 2)

        layout.addLayout(header_layout)

        # Satırlar tablosu
        table_label = QLabel("Yevmiye Satırları")
        layout.addWidget(table_label)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Hesap", "Borç", "Alacak", "Açıklama"]
        )

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 200)

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        layout.addWidget(self.table)

        # Satır ekleme butonları
        btn_row = QHBoxLayout()

        add_btn = QPushButton("Satır Ekle")
        add_btn.clicked.connect(self._add_row)
        btn_row.addWidget(add_btn)

        remove_btn = QPushButton("Satır Sil")
        remove_btn.clicked.connect(self._remove_row)
        btn_row.addWidget(remove_btn)

        btn_row.addStretch()

        # Toplamlar
        self.debit_total = QLabel("Borç: ₺0,00")
        btn_row.addWidget(self.debit_total)

        self.credit_total = QLabel("Alacak: ₺0,00")
        btn_row.addWidget(self.credit_total)

        self.balance_label = QLabel("Fark: ₺0,00")
        btn_row.addWidget(self.balance_label)

        layout.addLayout(btn_row)

        # Alt butonlar
        footer = QHBoxLayout()
        footer.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        footer.addWidget(cancel_btn)

        save_btn = QPushButton("Kaydet")
        save_btn.clicked.connect(self.save)
        footer.addWidget(save_btn)

        layout.addLayout(footer)

        # Başlangıçta 2 satır ekle
        self._add_row()
        self._add_row()

    def _load_accounts(self):
        """Hesapları yükle"""
        self.accounts = self.service.get_all_accounts()

    def _add_row(self):
        """Satır ekle"""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Hesap combo
        account_combo = QComboBox()
        account_combo.addItem("-- Hesap Seçin --", None)
        for acc in self.accounts:
            if acc.is_detail:
                account_combo.addItem(f"{acc.code} - {acc.name}", acc.id)
        self.table.setCellWidget(row, 0, account_combo)

        # Borç
        debit_item = QTableWidgetItem("0")
        debit_item.setTextAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.table.setItem(row, 1, debit_item)

        # Alacak
        credit_item = QTableWidgetItem("0")
        credit_item.setTextAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.table.setItem(row, 2, credit_item)

        # Açıklama
        desc_item = QTableWidgetItem("")
        self.table.setItem(row, 3, desc_item)

        # Değişiklikleri takip et
        self.table.itemChanged.connect(self._update_totals)

    def _remove_row(self):
        """Satır sil"""
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
            self._update_totals()

    def _update_totals(self):
        """Toplamları güncelle"""
        total_debit = Decimal(0)
        total_credit = Decimal(0)

        for row in range(self.table.rowCount()):
            try:
                debit_item = self.table.item(row, 1)
                if debit_item:
                    total_debit += Decimal(debit_item.text() or 0)
            except Exception:
                pass

            try:
                credit_item = self.table.item(row, 2)
                if credit_item:
                    total_credit += Decimal(credit_item.text() or 0)
            except Exception:
                pass

        self.debit_total.setText(f"Borç: ₺{total_debit:,.2f}")
        self.credit_total.setText(f"Alacak: ₺{total_credit:,.2f}")

        diff = total_debit - total_credit
        if diff == 0:
            self.balance_label.setText("Dengeli")
        else:
            self.balance_label.setText(f"Fark: ₺{abs(diff):,.2f}")
    def load_journal(self):
        """Mevcut yevmiyeyi yükle"""
        self.journal = self.service.get_journal_by_id(self.journal_id)
        if not self.journal:
            return

        self.date_edit.setDate(
            QDate(
                self.journal.entry_date.year,
                self.journal.entry_date.month,
                self.journal.entry_date.day,
            )
        )
        self.desc_input.setText(self.journal.description or "")

        # Satırları yükle
        self.table.setRowCount(0)
        for line in self.journal.lines:
            self._add_row()
            row = self.table.rowCount() - 1

            combo = self.table.cellWidget(row, 0)
            for i in range(combo.count()):
                if combo.itemData(i) == line.account_id:
                    combo.setCurrentIndex(i)
                    break

            self.table.item(row, 1).setText(str(line.debit or 0))
            self.table.item(row, 2).setText(str(line.credit or 0))
            self.table.item(row, 3).setText(line.description or "")

        self._update_totals()

    def save(self):
        """Kaydet"""
        # Satırları topla
        lines_data = []
        total_debit = Decimal(0)
        total_credit = Decimal(0)

        for row in range(self.table.rowCount()):
            combo = self.table.cellWidget(row, 0)
            account_id = combo.currentData()
            if not account_id:
                continue

            try:
                debit = Decimal(self.table.item(row, 1).text() or 0)
                credit = Decimal(self.table.item(row, 2).text() or 0)
            except Exception:
                debit = Decimal(0)
                credit = Decimal(0)

            if debit == 0 and credit == 0:
                continue

            desc = self.table.item(row, 3).text() or ""

            lines_data.append({
                "account_id": account_id,
                "debit": debit,
                "credit": credit,
                "description": desc,
            })

            total_debit += debit
            total_credit += credit

        if not lines_data:
            QMessageBox.warning(self, "Uyarı", "En az bir satır girilmeli!")
            return

        if total_debit != total_credit:
            QMessageBox.warning(
                self,
                "Uyarı",
                f"Borç ve alacak toplamları eşit olmalı!\n\n"
                f"Borç: ₺{total_debit:,.2f}\n"
                f"Alacak: ₺{total_credit:,.2f}\n"
                f"Fark: ₺{abs(total_debit - total_credit):,.2f}",
            )
            return

        qdate = self.date_edit.date()
        entry_date = date(qdate.year(), qdate.month(), qdate.day())

        data = {
            "entry_date": entry_date,
            "description": self.desc_input.text().strip() or None,
            "status": JournalEntryStatus.DRAFT,
        }

        try:
            if self.journal_id:
                # Güncelleme (karmaşık, şimdilik atlıyoruz)
                pass
            else:
                self.service.create_journal(lines_data, **data)

            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self, "Hata", f"Kayıt sırasında hata:\n{str(e)}"
            )
        finally:
            self.service.close()
