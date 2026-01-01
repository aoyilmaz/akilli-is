"""
Akıllı İş - Üretim Planlama Sayfası
"""

from datetime import datetime, timedelta
from decimal import Decimal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout, QComboBox, QSizePolicy,
    QToolTip
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QRect
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QCursor


class GanttBar(QWidget):
    """Gantt çubuğu"""
    
    clicked = pyqtSignal(int)
    
    def __init__(self, wo_id: int, order_no: str, item_name: str, 
                 progress: float, status: str, color: str, parent=None):
        super().__init__(parent)
        self.wo_id = wo_id
        self.order_no = order_no
        self.item_name = item_name
        self.progress = progress
        self.status = status
        self.color = QColor(color)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(32)
        self.setToolTip(f"{order_no}\n{item_name}\nİlerleme: %{progress:.0f}\nDurum: {status}")
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        # Arka plan
        bg_color = QColor(self.color)
        bg_color.setAlpha(60)
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(self.color, 1))
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 6, 6)
        
        # İlerleme çubuğu
        if self.progress > 0:
            progress_width = int((rect.width() - 4) * self.progress / 100)
            progress_rect = QRect(2, 2, progress_width, rect.height() - 4)
            painter.setBrush(QBrush(self.color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(progress_rect, 4, 4)
        
        # Metin
        painter.setPen(QPen(QColor("#f8fafc")))
        font = QFont("Arial", 10)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect.adjusted(8, 0, -8, 0), Qt.AlignmentFlag.AlignVCenter, 
                        f"{self.order_no} - {self.item_name[:20]}")
        
    def mousePressEvent(self, event):
        self.clicked.emit(self.wo_id)


class DayColumn(QFrame):
    """Gün sütunu"""
    
    def __init__(self, date: QDate, is_today: bool = False, is_weekend: bool = False, parent=None):
        super().__init__(parent)
        self.date = date
        self.is_today = is_today
        self.is_weekend = is_weekend
        self.setup_ui()
        
    def setup_ui(self):
        if self.is_today:
            bg = "#6366f120"
            border = "#6366f1"
        elif self.is_weekend:
            bg = "#1e293b"
            border = "#334155"
        else:
            bg = "transparent"
            border = "#334155"
            
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border-right: 1px solid {border};
                min-width: 100px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 8)
        layout.setSpacing(4)
        
        # Gün adı
        day_names = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
        day_name = day_names[self.date.dayOfWeek() - 1]
        
        day_label = QLabel(day_name)
        day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        color = "#6366f1" if self.is_today else "#94a3b8"
        day_label.setStyleSheet(f"color: {color}; font-size: 11px; background: transparent;")
        layout.addWidget(day_label)
        
        # Tarih
        date_label = QLabel(str(self.date.day()))
        date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        weight = "bold" if self.is_today else "normal"
        color = "#f8fafc" if self.is_today else "#e2e8f0"
        date_label.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: {weight}; background: transparent;")
        layout.addWidget(date_label)
        
        layout.addStretch()


class ProductionPlanningPage(QWidget):
    """Üretim Planlama sayfası"""
    
    page_title = "Üretim Planlama"
    
    work_order_clicked = pyqtSignal(int)
    refresh_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_date = QDate.currentDate()
        self.view_days = 14  # 2 hafta
        self.work_orders = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # === Başlık ===
        header_layout = QHBoxLayout()
        
        title_layout = QVBoxLayout()
        title = QLabel("📅 Üretim Planlama")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f8fafc;")
        subtitle = QLabel("İş emirlerini takvim üzerinde görüntüleyin ve planlayın")
        subtitle.setStyleSheet("font-size: 14px; color: #94a3b8;")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addLayout(title_layout)
        
        header_layout.addStretch()
        
        # Navigasyon
        prev_btn = QPushButton("◀ Önceki")
        prev_btn.setStyleSheet(self._btn_style())
        prev_btn.clicked.connect(self._prev_period)
        header_layout.addWidget(prev_btn)
        
        self.period_label = QLabel("")
        self.period_label.setStyleSheet("color: #f8fafc; font-weight: 600; padding: 0 16px;")
        header_layout.addWidget(self.period_label)
        
        next_btn = QPushButton("Sonraki ▶")
        next_btn.setStyleSheet(self._btn_style())
        next_btn.clicked.connect(self._next_period)
        header_layout.addWidget(next_btn)
        
        today_btn = QPushButton("Bugün")
        today_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                border: none; color: white;
                padding: 10px 20px; border-radius: 8px;
            }
            QPushButton:hover { background-color: #4f46e5; }
        """)
        today_btn.clicked.connect(self._go_today)
        header_layout.addWidget(today_btn)
        
        # Görünüm seçimi
        self.view_combo = QComboBox()
        self.view_combo.addItem("1 Hafta", 7)
        self.view_combo.addItem("2 Hafta", 14)
        self.view_combo.addItem("1 Ay", 30)
        self.view_combo.setCurrentIndex(1)
        self.view_combo.setStyleSheet("""
            QComboBox {
                background-color: #1e293b; border: 1px solid #334155;
                border-radius: 8px; padding: 8px 12px; color: #f8fafc; min-width: 100px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #1e293b; border: 1px solid #334155;
                color: #f8fafc; selection-background-color: #334155;
            }
        """)
        self.view_combo.currentIndexChanged.connect(self._on_view_changed)
        header_layout.addWidget(self.view_combo)
        
        # Yenile
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(40, 40)
        refresh_btn.setStyleSheet(self._btn_style())
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # === Özet Kartlar ===
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)
        
        self.planned_card = self._create_card("📅 Planlanan", "0", "#3b82f6")
        cards_layout.addWidget(self.planned_card)
        
        self.in_progress_card = self._create_card("🔄 Üretimde", "0", "#f59e0b")
        cards_layout.addWidget(self.in_progress_card)
        
        self.completed_card = self._create_card("✅ Bu Dönem Tamamlanan", "0", "#10b981")
        cards_layout.addWidget(self.completed_card)
        
        self.capacity_card = self._create_card("📊 Kapasite Kullanımı", "%0", "#8b5cf6")
        cards_layout.addWidget(self.capacity_card)
        
        layout.addLayout(cards_layout)
        
        # === Gantt Chart ===
        gantt_frame = QFrame()
        gantt_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 41, 59, 0.3);
                border: 1px solid #334155;
                border-radius: 12px;
            }
        """)
        gantt_layout = QVBoxLayout(gantt_frame)
        gantt_layout.setContentsMargins(0, 0, 0, 0)
        gantt_layout.setSpacing(0)
        
        # Takvim başlığı
        self.calendar_header = QWidget()
        self.calendar_header.setFixedHeight(70)
        self.calendar_header.setStyleSheet("background-color: #1e293b; border-top-left-radius: 12px; border-top-right-radius: 12px;")
        self.header_layout = QHBoxLayout(self.calendar_header)
        self.header_layout.setContentsMargins(150, 0, 0, 0)
        self.header_layout.setSpacing(0)
        gantt_layout.addWidget(self.calendar_header)
        
        # Scroll area for gantt content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                background: #1e293b; width: 10px; border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #334155; border-radius: 5px; min-height: 30px;
            }
            QScrollBar:horizontal {
                background: #1e293b; height: 10px; border-radius: 5px;
            }
            QScrollBar::handle:horizontal {
                background: #334155; border-radius: 5px; min-width: 30px;
            }
        """)
        
        self.gantt_content = QWidget()
        self.gantt_content_layout = QVBoxLayout(self.gantt_content)
        self.gantt_content_layout.setContentsMargins(0, 0, 0, 0)
        self.gantt_content_layout.setSpacing(0)
        scroll.setWidget(self.gantt_content)
        
        gantt_layout.addWidget(scroll)
        layout.addWidget(gantt_frame)
        
        self._update_period_label()
        self._build_calendar_header()
        
    def _create_card(self, title: str, value: str, color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color}15;
                border: 1px solid {color}40;
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #94a3b8; font-size: 13px; background: transparent;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold; background: transparent;")
        layout.addWidget(value_label)
        
        return card
        
    def _update_card(self, card: QFrame, value: str):
        value_label = card.findChild(QLabel, "value")
        if value_label:
            value_label.setText(value)
        
    def _btn_style(self):
        return """
            QPushButton {
                background-color: #1e293b; border: 1px solid #334155;
                color: #f8fafc; padding: 10px 16px; border-radius: 8px;
            }
            QPushButton:hover { background-color: #334155; }
        """
        
    def _update_period_label(self):
        start = self.current_date
        end = start.addDays(self.view_days - 1)
        
        months = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                  "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        
        if start.month() == end.month():
            text = f"{start.day()} - {end.day()} {months[start.month()-1]} {start.year()}"
        else:
            text = f"{start.day()} {months[start.month()-1]} - {end.day()} {months[end.month()-1]} {start.year()}"
            
        self.period_label.setText(text)
        
    def _build_calendar_header(self):
        # Mevcut header'ı temizle
        while self.header_layout.count():
            child = self.header_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        today = QDate.currentDate()
        
        for i in range(self.view_days):
            date = self.current_date.addDays(i)
            is_today = date == today
            is_weekend = date.dayOfWeek() >= 6
            
            day_col = DayColumn(date, is_today, is_weekend)
            self.header_layout.addWidget(day_col)
            
    def _prev_period(self):
        self.current_date = self.current_date.addDays(-self.view_days)
        self._update_period_label()
        self._build_calendar_header()
        self._build_gantt_rows()
        
    def _next_period(self):
        self.current_date = self.current_date.addDays(self.view_days)
        self._update_period_label()
        self._build_calendar_header()
        self._build_gantt_rows()
        
    def _go_today(self):
        self.current_date = QDate.currentDate()
        self._update_period_label()
        self._build_calendar_header()
        self._build_gantt_rows()
        
    def _on_view_changed(self):
        self.view_days = self.view_combo.currentData()
        self._update_period_label()
        self._build_calendar_header()
        self._build_gantt_rows()
        
    def load_data(self, work_orders: list):
        """İş emirlerini yükle"""
        self.work_orders = work_orders
        self._build_gantt_rows()
        self._update_stats()
        
    def _update_stats(self):
        """İstatistikleri güncelle"""
        planned = 0
        in_progress = 0
        completed = 0
        
        period_start = datetime(self.current_date.year(), self.current_date.month(), self.current_date.day())
        period_end = period_start + timedelta(days=self.view_days)
        
        for wo in self.work_orders:
            status = wo.get("status", "draft")
            planned_start = wo.get("planned_start")
            planned_end = wo.get("planned_end")
            
            # Bu dönemde mi?
            if planned_start and planned_end:
                wo_start = planned_start if isinstance(planned_start, datetime) else datetime.combine(planned_start, datetime.min.time())
                wo_end = planned_end if isinstance(planned_end, datetime) else datetime.combine(planned_end, datetime.min.time())
                
                if wo_start < period_end and wo_end > period_start:
                    if status in ["planned", "released"]:
                        planned += 1
                    elif status == "in_progress":
                        in_progress += 1
                    elif status in ["completed", "closed"]:
                        completed += 1
        
        self._update_card(self.planned_card, str(planned))
        self._update_card(self.in_progress_card, str(in_progress))
        self._update_card(self.completed_card, str(completed))
        
        # Basit kapasite hesabı (toplam iş günü / dönem günü)
        total_orders = planned + in_progress
        capacity = min(100, int(total_orders / self.view_days * 100)) if self.view_days > 0 else 0
        self._update_card(self.capacity_card, f"%{capacity}")
        
    def _build_gantt_rows(self):
        """Gantt satırlarını oluştur"""
        # Mevcut içeriği temizle
        while self.gantt_content_layout.count():
            child = self.gantt_content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        period_start = datetime(self.current_date.year(), self.current_date.month(), self.current_date.day())
        period_end = period_start + timedelta(days=self.view_days)
        
        status_colors = {
            "draft": "#94a3b8",
            "planned": "#3b82f6",
            "released": "#8b5cf6",
            "in_progress": "#f59e0b",
            "completed": "#10b981",
            "closed": "#64748b",
        }
        
        status_names = {
            "draft": "Taslak",
            "planned": "Planlandı",
            "released": "Serbest",
            "in_progress": "Üretimde",
            "completed": "Tamamlandı",
            "closed": "Kapatıldı",
        }
        
        visible_orders = []
        
        for wo in self.work_orders:
            planned_start = wo.get("planned_start")
            planned_end = wo.get("planned_end")
            
            if not planned_start or not planned_end:
                continue
                
            wo_start = planned_start if isinstance(planned_start, datetime) else datetime.combine(planned_start, datetime.min.time())
            wo_end = planned_end if isinstance(planned_end, datetime) else datetime.combine(planned_end, datetime.min.time())
            
            # Bu dönemde görünür mü?
            if wo_start < period_end and wo_end > period_start:
                visible_orders.append({
                    **wo,
                    "wo_start": wo_start,
                    "wo_end": wo_end,
                })
        
        if not visible_orders:
            # Boş durumu için yeni label oluştur
            empty_label = QLabel("Bu dönemde planlanmış iş emri bulunmuyor")
            empty_label.setStyleSheet("color: #64748b; font-size: 16px; padding: 40px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.gantt_content_layout.addWidget(empty_label)
            return
        
        # İş emirlerini başlangıç tarihine göre sırala
        visible_orders.sort(key=lambda x: x["wo_start"])
        
        for wo in visible_orders:
            row = QWidget()
            row.setFixedHeight(50)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 4, 0, 4)
            row_layout.setSpacing(0)
            
            # Sol etiket (150px)
            label_frame = QFrame()
            label_frame.setFixedWidth(150)
            label_frame.setStyleSheet("background-color: #1e293b; border-right: 1px solid #334155;")
            label_layout = QVBoxLayout(label_frame)
            label_layout.setContentsMargins(12, 4, 12, 4)
            label_layout.setSpacing(0)
            
            order_label = QLabel(wo.get("order_no", ""))
            order_label.setStyleSheet("color: #818cf8; font-weight: 600; font-size: 12px; background: transparent;")
            label_layout.addWidget(order_label)
            
            item_label = QLabel(wo.get("item_name", "")[:18])
            item_label.setStyleSheet("color: #94a3b8; font-size: 11px; background: transparent;")
            label_layout.addWidget(item_label)
            
            row_layout.addWidget(label_frame)
            
            # Gantt bar alanı
            bar_container = QWidget()
            bar_container.setStyleSheet("background: transparent;")
            bar_layout = QHBoxLayout(bar_container)
            bar_layout.setContentsMargins(0, 0, 0, 0)
            bar_layout.setSpacing(0)
            
            wo_start = wo["wo_start"]
            wo_end = wo["wo_end"]
            
            # Başlangıç offset'i
            start_offset = max(0, (wo_start - period_start).days)
            # Bitiş pozisyonu
            end_pos = min(self.view_days, (wo_end - period_start).days + 1)
            # Bar genişliği
            bar_days = end_pos - start_offset
            
            if start_offset > 0:
                spacer = QWidget()
                spacer.setFixedWidth(start_offset * 100)  # 100px per day
                bar_layout.addWidget(spacer)
            
            # Gantt bar
            status = wo.get("status", "draft")
            color = status_colors.get(status, "#94a3b8")
            progress = wo.get("progress_rate", 0)
            
            bar = GanttBar(
                wo.get("id", 0),
                wo.get("order_no", ""),
                wo.get("item_name", ""),
                progress,
                status_names.get(status, "?"),
                color
            )
            bar.setFixedWidth(bar_days * 100 - 8)  # 100px per day minus padding
            bar.clicked.connect(self.work_order_clicked.emit)
            bar_layout.addWidget(bar)
            
            bar_layout.addStretch()
            row_layout.addWidget(bar_container)
            
            self.gantt_content_layout.addWidget(row)
        
        self.gantt_content_layout.addStretch()
