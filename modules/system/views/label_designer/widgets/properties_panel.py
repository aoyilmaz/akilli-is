"""
PropertiesPanel - Seçili eleman özellikleri paneli
"""

from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QGroupBox, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QPushButton, QColorDialog,
    QFontComboBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont

from ..items.base import LabelItem
from ..items.text_item import TextItem, TextAlignment
from ..items.barcode_item import BarcodeItem, BarcodeType
from ..items.qrcode_item import QRCodeItem, QRErrorLevel
from ..items.image_item import ImageItem, AspectMode
from ..items.shape_item import ShapeItem, ShapeType, LineStyle


class PropertiesPanel(QScrollArea):
    """
    Seçili eleman özellikleri paneli.

    Dinamik olarak seçili elemana göre uygun form alanlarını gösterir.
    """

    # Sinyaller
    property_changed = pyqtSignal(str, object)  # property_name, new_value

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._current_item: Optional[LabelItem] = None
        self._updating = False  # Programatik güncelleme sırasında sinyal engelle

        self._setup_ui()

    def _setup_ui(self):
        """UI'ı yapılandırır"""
        self.setWidgetResizable(True)
        self.setMinimumWidth(250)
        self.setMaximumWidth(350)

        # Ana container
        self.container = QWidget()
        self.setWidget(self.container)

        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(10)

        # Başlık
        title = QLabel("Özellikler")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.main_layout.addWidget(title)

        # Seçim yok mesajı
        self.no_selection_label = QLabel("Bir eleman seçin")
        self.no_selection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_selection_label.setStyleSheet("color: #999; padding: 20px;")
        self.main_layout.addWidget(self.no_selection_label)

        # Geometri grubu (tüm elemanlar için ortak)
        self.geometry_group = self._create_geometry_group()
        self.main_layout.addWidget(self.geometry_group)
        self.geometry_group.hide()

        # Metin özellikleri
        self.text_group = self._create_text_group()
        self.main_layout.addWidget(self.text_group)
        self.text_group.hide()

        # Barkod özellikleri
        self.barcode_group = self._create_barcode_group()
        self.main_layout.addWidget(self.barcode_group)
        self.barcode_group.hide()

        # QR kod özellikleri
        self.qrcode_group = self._create_qrcode_group()
        self.main_layout.addWidget(self.qrcode_group)
        self.qrcode_group.hide()

        # Görüntü özellikleri
        self.image_group = self._create_image_group()
        self.main_layout.addWidget(self.image_group)
        self.image_group.hide()

        # Şekil özellikleri
        self.shape_group = self._create_shape_group()
        self.main_layout.addWidget(self.shape_group)
        self.shape_group.hide()

        # Veri bağlama grubu
        self.data_binding_group = self._create_data_binding_group()
        self.main_layout.addWidget(self.data_binding_group)
        self.data_binding_group.hide()

        # Stretch
        self.main_layout.addStretch()

    def _create_geometry_group(self) -> QGroupBox:
        """Geometri grubu oluşturur"""
        group = QGroupBox("Geometri")
        layout = QFormLayout(group)

        # X pozisyon
        self.x_spin = QDoubleSpinBox()
        self.x_spin.setRange(0, 1000)
        self.x_spin.setSuffix(" mm")
        self.x_spin.setDecimals(1)
        self.x_spin.valueChanged.connect(lambda v: self._emit_change("x_mm", v))
        layout.addRow("X:", self.x_spin)

        # Y pozisyon
        self.y_spin = QDoubleSpinBox()
        self.y_spin.setRange(0, 1000)
        self.y_spin.setSuffix(" mm")
        self.y_spin.setDecimals(1)
        self.y_spin.valueChanged.connect(lambda v: self._emit_change("y_mm", v))
        layout.addRow("Y:", self.y_spin)

        # Genişlik
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(1, 1000)
        self.width_spin.setSuffix(" mm")
        self.width_spin.setDecimals(1)
        self.width_spin.valueChanged.connect(lambda v: self._emit_change("width_mm", v))
        layout.addRow("Genişlik:", self.width_spin)

        # Yükseklik
        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(1, 1000)
        self.height_spin.setSuffix(" mm")
        self.height_spin.setDecimals(1)
        self.height_spin.valueChanged.connect(lambda v: self._emit_change("height_mm", v))
        layout.addRow("Yükseklik:", self.height_spin)

        # Rotasyon
        self.rotation_combo = QComboBox()
        self.rotation_combo.addItems(["0°", "90°", "180°", "270°"])
        self.rotation_combo.currentIndexChanged.connect(
            lambda i: self._emit_change("rotation", i * 90)
        )
        layout.addRow("Döndür:", self.rotation_combo)

        return group

    def _create_text_group(self) -> QGroupBox:
        """Metin özellikleri grubu"""
        group = QGroupBox("Metin")
        layout = QFormLayout(group)

        # Metin içeriği
        self.text_edit = QLineEdit()
        self.text_edit.textChanged.connect(lambda t: self._emit_change("text", t))
        layout.addRow("İçerik:", self.text_edit)

        # Font ailesi
        self.font_combo = QFontComboBox()
        self.font_combo.currentFontChanged.connect(
            lambda f: self._emit_change("font_family", f.family())
        )
        layout.addRow("Font:", self.font_combo)

        # Font boyutu
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(6, 144)
        self.font_size_spin.setValue(12)
        self.font_size_spin.valueChanged.connect(lambda v: self._emit_change("font_size", v))
        layout.addRow("Boyut:", self.font_size_spin)

        # Stil butonları
        style_layout = QHBoxLayout()

        self.bold_check = QCheckBox("B")
        self.bold_check.setStyleSheet("font-weight: bold;")
        self.bold_check.toggled.connect(lambda v: self._emit_change("bold", v))
        style_layout.addWidget(self.bold_check)

        self.italic_check = QCheckBox("I")
        self.italic_check.setStyleSheet("font-style: italic;")
        self.italic_check.toggled.connect(lambda v: self._emit_change("italic", v))
        style_layout.addWidget(self.italic_check)

        self.underline_check = QCheckBox("U")
        self.underline_check.setStyleSheet("text-decoration: underline;")
        self.underline_check.toggled.connect(lambda v: self._emit_change("underline", v))
        style_layout.addWidget(self.underline_check)

        layout.addRow("Stil:", style_layout)

        # Hizalama
        self.text_align_combo = QComboBox()
        self.text_align_combo.addItems(["Sol", "Orta", "Sağ"])
        self.text_align_combo.currentIndexChanged.connect(self._on_text_alignment_changed)
        layout.addRow("Hizalama:", self.text_align_combo)

        # Renk
        color_layout = QHBoxLayout()
        self.text_color_btn = QPushButton()
        self.text_color_btn.setFixedSize(30, 25)
        self.text_color_btn.setStyleSheet("background-color: #000000;")
        self.text_color_btn.clicked.connect(self._pick_text_color)
        color_layout.addWidget(self.text_color_btn)
        self.text_color_label = QLabel("#000000")
        color_layout.addWidget(self.text_color_label)
        color_layout.addStretch()
        layout.addRow("Renk:", color_layout)

        return group

    def _create_barcode_group(self) -> QGroupBox:
        """Barkod özellikleri grubu"""
        group = QGroupBox("Barkod")
        layout = QFormLayout(group)

        # Barkod verisi
        self.barcode_data_edit = QLineEdit()
        self.barcode_data_edit.textChanged.connect(lambda t: self._emit_change("barcode_data", t))
        layout.addRow("Veri:", self.barcode_data_edit)

        # Barkod türü
        self.barcode_type_combo = QComboBox()
        for bt in BarcodeType:
            self.barcode_type_combo.addItem(bt.display_name, bt)
        self.barcode_type_combo.currentIndexChanged.connect(self._on_barcode_type_changed)
        layout.addRow("Tür:", self.barcode_type_combo)

        # Metin göster
        self.barcode_text_check = QCheckBox("Barkod altında metin göster")
        self.barcode_text_check.toggled.connect(lambda v: self._emit_change("show_text", v))
        layout.addRow("", self.barcode_text_check)

        return group

    def _create_qrcode_group(self) -> QGroupBox:
        """QR kod özellikleri grubu"""
        group = QGroupBox("QR Kod")
        layout = QFormLayout(group)

        # QR verisi
        self.qr_data_edit = QLineEdit()
        self.qr_data_edit.textChanged.connect(lambda t: self._emit_change("qr_data", t))
        layout.addRow("Veri:", self.qr_data_edit)

        # Hata düzeltme
        self.qr_error_combo = QComboBox()
        for el in QRErrorLevel:
            self.qr_error_combo.addItem(el.display_name, el)
        self.qr_error_combo.currentIndexChanged.connect(self._on_qr_error_changed)
        layout.addRow("Hata Düzeltme:", self.qr_error_combo)

        # Kare yap butonu
        self.qr_square_btn = QPushButton("Kare Yap")
        self.qr_square_btn.clicked.connect(lambda: self._emit_change("make_square", True))
        layout.addRow("", self.qr_square_btn)

        return group

    def _create_image_group(self) -> QGroupBox:
        """Görüntü özellikleri grubu"""
        group = QGroupBox("Görüntü")
        layout = QFormLayout(group)

        # Dosya yolu
        path_layout = QHBoxLayout()
        self.image_path_edit = QLineEdit()
        self.image_path_edit.setReadOnly(True)
        path_layout.addWidget(self.image_path_edit)
        self.image_browse_btn = QPushButton("...")
        self.image_browse_btn.setFixedWidth(30)
        self.image_browse_btn.clicked.connect(self._browse_image)
        path_layout.addWidget(self.image_browse_btn)
        layout.addRow("Dosya:", path_layout)

        # Aspect mode
        self.aspect_combo = QComboBox()
        for am in AspectMode:
            self.aspect_combo.addItem(am.display_name, am)
        self.aspect_combo.currentIndexChanged.connect(self._on_aspect_changed)
        layout.addRow("Oran:", self.aspect_combo)

        # Embed butonu
        self.embed_btn = QPushButton("Görüntüyü Göm")
        self.embed_btn.clicked.connect(lambda: self._emit_change("embed_image", True))
        layout.addRow("", self.embed_btn)

        return group

    def _create_shape_group(self) -> QGroupBox:
        """Şekil özellikleri grubu"""
        group = QGroupBox("Şekil")
        layout = QFormLayout(group)

        # Kenar rengi
        stroke_layout = QHBoxLayout()
        self.stroke_color_btn = QPushButton()
        self.stroke_color_btn.setFixedSize(30, 25)
        self.stroke_color_btn.setStyleSheet("background-color: #000000;")
        self.stroke_color_btn.clicked.connect(self._pick_stroke_color)
        stroke_layout.addWidget(self.stroke_color_btn)
        self.stroke_color_label = QLabel("#000000")
        stroke_layout.addWidget(self.stroke_color_label)
        stroke_layout.addStretch()
        layout.addRow("Kenar Rengi:", stroke_layout)

        # Kenar kalınlığı
        self.stroke_width_spin = QDoubleSpinBox()
        self.stroke_width_spin.setRange(0.1, 20)
        self.stroke_width_spin.setValue(1)
        self.stroke_width_spin.valueChanged.connect(lambda v: self._emit_change("stroke_width", v))
        layout.addRow("Kenar Kalınlığı:", self.stroke_width_spin)

        # Çizgi stili
        self.line_style_combo = QComboBox()
        for ls in LineStyle:
            self.line_style_combo.addItem(ls.display_name, ls)
        self.line_style_combo.currentIndexChanged.connect(self._on_line_style_changed)
        layout.addRow("Çizgi Stili:", self.line_style_combo)

        # Dolgu rengi
        fill_layout = QHBoxLayout()
        self.fill_color_btn = QPushButton()
        self.fill_color_btn.setFixedSize(30, 25)
        self.fill_color_btn.setStyleSheet("background-color: transparent; border: 1px solid #ccc;")
        self.fill_color_btn.clicked.connect(self._pick_fill_color)
        fill_layout.addWidget(self.fill_color_btn)
        self.fill_color_label = QLabel("Yok")
        fill_layout.addWidget(self.fill_color_label)
        self.clear_fill_btn = QPushButton("Temizle")
        self.clear_fill_btn.setFixedWidth(60)
        self.clear_fill_btn.clicked.connect(lambda: self._emit_change("fill_color", None))
        fill_layout.addWidget(self.clear_fill_btn)
        layout.addRow("Dolgu:", fill_layout)

        # Köşe yuvarlaklığı (dikdörtgen için)
        self.corner_radius_spin = QDoubleSpinBox()
        self.corner_radius_spin.setRange(0, 50)
        self.corner_radius_spin.setValue(0)
        self.corner_radius_spin.valueChanged.connect(lambda v: self._emit_change("corner_radius", v))
        layout.addRow("Köşe Yarıçapı:", self.corner_radius_spin)

        return group

    def _create_data_binding_group(self) -> QGroupBox:
        """Veri bağlama grubu"""
        group = QGroupBox("Veri Bağlama")
        layout = QFormLayout(group)

        # Data key
        self.data_key_edit = QLineEdit()
        self.data_key_edit.setPlaceholderText("{Değişken_Adı}")
        self.data_key_edit.textChanged.connect(lambda t: self._emit_change("data_key", t))
        layout.addRow("Değişken:", self.data_key_edit)

        # Yardım metni
        help_label = QLabel("Örnek: {Urun_Adi}, {Barkod}, {SKT}")
        help_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addRow("", help_label)

        return group

    def set_item(self, item: Optional[LabelItem]):
        """Seçili elemanı ayarlar"""
        self._current_item = item
        self._update_ui()

    def set_items(self, items: List[LabelItem]):
        """Çoklu seçim için"""
        if len(items) == 1:
            self.set_item(items[0])
        elif len(items) == 0:
            self.set_item(None)
        else:
            # Çoklu seçim - sadece geometri göster
            self._current_item = items[0]  # İlk elemanın değerlerini göster
            self._hide_all_groups()
            self.geometry_group.show()
            self.no_selection_label.hide()
            self._update_geometry_values()

    def _update_ui(self):
        """UI'ı günceller"""
        self._updating = True

        self._hide_all_groups()

        if not self._current_item:
            self.no_selection_label.show()
            self._updating = False
            return

        self.no_selection_label.hide()
        self.geometry_group.show()
        self.data_binding_group.show()

        self._update_geometry_values()
        self._update_data_binding_values()

        item_type = self._current_item.item_type

        if item_type == "text":
            self.text_group.show()
            self._update_text_values()
        elif item_type == "barcode":
            self.barcode_group.show()
            self._update_barcode_values()
        elif item_type == "qrcode":
            self.qrcode_group.show()
            self._update_qrcode_values()
        elif item_type == "image":
            self.image_group.show()
            self._update_image_values()
        elif item_type in ("rectangle", "line", "ellipse"):
            self.shape_group.show()
            self._update_shape_values()

        self._updating = False

    def _hide_all_groups(self):
        """Tüm grupları gizler"""
        self.geometry_group.hide()
        self.text_group.hide()
        self.barcode_group.hide()
        self.qrcode_group.hide()
        self.image_group.hide()
        self.shape_group.hide()
        self.data_binding_group.hide()

    def _update_geometry_values(self):
        """Geometri değerlerini günceller"""
        if not self._current_item:
            return
        g = self._current_item.geometry
        self.x_spin.setValue(g.x_mm)
        self.y_spin.setValue(g.y_mm)
        self.width_spin.setValue(g.width_mm)
        self.height_spin.setValue(g.height_mm)
        self.rotation_combo.setCurrentIndex(g.rotation // 90)

    def _update_text_values(self):
        """Metin değerlerini günceller"""
        if not isinstance(self._current_item, TextItem):
            return
        item = self._current_item
        self.text_edit.setText(item.text)
        self.font_combo.setCurrentFont(QFont(item.style.font_family))
        self.font_size_spin.setValue(item.style.font_size)
        self.bold_check.setChecked(item.style.bold)
        self.italic_check.setChecked(item.style.italic)
        self.underline_check.setChecked(item.style.underline)

        align_idx = {"left": 0, "center": 1, "right": 2}.get(item.style.alignment.value, 0)
        self.text_align_combo.setCurrentIndex(align_idx)

        self.text_color_btn.setStyleSheet(f"background-color: {item.style.color};")
        self.text_color_label.setText(item.style.color)

    def _update_barcode_values(self):
        """Barkod değerlerini günceller"""
        if not isinstance(self._current_item, BarcodeItem):
            return
        item = self._current_item
        self.barcode_data_edit.setText(item.barcode_data)
        idx = self.barcode_type_combo.findData(item.barcode_type)
        if idx >= 0:
            self.barcode_type_combo.setCurrentIndex(idx)
        self.barcode_text_check.setChecked(item.show_text)

    def _update_qrcode_values(self):
        """QR kod değerlerini günceller"""
        if not isinstance(self._current_item, QRCodeItem):
            return
        item = self._current_item
        self.qr_data_edit.setText(item.qr_data)
        idx = self.qr_error_combo.findData(item.error_level)
        if idx >= 0:
            self.qr_error_combo.setCurrentIndex(idx)

    def _update_image_values(self):
        """Görüntü değerlerini günceller"""
        if not isinstance(self._current_item, ImageItem):
            return
        item = self._current_item
        self.image_path_edit.setText(item.image_path or "")
        idx = self.aspect_combo.findData(item.aspect_mode)
        if idx >= 0:
            self.aspect_combo.setCurrentIndex(idx)

    def _update_shape_values(self):
        """Şekil değerlerini günceller"""
        if not isinstance(self._current_item, ShapeItem):
            return
        item = self._current_item
        style = item.style

        self.stroke_color_btn.setStyleSheet(f"background-color: {style.stroke_color};")
        self.stroke_color_label.setText(style.stroke_color)
        self.stroke_width_spin.setValue(style.stroke_width)

        idx = self.line_style_combo.findData(style.line_style)
        if idx >= 0:
            self.line_style_combo.setCurrentIndex(idx)

        if style.fill_color:
            self.fill_color_btn.setStyleSheet(f"background-color: {style.fill_color};")
            self.fill_color_label.setText(style.fill_color)
        else:
            self.fill_color_btn.setStyleSheet("background-color: transparent; border: 1px solid #ccc;")
            self.fill_color_label.setText("Yok")

        self.corner_radius_spin.setValue(style.corner_radius)
        # Köşe yuvarlaklığı sadece dikdörtgen için
        self.corner_radius_spin.setEnabled(item.shape_type == ShapeType.RECTANGLE)

    def _update_data_binding_values(self):
        """Veri bağlama değerlerini günceller"""
        if not self._current_item:
            return
        self.data_key_edit.setText(self._current_item.data_key or "")

    def _emit_change(self, prop: str, value):
        """Özellik değişikliği sinyali gönderir"""
        if not self._updating and self._current_item:
            self.property_changed.emit(prop, value)

    def _on_text_alignment_changed(self, index: int):
        """Metin hizalama değiştiğinde"""
        alignments = [TextAlignment.LEFT, TextAlignment.CENTER, TextAlignment.RIGHT]
        if 0 <= index < len(alignments):
            self._emit_change("alignment", alignments[index])

    def _on_barcode_type_changed(self, index: int):
        """Barkod türü değiştiğinde"""
        bt = self.barcode_type_combo.currentData()
        if bt:
            self._emit_change("barcode_type", bt)

    def _on_qr_error_changed(self, index: int):
        """QR hata seviyesi değiştiğinde"""
        el = self.qr_error_combo.currentData()
        if el:
            self._emit_change("error_level", el)

    def _on_aspect_changed(self, index: int):
        """Aspect mode değiştiğinde"""
        am = self.aspect_combo.currentData()
        if am:
            self._emit_change("aspect_mode", am)

    def _on_line_style_changed(self, index: int):
        """Çizgi stili değiştiğinde"""
        ls = self.line_style_combo.currentData()
        if ls:
            self._emit_change("line_style", ls)

    def _pick_text_color(self):
        """Metin rengi seçici"""
        current = self.text_color_label.text()
        color = QColorDialog.getColor(QColor(current), self, "Metin Rengi")
        if color.isValid():
            self._emit_change("color", color.name())

    def _pick_stroke_color(self):
        """Kenar rengi seçici"""
        current = self.stroke_color_label.text()
        color = QColorDialog.getColor(QColor(current), self, "Kenar Rengi")
        if color.isValid():
            self._emit_change("stroke_color", color.name())

    def _pick_fill_color(self):
        """Dolgu rengi seçici"""
        color = QColorDialog.getColor(Qt.GlobalColor.white, self, "Dolgu Rengi")
        if color.isValid():
            self._emit_change("fill_color", color.name())

    def _browse_image(self):
        """Görüntü dosyası seçici"""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Görüntü Seç",
            "",
            "Görüntü Dosyaları (*.png *.jpg *.jpeg)"
        )
        if file_path:
            self._emit_change("image_path", file_path)
