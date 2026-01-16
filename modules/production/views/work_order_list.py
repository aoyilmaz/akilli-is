"""
Akıllı İş - İş Emirleri Liste Sayfası
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
from config.styles import get_button_style, BTN_HEIGHT_NORMAL, ICONS
from core.export_manager import ExportManager
from core.label_manager import LabelManager


class WorkOrderListPage(QWidget):
    """İş emirleri listesi"""

    new_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    view_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    status_change_requested = pyqtSignal(int, str)
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
        title = QLabel("📋 İş Emirleri")
        subtitle = QLabel("Üretim iş emirlerini yönetin ve takip edin")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addLayout(title_layout)

        header_layout.addStretch()

        # Durum filtresi
        header_layout.addWidget(QLabel("Durum:"))
        self.status_combo = QComboBox()
        self.status_combo.addItem("Tümü", None)
        self.status_combo.addItem("📝 Taslak", "draft")
        self.status_combo.addItem("📅 Planlandı", "planned")
        self.status_combo.addItem("🚀 Serbest", "released")
        self.status_combo.addItem("🔄 Üretimde", "in_progress")
        self.status_combo.addItem("✅ Tamamlandı", "completed")
        self.status_combo.addItem("🔒 Kapatıldı", "closed")
        self.status_combo.currentIndexChanged.connect(
            lambda: self.refresh_requested.emit()
        )
        header_layout.addWidget(self.status_combo)

        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 İş emri ara...")
        self.search_input.setFixedWidth(200)
        self.search_input.textChanged.connect(self._on_search)
        header_layout.addWidget(self.search_input)

        # Dışa Aktar
        export_btn = QPushButton(f"{ICONS['export']} Dışa Aktar")
        export_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        export_btn.setStyleSheet(get_button_style("export"))

        export_menu = ExportManager.create_export_menu(self, self._get_export_data)
        export_menu.addSeparator()
        label_action = QAction("🏷️ Etiket Bas", self)
        label_action.triggered.connect(self._print_labels)
        export_menu.addAction(label_action)

        export_btn.setMenu(export_menu)
        header_layout.addWidget(export_btn)

        # Yenile
        refresh_btn = QPushButton(f"{ICONS['refresh']} Yenile")
        refresh_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        refresh_btn.setStyleSheet(get_button_style("refresh"))
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        header_layout.addWidget(refresh_btn)

        # Yeni İş Emri
        new_btn = QPushButton(f"{ICONS['add']} Yeni İş Emri")
        new_btn.setFixedHeight(BTN_HEIGHT_NORMAL)
        new_btn.setStyleSheet(get_button_style("add"))
        new_btn.clicked.connect(self.new_clicked.emit)
        header_layout.addWidget(new_btn)

        layout.addLayout(header_layout)

        # === Özet Kartlar ===
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        self.total_card = self._create_card("📋 Toplam", "0", "#6366f1")
        cards_layout.addWidget(self.total_card)

        self.in_progress_card = self._create_card("🔄 Üretimde", "0", "#f59e0b")
        cards_layout.addWidget(self.in_progress_card)

        self.completed_card = self._create_card("✅ Tamamlanan", "0", "#10b981")
        cards_layout.addWidget(self.completed_card)

        self.delayed_card = self._create_card("⚠️ Geciken", "0", "#ef4444")
        cards_layout.addWidget(self.delayed_card)

        layout.addLayout(cards_layout)

        # === Tablo ===
        self.table = QTableWidget()
        self._setup_table()
        layout.addWidget(self.table)

        # === Alt Bilgi ===
        self.count_label = QLabel("Toplam: 0 iş emri")
        layout.addWidget(self.count_label)

    def _create_card(self, title: str, value: str, color: str) -> MiniStatCard:
        """Dashboard tarzı istatistik kartı"""
        return MiniStatCard(title, value, color)

    def _setup_table(self):
        columns = [
            ("İş Emri No", 120),
            ("Mamul", 180),
            ("Miktar", 100),
            ("Planlanan Başlangıç", 140),
            ("Planlanan Bitiş", 140),
            ("İlerleme", 100),
            ("Öncelik", 90),
            ("Durum", 110),
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

    def load_data(self, work_orders: list):
        """İş emirlerini yükle"""
        self.table.setRowCount(len(work_orders))

        status_display = {
            "draft": ("📝 Taslak", "#94a3b8"),
            "planned": ("📅 Planlandı", "#3b82f6"),
            "released": ("🚀 Serbest", "#8b5cf6"),
            "in_progress": ("🔄 Üretimde", "#f59e0b"),
            "completed": ("✅ Tamamlandı", "#10b981"),
            "closed": ("🔒 Kapatıldı", "#64748b"),
            "cancelled": ("❌ İptal", "#ef4444"),
        }

        priority_display = {
            "low": ("Düşük", "#64748b"),
            "normal": ("Normal", "#3b82f6"),
            "high": ("Yüksek", "#f59e0b"),
            "urgent": ("Acil", "#ef4444"),
        }

        total_count = len(work_orders)
        in_progress_count = 0
        completed_count = 0
        delayed_count = 0

        from datetime import datetime

        now = datetime.now()

        for row, wo in enumerate(work_orders):
            # İş Emri No
            no_item = QTableWidgetItem(wo.get("order_no", ""))
            no_item.setData(Qt.ItemDataRole.UserRole, wo.get("id"))
            no_item.setForeground(QColor("#818cf8"))
            self.table.setItem(row, 0, no_item)

            # Mamul
            self.table.setItem(row, 1, QTableWidgetItem(wo.get("item_name", "-")))

            # Miktar
            planned = wo.get("planned_quantity", 0)
            completed = wo.get("completed_quantity", 0)
            qty_text = f"{completed:,.0f} / {planned:,.0f}"
            qty_item = QTableWidgetItem(qty_text)
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, qty_item)

            # Planlanan Başlangıç
            start = wo.get("planned_start")
            start_text = start.strftime("%d.%m.%Y %H:%M") if start else "-"
            self.table.setItem(row, 3, QTableWidgetItem(start_text))

            # Planlanan Bitiş
            end = wo.get("planned_end")
            end_text = end.strftime("%d.%m.%Y %H:%M") if end else "-"
            end_item = QTableWidgetItem(end_text)

            # Gecikme kontrolü
            status = wo.get("status", "draft")
            if end and status in ["planned", "released", "in_progress"] and end < now:
                end_item.setForeground(QColor("#ef4444"))
                delayed_count += 1
            self.table.setItem(row, 4, end_item)

            # İlerleme
            progress = wo.get("progress_rate", 0)
            progress_item = QTableWidgetItem(f"%{progress:.0f}")
            progress_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if progress >= 100:
                progress_item.setForeground(QColor("#10b981"))
            elif progress > 0:
                progress_item.setForeground(QColor("#f59e0b"))
            self.table.setItem(row, 5, progress_item)

            # Öncelik
            priority = wo.get("priority", "normal")
            priority_text, priority_color = priority_display.get(
                priority, ("Normal", "#3b82f6")
            )
            priority_item = QTableWidgetItem(priority_text)
            priority_item.setForeground(QColor(priority_color))
            priority_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 6, priority_item)

            # Durum
            status_text, status_color = status_display.get(status, ("?", "#ffffff"))
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(QColor(status_color))
            self.table.setItem(row, 7, status_item)

            # İstatistikler
            if status == "in_progress":
                in_progress_count += 1
            elif status in ["completed", "closed"]:
                completed_count += 1

        # Kartları güncelle
        self._update_card(self.total_card, str(total_count))
        self._update_card(self.in_progress_card, str(in_progress_count))
        self._update_card(self.completed_card, str(completed_count))
        self._update_card(self.delayed_card, str(delayed_count))

        self.count_label.setText(f"Toplam: {len(work_orders)} iş emri")

    def _update_card(self, card: MiniStatCard, value: str):
        card.update_value(value)

    def get_status_filter(self) -> str:
        return self.status_combo.currentData()

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

        wo_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        status_text = self.table.item(row, 7).text()

        menu = QMenu(self)
        view_action = QAction("👁 Görüntüle", self)
        view_action.triggered.connect(lambda: self.view_clicked.emit(wo_id))
        menu.addAction(view_action)

        # Taslak ise düzenlenebilir
        if "Taslak" in status_text:
            edit_action = QAction("✏️ Düzenle", self)
            edit_action.triggered.connect(lambda: self.edit_clicked.emit(wo_id))
            menu.addAction(edit_action)

        menu.addSeparator()

        # Durum değişiklikleri
        if "Taslak" in status_text:
            plan_action = QAction("📅 Planla", self)
            plan_action.triggered.connect(
                lambda: self.status_change_requested.emit(wo_id, "planned")
            )
            menu.addAction(plan_action)

        if "Planlandı" in status_text:
            release_action = QAction("🚀 Serbest Bırak", self)
            release_action.triggered.connect(
                lambda: self.status_change_requested.emit(wo_id, "released")
            )
            menu.addAction(release_action)

        if "Serbest" in status_text:
            start_action = QAction("🔄 Üretime Başla", self)
            start_action.triggered.connect(
                lambda: self.status_change_requested.emit(wo_id, "in_progress")
            )
            menu.addAction(start_action)

        if "Üretimde" in status_text:
            complete_action = QAction("✅ Tamamla", self)
            complete_action.triggered.connect(
                lambda: self.status_change_requested.emit(wo_id, "completed")
            )
            menu.addAction(complete_action)

        if "Tamamlandı" in status_text:
            close_action = QAction("🔒 Kapat", self)
            close_action.triggered.connect(
                lambda: self.status_change_requested.emit(wo_id, "closed")
            )
            menu.addAction(close_action)

        menu.addSeparator()

        # Sadece taslak silinebilir
        if "Taslak" in status_text:
            delete_action = QAction("🗑 Sil", self)
            delete_action.triggered.connect(lambda: self._confirm_delete(wo_id))
            menu.addAction(delete_action)

        menu.exec(self.table.viewport().mapToGlobal(position))

    def _on_double_click(self, index):
        wo_id = self.table.item(index.row(), 0).data(Qt.ItemDataRole.UserRole)
        self.view_clicked.emit(wo_id)

    def _confirm_delete(self, wo_id: int):
        reply = QMessageBox.question(
            self,
            "Silme Onayı",
            "Bu iş emrini silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(wo_id)

    def _get_export_data(self):
        return ExportManager.extract_data_from_table(self.table)

    def _print_labels(self):
        data = self._get_export_data()
        LabelManager.print_work_order_labels(self, data)
