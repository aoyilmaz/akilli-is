"""
Akıllı İş - SPC Grafik Bileşenleri (Custom QPainter Widgets)
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QPolygonF
import numpy as np


class SPCChartWidget(QWidget):
    """
    SPC Kontrol Grafikleri (X-bar, R) için temel çizim sınıfı.
    """

    def __init__(self, title="Kontrol Grafiği", parent=None):
        super().__init__(parent)
        self.title = title
        self.data_points = []
        self.ucl = None
        self.lcl = None
        self.cl = None
        self.setMinimumHeight(250)

    def set_data(self, points, ucl=None, lcl=None, cl=None):
        """Grafik verilerini günceller."""
        self.data_points = points
        self.ucl = ucl
        self.lcl = lcl
        self.cl = cl
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Padding ve Alan Tanımlama
        padding_l, padding_r = 60, 40
        padding_t, padding_b = 40, 40
        w, h = self.width(), self.height()
        chart_rect = QRectF(
            padding_l, padding_t, w - padding_l - padding_r, h - padding_t - padding_b
        )

        # Arkaplan
        painter.fillRect(self.rect(), QColor("#FFFFFF"))

        # Başlık
        painter.setPen(QColor("#333333"))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.drawText(
            QRectF(0, 0, w, padding_t), Qt.AlignmentFlag.AlignCenter, self.title
        )

        if not self.data_points:
            painter.drawText(chart_rect, Qt.AlignmentFlag.AlignCenter, "Veri Yok")
            return

        # Ölçeklendirme
        all_vals = [p["val"] for p in self.data_points]
        if self.ucl is not None:
            all_vals.append(self.ucl)
        if self.lcl is not None:
            all_vals.append(self.lcl)
        if self.cl is not None:
            all_vals.append(self.cl)

        min_v = min(all_vals) * 0.995
        max_v = max(all_vals) * 1.005
        range_v = max_v - min_v if max_v != min_v else 1

        def to_y(val):
            return chart_rect.bottom() - ((val - min_v) / range_v) * chart_rect.height()

        def to_x(idx):
            if len(self.data_points) <= 1:
                return chart_rect.left()
            return (
                chart_rect.left()
                + (idx / (len(self.data_points) - 1)) * chart_rect.width()
            )

        # Eksiler ve Izgara
        painter.setPen(QPen(QColor("#E0E0E0"), 1))
        painter.drawLine(
            int(chart_rect.left()),
            int(chart_rect.bottom()),
            int(chart_rect.right()),
            int(chart_rect.bottom()),
        )
        painter.drawLine(
            int(chart_rect.left()),
            int(chart_rect.top()),
            int(chart_rect.left()),
            int(chart_rect.bottom()),
        )

        # Kontrol Limitleri Çizimi
        painter.setFont(QFont("Segoe UI", 7))
        if self.ucl is not None:
            y_ucl = to_y(self.ucl)
            painter.setPen(QPen(QColor("#F44336"), 1, Qt.PenStyle.DashLine))
            painter.drawLine(
                int(chart_rect.left()), int(y_ucl), int(chart_rect.right()), int(y_ucl)
            )
            painter.drawText(
                int(chart_rect.right() + 5), int(y_ucl + 5), f"UCL: {self.ucl:.2f}"
            )

        if self.lcl is not None:
            y_lcl = to_y(self.lcl)
            painter.setPen(QPen(QColor("#F44336"), 1, Qt.PenStyle.DashLine))
            painter.drawLine(
                int(chart_rect.left()), int(y_lcl), int(chart_rect.right()), int(y_lcl)
            )
            painter.drawText(
                int(chart_rect.right() + 5), int(y_lcl + 5), f"LCL: {self.lcl:.2f}"
            )

        if self.cl is not None:
            y_cl = to_y(self.cl)
            painter.setPen(QPen(QColor("#4CAF50"), 1, Qt.PenStyle.SolidLine))
            painter.drawLine(
                int(chart_rect.left()), int(y_cl), int(chart_rect.right()), int(y_cl)
            )
            painter.drawText(
                int(chart_rect.right() + 5), int(y_cl + 5), f"CL: {self.cl:.2f}"
            )

        # Veri Hattı
        path = QPolygonF()
        for i, pt in enumerate(self.data_points):
            path.append(QPointF(to_x(i), to_y(pt["val"])))

        painter.setPen(QPen(QColor("#2196F3"), 2))
        painter.drawPolyline(path)

        # Noktalar
        for i, pt in enumerate(self.data_points):
            x, y = to_x(i), to_y(pt["val"])
            color = QColor("#2196F3")
            if self.ucl and pt["val"] > self.ucl:
                color = QColor("#F44336")
            if self.lcl and pt["val"] < self.lcl:
                color = QColor("#F44336")

            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(x, y), 4, 4)

            # X ekseni etiketleri (Her 5 noktada bir)
            if i % 5 == 0 or i == len(self.data_points) - 1:
                painter.setPen(QColor("#999999"))
                painter.drawText(
                    QRectF(x - 20, chart_rect.bottom() + 5, 40, 20),
                    Qt.AlignmentFlag.AlignCenter,
                    pt["label"],
                )
