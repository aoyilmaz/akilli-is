"""
ResizeHandle - 8 noktalı boyutlandırma tutamacı
"""

from enum import Enum
from typing import TYPE_CHECKING, Optional

from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal, QObject
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QCursor

if TYPE_CHECKING:
    from ..items.base import LabelItem


class HandlePosition(Enum):
    """Tutamaç pozisyonları"""
    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    MIDDLE_LEFT = "middle_left"
    MIDDLE_RIGHT = "middle_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"

    @property
    def cursor(self) -> Qt.CursorShape:
        """Pozisyona göre fare imleci"""
        cursors = {
            HandlePosition.TOP_LEFT: Qt.CursorShape.SizeFDiagCursor,
            HandlePosition.TOP_CENTER: Qt.CursorShape.SizeVerCursor,
            HandlePosition.TOP_RIGHT: Qt.CursorShape.SizeBDiagCursor,
            HandlePosition.MIDDLE_LEFT: Qt.CursorShape.SizeHorCursor,
            HandlePosition.MIDDLE_RIGHT: Qt.CursorShape.SizeHorCursor,
            HandlePosition.BOTTOM_LEFT: Qt.CursorShape.SizeBDiagCursor,
            HandlePosition.BOTTOM_CENTER: Qt.CursorShape.SizeVerCursor,
            HandlePosition.BOTTOM_RIGHT: Qt.CursorShape.SizeFDiagCursor,
        }
        return cursors.get(self, Qt.CursorShape.ArrowCursor)


class ResizeHandleSignals(QObject):
    """ResizeHandle sinyalleri"""
    resize_started = pyqtSignal()
    resize_finished = pyqtSignal(QRectF)  # Yeni rect


class ResizeHandle(QGraphicsRectItem):
    """
    Boyutlandırma tutamacı.

    Elemanların köşe ve kenarlarında görünür.
    Sürüklendiğinde elemanın boyutunu değiştirir.
    """

    SIZE = 8  # Piksel

    def __init__(
        self,
        position: HandlePosition,
        parent_item: "LabelItem",
        parent=None
    ):
        super().__init__(parent)
        self._position = position
        self._parent_item = parent_item
        self._dragging = False
        self._start_pos: Optional[QPointF] = None
        self._start_rect: Optional[QRectF] = None

        # Sinyaller
        self.signals = ResizeHandleSignals()

        self._setup_handle()

    def _setup_handle(self):
        """Tutamacı yapılandırır"""
        # Boyut
        self.setRect(-self.SIZE / 2, -self.SIZE / 2, self.SIZE, self.SIZE)

        # Flags
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)

        # Görünüm
        self.setBrush(QBrush(QColor("#ffffff")))
        self.setPen(QPen(QColor("#007acc"), 1))

        # İmleç
        self.setCursor(QCursor(self._position.cursor))

        # Başlangıçta gizli
        self.setVisible(False)

        # Z-index (üstte)
        self.setZValue(1000)

    @property
    def position(self) -> HandlePosition:
        return self._position

    def update_position(self):
        """Tutamacı parent item'a göre konumlandırır"""
        rect = self._parent_item.boundingRect()
        parent_pos = self._parent_item.pos()

        # Pozisyona göre koordinat
        positions = {
            HandlePosition.TOP_LEFT: QPointF(rect.left(), rect.top()),
            HandlePosition.TOP_CENTER: QPointF(rect.center().x(), rect.top()),
            HandlePosition.TOP_RIGHT: QPointF(rect.right(), rect.top()),
            HandlePosition.MIDDLE_LEFT: QPointF(rect.left(), rect.center().y()),
            HandlePosition.MIDDLE_RIGHT: QPointF(rect.right(), rect.center().y()),
            HandlePosition.BOTTOM_LEFT: QPointF(rect.left(), rect.bottom()),
            HandlePosition.BOTTOM_CENTER: QPointF(rect.center().x(), rect.bottom()),
            HandlePosition.BOTTOM_RIGHT: QPointF(rect.right(), rect.bottom()),
        }

        local_pos = positions.get(self._position, QPointF(0, 0))
        self.setPos(parent_pos + local_pos)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None):
        """Tutamacı çizer"""
        # Beyaz arka plan, mavi kenarlık
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawRect(self.rect())

    def hoverEnterEvent(self, event):
        """Fare tutamaca girdiğinde"""
        self.setBrush(QBrush(QColor("#e6f2ff")))
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """Fare tutamaçtan çıktığında"""
        self.setBrush(QBrush(QColor("#ffffff")))
        self.update()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        """Fare basıldığında"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._start_pos = event.scenePos()
            self._start_rect = QRectF(
                self._parent_item.pos().x(),
                self._parent_item.pos().y(),
                self._parent_item.boundingRect().width(),
                self._parent_item.boundingRect().height()
            )
            self.signals.resize_started.emit()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Fare sürüklendiğinde"""
        if self._dragging and self._start_pos and self._start_rect:
            delta = event.scenePos() - self._start_pos
            new_rect = self._calculate_new_rect(delta)

            # Minimum boyut kontrolü
            if new_rect.width() >= 10 and new_rect.height() >= 10:
                # Parent item'ı güncelle
                self._parent_item.setPos(new_rect.topLeft())
                self._parent_item.update_geometry_from_handles(
                    QRectF(0, 0, new_rect.width(), new_rect.height())
                )

            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Fare bırakıldığında"""
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            self._dragging = False

            # Son rect'i hesapla
            if self._start_pos:
                delta = event.scenePos() - self._start_pos
                final_rect = self._calculate_new_rect(delta)
                self.signals.resize_finished.emit(final_rect)

            self._start_pos = None
            self._start_rect = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def _calculate_new_rect(self, delta: QPointF) -> QRectF:
        """Sürükleme delta'sına göre yeni rect hesaplar"""
        if not self._start_rect:
            return QRectF()

        rect = QRectF(self._start_rect)

        # Pozisyona göre rect'i değiştir
        if self._position == HandlePosition.TOP_LEFT:
            rect.setTopLeft(rect.topLeft() + delta)
        elif self._position == HandlePosition.TOP_CENTER:
            rect.setTop(rect.top() + delta.y())
        elif self._position == HandlePosition.TOP_RIGHT:
            rect.setTopRight(rect.topRight() + QPointF(delta.x(), delta.y()))
        elif self._position == HandlePosition.MIDDLE_LEFT:
            rect.setLeft(rect.left() + delta.x())
        elif self._position == HandlePosition.MIDDLE_RIGHT:
            rect.setRight(rect.right() + delta.x())
        elif self._position == HandlePosition.BOTTOM_LEFT:
            rect.setBottomLeft(rect.bottomLeft() + QPointF(delta.x(), delta.y()))
        elif self._position == HandlePosition.BOTTOM_CENTER:
            rect.setBottom(rect.bottom() + delta.y())
        elif self._position == HandlePosition.BOTTOM_RIGHT:
            rect.setBottomRight(rect.bottomRight() + delta)

        # Normalize (negatif boyutları düzelt)
        return rect.normalized()


def create_handles_for_item(item: "LabelItem") -> list:
    """
    Bir item için 8 adet resize handle oluşturur.

    Returns:
        8 adet ResizeHandle listesi
    """
    handles = []
    for position in HandlePosition:
        handle = ResizeHandle(position, item)
        handles.append(handle)
    return handles
