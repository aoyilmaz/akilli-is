"""
Akıllı İş - İş İstasyonları Liste Sayfası
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QAbstractItemView, QMenu, QMessageBox, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QAction
from ui.components.stat_cards import MiniStatCard

class WorkStationListPage(QWidget):
    """İş istasyonları listesi"""
    
    new_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
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
        title = QLabel("🏭 İş İstasyonları")
        subtitle = QLabel("Makine ve iş istasyonlarını yönetin")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addLayout(title_layout)
        
        header_layout.addStretch()
        
        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 İstasyon ara...")
        self.search_input.setFixedWidth(200)
        self.search_input.textChanged.connect(self._on_search)
        header_layout.addWidget(self.search_input)
        
        # Yenile
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        header_layout.addWidget(refresh_btn)
        
        # Yeni İstasyon
        new_btn = QPushButton("➕ Yeni İstasyon")
        new_btn.clicked.connect(self.new_clicked.emit)
        header_layout.addWidget(new_btn)
        
        layout.addLayout(header_layout)
        
        # === Özet Kartlar ===
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)
        
        self.total_card = self._create_card("🏭 Toplam İstasyon", "0", "#6366f1")
        cards_layout.addWidget(self.total_card)
        
        self.machine_card = self._create_card("⚙️ Makine", "0", "#3b82f6")
        cards_layout.addWidget(self.machine_card)
        
        self.workstation_card = self._create_card("🔧 İş İstasyonu", "0", "#10b981")
        cards_layout.addWidget(self.workstation_card)
        
        self.assembly_card = self._create_card("🔩 Montaj Hattı", "0", "#f59e0b")
        cards_layout.addWidget(self.assembly_card)
        
        layout.addLayout(cards_layout)
        
        # === Tablo ===
        self.table = QTableWidget()
        self._setup_table()
        layout.addWidget(self.table)
        
        # === Alt Bilgi ===
        self.count_label = QLabel("Toplam: 0 istasyon")
        layout.addWidget(self.count_label)
        
    def _create_card(self, title: str, value: str, color: str) -> MiniStatCard:
        """Dashboard tarzı istatistik kartı"""
        return MiniStatCard(title, value, color)
        
    def _setup_table(self):
        columns = [
            ("Kod", 100),
            ("İstasyon Adı", 200),
            ("Tür", 120),
            ("Kapasite/Saat", 110),
            ("Verimlilik", 100),
            ("Saatlik Maliyet", 120),
            ("Konum", 150),
            ("Durum", 100),
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
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.doubleClicked.connect(self._on_double_click)
        
    def load_data(self, stations: list):
        """İstasyon listesini yükle"""
        self.table.setRowCount(len(stations))
        
        type_display = {
            "machine": ("⚙️ Makine", "#3b82f6"),
            "workstation": ("🔧 İş İstasyonu", "#10b981"),
            "assembly": ("🔩 Montaj Hattı", "#f59e0b"),
            "manual": ("✋ Manuel", "#8b5cf6"),
        }
        
        total = len(stations)
        machine_count = 0
        workstation_count = 0
        assembly_count = 0
        
        for row, station in enumerate(stations):
            # Kod
            code_item = QTableWidgetItem(station.get("code", ""))
            code_item.setData(Qt.ItemDataRole.UserRole, station.get("id"))
            code_item.setForeground(QColor("#818cf8"))
            self.table.setItem(row, 0, code_item)
            
            # İstasyon Adı
            self.table.setItem(row, 1, QTableWidgetItem(station.get("name", "")))
            
            # Tür
            station_type = station.get("station_type", "machine")
            type_text, type_color = type_display.get(station_type, ("?", "#ffffff"))
            type_item = QTableWidgetItem(type_text)
            type_item.setForeground(QColor(type_color))
            self.table.setItem(row, 2, type_item)
            
            # İstatistik say
            if station_type == "machine":
                machine_count += 1
            elif station_type == "workstation":
                workstation_count += 1
            elif station_type == "assembly":
                assembly_count += 1
            
            # Kapasite/Saat
            capacity = station.get("capacity_per_hour", 0)
            capacity_item = QTableWidgetItem(f"{capacity:,.0f}" if capacity else "-")
            capacity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, capacity_item)
            
            # Verimlilik
            efficiency = station.get("efficiency_rate", 100)
            eff_item = QTableWidgetItem(f"%{efficiency:.0f}")
            eff_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if efficiency >= 90:
                eff_item.setForeground(QColor("#10b981"))
            elif efficiency >= 70:
                eff_item.setForeground(QColor("#f59e0b"))
            else:
                eff_item.setForeground(QColor("#ef4444"))
            self.table.setItem(row, 4, eff_item)
            
            # Saatlik Maliyet
            hourly_rate = station.get("hourly_rate", 0)
            rate_item = QTableWidgetItem(f"₺{hourly_rate:,.2f}")
            rate_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 5, rate_item)
            
            # Konum
            location = station.get("location", "") or station.get("warehouse_name", "")
            self.table.setItem(row, 6, QTableWidgetItem(location or "-"))
            
            # Durum
            is_active = station.get("is_active", True)
            status_text = "✅ Aktif" if is_active else "❌ Pasif"
            status_color = "#10b981" if is_active else "#ef4444"
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(QColor(status_color))
            self.table.setItem(row, 7, status_item)
        
        # Kartları güncelle
        self._update_card(self.total_card, str(total))
        self._update_card(self.machine_card, str(machine_count))
        self._update_card(self.workstation_card, str(workstation_count))
        self._update_card(self.assembly_card, str(assembly_count))
        
        self.count_label.setText(f"Toplam: {total} istasyon")
        
    def _update_card(self, card: MiniStatCard, value: str):
        card.update_value(value)
            
    def _on_search(self, text: str):
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
            
        station_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        menu = QMenu(self)
        edit_action = QAction("✏️ Düzenle", self)
        edit_action.triggered.connect(lambda: self.edit_clicked.emit(station_id))
        menu.addAction(edit_action)
        
        menu.addSeparator()
        
        delete_action = QAction("🗑 Sil", self)
        delete_action.triggered.connect(lambda: self._confirm_delete(station_id))
        menu.addAction(delete_action)
        
        menu.exec(self.table.viewport().mapToGlobal(position))
        
    def _on_double_click(self, index):
        station_id = self.table.item(index.row(), 0).data(Qt.ItemDataRole.UserRole)
        self.edit_clicked.emit(station_id)
        
    def _confirm_delete(self, station_id: int):
        reply = QMessageBox.question(
            self, "Silme Onayı",
            "Bu iş istasyonunu silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(station_id)
