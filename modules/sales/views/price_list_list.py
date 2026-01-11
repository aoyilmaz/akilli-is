"""
Akilli Is - Fiyat Listesi Liste Sayfasi
"""

from PyQt6.QtWidgets import (
    QStyle, QApplication,
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
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from ui.components.stat_cards import MiniStatCard


class PriceListListPage(QWidget):
    """Fiyat listesi listesi sayfasi"""

    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    view_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.price_lists = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Fiyat Listeleri")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ara... (kod, ad)")
        self.search_input.setFixedWidth(300)
        self.search_input.textChanged.connect(self._on_search)
        header_layout.addWidget(self.search_input)

        # Yenile butonu
        refresh_btn = QPushButton("Yenile")
        refresh_btn.setFixedHeight(42)
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        header_layout.addWidget(refresh_btn)

        # Yeni ekle butonu
        add_btn = QPushButton("+ Yeni Fiyat Listesi")
        add_btn.clicked.connect(self.add_clicked.emit)
        header_layout.addWidget(add_btn)

        layout.addLayout(header_layout)

        # Istatistik kartlari
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.total_card = self._create_stat_card("📊 Toplam", "0", "#6366f1")
        stats_layout.addWidget(self.total_card)

        self.sales_card = self._create_stat_card("📤 Satış", "0", "#10b981")
        stats_layout.addWidget(self.sales_card)

        self.purchase_card = self._create_stat_card("📥 Alış", "0", "#f59e0b")
        stats_layout.addWidget(self.purchase_card)

        self.default_card = self._create_stat_card("⭐ Varsayılan", "0", "#3b82f6")
        stats_layout.addWidget(self.default_card)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            [
                "Kod",
                "Liste Adi",
                "Tur",
                "Para Birimi",
                "Gecerlilik",
                "Varsayilan",
                "Kalem",
                "Islemler",
            ]
        )

        # Tablo stili
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        # Kolon genislikleri
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 180)
        self.table.setColumnWidth(5, 90)
        self.table.setColumnWidth(6, 80)
        self.table.setColumnWidth(7, 150)

        self.table.doubleClicked.connect(self._on_double_click)

        layout.addWidget(self.table)

    def _create_stat_card(self, title: str, value: str, color: str) -> MiniStatCard:
        """Dashboard tarzı istatistik kartı"""
        return MiniStatCard(title, value, color)

    def _update_card(self, card: MiniStatCard, value: str):
        """Kart değerini güncelle"""
        card.update_value(value)

    def load_data(self, price_lists: list):
        """Verileri yukle"""
        self.price_lists = price_lists
        self.table.setRowCount(0)

        total = len(price_lists)
        sales_count = 0
        purchase_count = 0
        default_count = 0

        for pl in price_lists:
            if pl.get("list_type") == "sales":
                sales_count += 1
            else:
                purchase_count += 1
            if pl.get("is_default"):
                default_count += 1

        self._update_card(self.total_card, str(total))
        self._update_card(self.sales_card, str(sales_count))
        self._update_card(self.purchase_card, str(purchase_count))
        self._update_card(self.default_card, str(default_count))

        for row, pl in enumerate(price_lists):
            self.table.insertRow(row)

            # Kod
            code_item = QTableWidgetItem(pl.get("code", ""))
            code_item.setData(Qt.ItemDataRole.UserRole, pl.get("id"))
            self.table.setItem(row, 0, code_item)

            # Ad
            self.table.setItem(row, 1, QTableWidgetItem(pl.get("name", "")))

            # Tur
            list_type = pl.get("list_type", "sales")
            type_text = "Satis" if list_type == "sales" else "Alis"
            self.table.setItem(row, 2, QTableWidgetItem(type_text))

            # Para birimi
            self.table.setItem(row, 3, QTableWidgetItem(pl.get("currency", "TRY")))

            # Gecerlilik
            valid_from = pl.get("valid_from")
            valid_until = pl.get("valid_until")
            validity = ""
            if valid_from:
                validity = str(valid_from)
            if valid_until:
                validity += f" - {valid_until}"
            if not validity:
                validity = "Suresiz"
            self.table.setItem(row, 4, QTableWidgetItem(validity))

            # Varsayilan
            is_default = pl.get("is_default", False)
            default_text = "Evet" if is_default else "-"
            default_item = QTableWidgetItem(default_text)
            if is_default:
                default_item.setForeground(Qt.GlobalColor.green)
            self.table.setItem(row, 5, default_item)

            # Kalem sayisi
            item_count = pl.get("item_count", 0)
            self.table.setItem(row, 6, QTableWidgetItem(str(item_count)))

            # Islem butonlari
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(4)

            style = QApplication.style()

            view_btn = QPushButton("Gor")
            view_btn.setFixedSize(40, 32)
            view_btn.setToolTip("Goruntule")
            view_btn.clicked.connect(
                lambda checked, id=pl.get("id"): self.view_clicked.emit(id)
            )
            btn_layout.addWidget(view_btn)

            edit_btn = QPushButton("Duz")
            edit_btn.setFixedSize(40, 32)
            edit_btn.setToolTip("Duzenle")
            edit_btn.clicked.connect(
                lambda checked, id=pl.get("id"): self.edit_clicked.emit(id)
            )
            btn_layout.addWidget(edit_btn)

            del_btn = QPushButton()
            del_btn.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
            del_btn.setIconSize(QSize(16, 16))
            del_btn.setFixedSize(40, 32)
            del_btn.setToolTip("Sil")
            del_btn.clicked.connect(
                lambda checked, id=pl.get("id"): self._confirm_delete(id)
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
                font-size: 11px;
                color: {color};
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
            for col in range(4):
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    def _on_double_click(self, index):
        """Cift tiklama"""
        row = index.row()
        item = self.table.item(row, 0)
        if item:
            price_list_id = item.data(Qt.ItemDataRole.UserRole)
            if price_list_id:
                self.view_clicked.emit(price_list_id)

    def _confirm_delete(self, price_list_id: int):
        """Silme onayi"""
        reply = QMessageBox.question(
            self,
            "Silme Onayi",
            "Bu fiyat listesini silmek istediginize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(price_list_id)
