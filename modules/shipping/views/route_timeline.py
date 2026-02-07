"""
Akıllı İş - Rota Planlama: Zaman Çizelgesi (Timeline/Gantt) Widget'ı
"""

from datetime import datetime, time, timedelta

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QScrollArea,
    QLabel,
    QFrame,
    QHBoxLayout,
    QGridLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFontMetrics

from database.models.route import Route
from database.models.shipping import Vehicle


class RouteTimelineWidget(QWidget):
    """Araçların günlük planını gösteren Gantt benzeri çizelge."""

    shipment_dropped = pyqtSignal(int, int, datetime)  # vehicle_id, shipment_id, time

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Başlık
        # Tarih seçici ve navigasyon butonları eklenebilir
        header = QHBoxLayout()
        header.addWidget(QLabel("Günlük Planlama (08:00 - 20:00)"))
        self.layout.addLayout(header)

        # Çizelge Alanı
        self.timeline_area = TimelineArea()
        self.layout.addWidget(self.timeline_area)

        # Events
        self.timeline_area.shipment_dropped.connect(self.shipment_dropped.emit)

    def load_data(self, vehicles, routes):
        """Verileri yükler ve çizelgeyi günceller."""
        self.timeline_area.set_data(vehicles, routes)


class TimelineArea(QWidget):
    """Çizim alanı."""

    shipment_dropped = pyqtSignal(int, int, datetime)  # vehicle_id, shipment_id, time

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setMinimumHeight(400)

        self.start_hour = 8
        self.end_hour = 20
        self.hour_width = 60  # Pixel per hour
        self.row_height = 50
        self.header_height = 30
        self.sidebar_width = 150

        self.vehicles = []
        self.routes = []
        self.date = datetime.now().date()

    def set_data(self, vehicles, routes):
        self.vehicles = vehicles
        self.routes = routes
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Arkaplan
        painter.fillRect(self.rect(), Qt.GlobalColor.white)

        # Grid ve Saatler
        pen_grid = QPen(QColor(240, 240, 240))
        pen_grid.setStyle(Qt.PenStyle.DashLine)

        painter.setFont(self.font())

        # Saat başlıkları
        for h in range(self.start_hour, self.end_hour + 1):
            x = self.sidebar_width + (h - self.start_hour) * self.hour_width
            painter.drawText(x - 10, 20, f"{h:02d}:00")

            # Dikey çizgi
            painter.setPen(pen_grid)
            painter.drawLine(x, self.header_height, x, self.height())

        # Araç Satırları
        y = self.header_height
        for vehicle in self.vehicles:
            # Satır arkaplanı (alternatif renk)
            # painter.fillRect(0, y, self.width(), self.row_height, QColor(250, 250, 250))

            # Araç İsmi (Sidebar)
            painter.setPen(Qt.GlobalColor.black)
            vehicle_name = f"{vehicle.plate} ({vehicle.model or '-'})"
            painter.drawText(10, y + 30, vehicle_name)

            # Ayırıcı çizgi
            painter.setPen(QColor(220, 220, 220))
            painter.drawLine(0, y + self.row_height, self.width(), y + self.row_height)

            # Rotaları çiz
            self._draw_routes(painter, vehicle, y)

            y += self.row_height

        # Sidebar dikey çizgi
        painter.setPen(QColor(200, 200, 200))
        painter.drawLine(self.sidebar_width, 0, self.sidebar_width, self.height())

    def _draw_routes(self, painter, vehicle, y_offset):
        """Araca ait rotaları çizer."""
        vehicle_routes = [r for r in self.routes if r.vehicle_id == vehicle.id]

        for route in vehicle_routes:
            # Başlangıç ve bitiş saatlerini pixel'e çevir
            start_px = self._time_to_x(route.planned_start_time)
            end_px = self._time_to_x(route.planned_end_time)

            if start_px is None or end_px is None:
                continue

            width = max(end_px - start_px, 10)  # En az 10px

            rect = QRect(start_px, y_offset + 5, width, self.row_height - 10)

            # Renk (Duruma göre)
            color = QColor(100, 181, 246)  # Mavi
            if route.status == "completed":
                color = QColor(129, 199, 132)  # Yeşil

            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 4, 4)

            # Rota No
            painter.setPen(Qt.GlobalColor.white)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, route.route_no)

    def _time_to_x(self, dt):
        """Datetime objesini X koordinatına çevirir."""
        if not dt:
            return None

        # Sadece saat ve dakika önemli
        h = dt.hour
        m = dt.minute

        if h < self.start_hour:
            total_minutes = 0
        elif h > self.end_hour:
            total_minutes = (self.end_hour - self.start_hour) * 60
        else:
            total_minutes = (h - self.start_hour) * 60 + m

        pixels_per_minute = self.hour_width / 60
        return int(self.sidebar_width + total_minutes * pixels_per_minute)

    def _x_to_time(self, x):
        """X koordinatını saate çevirir."""
        if x < self.sidebar_width:
            return None

        rel_x = x - self.sidebar_width
        pixels_per_minute = self.hour_width / 60
        minutes = rel_x / pixels_per_minute

        hour = self.start_hour + int(minutes // 60)
        minute = int(minutes % 60)

        # Geçerli bir datetime oluştur
        try:
            return datetime.combine(self.date, time(hour, minute))
        except ValueError:
            return None

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-shipment-id"):
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-shipment-id"):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-shipment-id"):
            shipment_id = int(
                event.mimeData().data("application/x-shipment-id").data().decode()
            )
            drop_pos = event.position().toPoint()

            # Hangi araç satırına bırakıldı?
            y = drop_pos.y() - self.header_height
            row_index = y // self.row_height

            if 0 <= row_index < len(self.vehicles):
                vehicle = self.vehicles[row_index]
                drop_time = self._x_to_time(drop_pos.x())

                if drop_time:
                    self.shipment_dropped.emit(vehicle.id, shipment_id, drop_time)

            event.accept()
