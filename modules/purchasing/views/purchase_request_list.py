"""
Akıllı İş - Satın Alma Talepleri Liste Sayfası
"""

from datetime import date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QFrame, QLineEdit,
    QHeaderView, QAbstractItemView, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal


class PurchaseRequestListPage(QWidget):
    """Satın alma talepleri listesi"""
    
    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    view_clicked = pyqtSignal(int)
    approve_clicked = pyqtSignal(int)
    reject_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.requests = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("📋 Satın Alma Talepleri")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f8fafc;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Durum filtresi
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tüm Durumlar", None)
        self.status_filter.addItem("🔵 Taslak", "draft")
        self.status_filter.addItem("🟡 Onay Bekliyor", "pending")
        self.status_filter.addItem("🟢 Onaylandı", "approved")
        self.status_filter.addItem("🔴 Reddedildi", "rejected")
        self.status_filter.addItem("📦 Sipariş Verildi", "ordered")
        self.status_filter.setStyleSheet(self._combo_style())
        self.status_filter.setMinimumWidth(160)
        self.status_filter.currentIndexChanged.connect(self._on_filter_changed)
        header_layout.addWidget(self.status_filter)
        
        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ara... (talep no, departman)")
        self.search_input.setFixedWidth(250)
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
        add_btn = QPushButton("➕ Yeni Talep")
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
        
        self.draft_card = self._create_stat_card("🔵", "Taslak", "0", "#64748b")
        stats_layout.addWidget(self.draft_card)
        
        self.pending_card = self._create_stat_card("🟡", "Onay Bekliyor", "0", "#f59e0b")
        stats_layout.addWidget(self.pending_card)
        
        self.approved_card = self._create_stat_card("🟢", "Onaylandı", "0", "#10b981")
        stats_layout.addWidget(self.approved_card)
        
        self.rejected_card = self._create_stat_card("🔴", "Reddedildi", "0", "#ef4444")
        stats_layout.addWidget(self.rejected_card)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Talep No", "Tarih", "Talep Eden", "Departman", 
            "Kalem", "Öncelik", "Durum", "Termin", "İşlemler"
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
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 120)  # Talep No
        self.table.setColumnWidth(1, 100)  # Tarih
        self.table.setColumnWidth(2, 120)  # Talep Eden
        self.table.setColumnWidth(4, 60)   # Kalem
        self.table.setColumnWidth(5, 80)   # Öncelik
        self.table.setColumnWidth(6, 120)  # Durum
        self.table.setColumnWidth(7, 100)  # Termin
        self.table.setColumnWidth(8, 180)  # İşlemler
        
        self.table.doubleClicked.connect(self._on_double_click)
        
        layout.addWidget(self.table)
        
    def _create_stat_card(self, icon: str, title: str, value: str, color: str) -> QFrame:
        card = QFrame()
        card.setFixedSize(140, 80)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color}15;
                border: 1px solid {color}30;
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)
        
        header = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 14px; background: transparent;")
        header.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {color}; font-size: 11px; background: transparent;")
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
                image: none;
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
    
    def load_data(self, requests: list):
        """Verileri yükle"""
        self.requests = requests
        self._apply_filter()
        
    def _apply_filter(self):
        """Filtreyi uygula"""
        status_filter = self.status_filter.currentData()
        
        filtered = self.requests
        if status_filter:
            filtered = [r for r in self.requests if r.get("status") == status_filter]
        
        self._display_data(filtered)
        self._update_stats()
        
    def _display_data(self, requests: list):
        """Tabloya verileri yükle"""
        self.table.setRowCount(0)
        
        priority_labels = {
            1: ("⬇️ Düşük", "#64748b"),
            2: ("➡️ Normal", "#3b82f6"),
            3: ("⬆️ Yüksek", "#f59e0b"),
            4: ("🔥 Acil", "#ef4444"),
        }
        
        status_labels = {
            "draft": ("🔵 Taslak", "#64748b"),
            "pending": ("🟡 Onay Bekliyor", "#f59e0b"),
            "approved": ("🟢 Onaylandı", "#10b981"),
            "rejected": ("🔴 Reddedildi", "#ef4444"),
            "ordered": ("📦 Sipariş Verildi", "#8b5cf6"),
            "cancelled": ("⚫ İptal", "#475569"),
        }
        
        for row, req in enumerate(requests):
            self.table.insertRow(row)
            
            # Talep No
            no_item = QTableWidgetItem(req.get("request_no", ""))
            no_item.setData(Qt.ItemDataRole.UserRole, req.get("id"))
            self.table.setItem(row, 0, no_item)
            
            # Tarih
            req_date = req.get("request_date")
            if req_date:
                if isinstance(req_date, date):
                    date_str = req_date.strftime("%d.%m.%Y")
                else:
                    date_str = str(req_date)
            else:
                date_str = "-"
            self.table.setItem(row, 1, QTableWidgetItem(date_str))
            
            # Talep Eden
            self.table.setItem(row, 2, QTableWidgetItem(req.get("requested_by", "") or "-"))
            
            # Departman
            self.table.setItem(row, 3, QTableWidgetItem(req.get("department", "") or "-"))
            
            # Kalem Sayısı
            item_count = req.get("total_items", 0)
            self.table.setItem(row, 4, QTableWidgetItem(str(item_count)))
            
            # Öncelik
            priority = req.get("priority", 2)
            priority_text, priority_color = priority_labels.get(priority, ("Normal", "#3b82f6"))
            priority_item = QTableWidgetItem(priority_text)
            priority_item.setForeground(Qt.GlobalColor.white)
            self.table.setItem(row, 5, priority_item)
            
            # Durum
            status = req.get("status", "draft")
            status_text, status_color = status_labels.get(status, ("Taslak", "#64748b"))
            status_item = QTableWidgetItem(status_text)
            self.table.setItem(row, 6, status_item)
            
            # Termin
            req_required = req.get("required_date")
            if req_required:
                if isinstance(req_required, date):
                    required_str = req_required.strftime("%d.%m.%Y")
                else:
                    required_str = str(req_required)
            else:
                required_str = "-"
            self.table.setItem(row, 7, QTableWidgetItem(required_str))
            
            # İşlem butonları
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(4)
            
            req_id = req.get("id")
            req_status = req.get("status", "draft")
            
            # Görüntüle
            view_btn = QPushButton("👁")
            view_btn.setFixedSize(32, 32)
            view_btn.setStyleSheet(self._action_btn_style("#3b82f6"))
            view_btn.setToolTip("Görüntüle")
            view_btn.clicked.connect(lambda checked, id=req_id: self.view_clicked.emit(id))
            btn_layout.addWidget(view_btn)
            
            # Düzenle (sadece taslak)
            if req_status == "draft":
                edit_btn = QPushButton("✏️")
                edit_btn.setFixedSize(32, 32)
                edit_btn.setStyleSheet(self._action_btn_style("#f59e0b"))
                edit_btn.setToolTip("Düzenle")
                edit_btn.clicked.connect(lambda checked, id=req_id: self.edit_clicked.emit(id))
                btn_layout.addWidget(edit_btn)
            
            # Onayla / Reddet (sadece pending)
            if req_status == "pending":
                approve_btn = QPushButton("✅")
                approve_btn.setFixedSize(32, 32)
                approve_btn.setStyleSheet(self._action_btn_style("#10b981"))
                approve_btn.setToolTip("Onayla")
                approve_btn.clicked.connect(lambda checked, id=req_id: self.approve_clicked.emit(id))
                btn_layout.addWidget(approve_btn)
                
                reject_btn = QPushButton("❌")
                reject_btn.setFixedSize(32, 32)
                reject_btn.setStyleSheet(self._action_btn_style("#ef4444"))
                reject_btn.setToolTip("Reddet")
                reject_btn.clicked.connect(lambda checked, id=req_id: self.reject_clicked.emit(id))
                btn_layout.addWidget(reject_btn)
            
            # Sil (sadece taslak)
            if req_status == "draft":
                del_btn = QPushButton("🗑")
                del_btn.setFixedSize(32, 32)
                del_btn.setStyleSheet(self._action_btn_style("#ef4444"))
                del_btn.setToolTip("Sil")
                del_btn.clicked.connect(lambda checked, id=req_id: self._confirm_delete(id))
                btn_layout.addWidget(del_btn)
            
            self.table.setCellWidget(row, 8, btn_widget)
            self.table.setRowHeight(row, 56)
            
    def _update_stats(self):
        """İstatistikleri güncelle"""
        total = len(self.requests)
        draft = sum(1 for r in self.requests if r.get("status") == "draft")
        pending = sum(1 for r in self.requests if r.get("status") == "pending")
        approved = sum(1 for r in self.requests if r.get("status") == "approved")
        rejected = sum(1 for r in self.requests if r.get("status") == "rejected")
        
        self._update_card(self.total_card, str(total))
        self._update_card(self.draft_card, str(draft))
        self._update_card(self.pending_card, str(pending))
        self._update_card(self.approved_card, str(approved))
        self._update_card(self.rejected_card, str(rejected))
        
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
            for col in range(7):
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)
            
    def _on_filter_changed(self):
        """Filtre değişti"""
        self._apply_filter()
            
    def _on_double_click(self, index):
        """Çift tıklama"""
        row = index.row()
        item = self.table.item(row, 0)
        if item:
            request_id = item.data(Qt.ItemDataRole.UserRole)
            if request_id:
                self.view_clicked.emit(request_id)
                
    def _confirm_delete(self, request_id: int):
        """Silme onayı"""
        reply = QMessageBox.question(
            self, "Silme Onayı",
            "Bu talebi silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(request_id)
