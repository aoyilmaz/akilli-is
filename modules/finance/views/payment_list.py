"""
Akıllı İş - Ödeme Liste Sayfası
Yeni bileşen mimarisi kullanılarak yeniden yapılandırıldı.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidgetItem,
    QComboBox,
    QDateEdit,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor
from decimal import Decimal

from ui.components import (
    PageHeader,
    EnhancedTableWidget,
    ColumnConfig,
    MiniStatCard,
)


class PaymentListPage(QWidget):
    """Ödeme listesi sayfası."""

    # Sinyaller
    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    view_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()

    STATUS_MAP = {
        "pending": ("⏳ Beklemede", "#f59e0b"),
        "completed": ("✅ Tamamlandı", "#10b981"),
        "cancelled": ("❌ İptal", "#ef4444"),
    }

    METHOD_MAP = {
        "cash": "💵 Nakit",
        "bank_transfer": "🏦 Havale/EFT",
        "check": "📝 Çek",
        "credit_card": "💳 Kredi Kartı",
        "promissory_note": "📄 Senet",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.payments = []
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        self.header = PageHeader(
            title="Ödemeler",
            icon="💳",
            show_search=True,
            show_refresh=True,
            show_add=True,
            add_text="Yeni Ödeme",
            search_placeholder="No, tedarikçi ara...",
            parent=self,
        )
        layout.addWidget(self.header)

        # Filtre alanı
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(12)

        filter_layout.addWidget(QLabel("Başlangıç:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setFixedWidth(130)
        filter_layout.addWidget(self.date_from)

        filter_layout.addWidget(QLabel("Bitiş:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setFixedWidth(130)
        filter_layout.addWidget(self.date_to)

        filter_layout.addWidget(QLabel("Durum:"))
        self.status_combo = QComboBox()
        self.status_combo.addItem("Tümü", None)
        self.status_combo.addItem("Tamamlandı", "completed")
        self.status_combo.addItem("Beklemede", "pending")
        self.status_combo.addItem("İptal", "cancelled")
        self.status_combo.setFixedWidth(130)
        filter_layout.addWidget(self.status_combo)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # İstatistik kartları
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.stat_cards = {}
        self.stat_cards["total"] = MiniStatCard("📊 Toplam", "0", "#6366f1")
        self.stat_cards["completed"] = MiniStatCard("✅ Tamamlanan", "0", "#10b981")
        self.stat_cards["amount"] = MiniStatCard("💰 Toplam Tutar", "₺0", "#ef4444")

        for card in self.stat_cards.values():
            stats_layout.addWidget(card)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Tablo
        columns = [
            ColumnConfig("payment_no", "Ödeme No", width=120),
            ColumnConfig("payment_date", "Tarih", width=100),
            ColumnConfig("supplier_name", "Tedarikçi", stretch=True),
            ColumnConfig("amount", "Tutar", width=120),
            ColumnConfig("payment_method", "Ödeme Yöntemi", width=130),
            ColumnConfig("status", "Durum", width=110),
            ColumnConfig("description", "Açıklama", width=150),
            ColumnConfig("actions", "İşlemler", width=120),
        ]

        self.table = EnhancedTableWidget(
            table_id="payment_list",
            columns=columns,
            parent=self,
        )
        layout.addWidget(self.table)

        # Alt bilgi
        self.count_label = QLabel("Toplam: 0 ödeme")
        layout.addWidget(self.count_label)

    def _connect_signals(self):
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        self.header.add_clicked.connect(self.add_clicked.emit)
        self.header.search_changed.connect(self._on_search)
        self.table.row_double_clicked.connect(self.view_clicked.emit)

    def load_data(self, payments: list):
        self.payments = payments
        self.table.setRowCount(len(payments))
        visible_cols = self.table.get_visible_columns()

        completed = 0
        total_amount = Decimal(0)

        for row, pmt in enumerate(payments):
            self._populate_row(row, pmt, visible_cols)

            if pmt.get("status") == "completed":
                completed += 1
                total_amount += Decimal(str(pmt.get("amount", 0) or 0))

        # Kartları güncelle
        self.stat_cards["total"].update_value(str(len(payments)))
        self.stat_cards["completed"].update_value(str(completed))
        self.stat_cards["amount"].update_value(f"₺{total_amount:,.2f}")

        self.count_label.setText(f"Toplam: {len(payments)} ödeme")

    def _populate_row(self, row: int, pmt: dict, visible_cols: list):
        pmt_id = pmt.get("id")

        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "payment_no":
                item = QTableWidgetItem(pmt.get("payment_no", ""))
                item.setData(Qt.ItemDataRole.UserRole, pmt_id)
                item.setForeground(QColor("#818cf8"))
                self.table.setItem(row, col_idx, item)

            elif col_key == "payment_date":
                date_val = pmt.get("payment_date")
                if hasattr(date_val, "strftime"):
                    date_str = date_val.strftime("%d.%m.%Y")
                else:
                    date_str = str(date_val) if date_val else ""
                self.table.setItem(row, col_idx, QTableWidgetItem(date_str))

            elif col_key == "supplier_name":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(pmt.get("supplier_name", ""))
                )

            elif col_key == "amount":
                amount = pmt.get("amount") or 0
                item = QTableWidgetItem(f"₺{float(amount):,.2f}")
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.table.setItem(row, col_idx, item)

            elif col_key == "payment_method":
                method = pmt.get("payment_method", "")
                text = self.METHOD_MAP.get(method, method)
                self.table.setItem(row, col_idx, QTableWidgetItem(text))

            elif col_key == "status":
                status = pmt.get("status", "")
                text, color = self.STATUS_MAP.get(status, (status, "#ffffff"))
                item = QTableWidgetItem(text)
                item.setForeground(QColor(color))
                self.table.setItem(row, col_idx, item)

            elif col_key == "description":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(pmt.get("description", "") or "")
                )

            elif col_key == "actions":
                self._add_action_buttons(row, col_idx, pmt)

        self.table.setRowHeight(row, 48)

    def _add_action_buttons(self, row: int, col: int, pmt: dict):
        pmt_id = pmt.get("id")

        btn_widget = QWidget()
        btn_widget.setProperty("class", "action-button-group")
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setContentsMargins(4, 4, 4, 4)
        btn_layout.setSpacing(4)

        view_btn = QPushButton("👁")
        view_btn.setFixedSize(28, 26)
        view_btn.setProperty("class", "action-view")
        view_btn.clicked.connect(lambda: self.view_clicked.emit(pmt_id))
        btn_layout.addWidget(view_btn)

        if pmt.get("status") != "cancelled":
            cancel_btn = QPushButton("❌")
            cancel_btn.setFixedSize(28, 26)
            cancel_btn.setProperty("class", "action-delete")
            cancel_btn.setToolTip("İptal Et")
            cancel_btn.clicked.connect(lambda: self._confirm_cancel(pmt_id))
            btn_layout.addWidget(cancel_btn)

        btn_layout.addStretch()
        self.table.setCellWidget(row, col, btn_widget)

    def _on_search(self, text: str):
        text = text.lower()
        for row in range(self.table.rowCount()):
            match = any(
                self.table.item(row, col)
                and text in self.table.item(row, col).text().lower()
                for col in range(self.table.columnCount())
            )
            self.table.setRowHidden(row, not match)

    def _confirm_cancel(self, payment_id: int):
        reply = QMessageBox.question(
            self,
            "İptal Onayı",
            "Bu ödemeyi iptal etmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(payment_id)

    def get_filter_data(self) -> dict:
        return {
            "date_from": self.date_from.date().toPyDate(),
            "date_to": self.date_to.date().toPyDate(),
            "status": self.status_combo.currentData(),
        }
