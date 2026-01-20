"""
Akıllı İş - Stok Sayımı Liste Sayfası
Yeni bileşen mimarisi kullanılarak yeniden yapılandırıldı.
"""

from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidgetItem,
    QComboBox,
    QMenu,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QAction

from config import COLORS
from ui.components import (
    PageHeader,
    EnhancedTableWidget,
    ColumnConfig,
    MiniStatCard,
)


class StockCountListPage(QWidget):
    """Stok sayımı listesi."""

    # Sinyaller
    new_count_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    view_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    apply_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()

    STATUS_DISPLAY = {
        "draft": ("🟡 Taslak", "#f59e0b"),
        "in_progress": ("🔵 Devam Ediyor", "#3b82f6"),
        "completed": ("✅ Tamamlandı", "#10b981"),
        "applied": ("📥 Uygulandı", "#8b5cf6"),
        "cancelled": ("❌ İptal", "#ef4444"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        self.header = PageHeader(
            title="Stok Sayımı",
            icon="📋",
            show_search=False,
            show_refresh=True,
            show_add=True,
            add_text="Yeni Sayım",
            parent=self,
        )

        # Filtre ekle
        self.status_combo = QComboBox()
        self.status_combo.addItem("Tümü", None)
        self.status_combo.addItem("🟡 Taslak", "draft")
        self.status_combo.addItem("🔵 Devam Ediyor", "in_progress")
        self.status_combo.addItem("✅ Tamamlandı", "completed")
        self.status_combo.addItem("📥 Uygulandı", "applied")
        self.status_combo.addItem("❌ İptal", "cancelled")
        self.status_combo.setMinimumWidth(150)
        self.status_combo.setFixedHeight(36)
        self.status_combo.currentIndexChanged.connect(
            lambda: self.refresh_requested.emit()
        )

        h_layout = self.header.header_layout()
        h_layout.insertWidget(1, QLabel("Durum:"))
        h_layout.insertWidget(2, self.status_combo)

        layout.addWidget(self.header)

        # İstatistik kartları
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.stat_cards = {}
        self.stat_cards["draft"] = MiniStatCard("🟡 Taslak", "0", "#f59e0b")
        self.stat_cards["progress"] = MiniStatCard("🔵 Devam Eden", "0", "#3b82f6")
        self.stat_cards["completed"] = MiniStatCard("✅ Tamamlanan", "0", "#10b981")
        self.stat_cards["diff"] = MiniStatCard("📊 Toplam Fark", "₺0", "#ef4444")

        for card in self.stat_cards.values():
            stats_layout.addWidget(card)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Tablo
        columns = [
            ColumnConfig("count_no", "Sayım No", width=120),
            ColumnConfig("date", "Tarih", width=140),
            ColumnConfig("warehouse", "Depo", width=150),
            ColumnConfig("description", "Açıklama", width=200, stretch=True),
            ColumnConfig("item_count", "Ürün Sayısı", width=100),
            ColumnConfig("counted", "Sayılan", width=100),
            ColumnConfig("diff_amount", "Fark Tutarı", width=120),
            ColumnConfig("status", "Durum", width=120),
        ]

        self.table = EnhancedTableWidget(
            table_id="stock_counts",
            columns=columns,
            parent=self,
        )
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.table)

        # Alt bilgi
        self.count_label = QLabel("Toplam: 0 sayım")
        layout.addWidget(self.count_label)

    def _connect_signals(self):
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        self.header.add_clicked.connect(self.new_count_clicked.emit)
        self.table.row_double_clicked.connect(self.view_clicked.emit)

    def load_data(self, counts: list):
        self.table.setRowCount(len(counts))
        visible_cols = self.table.get_visible_columns()

        draft_count = progress_count = completed_count = 0
        total_diff = 0

        for row, count in enumerate(counts):
            self._populate_row(row, count, visible_cols)

            # İstatistikler
            status = count.get("status", "draft")
            if status == "draft":
                draft_count += 1
            elif status == "in_progress":
                progress_count += 1
            elif status == "completed":
                completed_count += 1
            total_diff += count.get("difference_amount", 0)

        # Kartları güncelle
        self.stat_cards["draft"].update_value(str(draft_count))
        self.stat_cards["progress"].update_value(str(progress_count))
        self.stat_cards["completed"].update_value(str(completed_count))
        self.stat_cards["diff"].update_value(f"₺{total_diff:,.2f}")

        self.count_label.setText(f"Toplam: {len(counts)} sayım")

    def _populate_row(self, row: int, count: dict, visible_cols: list):
        count_id = count.get("id")

        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "count_no":
                cell = QTableWidgetItem(count.get("count_no", ""))
                cell.setData(Qt.ItemDataRole.UserRole, count_id)
                cell.setForeground(QColor("#818cf8"))
                self.table.setItem(row, col_idx, cell)

            elif col_key == "date":
                date_str = count.get("count_date", "")
                if isinstance(date_str, datetime):
                    date_str = date_str.strftime("%d.%m.%Y %H:%M")
                self.table.setItem(row, col_idx, QTableWidgetItem(str(date_str)))

            elif col_key == "warehouse":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(count.get("warehouse_name", "-"))
                )

            elif col_key == "description":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(count.get("description", ""))
                )

            elif col_key == "item_count":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(str(count.get("item_count", 0)))
                )

            elif col_key == "counted":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(str(count.get("counted_items", 0)))
                )

            elif col_key == "diff_amount":
                diff = count.get("difference_amount", 0)
                cell = QTableWidgetItem(f"₺{diff:,.2f}")
                cell.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                if diff < 0:
                    cell.setForeground(QColor(COLORS["error"]))
                elif diff > 0:
                    cell.setForeground(QColor(COLORS["success"]))
                self.table.setItem(row, col_idx, cell)

            elif col_key == "status":
                status = count.get("status", "draft")
                status_text, status_color = self.STATUS_DISPLAY.get(
                    status, ("?", "#ffffff")
                )
                cell = QTableWidgetItem(status_text)
                cell.setForeground(QColor(status_color))
                self.table.setItem(row, col_idx, cell)

        self.table.setRowHeight(row, 48)

    def get_status_filter(self) -> str:
        return self.status_combo.currentData()

    def _show_context_menu(self, position):
        row = self.table.rowAt(position.y())
        if row < 0:
            return

        count_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        status_text = self.table.item(row, 7).text() if self.table.item(row, 7) else ""

        menu = QMenu(self)
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

    def _confirm_delete(self, count_id: int):
        reply = QMessageBox.question(
            self,
            "Silme Onayı",
            "Bu sayımı silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(count_id)

    def _confirm_apply(self, count_id: int):
        reply = QMessageBox.question(
            self,
            "Uygulama Onayı",
            "Sayım farklarını stoklara uygulamak istediğinize emin misiniz?\n\n"
            "Bu işlem geri alınamaz!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.apply_clicked.emit(count_id)
