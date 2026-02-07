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
    QMessageBox,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

from config.styles import (
    ACCENT,
    SUCCESS,
    WARNING,
    ERROR,
    get_button_style,
    BTN_HEIGHT_NORMAL,
    ICONS,
)
from modules.accounting.services import AccountingService
from modules.accounting.cost_service import CostAccountingService


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
        # Buyuk Defter
        self.ledger_page = self._create_ledger_page()
        self.tabs.addTab(self.ledger_page, "Buyuk Defter")

        # Mizan
        self.trial_page = self._create_trial_balance_page()
        self.tabs.addTab(self.trial_page, "Mizan")

        # Bilanco
        self.balance_page = self._create_balance_sheet_page()
        self.tabs.addTab(self.balance_page, "Bilanco")

        # KDV Raporu
        self.vat_page = self._create_vat_report_page()
        self.tabs.addTab(self.vat_page, "KDV Raporu")

        # Maliyet Analizi
        self.cost_page = self._create_cost_report_page()
        self.tabs.addTab(self.cost_page, "Maliyet Analizi")

        self.tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tabs)

    # ... methods ...

    def _create_cost_report_page(self) -> QWidget:
        """Üretim Maliyet Raporu"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)

        # Filtre
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Tarih:"))
        self.cost_start = QDateEdit()
        self.cost_start.setDate(QDate.currentDate().addMonths(-1))
        self.cost_start.setCalendarPopup(True)
        filter_layout.addWidget(self.cost_start)

        filter_layout.addWidget(QLabel("-"))
        self.cost_end = QDateEdit()
        self.cost_end.setDate(QDate.currentDate())
        self.cost_end.setCalendarPopup(True)
        filter_layout.addWidget(self.cost_end)

        gen_btn = QPushButton(f"{ICONS['report']} Maliyet Analizi")
        gen_btn.setStyleSheet(get_button_style("primary"))
        gen_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        gen_btn.clicked.connect(self._generate_cost_report)
        filter_layout.addWidget(gen_btn)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Summary
        self.cost_summary = QLabel()
        layout.addWidget(self.cost_summary)

        # Table
        self.cost_table = QTableWidget()
        self.cost_table.setColumnCount(7)
        self.cost_table.setHorizontalHeaderLabels(
            [
                "İş Emri",
                "Miktar",
                "Malzeme",
                "İşçilik",
                "G. Gider",
                "Toplam",
                "Birim Fiyat",
            ]
        )
        header = self.cost_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.cost_table)

        return page

    def _generate_cost_report(self):
        qstart = self.cost_start.date()
        qend = self.cost_end.date()
        start = date(qstart.year(), qstart.month(), qstart.day())
        end = date(qend.year(), qend.month(), qend.day())

        service = None
        try:
            service = CostAccountingService()
            costs = service.get_production_costs(start, end)

            self.cost_table.setRowCount(len(costs))
            total_prod_cost = 0

            for i, c in enumerate(costs):
                self.cost_table.setItem(i, 0, QTableWidgetItem(c["order_no"]))
                self.cost_table.setItem(
                    i, 1, QTableWidgetItem(f"{c['completed_quantity']:,.2f}")
                )

                self.cost_table.setItem(
                    i, 2, QTableWidgetItem(f"₺{c['material_cost']:,.2f}")
                )
                self.cost_table.setItem(
                    i, 3, QTableWidgetItem(f"₺{c['labor_cost']:,.2f}")
                )
                self.cost_table.setItem(
                    i, 4, QTableWidgetItem(f"₺{c['overhead_cost']:,.2f}")
                )

                self.cost_table.setItem(
                    i, 5, QTableWidgetItem(f"₺{c['total_cost']:,.2f}")
                )
                self.cost_table.setItem(
                    i, 6, QTableWidgetItem(f"₺{c['unit_cost']:,.2f}")
                )

                total_prod_cost += c["total_cost"]

                # Right align numbers
                for col in range(1, 7):
                    item = self.cost_table.item(i, col)
                    if item:
                        item.setTextAlignment(
                            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                        )

            self.cost_summary.setText(
                f"Toplam Üretim Maliyeti: ₺{total_prod_cost:,.2f} ({len(costs)} İş Emri)"
            )

        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
        finally:
            if service:
                service.close()

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
        filter_layout.addWidget(self.ledger_account)

        filter_layout.addWidget(QLabel("Başlangıç:"))
        self.ledger_start = QDateEdit()
        self.ledger_start.setDate(QDate.currentDate().addMonths(-1))
        self.ledger_start.setCalendarPopup(True)
        filter_layout.addWidget(self.ledger_start)

        filter_layout.addWidget(QLabel("Bitiş:"))
        self.ledger_end = QDateEdit()
        self.ledger_end.setDate(QDate.currentDate())
        self.ledger_end.setCalendarPopup(True)
        filter_layout.addWidget(self.ledger_end)

        gen_btn = QPushButton(f"{ICONS['report']} Rapor Oluştur")
        gen_btn.setStyleSheet(get_button_style("primary"))
        gen_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        gen_btn.clicked.connect(self._generate_ledger)
        filter_layout.addWidget(gen_btn)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Ozet
        self.ledger_summary = QLabel()
        layout.addWidget(self.ledger_summary)

        # Tablo
        self.ledger_table = QTableWidget()
        self.ledger_table.setColumnCount(5)
        self.ledger_table.setHorizontalHeaderLabels(
            ["Tarih", "Fiş No", "Açıklama", "Borç", "Alacak"]
        )
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
        filter_layout.addWidget(self.trial_date)

        gen_btn = QPushButton(f"{ICONS['report']} Mizan Oluştur")
        gen_btn.setStyleSheet(get_button_style("primary"))
        gen_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        gen_btn.clicked.connect(self._generate_trial_balance)
        filter_layout.addWidget(gen_btn)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Toplam
        self.trial_summary = QLabel()
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
        filter_layout.addWidget(self.balance_date)

        gen_btn = QPushButton(f"{ICONS['report']} Bilanço Oluştur")
        gen_btn.setStyleSheet(get_button_style("primary"))
        gen_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
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
        layout.addWidget(self.balance_status)

        layout.addStretch()

        return page

    def _create_summary_card(self, title: str, value: str, color: str) -> QFrame:
        card = QFrame()
        layout = QVBoxLayout(card)

        title_label = QLabel(title)
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setObjectName("value")
        layout.addWidget(value_label)

        return card

    def _hex_to_rgb(self, hex_color: str) -> str:
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"{r}, {g}, {b}"

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
            else:
                diff = assets.get("total", 0) - data.get("total_liabilities_equity", 0)
                self.balance_status.setText(
                    f"Bilanco Dengesiz (Fark: {abs(diff):,.2f})"
                )
        except Exception as e:
            QMessageBox.warning(self, "Uyarı", str(e))
        finally:
            self._close_service()

    def _create_vat_report_page(self) -> QWidget:
        """KDV raporu sayfası"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)

        # Filtre
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Dönem:"))
        self.vat_start = QDateEdit()
        self.vat_start.setDate(QDate.currentDate().addMonths(-1))
        self.vat_start.setCalendarPopup(True)
        filter_layout.addWidget(self.vat_start)

        filter_layout.addWidget(QLabel("-"))
        self.vat_end = QDateEdit()
        self.vat_end.setDate(QDate.currentDate())
        self.vat_end.setCalendarPopup(True)
        filter_layout.addWidget(self.vat_end)

        gen_btn = QPushButton(f"{ICONS['report']} KDV Raporu")
        gen_btn.setStyleSheet(get_button_style("primary"))
        gen_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        gen_btn.clicked.connect(self._generate_vat_report)
        filter_layout.addWidget(gen_btn)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Kartlar
        cards_layout = QHBoxLayout()
        self.vat_sales_card = self._create_summary_card(
            "HESAPLANAN (SATIŞ)", "₺0", WARNING
        )
        cards_layout.addWidget(self.vat_sales_card)

        self.vat_purchase_card = self._create_summary_card(
            "İNDİRİLECEK (ALIŞ)", "₺0", SUCCESS
        )
        cards_layout.addWidget(self.vat_purchase_card)

        self.vat_net_card = self._create_summary_card(
            "NET KDV (ÖDENECEK)", "₺0", ACCENT
        )
        cards_layout.addWidget(self.vat_net_card)

        layout.addLayout(cards_layout)

        # Detay Tablosu
        self.vat_table = QTableWidget()
        self.vat_table.setColumnCount(4)
        self.vat_table.setHorizontalHeaderLabels(
            ["KDV Oranı", "Hesaplanan (Satış)", "İndirilecek (Alış)", "Fark"]
        )
        header = self.vat_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.vat_table)

        return page

    def _generate_vat_report(self):
        qstart = self.vat_start.date()
        qend = self.vat_end.date()
        start = date(qstart.year(), qstart.month(), qstart.day())
        end = date(qend.year(), qend.month(), qend.day())

        try:
            service = self._get_service()
            data = service.get_tax_report(start, end)

            sales_tax = data["sales"]["tax"]
            purchase_tax = data["purchases"]["tax"]
            net_tax = data["net_tax"]

            self.vat_sales_card.findChild(QLabel, "value").setText(f"₺{sales_tax:,.2f}")
            self.vat_purchase_card.findChild(QLabel, "value").setText(
                f"₺{purchase_tax:,.2f}"
            )

            try:
                # Try to find the title label (first label in layout)
                layout = self.vat_net_card.layout()
                for i in range(layout.count()):
                    widget = layout.itemAt(i).widget()
                    if isinstance(widget, QLabel) and widget.objectName() != "value":
                        net_label = (
                            "NET KDV (ÖDENECEK)"
                            if net_tax >= 0
                            else "NET KDV (İADE/DEVREDEN)"
                        )
                        widget.setText(net_label)
                        break
            except:
                pass

            self.vat_net_card.findChild(QLabel, "value").setText(
                f"₺{abs(net_tax):,.2f}"
            )

            # Fill table by rate
            rates = set()
            # Handle integer keys from service
            for k in data["sales"]["by_rate"]:
                rates.add(int(k))
            for k in data["purchases"]["by_rate"]:
                rates.add(int(k))

            sorted_rates = sorted(list(rates))

            self.vat_table.setRowCount(len(sorted_rates))
            for i, rate in enumerate(sorted_rates):
                # Helper to get tax safely
                def get_tax(source, r):
                    if r in source:
                        return source[r]["tax"]
                    if str(r) in source:
                        return source[str(r)]["tax"]
                    return 0

                s_tax = get_tax(data["sales"]["by_rate"], rate)
                p_tax = get_tax(data["purchases"]["by_rate"], rate)
                diff = s_tax - p_tax

                self.vat_table.setItem(i, 0, QTableWidgetItem(f"%{rate}"))

                s_item = QTableWidgetItem(f"₺{s_tax:,.2f}")
                s_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.vat_table.setItem(i, 1, s_item)

                p_item = QTableWidgetItem(f"₺{p_tax:,.2f}")
                p_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.vat_table.setItem(i, 2, p_item)

                diff_item = QTableWidgetItem(f"₺{diff:,.2f}")
                diff_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                if diff > 0:
                    diff_item.setForeground(QColor(WARNING))  # Owed
                else:
                    diff_item.setForeground(QColor(SUCCESS))  # Deductible
                self.vat_table.setItem(i, 3, diff_item)

        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))
        finally:
            self._close_service()
