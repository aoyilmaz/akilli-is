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
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f8fafc;")
        subtitle = QLabel("Hiyerarşik kategori yapısını yönetin")
        subtitle.setStyleSheet("font-size: 14px; color: #94a3b8;")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addLayout(title_layout)
        
        header_layout.addStretch()
        
        # Genişlet/Daralt
        expand_btn = QPushButton("📂 Tümünü Aç")
        expand_btn.clicked.connect(lambda: self.tree.expandAll())
        self._style_button(expand_btn)
        header_layout.addWidget(expand_btn)
        
        collapse_btn = QPushButton("📁 Tümünü Kapat")
        collapse_btn.clicked.connect(lambda: self.tree.collapseAll())
        self._style_button(collapse_btn)
        header_layout.addWidget(collapse_btn)
        
        # Yenile
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        self._style_button(refresh_btn)
        header_layout.addWidget(refresh_btn)
        
        # Yeni ekle
        add_btn = QPushButton("➕ Yeni Kategori")
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
        
        # === Arama ===
        search_frame = QFrame()
        search_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 41, 59, 0.5);
                border: 1px solid #334155;
                border-radius: 12px;
            }
        """)
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(16, 12, 16, 12)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Kategori ara...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px 16px;
                color: #f8fafc;
                min-width: 300px;
            }
            QLineEdit:focus { border-color: #6366f1; }
        """)
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
        
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: rgba(30, 41, 59, 0.3);
                border: 1px solid #334155;
                border-radius: 12px;
                outline: none;
            }
            QTreeWidget::item {
                padding: 8px 4px;
                border-bottom: 1px solid #334155;
            }
            QTreeWidget::item:selected {
                background-color: rgba(99, 102, 241, 0.2);
            }
            QTreeWidget::item:hover {
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
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {
                image: url(none);
                border-image: none;
            }
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {
                image: url(none);
                border-image: none;
            }
        """)
        
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        
        layout.addWidget(self.tree)
        
        # === Alt Bilgi ===
        self.count_label = QLabel("Toplam: 0 kategori")
        self.count_label.setStyleSheet("color: #64748b;")
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
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
            }
            QMenu::item { padding: 8px 16px; }
            QMenu::item:selected { background-color: #334155; }
        """)
        
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
            
    def _style_button(self, btn):
        btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                border: 1px solid #334155;
                color: #f8fafc;
                padding: 10px 16px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #334155; }
        """)
