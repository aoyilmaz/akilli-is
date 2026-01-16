"""
LabelView - Etiket görüntüleyici/düzenleyici view
"""

from typing import Optional

from PyQt6.QtWidgets import QGraphicsView, QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QWheelEvent, QMouseEvent, QKeyEvent

from .scene import LabelScene


class LabelView(QGraphicsView):
    """
    Etiket görüntüleyici.

    Özellikleri:
    - Zoom (Ctrl + scroll)
    - Pan (Orta tuş sürükleme veya Space + sol tuş)
    - Fit to view
    - Ruler senkronizasyonu (gelecek)
    """

    # Sinyaller
    zoom_changed = pyqtSignal(float)  # Zoom seviyesi
    cursor_position_changed = pyqtSignal(float, float)  # mm cinsinden pozisyon

    # Zoom sınırları
    MIN_ZOOM = 0.25
    MAX_ZOOM = 4.0
    ZOOM_STEP = 1.15

    def __init__(self, scene: Optional[LabelScene] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._zoom_level = 1.0
        self._panning = False
        self._pan_start: Optional[QPointF] = None
        self._space_pressed = False

        # Sahne
        if scene:
            self.setScene(scene)

        self._setup_view()

    def _setup_view(self):
        """View'i yapılandırır"""
        # Render ayarları
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # Viewport
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

        # Scroll bar'ları göster
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Transform
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)

        # Stil
        self.setStyleSheet("""
            QGraphicsView {
                border: 1px solid #ccc;
                background-color: #f0f0f0;
            }
        """)

    @property
    def zoom_level(self) -> float:
        return self._zoom_level

    def set_zoom(self, level: float):
        """Zoom seviyesini ayarlar"""
        level = max(self.MIN_ZOOM, min(self.MAX_ZOOM, level))
        if level == self._zoom_level:
            return

        # Transform uygula
        scale_factor = level / self._zoom_level
        self.scale(scale_factor, scale_factor)
        self._zoom_level = level

        self.zoom_changed.emit(level)

    def zoom_in(self):
        """Zoom in"""
        self.set_zoom(self._zoom_level * self.ZOOM_STEP)

    def zoom_out(self):
        """Zoom out"""
        self.set_zoom(self._zoom_level / self.ZOOM_STEP)

    def zoom_reset(self):
        """Zoom'u sıfırla (%100)"""
        self.set_zoom(1.0)

    def zoom_fit(self):
        """Sahneyi viewport'a sığdır"""
        if not self.scene():
            return

        # Sahne rect'i
        scene_rect = self.scene().sceneRect()
        if scene_rect.isEmpty():
            return

        # Viewport'a sığdır
        self.fitInView(scene_rect, Qt.AspectRatioMode.KeepAspectRatio)

        # Zoom seviyesini güncelle
        transform = self.transform()
        self._zoom_level = transform.m11()  # Horizontal scale
        self.zoom_changed.emit(self._zoom_level)

    def wheelEvent(self, event: QWheelEvent):
        """Scroll wheel olayı - Ctrl ile zoom"""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Zoom
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            elif delta < 0:
                self.zoom_out()
            event.accept()
        else:
            # Normal scroll
            super().wheelEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        """Tuş basma olayı"""
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            # Space ile pan modu
            self._space_pressed = True
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            event.accept()
        elif event.key() == Qt.Key.Key_Plus or event.key() == Qt.Key.Key_Equal:
            self.zoom_in()
            event.accept()
        elif event.key() == Qt.Key.Key_Minus:
            self.zoom_out()
            event.accept()
        elif event.key() == Qt.Key.Key_0:
            self.zoom_reset()
            event.accept()
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        """Tuş bırakma olayı"""
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self._space_pressed = False
            self._panning = False
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().keyReleaseEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        """Fare basma olayı"""
        if event.button() == Qt.MouseButton.MiddleButton:
            # Orta tuş ile pan
            self._panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        elif event.button() == Qt.MouseButton.LeftButton and self._space_pressed:
            # Space + sol tuş ile pan
            self._panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Fare hareket olayı"""
        if self._panning and self._pan_start:
            # Pan
            delta = event.position() - self._pan_start
            self._pan_start = event.position()

            # Scroll bar'ları hareket ettir
            h_bar = self.horizontalScrollBar()
            v_bar = self.verticalScrollBar()
            h_bar.setValue(int(h_bar.value() - delta.x()))
            v_bar.setValue(int(v_bar.value() - delta.y()))
            event.accept()
        else:
            # Fare pozisyonunu mm'e çevir ve sinyal gönder
            scene_pos = self.mapToScene(event.position().toPoint())
            if self.scene():
                from ..unit_converter import UnitConverter
                dpi = UnitConverter.SCREEN_DPI
                x_mm = UnitConverter.px_to_mm(scene_pos.x(), dpi)
                y_mm = UnitConverter.px_to_mm(scene_pos.y(), dpi)
                self.cursor_position_changed.emit(x_mm, y_mm)

            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Fare bırakma olayı"""
        if event.button() == Qt.MouseButton.MiddleButton or \
           (event.button() == Qt.MouseButton.LeftButton and self._space_pressed):
            self._panning = False
            self._pan_start = None
            if self._space_pressed:
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def get_visible_rect_mm(self) -> tuple:
        """Görünür alanı mm cinsinden döndürür"""
        rect = self.mapToScene(self.viewport().rect()).boundingRect()
        from ..unit_converter import UnitConverter
        dpi = UnitConverter.SCREEN_DPI
        return (
            UnitConverter.px_to_mm(rect.x(), dpi),
            UnitConverter.px_to_mm(rect.y(), dpi),
            UnitConverter.px_to_mm(rect.width(), dpi),
            UnitConverter.px_to_mm(rect.height(), dpi)
        )
