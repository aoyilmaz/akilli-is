"""
DesignerToolbar - Etiket tasarımcı araç çubuğu
"""

from typing import Optional

from PyQt6.QtWidgets import (
    QToolBar, QWidget, QToolButton, QMenu, QComboBox,
    QSpinBox, QLabel, QSizePolicy, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QAction


class DesignerToolbar(QToolBar):
    """
    Etiket tasarımcı araç çubuğu.

    Araçlar:
    - Seçim aracı
    - Metin ekle
    - Barkod ekle
    - QR kod ekle
    - Görüntü ekle
    - Şekil ekle (dikdörtgen, çizgi, elips)
    - Zoom kontrolleri
    - Grid toggle
    """

    # Sinyaller
    tool_selected = pyqtSignal(str)  # Araç adı
    add_text_clicked = pyqtSignal()
    add_barcode_clicked = pyqtSignal()
    add_qrcode_clicked = pyqtSignal()
    add_image_clicked = pyqtSignal()
    add_rectangle_clicked = pyqtSignal()
    add_line_clicked = pyqtSignal()
    add_ellipse_clicked = pyqtSignal()
    zoom_in_clicked = pyqtSignal()
    zoom_out_clicked = pyqtSignal()
    zoom_fit_clicked = pyqtSignal()
    zoom_reset_clicked = pyqtSignal()
    grid_toggled = pyqtSignal(bool)
    snap_toggled = pyqtSignal(bool)
    delete_clicked = pyqtSignal()
    duplicate_clicked = pyqtSignal()
    undo_clicked = pyqtSignal()
    redo_clicked = pyqtSignal()
    save_clicked = pyqtSignal()
    export_pdf_clicked = pyqtSignal()
    export_zpl_clicked = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__("Tasarım Araçları", parent)
        self._current_tool = "select"
        self._setup_toolbar()

    def _setup_toolbar(self):
        """Araç çubuğunu yapılandırır"""
        self.setMovable(False)
        self.setFloatable(False)
        self.setIconSize(self.iconSize())

        # === Dosya İşlemleri ===
        self._add_separator_label("Dosya")

        # Kaydet
        self.save_action = QAction("Kaydet", self)
        self.save_action.setToolTip("Şablonu kaydet (Ctrl+S)")
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self.save_clicked.emit)
        self.addAction(self.save_action)

        # Export menü
        export_btn = QToolButton(self)
        export_btn.setText("Dışa Aktar ▼")
        export_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        export_menu = QMenu(export_btn)

        pdf_action = export_menu.addAction("PDF olarak dışa aktar...")
        pdf_action.triggered.connect(self.export_pdf_clicked.emit)

        zpl_action = export_menu.addAction("ZPL olarak dışa aktar...")
        zpl_action.triggered.connect(self.export_zpl_clicked.emit)

        export_btn.setMenu(export_menu)
        self.addWidget(export_btn)

        self.addSeparator()

        # === Düzenleme ===
        self._add_separator_label("Düzenle")

        # Undo/Redo
        self.undo_action = QAction("Geri Al", self)
        self.undo_action.setToolTip("Geri al (Ctrl+Z)")
        self.undo_action.setShortcut("Ctrl+Z")
        self.undo_action.triggered.connect(self.undo_clicked.emit)
        self.addAction(self.undo_action)

        self.redo_action = QAction("Yinele", self)
        self.redo_action.setToolTip("Yinele (Ctrl+Y)")
        self.redo_action.setShortcut("Ctrl+Y")
        self.redo_action.triggered.connect(self.redo_clicked.emit)
        self.addAction(self.redo_action)

        self.addSeparator()

        # Sil / Çoğalt
        self.delete_action = QAction("Sil", self)
        self.delete_action.setToolTip("Seçili elemanları sil (Del)")
        self.delete_action.setShortcut("Delete")
        self.delete_action.triggered.connect(self.delete_clicked.emit)
        self.addAction(self.delete_action)

        self.duplicate_action = QAction("Çoğalt", self)
        self.duplicate_action.setToolTip("Seçili elemanları çoğalt (Ctrl+D)")
        self.duplicate_action.setShortcut("Ctrl+D")
        self.duplicate_action.triggered.connect(self.duplicate_clicked.emit)
        self.addAction(self.duplicate_action)

        self.addSeparator()

        # === Eleman Ekleme ===
        self._add_separator_label("Ekle")

        # Metin
        self.add_text_action = QAction("Metin", self)
        self.add_text_action.setToolTip("Metin ekle")
        self.add_text_action.triggered.connect(self.add_text_clicked.emit)
        self.addAction(self.add_text_action)

        # Barkod
        self.add_barcode_action = QAction("Barkod", self)
        self.add_barcode_action.setToolTip("Barkod ekle")
        self.add_barcode_action.triggered.connect(self.add_barcode_clicked.emit)
        self.addAction(self.add_barcode_action)

        # QR Kod
        self.add_qrcode_action = QAction("QR Kod", self)
        self.add_qrcode_action.setToolTip("QR kod ekle")
        self.add_qrcode_action.triggered.connect(self.add_qrcode_clicked.emit)
        self.addAction(self.add_qrcode_action)

        # Görüntü
        self.add_image_action = QAction("Görüntü", self)
        self.add_image_action.setToolTip("Görüntü ekle")
        self.add_image_action.triggered.connect(self.add_image_clicked.emit)
        self.addAction(self.add_image_action)

        # Şekiller menü
        shape_btn = QToolButton(self)
        shape_btn.setText("Şekil ▼")
        shape_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        shape_menu = QMenu(shape_btn)

        rect_action = shape_menu.addAction("Dikdörtgen")
        rect_action.triggered.connect(self.add_rectangle_clicked.emit)

        line_action = shape_menu.addAction("Çizgi")
        line_action.triggered.connect(self.add_line_clicked.emit)

        ellipse_action = shape_menu.addAction("Elips")
        ellipse_action.triggered.connect(self.add_ellipse_clicked.emit)

        shape_btn.setMenu(shape_menu)
        self.addWidget(shape_btn)

        self.addSeparator()

        # === Görünüm ===
        self._add_separator_label("Görünüm")

        # Grid toggle
        self.grid_action = QAction("Grid", self)
        self.grid_action.setCheckable(True)
        self.grid_action.setChecked(True)
        self.grid_action.setToolTip("Grid'i göster/gizle")
        self.grid_action.toggled.connect(self.grid_toggled.emit)
        self.addAction(self.grid_action)

        # Snap toggle
        self.snap_action = QAction("Snap", self)
        self.snap_action.setCheckable(True)
        self.snap_action.setChecked(True)
        self.snap_action.setToolTip("Grid'e yapış")
        self.snap_action.toggled.connect(self.snap_toggled.emit)
        self.addAction(self.snap_action)

        self.addSeparator()

        # Zoom kontrolleri
        self.zoom_out_action = QAction("-", self)
        self.zoom_out_action.setToolTip("Uzaklaştır")
        self.zoom_out_action.triggered.connect(self.zoom_out_clicked.emit)
        self.addAction(self.zoom_out_action)

        # Zoom label
        self.zoom_label = QLabel("100%")
        self.zoom_label.setMinimumWidth(50)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.addWidget(self.zoom_label)

        self.zoom_in_action = QAction("+", self)
        self.zoom_in_action.setToolTip("Yakınlaştır")
        self.zoom_in_action.triggered.connect(self.zoom_in_clicked.emit)
        self.addAction(self.zoom_in_action)

        self.zoom_fit_action = QAction("Sığdır", self)
        self.zoom_fit_action.setToolTip("Sahneyi sığdır")
        self.zoom_fit_action.triggered.connect(self.zoom_fit_clicked.emit)
        self.addAction(self.zoom_fit_action)

        self.zoom_reset_action = QAction("100%", self)
        self.zoom_reset_action.setToolTip("Zoom'u sıfırla")
        self.zoom_reset_action.triggered.connect(self.zoom_reset_clicked.emit)
        self.addAction(self.zoom_reset_action)

        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.addWidget(spacer)

    def _add_separator_label(self, text: str):
        """Bölüm etiketi ekler"""
        label = QLabel(f" {text}: ")
        label.setStyleSheet("color: #666; font-weight: bold;")
        self.addWidget(label)

    def set_zoom_level(self, level: float):
        """Zoom seviyesini gösterir"""
        self.zoom_label.setText(f"{int(level * 100)}%")

    def set_grid_enabled(self, enabled: bool):
        """Grid durumunu ayarlar"""
        self.grid_action.setChecked(enabled)

    def set_snap_enabled(self, enabled: bool):
        """Snap durumunu ayarlar"""
        self.snap_action.setChecked(enabled)

    def set_undo_enabled(self, enabled: bool):
        """Undo butonunu etkinleştirir/devre dışı bırakır"""
        self.undo_action.setEnabled(enabled)

    def set_redo_enabled(self, enabled: bool):
        """Redo butonunu etkinleştirir/devre dışı bırakır"""
        self.redo_action.setEnabled(enabled)
