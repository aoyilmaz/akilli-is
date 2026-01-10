"""
Akilli Is - Muhasebe Raporlari Modulu
"""

from datetime import date

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QDateEdit,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QTabWidget,
    QAbstractItemView,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

from config.styles import (
    BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BG_HOVER,
    BORDER, TEXT_PRIMARY, TEXT_MUTED, ACCENT,
    SUCCESS, WARNING, ERROR, INPUT_BG, INPUT_BORDER,
    get_tab_style, get_table_style, get_button_style, get_input_style,
)
from modules.accounting.services import AccountingService


class AccountingReportsModule(QWidget):
    """Muhasebe raporlari modulu - ic menu yok, tab yapisi"""

    page_title = "Muhasebe Raporlari"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(get_tab_style())

        # Buyuk Defter
        self.ledger_page = self._create_ledger_page()
        self.tabs.addTab(self.ledger_page, "Buyuk Defter")

        # Mizan
        self.trial_page = self._create_trial_balance_page()
        self.tabs.addTab(self.trial_page, "Mizan")

        # Bilanco
        self.balance_page = self._create_balance_sheet_page()
        self.tabs.addTab(self.balance_page, "Bilanco")

        self.tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tabs)

        # Ilk tab icin hesaplari yukle
        self._load_accounts_for_ledger()

    def _create_ledger_page(self) -> QWidget:
        """Büyük defter sayfası"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)

        # Filtreler
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Hesap:"))
        self.ledger_account = QComboBox()
        self.ledger_account.setMinimumWidth(250)
        self._style_combo(self.ledger_account)
        filter_layout.addWidget(self.ledger_account)

        filter_layout.addWidget(QLabel("Başlangıç:"))
        self.ledger_start = QDateEdit()
        self.ledger_start.setDate(QDate.currentDate().addMonths(-1))
        self.ledger_start.setCalendarPopup(True)
        self._style_date(self.ledger_start)
        filter_layout.addWidget(self.ledger_start)

        filter_layout.addWidget(QLabel("Bitiş:"))
        self.ledger_end = QDateEdit()
        self.ledger_end.setDate(QDate.currentDate())
        self.ledger_end.setCalendarPopup(True)
        self._style_date(self.ledger_end)
        filter_layout.addWidget(self.ledger_end)

        gen_btn = QPushButton("Rapor Olustur")
        gen_btn.setStyleSheet(get_button_style("primary"))
        gen_btn.clicked.connect(self._generate_ledger)
        filter_layout.addWidget(gen_btn)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Ozet
        self.ledger_summary = QLabel()
        self.ledger_summary.setStyleSheet(f"color: {TEXT_MUTED}; padding: 10px 0;")
        layout.addWidget(self.ledger_summary)

        # Tablo
        self.ledger_table = QTableWidget()
        self.ledger_table.setColumnCount(5)
        self.ledger_table.setHorizontalHeaderLabels(
            ["Tarih", "Fiş No", "Açıklama", "Borç", "Alacak"]
        )
        self._style_table(self.ledger_table)
        layout.addWidget(self.ledger_table)

        return page

    def _create_trial_balance_page(self) -> QWidget:
        """Mizan sayfası"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)

        # Filtre
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Tarih:"))
        self.trial_date = QDateEdit()
        self.trial_date.setDate(QDate.currentDate())
        self.trial_date.setCalendarPopup(True)
        self._style_date(self.trial_date)
        filter_layout.addWidget(self.trial_date)

        gen_btn = QPushButton("Mizan Olustur")
        gen_btn.setStyleSheet(get_button_style("primary"))
        gen_btn.clicked.connect(self._generate_trial_balance)
        filter_layout.addWidget(gen_btn)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Toplam
        self.trial_summary = QLabel()
        self.trial_summary.setStyleSheet(
            f"color: {TEXT_MUTED}; padding: 10px 0; font-size: 14px;"
        )
        layout.addWidget(self.trial_summary)

        # Tablo
        self.trial_table = QTableWidget()
        self.trial_table.setColumnCount(6)
        self.trial_table.setHorizontalHeaderLabels(
            [
                "Hesap Kodu",
                "Hesap Adı",
                "Borç (Dönem)",
                "Alacak (Dönem)",
                "Borç (Bakiye)",
                "Alacak (Bakiye)",
            ]
        )
        self._style_table(self.trial_table)
        layout.addWidget(self.trial_table)

        return page

    def _create_balance_sheet_page(self) -> QWidget:
        """Bilanço sayfası"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)

        # Filtre
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Tarih:"))
        self.balance_date = QDateEdit()
        self.balance_date.setDate(QDate.currentDate())
        self.balance_date.setCalendarPopup(True)
        self._style_date(self.balance_date)
        filter_layout.addWidget(self.balance_date)

        gen_btn = QPushButton("Bilanco Olustur")
        gen_btn.setStyleSheet(get_button_style("primary"))
        gen_btn.clicked.connect(self._generate_balance_sheet)
        filter_layout.addWidget(gen_btn)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Bilanço kartları
        cards_layout = QHBoxLayout()

        # Varliklar
        self.assets_card = self._create_summary_card("VARLIKLAR", "0", SUCCESS)
        cards_layout.addWidget(self.assets_card)

        # Borclar
        self.liabilities_card = self._create_summary_card("BORCLAR", "0", ERROR)
        cards_layout.addWidget(self.liabilities_card)

        # Ozkaynaklar
        self.equity_card = self._create_summary_card("OZKAYNAKLAR", "0", ACCENT)
        cards_layout.addWidget(self.equity_card)

        layout.addLayout(cards_layout)

        # Denge durumu
        self.balance_status = QLabel()
        self.balance_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.balance_status.setStyleSheet(
            """
            padding: 16px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 8px;
        """
        )
        layout.addWidget(self.balance_status)

        layout.addStretch()

        return page

    def _create_summary_card(self, title: str, value: str, color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_SECONDARY};
                border: 1px solid {color}40;
                border-radius: 8px;
                border-left: 3px solid {color};
                padding: 16px;
            }}
        """
        )

        layout = QVBoxLayout(card)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet(
            f"color: {color}; font-size: 28px; font-weight: bold;"
        )
        layout.addWidget(value_label)

        return card

    def _hex_to_rgb(self, hex_color: str) -> str:
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"{r}, {g}, {b}"

    def _style_combo(self, widget):
        widget.setStyleSheet(
            f"""
            QComboBox {{
                background-color: {INPUT_BG};
                border: 1px solid {INPUT_BORDER};
                border-radius: 4px;
                padding: 8px 12px;
                color: {TEXT_PRIMARY};
            }}
            QComboBox:focus {{
                border: 1px solid {ACCENT};
            }}
            QComboBox QAbstractItemView {{
                background-color: {BG_SECONDARY};
                border: 1px solid {BORDER};
                selection-background-color: {BG_HOVER};
            }}
        """
        )

    def _style_date(self, widget):
        widget.setStyleSheet(
            f"""
            QDateEdit {{
                background-color: {INPUT_BG};
                border: 1px solid {INPUT_BORDER};
                border-radius: 4px;
                padding: 8px 12px;
                color: {TEXT_PRIMARY};
            }}
            QDateEdit:focus {{
                border: 1px solid {ACCENT};
            }}
        """
        )

    def _style_table(self, table):
        table.setStyleSheet(get_table_style())
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.verticalHeader().setVisible(False)
        header = table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

    def _get_service(self):
        if self.service is None:
            self.service = AccountingService()
        return self.service

    def _close_service(self):
        if self.service:
            self.service.close()
            self.service = None

    def _on_tab_changed(self, index: int):
        """Tab degisti"""
        # Hesap listesini yukle (buyuk defter icin)
        if index == 0:
            self._load_accounts_for_ledger()

    def _load_accounts_for_ledger(self):
        """Büyük defter için hesap listesi"""
        try:
            service = self._get_service()
            accounts = service.get_all_accounts()
            self.ledger_account.clear()
            for acc in accounts:
                if acc.is_detail:
                    self.ledger_account.addItem(f"{acc.code} - {acc.name}", acc.id)
        finally:
            self._close_service()

    def _generate_ledger(self):
        """Büyük defter oluştur"""
        account_id = self.ledger_account.currentData()
        if not account_id:
            return

        qstart = self.ledger_start.date()
        qend = self.ledger_end.date()
        start = date(qstart.year(), qstart.month(), qstart.day())
        end = date(qend.year(), qend.month(), qend.day())

        try:
            service = self._get_service()
            data = service.get_ledger(account_id, start, end)

            # Özet
            self.ledger_summary.setText(
                f"📖 {data['account']['code']} - {data['account']['name']} | "
                f"Açılış: ₺{data['opening_balance']:,.2f} | "
                f"Kapanış: ₺{data['closing_balance']:,.2f}"
            )

            # Tablo
            movements = data.get("movements", [])
            self.ledger_table.setRowCount(len(movements))

            for row, m in enumerate(movements):
                self.ledger_table.setItem(row, 0, QTableWidgetItem(str(m["date"])))
                self.ledger_table.setItem(row, 1, QTableWidgetItem(m["entry_no"]))
                self.ledger_table.setItem(
                    row, 2, QTableWidgetItem(m["description"] or "")
                )

                debit_item = QTableWidgetItem(f"₺{m['debit']:,.2f}")
                debit_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.ledger_table.setItem(row, 3, debit_item)

                credit_item = QTableWidgetItem(f"₺{m['credit']:,.2f}")
                credit_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.ledger_table.setItem(row, 4, credit_item)

        except Exception as e:
            QMessageBox.warning(self, "Uyarı", str(e))
        finally:
            self._close_service()

    def _generate_trial_balance(self):
        """Mizan oluştur"""
        qdate = self.trial_date.date()
        as_of = date(qdate.year(), qdate.month(), qdate.day())

        try:
            service = self._get_service()
            data = service.get_trial_balance(as_of)

            # Toplam
            totals = data.get("totals", {})
            status = "✓ Dengeli" if totals.get("balanced") else "✗ Dengesiz"
            self.trial_summary.setText(
                f"Toplam Borç: ₺{totals['debit']:,.2f} | "
                f"Toplam Alacak: ₺{totals['credit']:,.2f} | {status}"
            )

            # Tablo
            rows = data.get("rows", [])
            self.trial_table.setRowCount(len(rows))

            for i, r in enumerate(rows):
                self.trial_table.setItem(i, 0, QTableWidgetItem(r["code"]))
                self.trial_table.setItem(i, 1, QTableWidgetItem(r["name"]))

                for col, key in [
                    (2, "period_debit"),
                    (3, "period_credit"),
                    (4, "closing_debit"),
                    (5, "closing_credit"),
                ]:
                    item = QTableWidgetItem(f"₺{r[key]:,.2f}")
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    self.trial_table.setItem(i, col, item)

        except Exception as e:
            QMessageBox.warning(self, "Uyarı", str(e))
        finally:
            self._close_service()

    def _generate_balance_sheet(self):
        """Bilanço oluştur"""
        qdate = self.balance_date.date()
        as_of = date(qdate.year(), qdate.month(), qdate.day())

        try:
            service = self._get_service()
            data = service.get_balance_sheet(as_of)

            # Kartları güncelle
            assets = data.get("assets", {})
            self.assets_card.findChild(QLabel, "value").setText(
                f"₺{assets.get('total', 0):,.2f}"
            )

            liabilities = data.get("liabilities", {})
            self.liabilities_card.findChild(QLabel, "value").setText(
                f"₺{liabilities.get('total', 0):,.2f}"
            )

            equity = data.get("equity", 0)
            self.equity_card.findChild(QLabel, "value").setText(f"₺{equity:,.2f}")

            # Denge durumu
            if data.get("balanced"):
                self.balance_status.setText("Bilanco Dengeli")
                self.balance_status.setStyleSheet(
                    f"""
                    padding: 16px;
                    font-size: 16px;
                    font-weight: bold;
                    border-radius: 8px;
                    background-color: {BG_SECONDARY};
                    color: {SUCCESS};
                    border: 1px solid {SUCCESS}40;
                """
                )
            else:
                diff = assets.get("total", 0) - data.get("total_liabilities_equity", 0)
                self.balance_status.setText(
                    f"Bilanco Dengesiz (Fark: {abs(diff):,.2f})"
                )
                self.balance_status.setStyleSheet(
                    f"""
                    padding: 16px;
                    font-size: 16px;
                    font-weight: bold;
                    border-radius: 8px;
                    background-color: {BG_SECONDARY};
                    color: {ERROR};
                    border: 1px solid {ERROR}40;
                """
                )

        except Exception as e:
            QMessageBox.warning(self, "Uyarı", str(e))
        finally:
            self._close_service()
