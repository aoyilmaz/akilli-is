"""
Akıllı İş - Satınalma Faturası Liste Sayfası
"""

from datetime import date
from decimal import Decimal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QFrame,
    QLineEdit,
    QHeaderView,
    QAbstractItemView,
    QMessageBox,
    QComboBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from ui.components.stat_cards import MiniStatCard
from config.styles import get_button_style, BTN_HEIGHT_NORMAL, ICONS


class PurchaseInvoiceListPage(QWidget):
    """Satınalma faturası listesi"""

    add_clicked = pyqtSignal()
    add_from_receipt_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    view_clicked = pyqtSignal(int)
    confirm_clicked = pyqtSignal(int)
    pay_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.invoices = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("📄 Satınalma Faturaları")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Durum filtresi
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tüm Durumlar", None)
        self.status_filter.addItem("🔵 Taslak", "draft")
        self.status_filter.addItem("📥 Alındı", "received")
        self.status_filter.addItem("🟡 Kısmi Ödendi", "partial")
        self.status_filter.addItem("🟢 Ödendi", "paid")
        self.status_filter.addItem("🔴 Vadesi Geçti", "overdue")
        self.status_filter.addItem("⚫ İptal", "cancelled")
        self.status_filter.setStyleSheet(self._combo_style())
        self.status_filter.setMinimumWidth(150)
        self.status_filter.currentIndexChanged.connect(self._on_filter_changed)
        header_layout.addWidget(self.status_filter)

        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ara... (fatura no, tedarikçi)")
        self.search_input.setFixedWidth(250)
        self.search_input.textChanged.connect(self._on_search)
        header_layout.addWidget(self.search_input)

        # Yenile
        refresh_btn = QPushButton(f"{ICONS['refresh']} Yenile")
        refresh_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        refresh_btn.setStyleSheet(get_button_style("refresh"))
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        header_layout.addWidget(refresh_btn)

        # Mal Kabulden Fatura
        from_receipt_btn = QPushButton("📦 Mal Kabulden")
        from_receipt_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        from_receipt_btn.setStyleSheet(get_button_style("secondary"))
        from_receipt_btn.clicked.connect(self.add_from_receipt_clicked.emit)
        header_layout.addWidget(from_receipt_btn)

        # Yeni (manuel)
        add_btn = QPushButton(f"{ICONS['add']} Yeni Fatura")
        add_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        add_btn.setStyleSheet(get_button_style("add"))
        add_btn.clicked.connect(self.add_clicked.emit)
        header_layout.addWidget(add_btn)

        layout.addLayout(header_layout)

        # İstatistik kartları
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.total_card = self._create_stat_card("📊", "Toplam", "0", "#6366f1")
        stats_layout.addWidget(self.total_card)

        self.open_card = self._create_stat_card("📥", "Açık", "0", "#f59e0b")
        stats_layout.addWidget(self.open_card)

        self.paid_card = self._create_stat_card("🟢", "Ödendi", "0", "#10b981")
        stats_layout.addWidget(self.paid_card)

        self.overdue_card = self._create_stat_card("🔴", "Vadesi Geçti", "0", "#ef4444")
        stats_layout.addWidget(self.overdue_card)

        self.balance_card = self._create_stat_card("💰", "Toplam Borç", "₺0", "#8b5cf6")
        stats_layout.addWidget(self.balance_card)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(
            [
                "Fatura No",
                "Tarih",
                "Vade",
                "Tedarikçi",
                "Toplam",
                "Ödenen",
                "Bakiye",
                "Durum",
                "İşlemler",
            ]
        )
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(4, 110)
        self.table.setColumnWidth(5, 110)
        self.table.setColumnWidth(6, 110)
        self.table.setColumnWidth(7, 120)
        self.table.setColumnWidth(8, 180)

        self.table.doubleClicked.connect(self._on_double_click)

        layout.addWidget(self.table)

    def _create_stat_card(
        self, icon: str, title: str, value: str, color: str
    ) -> MiniStatCard:
        """Dashboard tarzı istatistik kartı"""
        return MiniStatCard(f"{icon} {title}", value, color)

    def _update_card(self, card: MiniStatCard, value: str):
        """Kart değerini güncelle"""
        card.update_value(value)

    def _combo_style(self):
        return """
            QComboBox {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px 14px;
                color: #f8fafc;
                font-size: 14px;
            }
            QComboBox:hover { border-color: #475569; }
            QComboBox::drop-down { border: none; width: 30px; }
            QComboBox::down-arrow {
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #94a3b8;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                border: 1px solid #334155;
                color: #f8fafc;
                selection-background-color: #334155;
            }
        """

    def load_data(self, invoices: list):
        """Verileri yükle"""
        self.invoices = invoices
        self._apply_filter()

    def _apply_filter(self):
        status_filter = self.status_filter.currentData()

        filtered = self.invoices
        if status_filter:
            filtered = [i for i in self.invoices if i.get("status") == status_filter]

        self._display_data(filtered)
        self._update_stats()

    def _display_data(self, invoices: list):
        self.table.setRowCount(0)

        status_labels = {
            "draft": ("🔵 Taslak", "#64748b"),
            "received": ("📥 Alındı", "#3b82f6"),
            "partial": ("🟡 Kısmi Ödendi", "#f59e0b"),
            "paid": ("🟢 Ödendi", "#10b981"),
            "overdue": ("🔴 Vadesi Geçti", "#ef4444"),
            "cancelled": ("⚫ İptal", "#475569"),
        }

        for row, inv in enumerate(invoices):
            self.table.insertRow(row)

            # Fatura No
            no_item = QTableWidgetItem(inv.get("invoice_no", ""))
            no_item.setData(Qt.ItemDataRole.UserRole, inv.get("id"))
            self.table.setItem(row, 0, no_item)

            # Tarih
            inv_date = inv.get("invoice_date")
            if inv_date:
                if isinstance(inv_date, date):
                    date_str = inv_date.strftime("%d.%m.%Y")
                else:
                    date_str = str(inv_date)
            else:
                date_str = "-"
            self.table.setItem(row, 1, QTableWidgetItem(date_str))

            # Vade
            due = inv.get("due_date")
            if due:
                if isinstance(due, date):
                    due_str = due.strftime("%d.%m.%Y")
                else:
                    due_str = str(due)
            else:
                due_str = "-"
            self.table.setItem(row, 2, QTableWidgetItem(due_str))

            # Tedarikçi
            self.table.setItem(
                row, 3, QTableWidgetItem(inv.get("supplier_name", "") or "-")
            )

            # Toplam
            total = inv.get("total", 0) or 0
            self.table.setItem(row, 4, QTableWidgetItem(f"₺{float(total):,.2f}"))

            # Ödenen
            paid = inv.get("paid_amount", 0) or 0
            self.table.setItem(row, 5, QTableWidgetItem(f"₺{float(paid):,.2f}"))

            # Bakiye
            balance = inv.get("balance", 0) or 0
            balance_item = QTableWidgetItem(f"₺{float(balance):,.2f}")
            if float(balance) > 0:
                balance_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(row, 6, balance_item)

            # Durum
            status = inv.get("status", "draft")
            status_text, _ = status_labels.get(status, ("Taslak", "#64748b"))
            self.table.setItem(row, 7, QTableWidgetItem(status_text))

            # İşlem butonları
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(4)

            inv_id = inv.get("id")
            inv_status = inv.get("status", "draft")

            # Görüntüle
            view_btn = QPushButton("Gör")
            view_btn.setFixedSize(40, 28)
            view_btn.setToolTip("Görüntüle")
            view_btn.clicked.connect(
                lambda checked, id=inv_id: self.view_clicked.emit(id)
            )
            btn_layout.addWidget(view_btn)

            if inv_status == "draft":
                # Düzenle
                edit_btn = QPushButton("Düz")
                edit_btn.setFixedSize(40, 28)
                edit_btn.setToolTip("Düzenle")
                edit_btn.clicked.connect(
                    lambda checked, id=inv_id: self.edit_clicked.emit(id)
                )
                btn_layout.addWidget(edit_btn)

                # Onayla
                confirm_btn = QPushButton("On")
                confirm_btn.setFixedSize(40, 28)
                confirm_btn.setToolTip("Onayla")
                confirm_btn.clicked.connect(
                    lambda checked, id=inv_id: self.confirm_clicked.emit(id)
                )
                btn_layout.addWidget(confirm_btn)

                # Sil
                del_btn = QPushButton("Sil")
                del_btn.setFixedSize(40, 28)
                del_btn.setToolTip("Sil")
                del_btn.clicked.connect(
                    lambda checked, id=inv_id: self._confirm_delete(id)
                )
                btn_layout.addWidget(del_btn)

            elif inv_status in ["received", "partial", "overdue"]:
                # Ödeme Kaydet
                pay_btn = QPushButton("💳")
                pay_btn.setFixedSize(40, 28)
                pay_btn.setToolTip("Ödeme Kaydet")
                pay_btn.clicked.connect(
                    lambda checked, id=inv_id: self.pay_clicked.emit(id)
                )
                btn_layout.addWidget(pay_btn)

            self.table.setCellWidget(row, 8, btn_widget)
            self.table.setRowHeight(row, 56)

    def _update_stats(self):
        total = len(self.invoices)
        open_count = sum(
            1
            for i in self.invoices
            if i.get("status") in ["received", "partial", "overdue"]
        )
        paid = sum(1 for i in self.invoices if i.get("status") == "paid")
        overdue = sum(1 for i in self.invoices if i.get("status") == "overdue")
        total_balance = sum(float(i.get("balance", 0) or 0) for i in self.invoices)

        self._update_card(self.total_card, str(total))
        self._update_card(self.open_card, str(open_count))
        self._update_card(self.paid_card, str(paid))
        self._update_card(self.overdue_card, str(overdue))
        self._update_card(self.balance_card, f"₺{total_balance:,.0f}")

    def _action_btn_style(self, color: str) -> str:
        return f"""
            QPushButton {{
                background-color: {color}20;
                border: 1px solid {color}50;
                border-radius: 6px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {color}40;
            }}
        """

    def _on_search(self, text: str):
        text = text.lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(7):
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    def _on_filter_changed(self):
        self._apply_filter()

    def _on_double_click(self, index):
        row = index.row()
        item = self.table.item(row, 0)
        if item:
            invoice_id = item.data(Qt.ItemDataRole.UserRole)
            if invoice_id:
                self.view_clicked.emit(invoice_id)

    def _confirm_delete(self, invoice_id: int):
        reply = QMessageBox.question(
            self,
            "Silme Onayı",
            "Bu faturayı silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(invoice_id)
