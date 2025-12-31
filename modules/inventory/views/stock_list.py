"""
Akıllı İş - Stok Kartları Liste Sayfası
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QComboBox, QAbstractItemView, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QAction, QColor

from config.settings import COLORS
from database.models import ItemType


class StockListPage(QWidget):
    """Stok kartları liste sayfası"""
    
    # Sinyaller
    item_selected = pyqtSignal(int)  # item_id
    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)  # item_id
    delete_clicked = pyqtSignal(int)  # item_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Başlık satırı
        header_layout = QHBoxLayout()
        
        # Sol: Başlık
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        
        title = QLabel("Stok Kartları")
        title.setObjectName("title")
        
        subtitle = QLabel("Tüm stok kartlarını görüntüle ve yönet")
        subtitle.setObjectName("subtitle")
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addLayout(title_layout)
        
        header_layout.addStretch()
        
        # Sağ: Butonlar
        export_btn = QPushButton("  Dışa Aktar")
        export_btn.setIcon(QIcon())  # İkon eklenecek
        
        add_btn = QPushButton("  Yeni Stok Kartı")
        add_btn.setProperty("primary", True)
        add_btn.clicked.connect(self.add_clicked.emit)
        
        header_layout.addWidget(export_btn)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        # Filtre alanı
        filter_frame = QFrame()
        filter_frame.setObjectName("card")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(16, 16, 16, 16)
        filter_layout.setSpacing(12)
        
        # Arama kutusu
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Stok kodu veya adı ile ara...")
        self.search_input.setMinimumWidth(300)
        self.search_input.textChanged.connect(self.on_search)
        filter_layout.addWidget(self.search_input)
        
        # Kategori filtresi
        filter_layout.addWidget(QLabel("Tür:"))
        self.type_combo = QComboBox()
        self.type_combo.addItem("Tümü", None)
        self.type_combo.addItem("Hammadde", ItemType.HAMMADDE)
        self.type_combo.addItem("Mamül", ItemType.MAMUL)
        self.type_combo.addItem("Yarı Mamül", ItemType.YARI_MAMUL)
        self.type_combo.addItem("Ambalaj", ItemType.AMBALAJ)
        self.type_combo.addItem("Sarf", ItemType.SARF)
        self.type_combo.currentIndexChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.type_combo)
        
        # Durum filtresi
        filter_layout.addWidget(QLabel("Durum:"))
        self.status_combo = QComboBox()
        self.status_combo.addItem("Tümü", None)
        self.status_combo.addItem("Normal", "normal")
        self.status_combo.addItem("Kritik Stok", "critical")
        self.status_combo.addItem("Stok Yok", "zero")
        self.status_combo.currentIndexChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.status_combo)
        
        filter_layout.addStretch()
        
        layout.addWidget(filter_frame)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setObjectName("dataTable")
        self.setup_table()
        layout.addWidget(self.table)
        
        # Alt bilgi satırı
        footer_layout = QHBoxLayout()
        
        self.count_label = QLabel("Toplam: 0 kayıt")
        self.count_label.setObjectName("subtitle")
        footer_layout.addWidget(self.count_label)
        
        footer_layout.addStretch()
        
        # Sayfalama (ileride eklenecek)
        
        layout.addLayout(footer_layout)
        
    def setup_table(self):
        """Tabloyu yapılandır"""
        # Sütunlar
        columns = [
            ("Kod", 100),
            ("Stok Adı", 250),
            ("Tür", 100),
            ("Birim", 70),
            ("Miktar", 100),
            ("Min. Stok", 90),
            ("Birim Fiyat", 100),
            ("Durum", 90),
        ]
        
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels([c[0] for c in columns])
        
        # Sütun genişlikleri
        header = self.table.horizontalHeader()
        for i, (_, width) in enumerate(columns):
            if i == 1:  # Stok Adı sütunu genişlesin
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                self.table.setColumnWidth(i, width)
        
        # Tablo ayarları
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        
        # Sağ tık menüsü
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Çift tık
        self.table.doubleClicked.connect(self.on_double_click)
        
    def load_data(self, items: list):
        """Tabloyu verilerle doldur"""
        self.table.setRowCount(len(items))
        
        for row, item in enumerate(items):
            # Kod
            code_item = QTableWidgetItem(item.code)
            code_item.setData(Qt.ItemDataRole.UserRole, item.id)
            code_item.setForeground(QColor(COLORS["primary"]))
            self.table.setItem(row, 0, code_item)
            
            # Ad
            self.table.setItem(row, 1, QTableWidgetItem(item.name))
            
            # Tür
            type_names = {
                ItemType.HAMMADDE: "Hammadde",
                ItemType.MAMUL: "Mamül",
                ItemType.YARI_MAMUL: "Yarı Mamül",
                ItemType.AMBALAJ: "Ambalaj",
                ItemType.SARF: "Sarf",
                ItemType.DIGER: "Diğer",
            }
            self.table.setItem(row, 2, QTableWidgetItem(type_names.get(item.item_type, "")))
            
            # Birim
            unit_text = item.unit.code if item.unit else ""
            self.table.setItem(row, 3, QTableWidgetItem(unit_text))
            
            # Miktar
            qty_item = QTableWidgetItem(f"{item.total_stock:,.2f}")
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 4, qty_item)
            
            # Min stok
            min_item = QTableWidgetItem(f"{item.min_stock:,.2f}")
            min_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 5, min_item)
            
            # Birim fiyat
            price_item = QTableWidgetItem(f"₺{item.purchase_price:,.2f}")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 6, price_item)
            
            # Durum
            status_item = QTableWidgetItem()
            if item.total_stock <= 0:
                status_item.setText("Stok Yok")
                status_item.setForeground(QColor(COLORS["error"]))
            elif item.min_stock > 0 and item.total_stock < item.min_stock:
                status_item.setText("Kritik")
                status_item.setForeground(QColor(COLORS["warning"]))
            else:
                status_item.setText("Normal")
                status_item.setForeground(QColor(COLORS["success"]))
            self.table.setItem(row, 7, status_item)
        
        self.count_label.setText(f"Toplam: {len(items)} kayıt")
        
    def on_search(self, text: str):
        """Arama yapıldığında"""
        # Parent widget'tan filtreleme yapılacak
        pass
        
    def on_filter_changed(self):
        """Filtre değiştiğinde"""
        # Parent widget'tan filtreleme yapılacak
        pass
        
    def show_context_menu(self, position):
        """Sağ tık menüsü"""
        row = self.table.rowAt(position.y())
        if row < 0:
            return
            
        item_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        menu = QMenu(self)
        
        view_action = QAction("👁 Görüntüle", self)
        view_action.triggered.connect(lambda: self.item_selected.emit(item_id))
        menu.addAction(view_action)
        
        edit_action = QAction("✏️ Düzenle", self)
        edit_action.triggered.connect(lambda: self.edit_clicked.emit(item_id))
        menu.addAction(edit_action)
        
        menu.addSeparator()
        
        delete_action = QAction("🗑 Sil", self)
        delete_action.triggered.connect(lambda: self.confirm_delete(item_id))
        menu.addAction(delete_action)
        
        menu.exec(self.table.viewport().mapToGlobal(position))
        
    def on_double_click(self, index):
        """Çift tıklandığında"""
        item_id = self.table.item(index.row(), 0).data(Qt.ItemDataRole.UserRole)
        self.edit_clicked.emit(item_id)
        
    def confirm_delete(self, item_id: int):
        """Silme onayı"""
        reply = QMessageBox.question(
            self, "Silme Onayı",
            "Bu stok kartını silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(item_id)
            
    def get_selected_item_id(self) -> int | None:
        """Seçili satırın item_id'sini döndür"""
        row = self.table.currentRow()
        if row >= 0:
            return self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        return None
