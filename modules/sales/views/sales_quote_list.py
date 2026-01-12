"""
Akıllı İş - Satış Teklifleri Liste Sayfası
"""

from datetime import date
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


class SalesQuoteListPage(QWidget):
    """Satış teklifleri listesi"""

    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    view_clicked = pyqtSignal(int)
    send_clicked = pyqtSignal(int)
    accept_clicked = pyqtSignal(int)
    reject_clicked = pyqtSignal(int)
    convert_to_order_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.quotes = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("📄 Satış Teklifleri")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Durum filtresi
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tüm Durumlar", None)
        self.status_filter.addItem("🔵 Taslak", "draft")
        self.status_filter.addItem("📤 Gönderildi", "sent")
        self.status_filter.addItem("🟢 Kabul Edildi", "accepted")
        self.status_filter.addItem("🔴 Reddedildi", "rejected")
        self.status_filter.addItem("📦 Siparişe Dönüştü", "ordered")
        self.status_filter.addItem("⏰ Süresi Doldu", "expired")
        self.status_filter.addItem("⚫ İptal", "cancelled")
        self.status_filter.setStyleSheet(self._combo_style())
        self.status_filter.setMinimumWidth(180)
        self.status_filter.currentIndexChanged.connect(self._on_filter_changed)
        header_layout.addWidget(self.status_filter)

        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ara... (teklif no, müşteri)")
        self.search_input.setFixedWidth(250)
        self.search_input.textChanged.connect(self._on_search)
        header_layout.addWidget(self.search_input)

        # Yenile butonu
        refresh_btn = QPushButton(f"{ICONS['refresh']} Yenile")
        refresh_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        refresh_btn.setStyleSheet(get_button_style("refresh"))
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        header_layout.addWidget(refresh_btn)

        # Yeni ekle butonu
        add_btn = QPushButton(f"{ICONS['add']} Yeni Teklif")
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

        self.draft_card = self._create_stat_card("🔵", "Taslak", "0", "#64748b")
        stats_layout.addWidget(self.draft_card)

        self.sent_card = self._create_stat_card("📤", "Gönderildi", "0", "#3b82f6")
        stats_layout.addWidget(self.sent_card)

        self.accepted_card = self._create_stat_card(
            "🟢", "Kabul Edildi", "0", "#10b981"
        )
        stats_layout.addWidget(self.accepted_card)

        self.rejected_card = self._create_stat_card("🔴", "Reddedildi", "0", "#ef4444")
        stats_layout.addWidget(self.rejected_card)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(
            [
                "Teklif No",
                "Tarih",
                "Müşteri",
                "Toplam Tutar",
                "Kalem",
                "Geçerlilik",
                "Durum",
                "Para Birimi",
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
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(0, 120)  # Teklif No
        self.table.setColumnWidth(1, 100)  # Tarih
        self.table.setColumnWidth(3, 120)  # Toplam Tutar
        self.table.setColumnWidth(4, 60)  # Kalem
        self.table.setColumnWidth(5, 100)  # Geçerlilik
        self.table.setColumnWidth(6, 130)  # Durum
        self.table.setColumnWidth(7, 80)  # Para Birimi
        self.table.setColumnWidth(8, 200)  # İşlemler

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
                image: none;
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

    def load_data(self, quotes: list):
        """Verileri yükle"""
        self.quotes = quotes
        self._apply_filter()

    def _apply_filter(self):
        """Filtreyi uygula"""
        status_filter = self.status_filter.currentData()

        filtered = self.quotes
        if status_filter:
            filtered = [q for q in self.quotes if q.get("status") == status_filter]

        self._display_data(filtered)
        self._update_stats()

    def _display_data(self, quotes: list):
        """Tabloya verileri yükle"""
        self.table.setRowCount(0)

        status_labels = {
            "draft": ("🔵 Taslak", "#64748b"),
            "sent": ("📤 Gönderildi", "#3b82f6"),
            "accepted": ("🟢 Kabul Edildi", "#10b981"),
            "rejected": ("🔴 Reddedildi", "#ef4444"),
            "ordered": ("📦 Siparişe Dönüştü", "#8b5cf6"),
            "expired": ("⏰ Süresi Doldu", "#f59e0b"),
            "cancelled": ("⚫ İptal", "#475569"),
        }

        for row, quote in enumerate(quotes):
            self.table.insertRow(row)

            # Teklif No
            no_item = QTableWidgetItem(quote.get("quote_no", ""))
            no_item.setData(Qt.ItemDataRole.UserRole, quote.get("id"))
            self.table.setItem(row, 0, no_item)

            # Tarih
            quote_date = quote.get("quote_date")
            if quote_date:
                if isinstance(quote_date, date):
                    date_str = quote_date.strftime("%d.%m.%Y")
                else:
                    date_str = str(quote_date)
            else:
                date_str = "-"
            self.table.setItem(row, 1, QTableWidgetItem(date_str))

            # Müşteri
            self.table.setItem(
                row, 2, QTableWidgetItem(quote.get("customer_name", "") or "-")
            )

            # Toplam Tutar
            total = quote.get("total_amount", 0) or 0
            total_str = f"{total:,.2f}"
            self.table.setItem(row, 3, QTableWidgetItem(total_str))

            # Kalem Sayısı
            item_count = quote.get("total_items", 0)
            self.table.setItem(row, 4, QTableWidgetItem(str(item_count)))

            # Geçerlilik Tarihi
            valid_until = quote.get("valid_until")
            if valid_until:
                if isinstance(valid_until, date):
                    valid_str = valid_until.strftime("%d.%m.%Y")
                else:
                    valid_str = str(valid_until)
            else:
                valid_str = "-"
            self.table.setItem(row, 5, QTableWidgetItem(valid_str))

            # Durum
            status = quote.get("status", "draft")
            status_text, status_color = status_labels.get(status, ("Taslak", "#64748b"))
            status_item = QTableWidgetItem(status_text)
            self.table.setItem(row, 6, status_item)

            # Para Birimi
            currency = quote.get("currency_code", "TRY")
            self.table.setItem(row, 7, QTableWidgetItem(currency))

            # İşlem butonları
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(4)

            quote_id = quote.get("id")
            quote_status = quote.get("status", "draft")

            # Görüntüle
            view_btn = QPushButton("Gör")
            view_btn.setFixedSize(40, 28)
            view_btn.setToolTip("Görüntüle")
            view_btn.clicked.connect(
                lambda checked, id=quote_id: self.view_clicked.emit(id)
            )
            btn_layout.addWidget(view_btn)

            # Düzenle (sadece taslak)
            if quote_status == "draft":
                edit_btn = QPushButton("Düz")
                edit_btn.setFixedSize(40, 28)
                edit_btn.setToolTip("Düzenle")
                edit_btn.clicked.connect(
                    lambda checked, id=quote_id: self.edit_clicked.emit(id)
                )
                btn_layout.addWidget(edit_btn)

                # Müşteriye Gönder
                send_btn = QPushButton("Gön")
                send_btn.setFixedSize(40, 28)
                send_btn.setToolTip("Müşteriye Gönder")
                send_btn.clicked.connect(
                    lambda checked, id=quote_id: self.send_clicked.emit(id)
                )
                btn_layout.addWidget(send_btn)

            # Kabul Et / Reddet (sadece sent)
            if quote_status == "sent":
                accept_btn = QPushButton("On")
                accept_btn.setFixedSize(40, 28)
                accept_btn.setToolTip("Kabul Et")
                accept_btn.clicked.connect(
                    lambda checked, id=quote_id: self.accept_clicked.emit(id)
                )
                btn_layout.addWidget(accept_btn)

                reject_btn = QPushButton("İpt")
                reject_btn.setFixedSize(40, 28)
                reject_btn.setToolTip("Reddet")
                reject_btn.clicked.connect(
                    lambda checked, id=quote_id: self.reject_clicked.emit(id)
                )
                btn_layout.addWidget(reject_btn)

            # Siparişe Dönüştür (sadece accepted)
            if quote_status == "accepted":
                order_btn = QPushButton("📦")
                order_btn.setFixedSize(40, 28)
                order_btn.setToolTip("Siparişe Dönüştür")
                order_btn.clicked.connect(
                    lambda checked, id=quote_id: self.convert_to_order_clicked.emit(id)
                )
                btn_layout.addWidget(order_btn)

            # Sil (sadece taslak)
            if quote_status == "draft":
                del_btn = QPushButton("Sil")
                del_btn.setFixedSize(40, 28)
                del_btn.setToolTip("Sil")
                del_btn.clicked.connect(
                    lambda checked, id=quote_id: self._confirm_delete(id)
                )
                btn_layout.addWidget(del_btn)

            self.table.setCellWidget(row, 8, btn_widget)
            self.table.setRowHeight(row, 56)

    def _update_stats(self):
        """İstatistikleri güncelle"""
        total = len(self.quotes)
        draft = sum(1 for q in self.quotes if q.get("status") == "draft")
        sent = sum(1 for q in self.quotes if q.get("status") == "sent")
        accepted = sum(1 for q in self.quotes if q.get("status") == "accepted")
        rejected = sum(1 for q in self.quotes if q.get("status") == "rejected")

        self._update_card(self.total_card, str(total))
        self._update_card(self.draft_card, str(draft))
        self._update_card(self.sent_card, str(sent))
        self._update_card(self.accepted_card, str(accepted))
        self._update_card(self.rejected_card, str(rejected))

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
            for col in range(7):
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    def _on_filter_changed(self):
        """Filtre değişti"""
        self._apply_filter()

    def _on_double_click(self, index):
        """Çift tıklama"""
        row = index.row()
        item = self.table.item(row, 0)
        if item:
            quote_id = item.data(Qt.ItemDataRole.UserRole)
            if quote_id:
                self.view_clicked.emit(quote_id)

    def _confirm_delete(self, quote_id: int):
        """Silme onayı"""
        reply = QMessageBox.question(
            self,
            "Silme Onayı",
            "Bu teklifi silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(quote_id)
