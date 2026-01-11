"""
Akıllı İş - Depo Listesi Sayfası
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QAbstractItemView, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QAction

from config import COLORS

class WarehouseListPage(QWidget):
    """Depo listesi sayfası"""
    
    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()
    locations_clicked = pyqtSignal(int)  # Lokasyonları göster
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # === Başlık ===
        header_layout = QHBoxLayout()
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        
        title = QLabel("Depolar")
        subtitle = QLabel("Depo tanımlarını yönetin")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addLayout(title_layout)
        
        header_layout.addStretch()
        
        # Yenile
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        header_layout.addWidget(refresh_btn)
        
        # Yeni ekle
        add_btn = QPushButton("➕ Yeni Depo")
        add_btn.clicked.connect(self.add_clicked.emit)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        # === Arama ===
        search_frame = QFrame()
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(16, 12, 16, 12)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Depo kodu veya adı ile ara...")
        self.search_input.textChanged.connect(lambda: self.refresh_requested.emit())
        search_layout.addWidget(self.search_input)
        search_layout.addStretch()
        
        layout.addWidget(search_frame)
        
        # === Tablo ===
        self.table = QTableWidget()
        self._setup_table()
        layout.addWidget(self.table)
        
        # === Alt Bilgi ===
        self.count_label = QLabel("Toplam: 0 depo")
        layout.addWidget(self.count_label)
        
    def _setup_table(self):
        columns = [
            ("Kod", 100),
            ("Depo Adı", 200),
            ("Tür", 120),
            ("Şehir", 120),
            ("Yetkili", 150),
            ("Telefon", 120),
            ("Lokasyon", 80),
            ("Varsayılan", 90),
            ("Durum", 90),
        ]
        
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels([c[0] for c in columns])
        
        header = self.table.horizontalHeader()
        for i, (_, width) in enumerate(columns):
            if i == 1:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                self.table.setColumnWidth(i, width)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.doubleClicked.connect(self._on_double_click)
        
    def load_data(self, warehouses: list):
        """Verileri yükle"""
        self.table.setRowCount(len(warehouses))
        
        type_names = {
            "general": "🏭 Genel",
            "raw": "🧱 Hammadde",
            "finished": "📦 Mamul",
            "cold": "❄️ Soğuk",
            "bonded": "🔒 Antrepo",
        }
        
        for row, wh in enumerate(warehouses):
            # Kod
            code_item = QTableWidgetItem(wh.code)
            code_item.setData(Qt.ItemDataRole.UserRole, wh.id)
            code_item.setForeground(QColor("#818cf8"))
            self.table.setItem(row, 0, code_item)
            
            # Ad
            self.table.setItem(row, 1, QTableWidgetItem(wh.name))
            
            # Tür
            type_text = type_names.get(wh.warehouse_type, "🏭 Genel")
            self.table.setItem(row, 2, QTableWidgetItem(type_text))
            
            # Şehir
            self.table.setItem(row, 3, QTableWidgetItem(wh.city or "-"))
            
            # Yetkili
            self.table.setItem(row, 4, QTableWidgetItem(wh.manager_name or "-"))
            
            # Telefon
            self.table.setItem(row, 5, QTableWidgetItem(wh.phone or "-"))
            
            # Lokasyon sayısı
            loc_count = len(wh.locations) if wh.locations else 0
            loc_item = QTableWidgetItem(str(loc_count))
            loc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 6, loc_item)
            
            # Varsayılan
            default_item = QTableWidgetItem("✓" if wh.is_default else "")
            default_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if wh.is_default:
                default_item.setForeground(QColor(COLORS["success"]))
            self.table.setItem(row, 7, default_item)
            
            # Durum
            status_item = QTableWidgetItem("✅ Aktif" if wh.is_active else "❌ Pasif")
            status_item.setForeground(QColor(COLORS["success"] if wh.is_active else COLORS["error"]))
            self.table.setItem(row, 8, status_item)
        
        self.count_label.setText(f"Toplam: {len(warehouses)} depo")
        
    def get_search_text(self) -> str:
        return self.search_input.text().strip()
        
    def _show_context_menu(self, position):
        row = self.table.rowAt(position.y())
        if row < 0:
            return
            
        wh_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        menu = QMenu(self)
        edit_action = QAction("✏️ Düzenle", self)
        edit_action.triggered.connect(lambda: self.edit_clicked.emit(wh_id))
        menu.addAction(edit_action)
        
        loc_action = QAction("📍 Lokasyonlar", self)
        loc_action.triggered.connect(lambda: self.locations_clicked.emit(wh_id))
        menu.addAction(loc_action)
        
        menu.addSeparator()
        
        delete_action = QAction("🗑 Sil", self)
        delete_action.triggered.connect(lambda: self._confirm_delete(wh_id))
        menu.addAction(delete_action)
        
        menu.exec(self.table.viewport().mapToGlobal(position))
        
    def _on_double_click(self, index):
        wh_id = self.table.item(index.row(), 0).data(Qt.ItemDataRole.UserRole)
        self.edit_clicked.emit(wh_id)
        
    def _confirm_delete(self, wh_id: int):
        reply = QMessageBox.question(
            self, "Silme Onayı",
            "Bu depoyu silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(wh_id)
            