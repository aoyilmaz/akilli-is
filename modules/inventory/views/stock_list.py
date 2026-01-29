"""
Akıllı İş - Stok Kartları Liste Sayfası
Yeni bileşen mimarisi kullanılarak yeniden yapılandırıldı.
"""

from decimal import Decimal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidgetItem,
    QComboBox,
    QMenu,
    QMessageBox,
    QPushButton,
    QLineEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QAction, QIcon
import qtawesome as qta

from config import COLORS
from database.models import ItemType
from core.export_manager import ExportManager
from core.label_manager import LabelManager
from ui.components import (
    PageHeader,
    EnhancedTableWidget,
    ColumnConfig,
    MiniStatCard,
    ScrollableCardContainer,
)
from config.icons import ICONS
from config.themes import get_theme


class StockListPage(QWidget):
    """Stok kartları liste sayfası."""

    # Sinyaller
    item_selected = pyqtSignal(int)
    add_clicked = pyqtSignal()
    duplicate_clicked = pyqtSignal(int)
    edit_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()
    next_page_clicked = pyqtSignal()
    prev_page_clicked = pyqtSignal()

    TYPE_NAMES = {
        ItemType.HAMMADDE: "Hammadde",
        ItemType.MAMUL: "Mamül",
        ItemType.YARI_MAMUL: "Yarı Mamül",
        ItemType.AMBALAJ: "Ambalaj",
        ItemType.SARF: "Sarf",
        ItemType.TICARI: "Ticari",
        ItemType.HIZMET: "Hizmet",
        ItemType.DIGER: "Diğer",
    }

    TYPE_ICONS = {
        ItemType.HAMMADDE: ICONS.TYPE_RAW,
        ItemType.MAMUL: ICONS.TYPE_PRODUCT,
        ItemType.YARI_MAMUL: ICONS.TYPE_SEMI,
        ItemType.AMBALAJ: ICONS.TYPE_PACKAGE,
        ItemType.SARF: ICONS.TYPE_CONSUMABLE,
        ItemType.TICARI: ICONS.TYPE_COMMERCIAL,
        ItemType.HIZMET: ICONS.TYPE_SERVICE,
        ItemType.DIGER: ICONS.TYPE_OTHER,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items_data = []
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        self.header = PageHeader(
            title="Stok Kartları",
            icon=ICONS.INVENTORY,
            show_search=False,  # Header aramasını kapattık
            show_refresh=True,
            show_add=True,
            show_export=True,
            add_text="Yeni Stok Kartı",
            search_placeholder="",
            parent=self,
        )

        # Export menüsüne etiket ekleme
        if self.header.export_btn:
            export_menu = ExportManager.create_export_menu(self, self._get_export_data)
            export_menu.addSeparator()
            label_action = QAction("Ürün Etiketi Bas", self)
            label_action.setIcon(qta.icon(ICONS.TAG, color="black"))
            label_action.triggered.connect(self._print_labels)
            export_menu.addAction(label_action)
            self.header.export_btn.setMenu(export_menu)

        # Filtreleri header'a ekle
        self.active_combo = QComboBox()
        self.active_combo.addItem("Aktif Kayıtlar", True)
        self.active_combo.addItem("Pasif Kayıtlar", False)
        self.active_combo.addItem("Tümü", None)
        self.active_combo.setMinimumWidth(120)
        self.active_combo.setFixedHeight(36)
        self.active_combo.currentIndexChanged.connect(self._do_search)

        self.type_combo = QComboBox()
        self.type_combo.addItem("Tümü", None)
        for item_type, label in self.TYPE_NAMES.items():
            icon_name = self.TYPE_ICONS.get(item_type, "")
            icon = qta.icon(icon_name) if icon_name else QIcon()
            self.type_combo.addItem(icon, label, item_type)

        self.type_combo.setMinimumWidth(130)
        self.type_combo.setFixedHeight(36)
        self.type_combo.currentIndexChanged.connect(self._do_search)

        self.status_combo = QComboBox()
        self.status_combo.addItem("Tümü", None)
        self.status_combo.addItem(
            qta.icon(ICONS.STATUS_ICONS["success"], color="#22c55e"), "Normal", "normal"
        )
        self.status_combo.addItem(
            qta.icon(ICONS.STATUS_ICONS["low"], color="#eab308"), "Düşük Stok", "low"
        )
        self.status_combo.addItem(
            qta.icon(ICONS.STATUS_ICONS["critical"], color="#f97316"),
            "Kritik",
            "critical",
        )
        self.status_combo.addItem(
            qta.icon(ICONS.STATUS_ICONS["out_of_stock"], color="#ef4444"),
            "Stok Yok",
            "out_of_stock",
        )
        self.status_combo.setMinimumWidth(120)
        self.status_combo.setFixedHeight(36)
        self.status_combo.currentIndexChanged.connect(self._do_search)

        # Filtreleri ekle
        h_layout = self.header.header_layout()
        # Butonlardan önce ekle
        target_widget = (
            self.header.export_btn or self.header.refresh_btn or self.header.add_btn
        )

        if target_widget:
            idx = h_layout.indexOf(target_widget)
            h_layout.insertWidget(idx, QLabel("Durum:"))
            h_layout.insertWidget(idx + 1, self.active_combo)
            h_layout.insertWidget(idx + 2, QLabel("Tür:"))
            h_layout.insertWidget(idx + 3, self.type_combo)
            h_layout.insertWidget(idx + 4, QLabel("Stok:"))
            h_layout.insertWidget(idx + 5, self.status_combo)
        else:
            h_layout.addWidget(QLabel("Durum:"))
            h_layout.addWidget(self.active_combo)
            h_layout.addWidget(QLabel("Tür:"))
            h_layout.addWidget(self.type_combo)
            h_layout.addWidget(QLabel("Stok:"))
            h_layout.addWidget(self.status_combo)

        layout.addWidget(self.header)

        # Search input (Headerdan buraya taşıdık)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Stok kodu, adı veya barkod ile ara...")
        self.search_input.addAction(
            qta.icon(ICONS.SEARCH, color="#94a3b8"),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        self.search_input.setFixedHeight(30)
        self.search_input.setFixedWidth(280)
        self.search_input.textChanged.connect(self._on_search_changed)

        # İstatistik kartları (Scrollable)
        stats_container = ScrollableCardContainer()
        self.stat_cards = {}
        # Toplam: Kahverengi
        self.stat_cards["total"] = MiniStatCard(
            "Toplam", "0", "info", icon=ICONS.INVENTORY, icon_color="#8d6e63"
        )
        # Normal: Yeşil
        self.stat_cards["normal"] = MiniStatCard(
            "Normal", "0", "success", icon=ICONS.SUCCESS, icon_color="#22c55e"
        )
        # Düşük: Sarı
        self.stat_cards["low"] = MiniStatCard(
            "Düşük", "0", "warning", icon=ICONS.WARNING, icon_color="#eab308"
        )
        # Kritik: Turuncu
        self.stat_cards["critical"] = MiniStatCard(
            "Kritik", "0", "error", icon=ICONS.ERROR, icon_color="#f97316"
        )
        # Stok Yok: Kırmızı
        self.stat_cards["out_of_stock"] = MiniStatCard(
            "Stok Yok", "0", "error", icon=ICONS.DANGER, icon_color="#ef4444"
        )

        for card in self.stat_cards.values():
            stats_container.add_card(card)
        stats_container.add_stretch()

        # Stats ve Arama kutusu için container layout
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        top_bar_layout.setSpacing(12)

        # Stats container esnek olsun
        top_bar_layout.addWidget(stats_container, 1)

        # Arama kutusu sabit kalsın sağda
        top_bar_layout.addWidget(self.search_input, 0)

        layout.addLayout(top_bar_layout)

        # Tablo
        columns = [
            ColumnConfig("code", "Kod", width=100),
            ColumnConfig("name", "Stok Adı", width=280, stretch=True),
            ColumnConfig("type", "Tür", width=100),
            ColumnConfig("category", "Kategori", width=120),
            ColumnConfig("unit", "Birim", width=70),
            ColumnConfig("quantity", "Miktar", width=100),
            ColumnConfig("min_stock", "Min. Stok", width=90),
            ColumnConfig("purchase_price", "Alış Fiyatı", width=110),
            ColumnConfig("sale_price", "Satış Fiyatı", width=110),
            ColumnConfig("status", "Durum", width=100),
        ]

        self.table = EnhancedTableWidget(
            table_id="stock_items",
            columns=columns,
            parent=self,
        )
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.table)

        # Alt bilgi ve Sayfalama
        footer_layout = QHBoxLayout()

        self.count_label = QLabel("Toplam: 0 kayıt")
        footer_layout.addWidget(self.count_label)

        footer_layout.addStretch()

        # Sayfalama kontrolleri
        self.btn_prev = QPushButton("Önceki")
        self.btn_prev.clicked.connect(self.prev_page_clicked.emit)
        self.btn_prev.setIcon(qta.icon(ICONS.BACK))
        self.btn_prev.setEnabled(False)
        footer_layout.addWidget(self.btn_prev)

        self.page_label = QLabel("Sayfa 1 / 1")
        self.page_label.setStyleSheet("font-weight: bold; margin: 0 10px;")
        footer_layout.addWidget(self.page_label)

        self.btn_next = QPushButton("Sonraki")
        self.btn_next.clicked.connect(self.next_page_clicked.emit)
        self.btn_next.setIcon(qta.icon(ICONS.FORWARD))
        self.btn_next.setEnabled(False)
        footer_layout.addWidget(self.btn_next)

        footer_layout.addStretch()

        self.value_label = QLabel("Toplam Değer: ₺0,00")
        footer_layout.addWidget(self.value_label)

        layout.addLayout(footer_layout)

        # Arama debounce timer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._do_search)

    def _connect_signals(self):
        self.header.refresh_clicked.connect(self.refresh_requested.emit)
        self.header.add_clicked.connect(self.add_clicked.emit)
        self.header.search_changed.connect(self._on_search_changed)
        self.table.row_double_clicked.connect(self.edit_clicked.emit)

    def load_data(self, items: list):
        """Tabloyu verilerle doldur"""
        self.items_data = items
        self.table.setRowCount(len(items))
        visible_cols = self.table.get_visible_columns()

        for row, item in enumerate(items):
            self._populate_row(row, item, visible_cols)

    def update_stats(self, stats: dict):
        """İstatistik kartlarını güncelle"""
        self.stat_cards["total"].update_value(str(stats["total"]))
        self.stat_cards["normal"].update_value(str(stats["normal"]))
        self.stat_cards["low"].update_value(str(stats["low"]))
        self.stat_cards["critical"].update_value(str(stats["critical"]))
        self.stat_cards["out_of_stock"].update_value(str(stats.get("out_of_stock", 0)))

        self.value_label.setText(f"Toplam Değer: ₺{stats['total_value']:,.2f}")

    def update_pagination(
        self, current_page: int, total_pages: int, total_records: int
    ):
        """Sayfalama bilgilerini güncelle"""
        self.btn_prev.setEnabled(current_page > 1)
        self.btn_next.setEnabled(current_page < total_pages)
        self.page_label.setText(f"Sayfa {current_page} / {total_pages}")
        self.count_label.setText(f"Toplam: {total_records} kayıt")

    def _populate_row(self, row: int, item, visible_cols: list):
        for col_idx, col_key in enumerate(visible_cols):
            if col_key == "code":
                cell = QTableWidgetItem(item.code)
                cell.setData(Qt.ItemDataRole.UserRole, item.id)
                cell.setForeground(QColor("#818cf8"))
                self.table.setItem(row, col_idx, cell)

            elif col_key == "name":
                self.table.setItem(row, col_idx, QTableWidgetItem(item.name))

            elif col_key == "type":
                type_name = self.TYPE_NAMES.get(item.item_type, "Diğer")
                cell = QTableWidgetItem(type_name)

                # İkon ekle
                icon_name = self.TYPE_ICONS.get(item.item_type, ICONS.TYPE_OTHER)
                cell.setIcon(qta.icon(icon_name, color="#475569"))

                self.table.setItem(row, col_idx, cell)

            elif col_key == "category":
                cat_text = item.category.name if item.category else "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(cat_text))

            elif col_key == "unit":
                unit_text = item.unit.code if item.unit else "-"
                self.table.setItem(row, col_idx, QTableWidgetItem(unit_text))

            elif col_key == "quantity":
                total_stock = item.total_stock or Decimal(0)
                cell = QTableWidgetItem(f"{total_stock:,.2f}")
                cell.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.table.setItem(row, col_idx, cell)

            elif col_key == "min_stock":
                min_stock = item.min_stock or Decimal(0)
                cell = QTableWidgetItem(f"{min_stock:,.2f}")
                cell.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.table.setItem(row, col_idx, cell)

            elif col_key == "purchase_price":
                price = item.purchase_price or Decimal(0)
                cell = QTableWidgetItem(f"₺{price:,.2f}")
                cell.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.table.setItem(row, col_idx, cell)

            elif col_key == "sale_price":
                price = item.sale_price or Decimal(0)
                cell = QTableWidgetItem(f"₺{price:,.2f}")
                cell.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.table.setItem(row, col_idx, cell)

            elif col_key == "status":
                cell = QTableWidgetItem()
                t = get_theme()

                if not item.is_active:
                    cell.setText("Pasif")
                    cell.setIcon(
                        qta.icon(ICONS.STATUS_ICONS["passive"], color=t.text_muted)
                    )
                    cell.setForeground(QColor(t.text_muted))
                else:
                    status = item.stock_status
                    if status == "out_of_stock":
                        # Kırmızı
                        color = "#ef4444"
                        cell.setText("Stok Yok")
                        cell.setIcon(
                            qta.icon(ICONS.STATUS_ICONS["out_of_stock"], color=color)
                        )
                        cell.setForeground(QColor(color))
                    elif status == "critical":
                        # Turuncu
                        color = "#f97316"
                        cell.setText("Kritik")
                        cell.setIcon(
                            qta.icon(ICONS.STATUS_ICONS["critical"], color=color)
                        )
                        cell.setForeground(QColor(color))
                    elif status == "low":
                        # Sarı
                        color = "#eab308"
                        cell.setText("Düşük")
                        cell.setIcon(qta.icon(ICONS.STATUS_ICONS["low"], color=color))
                        cell.setForeground(QColor(color))
                    else:
                        # Yeşil
                        color = "#22c55e"
                        cell.setText("Normal")
                        cell.setIcon(
                            qta.icon(ICONS.STATUS_ICONS["normal"], color=color)
                        )
                        cell.setForeground(QColor(color))
                self.table.setItem(row, col_idx, cell)

    def _on_search_changed(self, text: str):
        self.search_timer.stop()
        self.search_timer.start(300)

    def _do_search(self):
        self.refresh_requested.emit()

    def get_filters(self) -> dict:
        return {
            "keyword": (self.search_input.text().strip() if self.search_input else ""),
            "is_active": self.active_combo.currentData(),
            "item_type": self.type_combo.currentData(),
            "stock_status": self.status_combo.currentData(),
        }

    def _get_export_data(self):
        return ExportManager.extract_data_from_table(self.table)

    def _print_labels(self):
        data = self._get_export_data()
        LabelManager.print_product_labels(self, data)

    def _show_context_menu(self, position):
        row = self.table.rowAt(position.y())
        if row < 0:
            return

        item_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        menu = QMenu(self)
        view_action = QAction("Görüntüle", self)
        view_action.setIcon(qta.icon(ICONS.EYE, color="#475569"))
        view_action.triggered.connect(lambda: self.item_selected.emit(item_id))
        menu.addAction(view_action)

        edit_action = QAction("Düzenle", self)
        edit_action.setIcon(qta.icon(ICONS.EDIT, color="#3498db"))
        edit_action.triggered.connect(lambda: self.edit_clicked.emit(item_id))
        menu.addAction(edit_action)

        duplicate_action = QAction("Kopyala ve Oluştur", self)
        duplicate_action.setIcon(qta.icon(ICONS.COPY, color="#8b5cf6"))
        duplicate_action.triggered.connect(lambda: self.duplicate_clicked.emit(item_id))
        menu.addAction(duplicate_action)

        menu.addSeparator()

        movement_action = QAction("Stok Hareketi", self)
        movement_action.setIcon(qta.icon(ICONS.MOVEMENT, color="#64748b"))
        menu.addAction(movement_action)

        history_action = QAction("Hareket Geçmişi", self)
        history_action.setIcon(qta.icon(ICONS.REFRESH, color="#64748b"))
        menu.addAction(history_action)

        menu.addSeparator()

        delete_action = QAction("Sil", self)
        delete_action.setIcon(qta.icon(ICONS.DELETE, color="#ef4444"))
        delete_action.triggered.connect(lambda: self._confirm_delete(item_id))
        menu.addAction(delete_action)

        menu.exec(self.table.viewport().mapToGlobal(position))

    def _confirm_delete(self, item_id: int):
        reply = QMessageBox.question(
            self,
            "Silme Onayı",
            "Bu stok kartını silmek istediğinize emin misiniz?\n\nBu işlem geri alınamaz.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_clicked.emit(item_id)
