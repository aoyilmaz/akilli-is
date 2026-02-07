"""
Akıllı İş - İş Emirleri Liste Sayfası
"""

from datetime import datetime
from PyQt6.QtWidgets import (
    QTableWidgetItem,
    QMenu,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QAction

from config.icons import ICONS
import qtawesome as qta
from core.export_manager import ExportManager
from core.label_manager import LabelManager
from ui.components.base_list_page import BaseListPage
from ui.components.enhanced_table import ColumnConfig


class WorkOrderListPage(BaseListPage):
    """İş emirleri listesi."""

    # BaseListPage sinyallerini kullan: add_clicked, edit_clicked, view_clicked, delete_clicked, refresh_requested
    status_change_requested = pyqtSignal(int, str)
    new_clicked = (
        pyqtSignal()
    )  # BaseListPage add_clicked'i buna bağlayabiliriz veya direkt onu kullanabiliriz.
    # Uyumlu olması için add_clicked -> new_clicked emit edelim.

    STATUS_DISPLAY = {
        "draft": ("Taslak", "#94a3b8"),
        "planned": ("Planlandı", "#3b82f6"),
        "released": ("Serbest", "#8b5cf6"),
        "in_progress": ("Üretimde", "#f59e0b"),
        "completed": ("Tamamlandı", "#10b981"),
        "quality_check": ("Kalite Kontrol", "#06b6d4"),
        "closed": ("Kapatıldı", "#64748b"),
        "cancelled": ("İptal", "#475569"),
    }

    PRIORITY_DISPLAY = {
        "low": ("Düşük", "#64748b"),
        "normal": ("Normal", "#3b82f6"),
        "high": ("Yüksek", "#f59e0b"),
        "urgent": ("Acil", "#ef4444"),
    }

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("order_no", "İş Emri No", width=120, filterable=True),
            ColumnConfig(
                "item_name", "Mamul", width=180, stretch=True, filterable=True
            ),
            ColumnConfig("quantity", "Miktar", width=100, filter_type="number"),
            ColumnConfig("start", "Planlanan Başlangıç", width=140),
            ColumnConfig("end", "Planlanan Bitiş", width=140),
            ColumnConfig("progress", "İlerleme", width=100, filter_type="number"),
            ColumnConfig("oee", "OEE", width=80, filter_type="number"),
            ColumnConfig("risk", "Risk", width=80, filter_type="enum"),
            ColumnConfig("priority", "Öncelik", width=90, filter_type="enum"),
            ColumnConfig("status", "Durum", width=110, filter_type="enum"),
        ]

        super().__init__(
            title="İş Emirleri",
            icon=ICONS.WORK_ORDER,
            table_id="work_orders",
            columns=columns,
            show_add=True,
            show_export=True,
            add_text="Yeni İş Emri",
            search_placeholder="İş emri ara...",
            parent=parent,
        )

        # Ekstra UI ayarları
        self._setup_extra_ui()

        # Sinyal yönlendirmeleri
        self.add_clicked.connect(self.new_clicked.emit)

    def _setup_extra_ui(self):
        # Export menüsüne etiket ekleme
        if self.header.export_btn:
            export_menu = ExportManager.create_export_menu(self, self._get_export_data)
            export_menu.addSeparator()
            label_action = QAction("Etiket Bas", self)
            label_action.setIcon(
                qta.icon(ICONS.TAG, color="#ffffff")
            )  # color beyaz olsun dark mode uyumlu? original white
            label_action.triggered.connect(self._print_labels)
            export_menu.addAction(label_action)
            self.header.export_btn.setMenu(export_menu)

        # Footer İstatistikleri
        self.footer.add_stat("in_progress", "Üretimde", ICONS.PLAY, "warning")
        self.footer.add_stat("completed", "Tamamlanan", ICONS.CHECK, "success")
        self.footer.add_stat("delayed", "Geciken", ICONS.WARNING, "error")

        # Context Menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # Filtre seçenekleri
        self.table.set_filter_options(
            "status", [v[0] for v in self.STATUS_DISPLAY.values()]
        )
        self.table.set_filter_options(
            "priority", [v[0] for v in self.PRIORITY_DISPLAY.values()]
        )
        self.table.set_filter_options("risk", ["Yok", "Düşük", "Yüksek"])

    def load_data(self, work_orders: list):
        self.table.setRowCount(len(work_orders))

        now = datetime.now()
        in_progress_count = completed_count = delayed_count = 0

        self.table.setSortingEnabled(False)
        for row, wo in enumerate(work_orders):
            self._populate_row(row, wo, now)

            status = wo.get("status", "draft")
            if status == "in_progress":
                in_progress_count += 1
            elif status in ["quality_check", "completed", "closed"]:
                completed_count += 1

            end = wo.get("planned_end")
            if end and status in ["planned", "released", "in_progress"] and end < now:
                delayed_count += 1
        self.table.setSortingEnabled(True)

        # Kartları güncelle
        self.update_count(len(work_orders))
        self.update_stat_card("in_progress", str(in_progress_count))
        self.update_stat_card("completed", str(completed_count))
        self.update_stat_card("delayed", str(delayed_count))

        # Filtreleri uygula
        self.table.apply_saved_filters()

    def _populate_row(self, row: int, wo: dict, now):
        wo_id = wo.get("id")

        # order_no
        item = QTableWidgetItem(wo.get("order_no", ""))
        item.setData(Qt.ItemDataRole.UserRole, wo_id)
        item.setForeground(QColor("#818cf8"))
        self.table.setItem(row, 0, item)

        # item_name
        self.table.setItem(row, 1, QTableWidgetItem(wo.get("item_name", "-")))

        # quantity
        planned = wo.get("planned_quantity", 0)
        completed = wo.get("completed_quantity", 0)
        qty_text = f"{completed:,.0f} / {planned:,.0f}"  # 0/100
        # Sort by planned quantity maybe? Or progress?
        # Let's use custom numeric item with planned quantity value for sorting
        from ui.components.enhanced_table import NumericTableWidgetItem

        item = NumericTableWidgetItem(planned, qty_text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 2, item)

        # start
        start = wo.get("planned_start")
        start_text = start.strftime("%d.%m.%Y %H:%M") if start else "-"
        self.table.setItem(row, 3, QTableWidgetItem(start_text))

        # end
        end = wo.get("planned_end")
        end_text = end.strftime("%d.%m.%Y %H:%M") if end else "-"
        item = QTableWidgetItem(end_text)
        status = wo.get("status", "draft")
        if end and status in ["planned", "released", "in_progress"] and end < now:
            item.setForeground(QColor("#ef4444"))
        self.table.setItem(row, 4, item)

        # progress
        progress = wo.get("progress_rate", 0)
        from ui.components.enhanced_table import NumericTableWidgetItem

        item = NumericTableWidgetItem(progress, f"%{progress:.0f}")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if progress >= 100:
            item.setForeground(QColor("#10b981"))
        elif progress > 0:
            item.setForeground(QColor("#f59e0b"))
        self.table.setItem(row, 5, item)

        # OEE
        oee = wo.get("total_oee", 0)
        item = NumericTableWidgetItem(oee, f"%{oee:.0f}")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if oee >= 85:
            item.setForeground(QColor("#10b981"))
        elif oee > 0:
            item.setForeground(QColor("#f59e0b"))
        self.table.setItem(row, 6, item)

        # Risk
        risk = wo.get("delay_risk", "none")
        risk_map = {
            "none": ("Yok", "#94a3b8", ""),
            "low": ("Düşük", "#f59e0b", ICONS.WARNING),
            "high": ("Yüksek", "#ef4444", ICONS.WARNING),
        }
        risk_text, risk_color, risk_icon = risk_map.get(risk, ("Yok", "#94a3b8", ""))
        item = QTableWidgetItem(risk_text)
        item.setForeground(QColor(risk_color))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if risk_icon:
            item.setIcon(qta.icon(risk_icon, color=risk_color))
        self.table.setItem(row, 7, item)

        # priority
        priority = wo.get("priority", "normal")
        text, color = self.PRIORITY_DISPLAY.get(priority, ("Normal", "#3b82f6"))
        item = QTableWidgetItem(text)
        item.setForeground(QColor(color))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 8, item)

        # status
        status = wo.get("status", "draft")
        text, color = self.STATUS_DISPLAY.get(status, ("?", "#ffffff"))
        item = QTableWidgetItem(text)
        item.setForeground(QColor(color))
        self.table.setItem(row, 9, item)

    def _show_context_menu(self, position):
        row = self.table.rowAt(position.y())
        if row < 0:
            return

        wo_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        status_col = self.table.columnCount() - 1
        status_text = (
            self.table.item(row, status_col).text()
            if self.table.item(row, status_col)
            else ""
        )

        menu = QMenu(self)
        view_action = QAction("Görüntüle", self)
        view_action.triggered.connect(lambda: self.view_clicked.emit(wo_id))
        menu.addAction(view_action)

        if "Taslak" in status_text:
            edit_action = QAction("Düzenle", self)
            edit_action.triggered.connect(lambda: self.edit_clicked.emit(wo_id))
            menu.addAction(edit_action)

        menu.addSeparator()

        if "Taslak" in status_text:
            plan_action = QAction("Planla", self)
            plan_action.triggered.connect(
                lambda: self.status_change_requested.emit(wo_id, "planned")
            )
            menu.addAction(plan_action)

        if "Planlandı" in status_text:
            release_action = QAction("Serbest Bırak", self)
            release_action.triggered.connect(
                lambda: self.status_change_requested.emit(wo_id, "released")
            )
            menu.addAction(release_action)

        if "Serbest" in status_text:
            start_action = QAction("Üretime Başla", self)
            start_action.triggered.connect(
                lambda: self.status_change_requested.emit(wo_id, "in_progress")
            )
            menu.addAction(start_action)

        if "Üretimde" in status_text:
            complete_action = QAction("Tamamla", self)
            complete_action.triggered.connect(
                lambda: self.status_change_requested.emit(wo_id, "completed")
            )
            menu.addAction(complete_action)

        if "Tamamlandı" in status_text or "Kalite Kontrol" in status_text:
            close_action = QAction("Kapat", self)
            close_action.triggered.connect(
                lambda: self.status_change_requested.emit(wo_id, "closed")
            )
            menu.addAction(close_action)

        menu.addSeparator()

        if "Taslak" in status_text:
            delete_action = QAction("Sil", self)
            delete_action.triggered.connect(lambda: self._confirm_delete(wo_id))
            menu.addAction(delete_action)

        menu.exec(self.table.viewport().mapToGlobal(position))

    def _confirm_delete(self, wo_id: int):
        if self.confirm_delete("iş emrini"):
            self.delete_clicked.emit(wo_id)

    def get_filters(self) -> dict:
        return {
            "keyword": self.header.get_search_text(),
            # "status": self.filter_status_combo.currentData() if hasattr ... (WorkOrderListPage UI doesnt have combo filters in header yet, derived from table filters mostly)
            # Standard implementation typically just returns keyword if no specific header controls exist
        }

    def get_search_text(self) -> str:
        return self.header.get_search_text()

    def _get_export_data(self):
        return ExportManager.extract_data_from_table(self.table)

    def _print_labels(self):
        data = self._get_export_data()
        LabelManager.print_work_order_labels(self, data)
