"""
Akıllı İş - Satış Siparişleri Liste Sayfası
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


class SalesOrderListPage(QWidget):
    """Satış siparişleri listesi"""

    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    view_clicked = pyqtSignal(int)
    confirm_clicked = pyqtSignal(int)
    cancel_clicked = pyqtSignal(int)
    create_delivery_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.orders = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("🛒 Satış Siparişleri")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Durum filtresi
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tüm Durumlar", None)
        self.status_filter.addItem("🔵 Taslak", "draft")
        self.status_filter.addItem("🟢 Onaylandı", "confirmed")
        self.status_filter.addItem("🟡 Kısmi Teslim", "partial_delivered")
        self.status_filter.addItem("✅ Teslim Edildi", "delivered")
        self.status_filter.addItem("🔒 Kapatıldı", "closed")
        self.status_filter.addItem("⚫ İptal", "cancelled")
        self.status_filter.setStyleSheet(self._combo_style())
        self.status_filter.setMinimumWidth(160)
        self.status_filter.currentIndexChanged.connect(self._on_filter_changed)
        header_layout.addWidget(self.status_filter)

        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ara... (sipariş no, müşteri)")
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
        add_btn = QPushButton(f"{ICONS['add']} Yeni Sipariş")
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

        self.confirmed_card = self._create_stat_card("🟢", "Onaylandı", "0", "#10b981")
        stats_layout.addWidget(self.confirmed_card)

        self.partial_card = self._create_stat_card("🟡", "Kısmi Teslim", "0", "#f59e0b")
        stats_layout.addWidget(self.partial_card)

        self.delivered_card = self._create_stat_card(
            "✅", "Teslim Edildi", "0", "#8b5cf6"
        )
        stats_layout.addWidget(self.delivered_card)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(
            [
                "Sipariş No",
                "Tarih",
                "Müşteri",
                "Toplam Tutar",
                "Kalem",
                "Teslim Tarihi",
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

        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 60)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(6, 130)
        self.table.setColumnWidth(7, 80)
        self.table.setColumnWidth(8, 200)

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

    def load_data(self, orders: list):
        """Verileri yükle"""
        self.orders = orders
        self._apply_filter()

    def _apply_filter(self):
        """Filtreyi uygula"""
        status_filter = self.status_filter.currentData()

        filtered = self.orders
        if status_filter:
            filtered = [o for o in self.orders if o.get("status") == status_filter]

        self._display_data(filtered)
        self._update_stats()

    def _display_data(self, orders: list):
        """Tabloya verileri yükle"""
        self.table.setRowCount(0)

        status_labels = {
            "draft": ("🔵 Taslak", "#64748b"),
            "confirmed": ("🟢 Onaylandı", "#10b981"),
            "partial_delivered": ("🟡 Kısmi Teslim", "#f59e0b"),
            "delivered": ("✅ Teslim Edildi", "#8b5cf6"),
            "closed": ("🔒 Kapatıldı", "#475569"),
            "cancelled": ("⚫ İptal", "#475569"),
        }

        for row, order in enumerate(orders):
            self.table.insertRow(row)

            # Sipariş No
            no_item = QTableWidgetItem(order.get("order_no", ""))
            no_item.setData(Qt.ItemDataRole.UserRole, order.get("id"))
            self.table.setItem(row, 0, no_item)

            # Tarih
            order_date = order.get("order_date")
            if order_date:
                if isinstance(order_date, date):
                    date_str = order_date.strftime("%d.%m.%Y")
                else:
                    date_str = str(order_date)
            else:
                date_str = "-"
            self.table.setItem(row, 1, QTableWidgetItem(date_str))

            # Müşteri
            self.table.setItem(
                row, 2, QTableWidgetItem(order.get("customer_name", "") or "-")
            )

            # Toplam Tutar
            total = order.get("total_amount", 0) or 0
            total_str = f"{total:,.2f}"
            self.table.setItem(row, 3, QTableWidgetItem(total_str))

            # Kalem Sayısı
            item_count = order.get("total_items", 0)
            self.table.setItem(row, 4, QTableWidgetItem(str(item_count)))

            # Teslim Tarihi
            delivery_date = order.get("delivery_date")
            if delivery_date:
                if isinstance(delivery_date, date):
                    delivery_str = delivery_date.strftime("%d.%m.%Y")
                else:
                    delivery_str = str(delivery_date)
            else:
                delivery_str = "-"
            self.table.setItem(row, 5, QTableWidgetItem(delivery_str))

            # Durum
            status = order.get("status", "draft")
            status_text, _ = status_labels.get(status, ("Taslak", "#64748b"))
            status_item = QTableWidgetItem(status_text)
            self.table.setItem(row, 6, status_item)

            # Para Birimi
            currency = order.get("currency_code", "TRY")
            self.table.setItem(row, 7, QTableWidgetItem(currency))

            # İşlem butonları
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(4)

            order_id = order.get("id")
            order_status = order.get("status", "draft")

            # Görüntüle
            view_btn = QPushButton("Gör")
            view_btn.setFixedSize(40, 28)
            view_btn.setToolTip("Görüntüle")
            view_btn.clicked.connect(
                lambda checked, id=order_id: self.view_clicked.emit(id)
            )
            btn_layout.addWidget(view_btn)

            # Düzenle (sadece taslak)
            if order_status == "draft":
                edit_btn = QPushButton("Düz")
                edit_btn.setFixedSize(40, 28)
                edit_btn.setToolTip("Düzenle")
                edit_btn.clicked.connect(
                    lambda checked, id=order_id: self.edit_clicked.emit(id)
                )
                btn_layout.addWidget(edit_btn)

                # Onayla
                confirm_btn = QPushButton("On")
                confirm_btn.setFixedSize(40, 28)
                confirm_btn.setToolTip("Onayla")
                confirm_btn.clicked.connect(
                    lambda checked, id=order_id: self.confirm_clicked.emit(id)
                )
                btn_layout.addWidget(confirm_btn)

            # İrsaliye Oluştur (confirmed veya partial_delivered)
            if order_status in ["confirmed", "partial_delivered"]:
                delivery_btn = QPushButton("Sev")
                delivery_btn.setFixedSize(40, 28)
                delivery_btn.setToolTip("İrsaliye Oluştur")
                delivery_btn.clicked.connect(
                    lambda checked, id=order_id: (self.create_delivery_clicked.emit(id))
                )
                btn_layout.addWidget(delivery_btn)

            # İptal (sadece taslak veya onaylanmış)
            if order_status in ["draft", "confirmed"]:
                cancel_btn = QPushButton("İpt")
                cancel_btn.setFixedSize(40, 28)
                cancel_btn.setToolTip("İptal Et")
                cancel_btn.clicked.connect(
                    lambda checked, id=order_id: self.cancel_clicked.emit(id)
                )
                btn_layout.addWidget(cancel_btn)

            # Sil (sadece taslak)
            if order_status == "draft":
                del_btn = QPushButton("Sil")
                del_btn.setFixedSize(40, 28)
                del_btn.setToolTip("Sil")
                del_btn.clicked.connect(
                    lambda checked, id=order_id: self._confirm_delete(id)
                )
                btn_layout.addWidget(del_btn)

            self.table.setCellWidget(row, 8, btn_widget)
            self.table.setRowHeight(row, 56)

    def _update_stats(self):
        """İstatistikleri güncelle"""
        total = len(self.orders)
        draft = sum(1 for o in self.orders if o.get("status") == "draft")
        confirmed = sum(1 for o in self.orders if o.get("status") == "confirmed")
        partial = sum(1 for o in self.orders if o.get("status") == "partial_delivered")
        delivered = sum(1 for o in self.orders if o.get("status") == "delivered")

        self._update_card(self.total_card, str(total))
        self._update_card(self.draft_card, str(draft))
        self._update_card(self.confirmed_card, str(confirmed))
        self._update_card(self.partial_card, str(partial))
        self._update_card(self.delivered_card, str(delivered))

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
            order_id = item.data(Qt.ItemDataRole.UserRole)
            if order_id:
                self.view_clicked.emit(order_id)

    def _confirm_delete(self, order_id: int):
        """Silme onayı"""
        reply = QMessageBox.question(
            self,
            "Silme Onayı",
            "Bu siparişi silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(order_id)
