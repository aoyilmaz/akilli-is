"""
Akıllı İş - Stok Sayımı Liste Sayfası
"""

from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QAbstractItemView, QMenu, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QAction

from config import COLORS


class StockCountListPage(QWidget):
    """Stok sayımı listesi"""
    
    new_count_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    view_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    apply_clicked = pyqtSignal(int)  # Sayımı uygula
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
        title = QLabel("📋 Stok Sayımı")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f8fafc;")
        subtitle = QLabel("Envanter sayım işlemlerini yönetin")
        subtitle.setStyleSheet("font-size: 14px; color: #94a3b8;")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addLayout(title_layout)
        
        header_layout.addStretch()
        
        # Filtre
        header_layout.addWidget(QLabel("Durum:"))
        self.status_combo = QComboBox()
        self.status_combo.addItem("Tümü", None)
        self.status_combo.addItem("🟡 Taslak", "draft")
        self.status_combo.addItem("🔵 Devam Ediyor", "in_progress")
        self.status_combo.addItem("✅ Tamamlandı", "completed")
        self.status_combo.addItem("📥 Uygulandı", "applied")
        self.status_combo.addItem("❌ İptal", "cancelled")
        self._style_combo(self.status_combo)
        self.status_combo.currentIndexChanged.connect(lambda: self.refresh_requested.emit())
        header_layout.addWidget(self.status_combo)
        
        # Yenile
        refresh_btn = QPushButton("🔄 Yenile")
        self._style_button(refresh_btn)
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        header_layout.addWidget(refresh_btn)
        
        # Yeni Sayım
        new_btn = QPushButton("➕ Yeni Sayım")
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
        new_btn.clicked.connect(self.new_count_clicked.emit)
        header_layout.addWidget(new_btn)
        
        layout.addLayout(header_layout)
        
        # === Özet Kartlar ===
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)
        
        self.draft_card = self._create_card("🟡 Taslak", "0", "#f59e0b")
        cards_layout.addWidget(self.draft_card)
        
        self.progress_card = self._create_card("🔵 Devam Eden", "0", "#3b82f6")
        cards_layout.addWidget(self.progress_card)
        
        self.completed_card = self._create_card("✅ Tamamlanan", "0", "#10b981")
        cards_layout.addWidget(self.completed_card)
        
        self.diff_card = self._create_card("📊 Toplam Fark", "₺0", "#ef4444")
        cards_layout.addWidget(self.diff_card)
        
        layout.addLayout(cards_layout)
        
        # === Tablo ===
        self.table = QTableWidget()
        self._setup_table()
        layout.addWidget(self.table)
        
        # === Alt Bilgi ===
        self.count_label = QLabel("Toplam: 0 sayım")
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
        title_label.setStyleSheet("color: #94a3b8; font-size: 13px;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")
        layout.addWidget(value_label)
        
        return card
        
    def _setup_table(self):
        columns = [
            ("Sayım No", 120),
            ("Tarih", 140),
            ("Depo", 150),
            ("Açıklama", 200),
            ("Ürün Sayısı", 100),
            ("Sayılan", 100),
            ("Fark Tutarı", 120),
            ("Durum", 120),
        ]
        
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels([c[0] for c in columns])
        
        header = self.table.horizontalHeader()
        for i, (_, width) in enumerate(columns):
            if i == 3:
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
        
    def load_data(self, counts: list):
        """Sayım listesini yükle"""
        self.table.setRowCount(len(counts))
        
        status_display = {
            "draft": ("🟡 Taslak", "#f59e0b"),
            "in_progress": ("🔵 Devam Ediyor", "#3b82f6"),
            "completed": ("✅ Tamamlandı", "#10b981"),
            "applied": ("📥 Uygulandı", "#8b5cf6"),
            "cancelled": ("❌ İptal", "#ef4444"),
        }
        
        draft_count = 0
        progress_count = 0
        completed_count = 0
        total_diff = 0
        
        for row, count in enumerate(counts):
            # Sayım No
            no_item = QTableWidgetItem(count.get("count_no", ""))
            no_item.setData(Qt.ItemDataRole.UserRole, count.get("id"))
            no_item.setForeground(QColor("#818cf8"))
            self.table.setItem(row, 0, no_item)
            
            # Tarih
            date_str = count.get("count_date", "")
            if isinstance(date_str, datetime):
                date_str = date_str.strftime("%d.%m.%Y %H:%M")
            self.table.setItem(row, 1, QTableWidgetItem(date_str))
            
            # Depo
            self.table.setItem(row, 2, QTableWidgetItem(count.get("warehouse_name", "-")))
            
            # Açıklama
            self.table.setItem(row, 3, QTableWidgetItem(count.get("description", "")))
            
            # Ürün sayısı
            item_count = count.get("item_count", 0)
            self.table.setItem(row, 4, QTableWidgetItem(str(item_count)))
            
            # Sayılan
            counted = count.get("counted_items", 0)
            self.table.setItem(row, 5, QTableWidgetItem(str(counted)))
            
            # Fark tutarı
            diff = count.get("difference_amount", 0)
            diff_item = QTableWidgetItem(f"₺{diff:,.2f}")
            diff_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if diff < 0:
                diff_item.setForeground(QColor(COLORS["error"]))
            elif diff > 0:
                diff_item.setForeground(QColor(COLORS["success"]))
            self.table.setItem(row, 6, diff_item)
            
            # Durum
            status = count.get("status", "draft")
            status_text, status_color = status_display.get(status, ("?", "#ffffff"))
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(QColor(status_color))
            self.table.setItem(row, 7, status_item)
            
            # İstatistikler
            if status == "draft":
                draft_count += 1
            elif status == "in_progress":
                progress_count += 1
            elif status == "completed":
                completed_count += 1
            total_diff += diff
        
        # Kartları güncelle
        self._update_card(self.draft_card, str(draft_count))
        self._update_card(self.progress_card, str(progress_count))
        self._update_card(self.completed_card, str(completed_count))
        self._update_card(self.diff_card, f"₺{total_diff:,.2f}")
        
        self.count_label.setText(f"Toplam: {len(counts)} sayım")
        
    def _update_card(self, card: QFrame, value: str):
        value_label = card.findChild(QLabel, "value")
        if value_label:
            value_label.setText(value)
            
    def get_status_filter(self) -> str:
        return self.status_combo.currentData()
        
    def _show_context_menu(self, position):
        row = self.table.rowAt(position.y())
        if row < 0:
            return
            
        count_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        status_text = self.table.item(row, 7).text()
        
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
        
        view_action = QAction("👁 Görüntüle", self)
        view_action.triggered.connect(lambda: self.view_clicked.emit(count_id))
        menu.addAction(view_action)
        
        if "Taslak" in status_text or "Devam" in status_text:
            edit_action = QAction("✏️ Düzenle", self)
            edit_action.triggered.connect(lambda: self.edit_clicked.emit(count_id))
            menu.addAction(edit_action)
        
        if "Tamamlandı" in status_text:
            apply_action = QAction("📥 Stoklara Uygula", self)
            apply_action.triggered.connect(lambda: self._confirm_apply(count_id))
            menu.addAction(apply_action)
        
        menu.addSeparator()
        
        if "Taslak" in status_text:
            delete_action = QAction("🗑 Sil", self)
            delete_action.triggered.connect(lambda: self._confirm_delete(count_id))
            menu.addAction(delete_action)
        
        menu.exec(self.table.viewport().mapToGlobal(position))
        
    def _on_double_click(self, index):
        count_id = self.table.item(index.row(), 0).data(Qt.ItemDataRole.UserRole)
        self.view_clicked.emit(count_id)
        
    def _confirm_delete(self, count_id: int):
        reply = QMessageBox.question(
            self, "Silme Onayı",
            "Bu sayımı silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(count_id)
            
    def _confirm_apply(self, count_id: int):
        reply = QMessageBox.question(
            self, "Uygulama Onayı",
            "Sayım farklarını stoklara uygulamak istediğinize emin misiniz?\n\n"
            "Bu işlem geri alınamaz!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.apply_clicked.emit(count_id)
    
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
                min-width: 150px;
            }
        """)
