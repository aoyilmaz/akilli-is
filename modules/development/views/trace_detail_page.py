"""
Akıllı İş - Trace Detail Page
Trace session detay görünümü (Timeline + Tablo)
"""

import json
from datetime import datetime
from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QTabWidget,
    QTextEdit,
    QSplitter,
    QFrame,
    QScrollArea,
    QGroupBox,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor, QFont

from database.base import get_session
from database.models.development import TraceSession, TraceEvent, TraceEventType


class TraceDetailPage(QWidget):
    """
    Trace Session Detay Sayfası

    İki görünüm:
    1. Timeline - Kronolojik event listesi
    2. Tablo - Filtrelenebilir event tablosu
    """

    back_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_session: Optional[TraceSession] = None
        self._events: List[TraceEvent] = []
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """UI bileşenlerini oluştur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Üst bar (geri butonu + başlık)
        header_layout = QHBoxLayout()

        self.back_btn = QPushButton("Geri")
        self.back_btn.setMaximumWidth(80)
        header_layout.addWidget(self.back_btn)

        self.title_label = QLabel("Trace Detayi")
        self.title_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #fff;"
        )
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        # Export butonu
        self.export_btn = QPushButton("JSON Indir")
        self.export_btn.setMaximumWidth(100)
        header_layout.addWidget(self.export_btn)

        layout.addLayout(header_layout)

        # Session bilgisi
        self.info_group = QGroupBox("Oturum Bilgisi")
        self.info_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """
        )
        info_layout = QHBoxLayout(self.info_group)

        self.info_labels = {
            "user": QLabel("Kullanici: -"),
            "status": QLabel("Durum: -"),
            "started": QLabel("Baslangic: -"),
            "ended": QLabel("Bitis: -"),
            "events": QLabel("Event: -"),
            "error": QLabel("Hata: -"),
        }

        for label in self.info_labels.values():
            label.setStyleSheet("color: #ccc; font-weight: normal;")
            info_layout.addWidget(label)

        layout.addWidget(self.info_group)

        # Tab widget (Timeline + Tablo)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            """
            QTabWidget::pane {
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #aaa;
                padding: 8px 16px;
                border: 1px solid #3d3d3d;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #3d3d3d;
                color: #fff;
            }
        """
        )

        # Timeline tab
        self.timeline_widget = self._create_timeline_widget()
        self.tabs.addTab(self.timeline_widget, "Timeline")

        # Tablo tab
        self.table_widget = self._create_table_widget()
        self.tabs.addTab(self.table_widget, "Tablo")

        # Detay tab
        self.detail_widget = self._create_detail_widget()
        self.tabs.addTab(self.detail_widget, "Detay")

        # İnceleme tab
        self.inspection_widget = self._create_inspection_widget()
        self.tabs.addTab(self.inspection_widget, "İncele")

        layout.addWidget(self.tabs)

    def _create_timeline_widget(self) -> QWidget:
        """Timeline widget oluştur"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            """
            QScrollArea {
                border: none;
                background-color: #1e1e1e;
            }
        """
        )

        self.timeline_container = QWidget()
        self.timeline_layout = QVBoxLayout(self.timeline_container)
        self.timeline_layout.setSpacing(4)
        self.timeline_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self.timeline_container)
        layout.addWidget(scroll)

        return widget

    def _create_table_widget(self) -> QWidget:
        """Tablo widget oluştur"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)

        self.event_table = QTableWidget()
        self.event_table.setColumnCount(8)
        self.event_table.setHorizontalHeaderLabels(
            [
                "Zaman",
                "Modul",
                "Sayfa",
                "Sekme",
                "Tip",
                "Widget",
                "Widget Name",
                "Detay",
            ]
        )
        self.event_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.event_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.event_table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents
        )
        self.event_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.event_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.event_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.event_table.setAlternatingRowColors(True)
        self.event_table.verticalHeader().setVisible(False)

        self.event_table.setStyleSheet(
            """
            QTableWidget {
                background-color: #2d2d2d;
                gridline-color: #3d3d3d;
                color: #fff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QTableWidget::item:selected {
                background-color: #0d6efd;
            }
            QHeaderView::section {
                background-color: #1e1e1e;
                color: #aaa;
                padding: 6px;
                border: none;
                border-bottom: 1px solid #3d3d3d;
            }
        """
        )

        layout.addWidget(self.event_table)
        return widget

    def _create_detail_widget(self) -> QWidget:
        """Detay widget (JSON görüntüleyici)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)

        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setFont(QFont("Consolas", 10))
        self.detail_text.setStyleSheet(
            """
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
        """
        )

        layout.addWidget(self.detail_text)
        return widget

    def _create_inspection_widget(self) -> QWidget:
        """İnceleme widget (HTML görüntüleyici)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)

        self.inspection_text = QTextEdit()
        self.inspection_text.setReadOnly(True)
        self.inspection_text.setFont(QFont("Consolas", 11))
        self.inspection_text.setStyleSheet(
            """
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 10px;
            }
        """
        )

        layout.addWidget(self.inspection_text)
        return widget

    def _connect_signals(self):
        """Sinyalleri bağla"""
        self.back_btn.clicked.connect(self.back_requested.emit)
        self.export_btn.clicked.connect(self._export_json)
        self.event_table.itemSelectionChanged.connect(self._on_event_selected)
        self.event_table.cellDoubleClicked.connect(self._on_table_double_clicked)

    def _on_table_double_clicked(self, row: int, column: int):
        """Tablo hucresine cift tiklandiginda detay goster"""
        if row < len(self._events):
            self._show_event_detail(row)

    def _show_event_detail(self, event_index: int):
        """Event detayini dialog olarak goster"""
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox

        if event_index >= len(self._events):
            return

        event = self._events[event_index]

        # Dialog olustur
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Event Detayi - {event.event_type.value}")
        dialog.setMinimumSize(700, 500)
        dialog.setStyleSheet(
            """
            QDialog {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #fff;
            }
        """
        )

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Baslik bilgileri
        header_group = QGroupBox("Event Bilgisi")
        header_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                margin-top: 8px;
                padding: 8px;
                color: #fff;
            }
        """
        )
        header_layout = QVBoxLayout(header_group)

        # Zaman
        time_str = event.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        header_layout.addWidget(QLabel(f"Zaman: {time_str}"))

        # Modul/Sayfa/Sekme
        modul, sayfa, sekme = self._parse_widget_path(event.widget_path)
        header_layout.addWidget(QLabel(f"Modul: {modul}"))
        header_layout.addWidget(QLabel(f"Sayfa: {sayfa}"))
        header_layout.addWidget(QLabel(f"Sekme: {sekme}"))

        # Tip ve Widget
        header_layout.addWidget(QLabel(f"Tip: {event.event_type.value}"))
        header_layout.addWidget(QLabel(f"Widget: {self._get_widget_type(event)}"))
        header_layout.addWidget(QLabel(f"Widget Name: {event.widget_name or '-'}"))

        if event.duration_ms:
            header_layout.addWidget(QLabel(f"Sure: {event.duration_ms}ms"))

        layout.addWidget(header_group)

        # Detay icerigi
        detail_group = QGroupBox("Detay Icerigi")
        detail_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                margin-top: 8px;
                padding: 8px;
                color: #fff;
            }
        """
        )
        detail_layout = QVBoxLayout(detail_group)

        detail_text = QTextEdit()
        detail_text.setReadOnly(True)
        detail_text.setFont(QFont("Consolas", 10))
        detail_text.setStyleSheet(
            """
            QTextEdit {
                background-color: #2d2d2d;
                color: #d4d4d4;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
        """
        )

        # Detay icerigi - tip'e gore farkli gosterim
        if event.event_data:
            if event.event_type == TraceEventType.SQL_QUERY:
                # SQL sorgusu icin ozel gosterim
                sql = event.event_data.get("sql", "")
                params = event.event_data.get("params", {})
                row_count = event.event_data.get("row_count", "?")
                operation = event.event_data.get("operation", "")

                content = f"-- {operation} Query ({row_count} rows)\n\n"
                content += sql
                if params:
                    content += f"\n\n-- Parameters:\n{json.dumps(params, indent=2, ensure_ascii=False)}"
                detail_text.setText(content)
            elif event.event_type == TraceEventType.ERROR_OCCURRED:
                # Hata icin traceback goster
                exc_type = event.event_data.get("exception_type", "Error")
                message = event.event_data.get("error_message", "")
                traceback_str = event.event_data.get("traceback", "")

                content = f"{exc_type}: {message}\n\n"
                content += "Traceback:\n"
                content += traceback_str
                detail_text.setText(content)
            elif event.event_type == TraceEventType.METHOD_CALL:
                # Metod cagrisı
                params = event.event_data.get("params", {})
                return_summary = event.event_data.get("return_summary", "")
                status = event.event_data.get("status", "")
                duration = event.event_data.get("duration_ms", "")

                content = f"Status: {status}\n"
                content += f"Duration: {duration}ms\n"
                content += f"Return: {return_summary}\n\n"
                content += (
                    f"Parameters:\n{json.dumps(params, indent=2, ensure_ascii=False)}"
                )
                detail_text.setText(content)
            else:
                # Diger tipler icin JSON
                detail_text.setText(
                    json.dumps(event.event_data, indent=2, ensure_ascii=False)
                )
        else:
            detail_text.setText("(Detay yok)")

        detail_layout.addWidget(detail_text)
        layout.addWidget(detail_group, 1)

        # Kapat butonu
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(dialog.close)
        button_box.setStyleSheet(
            """
            QPushButton {
                background-color: #3d3d3d;
                color: #fff;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
        """
        )
        layout.addWidget(button_box)

        dialog.exec()

    def load_session(self, session_id: int):
        """Session verilerini yükle"""
        try:
            db_session = get_session()
            self._current_session = db_session.query(TraceSession).get(session_id)

            if self._current_session:
                self._events = (
                    db_session.query(TraceEvent)
                    .filter(TraceEvent.session_id == session_id)
                    .order_by(TraceEvent.timestamp)
                    .all()
                )

                self._update_info()
                self._populate_timeline()
                self._populate_table()
                self._update_detail()
                self._update_inspection()

        except Exception as e:
            print(f"[TraceDetailPage] load_session error: {e}")

    def _update_info(self):
        """Session bilgilerini güncelle"""
        if not self._current_session:
            return

        s = self._current_session

        self.title_label.setText(f"Trace #{s.id}")

        username = s.user.username if s.user else "?"
        self.info_labels["user"].setText(f"Kullanici: {username}")

        status_labels = {
            "active": "Aktif",
            "completed": "Tamamlandi",
            "error": "Hata",
            "timeout": "Zaman Asimi",
        }
        status_text = status_labels.get(s.status.value, s.status.value)
        self.info_labels["status"].setText(f"Durum: {status_text}")

        self.info_labels["started"].setText(
            f"Baslangic: {s.started_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        if s.ended_at:
            self.info_labels["ended"].setText(
                f"Bitis: {s.ended_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        else:
            self.info_labels["ended"].setText("Bitis: -")

        self.info_labels["events"].setText(f"Event: {len(self._events)}")

        if s.error_log:
            self.info_labels["error"].setText(f"Hata: {s.error_log.error_type}")
        else:
            self.info_labels["error"].setText("Hata: -")

    def _populate_timeline(self):
        """Timeline'ı doldur"""
        # Önceki içeriği temizle
        while self.timeline_layout.count():
            item = self.timeline_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Event tipine göre renkler
        type_colors = {
            TraceEventType.PAGE_NAVIGATION: "#2196F3",
            TraceEventType.BUTTON_CLICK: "#4CAF50",
            TraceEventType.TABLE_FILTER: "#FF9800",
            TraceEventType.TABLE_SELECTION: "#FF9800",
            TraceEventType.FORM_INPUT: "#9C27B0",
            TraceEventType.METHOD_CALL: "#00BCD4",
            TraceEventType.SQL_QUERY: "#FFC107",
            TraceEventType.ERROR_OCCURRED: "#f44336",
        }

        type_labels = {
            TraceEventType.PAGE_NAVIGATION: "PAGE",
            TraceEventType.BUTTON_CLICK: "BUTTON",
            TraceEventType.TABLE_FILTER: "FILTER",
            TraceEventType.TABLE_SELECTION: "SELECT",
            TraceEventType.FORM_INPUT: "INPUT",
            TraceEventType.METHOD_CALL: "METHOD",
            TraceEventType.SQL_QUERY: "SQL",
            TraceEventType.ERROR_OCCURRED: "ERROR",
        }

        for idx, event in enumerate(self._events):
            # Timeline satırı
            row = QFrame()
            row.setProperty("event_index", idx)  # Tiklamada kullanilacak
            row.setStyleSheet(
                """
                QFrame {
                    background-color: #2d2d2d;
                    border-radius: 4px;
                    padding: 4px;
                }
                QFrame:hover {
                    background-color: #3d3d3d;
                }
            """
            )
            row.setCursor(Qt.CursorShape.PointingHandCursor)
            row.mousePressEvent = lambda e, i=idx: self._show_event_detail(i)

            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(8, 4, 8, 4)
            row_layout.setSpacing(8)

            # Zaman
            time_str = event.timestamp.strftime("%H:%M:%S.%f")[:-3]
            time_label = QLabel(time_str)
            time_label.setStyleSheet(
                "color: #888; font-family: Consolas; min-width: 80px;"
            )
            row_layout.addWidget(time_label)

            # Modul, Sayfa, Sekme
            modul, sayfa, sekme = self._parse_widget_path(event.widget_path)
            modul_label = QLabel(modul)
            modul_label.setStyleSheet("color: #81c784; min-width: 80px;")
            row_layout.addWidget(modul_label)

            sayfa_label = QLabel(sayfa)
            sayfa_label.setStyleSheet("color: #64b5f6; min-width: 100px;")
            row_layout.addWidget(sayfa_label)

            sekme_label = QLabel(sekme)
            sekme_label.setStyleSheet("color: #ba68c8; min-width: 80px;")
            row_layout.addWidget(sekme_label)

            # Tip etiketi
            type_color = type_colors.get(event.event_type, "#666")
            type_text = type_labels.get(event.event_type, event.event_type.value)
            type_label = QLabel(f"[{type_text}]")
            type_label.setStyleSheet(
                f"color: {type_color}; font-weight: bold; min-width: 70px;"
            )
            row_layout.addWidget(type_label)

            # Widget tipi
            widget_type = self._get_widget_type(event)
            widget_type_label = QLabel(widget_type)
            widget_type_label.setStyleSheet("color: #ffb74d; min-width: 80px;")
            row_layout.addWidget(widget_type_label)

            # Widget adı
            widget_label = QLabel(event.widget_name or "-")
            widget_label.setStyleSheet("color: #fff; min-width: 120px;")
            row_layout.addWidget(widget_label)

            # Kısa detay
            detail_text = self._get_short_detail(event)
            detail_label = QLabel(detail_text)
            detail_label.setStyleSheet("color: #4fc3f7;")  # Link rengi
            row_layout.addWidget(detail_label, 1)

            # Süre (varsa)
            if event.duration_ms:
                duration_label = QLabel(f"{event.duration_ms}ms")
                duration_label.setStyleSheet("color: #888; min-width: 60px;")
                row_layout.addWidget(duration_label)

            self.timeline_layout.addWidget(row)

        # Alt boşluk
        self.timeline_layout.addStretch()

    def _parse_widget_path(self, widget_path: str) -> tuple:
        """
        Widget path'i modul, sayfa, sekme olarak ayir

        Args:
            widget_path: "Modul > Sayfa > Sekme" formatinda string

        Returns:
            (modul, sayfa, sekme) tuple
        """
        if not widget_path:
            return ("-", "-", "-")

        parts = [p.strip() for p in widget_path.split(">")]

        modul = parts[0] if len(parts) > 0 else "-"
        sayfa = parts[1] if len(parts) > 1 else "-"
        sekme = parts[2] if len(parts) > 2 else "-"

        return (modul, sayfa, sekme)

    def _populate_table(self):
        """Tabloyu doldur"""
        self.event_table.setRowCount(len(self._events))

        type_labels = {
            TraceEventType.PAGE_NAVIGATION: "Sayfa",
            TraceEventType.BUTTON_CLICK: "Buton",
            TraceEventType.TABLE_FILTER: "Filtre",
            TraceEventType.TABLE_SELECTION: "Secim",
            TraceEventType.FORM_INPUT: "Girdi",
            TraceEventType.METHOD_CALL: "Metod",
            TraceEventType.SQL_QUERY: "SQL",
            TraceEventType.ERROR_OCCURRED: "Hata",
        }

        for row, event in enumerate(self._events):
            # Zaman
            time_str = event.timestamp.strftime("%H:%M:%S.%f")[:-3]
            self.event_table.setItem(row, 0, QTableWidgetItem(time_str))

            # Modul, Sayfa, Sekme (widget_path'ten)
            modul, sayfa, sekme = self._parse_widget_path(event.widget_path)
            self.event_table.setItem(row, 1, QTableWidgetItem(modul))
            self.event_table.setItem(row, 2, QTableWidgetItem(sayfa))
            self.event_table.setItem(row, 3, QTableWidgetItem(sekme))

            # Tip
            type_text = type_labels.get(event.event_type, event.event_type.value)
            self.event_table.setItem(row, 4, QTableWidgetItem(type_text))

            # Widget (event tipi)
            widget_type = self._get_widget_type(event)
            self.event_table.setItem(row, 5, QTableWidgetItem(widget_type))

            # Widget Name
            self.event_table.setItem(row, 6, QTableWidgetItem(event.widget_name or "-"))

            # Detay (tiklanabilir)
            detail_text = self._get_short_detail(event)
            detail_item = QTableWidgetItem(detail_text)
            detail_item.setForeground(QColor("#4fc3f7"))  # Mavi renk (link gorunumu)
            self.event_table.setItem(row, 7, detail_item)

    def _get_widget_type(self, event: TraceEvent) -> str:
        """Event icin widget tipini belirle"""
        if event.event_type == TraceEventType.BUTTON_CLICK:
            data = event.event_data or {}
            if data.get("is_checkable"):
                return "CheckButton"
            return "Button"
        elif event.event_type == TraceEventType.FORM_INPUT:
            data = event.event_data or {}
            field_type = data.get("field_type", "input")
            type_map = {
                "text": "LineEdit",
                "textarea": "TextEdit",
                "combobox": "ComboBox",
                "spinbox": "SpinBox",
                "date": "DateEdit",
                "checkbox": "CheckBox",
                "radio": "RadioButton",
            }
            return type_map.get(field_type, "Input")
        elif event.event_type == TraceEventType.TABLE_FILTER:
            return "TableFilter"
        elif event.event_type == TraceEventType.TABLE_SELECTION:
            return "TableRow"
        elif event.event_type == TraceEventType.PAGE_NAVIGATION:
            return "Page"
        elif event.event_type == TraceEventType.METHOD_CALL:
            return "Method"
        elif event.event_type == TraceEventType.SQL_QUERY:
            data = event.event_data or {}
            return data.get("operation", "SQL")
        elif event.event_type == TraceEventType.ERROR_OCCURRED:
            return "Exception"
        return "-"

    def _get_short_detail(self, event: TraceEvent) -> str:
        """Event için kısa detay metni"""
        if not event.event_data:
            return ""

        data = event.event_data

        if event.event_type == TraceEventType.BUTTON_CLICK:
            return data.get("button_text", "")

        elif event.event_type == TraceEventType.FORM_INPUT:
            field = data.get("field_type", "")
            value = data.get("value", "")
            if len(str(value)) > 30:
                value = str(value)[:30] + "..."
            return f"{field}: {value}"

        elif event.event_type == TraceEventType.SQL_QUERY:
            op = data.get("operation", "")
            rows = data.get("row_count", "?")
            return f"{op} ({rows} rows)"

        elif event.event_type == TraceEventType.METHOD_CALL:
            status = data.get("status", "")
            duration = data.get("duration_ms", "")
            return f"{status} - {duration}ms"

        elif event.event_type == TraceEventType.PAGE_NAVIGATION:
            return data.get("to_page", "")

        elif event.event_type == TraceEventType.ERROR_OCCURRED:
            exc_type = data.get("exception_type", "Error")
            message = str(data.get("error_message", ""))
            if len(message) > 50:
                message = message[:50] + "..."
            return f"{exc_type}: {message}"

        return str(data)[:50]

    def _update_detail(self):
        """Detay panelini güncelle"""
        if not self._current_session:
            return

        # Full JSON çıktısı
        payload = {
            "session": {
                "id": self._current_session.id,
                "user_id": self._current_session.user_id,
                "started_at": self._current_session.started_at.isoformat(),
                "ended_at": (
                    self._current_session.ended_at.isoformat()
                    if self._current_session.ended_at
                    else None
                ),
                "status": self._current_session.status.value,
                "total_events": len(self._events),
            },
            "events": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "type": e.event_type.value,
                    "widget_name": e.widget_name,
                    "widget_path": e.widget_path,
                    "data": e.event_data,
                    "duration_ms": e.duration_ms,
                }
                for e in self._events
            ],
        }

        if self._current_session.error_log:
            payload["error"] = {
                "type": self._current_session.error_log.error_type,
                "message": self._current_session.error_log.error_message,
                "traceback": self._current_session.error_log.error_traceback,
            }

        self.detail_text.setText(json.dumps(payload, indent=2, ensure_ascii=False))

    def _update_inspection(self):
        """İnceleme panelini HTML formatında güncelle"""
        if not self._current_session:
            return

        session = self._current_session
        events = self._events

        lines = []
        user_name = session.user.username if session.user else "?"
        start_time = session.started_at.strftime("%H:%M:%S")

        # Başlangıç Satırı
        lines.append(
            f"<div style='color:#6c5ce7'><b>BAŞLANGIÇ [{start_time}]:</b> "
            f"Destek Modu Açıldı (Kullanıcı: {user_name})</div>"
        )

        for event in events:
            time_str = event.timestamp.strftime("%H:%M:%S")
            data = event.event_data or {}

            line = ""

            # 1. SAYFA (Navigasyon)
            if event.event_type == TraceEventType.PAGE_NAVIGATION:
                page = event.widget_name or "Bilinmeyen Sayfa"
                line = (
                    f"<span style='color:#e67e22'><b>SAYFA:</b> {page} açıldı.</span>"
                )

            # 2. FİLTRE (Arama / Form Input)
            elif event.event_type == TraceEventType.FORM_INPUT:
                if "SearchInput" in (event.widget_name or "") or data.get(
                    "placeholder", ""
                ).startswith("Ara"):
                    val = data.get("value", "")
                    line = f"<span style='color:#3498db'><b>FİLTRE:</b> '{val}' araması yapıldı.</span>"
                elif data.get("action") == "clipboard_copy":
                    line = f"<span style='color:#3498db'><b>COPY (Panoya Kopyalandı):</b> {data.get('source_widget')}</span>"
                elif data.get("action") == "clipboard_paste":
                    content = data.get("content", "")
                    line = f"<span style='color:#3498db'><b>PASTE (Yapıştırıldı):</b> '{content}'</span>"
                else:
                    field = event.widget_name
                    val = data.get("value", "")
                    line = f"<span><b>GİRİŞ:</b> {field} = '{val}'</span>"

            # 3. SEÇİM (Tablo Seçimi)
            elif event.event_type == TraceEventType.TABLE_SELECTION:
                detail = ""
                if "item_text" in data:
                    detail = f"'{data['item_text']}'"
                elif "row_index" in data:
                    # col_0, col_1 gibi verileri topla
                    cols = [v for k, v in data.items() if k.startswith("col_")]
                    detail = (
                        f"Satır {data['row_index']} ({', '.join(str(c) for c in cols)})"
                    )

                line = f"<span style='color:#2ecc71'><b>SEÇİM:</b> {detail} seçildi.</span>"

            # 4. BUTON
            elif event.event_type == TraceEventType.BUTTON_CLICK:
                btn_text = data.get("button_text", event.widget_name)
                line = f"<span style='color:#2ecc71'><b>BUTON:</b> '{btn_text}' butonuna tıklandı.</span>"

            # 5. SERVİS (Method Call)
            elif event.event_type == TraceEventType.METHOD_CALL:
                method = event.widget_name
                duration = data.get("duration_ms", 0)
                line = f"<span style='color:#9b59b6'><b>SERVİS:</b> {method} çağrıldı ({duration}ms).</span>"

            # 6. SQL
            elif event.event_type == TraceEventType.SQL_QUERY:
                sql = data.get("sql", "")
                duration = data.get("duration_ms", 0)
                # SQL'i biraz kısalt
                if len(sql) > 150:
                    sql = sql[:150] + "..."
                row_count = data.get("row_count", 0)
                line = f"<span style='color:#bdc3c7'><i>SQL: {sql} (Süre: {duration}ms, Rows: {row_count})</i></span>"

            # 7. LOG / MESSAGE BOX
            elif event.event_type == TraceEventType.LOG_ENTRY:
                msg_type = data.get("type", "")
                if msg_type == "message_box":
                    title = data.get("title", "")
                    msg = data.get("message", "")
                    level = data.get("level", "")
                    color = "#e74c3c" if level in ("critical", "warning") else "#3498db"
                    line = f"<span style='color:{color}'><b>UYARI ({level}):</b> [{title}] {msg}</span>"
                else:
                    line = f"<span style='color:#bdc3c7'>LOG: {data}</span>"

            # 8. HATA
            elif event.event_type == TraceEventType.ERROR_OCCURRED:
                err_type = data.get("error_type", "Hata")
                err_msg = data.get("error_message", "")
                line = f"<span style='color:#e74c3c'><b>HATA:</b> {err_type}: {err_msg}</span>"

            # 9. SYSTEM
            elif event.event_type == TraceEventType.SYSTEM_STATS:
                cpu = data.get("cpu_percent", 0)
                ram = data.get("memory_percent", 0)
                line = f"<span style='color:#ecf0f1'><b>SİSTEM:</b> CPU: %{cpu}, RAM: %{ram}</span>"

            # Diğerleri
            else:
                line = f"<span>{event.event_type.value}: {event.widget_name}</span>"

            if line:
                lines.append(f"<div><small>[{time_str}]</small> {line}</div><br>")

        # Bitiş Satırı
        end_time = (
            session.ended_at.strftime("%H:%M:%S")
            if session.ended_at
            else "Devam Ediyor"
        )
        status_tr = {
            "active": "Aktif",
            "completed": "Tamamlandı",
            "error": "Hata",
            "timeout": "Zaman Aşımı",
        }.get(session.status.value, session.status.value)

        lines.append(
            f"<div style='color:#6c5ce7'><b>BİTİŞ [{end_time}]:</b> "
            f"Trace durumu: {status_tr}.</div>"
        )

        self.inspection_text.setHtml("".join(lines))

    def _on_event_selected(self):
        """Event seçildiğinde detay paneline odaklan"""
        selected_rows = self.event_table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            if row < len(self._events):
                event = self._events[row]
                # Detay metnini seçili event'e göre güncelle
                event_json = {
                    "timestamp": event.timestamp.isoformat(),
                    "type": event.event_type.value,
                    "widget_name": event.widget_name,
                    "widget_path": event.widget_path,
                    "data": event.event_data,
                    "duration_ms": event.duration_ms,
                }
                self.detail_text.setText(
                    json.dumps(event_json, indent=2, ensure_ascii=False)
                )

    def _export_json(self):
        """JSON olarak export et"""
        from PyQt6.QtWidgets import QFileDialog

        if not self._current_session:
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "JSON Kaydet",
            f"trace_{self._current_session.id}.json",
            "JSON Files (*.json)",
        )

        if filename:
            try:
                payload = json.loads(self.detail_text.toPlainText())
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[TraceDetailPage] export error: {e}")
