"""
Akıllı İş - Kategori Listesi Sayfası
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTreeWidget, QTreeWidgetItem, QFrame,
    QAbstractItemView, QMenu, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QAction, QIcon

from config import COLORS

class CategoryListPage(QWidget):
    """Kategori listesi (ağaç yapısı)"""
    
    add_clicked = pyqtSignal()
    add_child_clicked = pyqtSignal(int)  # Alt kategori ekle
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.categories_data = {}
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # === Başlık ===
        header_layout = QHBoxLayout()
        
        title_layout = QVBoxLayout()
        title = QLabel("Stok Kategorileri")
        subtitle = QLabel("Hiyerarşik kategori yapısını yönetin")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addLayout(title_layout)
        
        header_layout.addStretch()
        
        # Genişlet/Daralt
        expand_btn = QPushButton("📂 Tümünü Aç")
        expand_btn.clicked.connect(lambda: self.tree.expandAll())
        header_layout.addWidget(expand_btn)
        
        collapse_btn = QPushButton("📁 Tümünü Kapat")
        collapse_btn.clicked.connect(lambda: self.tree.collapseAll())
        header_layout.addWidget(collapse_btn)
        
        # Yenile
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        header_layout.addWidget(refresh_btn)
        
        # Yeni ekle
        add_btn = QPushButton("➕ Yeni Kategori")
        add_btn.clicked.connect(self.add_clicked.emit)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        # === Arama ===
        search_frame = QFrame()
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(16, 12, 16, 12)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Kategori ara...")
        self.search_input.textChanged.connect(self._filter_tree)
        search_layout.addWidget(self.search_input)
        search_layout.addStretch()
        
        layout.addWidget(search_frame)
        
        # === Ağaç Görünümü ===
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Kategori", "Kod", "Ürün Sayısı", "Durum"])
        self.tree.setColumnCount(4)
        
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.tree.setColumnWidth(1, 120)
        self.tree.setColumnWidth(2, 100)
        self.tree.setColumnWidth(3, 100)
        
        self.tree.setAlternatingRowColors(True)
        self.tree.setAnimated(True)
        self.tree.setIndentation(24)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        
        layout.addWidget(self.tree)
        
        # === Alt Bilgi ===
        self.count_label = QLabel("Toplam: 0 kategori")
        layout.addWidget(self.count_label)
        
    def load_data(self, categories: list):
        """Kategorileri yükle"""
        self.tree.clear()
        self.categories_data = {cat.id: cat for cat in categories}
        
        # Kök kategorileri bul
        root_cats = [c for c in categories if c.parent_id is None]
        
        for cat in root_cats:
            item = self._create_tree_item(cat)
            self.tree.addTopLevelItem(item)
            self._add_children(item, cat.id, categories)
        
        self.tree.expandAll()
        self.count_label.setText(f"Toplam: {len(categories)} kategori")
        
    def _create_tree_item(self, category) -> QTreeWidgetItem:
        """Ağaç öğesi oluştur"""
        item = QTreeWidgetItem()
        
        # İkon + Ad
        icon = category.icon or "📁"
        item.setText(0, f"{icon} {category.name}")
        item.setData(0, Qt.ItemDataRole.UserRole, category.id)
        
        # Kod
        item.setText(1, category.code)
        item.setForeground(1, QColor("#818cf8"))
        
        # Ürün sayısı
        product_count = len(category.items) if hasattr(category, 'items') else 0
        item.setText(2, str(product_count))
        item.setTextAlignment(2, Qt.AlignmentFlag.AlignCenter)
        
        # Durum
        status = "✅ Aktif" if category.is_active else "❌ Pasif"
        item.setText(3, status)
        item.setForeground(3, QColor(COLORS["success"] if category.is_active else COLORS["error"]))
        
        return item
        
    def _add_children(self, parent_item: QTreeWidgetItem, parent_id: int, categories: list):
        """Alt kategorileri ekle"""
        children = [c for c in categories if c.parent_id == parent_id]
        for cat in children:
            child_item = self._create_tree_item(cat)
            parent_item.addChild(child_item)
            self._add_children(child_item, cat.id, categories)
            
    def _filter_tree(self, text: str):
        """Ağacı filtrele"""
        text = text.lower()
        
        def filter_item(item: QTreeWidgetItem) -> bool:
            # Bu öğe eşleşiyor mu?
            match = text in item.text(0).lower() or text in item.text(1).lower()
            
            # Alt öğeleri kontrol et
            child_match = False
            for i in range(item.childCount()):
                if filter_item(item.child(i)):
                    child_match = True
            
            # Görünürlüğü ayarla
            item.setHidden(not (match or child_match) and bool(text))
            
            if match or child_match:
                item.setExpanded(True)
            
            return match or child_match
        
        for i in range(self.tree.topLevelItemCount()):
            filter_item(self.tree.topLevelItem(i))
            
    def _show_context_menu(self, position):
        item = self.tree.itemAt(position)
        if not item:
            return
            
        cat_id = item.data(0, Qt.ItemDataRole.UserRole)
        
        menu = QMenu(self)
        edit_action = QAction("✏️ Düzenle", self)
        edit_action.triggered.connect(lambda: self.edit_clicked.emit(cat_id))
        menu.addAction(edit_action)
        
        add_child_action = QAction("➕ Alt Kategori Ekle", self)
        add_child_action.triggered.connect(lambda: self.add_child_clicked.emit(cat_id))
        menu.addAction(add_child_action)
        
        menu.addSeparator()
        
        delete_action = QAction("🗑 Sil", self)
        delete_action.triggered.connect(lambda: self._confirm_delete(cat_id))
        menu.addAction(delete_action)
        
        menu.exec(self.tree.viewport().mapToGlobal(position))
        
    def _on_double_click(self, item: QTreeWidgetItem, column: int):
        cat_id = item.data(0, Qt.ItemDataRole.UserRole)
        self.edit_clicked.emit(cat_id)
        
    def _confirm_delete(self, cat_id: int):
        cat = self.categories_data.get(cat_id)
        if not cat:
            return
            
        # Alt kategori var mı?
        has_children = any(c.parent_id == cat_id for c in self.categories_data.values())
        
        msg = f"'{cat.name}' kategorisini silmek istediğinize emin misiniz?"
        if has_children:
            msg += "\n\n⚠️ Bu kategorinin alt kategorileri var!"
        
        reply = QMessageBox.question(
            self, "Silme Onayı", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(cat_id)
            