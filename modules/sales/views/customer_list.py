"""
Akıllı İş - Müşteri Liste Sayfası
"""

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
    QStyle,
    QApplication,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from ui.components.stat_cards import MiniStatCard
from config.styles import get_button_style, BTN_HEIGHT_NORMAL, ICONS


class CustomerListPage(QWidget):
    """Müşteri listesi sayfası"""

    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    view_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.customers = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("👥 Müşteriler")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ara... (kod, ad, vergi no)")
        self.search_input.setFixedWidth(300)
        self.search_input.textChanged.connect(self._on_search)
        header_layout.addWidget(self.search_input)

        # Yenile butonu
        refresh_btn = QPushButton(f"{ICONS['refresh']} Yenile")
        refresh_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        refresh_btn.setStyleSheet(get_button_style("refresh"))
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        header_layout.addWidget(refresh_btn)

        # Yeni ekle butonu
        add_btn = QPushButton(f"{ICONS['add']} Yeni Müşteri")
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

        self.active_card = self._create_stat_card("✅", "Aktif", "0", "#10b981")
        stats_layout.addWidget(self.active_card)

        self.with_orders_card = self._create_stat_card(
            "🛒", "Siparişli", "0", "#f59e0b"
        )
        stats_layout.addWidget(self.with_orders_card)

        self.credit_card = self._create_stat_card("💳", "Toplam Limit", "₺0", "#3b82f6")
        stats_layout.addWidget(self.credit_card)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            [
                "Kod",
                "Müşteri Adı",
                "Telefon",
                "E-posta",
                "Şehir",
                "Vade (Gün)",
                "Puan",
                "İşlemler",
            ]
        )

        # Tablo stili
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        # Kolon genişlikleri
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(2, 130)
        self.table.setColumnWidth(3, 180)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 80)
        self.table.setColumnWidth(7, 150)

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

    def load_data(self, customers: list):
        """Verileri yükle"""
        self.customers = customers
        self.table.setRowCount(0)

        total = len(customers)
        active = 0
        total_credit = 0

        for cust in customers:
            if cust.get("is_active", True):
                active += 1
            total_credit += float(cust.get("credit_limit", 0) or 0)

        self._update_card(self.total_card, str(total))
        self._update_card(self.active_card, str(active))
        self._update_card(self.credit_card, f"₺{total_credit:,.0f}")

        for row, cust in enumerate(customers):
            self.table.insertRow(row)

            # Kod
            code_item = QTableWidgetItem(cust.get("code", ""))
            code_item.setData(Qt.ItemDataRole.UserRole, cust.get("id"))
            self.table.setItem(row, 0, code_item)

            # Ad
            self.table.setItem(row, 1, QTableWidgetItem(cust.get("name", "")))

            # Telefon
            self.table.setItem(row, 2, QTableWidgetItem(cust.get("phone", "") or "-"))

            # E-posta
            self.table.setItem(row, 3, QTableWidgetItem(cust.get("email", "") or "-"))

            # Şehir
            self.table.setItem(row, 4, QTableWidgetItem(cust.get("city", "") or "-"))

            # Vade
            vade = cust.get("payment_term_days", 0) or 0
            self.table.setItem(row, 5, QTableWidgetItem(str(vade)))

            # Puan
            rating = cust.get("rating", 0) or 0
            stars = "⭐" * rating if rating > 0 else "-"
            self.table.setItem(row, 6, QTableWidgetItem(stars))

            # İşlem butonları
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(4)

            style = QApplication.style()

            view_btn = QPushButton()
            view_btn.setIcon(
                style.standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView)
            )
            view_btn.setIconSize(QSize(16, 16))
            view_btn.setFixedSize(32, 28)
            view_btn.setToolTip("Görüntüle")
            view_btn.clicked.connect(
                lambda checked, id=cust.get("id"): self.view_clicked.emit(id)
            )
            btn_layout.addWidget(view_btn)

            edit_btn = QPushButton()
            edit_btn.setIcon(
                style.standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
            )
            edit_btn.setIconSize(QSize(16, 16))
            edit_btn.setFixedSize(32, 28)
            edit_btn.setToolTip("Düzenle")
            edit_btn.clicked.connect(
                lambda checked, id=cust.get("id"): self.edit_clicked.emit(id)
            )
            btn_layout.addWidget(edit_btn)

            del_btn = QPushButton()
            del_btn.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
            del_btn.setIconSize(QSize(16, 16))
            del_btn.setFixedSize(32, 28)
            del_btn.setToolTip("Sil")
            del_btn.clicked.connect(
                lambda checked, id=cust.get("id"): self._confirm_delete(id)
            )
            btn_layout.addWidget(del_btn)

            self.table.setCellWidget(row, 7, btn_widget)
            self.table.setRowHeight(row, 56)

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
        """Arama"""
        text = text.lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(6):
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    def _on_double_click(self, index):
        """Çift tıklama"""
        row = index.row()
        item = self.table.item(row, 0)
        if item:
            customer_id = item.data(Qt.ItemDataRole.UserRole)
            if customer_id:
                self.view_clicked.emit(customer_id)

    def _confirm_delete(self, customer_id: int):
        """Silme onayı"""
        reply = QMessageBox.question(
            self,
            "Silme Onayı",
            "Bu müşteriyi silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(customer_id)
