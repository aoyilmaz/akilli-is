"""
Akıllı İş - Stok Hareketleri Listesi
"""

from datetime import datetime, timedelta
from decimal import Decimal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QComboBox, QAbstractItemView, QMenu, QDateEdit,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor, QAction

from config import COLORS
from database.models import StockMovementType


class MovementListPage(QWidget):
    """Stok hareketleri listesi"""
    
    add_entry_clicked = pyqtSignal()      # Giriş fişi
    add_exit_clicked = pyqtSignal()       # Çıkış fişi
    add_transfer_clicked = pyqtSignal()   # Transfer fişi
    view_clicked = pyqtSignal(int)
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
        title = QLabel("Stok Hareketleri")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f8fafc;")
        subtitle = QLabel("Stok giriş, çıkış ve transfer işlemlerini yönetin")
        subtitle.setStyleSheet("font-size: 14px; color: #94a3b8;")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addLayout(title_layout)
        
        header_layout.addStretch()
        
        # Butonlar
        refresh_btn = QPushButton("🔄 Yenile")
        self._style_button(refresh_btn)
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        header_layout.addWidget(refresh_btn)
        
        entry_btn = QPushButton("📥 Giriş Fişi")
        entry_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                border: none;
                color: white;
                font-weight: 600;
                padding: 12px 20px;
                border-radius: 12px;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        entry_btn.clicked.connect(self.add_entry_clicked.emit)
        header_layout.addWidget(entry_btn)
        
        exit_btn = QPushButton("📤 Çıkış Fişi")
        exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                border: none;
                color: white;
                font-weight: 600;
                padding: 12px 20px;
                border-radius: 12px;
            }
            QPushButton:hover { background-color: #dc2626; }
        """)
        exit_btn.clicked.connect(self.add_exit_clicked.emit)
        header_layout.addWidget(exit_btn)
        
        transfer_btn = QPushButton("🔄 Transfer")
        transfer_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                border: none;
                color: white;
                font-weight: 600;
                padding: 12px 20px;
                border-radius: 12px;
            }
            QPushButton:hover { background-color: #4f46e5; }
        """)
        transfer_btn.clicked.connect(self.add_transfer_clicked.emit)
        header_layout.addWidget(transfer_btn)
        
        layout.addLayout(header_layout)
        
        # === Filtreler ===
        filter_frame = QFrame()
        filter_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 41, 59, 0.5);
                border: 1px solid #334155;
                border-radius: 12px;
            }
        """)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(16, 12, 16, 12)
        filter_layout.setSpacing(16)
        
        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Stok kodu, belge no ile ara...")
        self._style_input(self.search_input)
        self.search_input.setMinimumWidth(250)
        filter_layout.addWidget(self.search_input)
        
        # Hareket türü
        filter_layout.addWidget(QLabel("Tür:"))
        self.type_combo = QComboBox()
        self.type_combo.addItem("Tümü", None)
        self.type_combo.addItem("📥 Giriş", "giris")
        self.type_combo.addItem("📤 Çıkış", "cikis")
        self.type_combo.addItem("🔄 Transfer", "transfer")
        self.type_combo.addItem("🛒 Satın Alma", "satin_alma")
        self.type_combo.addItem("💰 Satış", "satis")
        self._style_combo(self.type_combo)
        filter_layout.addWidget(self.type_combo)
        
        # Tarih aralığı
        filter_layout.addWidget(QLabel("Tarih:"))
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        self._style_date(self.start_date)
        filter_layout.addWidget(self.start_date)
        
        filter_layout.addWidget(QLabel("-"))
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self._style_date(self.end_date)
        filter_layout.addWidget(self.end_date)
        
        # Filtrele butonu
        filter_btn = QPushButton("Filtrele")
        self._style_button(filter_btn)
        filter_btn.clicked.connect(self.refresh_requested.emit)
        filter_layout.addWidget(filter_btn)
        
        filter_layout.addStretch()
        
        layout.addWidget(filter_frame)
        
        # === Tablo ===
        self.table = QTableWidget()
        self._setup_table()
        layout.addWidget(self.table)
        
        # === Alt Bilgi ===
        footer_layout = QHBoxLayout()
        self.count_label = QLabel("Toplam: 0 hareket")
        self.count_label.setStyleSheet("color: #64748b;")
        footer_layout.addWidget(self.count_label)
        
        footer_layout.addStretch()
        
        self.total_label = QLabel("Giriş: ₺0 | Çıkış: ₺0")
        self.total_label.setStyleSheet("color: #64748b;")
        footer_layout.addWidget(self.total_label)
        
        layout.addLayout(footer_layout)
        
    def _setup_table(self):
        columns = [
            ("Tarih", 140),
            ("Belge No", 120),
            ("Tür", 100),
            ("Stok Kodu", 100),
            ("Stok Adı", 200),
            ("Miktar", 90),
            ("Birim", 60),
            ("Birim Fiyat", 100),
            ("Toplam", 110),
            ("Kaynak", 100),
            ("Hedef", 100),
        ]
        
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels([c[0] for c in columns])
        
        header = self.table.horizontalHeader()
        for i, (_, width) in enumerate(columns):
            if i == 4:
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
                border-bottom: 1px solid #334155;
            }
        """)
        
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
    def load_data(self, movements: list):
        self.table.setRowCount(len(movements))
        
        type_names = {
            StockMovementType.GIRIS: ("📥 Giriş", COLORS["success"]),
            StockMovementType.CIKIS: ("📤 Çıkış", COLORS["error"]),
            StockMovementType.SATIN_ALMA: ("🛒 Satın Alma", COLORS["success"]),
            StockMovementType.SATIS: ("💰 Satış", COLORS["error"]),
            StockMovementType.URETIM_GIRIS: ("🏭 Üretim Giriş", COLORS["success"]),
            StockMovementType.URETIM_CIKIS: ("🏭 Üretim Çıkış", COLORS["error"]),
            StockMovementType.TRANSFER: ("🔄 Transfer", COLORS["info"]),
            StockMovementType.SAYIM_FAZLA: ("➕ Sayım Fazla", COLORS["success"]),
            StockMovementType.SAYIM_EKSIK: ("➖ Sayım Eksik", COLORS["error"]),
            StockMovementType.FIRE: ("🔥 Fire", COLORS["warning"]),
            StockMovementType.IADE_ALIS: ("↩️ Alış İade", COLORS["error"]),
            StockMovementType.IADE_SATIS: ("↩️ Satış İade", COLORS["success"]),
        }
        
        total_in = Decimal(0)
        total_out = Decimal(0)
        
        for row, mov in enumerate(movements):
            # Tarih
            date_str = mov.movement_date.strftime("%d.%m.%Y %H:%M") if mov.movement_date else "-"
            date_item = QTableWidgetItem(date_str)
            date_item.setData(Qt.ItemDataRole.UserRole, mov.id)
            self.table.setItem(row, 0, date_item)
            
            # Belge No
            self.table.setItem(row, 1, QTableWidgetItem(mov.document_no or "-"))
            
            # Tür
            type_text, type_color = type_names.get(mov.movement_type, ("?", "#ffffff"))
            type_item = QTableWidgetItem(type_text)
            type_item.setForeground(QColor(type_color))
            self.table.setItem(row, 2, type_item)
            
            # Stok Kodu
            code_item = QTableWidgetItem(mov.item_code or "-")
            code_item.setForeground(QColor("#818cf8"))
            self.table.setItem(row, 3, code_item)
            
            # Stok Adı
            self.table.setItem(row, 4, QTableWidgetItem(mov.item_name or "-"))
            
            # Miktar
            qty = mov.quantity or Decimal(0)
            qty_item = QTableWidgetItem(f"{qty:,.2f}")
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 5, qty_item)
            
            # Birim
            unit_text = mov.unit.code if mov.unit else "-"
            self.table.setItem(row, 6, QTableWidgetItem(unit_text))
            
            # Birim Fiyat
            price = mov.unit_price or Decimal(0)
            price_item = QTableWidgetItem(f"₺{price:,.2f}")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 7, price_item)
            
            # Toplam
            total = mov.total_price or Decimal(0)
            total_item = QTableWidgetItem(f"₺{total:,.2f}")
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 8, total_item)
            
            # Kaynak depo
            from_wh = mov.from_warehouse.code if mov.from_warehouse else "-"
            self.table.setItem(row, 9, QTableWidgetItem(from_wh))
            
            # Hedef depo
            to_wh = mov.to_warehouse.code if mov.to_warehouse else "-"
            self.table.setItem(row, 10, QTableWidgetItem(to_wh))
            
            # Toplamları hesapla
            if mov.movement_type in [StockMovementType.GIRIS, StockMovementType.SATIN_ALMA, 
                                      StockMovementType.URETIM_GIRIS, StockMovementType.SAYIM_FAZLA,
                                      StockMovementType.IADE_SATIS]:
                total_in += total
            else:
                total_out += total
        
        self.count_label.setText(f"Toplam: {len(movements)} hareket")
        self.total_label.setText(f"Giriş: ₺{total_in:,.2f} | Çıkış: ₺{total_out:,.2f}")
        
    def get_filters(self) -> dict:
        return {
            "keyword": self.search_input.text().strip(),
            "movement_type": self.type_combo.currentData(),
            "start_date": self.start_date.date().toPyDate(),
            "end_date": self.end_date.date().toPyDate(),
        }
        
    def _show_context_menu(self, position):
        row = self.table.rowAt(position.y())
        if row < 0:
            return
        
        mov_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
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
        
        view_action = QAction("👁 Detay Görüntüle", self)
        view_action.triggered.connect(lambda: self.view_clicked.emit(mov_id))
        menu.addAction(view_action)
        
        menu.exec(self.table.viewport().mapToGlobal(position))
    
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
        
    def _style_input(self, widget):
        widget.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px 16px;
                color: #f8fafc;
            }
            QLineEdit:focus { border-color: #6366f1; }
        """)
        
    def _style_combo(self, widget):
        widget.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 8px 12px;
                color: #f8fafc;
                min-width: 130px;
            }
        """)
        
    def _style_date(self, widget):
        widget.setStyleSheet("""
            QDateEdit {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 8px 12px;
                color: #f8fafc;
            }
        """)
