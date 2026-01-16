"""
Akıllı İş - Aday Müşteri Liste Sayfası
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QFrame,
    QLineEdit,
    QHeaderView,
    QAbstractItemView,
    QMessageBox,
    QStyle,
    QApplication,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from ui.components.stat_cards import MiniStatCard
from config.styles import get_button_style, BTN_HEIGHT_NORMAL, ICONS
from database.models.crm import LeadStatus


class LeadListPage(QWidget):
    """Aday Müşteri (Lead) listesi sayfası"""

    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    convert_clicked = pyqtSignal(int)  # Müşteriye dönüştür
    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.leads = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("🚀 Aday Müşteriler (Leads)")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ara... (ad, şirket)")
        self.search_input.setFixedWidth(300)
        self.search_input.textChanged.connect(self._on_search)
        header_layout.addWidget(self.search_input)

        # Yenile butonu
        refresh_btn = QPushButton(f"{ICONS['refresh']} Yenile")
        refresh_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        refresh_btn.setStyleSheet(get_button_style("refresh"))
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        header_layout.addWidget(refresh_btn)

        # Yeni ekle butonu
        add_btn = QPushButton(f"{ICONS['add']} Yeni Aday")
        add_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        add_btn.setStyleSheet(get_button_style("add"))
        add_btn.clicked.connect(self.add_clicked.emit)
        header_layout.addWidget(add_btn)

        layout.addLayout(header_layout)

        # İstatistik kartları
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.total_card = self._create_stat_card("📊", "Toplam", "0", "#6366f1")
        stats_layout.addWidget(self.total_card)

        self.new_card = self._create_stat_card("✨", "Yeni", "0", "#3b82f6")
        stats_layout.addWidget(self.new_card)

        self.contacted_card = self._create_stat_card("📞", "Görüşüldü", "0", "#f59e0b")
        stats_layout.addWidget(self.contacted_card)

        self.qualified_card = self._create_stat_card("✅", "Kalifiye", "0", "#10b981")
        stats_layout.addWidget(self.qualified_card)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            [
                "Ad Soyad",
                "Şirket",
                "Durum",
                "Telefon",
                "E-posta",
                "Kaynak",
                "İşlemler",
            ]
        )

        # Tablo stili
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        # Kolon genişlikleri
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 180)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(6, 160)

        self.table.doubleClicked.connect(self._on_double_click)

        layout.addWidget(self.table)

    def _create_stat_card(
        self, icon: str, title: str, value: str, color: str
    ) -> MiniStatCard:
        """Dashboard tarzı istatistik kartı"""
        return MiniStatCard(f"{icon} {title}", value, color)

    def _update_card(self, card: MiniStatCard, value: str):
        """Kart değerini güncelle"""
        card.update_value(value)

    def load_data(self, leads: list):
        """Verileri yükle"""
        self.leads = leads  # leads is dict list
        self.table.setRowCount(0)

        total = len(leads)
        new_count = 0
        contacted_count = 0
        qualified_count = 0

        for lead in leads:
            status = lead.get("status")
            if status == LeadStatus.NEW.value:
                new_count += 1
            elif status == LeadStatus.CONTACTED.value:
                contacted_count += 1
            elif status == LeadStatus.QUALIFIED.value:
                qualified_count += 1

        self._update_card(self.total_card, str(total))
        self._update_card(self.new_card, str(new_count))
        self._update_card(self.contacted_card, str(contacted_count))
        self._update_card(self.qualified_card, str(qualified_count))

        for row, lead in enumerate(leads):
            self.table.insertRow(row)

            # Ad Soyad
            name = f"{lead.get('first_name', '')} {lead.get('last_name', '')}"
            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.ItemDataRole.UserRole, lead.get("id"))
            self.table.setItem(row, 0, name_item)

            # Şirket
            self.table.setItem(
                row, 1, QTableWidgetItem(lead.get("company_name", "") or "-")
            )

            # Durum
            status_text = lead.get("status", "").upper()
            status_item = QTableWidgetItem(status_text)
            # Renklendirme yapılabilir
            self.table.setItem(row, 2, status_item)

            # Telefon
            self.table.setItem(row, 3, QTableWidgetItem(lead.get("phone", "") or "-"))

            # E-posta
            self.table.setItem(row, 4, QTableWidgetItem(lead.get("email", "") or "-"))

            # Kaynak
            self.table.setItem(row, 5, QTableWidgetItem(lead.get("source", "") or "-"))

            # İşlem butonları
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(4)

            style = QApplication.style()

            # Dönüştür Butonu
            convert_btn = QPushButton()
            convert_btn.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_ArrowRight))
            convert_btn.setIconSize(QSize(16, 16))
            convert_btn.setFixedSize(32, 28)
            convert_btn.setToolTip("Müşteriye Dönüştür")
            convert_btn.clicked.connect(
                lambda checked, id=lead.get("id"): self.convert_clicked.emit(id)
            )
            # Eğer zaten dönüştürüldüyse pasif yap
            if lead.get("status") == LeadStatus.CONVERTED.value:
                convert_btn.setEnabled(False)

            btn_layout.addWidget(convert_btn)

            # Düzenle Butonu
            edit_btn = QPushButton()
            edit_btn.setIcon(
                style.standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
            )
            edit_btn.setIconSize(QSize(16, 16))
            edit_btn.setFixedSize(32, 28)
            edit_btn.setToolTip("Düzenle")
            edit_btn.clicked.connect(
                lambda checked, id=lead.get("id"): self.edit_clicked.emit(id)
            )
            btn_layout.addWidget(edit_btn)

            # Sil Butonu
            del_btn = QPushButton()
            del_btn.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
            del_btn.setIconSize(QSize(16, 16))
            del_btn.setFixedSize(32, 28)
            del_btn.setToolTip("Sil")
            del_btn.clicked.connect(
                lambda checked, id=lead.get("id"): self._confirm_delete(id)
            )
            btn_layout.addWidget(del_btn)

            self.table.setCellWidget(row, 6, btn_widget)
            self.table.setRowHeight(row, 56)

    def _on_search(self, text: str):
        """Arama"""
        text = text.lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(5):
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    def _on_double_click(self, index):
        """Çift tıklama"""
        row = index.row()
        item = self.table.item(row, 0)
        if item:
            lead_id = item.data(Qt.ItemDataRole.UserRole)
            if lead_id:
                self.edit_clicked.emit(lead_id)

    def _confirm_delete(self, lead_id: int):
        """Silme onayı"""
        reply = QMessageBox.question(
            self,
            "Silme Onayı",
            "Bu aday müşteriyi silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(lead_id)
