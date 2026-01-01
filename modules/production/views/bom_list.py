"""
Akıllı İş - Ürün Reçeteleri (BOM) Liste Sayfası
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QAbstractItemView, QMenu, QMessageBox, QComboBox, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QAction

from config import COLORS


class BOMListPage(QWidget):
    """Ürün reçeteleri listesi"""
    
    new_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    view_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    copy_clicked = pyqtSignal(int)
    activate_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()
    
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
        title = QLabel("📋 Ürün Reçeteleri (BOM)")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f8fafc;")
        subtitle = QLabel("Mamul üretimi için malzeme listelerini yönetin")
        subtitle.setStyleSheet("font-size: 14px; color: #94a3b8;")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addLayout(title_layout)
        
        header_layout.addStretch()
        
        # Durum filtresi
        header_layout.addWidget(QLabel("Durum:"))
        self.status_combo = QComboBox()
        self.status_combo.addItem("Tümü", None)
        self.status_combo.addItem("🟡 Taslak", "draft")
        self.status_combo.addItem("✅ Aktif", "active")
        self.status_combo.addItem("🔄 Revizyon", "revision")
        self.status_combo.addItem("❌ Geçersiz", "obsolete")
        self._style_combo(self.status_combo)
        self.status_combo.currentIndexChanged.connect(lambda: self.refresh_requested.emit())
        header_layout.addWidget(self.status_combo)
        
        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Reçete ara...")
        self.search_input.setFixedWidth(200)
        self._style_input(self.search_input)
        self.search_input.textChanged.connect(self._on_search)
        header_layout.addWidget(self.search_input)
        
        # Yenile
        refresh_btn = QPushButton("🔄 Yenile")
        self._style_button(refresh_btn)
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        header_layout.addWidget(refresh_btn)
        
        # Yeni Reçete
        new_btn = QPushButton("➕ Yeni Reçete")
        new_btn.setStyleSheet("""
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
        new_btn.clicked.connect(self.new_clicked.emit)
        header_layout.addWidget(new_btn)
        
        layout.addLayout(header_layout)
        
        # === Özet Kartlar ===
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)
        
        self.total_card = self._create_card("📋 Toplam Reçete", "0", "#6366f1")
        cards_layout.addWidget(self.total_card)
        
        self.active_card = self._create_card("✅ Aktif", "0", "#10b981")
        cards_layout.addWidget(self.active_card)
        
        self.draft_card = self._create_card("🟡 Taslak", "0", "#f59e0b")
        cards_layout.addWidget(self.draft_card)
        
        self.products_card = self._create_card("📦 Ürün Sayısı", "0", "#3b82f6")
        cards_layout.addWidget(self.products_card)
        
        layout.addLayout(cards_layout)
        
        # === Tablo ===
        self.table = QTableWidget()
        self._setup_table()
        layout.addWidget(self.table)
        
        # === Alt Bilgi ===
        self.count_label = QLabel("Toplam: 0 reçete")
        self.count_label.setStyleSheet("color: #64748b;")
        layout.addWidget(self.count_label)
        
    def _create_card(self, title: str, value: str, color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color}15;
                border: 1px solid {color}40;
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #94a3b8; font-size: 13px; background: transparent;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold; background: transparent;")
        layout.addWidget(value_label)
        
        return card
        
    def _setup_table(self):
        columns = [
            ("Reçete Kodu", 120),
            ("Mamul", 200),
            ("Reçete Adı", 200),
            ("Versiyon", 80),
            ("Malzeme Sayısı", 110),
            ("Tahmini Maliyet", 130),
            ("Durum", 100),
        ]
        
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels([c[0] for c in columns])
        
        header = self.table.horizontalHeader()
        for i, (_, width) in enumerate(columns):
            if i == 2:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                self.table.setColumnWidth(i, width)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(30, 41, 59, 0.3);
                border: 1px solid #334155;
                border-radius: 12px;
            }
            QTableWidget::item {
                padding: 10px 8px;
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
                padding: 10px 8px;
                border: none;
            }
        """)
        
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.doubleClicked.connect(self._on_double_click)
        
    def load_data(self, boms: list):
        """Reçete listesini yükle"""
        self.table.setRowCount(len(boms))
        
        status_display = {
            "draft": ("🟡 Taslak", "#f59e0b"),
            "active": ("✅ Aktif", "#10b981"),
            "revision": ("🔄 Revizyon", "#3b82f6"),
            "obsolete": ("❌ Geçersiz", "#ef4444"),
        }
        
        total_count = len(boms)
        active_count = 0
        draft_count = 0
        unique_products = set()
        
        for row, bom in enumerate(boms):
            # Reçete Kodu
            code_item = QTableWidgetItem(bom.get("code", ""))
            code_item.setData(Qt.ItemDataRole.UserRole, bom.get("id"))
            code_item.setForeground(QColor("#818cf8"))
            self.table.setItem(row, 0, code_item)
            
            # Mamul
            item_name = bom.get("item_name", "-")
            unique_products.add(bom.get("item_id"))
            self.table.setItem(row, 1, QTableWidgetItem(item_name))
            
            # Reçete Adı
            self.table.setItem(row, 2, QTableWidgetItem(bom.get("name", "")))
            
            # Versiyon
            version = f"v{bom.get('version', 1)}.{bom.get('revision', 'A')}"
            version_item = QTableWidgetItem(version)
            version_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, version_item)
            
            # Malzeme Sayısı
            line_count = bom.get("line_count", 0)
            count_item = QTableWidgetItem(str(line_count))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, count_item)
            
            # Tahmini Maliyet
            cost = bom.get("total_cost", 0)
            cost_item = QTableWidgetItem(f"₺{cost:,.2f}")
            cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 5, cost_item)
            
            # Durum
            status = bom.get("status", "draft")
            status_text, status_color = status_display.get(status, ("?", "#ffffff"))
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(QColor(status_color))
            self.table.setItem(row, 6, status_item)
            
            # İstatistikler
            if status == "active":
                active_count += 1
            elif status == "draft":
                draft_count += 1
        
        # Kartları güncelle
        self._update_card(self.total_card, str(total_count))
        self._update_card(self.active_card, str(active_count))
        self._update_card(self.draft_card, str(draft_count))
        self._update_card(self.products_card, str(len(unique_products)))
        
        self.count_label.setText(f"Toplam: {len(boms)} reçete")
        
    def _update_card(self, card: QFrame, value: str):
        value_label = card.findChild(QLabel, "value")
        if value_label:
            value_label.setText(value)
            
    def get_status_filter(self) -> str:
        return self.status_combo.currentData()
        
    def _on_search(self, text: str):
        """Tabloda arama"""
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)
        
    def _show_context_menu(self, position):
        row = self.table.rowAt(position.y())
        if row < 0:
            return
            
        bom_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        status_text = self.table.item(row, 6).text()
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
            }
            QMenu::item { padding: 8px 16px; color: #f8fafc; }
            QMenu::item:selected { background-color: #334155; }
        """)
        
        view_action = QAction("👁 Görüntüle", self)
        view_action.triggered.connect(lambda: self.view_clicked.emit(bom_id))
        menu.addAction(view_action)
        
        edit_action = QAction("✏️ Düzenle", self)
        edit_action.triggered.connect(lambda: self.edit_clicked.emit(bom_id))
        menu.addAction(edit_action)
        
        copy_action = QAction("📋 Kopyala", self)
        copy_action.triggered.connect(lambda: self.copy_clicked.emit(bom_id))
        menu.addAction(copy_action)
        
        menu.addSeparator()
        
        if "Aktif" not in status_text:
            activate_action = QAction("✅ Aktifleştir", self)
            activate_action.triggered.connect(lambda: self.activate_clicked.emit(bom_id))
            menu.addAction(activate_action)
        
        menu.addSeparator()
        
        delete_action = QAction("🗑 Sil", self)
        delete_action.triggered.connect(lambda: self._confirm_delete(bom_id))
        menu.addAction(delete_action)
        
        menu.exec(self.table.viewport().mapToGlobal(position))
        
    def _on_double_click(self, index):
        bom_id = self.table.item(index.row(), 0).data(Qt.ItemDataRole.UserRole)
        self.edit_clicked.emit(bom_id)
        
    def _confirm_delete(self, bom_id: int):
        reply = QMessageBox.question(
            self, "Silme Onayı",
            "Bu reçeteyi silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(bom_id)
    
    def _style_button(self, btn):
        btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                border: 1px solid #334155;
                color: #f8fafc;
                padding: 10px 20px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #334155; }
        """)
        
    def _style_combo(self, combo):
        combo.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 8px 12px;
                color: #f8fafc;
                min-width: 120px;
            }
            QComboBox:hover { border-color: #475569; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                border: 1px solid #334155;
                color: #f8fafc;
                selection-background-color: #334155;
            }
        """)
        
    def _style_input(self, widget):
        widget.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 8px 12px;
                color: #f8fafc;
            }
            QLineEdit:focus { border-color: #6366f1; }
        """)
