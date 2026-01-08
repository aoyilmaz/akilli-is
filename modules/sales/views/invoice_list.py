"""
Akıllı İş - Faturalar Liste Sayfası
"""

from datetime import date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QFrame, QLineEdit,
    QHeaderView, QAbstractItemView, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal


class InvoiceListPage(QWidget):
    """Faturalar listesi"""

    add_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    view_clicked = pyqtSignal(int)
    issue_clicked = pyqtSignal(int)
    payment_clicked = pyqtSignal(int)
    cancel_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.invoices = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("📄 Faturalar")
        title.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #f8fafc;"
        )
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Durum filtresi
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tüm Durumlar", None)
        self.status_filter.addItem("🔵 Taslak", "draft")
        self.status_filter.addItem("📤 Kesildi", "issued")
        self.status_filter.addItem("🟡 Kısmi Ödendi", "partial_paid")
        self.status_filter.addItem("🟢 Ödendi", "paid")
        self.status_filter.addItem("🔴 Vadesi Geçti", "overdue")
        self.status_filter.addItem("⚫ İptal", "cancelled")
        self.status_filter.setStyleSheet(self._combo_style())
        self.status_filter.setMinimumWidth(160)
        self.status_filter.currentIndexChanged.connect(self._on_filter_changed)
        header_layout.addWidget(self.status_filter)

        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Ara... (fatura no, müşteri)")
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
        add_btn = QPushButton("➕ Yeni Fatura")
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

        self.issued_card = self._create_stat_card(
            "📤", "Kesildi", "0", "#3b82f6"
        )
        stats_layout.addWidget(self.issued_card)

        self.paid_card = self._create_stat_card("🟢", "Ödendi", "0", "#10b981")
        stats_layout.addWidget(self.paid_card)

        self.overdue_card = self._create_stat_card(
            "🔴", "Vadesi Geçti", "0", "#ef4444"
        )
        stats_layout.addWidget(self.overdue_card)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Fatura No", "Tarih", "Müşteri", "Toplam Tutar",
            "Ödenen", "Kalan", "Vade", "Durum", "İşlemler"
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
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(3, 110)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(6, 100)
        self.table.setColumnWidth(7, 120)
        self.table.setColumnWidth(8, 180)

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

    def load_data(self, invoices: list):
        """Verileri yükle"""
        self.invoices = invoices
        self._apply_filter()

    def _apply_filter(self):
        """Filtreyi uygula"""
        status_filter = self.status_filter.currentData()

        filtered = self.invoices
        if status_filter:
            filtered = [
                i for i in self.invoices if i.get("status") == status_filter
            ]

        self._display_data(filtered)
        self._update_stats()

    def _display_data(self, invoices: list):
        """Tabloya verileri yükle"""
        self.table.setRowCount(0)

        status_labels = {
            "draft": ("🔵 Taslak", "#64748b"),
            "issued": ("📤 Kesildi", "#3b82f6"),
            "partial_paid": ("🟡 Kısmi Ödendi", "#f59e0b"),
            "paid": ("🟢 Ödendi", "#10b981"),
            "overdue": ("🔴 Vadesi Geçti", "#ef4444"),
            "cancelled": ("⚫ İptal", "#475569"),
        }

        for row, inv in enumerate(invoices):
            self.table.insertRow(row)

            # Fatura No
            no_item = QTableWidgetItem(inv.get("invoice_no", ""))
            no_item.setData(Qt.ItemDataRole.UserRole, inv.get("id"))
            self.table.setItem(row, 0, no_item)

            # Tarih
            inv_date = inv.get("invoice_date")
            if inv_date:
                if isinstance(inv_date, date):
                    date_str = inv_date.strftime("%d.%m.%Y")
                else:
                    date_str = str(inv_date)
            else:
                date_str = "-"
            self.table.setItem(row, 1, QTableWidgetItem(date_str))

            # Müşteri
            self.table.setItem(
                row, 2, QTableWidgetItem(inv.get("customer_name", "") or "-")
            )

            # Toplam Tutar
            total = inv.get("total_amount", 0) or 0
            self.table.setItem(row, 3, QTableWidgetItem(f"{total:,.2f}"))

            # Ödenen
            paid = inv.get("paid_amount", 0) or 0
            self.table.setItem(row, 4, QTableWidgetItem(f"{paid:,.2f}"))

            # Kalan
            remaining = total - paid
            remaining_item = QTableWidgetItem(f"{remaining:,.2f}")
            if remaining > 0:
                remaining_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(row, 5, remaining_item)

            # Vade Tarihi
            due_date = inv.get("due_date")
            if due_date:
                if isinstance(due_date, date):
                    due_str = due_date.strftime("%d.%m.%Y")
                else:
                    due_str = str(due_date)
            else:
                due_str = "-"
            self.table.setItem(row, 6, QTableWidgetItem(due_str))

            # Durum
            status = inv.get("status", "draft")
            status_text, _ = status_labels.get(status, ("Taslak", "#64748b"))
            status_item = QTableWidgetItem(status_text)
            self.table.setItem(row, 7, status_item)

            # İşlem butonları
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(4)

            inv_id = inv.get("id")
            inv_status = inv.get("status", "draft")

            # Görüntüle
            view_btn = QPushButton("👁")
            view_btn.setFixedSize(32, 32)
            view_btn.setStyleSheet(self._action_btn_style("#3b82f6"))
            view_btn.setToolTip("Görüntüle")
            view_btn.clicked.connect(
                lambda checked, id=inv_id: self.view_clicked.emit(id)
            )
            btn_layout.addWidget(view_btn)

            # Düzenle (sadece taslak)
            if inv_status == "draft":
                edit_btn = QPushButton("✏️")
                edit_btn.setFixedSize(32, 32)
                edit_btn.setStyleSheet(self._action_btn_style("#f59e0b"))
                edit_btn.setToolTip("Düzenle")
                edit_btn.clicked.connect(
                    lambda checked, id=inv_id: self.edit_clicked.emit(id)
                )
                btn_layout.addWidget(edit_btn)

                # Kes
                issue_btn = QPushButton("📤")
                issue_btn.setFixedSize(32, 32)
                issue_btn.setStyleSheet(self._action_btn_style("#3b82f6"))
                issue_btn.setToolTip("Fatura Kes")
                issue_btn.clicked.connect(
                    lambda checked, id=inv_id: self.issue_clicked.emit(id)
                )
                btn_layout.addWidget(issue_btn)

            # Ödeme Kaydet (issued, partial_paid, overdue)
            if inv_status in ["issued", "partial_paid", "overdue"]:
                payment_btn = QPushButton("💰")
                payment_btn.setFixedSize(32, 32)
                payment_btn.setStyleSheet(self._action_btn_style("#10b981"))
                payment_btn.setToolTip("Ödeme Kaydet")
                payment_btn.clicked.connect(
                    lambda checked, id=inv_id: self.payment_clicked.emit(id)
                )
                btn_layout.addWidget(payment_btn)

            # İptal (sadece taslak veya issued)
            if inv_status in ["draft", "issued"]:
                cancel_btn = QPushButton("❌")
                cancel_btn.setFixedSize(32, 32)
                cancel_btn.setStyleSheet(self._action_btn_style("#ef4444"))
                cancel_btn.setToolTip("İptal Et")
                cancel_btn.clicked.connect(
                    lambda checked, id=inv_id: self.cancel_clicked.emit(id)
                )
                btn_layout.addWidget(cancel_btn)

            # Sil (sadece taslak)
            if inv_status == "draft":
                del_btn = QPushButton("🗑")
                del_btn.setFixedSize(32, 32)
                del_btn.setStyleSheet(self._action_btn_style("#ef4444"))
                del_btn.setToolTip("Sil")
                del_btn.clicked.connect(
                    lambda checked, id=inv_id: self._confirm_delete(id)
                )
                btn_layout.addWidget(del_btn)

            self.table.setCellWidget(row, 8, btn_widget)
            self.table.setRowHeight(row, 56)

    def _update_stats(self):
        """İstatistikleri güncelle"""
        total = len(self.invoices)
        draft = sum(1 for i in self.invoices if i.get("status") == "draft")
        issued = sum(1 for i in self.invoices if i.get("status") == "issued")
        paid = sum(1 for i in self.invoices if i.get("status") == "paid")
        overdue = sum(1 for i in self.invoices if i.get("status") == "overdue")

        self._update_card(self.total_card, str(total))
        self._update_card(self.draft_card, str(draft))
        self._update_card(self.issued_card, str(issued))
        self._update_card(self.paid_card, str(paid))
        self._update_card(self.overdue_card, str(overdue))

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
            inv_id = item.data(Qt.ItemDataRole.UserRole)
            if inv_id:
                self.view_clicked.emit(inv_id)

    def _confirm_delete(self, inv_id: int):
        """Silme onayı"""
        reply = QMessageBox.question(
            self, "Silme Onayı",
            "Bu faturayı silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(inv_id)
