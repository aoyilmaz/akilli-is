"""
Akıllı İş - Satın Alma Siparişleri Liste Sayfası
"""

from datetime import date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QFrame, QLineEdit,
    QHeaderView, QAbstractItemView, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal


class PurchaseOrderListPage(QWidget):
    """Satın alma siparişleri listesi"""
    
    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    view_clicked = pyqtSignal(int)
    send_clicked = pyqtSignal(int)
    receive_clicked = pyqtSignal(int)
    create_receipt_clicked = pyqtSignal(int)
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
        
        title = QLabel("📦 Satın Alma Siparişleri")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f8fafc;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Durum filtresi
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tüm Durumlar", None)
        self.status_filter.addItem("🔵 Taslak", "draft")
        self.status_filter.addItem("📤 Gönderildi", "sent")
        self.status_filter.addItem("✅ Onaylandı", "confirmed")
        self.status_filter.addItem("🟡 Kısmi Teslim", "partial")
        self.status_filter.addItem("🟢 Teslim Alındı", "received")
        self.status_filter.addItem("⚫ Kapatıldı", "closed")
        self.status_filter.addItem("🔴 İptal", "cancelled")
        self.status_filter.setStyleSheet(self._combo_style())
        self.status_filter.setMinimumWidth(160)
        self.status_filter.currentIndexChanged.connect(self._on_filter_changed)
        header_layout.addWidget(self.status_filter)
        
        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ara... (sipariş no, tedarikçi)")
        self.search_input.setFixedWidth(250)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px 14px;
                color: #f8fafc;
                font-size: 14px;
            }
            QLineEdit:focus { border-color: #6366f1; }
        """)
        self.search_input.textChanged.connect(self._on_search)
        header_layout.addWidget(self.search_input)
        
        # Yenile
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(42, 42)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                font-size: 18px;
            }
            QPushButton:hover { background-color: #334155; }
        """)
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        header_layout.addWidget(refresh_btn)
        
        # Yeni sipariş
        add_btn = QPushButton("➕ Yeni Sipariş")
        add_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #a855f7);
                border: none;
                color: white;
                font-weight: 600;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #9333ea);
            }
        """)
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
        
        self.open_card = self._create_stat_card("📤", "Açık", "0", "#f59e0b")
        stats_layout.addWidget(self.open_card)
        
        self.received_card = self._create_stat_card("🟢", "Teslim", "0", "#10b981")
        stats_layout.addWidget(self.received_card)
        
        self.total_amount_card = self._create_stat_card("💰", "Toplam Tutar", "₺0", "#8b5cf6")
        stats_layout.addWidget(self.total_amount_card)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Sipariş No", "Tarih", "Tedarikçi", "Teslim Tarihi",
            "Kalem", "Tutar", "Durum", "Teslim %", "İşlemler"
        ])
        
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 12px;
                gridline-color: #1e293b;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #1e293b;
                color: #f8fafc;
            }
            QTableWidget::item:selected {
                background-color: #6366f120;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #94a3b8;
                padding: 12px;
                border: none;
                font-weight: 600;
                font-size: 12px;
            }
        """)
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(1, 90)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 50)
        self.table.setColumnWidth(5, 110)
        self.table.setColumnWidth(6, 110)
        self.table.setColumnWidth(7, 70)
        self.table.setColumnWidth(8, 180)
        
        self.table.doubleClicked.connect(self._on_double_click)
        
        layout.addWidget(self.table)
        
    def _create_stat_card(self, icon: str, title: str, value: str, color: str) -> QFrame:
        card = QFrame()
        card.setFixedSize(150, 80)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color}15;
                border: 1px solid {color}30;
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)
        
        header = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 14px; background: transparent;")
        header.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {color}; font-size: 11px; background: transparent;")
        header.addWidget(title_label)
        header.addStretch()
        layout.addLayout(header)
        
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold; background: transparent;")
        layout.addWidget(value_label)
        
        return card
        
    def _update_card(self, card: QFrame, value: str):
        label = card.findChild(QLabel, "value")
        if label:
            label.setText(value)
    
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
    
    def load_data(self, orders: list):
        """Verileri yükle"""
        self.orders = orders
        self._apply_filter()
        
    def _apply_filter(self):
        status_filter = self.status_filter.currentData()
        
        filtered = self.orders
        if status_filter:
            filtered = [o for o in self.orders if o.get("status") == status_filter]
        
        self._display_data(filtered)
        self._update_stats()
        
    def _display_data(self, orders: list):
        self.table.setRowCount(0)
        
        status_labels = {
            "draft": ("🔵 Taslak", "#64748b"),
            "sent": ("📤 Gönderildi", "#3b82f6"),
            "confirmed": ("✅ Onaylandı", "#10b981"),
            "partial": ("🟡 Kısmi", "#f59e0b"),
            "received": ("🟢 Teslim", "#10b981"),
            "closed": ("⚫ Kapalı", "#475569"),
            "cancelled": ("🔴 İptal", "#ef4444"),
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
            
            # Tedarikçi
            self.table.setItem(row, 2, QTableWidgetItem(order.get("supplier_name", "") or "-"))
            
            # Teslim Tarihi
            delivery_date = order.get("delivery_date")
            if delivery_date:
                if isinstance(delivery_date, date):
                    del_str = delivery_date.strftime("%d.%m.%Y")
                else:
                    del_str = str(delivery_date)
            else:
                del_str = "-"
            self.table.setItem(row, 3, QTableWidgetItem(del_str))
            
            # Kalem
            self.table.setItem(row, 4, QTableWidgetItem(str(order.get("total_items", 0))))
            
            # Tutar
            total = order.get("total", 0) or 0
            currency = order.get("currency", "TRY")
            symbol = {"TRY": "₺", "USD": "$", "EUR": "€", "GBP": "£"}.get(currency, "₺")
            self.table.setItem(row, 5, QTableWidgetItem(f"{symbol}{float(total):,.2f}"))
            
            # Durum
            status = order.get("status", "draft")
            status_text, _ = status_labels.get(status, ("Taslak", "#64748b"))
            self.table.setItem(row, 6, QTableWidgetItem(status_text))
            
            # Teslim %
            received_rate = order.get("received_rate", 0) or 0
            self.table.setItem(row, 7, QTableWidgetItem(f"%{int(received_rate)}"))
            
            # İşlem butonları
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(4)
            
            order_id = order.get("id")
            order_status = order.get("status", "draft")
            
            # Görüntüle
            view_btn = QPushButton("👁")
            view_btn.setFixedSize(32, 32)
            view_btn.setStyleSheet(self._action_btn_style("#3b82f6"))
            view_btn.setToolTip("Görüntüle")
            view_btn.clicked.connect(lambda checked, id=order_id: self.view_clicked.emit(id))
            btn_layout.addWidget(view_btn)
            
            if order_status == "draft":
                # Düzenle
                edit_btn = QPushButton("✏️")
                edit_btn.setFixedSize(32, 32)
                edit_btn.setStyleSheet(self._action_btn_style("#f59e0b"))
                edit_btn.setToolTip("Düzenle")
                edit_btn.clicked.connect(lambda checked, id=order_id: self.edit_clicked.emit(id))
                btn_layout.addWidget(edit_btn)
                
                # Gönder
                send_btn = QPushButton("📤")
                send_btn.setFixedSize(32, 32)
                send_btn.setStyleSheet(self._action_btn_style("#10b981"))
                send_btn.setToolTip("Tedarikçiye Gönder")
                send_btn.clicked.connect(lambda checked, id=order_id: self.send_clicked.emit(id))
                btn_layout.addWidget(send_btn)
                
                # Sil
                del_btn = QPushButton("🗑")
                del_btn.setFixedSize(32, 32)
                del_btn.setStyleSheet(self._action_btn_style("#ef4444"))
                del_btn.setToolTip("Sil")
                del_btn.clicked.connect(lambda checked, id=order_id: self._confirm_delete(id))
                btn_layout.addWidget(del_btn)
                
            elif order_status in ["sent", "confirmed", "partial"]:
                # Mal Kabul
                receive_btn = QPushButton("📥")
                receive_btn.setFixedSize(32, 32)
                receive_btn.setStyleSheet(self._action_btn_style("#8b5cf6"))
                receive_btn.setToolTip("Mal Kabul Oluştur")
                receive_btn.clicked.connect(lambda checked, id=order_id: self.create_receipt_clicked.emit(id))
                btn_layout.addWidget(receive_btn)
            
            self.table.setCellWidget(row, 8, btn_widget)
            self.table.setRowHeight(row, 56)
            
    def _update_stats(self):
        total = len(self.orders)
        draft = sum(1 for o in self.orders if o.get("status") == "draft")
        open_orders = sum(1 for o in self.orders if o.get("status") in ["sent", "confirmed", "partial"])
        received = sum(1 for o in self.orders if o.get("status") in ["received", "closed"])
        total_amount = sum(float(o.get("total", 0) or 0) for o in self.orders)
        
        self._update_card(self.total_card, str(total))
        self._update_card(self.draft_card, str(draft))
        self._update_card(self.open_card, str(open_orders))
        self._update_card(self.received_card, str(received))
        self._update_card(self.total_amount_card, f"₺{total_amount:,.0f}")
        
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
            for col in range(6):
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
            order_id = item.data(Qt.ItemDataRole.UserRole)
            if order_id:
                self.view_clicked.emit(order_id)
                
    def _confirm_delete(self, order_id: int):
        reply = QMessageBox.question(
            self, "Silme Onayı",
            "Bu siparişi silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(order_id)
