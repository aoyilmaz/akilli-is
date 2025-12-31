"""
Akıllı İş - Stok Kartları Liste Sayfası
"""

from decimal import Decimal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QComboBox, QAbstractItemView, QMenu, QMessageBox,
    QStyledItemDelegate
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QAction

from config import COLORS
from database.models import ItemType


class StockListPage(QWidget):
    """Stok kartları liste sayfası"""
    
    # Sinyaller
    item_selected = pyqtSignal(int)
    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items_data = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # === Başlık Satırı ===
        header_layout = QHBoxLayout()
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        
        title = QLabel("Stok Kartları")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f8fafc;")
        
        subtitle = QLabel("Tüm stok kartlarını görüntüle ve yönet")
        subtitle.setStyleSheet("font-size: 14px; color: #94a3b8;")
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addLayout(title_layout)
        
        header_layout.addStretch()
        
        # Yenile butonu
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        header_layout.addWidget(refresh_btn)
        
        # Dışa aktar butonu
        export_btn = QPushButton("📤 Dışa Aktar")
        header_layout.addWidget(export_btn)
        
        # Yeni ekle butonu
        add_btn = QPushButton("➕ Yeni Stok Kartı")
        add_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #a855f7);
                border: none;
                color: white;
                font-weight: 600;
                padding: 12px 24px;
                border-radius: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #9333ea);
            }
        """)
        add_btn.clicked.connect(self.add_clicked.emit)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        # === Filtre Alanı ===
        filter_frame = QFrame()
        filter_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 41, 59, 0.5);
                border: 1px solid #334155;
                border-radius: 16px;
                padding: 8px;
            }
        """)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(16, 12, 16, 12)
        filter_layout.setSpacing(16)
        
        # Arama kutusu
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Stok kodu, adı veya barkod ile ara...")
        self.search_input.setMinimumWidth(300)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px 16px;
                color: #f8fafc;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #6366f1;
            }
        """)
        
        # Arama için debounce timer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._do_search)
        self.search_input.textChanged.connect(self._on_search_changed)
        
        filter_layout.addWidget(self.search_input)
        
        # Tür filtresi
        type_label = QLabel("Tür:")
        type_label.setStyleSheet("color: #94a3b8;")
        filter_layout.addWidget(type_label)
        
        self.type_combo = QComboBox()
        self.type_combo.addItem("Tümü", None)
        self.type_combo.addItem("🧱 Hammadde", ItemType.HAMMADDE)
        self.type_combo.addItem("📦 Mamül", ItemType.MAMUL)
        self.type_combo.addItem("⚙️ Yarı Mamül", ItemType.YARI_MAMUL)
        self.type_combo.addItem("🎁 Ambalaj", ItemType.AMBALAJ)
        self.type_combo.addItem("🔧 Sarf", ItemType.SARF)
        self.type_combo.addItem("🏷️ Ticari", ItemType.TICARI)
        self.type_combo.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 8px 16px;
                color: #f8fafc;
                min-width: 140px;
            }
        """)
        self.type_combo.currentIndexChanged.connect(self._do_search)
        filter_layout.addWidget(self.type_combo)
        
        # Durum filtresi
        status_label = QLabel("Durum:")
        status_label.setStyleSheet("color: #94a3b8;")
        filter_layout.addWidget(status_label)
        
        self.status_combo = QComboBox()
        self.status_combo.addItem("Tümü", None)
        self.status_combo.addItem("✅ Normal", "normal")
        self.status_combo.addItem("⚠️ Düşük Stok", "low")
        self.status_combo.addItem("🔴 Kritik", "critical")
        self.status_combo.addItem("❌ Stok Yok", "out_of_stock")
        self.status_combo.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 8px 16px;
                color: #f8fafc;
                min-width: 140px;
            }
        """)
        self.status_combo.currentIndexChanged.connect(self._do_search)
        filter_layout.addWidget(self.status_combo)
        
        filter_layout.addStretch()
        
        layout.addWidget(filter_frame)
        
        # === Tablo ===
        self.table = QTableWidget()
        self.setup_table()
        layout.addWidget(self.table)
        
        # === Alt Bilgi ===
        footer_layout = QHBoxLayout()
        
        self.count_label = QLabel("Toplam: 0 kayıt")
        self.count_label.setStyleSheet("color: #64748b; font-size: 13px;")
        footer_layout.addWidget(self.count_label)
        
        footer_layout.addStretch()
        
        # Stok değeri
        self.value_label = QLabel("Toplam Değer: ₺0,00")
        self.value_label.setStyleSheet("color: #64748b; font-size: 13px;")
        footer_layout.addWidget(self.value_label)
        
        layout.addLayout(footer_layout)
        
    def setup_table(self):
        """Tabloyu yapılandır"""
        columns = [
            ("Kod", 100),
            ("Stok Adı", 280),
            ("Tür", 100),
            ("Kategori", 120),
            ("Birim", 70),
            ("Miktar", 100),
            ("Min. Stok", 90),
            ("Alış Fiyatı", 110),
            ("Satış Fiyatı", 110),
            ("Durum", 100),
        ]
        
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels([c[0] for c in columns])
        
        # Sütun genişlikleri
        header = self.table.horizontalHeader()
        for i, (_, width) in enumerate(columns):
            if i == 1:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                self.table.setColumnWidth(i, width)
        
        # Tablo ayarları
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        
        # Stil
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(30, 41, 59, 0.3);
                border: 1px solid #334155;
                border-radius: 12px;
                gridline-color: transparent;
            }
            QTableWidget::item {
                padding: 12px 8px;
                border-bottom: 1px solid #334155;
            }
            QTableWidget::item:selected {
                background-color: rgba(99, 102, 241, 0.2);
            }
            QTableWidget::item:hover {
                background-color: rgba(51, 65, 85, 0.5);
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #94a3b8;
                font-weight: 600;
                padding: 12px 8px;
                border: none;
                border-bottom: 1px solid #334155;
            }
        """)
        
        # Sağ tık menüsü
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Çift tık
        self.table.doubleClicked.connect(self._on_double_click)
        
    def load_data(self, items: list):
        """Tabloyu verilerle doldur"""
        self.items_data = items
        self.table.setRowCount(len(items))
        
        type_names = {
            ItemType.HAMMADDE: "🧱 Hammadde",
            ItemType.MAMUL: "📦 Mamül",
            ItemType.YARI_MAMUL: "⚙️ Yarı Mamül",
            ItemType.AMBALAJ: "🎁 Ambalaj",
            ItemType.SARF: "🔧 Sarf",
            ItemType.TICARI: "🏷️ Ticari",
            ItemType.HIZMET: "💼 Hizmet",
            ItemType.DIGER: "📋 Diğer",
        }
        
        total_value = Decimal(0)
        
        for row, item in enumerate(items):
            # Kod
            code_item = QTableWidgetItem(item.code)
            code_item.setData(Qt.ItemDataRole.UserRole, item.id)
            code_item.setForeground(QColor("#818cf8"))
            self.table.setItem(row, 0, code_item)
            
            # Ad
            self.table.setItem(row, 1, QTableWidgetItem(item.name))
            
            # Tür
            type_text = type_names.get(item.item_type, "📋 Diğer")
            self.table.setItem(row, 2, QTableWidgetItem(type_text))
            
            # Kategori
            cat_text = item.category.name if item.category else "-"
            self.table.setItem(row, 3, QTableWidgetItem(cat_text))
            
            # Birim
            unit_text = item.unit.code if item.unit else "-"
            self.table.setItem(row, 4, QTableWidgetItem(unit_text))
            
            # Miktar
            total_stock = item.total_stock or Decimal(0)
            qty_item = QTableWidgetItem(f"{total_stock:,.2f}")
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 5, qty_item)
            
            # Min stok
            min_stock = item.min_stock or Decimal(0)
            min_item = QTableWidgetItem(f"{min_stock:,.2f}")
            min_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 6, min_item)
            
            # Alış fiyatı
            purchase_price = item.purchase_price or Decimal(0)
            purchase_item = QTableWidgetItem(f"₺{purchase_price:,.2f}")
            purchase_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 7, purchase_item)
            
            # Satış fiyatı
            sale_price = item.sale_price or Decimal(0)
            sale_item = QTableWidgetItem(f"₺{sale_price:,.2f}")
            sale_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 8, sale_item)
            
            # Durum
            status_item = QTableWidgetItem()
            status = item.stock_status
            if status == "out_of_stock":
                status_item.setText("❌ Stok Yok")
                status_item.setForeground(QColor(COLORS["error"]))
            elif status == "critical":
                status_item.setText("🔴 Kritik")
                status_item.setForeground(QColor(COLORS["error"]))
            elif status == "low":
                status_item.setText("⚠️ Düşük")
                status_item.setForeground(QColor(COLORS["warning"]))
            else:
                status_item.setText("✅ Normal")
                status_item.setForeground(QColor(COLORS["success"]))
            self.table.setItem(row, 9, status_item)
            
            # Toplam değer hesapla
            total_value += total_stock * purchase_price
        
        self.count_label.setText(f"Toplam: {len(items)} kayıt")
        self.value_label.setText(f"Toplam Değer: ₺{total_value:,.2f}")
        
    def _on_search_changed(self, text: str):
        """Arama metni değiştiğinde (debounce)"""
        self.search_timer.stop()
        self.search_timer.start(300)
        
    def _do_search(self):
        """Aramayı gerçekleştir"""
        self.refresh_requested.emit()
        
    def get_filters(self) -> dict:
        """Mevcut filtreleri döndür"""
        return {
            "keyword": self.search_input.text().strip(),
            "item_type": self.type_combo.currentData(),
            "stock_status": self.status_combo.currentData(),
        }
        
    def show_context_menu(self, position):
        """Sağ tık menüsü"""
        row = self.table.rowAt(position.y())
        if row < 0:
            return
            
        item_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #334155;
            }
        """)
        
        view_action = QAction("👁 Görüntüle", self)
        view_action.triggered.connect(lambda: self.item_selected.emit(item_id))
        menu.addAction(view_action)
        
        edit_action = QAction("✏️ Düzenle", self)
        edit_action.triggered.connect(lambda: self.edit_clicked.emit(item_id))
        menu.addAction(edit_action)
        
        menu.addSeparator()
        
        movement_action = QAction("📦 Stok Hareketi", self)
        menu.addAction(movement_action)
        
        history_action = QAction("📋 Hareket Geçmişi", self)
        menu.addAction(history_action)
        
        menu.addSeparator()
        
        delete_action = QAction("🗑 Sil", self)
        delete_action.triggered.connect(lambda: self._confirm_delete(item_id))
        menu.addAction(delete_action)
        
        menu.exec(self.table.viewport().mapToGlobal(position))
        
    def _on_double_click(self, index):
        """Çift tıklandığında"""
        item_id = self.table.item(index.row(), 0).data(Qt.ItemDataRole.UserRole)
        self.edit_clicked.emit(item_id)
        
    def _confirm_delete(self, item_id: int):
        """Silme onayı"""
        reply = QMessageBox.question(
            self, "Silme Onayı",
            "Bu stok kartını silmek istediğinize emin misiniz?\n\nBu işlem geri alınamaz.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(item_id)
