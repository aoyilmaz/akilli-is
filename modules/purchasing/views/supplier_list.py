"""
Akıllı İş - Tedarikçi Liste Sayfası
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QFrame, QLineEdit,
    QHeaderView, QAbstractItemView, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal


class SupplierListPage(QWidget):
    """Tedarikçi listesi sayfası"""
    
    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    view_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.suppliers = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("🏢 Tedarikçiler")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f8fafc;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ara... (kod, ad, vergi no)")
        self.search_input.setFixedWidth(300)
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
        
        # Yenile butonu
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
        
        # Yeni ekle butonu
        add_btn = QPushButton("➕ Yeni Tedarikçi")
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
        
        self.active_card = self._create_stat_card("✅", "Aktif", "0", "#10b981")
        stats_layout.addWidget(self.active_card)
        
        self.with_orders_card = self._create_stat_card("📦", "Siparişli", "0", "#f59e0b")
        stats_layout.addWidget(self.with_orders_card)
        
        self.credit_card = self._create_stat_card("💳", "Toplam Limit", "₺0", "#3b82f6")
        stats_layout.addWidget(self.credit_card)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Kod", "Tedarikçi Adı", "Telefon", "E-posta", 
            "Şehir", "Vade (Gün)", "Puan", "İşlemler"
        ])
        
        # Tablo stili
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
        
    def _create_stat_card(self, icon: str, title: str, value: str, color: str) -> QFrame:
        card = QFrame()
        card.setFixedSize(160, 80)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color}15;
                border: 1px solid {color}30;
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        
        header = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 16px; background: transparent;")
        header.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {color}; font-size: 12px; background: transparent;")
        header.addWidget(title_label)
        header.addStretch()
        layout.addLayout(header)
        
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: bold; background: transparent;")
        layout.addWidget(value_label)
        
        return card
        
    def _update_card(self, card: QFrame, value: str):
        label = card.findChild(QLabel, "value")
        if label:
            label.setText(value)
    
    def load_data(self, suppliers: list):
        """Verileri yükle"""
        self.suppliers = suppliers
        self.table.setRowCount(0)
        
        total = len(suppliers)
        active = 0
        total_credit = 0
        
        for sup in suppliers:
            if sup.get("is_active", True):
                active += 1
            total_credit += float(sup.get("credit_limit", 0) or 0)
        
        self._update_card(self.total_card, str(total))
        self._update_card(self.active_card, str(active))
        self._update_card(self.credit_card, f"₺{total_credit:,.0f}")
        
        for row, sup in enumerate(suppliers):
            self.table.insertRow(row)
            
            # Kod
            code_item = QTableWidgetItem(sup.get("code", ""))
            code_item.setData(Qt.ItemDataRole.UserRole, sup.get("id"))
            self.table.setItem(row, 0, code_item)
            
            # Ad
            self.table.setItem(row, 1, QTableWidgetItem(sup.get("name", "")))
            
            # Telefon
            self.table.setItem(row, 2, QTableWidgetItem(sup.get("phone", "") or "-"))
            
            # E-posta
            self.table.setItem(row, 3, QTableWidgetItem(sup.get("email", "") or "-"))
            
            # Şehir
            self.table.setItem(row, 4, QTableWidgetItem(sup.get("city", "") or "-"))
            
            # Vade
            vade = sup.get("payment_term_days", 0) or 0
            self.table.setItem(row, 5, QTableWidgetItem(str(vade)))
            
            # Puan
            rating = sup.get("rating", 0) or 0
            stars = "⭐" * rating if rating > 0 else "-"
            self.table.setItem(row, 6, QTableWidgetItem(stars))
            
            # İşlem butonları
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(4)
            
            view_btn = QPushButton("👁")
            view_btn.setFixedSize(32, 32)
            view_btn.setStyleSheet(self._action_btn_style("#3b82f6"))
            view_btn.setToolTip("Görüntüle")
            view_btn.clicked.connect(lambda checked, id=sup.get("id"): self.view_clicked.emit(id))
            btn_layout.addWidget(view_btn)
            
            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(32, 32)
            edit_btn.setStyleSheet(self._action_btn_style("#f59e0b"))
            edit_btn.setToolTip("Düzenle")
            edit_btn.clicked.connect(lambda checked, id=sup.get("id"): self.edit_clicked.emit(id))
            btn_layout.addWidget(edit_btn)
            
            del_btn = QPushButton("🗑")
            del_btn.setFixedSize(32, 32)
            del_btn.setStyleSheet(self._action_btn_style("#ef4444"))
            del_btn.setToolTip("Sil")
            del_btn.clicked.connect(lambda checked, id=sup.get("id"): self._confirm_delete(id))
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
            for col in range(6):  # İlk 6 kolon
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
            supplier_id = item.data(Qt.ItemDataRole.UserRole)
            if supplier_id:
                self.view_clicked.emit(supplier_id)
                
    def _confirm_delete(self, supplier_id: int):
        """Silme onayı"""
        reply = QMessageBox.question(
            self, "Silme Onayı",
            "Bu tedarikçiyi silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(supplier_id)
