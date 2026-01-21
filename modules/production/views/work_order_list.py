"""
Akıllı İş - İş Emirleri Liste Sayfası
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

from core.export_manager import ExportManager
from core.label_manager import LabelManager
from ui.components import (
    PageHeader,
    EnhancedTableWidget,
    ColumnConfig,
    MiniStatCard,
)


class WorkOrderListPage(QWidget):
    """İş emirleri listesi."""

    # Sinyaller
    new_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    view_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    status_change_requested = pyqtSignal(int, str)
    refresh_requested = pyqtSignal()

    STATUS_DISPLAY = {
        "draft": ("📝 Taslak", "#94a3b8"),
        "planned": ("📅 Planlandı", "#3b82f6"),
        "released": ("🚀 Serbest", "#8b5cf6"),
        "in_progress": ("🔄 Üretimde", "#f59e0b"),
        "completed": ("✅ Tamamlandı", "#10b981"),
        "quality_check": ("🔍 Kalite Kontrol", "#06b6d4"),
        "closed": ("🔒 Kapatıldı", "#64748b"),
        "cancelled": ("❌ İptal", "#ef4444"),
    }

    PRIORITY_DISPLAY = {
        "low": ("Düşük", "#64748b"),
        "normal": ("Normal", "#3b82f6"),
        "high": ("Yüksek", "#f59e0b"),
        "urgent": ("Acil", "#ef4444"),
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
            title="İş Emirleri",
            icon="📋",
            show_search=True,
            show_refresh=True,
            show_add=True,
            show_export=True,
            add_text="Yeni İş Emri",
            search_placeholder="İş emri ara...",
            parent=self,
        )

        # Export menüsüne etiket ekleme
        if self.header.export_btn:
            export_menu = ExportManager.create_export_menu(self, self._get_export_data)
            export_menu.addSeparator()
            label_action = QAction("🏷️ Etiket Bas", self)
            label_action.triggered.connect(self._print_labels)
            export_menu.addAction(label_action)
            self.header.export_btn.setMenu(export_menu)

        # Filtre ekle
        self.status_combo = QComboBox()
        self.status_combo.addItem("Tümü", None)
        self.status_combo.addItem("📝 Taslak", "draft")
        self.status_combo.addItem("📅 Planlandı", "planned")
        self.status_combo.addItem("🚀 Serbest", "released")
        self.status_combo.addItem("🔄 Üretimde", "in_progress")
        self.status_combo.addItem("🔍 Kalite Kontrol", "quality_check")
        self.status_combo.addItem("✅ Tamamlandı", "completed")
        self.status_combo.addItem("🔒 Kapatıldı", "closed")
        self.status_combo.setMinimumWidth(140)
        self.status_combo.currentIndexChanged.connect(
            lambda: self.refresh_requested.emit()
        )

        if self.header.search_input:
            h_layout = self.header.header_layout()
            idx = h_layout.indexOf(self.header.search_input)
            h_layout.insertWidget(idx, QLabel("Durum:"))
            h_layout.insertWidget(idx + 1, self.status_combo)

        layout.addWidget(self.header)

        # İstatistik kartları
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.stat_cards = {}
        self.stat_cards["total"] = MiniStatCard("📋 Toplam", "0", "#6366f1")
        self.stat_cards["in_progress"] = MiniStatCard("🔄 Üretimde", "0", "#f59e0b")
        self.stat_cards["completed"] = MiniStatCard("✅ Tamamlanan", "0", "#10b981")
        self.stat_cards["delayed"] = MiniStatCard("⚠️ Geciken", "0", "#ef4444")

        for card in self.stat_cards.values():
            stats_layout.addWidget(card)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Tablo
        columns = [
            ColumnConfig("order_no", "İş Emri No", width=120),
            ColumnConfig("item_name", "Mamul", width=180, stretch=True),
            ColumnConfig("quantity", "Miktar", width=100),
            ColumnConfig("start", "Planlanan Başlangıç", width=140),
            ColumnConfig("end", "Planlanan Bitiş", width=140),
            ColumnConfig("progress", "İlerleme", width=100),
            ColumnConfig("priority", "Öncelik", width=90),
            ColumnConfig("status", "Durum", width=110),
        ]

        self.table = EnhancedTableWidget(
            table_id="work_orders",
            columns=columns,
            parent=self,
        )
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.table)

        # Alt bilgi
        self.count_label = QLabel("Toplam: 0 iş emri")
        layout.addWidget(self.count_label)

    def _connect_signals(self):
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        self.header.add_clicked.connect(self.new_clicked.emit)
        self.header.search_changed.connect(self._on_search)
        self.table.row_double_clicked.connect(self.view_clicked.emit)

    def load_data(self, work_orders: list):
        self.table.setRowCount(len(work_orders))
        visible_cols = self.table.get_visible_columns()

        now = datetime.now()
        in_progress_count = completed_count = delayed_count = 0

        for row, wo in enumerate(work_orders):
            self._populate_row(row, wo, visible_cols, now)

            status = wo.get("status", "draft")
            if status == "in_progress":
                in_progress_count += 1
            elif status in ["quality_check", "completed", "closed"]:
                completed_count += 1

            end = wo.get("planned_end")
            if end and status in ["planned", "released", "in_progress"] and end < now:
                delayed_count += 1

        # Kartları güncelle
        self.stat_cards["total"].update_value(str(len(work_orders)))
        self.stat_cards["in_progress"].update_value(str(in_progress_count))
        self.stat_cards["completed"].update_value(str(completed_count))
        self.stat_cards["delayed"].update_value(str(delayed_count))

        self.count_label.setText(f"Toplam: {len(work_orders)} iş emri")

    def _populate_row(self, row: int, wo: dict, visible_cols: list, now):
        wo_id = wo.get("id")

        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "order_no":
                item = QTableWidgetItem(wo.get("order_no", ""))
                item.setData(Qt.ItemDataRole.UserRole, wo_id)
                item.setForeground(QColor("#818cf8"))
                self.table.setItem(row, col_idx, item)

            elif col_key == "item_name":
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(wo.get("item_name", "-"))
                )

            elif col_key == "quantity":
                planned = wo.get("planned_quantity", 0)
                completed = wo.get("completed_quantity", 0)
                qty_text = f"{completed:,.0f} / {planned:,.0f}"
                item = QTableWidgetItem(qty_text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col_idx, item)

            elif col_key == "start":
                start = wo.get("planned_start")
                start_text = start.strftime("%d.%m.%Y %H:%M") if start else "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(start_text))

            elif col_key == "end":
                end = wo.get("planned_end")
                end_text = end.strftime("%d.%m.%Y %H:%M") if end else "-"
                item = QTableWidgetItem(end_text)
                status = wo.get("status", "draft")
                if (
                    end
                    and status in ["planned", "released", "in_progress"]
                    and end < now
                ):
                    item.setForeground(QColor("#ef4444"))
                self.table.setItem(row, col_idx, item)

            elif col_key == "progress":
                progress = wo.get("progress_rate", 0)
                item = QTableWidgetItem(f"%{progress:.0f}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if progress >= 100:
                    item.setForeground(QColor("#10b981"))
                elif progress > 0:
                    item.setForeground(QColor("#f59e0b"))
                self.table.setItem(row, col_idx, item)

            elif col_key == "priority":
                priority = wo.get("priority", "normal")
                text, color = self.PRIORITY_DISPLAY.get(priority, ("Normal", "#3b82f6"))
                item = QTableWidgetItem(text)
                item.setForeground(QColor(color))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col_idx, item)

            elif col_key == "status":
                status = wo.get("status", "draft")
                text, color = self.STATUS_DISPLAY.get(status, ("?", "#ffffff"))
                item = QTableWidgetItem(text)
                item.setForeground(QColor(color))
                self.table.setItem(row, col_idx, item)

        self.table.setRowHeight(row, 48)

    def get_status_filter(self) -> str:
        return self.status_combo.currentData()

    def _on_search(self, text: str):
        text = text.lower()
        for row in range(self.table.rowCount()):
            match = any(
                self.table.item(row, col)
                and text in self.table.item(row, col).text().lower()
                for col in range(self.table.columnCount())
            )
            self.table.setRowHidden(row, not match)

    def _show_context_menu(self, position):
        row = self.table.rowAt(position.y())
        if row < 0:
            return

        wo_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        status_text = self.table.item(row, 7).text() if self.table.item(row, 7) else ""

        menu = QMenu(self)
        view_action = QAction("👁 Görüntüle", self)
        view_action.triggered.connect(lambda: self.view_clicked.emit(wo_id))
        menu.addAction(view_action)

        if "Taslak" in status_text:
            edit_action = QAction("✏️ Düzenle", self)
            edit_action.triggered.connect(lambda: self.edit_clicked.emit(wo_id))
            menu.addAction(edit_action)

        menu.addSeparator()

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

        if "Tamamlandı" in status_text or "Kalite Kontrol" in status_text:
            close_action = QAction("🔒 Kapat", self)
            close_action.triggered.connect(
                lambda: self.status_change_requested.emit(wo_id, "closed")
            )
            menu.addAction(close_action)

        menu.addSeparator()

        if "Taslak" in status_text:
            delete_action = QAction("🗑 Sil", self)
            delete_action.triggered.connect(lambda: self._confirm_delete(wo_id))
            menu.addAction(delete_action)

        menu.exec(self.table.viewport().mapToGlobal(position))

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
