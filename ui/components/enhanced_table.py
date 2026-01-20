"""
Akıllı İş ERP - Gelişmiş Tablo Bileşeni
Sütun yönetimi, kalıcı ayarlar ve gelişmiş özellikler sunar.
"""

from PyQt6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QMenu,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings
from PyQt6.QtGui import QAction
from typing import List, Optional


class ColumnConfig:
    """Sütun yapılandırma sınıfı"""

    def __init__(
        self,
        key: str,
        title: str,
        width: int = 100,
        resizable: bool = True,
        movable: bool = True,
        hideable: bool = True,
        visible: bool = True,
        stretch: bool = False,
    ):
        self.key = key
        self.title = title
        self.default_width = width
        self.width = width
        self.resizable = resizable
        self.movable = movable
        self.hideable = hideable
        self.visible = visible
        self.stretch = stretch
        self.order = 0  # Sıra numarası


class EnhancedTableWidget(QTableWidget):
    """
    Gelişmiş tablo bileşeni.

    Özellikler:
    - Sütun genişliği kullanıcı tarafından ayarlanabilir
    - Sütunlar sürükle-bırak ile yer değiştirebilir
    - Ayarlar QSettings ile kalıcı olarak saklanır
    - Sütun gizleme/gösterme (context menu)
    - Varsayılan ayarlara dönüş

    Ayar Saklama:
    - Sistem geneli varsayılan ayarlar
    - Kullanıcı bazlı özel ayarlar (varsa)
    """

    # Sinyaller
    row_double_clicked = pyqtSignal(int)  # Satır ID'si
    row_selected = pyqtSignal(int)  # Satır ID'si
    settings_changed = pyqtSignal()  # Ayarlar değiştiğinde

    def __init__(
        self,
        table_id: str,
        columns: List[ColumnConfig],
        user_id: Optional[int] = None,
        parent=None,
    ):
        super().__init__(parent)

        self.table_id = table_id
        self.user_id = user_id
        self.columns = {col.key: col for col in columns}
        self.column_order = [col.key for col in columns]

        # QSS class ata
        self.setProperty("class", "enhanced-table")

        self._setup_table()
        self._load_settings()
        self._apply_column_settings()
        self._connect_signals()

    def _setup_table(self):
        """Tablo temel yapılandırması"""
        # Görünüm ayarları
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setSortingEnabled(True)

        # Header yapılandırması
        header = self.horizontalHeader()
        header.setSectionsMovable(True)
        header.setStretchLastSection(False)
        header.sectionMoved.connect(self._on_section_moved)
        header.sectionResized.connect(self._on_section_resized)
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self._show_column_menu)

        # Sütunları oluştur
        visible_columns = [
            key for key in self.column_order if self.columns[key].visible
        ]
        self.setColumnCount(len(visible_columns))
        self.setHorizontalHeaderLabels(
            [self.columns[key].title for key in visible_columns]
        )

    def _connect_signals(self):
        """İç sinyalleri bağla"""
        self.doubleClicked.connect(self._on_double_click)
        self.itemSelectionChanged.connect(self._on_selection_changed)

    def _get_settings_key(self, suffix: str) -> str:
        """Ayar anahtarı oluştur"""
        if self.user_id:
            return f"table/{self.table_id}/user_{self.user_id}/{suffix}"
        return f"table/{self.table_id}/system/{suffix}"

    def _load_settings(self):
        """QSettings'ten ayarları yükle"""
        settings = QSettings()

        # Önce kullanıcı ayarlarını dene, yoksa sistem ayarlarını kullan
        order_key = self._get_settings_key("column_order")
        widths_key = self._get_settings_key("column_widths")
        visibility_key = self._get_settings_key("column_visibility")

        # Sütun sırası
        saved_order = settings.value(order_key)
        if saved_order:
            # Sadece mevcut sütunları al, yenileri sona ekle
            valid_order = [k for k in saved_order if k in self.columns]
            new_columns = [k for k in self.column_order if k not in valid_order]
            self.column_order = valid_order + new_columns

        # Sütun genişlikleri
        saved_widths = settings.value(widths_key)
        if saved_widths and isinstance(saved_widths, dict):
            for key, width in saved_widths.items():
                if key in self.columns:
                    self.columns[key].width = int(width)

        # Sütun görünürlüğü
        saved_visibility = settings.value(visibility_key)
        if saved_visibility and isinstance(saved_visibility, dict):
            for key, visible in saved_visibility.items():
                if key in self.columns:
                    self.columns[key].visible = visible

    def _save_settings(self):
        """Ayarları QSettings'e kaydet"""
        settings = QSettings()

        # Sütun sırası
        settings.setValue(self._get_settings_key("column_order"), self.column_order)

        # Sütun genişlikleri
        widths = {key: col.width for key, col in self.columns.items()}
        settings.setValue(self._get_settings_key("column_widths"), widths)

        # Sütun görünürlüğü
        visibility = {key: col.visible for key, col in self.columns.items()}
        settings.setValue(self._get_settings_key("column_visibility"), visibility)

        settings.sync()
        self.settings_changed.emit()

    def _apply_column_settings(self):
        """Sütun ayarlarını tabloya uygula"""
        header = self.horizontalHeader()
        visible_columns = [
            key for key in self.column_order if self.columns[key].visible
        ]

        for visual_idx, key in enumerate(visible_columns):
            col = self.columns[key]
            logical_idx = visual_idx  # Görsel index = mantıksal index

            # Genişlik
            self.setColumnWidth(logical_idx, col.width)

            # Stretch
            if col.stretch:
                header.setSectionResizeMode(logical_idx, QHeaderView.ResizeMode.Stretch)
            elif col.resizable:
                header.setSectionResizeMode(
                    logical_idx, QHeaderView.ResizeMode.Interactive
                )
            else:
                header.setSectionResizeMode(logical_idx, QHeaderView.ResizeMode.Fixed)

    def _on_section_moved(self, logical_idx: int, old_visual: int, new_visual: int):
        """Sütun taşındığında"""
        visible_columns = [
            key for key in self.column_order if self.columns[key].visible
        ]

        if old_visual < len(visible_columns) and new_visual < len(visible_columns):
            # Sırayı güncelle
            moved_key = visible_columns[old_visual]
            visible_columns.remove(moved_key)
            visible_columns.insert(new_visual, moved_key)

            # Tüm sırayı güncelle (gizli sütunları koruyarak)
            new_order = []
            visible_idx = 0
            for key in self.column_order:
                if self.columns[key].visible:
                    if visible_idx < len(visible_columns):
                        new_order.append(visible_columns[visible_idx])
                    visible_idx += 1
                else:
                    new_order.append(key)

            self.column_order = new_order
            self._save_settings()

    def _on_section_resized(self, logical_idx: int, old_size: int, new_size: int):
        """Sütun boyutu değiştiğinde"""
        visible_columns = [
            key for key in self.column_order if self.columns[key].visible
        ]

        if logical_idx < len(visible_columns):
            key = visible_columns[logical_idx]
            self.columns[key].width = new_size
            self._save_settings()

    def _show_column_menu(self, position):
        """Sütun gizle/göster context menüsü"""
        menu = QMenu(self)
        menu.setProperty("class", "column-menu")

        # Başlık
        title_action = QAction("📋 Sütun Ayarları", menu)
        title_action.setEnabled(False)
        menu.addAction(title_action)
        menu.addSeparator()

        # Sütun seçenekleri
        for key in self.column_order:
            col = self.columns[key]
            if not col.hideable:
                continue

            action = QAction(col.title, menu)
            action.setCheckable(True)
            action.setChecked(col.visible)
            action.triggered.connect(
                lambda checked, k=key: self._toggle_column_visibility(k, checked)
            )
            menu.addAction(action)

        menu.addSeparator()

        # Varsayılana dön
        reset_action = QAction("🔄 Varsayılana Dön", menu)
        reset_action.triggered.connect(self.reset_to_defaults)
        menu.addAction(reset_action)

        menu.exec(self.horizontalHeader().mapToGlobal(position))

    def _toggle_column_visibility(self, key: str, visible: bool):
        """Sütun görünürlüğünü değiştir"""
        if key in self.columns:
            self.columns[key].visible = visible
            self._rebuild_columns()
            self._save_settings()

    def _rebuild_columns(self):
        """Sütunları yeniden oluştur"""
        # Mevcut verileri kaydet
        row_count = self.rowCount()
        data = []
        for row in range(row_count):
            row_data = {}
            visible_cols = [k for k in self.column_order if self.columns[k].visible]
            for col_idx, key in enumerate(visible_cols):
                item = self.item(row, col_idx)
                if item:
                    row_data[key] = {
                        "text": item.text(),
                        "data": item.data(Qt.ItemDataRole.UserRole),
                    }
            data.append(row_data)

        # Sütunları yeniden oluştur
        visible_columns = [
            key for key in self.column_order if self.columns[key].visible
        ]
        self.setColumnCount(len(visible_columns))
        self.setHorizontalHeaderLabels(
            [self.columns[key].title for key in visible_columns]
        )
        self._apply_column_settings()

        # Verileri geri yükle
        self.setRowCount(row_count)
        for row, row_data in enumerate(data):
            for col_idx, key in enumerate(visible_columns):
                if key in row_data:
                    item = QTableWidgetItem(row_data[key]["text"])
                    if row_data[key]["data"] is not None:
                        item.setData(Qt.ItemDataRole.UserRole, row_data[key]["data"])
                    self.setItem(row, col_idx, item)

    def reset_to_defaults(self):
        """Varsayılan ayarlara dön"""
        settings = QSettings()

        # Ayarları sil
        settings.remove(self._get_settings_key("column_order"))
        settings.remove(self._get_settings_key("column_widths"))
        settings.remove(self._get_settings_key("column_visibility"))
        settings.sync()

        # Varsayılan değerlere dön
        for col in self.columns.values():
            col.width = col.default_width
            col.visible = True

        self.column_order = list(self.columns.keys())
        self._rebuild_columns()
        self.settings_changed.emit()

    def _on_double_click(self, index):
        """Çift tıklama olayı"""
        row = index.row()
        item = self.item(row, 0)
        if item:
            row_id = item.data(Qt.ItemDataRole.UserRole)
            if row_id:
                self.row_double_clicked.emit(row_id)

    def _on_selection_changed(self):
        """Seçim değiştiğinde"""
        selected = self.selectedItems()
        if selected:
            row = selected[0].row()
            item = self.item(row, 0)
            if item:
                row_id = item.data(Qt.ItemDataRole.UserRole)
                if row_id:
                    self.row_selected.emit(row_id)

    def get_selected_id(self) -> Optional[int]:
        """Seçili satırın ID'sini döndür"""
        selected = self.selectedItems()
        if selected:
            row = selected[0].row()
            item = self.item(row, 0)
            if item:
                return item.data(Qt.ItemDataRole.UserRole)
        return None

    def get_visible_columns(self) -> List[str]:
        """Görünür sütun key'lerini döndür"""
        return [key for key in self.column_order if self.columns[key].visible]

    def set_user_id(self, user_id: int):
        """Kullanıcı ID'sini ayarla ve ayarları yeniden yükle"""
        self.user_id = user_id
        self._load_settings()
        self._rebuild_columns()
