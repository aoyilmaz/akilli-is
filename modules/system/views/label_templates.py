"""
Etiket Şablonları Yönetim Sayfası

Yeni LabelDesignerWidget entegrasyonu ile profesyonel etiket tasarımı.
"""

import logging
import json
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QFrame,
    QComboBox,
    QSpinBox,
    QTreeWidget,
    QTreeWidgetItem,
    QLabel,
    QGroupBox,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTabWidget,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from database import SessionLocal
from database.models.common import LabelTemplate
from core.label_manager import LabelManager
from config.styles import get_button_style, BTN_HEIGHT_NORMAL, ICONS
from .label_editor_utils import TEMPLATE_VARIABLES, get_dummy_data

# Yeni Label Designer
from .label_designer import (
    LabelDesignerWidget,
    LabelSize,
    LabelScene,
    RenderContext,
    PDFRenderer,
    ZPLRenderer,
)

logger = logging.getLogger(__name__)


class LabelTemplatesPage(QWidget):
    """
    Etiket Şablonları Yönetim Sayfası.

    Yeni profesyonel LabelDesignerWidget ile entegre edilmiş.
    """

    def __init__(self):
        super().__init__()
        self.session = SessionLocal()
        self.current_template: Optional[LabelTemplate] = None

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """UI'ı oluşturur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Ana Splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- SOL PANEL (Şablonlar & Veri Kaynakları) ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)

        self.left_tabs = QTabWidget()

        # Tab 1: Şablon Listesi
        self.template_list_widget = QWidget()
        tmpl_layout = QVBoxLayout(self.template_list_widget)
        tmpl_layout.setContentsMargins(5, 5, 5, 5)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Kod", "Ad"])
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        tmpl_layout.addWidget(self.table)

        # Butonlar
        btn_layout = QHBoxLayout()

        new_btn = QPushButton(f"{ICONS.get('add', '➕')} Yeni")
        new_btn.setStyleSheet(get_button_style("primary"))
        new_btn.clicked.connect(self._new_template)
        btn_layout.addWidget(new_btn)

        delete_btn = QPushButton(f"{ICONS.get('delete', '🗑️')} Sil")
        delete_btn.setStyleSheet(get_button_style("danger"))
        delete_btn.clicked.connect(self._delete_template)
        btn_layout.addWidget(delete_btn)

        tmpl_layout.addLayout(btn_layout)

        self.left_tabs.addTab(self.template_list_widget, "Şablonlar")

        # Tab 2: Veri Kaynakları (Tree)
        self.data_tree = QTreeWidget()
        self.data_tree.setHeaderLabel("Veri Alanları")
        self.data_tree.itemDoubleClicked.connect(self._insert_from_tree)
        self.left_tabs.addTab(self.data_tree, "Veri Kaynakları")

        left_layout.addWidget(self.left_tabs)
        self.main_splitter.addWidget(left_widget)

        # --- ORTA PANEL (Label Designer Widget) ---
        self.designer = LabelDesignerWidget(LabelSize(100, 50))
        self.designer.template_changed.connect(self._on_designer_changed)
        self.main_splitter.addWidget(self.designer)

        # --- SAĞ PANEL (Belge Ayarları) ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)

        # Belge Ayarları
        doc_group = QGroupBox("Belge Ayarları")
        doc_layout = QFormLayout(doc_group)

        self.doc_code = QLineEdit()
        self.doc_name = QLineEdit()
        self.doc_type = QComboBox()
        self.doc_type.addItems(["product", "work_order", "shipping", "location"])
        self.doc_type.currentTextChanged.connect(self._on_type_changed)

        self.doc_w = QSpinBox()
        self.doc_w.setRange(10, 500)
        self.doc_w.setValue(100)
        self.doc_w.setSuffix(" mm")
        self.doc_w.valueChanged.connect(self._on_doc_size_changed)

        self.doc_h = QSpinBox()
        self.doc_h.setRange(10, 500)
        self.doc_h.setValue(50)
        self.doc_h.setSuffix(" mm")
        self.doc_h.valueChanged.connect(self._on_doc_size_changed)

        doc_layout.addRow("Kod:", self.doc_code)
        doc_layout.addRow("Ad:", self.doc_name)
        doc_layout.addRow("Tür:", self.doc_type)
        doc_layout.addRow("Genişlik:", self.doc_w)
        doc_layout.addRow("Yükseklik:", self.doc_h)

        right_layout.addWidget(doc_group)

        # İşlem Butonları
        action_group = QGroupBox("İşlemler")
        action_layout = QVBoxLayout(action_group)

        save_btn = QPushButton(f"{ICONS.get('save', '💾')} Kaydet")
        save_btn.setStyleSheet(get_button_style("success"))
        save_btn.clicked.connect(self._save_template)
        action_layout.addWidget(save_btn)

        preview_btn = QPushButton(f"{ICONS.get('print', '🖨️')} PDF Önizleme")
        preview_btn.setStyleSheet(get_button_style("info"))
        preview_btn.clicked.connect(self._show_preview_dialog)
        action_layout.addWidget(preview_btn)

        zpl_btn = QPushButton("📄 ZPL Önizleme")
        zpl_btn.setStyleSheet(get_button_style("secondary"))
        zpl_btn.clicked.connect(self._show_zpl_preview)
        action_layout.addWidget(zpl_btn)

        right_layout.addWidget(action_group)

        # Bilgi
        info_group = QGroupBox("Bilgi")
        info_layout = QVBoxLayout(info_group)
        info_label = QLabel(
            "Veri alanlarına çift tıklayarak\n"
            "tasarıma ekleyebilirsiniz.\n\n"
            "Değişken formatı: {Alan_Adi}"
        )
        info_label.setStyleSheet("color: #666; font-size: 11px;")
        info_layout.addWidget(info_label)
        right_layout.addWidget(info_group)

        right_layout.addStretch()
        self.main_splitter.addWidget(right_widget)

        # Splitter Oranları
        self.main_splitter.setSizes([250, 900, 200])
        layout.addWidget(self.main_splitter)

    def _on_doc_size_changed(self):
        """Belge boyutu değiştiğinde"""
        w = self.doc_w.value()
        h = self.doc_h.value()
        self.designer.set_label_dimensions(w, h)

    def _on_designer_changed(self):
        """Designer değiştiğinde"""
        # Otomatik kaydetme veya değişiklik işareti eklenebilir
        pass

    # --- Veri Yönetimi ---

    def load_data(self):
        """Şablonları yükler"""
        self.table.setRowCount(0)
        templates = self.session.query(LabelTemplate).all()
        for tmpl in templates:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(tmpl.code))
            self.table.setItem(row, 1, QTableWidgetItem(tmpl.name))
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, tmpl.id)

    def _on_selection_changed(self):
        """Şablon seçimi değiştiğinde"""
        items = self.table.selectedItems()
        if not items:
            return
        row = items[0].row()
        tmpl_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self._load_template_details(tmpl_id)

    def _load_template_details(self, tmpl_id: int):
        """Şablon detaylarını yükler"""
        tmpl = self.session.query(LabelTemplate).get(tmpl_id)
        if not tmpl:
            return
        self.current_template = tmpl

        self.doc_code.setText(tmpl.code)
        self.doc_name.setText(tmpl.name)
        self.doc_type.setCurrentText(tmpl.template_type)
        self.doc_w.setValue(tmpl.width_mm or 100)
        self.doc_h.setValue(tmpl.height_mm or 50)

        # İçeriği yükle
        if tmpl.content and tmpl.content.startswith("{"):
            try:
                data = json.loads(tmpl.content)
                # v1 -> v2 migration
                if data.get("version") != "2.0":
                    data = self._migrate_v1_to_v2(data, tmpl.width_mm, tmpl.height_mm)
                self.designer.load_from_dict(data)
            except Exception as e:
                logger.error(f"Şablon yükleme hatası: {e}")
                # Boş şablon yükle
                self.designer.new_template()
        else:
            self.designer.new_template()

        self._rebuild_data_tree(tmpl.template_type)

    def _migrate_v1_to_v2(self, old_data: dict, width_mm: int, height_mm: int) -> dict:
        """
        v1 şablon formatını v2'ye dönüştürür.

        v1 format:
        {
            "items": [
                {"type": "text", "x": 50, "y": 25, "text": "...", ...}
            ]
        }

        v2 format:
        {
            "version": "2.0",
            "size": {"width_mm": 100, "height_mm": 50},
            "items": [
                {"type": "text", "geometry": {...}, "text": "...", ...}
            ]
        }
        """
        MM_TO_PX_OLD = 5  # Eski sabit

        new_data = {
            "version": "2.0",
            "size": {"width_mm": width_mm or 100, "height_mm": height_mm or 50},
            "grid": {"enabled": True, "snap": True, "size_mm": 5},
            "items": []
        }

        for old_item in old_data.get("items", []):
            item_type = old_item.get("type", "text")

            # Pozisyonu mm'e çevir
            x_mm = old_item.get("x", 0) / MM_TO_PX_OLD
            y_mm = old_item.get("y", 0) / MM_TO_PX_OLD

            if item_type == "text":
                new_item = {
                    "type": "text",
                    "geometry": {
                        "x_mm": x_mm,
                        "y_mm": y_mm,
                        "width_mm": 50,
                        "height_mm": 10,
                        "rotation": 0
                    },
                    "text": old_item.get("text", ""),
                    "style": {
                        "font_family": old_item.get("font", "Arial"),
                        "font_size": old_item.get("size", 12),
                        "bold": old_item.get("bold", False),
                        "italic": old_item.get("italic", False),
                        "underline": False,
                        "color": "#000000",
                        "alignment": "left"
                    }
                }
                # Data key varsa ekle
                text = old_item.get("text", "")
                if "{{" in text or "{" in text:
                    new_item["data_key"] = text

            elif item_type == "barcode":
                new_item = {
                    "type": "barcode",
                    "geometry": {
                        "x_mm": x_mm,
                        "y_mm": y_mm,
                        "width_mm": 60,
                        "height_mm": 15,
                        "rotation": 0
                    },
                    "barcode_type": "code128",
                    "barcode_data": old_item.get("key", "123456789"),
                    "show_text": True
                }
                if old_item.get("key"):
                    new_item["data_key"] = old_item.get("key")

            else:
                continue

            new_data["items"].append(new_item)

        return new_data

    def _new_template(self):
        """Yeni şablon oluşturur"""
        self.current_template = None
        self.doc_code.clear()
        self.doc_name.clear()
        self.doc_type.setCurrentIndex(0)
        self.doc_w.setValue(100)
        self.doc_h.setValue(50)
        self.designer.new_template()
        self.designer.set_label_dimensions(100, 50)
        self._rebuild_data_tree("product")

    def _delete_template(self):
        """Seçili şablonu siler"""
        items = self.table.selectedItems()
        if not items:
            QMessageBox.warning(self, "Uyarı", "Silmek için bir şablon seçin.")
            return

        reply = QMessageBox.question(
            self,
            "Onay",
            "Bu şablonu silmek istediğinizden emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        row = items[0].row()
        tmpl_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        try:
            tmpl = self.session.query(LabelTemplate).get(tmpl_id)
            if tmpl:
                self.session.delete(tmpl)
                self.session.commit()
                self.load_data()
                self._new_template()
                QMessageBox.information(self, "Başarılı", "Şablon silindi.")
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")

    def _on_type_changed(self, text: str):
        """Şablon türü değiştiğinde"""
        self._rebuild_data_tree(text)

    def _rebuild_data_tree(self, tmpl_type: str):
        """Veri alanları ağacını yeniden oluşturur"""
        self.data_tree.clear()
        variables = TEMPLATE_VARIABLES.get(tmpl_type, [])

        root = QTreeWidgetItem(self.data_tree)
        root.setText(0, "Veritabanı Alanları")
        root.setExpanded(True)

        for var in variables:
            item = QTreeWidgetItem(root)
            item.setText(0, f"{var['label']} ({var['key']})")
            item.setData(0, Qt.ItemDataRole.UserRole, var)

        # Sistem değişkenleri
        sys_root = QTreeWidgetItem(self.data_tree)
        sys_root.setText(0, "Sistem Değişkenleri")
        sys_root.setExpanded(True)

        sys_vars = [
            {"key": "Tarih", "label": "Tarih", "type": "text"},
            {"key": "Saat", "label": "Saat", "type": "text"},
            {"key": "Kullanici", "label": "Kullanıcı", "type": "text"},
        ]
        for var in sys_vars:
            item = QTreeWidgetItem(sys_root)
            item.setText(0, f"{var['label']} ({var['key']})")
            item.setData(0, Qt.ItemDataRole.UserRole, var)

    def _insert_from_tree(self, item: QTreeWidgetItem, col: int):
        """Veri alanını tasarıma ekler"""
        var = item.data(0, Qt.ItemDataRole.UserRole)
        if not var:
            return

        key = var["key"]
        vtype = var.get("type", "text")

        if vtype == "barcode":
            barcode = self.designer.scene.add_barcode(10, 10, 60, 15, f"{{{key}}}")
            barcode.data_key = f"{{{key}}}"
            barcode.setSelected(True)
        elif vtype == "qrcode":
            qr = self.designer.scene.add_qrcode(10, 10, 20, f"{{{key}}}")
            qr.data_key = f"{{{key}}}"
            qr.setSelected(True)
        else:
            text = self.designer.scene.add_text(10, 10, 50, 10, f"{{{key}}}")
            text.data_key = f"{{{key}}}"
            text.setSelected(True)

    def _save_template(self):
        """Şablonu kaydeder"""
        if not self.doc_code.text() or not self.doc_name.text():
            QMessageBox.warning(self, "Hata", "Kod ve Ad zorunludur.")
            return

        data_dict = self.designer.get_template_dict()
        content = json.dumps(data_dict, ensure_ascii=False, indent=2)

        try:
            if not self.current_template:
                self.current_template = LabelTemplate()
                self.session.add(self.current_template)

            self.current_template.code = self.doc_code.text()
            self.current_template.name = self.doc_name.text()
            self.current_template.template_type = self.doc_type.currentText()
            self.current_template.width_mm = self.doc_w.value()
            self.current_template.height_mm = self.doc_h.value()
            self.current_template.content = content

            self.session.commit()
            QMessageBox.information(self, "Başarılı", "Şablon kaydedildi.")
            self.load_data()
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {e}")

    def _show_preview_dialog(self):
        """PDF önizlemesi gösterir"""
        import tempfile
        import os
        import sys

        # Dummy veri
        dummy_data = get_dummy_data(self.doc_type.currentText())
        context = RenderContext(data=dummy_data)

        # PDF oluştur
        renderer = PDFRenderer(dpi=300)
        label_size = LabelSize(self.doc_w.value(), self.doc_h.value())

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            file_name = tmp.name

        try:
            output = renderer.save_to_file(
                self.designer.scene.items_list,
                label_size,
                file_name,
                context
            )

            if output.success:
                # Aç
                if sys.platform == "darwin":
                    os.system(f'open "{file_name}"')
                elif sys.platform == "win32":
                    os.startfile(file_name)
                else:
                    os.system(f'xdg-open "{file_name}"')
            else:
                QMessageBox.critical(self, "Hata", f"PDF oluşturma hatası: {output.error}")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Önizleme hatası: {e}")

    def _show_zpl_preview(self):
        """ZPL önizlemesi gösterir"""
        # Dummy veri
        dummy_data = get_dummy_data(self.doc_type.currentText())
        context = RenderContext(data=dummy_data)

        # ZPL oluştur
        renderer = ZPLRenderer(dpi=203)
        label_size = LabelSize(self.doc_w.value(), self.doc_h.value())

        output = renderer.render(
            self.designer.scene.items_list,
            label_size,
            context
        )

        if output.success:
            # Dialog'da göster
            from PyQt6.QtWidgets import QDialog, QTextEdit, QDialogButtonBox

            dialog = QDialog(self)
            dialog.setWindowTitle("ZPL Önizleme")
            dialog.resize(600, 400)

            layout = QVBoxLayout(dialog)

            text_edit = QTextEdit()
            text_edit.setPlainText(output.data)
            text_edit.setReadOnly(True)
            text_edit.setFont(QFont("Courier New", 10))
            layout.addWidget(text_edit)

            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
            buttons.accepted.connect(dialog.accept)
            layout.addWidget(buttons)

            dialog.exec()
        else:
            QMessageBox.critical(self, "Hata", f"ZPL oluşturma hatası: {output.error}")

    def closeEvent(self, event):
        """Pencere kapatılırken"""
        self.session.close()
        super().closeEvent(event)
