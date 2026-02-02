"""
Akıllı İş - Kategori Listesi Sayfası
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QMenu,
    QMessageBox,
    QHeaderView,
    QComboBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QAction
import qtawesome as qta

from config.icons import ICONS
from config.themes import get_theme


class CategoryListPage(QWidget):
    """Kategori listesi (ağaç yapısı)"""

    add_clicked, add_child_clicked = pyqtSignal(), pyqtSignal(int)
    edit_clicked, delete_clicked = pyqtSignal(int), pyqtSignal(int)
    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.categories_data = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        from ui.components.page_header import PageHeader

        self.header = PageHeader(
            title="Stok Kategorileri",
            icon=ICONS.INVENTORY,
            show_search=True,
            show_add=True,
            add_text="Yeni Kategori",
            search_placeholder="Kategori ara...",
            parent=self,
        )

        # Expand/Collapse Buttons
        eb = QPushButton("Tümünü Aç")
        eb.setProperty("class", "btn-secondary")
        eb.setFixedHeight(36)
        eb.setIcon(qta.icon(ICONS.ARROW_DOWN, color="#475569"))
        eb.clicked.connect(lambda: self.tree.expandAll())

        cb = QPushButton("Tümünü Kapat")
        cb.setProperty("class", "btn-secondary")
        cb.setFixedHeight(36)
        cb.setIcon(qta.icon(ICONS.ARROW_UP, color="#475569"))
        cb.clicked.connect(lambda: self.tree.collapseAll())

        # Status Filter
        self.status_filter = QComboBox()
        self.status_filter.setFixedWidth(120)
        self.status_filter.setFixedHeight(36)
        self.status_filter.addItems(["Tümü", "Aktif", "Pasif"])
        self.status_filter.currentIndexChanged.connect(
            lambda: self._filter_tree(self.search_input.text())
        )

        hl = self.header.header_layout()
        idx = hl.indexOf(self.header.search_input) if self.header.search_input else -1
        if idx >= 0:
            hl.insertWidget(idx, QLabel("Durum:"))
            hl.insertWidget(idx + 1, self.status_filter)
            hl.insertWidget(idx + 2, eb)
            hl.insertWidget(idx + 3, cb)

        # Move Refresh button to the far right
        if self.header.refresh_btn:
            hl.removeWidget(self.header.refresh_btn)
            hl.addWidget(self.header.refresh_btn)

        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        self.header.add_clicked.connect(self.add_clicked.emit)
        self.header.search_changed.connect(self._filter_tree)
        self.search_input = self.header.search_input
        layout.addWidget(self.header)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Kategori", "Kod", "Ürün Sayısı", "Durum"])
        self.tree.setColumnCount(4)
        h = self.tree.header()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i, w in [(1, 120), (2, 100), (3, 100)]:
            h.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
            self.tree.setColumnWidth(i, w)
        self.tree.setAlternatingRowColors(True)
        self.tree.setAnimated(True)
        self.tree.setIndentation(24)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.tree)
        self.count_label = QLabel("Toplam: 0 kategori")
        layout.addWidget(self.count_label)

    def load_data(self, categories: list):
        self.tree.clear()
        self.categories_data = {c.id: c for c in categories}
        for cat in [c for c in categories if c.parent_id is None]:
            it = self._create_tree_item(cat)
            self.tree.addTopLevelItem(it)
            self._add_children(it, cat.id, categories)
        self.tree.expandAll()
        self.count_label.setText(f"Toplam: {len(categories)} kategori")

    def _create_tree_item(self, category) -> QTreeWidgetItem:
        it = QTreeWidgetItem()
        ic = category.icon or "📁"
        it.setText(0, f"{ic} {category.name}")
        it.setData(0, Qt.ItemDataRole.UserRole, category.id)
        it.setText(1, category.code)
        it.setForeground(1, QColor("#818cf8"))
        it.setText(2, str(len(category.items) if hasattr(category, "items") else 0))
        it.setTextAlignment(2, Qt.AlignmentFlag.AlignCenter)
        th = get_theme()
        if category.is_active:
            it.setText(3, "Aktif")
            it.setIcon(3, qta.icon(ICONS.STATUS_ICONS["active"], color=th.success))
            it.setForeground(3, QColor(th.success))
        else:
            it.setText(3, "Pasif")
            it.setIcon(3, qta.icon(ICONS.STATUS_ICONS["passive"], color=th.text_muted))
            it.setForeground(3, QColor(th.text_muted))
        return it

    def _add_children(self, parent_item, parent_id, categories):
        for cat in [c for c in categories if c.parent_id == parent_id]:
            it = self._create_tree_item(cat)
            parent_item.addChild(it)
            self._add_children(it, cat.id, categories)

    def _filter_tree(self, text: str):
        t = text.lower()
        status = self.status_filter.currentText()  # "Tümü", "Aktif", "Pasif"

        def filter_it(it):
            # Text matching
            text_match = t in it.text(0).lower() or t in it.text(1).lower()

            # Status matching
            status_match = True
            if status != "Tümü":
                item_status = it.text(3)  # "Aktif" or "Pasif"
                if status != item_status:
                    status_match = False

            matches = text_match and status_match

            # Check children
            child_matches = False
            for i in range(it.childCount()):
                if filter_it(it.child(i)):
                    child_matches = True

            # Show if matches or has matching children
            visible = matches or child_matches
            it.setHidden(not visible)

            if visible:
                it.setExpanded(True)

            return visible

        for i in range(self.tree.topLevelItemCount()):
            filter_it(self.tree.topLevelItem(i))

    def _show_context_menu(self, pos):
        it = self.tree.itemAt(pos)
        if not it:
            return
        cid = it.data(0, Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        ed = QAction("Düzenle", self)
        ed.setIcon(qta.icon(ICONS.EDIT, color="#cccccc"))
        ed.triggered.connect(lambda: self.edit_clicked.emit(cid))
        menu.addAction(ed)
        ac = QAction("Alt Kategori Ekle", self)
        ac.setIcon(qta.icon(ICONS.ADD, color="#cccccc"))
        ac.triggered.connect(lambda: self.add_child_clicked.emit(cid))
        menu.addAction(ac)
        menu.addSeparator()
        de = QAction("Sil", self)
        de.setIcon(qta.icon(ICONS.DELETE, color="#ef4444"))
        de.triggered.connect(lambda: self._confirm_delete(cid))
        menu.addAction(de)
        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _on_double_click(self, item, column):
        self.edit_clicked.emit(item.data(0, Qt.ItemDataRole.UserRole))

    def _confirm_delete(self, cid):
        cat = self.categories_data.get(cid)
        if not cat:
            return
        hc = any(c.parent_id == cid for c in self.categories_data.values())
        msg = f"'{cat.name}' kategorisini silmek istediğinize emin misiniz?"
        if hc:
            msg += "\n\n⚠️ Bu kategorinin alt kategorileri var!"
        if (
            QMessageBox.question(
                self,
                "Silme Onayı",
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        ):
            self.delete_clicked.emit(cid)
