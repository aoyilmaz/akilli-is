"""
Akıllı İş - Mal Kabul Liste Sayfası
"""

from datetime import date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QFrame, QLineEdit,
    QHeaderView, QAbstractItemView, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from ui.components.stat_cards import MiniStatCard

class GoodsReceiptListPage(QWidget):
    """Mal kabul listesi"""
    
    add_clicked = pyqtSignal()
    add_from_order_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    view_clicked = pyqtSignal(int)
    complete_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.receipts = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("📥 Mal Kabul")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Durum filtresi
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tüm Durumlar", None)
        self.status_filter.addItem("🔵 Taslak", "draft")
        self.status_filter.addItem("🟢 Tamamlandı", "completed")
        self.status_filter.addItem("⚫ İptal", "cancelled")
        self.status_filter.setStyleSheet(self._combo_style())
        self.status_filter.setMinimumWidth(150)
        self.status_filter.currentIndexChanged.connect(self._on_filter_changed)
        header_layout.addWidget(self.status_filter)
        
        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ara... (fiş no, tedarikçi)")
        self.search_input.setFixedWidth(250)
        self.search_input.textChanged.connect(self._on_search)
        header_layout.addWidget(self.search_input)
        
        # Yenile
        refresh_btn = QPushButton("Yen")
        refresh_btn.setFixedSize(42, 42)
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        header_layout.addWidget(refresh_btn)
        
        # Siparişten Mal Kabul
        from_order_btn = QPushButton("📦 Siparişten")
        from_order_btn.clicked.connect(self.add_from_order_clicked.emit)
        header_layout.addWidget(from_order_btn)
        
        # Yeni (manuel)
        add_btn = QPushButton("➕ Manuel Giriş")
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
        
        self.completed_card = self._create_stat_card("🟢", "Tamamlandı", "0", "#10b981")
        stats_layout.addWidget(self.completed_card)
        
        self.today_card = self._create_stat_card("📅", "Bugün", "0", "#f59e0b")
        stats_layout.addWidget(self.today_card)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Fiş No", "Tarih", "Tedarikçi", "Sipariş No",
            "Depo", "Kalem", "Durum", "İşlemler"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 60)
        self.table.setColumnWidth(6, 110)
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
    
    def load_data(self, receipts: list):
        """Verileri yükle"""
        self.receipts = receipts
        self._apply_filter()
        
    def _apply_filter(self):
        status_filter = self.status_filter.currentData()
        
        filtered = self.receipts
        if status_filter:
            filtered = [r for r in self.receipts if r.get("status") == status_filter]
        
        self._display_data(filtered)
        self._update_stats()
        
    def _display_data(self, receipts: list):
        self.table.setRowCount(0)
        
        status_labels = {
            "draft": ("🔵 Taslak", "#64748b"),
            "completed": ("🟢 Tamamlandı", "#10b981"),
            "cancelled": ("⚫ İptal", "#475569"),
        }
        
        for row, rec in enumerate(receipts):
            self.table.insertRow(row)
            
            # Fiş No
            no_item = QTableWidgetItem(rec.get("receipt_no", ""))
            no_item.setData(Qt.ItemDataRole.UserRole, rec.get("id"))
            self.table.setItem(row, 0, no_item)
            
            # Tarih
            rec_date = rec.get("receipt_date")
            if rec_date:
                if isinstance(rec_date, date):
                    date_str = rec_date.strftime("%d.%m.%Y")
                else:
                    date_str = str(rec_date)
            else:
                date_str = "-"
            self.table.setItem(row, 1, QTableWidgetItem(date_str))
            
            # Tedarikçi
            self.table.setItem(row, 2, QTableWidgetItem(rec.get("supplier_name", "") or "-"))
            
            # Sipariş No
            self.table.setItem(row, 3, QTableWidgetItem(rec.get("order_no", "") or "-"))
            
            # Depo
            self.table.setItem(row, 4, QTableWidgetItem(rec.get("warehouse_name", "") or "-"))
            
            # Kalem
            self.table.setItem(row, 5, QTableWidgetItem(str(rec.get("total_items", 0))))
            
            # Durum
            status = rec.get("status", "draft")
            status_text, _ = status_labels.get(status, ("Taslak", "#64748b"))
            self.table.setItem(row, 6, QTableWidgetItem(status_text))
            
            # İşlem butonları
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(4)
            
            rec_id = rec.get("id")
            rec_status = rec.get("status", "draft")
            
            # Görüntüle
            view_btn = QPushButton("Gör")
            view_btn.setFixedSize(40, 28)
            view_btn.setToolTip("Görüntüle")
            view_btn.clicked.connect(lambda checked, id=rec_id: self.view_clicked.emit(id))
            btn_layout.addWidget(view_btn)
            
            if rec_status == "draft":
                # Düzenle
                edit_btn = QPushButton("Düz")
                edit_btn.setFixedSize(40, 28)
                edit_btn.setToolTip("Düzenle")
                edit_btn.clicked.connect(lambda checked, id=rec_id: self.edit_clicked.emit(id))
                btn_layout.addWidget(edit_btn)
                
                # Tamamla
                complete_btn = QPushButton("On")
                complete_btn.setFixedSize(40, 28)
                complete_btn.setToolTip("Tamamla (Stok Girişi)")
                complete_btn.clicked.connect(lambda checked, id=rec_id: self.complete_clicked.emit(id))
                btn_layout.addWidget(complete_btn)
                
                # Sil
                del_btn = QPushButton("Sil")
                del_btn.setFixedSize(40, 28)
                del_btn.setToolTip("Sil")
                del_btn.clicked.connect(lambda checked, id=rec_id: self._confirm_delete(id))
                btn_layout.addWidget(del_btn)
            
            self.table.setCellWidget(row, 7, btn_widget)
            self.table.setRowHeight(row, 56)
            
    def _update_stats(self):
        total = len(self.receipts)
        draft = sum(1 for r in self.receipts if r.get("status") == "draft")
        completed = sum(1 for r in self.receipts if r.get("status") == "completed")
        today = sum(1 for r in self.receipts if r.get("receipt_date") == date.today())
        
        self._update_card(self.total_card, str(total))
        self._update_card(self.draft_card, str(draft))
        self._update_card(self.completed_card, str(completed))
        self._update_card(self.today_card, str(today))
        
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
            receipt_id = item.data(Qt.ItemDataRole.UserRole)
            if receipt_id:
                self.view_clicked.emit(receipt_id)
                
    def _confirm_delete(self, receipt_id: int):
        reply = QMessageBox.question(
            self, "Silme Onayı",
            "Bu mal kabul fişini silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(receipt_id)
