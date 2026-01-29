"""
Akıllı İş - Stok Sayımı Liste Sayfası
"""

from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QTableWidgetItem,
    QComboBox,
    QMenu,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QAction
import qtawesome as qta

from config.icons import ICONS
from ui.components import (
    BaseListPage,
    ColumnConfig,
)


class StockCountListPage(BaseListPage):
    """Stok sayımı listesi."""

    new_count_clicked, apply_clicked = pyqtSignal(), pyqtSignal(int)
    STATUS_DISPLAY = {
        "draft": ("Taslak", "#f59e0b"),
        "in_progress": ("Devam Ediyor", "#3b82f6"),
        "completed": ("Tamamlandı", "#10b981"),
        "applied": ("Uygulandı", "#8b5cf6"),
        "cancelled": ("İptal", "#ef4444"),
    }

    def __init__(self, parent=None):
        cols = [
            ColumnConfig("count_no", "Sayım No", width=120),
            ColumnConfig("date", "Tarih", width=140),
            ColumnConfig("warehouse", "Depo", width=150),
            ColumnConfig("description", "Açıklama", width=200, stretch=True),
            ColumnConfig("item_count", "Ürün Sayısı", width=100),
            ColumnConfig("counted", "Sayılan", width=100),
            ColumnConfig("diff_amount", "Fark Tutarı", width=120),
            ColumnConfig("status", "Durum", width=120),
            ColumnConfig(
                "actions",
                "İşlemler",
                width=140,
                resizable=False,
                movable=False,
                hideable=False,
            ),
        ]
        super().__init__(
            title="Stok Sayımı",
            icon=ICONS.INVENTORY,
            table_id="stock_counts",
            columns=cols,
            show_stats=True,
            show_search=True,
            show_refresh=True,
            show_add=True,
            add_text="Yeni Sayım",
            parent=parent,
        )
        self._setup_filters()
        self._setup_stat_cards()
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

    def _setup_filters(self):
        self.status_combo = QComboBox()
        self.status_combo.addItem("Tüm Durumlar", None)
        for t, v in [
            ("Taslak", "draft"),
            ("Devam Ediyor", "in_progress"),
            ("Tamamlandı", "completed"),
            ("Uygulandı", "applied"),
            ("İptal", "cancelled"),
        ]:
            self.status_combo.addItem(t, v)
        self.status_combo.setMinimumWidth(150)
        self.status_combo.currentIndexChanged.connect(
            lambda: self.refresh_requested.emit()
        )
        if self.header.search_input:
            hl = self.header.header_layout()
            idx = hl.indexOf(self.header.search_input)
            hl.insertWidget(idx, self.status_combo)

    def _setup_stat_cards(self):
        self.add_stat_card("draft", "Taslak", "0", "warning", ICONS.TIME)
        self.add_stat_card("progress", "Devam Eden", "0", "info", ICONS.TIME)
        self.add_stat_card("completed", "Tamamlanan", "0", "success", ICONS.CHECK)
        self.add_stat_card("diff", "Toplam Fark", "₺0", "danger", ICONS.MONEY)

    def _connect_signals(self):
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        self.header.add_clicked.connect(self.new_count_clicked.emit)
        self.table.row_double_clicked.connect(self.view_clicked.emit)

    def load_data(self, counts: list):
        self.table.setRowCount(len(counts))
        vcols = self.table.get_visible_columns()
        dc = pc = cc = td = 0
        for r, c in enumerate(counts):
            self._populate_row(r, c, vcols)
            s = c.get("status", "draft")
            if s == "draft":
                dc += 1
            elif s == "in_progress":
                pc += 1
            elif s == "completed":
                cc += 1
            td += c.get("difference_amount", 0)
        self.update_stat_card("draft", str(dc))
        self.update_stat_card("progress", str(pc))
        self.update_stat_card("completed", str(cc))
        self.update_stat_card("diff", f"₺{td:,.2f}")

    def _populate_row(self, r, c, vcols):
        cid, s = c.get("id"), c.get("status", "draft")
        for ci, k in enumerate(vcols):
            if k == "count_no":
                it = QTableWidgetItem(c.get("count_no", ""))
                it.setData(Qt.ItemDataRole.UserRole, cid)
                it.setForeground(QColor("#818cf8"))
                self.table.setItem(r, ci, it)
            elif k == "date":
                self.table.setItem(
                    r, ci, QTableWidgetItem(self._format_dt(c.get("count_date")))
                )
            elif k == "warehouse":
                self.table.setItem(
                    r, ci, QTableWidgetItem(c.get("warehouse_name", "-"))
                )
            elif k == "description":
                self.table.setItem(r, ci, QTableWidgetItem(c.get("description", "")))
            elif k in ["item_count", "counted"]:
                self.table.setItem(
                    r,
                    ci,
                    QTableWidgetItem(
                        str(
                            c.get(
                                "item_count" if k == "item_count" else "counted_items",
                                0,
                            )
                        )
                    ),
                )
            elif k == "diff_amount":
                v = c.get("difference_amount", 0)
                it = QTableWidgetItem(f"₺{v:,.2f}")
                it.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                if v < 0:
                    it.setForeground(QColor("#ef4444"))
                elif v > 0:
                    it.setForeground(QColor("#10b981"))
                self.table.setItem(r, ci, it)
            elif k == "status":
                txt, color = self.STATUS_DISPLAY.get(s, ("?", "#ffffff"))
                it = QTableWidgetItem(txt)
                it.setForeground(QColor(color))
                self.table.setItem(r, ci, it)
            elif k == "actions":
                self._setup_actions(r, ci, cid, s)

    def _setup_actions(self, r, ci, cid, s):
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(4, 2, 4, 2)
        l.setSpacing(4)
        from ui.components.action_buttons import (
            create_view_button,
            create_edit_button,
            create_delete_button,
            create_approve_button,
        )

        vb = create_view_button(w)
        vb.clicked.connect(lambda: self.view_clicked.emit(cid))
        l.addWidget(vb)
        if s in ["draft", "in_progress"]:
            eb = create_edit_button(w)
            eb.clicked.connect(lambda: self.edit_clicked.emit(cid))
            l.addWidget(eb)
            db = create_delete_button(w)
            db.clicked.connect(lambda: self._confirm_delete(cid))
            l.addWidget(db)
        elif s == "completed":
            ab = create_approve_button(w)
            ab.setToolTip("Stoklara Uygula")
            ab.clicked.connect(lambda: self._confirm_apply(cid))
            l.addWidget(ab)
        l.addStretch()
        self.table.setCellWidget(r, ci, w)

    def _format_dt(self, dt) -> str:
        return (
            dt.strftime("%d.%m.%Y %H:%M")
            if isinstance(dt, datetime)
            else str(dt or "-")
        )

    def get_status_filter(self) -> str:
        return self.status_combo.currentData()

    def _show_context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0:
            return
        cid = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        st = self.table.item(row, 7).text() if self.table.item(row, 7) else ""
        menu = QMenu(self)
        vi = QAction("Görüntüle", self)
        vi.setIcon(qta.icon(ICONS.VIEW, color="#cccccc"))
        vi.triggered.connect(lambda: self.view_clicked.emit(cid))
        menu.addAction(vi)
        if "Taslak" in st or "Devam" in st:
            ed = QAction("Düzenle", self)
            ed.setIcon(qta.icon(ICONS.EDIT, color="#cccccc"))
            ed.triggered.connect(lambda: self.edit_clicked.emit(cid))
            menu.addAction(ed)
        if "Tamamlandı" in st:
            ap = QAction("Stoklara Uygula", self)
            ap.setIcon(qta.icon(ICONS.CHECK, color="#10b981"))
            ap.triggered.connect(lambda: self._confirm_apply(cid))
            menu.addAction(ap)
        menu.addSeparator()
        if "Taslak" in st:
            de = QAction("Sil", self)
            de.setIcon(qta.icon(ICONS.DELETE, color="#ef4444"))
            de.triggered.connect(lambda: self._confirm_delete(cid))
            menu.addAction(de)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _confirm_delete(self, cid):
        if (
            QMessageBox.question(
                self,
                "Silme Onayı",
                "Bu sayımı silmek istediğinize emin misiniz?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        ):
            self.delete_clicked.emit(cid)

    def _confirm_apply(self, cid):
        msg = "Sayım farklarını stoklara uygulamak istediğinize emin misiniz?\n\nBu işlem geri alınamaz!"
        if (
            QMessageBox.question(
                self,
                "Uygulama Onayı",
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        ):
            self.apply_clicked.emit(cid)
