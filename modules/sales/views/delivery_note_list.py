"""
Akıllı İş - Teslimat İrsaliyeleri Liste Sayfası
"""

from datetime import date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QFrame, QLineEdit,
    QHeaderView, QAbstractItemView, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal


class DeliveryNoteListPage(QWidget):
    """Teslimat irsaliyeleri listesi"""

    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    view_clicked = pyqtSignal(int)
    ship_clicked = pyqtSignal(int)
    complete_clicked = pyqtSignal(int)
    cancel_clicked = pyqtSignal(int)
    create_invoice_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.notes = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("🚚 Teslimat İrsaliyeleri")
        title.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #f8fafc;"
        )
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Durum filtresi
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tüm Durumlar", None)
        self.status_filter.addItem("🔵 Taslak", "draft")
        self.status_filter.addItem("📦 Sevk Edildi", "shipped")
        self.status_filter.addItem("✅ Teslim Edildi", "delivered")
        self.status_filter.addItem("⚫ İptal", "cancelled")
        self.status_filter.setStyleSheet(self._combo_style())
        self.status_filter.setMinimumWidth(160)
        self.status_filter.currentIndexChanged.connect(self._on_filter_changed)
        header_layout.addWidget(self.status_filter)

        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ara... (irsaliye no, müşteri)")
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
        add_btn = QPushButton("➕ Yeni İrsaliye")
        add_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #a855f7
                );
                border: none;
                color: white;
                font-weight: 600;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4f46e5, stop:1 #9333ea
                );
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

        self.shipped_card = self._create_stat_card(
            "📦", "Sevk Edildi", "0", "#f59e0b"
        )
        stats_layout.addWidget(self.shipped_card)

        self.delivered_card = self._create_stat_card(
            "✅", "Teslim Edildi", "0", "#10b981"
        )
        stats_layout.addWidget(self.delivered_card)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "İrsaliye No", "Tarih", "Müşteri", "Sipariş No",
            "Kalem", "Sevk Tarihi", "Durum", "İşlemler"
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
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        # Kolon genişlikleri
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 60)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(6, 130)
        self.table.setColumnWidth(7, 200)

        self.table.doubleClicked.connect(self._on_double_click)

        layout.addWidget(self.table)

    def _create_stat_card(
        self, icon: str, title: str, value: str, color: str
    ) -> QFrame:
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
        title_label.setStyleSheet(
            f"color: {color}; font-size: 11px; background: transparent;"
        )
        header.addWidget(title_label)
        header.addStretch()
        layout.addLayout(header)

        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet(
            f"color: {color}; font-size: 22px; "
            f"font-weight: bold; background: transparent;"
        )
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

    def load_data(self, notes: list):
        """Verileri yükle"""
        self.notes = notes
        self._apply_filter()

    def _apply_filter(self):
        """Filtreyi uygula"""
        status_filter = self.status_filter.currentData()

        filtered = self.notes
        if status_filter:
            filtered = [
                n for n in self.notes if n.get("status") == status_filter
            ]

        self._display_data(filtered)
        self._update_stats()

    def _display_data(self, notes: list):
        """Tabloya verileri yükle"""
        self.table.setRowCount(0)

        status_labels = {
            "draft": ("🔵 Taslak", "#64748b"),
            "shipped": ("📦 Sevk Edildi", "#f59e0b"),
            "delivered": ("✅ Teslim Edildi", "#10b981"),
            "cancelled": ("⚫ İptal", "#475569"),
        }

        for row, note in enumerate(notes):
            self.table.insertRow(row)

            # İrsaliye No
            no_item = QTableWidgetItem(note.get("note_no", ""))
            no_item.setData(Qt.ItemDataRole.UserRole, note.get("id"))
            self.table.setItem(row, 0, no_item)

            # Tarih
            note_date = note.get("note_date")
            if note_date:
                if isinstance(note_date, date):
                    date_str = note_date.strftime("%d.%m.%Y")
                else:
                    date_str = str(note_date)
            else:
                date_str = "-"
            self.table.setItem(row, 1, QTableWidgetItem(date_str))

            # Müşteri
            self.table.setItem(
                row, 2, QTableWidgetItem(note.get("customer_name", "") or "-")
            )

            # Sipariş No
            self.table.setItem(
                row, 3, QTableWidgetItem(note.get("order_no", "") or "-")
            )

            # Kalem Sayısı
            item_count = note.get("total_items", 0)
            self.table.setItem(row, 4, QTableWidgetItem(str(item_count)))

            # Sevk Tarihi
            ship_date = note.get("ship_date")
            if ship_date:
                if isinstance(ship_date, date):
                    ship_str = ship_date.strftime("%d.%m.%Y")
                else:
                    ship_str = str(ship_date)
            else:
                ship_str = "-"
            self.table.setItem(row, 5, QTableWidgetItem(ship_str))

            # Durum
            status = note.get("status", "draft")
            status_text, _ = status_labels.get(status, ("Taslak", "#64748b"))
            status_item = QTableWidgetItem(status_text)
            self.table.setItem(row, 6, status_item)

            # İşlem butonları
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(4)

            note_id = note.get("id")
            note_status = note.get("status", "draft")

            # Görüntüle
            view_btn = QPushButton("👁")
            view_btn.setFixedSize(32, 32)
            view_btn.setStyleSheet(self._action_btn_style("#3b82f6"))
            view_btn.setToolTip("Görüntüle")
            view_btn.clicked.connect(
                lambda checked, id=note_id: self.view_clicked.emit(id)
            )
            btn_layout.addWidget(view_btn)

            # Düzenle (sadece taslak)
            if note_status == "draft":
                edit_btn = QPushButton("✏️")
                edit_btn.setFixedSize(32, 32)
                edit_btn.setStyleSheet(self._action_btn_style("#f59e0b"))
                edit_btn.setToolTip("Düzenle")
                edit_btn.clicked.connect(
                    lambda checked, id=note_id: self.edit_clicked.emit(id)
                )
                btn_layout.addWidget(edit_btn)

                # Sevk Et
                ship_btn = QPushButton("📦")
                ship_btn.setFixedSize(32, 32)
                ship_btn.setStyleSheet(self._action_btn_style("#f59e0b"))
                ship_btn.setToolTip("Sevk Et")
                ship_btn.clicked.connect(
                    lambda checked, id=note_id: self.ship_clicked.emit(id)
                )
                btn_layout.addWidget(ship_btn)

            # Teslim Et (sadece shipped)
            if note_status == "shipped":
                complete_btn = QPushButton("✅")
                complete_btn.setFixedSize(32, 32)
                complete_btn.setStyleSheet(self._action_btn_style("#10b981"))
                complete_btn.setToolTip("Teslim Et")
                complete_btn.clicked.connect(
                    lambda checked, id=note_id: self.complete_clicked.emit(id)
                )
                btn_layout.addWidget(complete_btn)

            # Fatura Oluştur (delivered)
            if note_status == "delivered":
                invoice_btn = QPushButton("📄")
                invoice_btn.setFixedSize(32, 32)
                invoice_btn.setStyleSheet(self._action_btn_style("#8b5cf6"))
                invoice_btn.setToolTip("Fatura Oluştur")
                invoice_btn.clicked.connect(
                    lambda checked, id=note_id: (
                        self.create_invoice_clicked.emit(id)
                    )
                )
                btn_layout.addWidget(invoice_btn)

            # İptal (sadece taslak veya shipped)
            if note_status in ["draft", "shipped"]:
                cancel_btn = QPushButton("❌")
                cancel_btn.setFixedSize(32, 32)
                cancel_btn.setStyleSheet(self._action_btn_style("#ef4444"))
                cancel_btn.setToolTip("İptal Et")
                cancel_btn.clicked.connect(
                    lambda checked, id=note_id: self.cancel_clicked.emit(id)
                )
                btn_layout.addWidget(cancel_btn)

            # Sil (sadece taslak)
            if note_status == "draft":
                del_btn = QPushButton("🗑")
                del_btn.setFixedSize(32, 32)
                del_btn.setStyleSheet(self._action_btn_style("#ef4444"))
                del_btn.setToolTip("Sil")
                del_btn.clicked.connect(
                    lambda checked, id=note_id: self._confirm_delete(id)
                )
                btn_layout.addWidget(del_btn)

            self.table.setCellWidget(row, 7, btn_widget)
            self.table.setRowHeight(row, 56)

    def _update_stats(self):
        """İstatistikleri güncelle"""
        total = len(self.notes)
        draft = sum(1 for n in self.notes if n.get("status") == "draft")
        shipped = sum(1 for n in self.notes if n.get("status") == "shipped")
        delivered = sum(1 for n in self.notes if n.get("status") == "delivered")

        self._update_card(self.total_card, str(total))
        self._update_card(self.draft_card, str(draft))
        self._update_card(self.shipped_card, str(shipped))
        self._update_card(self.delivered_card, str(delivered))

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
            for col in range(6):
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
            note_id = item.data(Qt.ItemDataRole.UserRole)
            if note_id:
                self.view_clicked.emit(note_id)

    def _confirm_delete(self, note_id: int):
        """Silme onayı"""
        reply = QMessageBox.question(
            self, "Silme Onayı",
            "Bu irsaliyeyi silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(note_id)
