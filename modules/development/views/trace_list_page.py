"""
Akıllı İş - Trace List Page
Trace session listesi
"""

from datetime import datetime
from typing import List

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QDateEdit,
    QLabel,
    QHeaderView,
)
from PyQt6.QtCore import pyqtSignal, Qt, QDate
from PyQt6.QtGui import QColor

from database.base import get_session
from database.models.development import TraceSession, TraceStatus
from ui.components.enhanced_table import EnhancedTableWidget


class TraceListPage(QWidget):
    """
    Trace Session Listesi

    Filtreler:
    - Tarih aralığı (Header'da)
    """

    session_selected = pyqtSignal(int)  # session_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """UI bileşenlerini oluştur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        from ui.components.page_header import PageHeader

        self.header = PageHeader(
            title="Trace Oturumları",
            show_search=False,
            show_add=False,
            show_refresh=True,
            show_back=False,
        )
        self.header.refresh_clicked.connect(self.refresh)

        # Tarih filtresini header'a ekle
        header_layout = self.header.header_layout()

        # Spacer'dan önce eklemek için (addStretch PageHeader'da var)
        # PageHeader yapısı: [Back] [Title/Icon] [Stretch] [Search] [Buttons...]
        # Biz Search yerine veya Stretch'ten sonra tarihleri ekleyelim.
        # PageHeader layout'una widget ekleyince sona eklenir (Search'ten sonra).
        # Arama kapalı olduğu için butonlardan önce gelecek.

        date_container = QWidget()
        date_layout = QHBoxLayout(date_container)
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.setSpacing(8)

        date_label = QLabel("Tarih:")
        date_label.setStyleSheet("color: #ecf0f1;")
        date_layout.addWidget(date_label)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-7))
        self.date_from.setDisplayFormat("dd.MM.yyyy")
        self.date_from.setFixedWidth(130)
        self.date_from.setStyleSheet(
            "background-color: #2d2d2d; color: white; border: 1px solid #3d3d3d; border-radius: 4px; padding: 4px;"
        )
        date_layout.addWidget(self.date_from)

        sep_label = QLabel("-")
        sep_label.setStyleSheet("color: #ecf0f1;")
        date_layout.addWidget(sep_label)

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setDisplayFormat("dd.MM.yyyy")
        self.date_to.setFixedWidth(130)
        self.date_to.setStyleSheet(
            "background-color: #2d2d2d; color: white; border: 1px solid #3d3d3d; border-radius: 4px; padding: 4px;"
        )
        date_layout.addWidget(self.date_to)

        # Tarih container'ını header'ın butonlarından önce eklemek için insertWidget kullanmalıyız ama
        # PageHeader layout indexlerini bilmiyoruz. addWidget sona ekler.
        # PageHeader'da butonlar addWidget ile ekleniyor.
        # Bizim eklediğimiz de en sona eklenecek. İdeal değil ama çalışır.
        # Ancak PageHeader'da butonlar sağa dayalı.
        # add_action_button metodunu kullanalım (layout'un sonuna ekler).

        # Ancak butonlardan önce görünmesi daha şık olur.
        # Layout tersten: Add, Refresh, Export, Filter, Search.
        # Bizimki Refresh'in solunda olsun istiyoruz.
        # count() - 1 (Refresh butonu varsa) pozisyonuna insert etmeyi deneyebiliriz.

        # Refresh butonu en sonda (Show Add False olduğu için).
        # Refresh varsa layout.count() - 1 indexindedir.

        idx = header_layout.count()
        if self.header.refresh_btn:
            idx -= 1

        header_layout.insertWidget(idx, date_container)

        layout.addWidget(self.header)

        # Tablo
        from ui.components.enhanced_table import ColumnConfig

        columns = [
            ColumnConfig("id", "ID", 60),
            ColumnConfig("username", "Kullanıcı", 120),
            ColumnConfig("started_at", "Başlangıç", 140),
            ColumnConfig("ended_at", "Bitiş", 140),
            ColumnConfig("status", "Durum", 100),
            ColumnConfig("event_count", "Event Sayısı", 100),
            ColumnConfig("error", "Hata", 200, stretch=True),
        ]

        self.table = EnhancedTableWidget(table_id="trace_list", columns=columns)

        # Çift tıklama olayı
        self.table.row_double_clicked.connect(self._on_row_double_clicked)

        layout.addWidget(self.table)

        # Butonlar vs. için alt panel (gerekirse)

    def _connect_signals(self):
        """Sinyalleri bağla"""
        self.date_from.dateChanged.connect(self.refresh)
        self.date_to.dateChanged.connect(self.refresh)
        # Tablo refresh desteği varsa bağla (EnhancedTableWidget'ta refresh sinyali olup olmadığını kontrol etmek lazım)
        if hasattr(self.table, "refresh_requested"):
            self.table.refresh_requested.connect(self.refresh)

    def refresh(self):
        """Verileri yenile"""
        try:
            sessions = self._load_sessions()
            self._populate_table(sessions)
        except Exception as e:
            print(f"[TraceListPage] refresh error: {e}")

    def _load_sessions(self) -> List[TraceSession]:
        """Session'ları veritabanından yükle"""
        session = get_session()
        query = session.query(TraceSession)

        # Tarih filtresi
        date_from = self.date_from.date().toPyDate()
        date_to = self.date_to.date().toPyDate()
        query = query.filter(
            TraceSession.started_at >= datetime.combine(date_from, datetime.min.time()),
            TraceSession.started_at <= datetime.combine(date_to, datetime.max.time()),
        )

        # Sıralama (en yeni önce)
        query = query.order_by(TraceSession.started_at.desc())

        return query.limit(100).all()

    def _populate_table(self, sessions: List[TraceSession]):
        """Tabloyu doldur"""
        self.table.setRowCount(0)  # Önce temizle

        status_colors = {
            TraceStatus.ACTIVE: "#28a745",  # Yeşil
            TraceStatus.COMPLETED: "#0d6efd",  # Mavi
            TraceStatus.ERROR: "#dc3545",  # Kırmızı
            TraceStatus.TIMEOUT: "#ffc107",  # Sarı
        }

        status_labels = {
            TraceStatus.ACTIVE: "Aktif",
            TraceStatus.COMPLETED: "Tamamlandı",
            TraceStatus.ERROR: "Hata",
            TraceStatus.TIMEOUT: "Zaman Aşımı",
        }

        data = []
        for trace_session in sessions:
            row_data = []

            # ID
            row_data.append(str(trace_session.id))

            # Kullanıcı
            username = trace_session.user.username if trace_session.user else "?"
            row_data.append(username)

            # Başlangıç
            start_str = trace_session.started_at.strftime("%d.%m.%Y %H:%M:%S")
            row_data.append(start_str)

            # Bitiş
            end_str = (
                trace_session.ended_at.strftime("%d.%m.%Y %H:%M:%S")
                if trace_session.ended_at
                else "-"
            )
            row_data.append(end_str)

            # Durum
            status_text = status_labels.get(trace_session.status, "?")
            # Renk bilgisini EnhancedTableWidget'a geçiremiyoruz direkt olarak add_row ile ama
            # item bazlı işlem yapabiliriz aşağıda
            row_data.append(status_text)

            # Event Sayısı
            row_data.append(str(trace_session.total_events))

            # Hata
            error_text = (
                trace_session.error_log.error_type if trace_session.error_log else "-"
            )
            row_data.append(error_text)

            data.append(row_data)

        # Tabloya verileri ekle
        for i, row_values in enumerate(data):
            self.table.insertRow(i)
            trace_session = sessions[i]

            for j, val in enumerate(row_values):
                from PyQt6.QtWidgets import QTableWidgetItem

                item = QTableWidgetItem(str(val))

                # ID için data sakla
                if j == 0:
                    item.setData(Qt.ItemDataRole.UserRole, int(val))

                # Durum kolonu renklendirme (4. indeks)
                if j == 4:
                    color_code = status_colors.get(trace_session.status)
                    if color_code:
                        item.setForeground(QColor(color_code))
                        item.setToolTip(f"Durum: {val}")

                self.table.setItem(i, j, item)

    def _on_row_double_clicked(self, session_id):
        """Satır çift tıklandığında"""
        self.session_selected.emit(session_id)
