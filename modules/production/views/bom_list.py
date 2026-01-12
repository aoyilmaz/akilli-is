"""
Akıllı İş - Ürün Reçeteleri (BOM) Liste Sayfası
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QAbstractItemView,
    QMenu,
    QMessageBox,
    QComboBox,
    QLineEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QAction
from ui.components.stat_cards import MiniStatCard

from config import COLORS
from config.styles import get_button_style, BTN_HEIGHT_NORMAL, ICONS


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
        subtitle = QLabel("Mamul üretimi için malzeme listelerini yönetin")
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
        self.status_combo.currentIndexChanged.connect(
            lambda: self.refresh_requested.emit()
        )
        header_layout.addWidget(self.status_combo)

        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Reçete ara...")
        self.search_input.setFixedWidth(200)
        self.search_input.textChanged.connect(self._on_search)
        header_layout.addWidget(self.search_input)

        # Yenile
        refresh_btn = QPushButton(f"{ICONS['refresh']} Yenile")
        refresh_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        refresh_btn.setStyleSheet(get_button_style("refresh"))
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        header_layout.addWidget(refresh_btn)

        # Yeni Reçete
        new_btn = QPushButton(f"{ICONS['add']} Yeni Reçete")
        new_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        new_btn.setStyleSheet(get_button_style("add"))
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
        layout.addWidget(self.count_label)

    def _create_card(self, title: str, value: str, color: str) -> MiniStatCard:
        """Dashboard tarzı istatistik kartı"""
        return MiniStatCard(title, value, color)

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
            cost_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
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

    def _update_card(self, card: MiniStatCard, value: str):
        card.update_value(value)

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
            activate_action.triggered.connect(
                lambda: self.activate_clicked.emit(bom_id)
            )
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
            self,
            "Silme Onayı",
            "Bu reçeteyi silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(bom_id)
