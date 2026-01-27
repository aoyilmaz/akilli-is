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
    QApplication,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QRect, QSize, QMimeData, QTimer
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QLinearGradient, QDrag
from ui.components.stat_cards import MiniStatCard
from config.icons import ICONS


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
        operation_id: int = None,
        parent=None,
    ):
        super().__init__(parent)
        self.wo_id = wo_id
        self.operation_id = operation_id
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

        # Drag state başlangıç değerleri
        self._drag_active = False
        self.drag_start_position = None

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

        # Arka plan (Açık Renk - Bekleyen Kısım)
        bg_color = QColor(self.color)
        bg_color.setAlpha(80)  # Daha açık renk
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(self.color.darker(120), 1))
        painter.drawRoundedRect(rect.adjusted(1, 2, -1, -2), 4, 4)

        # İlerleme (Koyu Renk - Tamamlanan Kısım)
        if self.progress > 0:
            progress_width = int((rect.width() - 2) * min(self.progress, 100) / 100)
            if progress_width > 0:
                # Koyu kısım için gradient
                done_gradient = QLinearGradient(0, 0, 0, rect.height())
                done_color = QColor(self.color)
                done_color.setAlpha(255)
                done_gradient.setColorAt(0, done_color.lighter(120))
                done_gradient.setColorAt(1, done_color.darker(110))

                painter.setBrush(QBrush(done_gradient))
                painter.setPen(Qt.PenStyle.NoPen)
                # İlerleme çubuğunu çiz
                progress_rect = QRect(1, 2, progress_width, rect.height() - 4)
                painter.drawRoundedRect(progress_rect, 4, 4)

        # Metin (Yüzde ve Bilgi)
        painter.setPen(QPen(QColor("#ffffff")))
        font = QFont("Segoe UI", 8)
        font.setBold(True)
        painter.setFont(font)

        # Merkeze Yüzde Yaz (%)
        if rect.width() > 40:
            painter.drawText(
                rect, Qt.AlignmentFlag.AlignCenter, f"%{self.progress:.0f}"
            )

        # Sola Sipariş No Yaz
        text = f"{self.order_no}"
        if rect.width() > 100:
            painter.drawText(
                rect.adjusted(8, 0, -8, 0),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                text,
            )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()
            self._drag_active = False  # Drag başladı mı kontrolü

    def mouseReleaseEvent(self, event):
        # Eğer sürükleme olmadıysa tıklama kabul et
        if not self._drag_active and event.button() == Qt.MouseButton.LeftButton:
            # Tıklama mesafesi kontrolü (hafif oynamalar için)
            if self.drag_start_position is not None:
                if (event.pos() - self.drag_start_position).manhattanLength() < 5:
                    self.clicked.emit(self.wo_id)
        # Drag state'i sıfırla
        self._drag_active = False

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if self.drag_start_position is None:
            return
        if (
            event.pos() - self.drag_start_position
        ).manhattanLength() < QApplication.startDragDistance():
            return

        # Drag başladı olarak işaretle
        self._drag_active = True

        drag = QDrag(self)
        mime_data = QMimeData()

        # Verileri taşı: wo_id, duration_hours, start_offset_x, operation_id
        mime_data.setText(
            f"{self.wo_id}|{self.duration_hours}|{self.drag_start_position.x()}|{self.operation_id}"
        )

        drag.setMimeData(mime_data)
        drag.setPixmap(self.grab())
        drag.setHotSpot(event.pos())

        drag.exec(Qt.DropAction.MoveAction)

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
        self.holidays = holidays or []

        # Holiday'leri set olarak tut (hızlı lookup için)
        self.holiday_dates = {h[0]: (h[1], h[2]) for h in self.holidays}

        self.setFixedHeight(50)
        self.setMinimumWidth(num_days * pixels_per_day)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        left_margin = 0  # Artık sol panel yok

        # Arka plan - Global tema renkleri
        painter.fillRect(0, 0, self.width(), self.height(), QColor("#252526"))

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


class MachineHeaderWidget(QFrame):
    """Sol panel için iş istasyonu başlığı"""

    def __init__(
        self,
        station_code: str,
        station_name: str,
        station_type: str,
        parent=None,
    ):
        super().__init__(parent)
        self.setFixedHeight(52)  # MachineRow ile aynı yükseklik
        self.setFixedWidth(180)  # Sabit genişlik for sol panel

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(2)

        type_icons = {
            "machine": "⚙️",
            "workstation": "🔧",
            "assembly": "🏭",
            "manual": "👷",
            "unassigned": "❓",
        }
        icon = type_icons.get(station_type, "⚙️")

        # Kod
        self.code_label = QLabel(f"{icon} {station_code}")
        self.code_label.setStyleSheet("font-weight: bold; color: #e2e8f0;")
        layout.addWidget(self.code_label)

        # İsim
        self.name_label = QLabel(station_name[:22])
        self.name_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(self.name_label)

        # Alt çizgi (Gantt satırlarıyla hizalamak için)
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Plain)
        line.setStyleSheet("background-color: #334155;")
        line.setFixedHeight(1)
        # Layout içine alt çizgiyi eklemek yerine, paintEvent ile çizmek daha iyi olabilir
        # ama şimdilik layout ile gidelim veya border kullanalım.
        self.setStyleSheet(".MachineHeaderWidget { border-bottom: 1px solid #334155; }")


class MachineRow(QFrame):
    """Makine satırı - Sadece Gantt alanı (Sağ taraf)"""

    work_order_clicked = pyqtSignal(int)
    operation_moved = pyqtSignal(
        int, object, int, int
    )  # wo_id, new_start_time, operation_id, new_machine_id
    cascade_requested = pyqtSignal(
        int, str, object, int
    )  # op_id, mode, new_start, new_station_id

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

        self.holidays = []

        self.setFixedHeight(52)
        self.setAcceptDrops(True)

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
                operation_id=op.get("operation_id"),
                parent=bar_area,
            )
            bar.clicked.connect(self.work_order_clicked.emit)
            bar.setGeometry(x, 8, width, 36)
            bar.show()

        layout.addWidget(bar_area)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        try:
            data = event.mimeData().text().split("|")
            wo_id = int(data[0])
            duration_hours = float(data[1])
            click_offset = int(data[2])
            operation_id = int(data[3]) if data[3] != "None" else None

            drop_x = event.position().x()
            usage_area_start = 0  # Artık sol panel yok, offset 0

            relative_x = drop_x - usage_area_start - click_offset

            # Zamanı hesapla
            if not hasattr(self, "_period_info"):
                return

            period_start, period_days, pixels_per_day = self._period_info

            days_offset = relative_x / pixels_per_day
            days_offset = max(0, days_offset)  # Negatif olmamalı

            new_start_time = period_start + timedelta(days=days_offset)

            # Operasyon ID varsa cascade sinyali gönder (APS entegrasyonu)
            if operation_id:
                self.cascade_requested.emit(
                    operation_id, "validate", new_start_time, self.station_id
                )

            # Sinyal gönder
            self.operation_moved.emit(
                wo_id, new_start_time, operation_id, self.station_id
            )
            event.accept()

        except Exception as e:
            print(f"Drop hatası: {e}")
            event.ignore()

    def paintEvent(self, event):
        super().paintEvent(event)

        # Hafta sonu ve tatil arkaplanlarını çiz
        if not hasattr(self, "_period_info"):
            return

        painter = QPainter(self)
        period_start, period_days, pixels_per_day = self._period_info
        holiday_dates = {h[0] for h in self.holidays}

        for i in range(period_days):
            x = 0 + i * pixels_per_day  # Offset 0
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
    """Üretim Planlama Sayfası - Takvim Entegrasyonlu + APS Cascade Desteği"""

    page_title = "Üretim Planlama"

    work_order_clicked = pyqtSignal(int)
    operation_moved = pyqtSignal(int, object, int, int)
    refresh_requested = pyqtSignal()
    cascade_completed = pyqtSignal(int, list)  # operation_id, affected_operations

    def __init__(self, parent=None):
        super().__init__(parent)
        self.work_stations = []
        self.operations = []
        self.holidays = []  # [(date, name, is_half_day), ...]
        self.aps_service = None  # APS servisi (dışarıdan set edilir)

        self.current_date = QDate.currentDate()
        self.view_days = 14
        self.pixels_per_day = 60

        self.pixels_per_day = 60

        # Otomatik yenileme (30 saniye)
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.refresh_requested.emit)
        self.auto_refresh_timer.start(30000)

        self.setup_ui()

    def set_aps_service(self, aps_service):
        """APS servisini ayarla (cascade işlemleri için)."""
        self.aps_service = aps_service

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # === Header - PageHeader kullanarak ===
        from ui.components.page_header import PageHeader

        self.header = PageHeader(
            title="Üretim Planlama",
            icon=ICONS.PLANNING,
            show_search=False,
            show_refresh=False,  # En sağa almak için manuel ekleyeceğiz
            show_add=False,
            parent=self,
        )

        h_layout = self.header.header_layout()

        # Navigasyon
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(8)

        prev_btn = QPushButton("◀")
        prev_btn.setFixedSize(32, 36)
        prev_btn.clicked.connect(self._prev_period)
        nav_layout.addWidget(prev_btn)

        today_btn = QPushButton("Bugün")
        today_btn.setFixedHeight(36)
        today_btn.clicked.connect(self._go_today)
        nav_layout.addWidget(today_btn)

        next_btn = QPushButton("▶")
        next_btn.setFixedSize(32, 36)
        next_btn.clicked.connect(self._next_period)
        nav_layout.addWidget(next_btn)

        self.period_label = QLabel("")
        nav_layout.addWidget(self.period_label)

        h_layout.addLayout(nav_layout)

        # Görünüm seçici
        h_layout.addSpacing(16)

        view_label = QLabel("Görünüm:")
        h_layout.addWidget(view_label)

        self.view_combo = QComboBox()
        self.view_combo.addItem("1 Hafta", 7)
        self.view_combo.addItem("2 Hafta", 14)
        self.view_combo.addItem("3 Hafta", 21)
        self.view_combo.addItem("1 Ay", 30)
        self.view_combo.addItem("2 Ay", 60)
        self.view_combo.setCurrentIndex(1)
        self.view_combo.setFixedHeight(36)
        self.view_combo.currentIndexChanged.connect(self._on_view_changed)
        h_layout.addWidget(self.view_combo)

        # Zoom
        h_layout.addSpacing(8)
        zoom_label = QLabel("Zoom:")
        h_layout.addWidget(zoom_label)

        self.zoom_combo = QComboBox()
        self.zoom_combo.addItem("Küçük", 30)
        self.zoom_combo.addItem("Normal", 60)
        self.zoom_combo.addItem("Büyük", 90)
        self.zoom_combo.setCurrentIndex(1)
        self.zoom_combo.setFixedHeight(36)
        self.zoom_combo.currentIndexChanged.connect(self._on_zoom_changed)
        h_layout.addWidget(self.zoom_combo)

        # Refresh butonu (KALDIRILDI - Otomatik yenileme eklendi)
        # h_layout.addSpacing(8)
        # refresh_btn = QPushButton("🔄 Yenile")
        # refresh_btn.setProperty("class", "btn-refresh")
        # refresh_btn.setFixedHeight(36)
        # refresh_btn.clicked.connect(self.refresh_requested.emit)
        # h_layout.addWidget(refresh_btn)

        # Refresh sinyali (Header'dan gelmeyecek artık ama yine de dursun)
        self.header.refresh_clicked.connect(self.refresh_requested.emit)

        layout.addWidget(self.header)

        # Bilgi kartları
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        self.machines_card = self._create_stat_card(
            ICONS.MACHINE, "Aktif Makine", "0", "primary"
        )
        cards_layout.addWidget(self.machines_card)

        self.planned_card = self._create_stat_card(
            ICONS.PLANNING, "Planlanan", "0", "info"
        )
        cards_layout.addWidget(self.planned_card)

        self.in_progress_card = self._create_stat_card(
            ICONS.OPERATION, "Üretimde", "0", "warning"
        )
        cards_layout.addWidget(self.in_progress_card)

        self.delayed_card = self._create_stat_card(
            ICONS.WARNING, "Geciken", "0", "error"
        )
        cards_layout.addWidget(self.delayed_card)

        self.utilization_card = self._create_stat_card(
            ICONS.TREND_UP, "Kapasite", "%0", "success"
        )
        cards_layout.addWidget(self.utilization_card)

        # Tatil kartı
        self.holiday_card = self._create_stat_card(
            ICONS.CALENDAR, "Tatil", "0 gün", "info"
        )
        cards_layout.addWidget(self.holiday_card)

        cards_layout.addStretch()

        layout.addLayout(cards_layout)

        # Gantt Grid Layout (2x2)
        gantt_grid = QGridLayout()
        gantt_grid.setSpacing(0)
        gantt_grid.setContentsMargins(0, 0, 0, 0)

        # 1. Sol Üst: Sabit Başlık
        tl_label = QLabel("İş İstasyonu")
        tl_label.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        )
        tl_label.setStyleSheet(
            "background-color: #1e1e1e; color: #64748b; font-weight: bold; "
            "padding-left: 10px; border-bottom: 1px solid #334155;"
        )
        tl_label.setFixedSize(180, 50)
        gantt_grid.addWidget(tl_label, 0, 0)

        # 2. Sağ Üst: Timeline Header (Yatay Scroll - Bar Gizli)
        self.header_scroll = QScrollArea()
        self.header_scroll.setWidgetResizable(True)
        self.header_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.header_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.header_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.header_scroll.setFixedHeight(50)
        # Widget _refresh_view içinde atanacak
        gantt_grid.addWidget(self.header_scroll, 0, 1)

        # 3. Sol Alt: İsimler (Dikey Scroll - Bar Gizli)
        self.names_scroll = QScrollArea()
        self.names_scroll.setWidgetResizable(True)
        self.names_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.names_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.names_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.names_scroll.setFixedWidth(180)

        self.names_content = QWidget()
        self.names_layout = QVBoxLayout(self.names_content)
        self.names_layout.setContentsMargins(0, 0, 0, 0)
        self.names_layout.setSpacing(0)
        self.names_scroll.setWidget(self.names_content)
        gantt_grid.addWidget(self.names_scroll, 1, 0)

        # 4. Sağ Alt: Gantt Alanı (Tam Scroll)
        self.gantt_scroll = QScrollArea()
        self.gantt_scroll.setWidgetResizable(True)
        self.gantt_scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.gantt_content = QWidget()
        self.gantt_content_layout = QVBoxLayout(self.gantt_content)
        self.gantt_content_layout.setContentsMargins(0, 0, 0, 0)
        self.gantt_content_layout.setSpacing(0)
        self.gantt_scroll.setWidget(self.gantt_content)
        gantt_grid.addWidget(self.gantt_scroll, 1, 1)

        # Scroll Senkronizasyonu
        self.gantt_scroll.horizontalScrollBar().valueChanged.connect(
            self.header_scroll.horizontalScrollBar().setValue
        )
        self.gantt_scroll.verticalScrollBar().valueChanged.connect(
            self.names_scroll.verticalScrollBar().setValue
        )

        layout.addLayout(gantt_grid)

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
        return MiniStatCard(title, value, color, orientation="horizontal", icon=icon)

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
        if hasattr(self, "timeline_header"):
            self.timeline_header.deleteLater()

        self.timeline_header = TimelineHeader(
            self.current_date, self.view_days, self.pixels_per_day, self.holidays
        )
        self.header_scroll.setWidget(self.timeline_header)

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
        # Her iki layout'u temizle
        while self.gantt_content_layout.count():
            child = self.gantt_content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        while self.names_layout.count():
            child = self.names_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self.work_stations:
            # TODO: Boş durumu için daha iyi bir gösterim düşünülebilir
            # Şimdilik Names layout boş kalacak
            empty_label = QLabel("Henüz iş istasyonu tanımlanmamış")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.gantt_content_layout.addWidget(empty_label)
            return

        period_start = datetime(
            self.current_date.year(), self.current_date.month(), self.current_date.day()
        )

        ops_by_station = {}
        unassigned_ops = []  # İstasyon atanmamış operasyonlar

        for op in self.operations:
            ws_id = op.get("work_station_id")
            if ws_id:
                if ws_id not in ops_by_station:
                    ops_by_station[ws_id] = []
                ops_by_station[ws_id].append(op)
            else:
                # İstasyon atanmamış operasyonları ayrı topla
                unassigned_ops.append(op)

        for ws in self.work_stations:
            ws_id = ws.get("id")
            station_code = ws.get("code", "")
            station_name = ws.get("name", "")
            station_type = ws.get("station_type", "machine")

            # 1. İsim Widget'ı (Sol)
            header_widget = MachineHeaderWidget(
                station_code=station_code,
                station_name=station_name,
                station_type=station_type,
            )
            self.names_layout.addWidget(header_widget)

            # 2. Gantt Row Widget'ı (Sağ)
            row = MachineRow(
                station_id=ws_id,
                station_code=station_code,
                station_name=station_name,
                station_type=station_type,
                capacity=float(ws.get("capacity_per_hour", 0) or 0),
            )
            row.work_order_clicked.connect(self.work_order_clicked.emit)
            row.operation_moved.connect(self.operation_moved.emit)
            row.cascade_requested.connect(self._handle_cascade_request)

            station_ops = ops_by_station.get(ws_id, [])
            row.set_operations(
                station_ops,
                period_start,
                self.view_days,
                self.pixels_per_day,
                self.holidays,
            )

            self.gantt_content_layout.addWidget(row)

        # Atanmamış operasyonlar için özel satır
        if unassigned_ops:
            # Sol
            unassigned_header = MachineHeaderWidget(
                station_code="---",
                station_name="Atanmamış",
                station_type="unassigned",
            )
            self.names_layout.addWidget(unassigned_header)

            # Sağ
            unassigned_row = MachineRow(
                station_id=None,
                station_code="---",
                station_name="Atanmamış",
                station_type="unassigned",
                capacity=0,
            )
            unassigned_row.work_order_clicked.connect(self.work_order_clicked.emit)
            unassigned_row.operation_moved.connect(self.operation_moved.emit)
            unassigned_row.cascade_requested.connect(self._handle_cascade_request)

            unassigned_row.set_operations(
                unassigned_ops,
                period_start,
                self.view_days,
                self.pixels_per_day,
                self.holidays,
            )

            self.gantt_content_layout.addWidget(unassigned_row)

        self.gantt_content_layout.addStretch()
        self.names_layout.addStretch()

        # Genişlik ayarla
        self.gantt_content.setMinimumWidth(self.view_days * self.pixels_per_day)

    def _handle_cascade_request(
        self, operation_id: int, mode: str, new_start, new_station_id: int
    ):
        """
        APS cascade talebini işle.

        Args:
            operation_id: Taşınan operasyon ID
            mode: "validate" - önizleme için doğrulama
            new_start: Yeni başlangıç zamanı
            new_station_id: Yeni istasyon ID
        """
        if not self.aps_service:
            return

        if mode == "validate":
            # Taşımayı doğrula ve çakışmaları kontrol et
            validation = self.aps_service.validate_move(
                operation_id, new_start, new_station_id
            )

            if validation.get("conflicts"):
                # Çakışma var, diyalog göster
                from modules.production.views.move_conflict_dialog import (
                    MoveConflictDialog,
                )

                dialog = MoveConflictDialog(
                    operation_id=operation_id,
                    conflicts=validation.get("conflicts", []),
                    warnings=validation.get("warnings", []),
                    parent=self,
                )

                if dialog.exec():
                    resolution = dialog.get_resolution()

                    if resolution != MoveConflictDialog.RESOLUTION_CANCEL:
                        # Seçilen çözümle taşıma işlemini gerçekleştir
                        self._execute_cascade_move(
                            operation_id, new_start, new_station_id, resolution
                        )
                    else:
                        # İptal - görünümü yenile (eski konuma dön)
                        self.refresh_requested.emit()

    def _execute_cascade_move(
        self, operation_id: int, new_start, new_station_id: int, cascade_mode: str
    ):
        """
        Cascade moduna göre taşıma işlemini gerçekleştir.
        """
        if not self.aps_service:
            return

        try:
            result = self.aps_service.reschedule_operation(
                operation_id=operation_id,
                new_start=new_start,
                new_station_id=new_station_id,
                cascade_mode=cascade_mode,
            )

            if result.get("success"):
                affected = result.get("affected_operations", [])
                self.cascade_completed.emit(operation_id, affected)

                # Görünümü yenile
                self.refresh_requested.emit()

        except Exception as e:
            print(f"Cascade taşıma hatası: {e}")
            # Hata durumunda görünümü yenile
            self.refresh_requested.emit()
