"""
Akıllı İş - Üretim Planlama Sayfası
TAKVİM ENTEGRASYONlu MAKİNE BAZLI GANTT CHART
"""

from datetime import datetime, timedelta, date
from decimal import Decimal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
    QComboBox,
    QSizePolicy,
    QToolTip,
    QGridLayout,
    QSpacerItem,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QRect, QSize
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QLinearGradient
from ui.components.stat_cards import MiniStatCard


class GanttBar(QWidget):
    """Gantt çubuğu - İş emri operasyonu"""

    clicked = pyqtSignal(int)  # work_order_id

    def __init__(
        self,
        wo_id: int,
        order_no: str,
        item_name: str,
        operation_name: str,
        progress: float,
        status: str,
        color: str,
        duration_hours: float = 0,
        parent=None,
    ):
        super().__init__(parent)
        self.wo_id = wo_id
        self.order_no = order_no
        self.item_name = item_name
        self.operation_name = operation_name
        self.progress = progress
        self.status = status
        self.color = QColor(color)
        self.duration_hours = duration_hours

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(36)
        self.setMaximumHeight(36)

        # Tooltip
        tooltip = f"""<b>{order_no}</b><br/>
        Ürün: {item_name}<br/>
        Operasyon: {operation_name}<br/>
        Süre: {duration_hours:.1f} saat<br/>
        İlerleme: %{progress:.0f}<br/>
        Durum: {status}"""
        self.setToolTip(tooltip)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()

        # Gradient arka plan
        gradient = QLinearGradient(0, 0, 0, rect.height())
        bg_color = QColor(self.color)
        bg_color.setAlpha(180)
        gradient.setColorAt(0, bg_color.lighter(120))
        gradient.setColorAt(1, bg_color)

        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(self.color.darker(110), 1))
        painter.drawRoundedRect(rect.adjusted(1, 2, -1, -2), 4, 4)

        # İlerleme çubuğu (alt kısımda)
        if self.progress > 0:
            progress_width = int((rect.width() - 4) * min(self.progress, 100) / 100)
            progress_rect = QRect(2, rect.height() - 6, progress_width, 4)
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(progress_rect, 2, 2)

        # Metin
        painter.setPen(QPen(QColor("#ffffff")))
        font = QFont("Segoe UI", 9)
        font.setBold(True)
        painter.setFont(font)

        text = f"{self.order_no}"
        if rect.width() > 120:
            text = f"{self.order_no} - {self.item_name[:15]}"
        if rect.width() > 200:
            text = (
                f"{self.order_no} - {self.item_name[:20]} ({self.duration_hours:.0f}h)"
            )

        painter.drawText(
            rect.adjusted(8, 0, -8, -4),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            text,
        )

    def mousePressEvent(self, event):
        self.clicked.emit(self.wo_id)

    def sizeHint(self):
        return QSize(100, 36)


class TimelineHeader(QWidget):
    """Zaman çizelgesi başlığı - Tatil gösterimli"""

    def __init__(
        self,
        start_date: QDate,
        num_days: int,
        pixels_per_day: int,
        holidays: list = None,
        parent=None,
    ):
        super().__init__(parent)
        self.start_date = start_date
        self.num_days = num_days
        self.pixels_per_day = pixels_per_day
        self.holidays = holidays or []  # [(date, name, is_half_day), ...]

        # Holiday'leri set olarak tut (hızlı lookup için)
        self.holiday_dates = {h[0]: (h[1], h[2]) for h in self.holidays}

        self.setFixedHeight(50)
        self.setMinimumWidth(180 + num_days * pixels_per_day)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Sol kenar boşluğu (makine isimleri için)
        left_margin = 180

        # Arka plan - Global tema renkleri
        painter.fillRect(0, 0, left_margin, self.height(), QColor("#1e1e1e"))
        painter.fillRect(
            left_margin, 0, self.width() - left_margin, self.height(), QColor("#252526")
        )

        # Sol başlık
        painter.setPen(QColor("#64748b"))
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(
            10,
            0,
            left_margin - 20,
            self.height(),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            "İş İstasyonu",
        )

        # Gün başlıkları
        day_names_short = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
        months = [
            "Oca",
            "Şub",
            "Mar",
            "Nis",
            "May",
            "Haz",
            "Tem",
            "Ağu",
            "Eyl",
            "Eki",
            "Kas",
            "Ara",
        ]

        for i in range(self.num_days):
            x = left_margin + i * self.pixels_per_day
            day = self.start_date.addDays(i)
            day_date = date(day.year(), day.month(), day.day())

            is_weekend = day.dayOfWeek() >= 6
            is_holiday = day_date in self.holiday_dates
            is_today = day == QDate.currentDate()

            # Arka plan rengi
            if is_holiday:
                # Tatil - Kırmızımsı
                bg_color = QColor("#7f1d1d")  # red-900
            elif is_weekend:
                # Hafta sonu - Açık yeşil
                bg_color = QColor("#064e3b")  # emerald-900
            elif is_today:
                # Bugün - Vurgulu açık mavi
                bg_color = QColor("#0369a1")  # sky-700
            else:
                # Çalışma günleri - Açık mavi
                bg_color = QColor("#0c4a6e")  # sky-900

            painter.fillRect(x, 0, self.pixels_per_day, self.height(), bg_color)

            # Dikey çizgi
            painter.setPen(QPen(QColor("#334155"), 1))
            painter.drawLine(x, 0, x, self.height())

            # Gün bilgisi
            if self.pixels_per_day >= 40:
                # Geniş görünüm - iki satır
                day_name = day_names_short[day.dayOfWeek() - 1]

                # Tatil adı göster
                if is_holiday:
                    holiday_name, is_half = self.holiday_dates[day_date]
                    painter.setPen(QColor("#fca5a5"))  # red-300
                    font = QFont("Segoe UI", 8)
                    painter.setFont(font)
                    # Kısalt
                    short_name = (
                        holiday_name[:8] + ".."
                        if len(holiday_name) > 10
                        else holiday_name
                    )
                    painter.drawText(
                        x + 2,
                        2,
                        self.pixels_per_day - 4,
                        14,
                        Qt.AlignmentFlag.AlignCenter,
                        short_name,
                    )

                    painter.setPen(QColor("#f87171"))
                    painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                    painter.drawText(
                        x,
                        14,
                        self.pixels_per_day,
                        18,
                        Qt.AlignmentFlag.AlignCenter,
                        f"{day.day()}",
                    )

                    half_text = "½" if is_half else "✗"
                    painter.setPen(QColor("#fca5a5"))
                    painter.setFont(QFont("Segoe UI", 8))
                    painter.drawText(
                        x,
                        32,
                        self.pixels_per_day,
                        14,
                        Qt.AlignmentFlag.AlignCenter,
                        half_text,
                    )
                else:
                    # Normal gün
                    painter.setPen(
                        QColor("#64748b") if is_weekend else QColor("#94a3b8")
                    )
                    painter.setFont(QFont("Segoe UI", 8))
                    painter.drawText(
                        x,
                        2,
                        self.pixels_per_day,
                        14,
                        Qt.AlignmentFlag.AlignCenter,
                        day_name,
                    )

                    painter.setPen(
                        QColor("#e2e8f0")
                        if is_today
                        else QColor("#f8fafc") if not is_weekend else QColor("#64748b")
                    )
                    painter.setFont(
                        QFont(
                            "Segoe UI",
                            11,
                            QFont.Weight.Bold if is_today else QFont.Weight.Normal,
                        )
                    )
                    painter.drawText(
                        x,
                        14,
                        self.pixels_per_day,
                        20,
                        Qt.AlignmentFlag.AlignCenter,
                        f"{day.day()}",
                    )

                    if day.day() == 1 or i == 0:
                        painter.setPen(QColor("#818cf8"))
                        painter.setFont(QFont("Segoe UI", 8))
                        painter.drawText(
                            x,
                            32,
                            self.pixels_per_day,
                            14,
                            Qt.AlignmentFlag.AlignCenter,
                            months[day.month() - 1],
                        )
            else:
                # Dar görünüm - sadece gün
                painter.setPen(
                    QColor("#f87171")
                    if is_holiday
                    else QColor("#f8fafc") if not is_weekend else QColor("#64748b")
                )
                painter.setFont(QFont("Segoe UI", 9))
                painter.drawText(
                    x,
                    0,
                    self.pixels_per_day,
                    self.height(),
                    Qt.AlignmentFlag.AlignCenter,
                    f"{day.day()}",
                )


class MachineRow(QFrame):
    """Makine satırı - Sol etiket + Gantt alanı"""

    work_order_clicked = pyqtSignal(int)

    def __init__(
        self,
        station_id: int,
        station_code: str,
        station_name: str,
        station_type: str,
        capacity: float,
        parent=None,
    ):
        super().__init__(parent)
        self.station_id = station_id
        self.station_code = station_code
        self.station_name = station_name
        self.station_type = station_type
        self.capacity = capacity
        self.operations = []
        self.holidays = []

        self.setFixedHeight(52)

    def set_operations(
        self,
        operations: list,
        period_start: datetime,
        period_days: int,
        pixels_per_day: int,
        holidays: list = None,
    ):
        """Operasyonları ayarla ve çubukları oluştur"""
        self.operations = operations
        self.holidays = holidays or []
        self._build_ui(period_start, period_days, pixels_per_day)

    def _build_ui(self, period_start: datetime, period_days: int, pixels_per_day: int):
        if self.layout():
            QWidget().setLayout(self.layout())

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sol etiket (180px sabit)
        label_frame = QFrame()
        label_frame.setFixedWidth(180)
        label_layout = QVBoxLayout(label_frame)
        label_layout.setContentsMargins(12, 6, 12, 6)
        label_layout.setSpacing(2)

        type_icons = {
            "machine": "⚙️",
            "workstation": "🔧",
            "assembly": "🏭",
            "manual": "👷",
        }
        icon = type_icons.get(self.station_type, "⚙️")

        code_label = QLabel(f"{icon} {self.station_code}")
        label_layout.addWidget(code_label)

        name_label = QLabel(self.station_name[:22])
        label_layout.addWidget(name_label)

        layout.addWidget(label_frame)

        # Gantt bar alanı
        bar_area = QWidget()
        bar_area.setMinimumWidth(period_days * pixels_per_day)

        # Holiday set'i
        holiday_dates = {h[0] for h in self.holidays}

        # Arka plan çiz (hafta sonları ve tatiller)
        period_end = period_start + timedelta(days=period_days)

        status_colors = {
            "draft": "#64748b",
            "planned": "#3b82f6",
            "released": "#8b5cf6",
            "in_progress": "#f59e0b",
            "completed": "#10b981",
            "closed": "#475569",
            "pending": "#64748b",
        }

        status_names = {
            "draft": "Taslak",
            "planned": "Planlandı",
            "released": "Serbest",
            "in_progress": "Üretimde",
            "completed": "Tamamlandı",
            "closed": "Kapatıldı",
            "pending": "Bekliyor",
        }

        for op in self.operations:
            op_start = op.get("start_time")
            op_end = op.get("end_time")

            if not op_start or not op_end:
                continue

            if not isinstance(op_start, datetime):
                op_start = datetime.combine(op_start, datetime.min.time())
            if not isinstance(op_end, datetime):
                op_end = datetime.combine(op_end, datetime.min.time())

            if op_start >= period_end or op_end <= period_start:
                continue

            # Görünür kısmı hesapla
            visible_start = max(op_start, period_start)
            visible_end = min(op_end, period_end)

            # Pozisyon hesapla
            start_offset = (visible_start - period_start).total_seconds() / 86400
            duration_days = (visible_end - visible_start).total_seconds() / 86400

            x = int(start_offset * pixels_per_day)
            width = max(int(duration_days * pixels_per_day), 20)

            # Süre hesapla
            total_hours = (op_end - op_start).total_seconds() / 3600

            status = op.get("status", "planned")
            color = status_colors.get(status, "#3b82f6")
            status_name = status_names.get(status, status)

            bar = GanttBar(
                wo_id=op.get("work_order_id", 0),
                order_no=op.get("order_no", ""),
                item_name=op.get("item_name", ""),
                operation_name=op.get("operation_name", ""),
                progress=float(op.get("progress", 0) or 0),
                status=status_name,
                color=color,
                duration_hours=total_hours,
                parent=bar_area,
            )
            bar.clicked.connect(self.work_order_clicked.emit)
            bar.setGeometry(x, 8, width, 36)
            bar.show()

        layout.addWidget(bar_area)

    def paintEvent(self, event):
        super().paintEvent(event)

        # Hafta sonu ve tatil arkaplanlarını çiz
        if not hasattr(self, "_period_info"):
            return

        painter = QPainter(self)
        period_start, period_days, pixels_per_day = self._period_info
        holiday_dates = {h[0] for h in self.holidays}

        for i in range(period_days):
            x = 180 + i * pixels_per_day
            day = period_start + timedelta(days=i)
            day_date = day.date() if isinstance(day, datetime) else day

            is_weekend = day_date.weekday() >= 5
            is_holiday = day_date in holiday_dates

            if is_holiday:
                painter.fillRect(
                    x, 0, pixels_per_day, self.height(), QColor(127, 29, 29, 60)
                )  # red-900/60
            elif is_weekend:
                painter.fillRect(
                    x, 0, pixels_per_day, self.height(), QColor(15, 23, 42, 120)
                )  # slate-950/120


class ProductionPlanningPage(QWidget):
    """Üretim Planlama Sayfası - Takvim Entegrasyonlu"""

    page_title = "Üretim Planlama"

    work_order_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.work_stations = []
        self.operations = []
        self.holidays = []  # [(date, name, is_half_day), ...]

        self.current_date = QDate.currentDate()
        self.view_days = 14
        self.pixels_per_day = 60

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("📅 Üretim Planlama")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Navigasyon
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(8)

        prev_btn = QPushButton("◀")
        prev_btn.setFixedSize(32, 32)
        prev_btn.clicked.connect(self._prev_period)
        nav_layout.addWidget(prev_btn)

        today_btn = QPushButton("Bugün")
        today_btn.clicked.connect(self._go_today)
        nav_layout.addWidget(today_btn)

        next_btn = QPushButton("▶")
        next_btn.setFixedSize(32, 32)
        next_btn.clicked.connect(self._next_period)
        nav_layout.addWidget(next_btn)

        self.period_label = QLabel("")
        nav_layout.addWidget(self.period_label)

        header_layout.addLayout(nav_layout)

        # Görünüm seçici
        header_layout.addSpacing(16)

        view_label = QLabel("Görünüm:")
        header_layout.addWidget(view_label)

        self.view_combo = QComboBox()
        self.view_combo.addItem("1 Hafta", 7)
        self.view_combo.addItem("2 Hafta", 14)
        self.view_combo.addItem("1 Ay", 30)
        self.view_combo.addItem("2 Ay", 60)
        self.view_combo.setCurrentIndex(1)
        self.view_combo.currentIndexChanged.connect(self._on_view_changed)
        header_layout.addWidget(self.view_combo)

        # Zoom
        header_layout.addSpacing(8)
        zoom_label = QLabel("Zoom:")
        header_layout.addWidget(zoom_label)

        self.zoom_combo = QComboBox()
        self.zoom_combo.addItem("Küçük", 30)
        self.zoom_combo.addItem("Normal", 60)
        self.zoom_combo.addItem("Büyük", 90)
        self.zoom_combo.setCurrentIndex(1)
        self.zoom_combo.currentIndexChanged.connect(self._on_zoom_changed)
        header_layout.addWidget(self.zoom_combo)

        layout.addLayout(header_layout)

        # Bilgi kartları
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        self.machines_card = self._create_stat_card(
            "🏭", "Aktif Makine", "0", "#6366f1"
        )
        cards_layout.addWidget(self.machines_card)

        self.planned_card = self._create_stat_card("📋", "Planlanan", "0", "#3b82f6")
        cards_layout.addWidget(self.planned_card)

        self.in_progress_card = self._create_stat_card("⚡", "Üretimde", "0", "#f59e0b")
        cards_layout.addWidget(self.in_progress_card)

        self.delayed_card = self._create_stat_card("⚠️", "Geciken", "0", "#ef4444")
        cards_layout.addWidget(self.delayed_card)

        self.utilization_card = self._create_stat_card(
            "📊", "Kapasite", "%0", "#10b981"
        )
        cards_layout.addWidget(self.utilization_card)

        # Tatil kartı
        self.holiday_card = self._create_stat_card("🎉", "Tatil", "0 gün", "#a855f7")
        cards_layout.addWidget(self.holiday_card)

        cards_layout.addStretch()

        layout.addLayout(cards_layout)

        # Gantt alanı
        gantt_frame = QFrame()
        gantt_layout = QVBoxLayout(gantt_frame)
        gantt_layout.setContentsMargins(0, 0, 0, 0)
        gantt_layout.setSpacing(0)

        # Zaman çizelgesi header
        self.timeline_header = TimelineHeader(
            self.current_date, self.view_days, self.pixels_per_day, self.holidays
        )
        gantt_layout.addWidget(self.timeline_header)

        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        # Gantt içerik alanı
        self.gantt_content = QWidget()
        self.gantt_content_layout = QVBoxLayout(self.gantt_content)
        self.gantt_content_layout.setContentsMargins(0, 0, 0, 0)
        self.gantt_content_layout.setSpacing(0)

        self.scroll_area.setWidget(self.gantt_content)
        gantt_layout.addWidget(self.scroll_area)

        layout.addWidget(gantt_frame)

        # Alt bilgi
        footer_layout = QHBoxLayout()

        # Lejant
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(16)

        legend_items = [
            ("🎉 Tatil", "#7f1d1d"),
            ("📋 Planlandı", "#3b82f6"),
            ("🔓 Serbest", "#8b5cf6"),
            ("⚡ Üretimde", "#f59e0b"),
            ("✅ Tamamlandı", "#10b981"),
        ]

        for text, color in legend_items:
            item = QLabel(text)
            legend_layout.addWidget(item)

        footer_layout.addLayout(legend_layout)
        footer_layout.addStretch()

        self.info_label = QLabel("")
        footer_layout.addWidget(self.info_label)

        layout.addLayout(footer_layout)

        self._update_period_label()

    def _create_stat_card(
        self, icon: str, title: str, value: str, color: str
    ) -> MiniStatCard:
        """Dashboard tarzı istatistik kartı"""
        return MiniStatCard(f"{icon} {title}", value, color)

    def _update_card(self, card: MiniStatCard, value: str):
        """Kart değerini güncelle"""
        card.update_value(value)

    def _update_period_label(self):
        start = self.current_date
        end = start.addDays(self.view_days - 1)

        months = [
            "Oca",
            "Şub",
            "Mar",
            "Nis",
            "May",
            "Haz",
            "Tem",
            "Ağu",
            "Eyl",
            "Eki",
            "Kas",
            "Ara",
        ]

        if start.month() == end.month():
            text = (
                f"{start.day()} - {end.day()} {months[start.month()-1]} {start.year()}"
            )
        else:
            text = f"{start.day()} {months[start.month()-1]} - {end.day()} {months[end.month()-1]}"

        self.period_label.setText(text)

    def _prev_period(self):
        self.current_date = self.current_date.addDays(-self.view_days)
        self._refresh_view()

    def _next_period(self):
        self.current_date = self.current_date.addDays(self.view_days)
        self._refresh_view()

    def _go_today(self):
        self.current_date = QDate.currentDate()
        self._refresh_view()

    def _on_view_changed(self):
        self.view_days = self.view_combo.currentData()
        self._refresh_view()

    def _on_zoom_changed(self):
        self.pixels_per_day = self.zoom_combo.currentData()
        self._refresh_view()

    def _refresh_view(self):
        self._update_period_label()

        # Timeline header'ı yeniden oluştur
        self.timeline_header.deleteLater()
        self.timeline_header = TimelineHeader(
            self.current_date, self.view_days, self.pixels_per_day, self.holidays
        )

        gantt_frame = self.scroll_area.parent()
        if gantt_frame and gantt_frame.layout():
            gantt_frame.layout().insertWidget(0, self.timeline_header)

        self._build_gantt()
        self._update_stats()

    def set_holidays(self, holidays: list):
        """
        Tatil listesini ayarla
        holidays: [{"date": date, "name": str, "is_half_day": bool}, ...]
        """
        self.holidays = []
        for h in holidays:
            hdate = h.get("date")
            if hdate:
                self.holidays.append(
                    (hdate, h.get("name", ""), h.get("is_half_day", False))
                )

    def load_data(self, work_stations: list, operations: list, holidays: list = None):
        """
        Veri yükle

        work_stations: [{"id", "code", "name", "station_type", "capacity_per_hour"}, ...]
        operations: [{"work_order_id", "order_no", "item_name", "work_station_id",
                      "operation_name", "start_time", "end_time", "status", "progress"}, ...]
        holidays: [{"date": date, "name": str, "is_half_day": bool}, ...]
        """
        self.work_stations = work_stations
        self.operations = operations

        if holidays:
            self.set_holidays(holidays)

        self._refresh_view()

    def _update_stats(self):
        """İstatistikleri güncelle"""
        period_start = datetime(
            self.current_date.year(), self.current_date.month(), self.current_date.day()
        )
        period_end = period_start + timedelta(days=self.view_days)

        active_machines = set()
        planned_count = 0
        in_progress_count = 0
        delayed_count = 0
        total_hours = 0

        now = datetime.now()

        # Dönemdeki tatil sayısı
        holiday_dates = {h[0] for h in self.holidays}
        holiday_count = 0

        for i in range(self.view_days):
            check_date = (period_start + timedelta(days=i)).date()
            if check_date in holiday_dates:
                holiday_count += 1

        for op in self.operations:
            start_time = op.get("start_time")
            end_time = op.get("end_time")
            status = op.get("status", "planned")

            if not start_time or not end_time:
                continue

            if not isinstance(start_time, datetime):
                start_time = datetime.combine(start_time, datetime.min.time())
            if not isinstance(end_time, datetime):
                end_time = datetime.combine(end_time, datetime.min.time())

            if start_time < period_end and end_time > period_start:
                ws_id = op.get("work_station_id")
                if ws_id:
                    active_machines.add(ws_id)

                if status in ["planned", "released"]:
                    planned_count += 1
                elif status == "in_progress":
                    in_progress_count += 1

                if status in ["planned", "released", "in_progress"] and end_time < now:
                    delayed_count += 1

                duration = (
                    min(end_time, period_end) - max(start_time, period_start)
                ).total_seconds() / 3600
                total_hours += max(0, duration)

        self._update_card(self.machines_card, str(len(active_machines)))
        self._update_card(self.planned_card, str(planned_count))
        self._update_card(self.in_progress_card, str(in_progress_count))
        self._update_card(self.delayed_card, str(delayed_count))
        self._update_card(self.holiday_card, f"{holiday_count} gün")

        # Kapasite kullanımı (tatilleri çıkar)
        working_days = self.view_days - holiday_count
        # Hafta sonlarını da çıkar
        for i in range(self.view_days):
            check_date = (period_start + timedelta(days=i)).date()
            if check_date.weekday() >= 5 and check_date not in holiday_dates:
                working_days -= 1

        total_capacity = len(self.work_stations) * max(working_days, 1) * 8
        utilization = (
            int(total_hours / total_capacity * 100) if total_capacity > 0 else 0
        )
        self._update_card(self.utilization_card, f"%{min(100, utilization)}")

        self.info_label.setText(
            f"{len(self.work_stations)} makine, {len(self.operations)} operasyon, {working_days} iş günü"
        )

    def _build_gantt(self):
        """Gantt satırlarını oluştur"""
        while self.gantt_content_layout.count():
            child = self.gantt_content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self.work_stations:
            empty_label = QLabel("Henüz iş istasyonu tanımlanmamış")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.gantt_content_layout.addWidget(empty_label)
            return

        period_start = datetime(
            self.current_date.year(), self.current_date.month(), self.current_date.day()
        )

        ops_by_station = {}
        for op in self.operations:
            ws_id = op.get("work_station_id")
            if ws_id:
                if ws_id not in ops_by_station:
                    ops_by_station[ws_id] = []
                ops_by_station[ws_id].append(op)

        for ws in self.work_stations:
            ws_id = ws.get("id")

            row = MachineRow(
                station_id=ws_id,
                station_code=ws.get("code", ""),
                station_name=ws.get("name", ""),
                station_type=ws.get("station_type", "machine"),
                capacity=float(ws.get("capacity_per_hour", 0) or 0),
            )
            row.work_order_clicked.connect(self.work_order_clicked.emit)

            station_ops = ops_by_station.get(ws_id, [])
            row.set_operations(
                station_ops,
                period_start,
                self.view_days,
                self.pixels_per_day,
                self.holidays,
            )

            self.gantt_content_layout.addWidget(row)

        self.gantt_content_layout.addStretch()
        self.gantt_content.setMinimumWidth(180 + self.view_days * self.pixels_per_day)
