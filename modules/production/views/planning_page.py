"""
Akıllı İş - Üretim Planlama Sayfası
MAKİNE BAZLI GANTT CHART
"""

from datetime import datetime, timedelta
from decimal import Decimal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QComboBox, QSizePolicy, QToolTip,
    QGridLayout, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QRect, QSize
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QLinearGradient


class GanttBar(QWidget):
    """Gantt çubuğu - İş emri operasyonu"""
    
    clicked = pyqtSignal(int)  # work_order_id
    
    def __init__(self, wo_id: int, order_no: str, item_name: str, 
                 operation_name: str, progress: float, status: str, 
                 color: str, duration_hours: float = 0, parent=None):
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
        
        # Çubuk genişliğine göre metin
        text = f"{self.order_no}"
        if rect.width() > 120:
            text = f"{self.order_no} - {self.item_name[:15]}"
        if rect.width() > 200:
            text = f"{self.order_no} - {self.item_name[:20]} ({self.duration_hours:.0f}h)"
            
        painter.drawText(rect.adjusted(8, 0, -8, -4), 
                        Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, 
                        text)
        
    def mousePressEvent(self, event):
        self.clicked.emit(self.wo_id)
        
    def sizeHint(self):
        return QSize(100, 36)


class MachineRow(QFrame):
    """Makine satırı - Sol etiket + Gantt alanı"""
    
    work_order_clicked = pyqtSignal(int)
    
    def __init__(self, station_id: int, station_code: str, station_name: str, 
                 station_type: str, capacity: float, parent=None):
        super().__init__(parent)
        self.station_id = station_id
        self.station_code = station_code
        self.station_name = station_name
        self.station_type = station_type
        self.capacity = capacity
        self.operations = []  # Bu makinedeki operasyonlar
        
        self.setFixedHeight(52)
        self.setStyleSheet("""
            MachineRow {
                background-color: transparent;
                border-bottom: 1px solid #334155;
            }
        """)
        
    def set_operations(self, operations: list, period_start: datetime, 
                       period_days: int, pixels_per_day: int):
        """Operasyonları ayarla ve çubukları oluştur"""
        self.operations = operations
        self._build_ui(period_start, period_days, pixels_per_day)
        
    def _build_ui(self, period_start: datetime, period_days: int, pixels_per_day: int):
        # Mevcut layout'u temizle
        if self.layout():
            QWidget().setLayout(self.layout())
            
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Sol etiket (180px sabit)
        label_frame = QFrame()
        label_frame.setFixedWidth(180)
        label_frame.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border-right: 2px solid #334155;
            }
        """)
        label_layout = QVBoxLayout(label_frame)
        label_layout.setContentsMargins(12, 6, 12, 6)
        label_layout.setSpacing(2)
        
        # Makine ikonu ve kodu
        type_icons = {
            "machine": "⚙️",
            "workstation": "🔧",
            "assembly": "🏭",
            "manual": "👷",
        }
        icon = type_icons.get(self.station_type, "⚙️")
        
        code_label = QLabel(f"{icon} {self.station_code}")
        code_label.setStyleSheet("color: #818cf8; font-weight: bold; font-size: 12px; background: transparent;")
        label_layout.addWidget(code_label)
        
        name_label = QLabel(self.station_name[:22])
        name_label.setStyleSheet("color: #94a3b8; font-size: 11px; background: transparent;")
        label_layout.addWidget(name_label)
        
        layout.addWidget(label_frame)
        
        # Gantt bar alanı
        bar_area = QWidget()
        bar_area.setStyleSheet("background: transparent;")
        bar_area.setMinimumWidth(period_days * pixels_per_day)
        
        # Operasyonları çiz
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
                
            # Datetime'a çevir
            if not isinstance(op_start, datetime):
                op_start = datetime.combine(op_start, datetime.min.time())
            if not isinstance(op_end, datetime):
                op_end = datetime.combine(op_end, datetime.min.time())
            
            # Bu dönemde görünür mü?
            if op_start >= period_end or op_end <= period_start:
                continue
            
            # Görünür kısmı hesapla
            visible_start = max(op_start, period_start)
            visible_end = min(op_end, period_end)
            
            # Pozisyon hesapla
            start_offset_days = (visible_start - period_start).total_seconds() / 86400
            duration_days = (visible_end - visible_start).total_seconds() / 86400
            
            x_pos = int(start_offset_days * pixels_per_day)
            width = max(40, int(duration_days * pixels_per_day) - 4)  # Min 40px
            
            # Süre hesapla (saat)
            total_duration = (op_end - op_start).total_seconds() / 3600
            
            # Gantt bar oluştur
            status = op.get("status", "planned")
            color = status_colors.get(status, "#3b82f6")
            
            bar = GanttBar(
                wo_id=op.get("work_order_id", 0),
                order_no=op.get("order_no", ""),
                item_name=op.get("item_name", ""),
                operation_name=op.get("operation_name", ""),
                progress=op.get("progress", 0),
                status=status_names.get(status, "?"),
                color=color,
                duration_hours=total_duration,
                parent=bar_area
            )
            bar.setGeometry(x_pos, 8, width, 36)
            bar.clicked.connect(self.work_order_clicked.emit)
            bar.show()
        
        layout.addWidget(bar_area)
        layout.addStretch()


class TimelineHeader(QWidget):
    """Zaman çizelgesi başlığı"""
    
    def __init__(self, start_date: QDate, days: int, pixels_per_day: int, parent=None):
        super().__init__(parent)
        self.start_date = start_date
        self.days = days
        self.pixels_per_day = pixels_per_day
        self.setFixedHeight(60)
        self.setMinimumWidth(180 + days * pixels_per_day)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Arka plan
        painter.fillRect(self.rect(), QColor("#1e293b"))
        
        today = QDate.currentDate()
        x_offset = 180  # Sol etiket alanı
        
        # Ay başlıkları için
        current_month = None
        month_start_x = x_offset
        months_tr = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                     "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        
        for i in range(self.days):
            date = self.start_date.addDays(i)
            x = x_offset + i * self.pixels_per_day
            
            is_today = date == today
            is_weekend = date.dayOfWeek() >= 6
            
            # Ay değişimi kontrolü
            if current_month != date.month():
                if current_month is not None:
                    # Önceki ay başlığını çiz
                    month_width = x - month_start_x
                    painter.setPen(QPen(QColor("#475569")))
                    painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                    month_text = f"{months_tr[current_month-1]}"
                    painter.drawText(QRect(month_start_x, 2, month_width, 20), 
                                   Qt.AlignmentFlag.AlignCenter, month_text)
                
                current_month = date.month()
                month_start_x = x
            
            # Gün arka planı
            if is_today:
                painter.fillRect(x, 22, self.pixels_per_day, 38, QColor("#6366f130"))
            elif is_weekend:
                painter.fillRect(x, 22, self.pixels_per_day, 38, QColor("#1e293b"))
            
            # Dikey çizgi
            painter.setPen(QPen(QColor("#334155"), 1))
            painter.drawLine(x, 22, x, 60)
            
            # Gün adı
            day_names = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
            day_name = day_names[date.dayOfWeek() - 1]
            
            painter.setFont(QFont("Segoe UI", 8))
            color = "#6366f1" if is_today else ("#64748b" if is_weekend else "#94a3b8")
            painter.setPen(QPen(QColor(color)))
            painter.drawText(QRect(x, 24, self.pixels_per_day, 16), 
                           Qt.AlignmentFlag.AlignCenter, day_name)
            
            # Gün numarası
            painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold if is_today else QFont.Weight.Normal))
            color = "#ffffff" if is_today else ("#64748b" if is_weekend else "#e2e8f0")
            painter.setPen(QPen(QColor(color)))
            painter.drawText(QRect(x, 38, self.pixels_per_day, 20), 
                           Qt.AlignmentFlag.AlignCenter, str(date.day()))
        
        # Son ay başlığı
        if current_month is not None:
            month_width = x_offset + self.days * self.pixels_per_day - month_start_x
            painter.setPen(QPen(QColor("#475569")))
            painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            month_text = f"{months_tr[current_month-1]}"
            painter.drawText(QRect(month_start_x, 2, month_width, 20), 
                           Qt.AlignmentFlag.AlignCenter, month_text)
        
        # Sol etiket alanı başlığı
        painter.fillRect(0, 0, 180, 60, QColor("#0f172a"))
        painter.setPen(QPen(QColor("#94a3b8")))
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        painter.drawText(QRect(0, 0, 180, 60), Qt.AlignmentFlag.AlignCenter, "İş İstasyonları")
        
        # Sağ kenarlık
        painter.setPen(QPen(QColor("#334155"), 2))
        painter.drawLine(180, 0, 180, 60)


class ProductionPlanningPage(QWidget):
    """Üretim Planlama sayfası - Makine Bazlı Gantt"""
    
    page_title = "Üretim Planlama"
    
    work_order_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_date = QDate.currentDate()
        self.view_days = 14
        self.pixels_per_day = 80  # Her gün için piksel
        self.work_stations = []
        self.operations = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # === Başlık ===
        header_layout = QHBoxLayout()
        
        title_layout = QVBoxLayout()
        title = QLabel("🏭 Üretim Planlama")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f8fafc;")
        subtitle = QLabel("Makinelere göre iş emirlerini planlayın ve takip edin")
        subtitle.setStyleSheet("font-size: 14px; color: #94a3b8;")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addLayout(title_layout)
        
        header_layout.addStretch()
        
        # Navigasyon
        prev_btn = QPushButton("◀")
        prev_btn.setFixedSize(36, 36)
        prev_btn.setStyleSheet(self._nav_btn_style())
        prev_btn.clicked.connect(self._prev_period)
        header_layout.addWidget(prev_btn)
        
        self.period_label = QLabel("")
        self.period_label.setStyleSheet("color: #f8fafc; font-weight: 600; font-size: 14px; padding: 0 12px;")
        header_layout.addWidget(self.period_label)
        
        next_btn = QPushButton("▶")
        next_btn.setFixedSize(36, 36)
        next_btn.setStyleSheet(self._nav_btn_style())
        next_btn.clicked.connect(self._next_period)
        header_layout.addWidget(next_btn)
        
        today_btn = QPushButton("Bugün")
        today_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1; border: none; color: white;
                padding: 8px 16px; border-radius: 6px; font-weight: 600;
            }
            QPushButton:hover { background-color: #4f46e5; }
        """)
        today_btn.clicked.connect(self._go_today)
        header_layout.addWidget(today_btn)
        
        header_layout.addSpacing(16)
        
        # Görünüm seçimi
        view_label = QLabel("Görünüm:")
        view_label.setStyleSheet("color: #94a3b8;")
        header_layout.addWidget(view_label)
        
        self.view_combo = QComboBox()
        self.view_combo.addItem("1 Hafta", 7)
        self.view_combo.addItem("2 Hafta", 14)
        self.view_combo.addItem("3 Hafta", 21)
        self.view_combo.addItem("1 Ay", 30)
        self.view_combo.setCurrentIndex(1)
        self.view_combo.setStyleSheet(self._combo_style())
        self.view_combo.currentIndexChanged.connect(self._on_view_changed)
        header_layout.addWidget(self.view_combo)
        
        # Yakınlaştırma
        zoom_label = QLabel("Zoom:")
        zoom_label.setStyleSheet("color: #94a3b8; margin-left: 16px;")
        header_layout.addWidget(zoom_label)
        
        self.zoom_combo = QComboBox()
        self.zoom_combo.addItem("Küçük", 50)
        self.zoom_combo.addItem("Normal", 80)
        self.zoom_combo.addItem("Büyük", 120)
        self.zoom_combo.setCurrentIndex(1)
        self.zoom_combo.setStyleSheet(self._combo_style())
        self.zoom_combo.currentIndexChanged.connect(self._on_zoom_changed)
        header_layout.addWidget(self.zoom_combo)
        
        # Yenile
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.setStyleSheet(self._btn_style())
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # === Özet Kartlar ===
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)
        
        self.machines_card = self._create_card("⚙️ Aktif Makine", "0", "#6366f1")
        cards_layout.addWidget(self.machines_card)
        
        self.planned_card = self._create_card("📅 Planlanan İş", "0", "#3b82f6")
        cards_layout.addWidget(self.planned_card)
        
        self.in_progress_card = self._create_card("🔄 Üretimde", "0", "#f59e0b")
        cards_layout.addWidget(self.in_progress_card)
        
        self.utilization_card = self._create_card("📊 Kapasite", "%0", "#10b981")
        cards_layout.addWidget(self.utilization_card)
        
        self.delayed_card = self._create_card("⚠️ Geciken", "0", "#ef4444")
        cards_layout.addWidget(self.delayed_card)
        
        layout.addLayout(cards_layout)
        
        # === Gantt Chart Container ===
        gantt_container = QFrame()
        gantt_container.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 41, 59, 0.5);
                border: 1px solid #334155;
                border-radius: 12px;
            }
        """)
        gantt_main_layout = QVBoxLayout(gantt_container)
        gantt_main_layout.setContentsMargins(0, 0, 0, 0)
        gantt_main_layout.setSpacing(0)
        
        # Timeline header (ayrı scroll yok, sabit)
        self.timeline_header = TimelineHeader(self.current_date, self.view_days, self.pixels_per_day)
        self.timeline_header.setStyleSheet("border-top-left-radius: 12px; border-top-right-radius: 12px;")
        gantt_main_layout.addWidget(self.timeline_header)
        
        # Scroll area for machine rows
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                background: #1e293b; width: 12px; border-radius: 6px; margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: #475569; border-radius: 5px; min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background: #64748b; }
            QScrollBar:horizontal {
                background: #1e293b; height: 12px; border-radius: 6px; margin: 2px;
            }
            QScrollBar::handle:horizontal {
                background: #475569; border-radius: 5px; min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover { background: #64748b; }
            QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
        """)
        
        self.gantt_content = QWidget()
        self.gantt_content_layout = QVBoxLayout(self.gantt_content)
        self.gantt_content_layout.setContentsMargins(0, 0, 0, 0)
        self.gantt_content_layout.setSpacing(0)
        self.gantt_content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.gantt_content)
        gantt_main_layout.addWidget(self.scroll_area)
        
        layout.addWidget(gantt_container)
        
        # === Alt bilgi ===
        footer_layout = QHBoxLayout()
        
        # Lejant
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(16)
        
        legend_items = [
            ("Planlandı", "#3b82f6"),
            ("Serbest", "#8b5cf6"),
            ("Üretimde", "#f59e0b"),
            ("Tamamlandı", "#10b981"),
        ]
        
        for name, color in legend_items:
            item_layout = QHBoxLayout()
            item_layout.setSpacing(4)
            
            color_box = QLabel()
            color_box.setFixedSize(16, 16)
            color_box.setStyleSheet(f"background-color: {color}; border-radius: 3px;")
            item_layout.addWidget(color_box)
            
            text_label = QLabel(name)
            text_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
            item_layout.addWidget(text_label)
            
            legend_layout.addLayout(item_layout)
        
        footer_layout.addLayout(legend_layout)
        footer_layout.addStretch()
        
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #64748b; font-size: 12px;")
        footer_layout.addWidget(self.info_label)
        
        layout.addLayout(footer_layout)
        
        self._update_period_label()
        
    def _create_card(self, title: str, value: str, color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color}15;
                border: 1px solid {color}40;
                border-radius: 10px;
            }}
        """)
        card.setFixedHeight(70)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #94a3b8; font-size: 11px; background: transparent;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold; background: transparent;")
        layout.addWidget(value_label)
        
        return card
        
    def _update_card(self, card: QFrame, value: str):
        value_label = card.findChild(QLabel, "value")
        if value_label:
            value_label.setText(value)
    
    def _nav_btn_style(self):
        return """
            QPushButton {
                background-color: #1e293b; border: 1px solid #334155;
                color: #f8fafc; border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #334155; }
        """
        
    def _btn_style(self):
        return """
            QPushButton {
                background-color: #1e293b; border: 1px solid #334155;
                color: #f8fafc; padding: 8px 16px; border-radius: 6px;
            }
            QPushButton:hover { background-color: #334155; }
        """
        
    def _combo_style(self):
        return """
            QComboBox {
                background-color: #1e293b; border: 1px solid #334155;
                border-radius: 6px; padding: 6px 10px; color: #f8fafc; min-width: 90px;
            }
            QComboBox:hover { border-color: #475569; }
            QComboBox::drop-down { border: none; width: 20px; }
            QComboBox::down-arrow { image: none; border: none; }
            QComboBox QAbstractItemView {
                background-color: #1e293b; border: 1px solid #334155;
                color: #f8fafc; selection-background-color: #334155;
            }
        """
        
    def _update_period_label(self):
        start = self.current_date
        end = start.addDays(self.view_days - 1)
        
        months = ["Oca", "Şub", "Mar", "Nis", "May", "Haz",
                  "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
        
        if start.month() == end.month():
            text = f"{start.day()} - {end.day()} {months[start.month()-1]} {start.year()}"
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
        self.timeline_header = TimelineHeader(self.current_date, self.view_days, self.pixels_per_day)
        # Header'ı güncelle (layout'un ilk elemanını değiştir)
        gantt_container = self.scroll_area.parent()
        if gantt_container and gantt_container.layout():
            old_header = gantt_container.layout().itemAt(0)
            if old_header and old_header.widget():
                old_header.widget().deleteLater()
            gantt_container.layout().insertWidget(0, self.timeline_header)
        self._build_gantt()
        
    def load_data(self, work_stations: list, operations: list):
        """
        Veri yükle
        
        work_stations: [{"id", "code", "name", "station_type", "capacity_per_hour"}, ...]
        operations: [{"work_order_id", "order_no", "item_name", "work_station_id", 
                      "operation_name", "start_time", "end_time", "status", "progress"}, ...]
        """
        self.work_stations = work_stations
        self.operations = operations
        self._build_gantt()
        self._update_stats()
        
    def _update_stats(self):
        """İstatistikleri güncelle"""
        period_start = datetime(self.current_date.year(), self.current_date.month(), self.current_date.day())
        period_end = period_start + timedelta(days=self.view_days)
        
        active_machines = set()
        planned_count = 0
        in_progress_count = 0
        delayed_count = 0
        total_hours = 0
        
        now = datetime.now()
        
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
            
            # Bu dönemde mi?
            if start_time < period_end and end_time > period_start:
                ws_id = op.get("work_station_id")
                if ws_id:
                    active_machines.add(ws_id)
                
                if status in ["planned", "released"]:
                    planned_count += 1
                elif status == "in_progress":
                    in_progress_count += 1
                    
                # Gecikme kontrolü
                if status in ["planned", "released", "in_progress"] and end_time < now:
                    delayed_count += 1
                    
                # Toplam saat
                duration = (min(end_time, period_end) - max(start_time, period_start)).total_seconds() / 3600
                total_hours += max(0, duration)
        
        self._update_card(self.machines_card, str(len(active_machines)))
        self._update_card(self.planned_card, str(planned_count))
        self._update_card(self.in_progress_card, str(in_progress_count))
        self._update_card(self.delayed_card, str(delayed_count))
        
        # Kapasite kullanımı (basit hesap)
        total_capacity = len(self.work_stations) * self.view_days * 8  # 8 saat/gün
        utilization = int(total_hours / total_capacity * 100) if total_capacity > 0 else 0
        self._update_card(self.utilization_card, f"%{min(100, utilization)}")
        
        self.info_label.setText(f"{len(self.work_stations)} makine, {len(self.operations)} operasyon")
        
    def _build_gantt(self):
        """Gantt satırlarını oluştur"""
        # Mevcut içeriği temizle
        while self.gantt_content_layout.count():
            child = self.gantt_content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not self.work_stations:
            empty_label = QLabel("Henüz iş istasyonu tanımlanmamış")
            empty_label.setStyleSheet("color: #64748b; font-size: 14px; padding: 40px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.gantt_content_layout.addWidget(empty_label)
            return
        
        period_start = datetime(self.current_date.year(), self.current_date.month(), self.current_date.day())
        
        # Operasyonları iş istasyonuna göre grupla
        ops_by_station = {}
        for op in self.operations:
            ws_id = op.get("work_station_id")
            if ws_id:
                if ws_id not in ops_by_station:
                    ops_by_station[ws_id] = []
                ops_by_station[ws_id].append(op)
        
        # Her makine için satır oluştur
        for ws in self.work_stations:
            ws_id = ws.get("id")
            
            row = MachineRow(
                station_id=ws_id,
                station_code=ws.get("code", ""),
                station_name=ws.get("name", ""),
                station_type=ws.get("station_type", "machine"),
                capacity=float(ws.get("capacity_per_hour", 0) or 0)
            )
            row.work_order_clicked.connect(self.work_order_clicked.emit)
            
            # Bu makinenin operasyonlarını ayarla
            station_ops = ops_by_station.get(ws_id, [])
            row.set_operations(station_ops, period_start, self.view_days, self.pixels_per_day)
            
            self.gantt_content_layout.addWidget(row)
        
        # Alt boşluk
        self.gantt_content_layout.addStretch()
        
        # Content genişliğini ayarla
        self.gantt_content.setMinimumWidth(180 + self.view_days * self.pixels_per_day)
