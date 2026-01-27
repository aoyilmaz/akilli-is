"""
Akıllı İş - Kapasite Darboğaz Widget

Dashboard için kapasite darboğazlarını gösteren widget.
30 gün içinde %100+ yüklenmiş istasyonları kırmızı barlarla gösterir.
"""

from datetime import date, timedelta
from typing import List, Dict, Optional
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QProgressBar,
    QFrame,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QFont

from core.threads.worker_manager import WorkerManager


class CapacityBar(QWidget):
    """Kapasite doluluk barı."""

    def __init__(self, utilization: float, parent=None):
        super().__init__(parent)
        self.utilization = utilization
        self.setMinimumHeight(20)
        self.setMaximumHeight(20)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        height = rect.height()
        width = rect.width()

        # Arka plan
        painter.setBrush(QBrush(QColor("#e5e7eb")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, width, height, 4, 4)

        # Doluluk barı
        fill_width = min(width, int(width * self.utilization / 100))

        # Renk seçimi
        if self.utilization >= 100:
            color = QColor("#ef4444")  # Kırmızı
        elif self.utilization >= 80:
            color = QColor("#f59e0b")  # Turuncu
        else:
            color = QColor("#10b981")  # Yeşil

        painter.setBrush(QBrush(color))
        painter.drawRoundedRect(0, 0, fill_width, height, 4, 4)

        # Yüzde metni
        painter.setPen(QPen(QColor("#1f2937")))
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"%{self.utilization:.0f}")


class CapacityBottleneckWidget(QWidget):
    """
    Kapasite Darboğaz Widget

    Gelecek N gün içinde >%100 yüklenmiş istasyonları gösterir.
    Her satırda "Dengele" butonu ile yük dengeleme yapılabilir.
    """

    balance_requested = pyqtSignal(int, object)  # station_id, date

    def __init__(self, parent=None):
        super().__init__(parent)
        self.aps_service = None
        self.period_days = 30
        self.threshold = 100.0
        self.bottlenecks = []

        self.setup_ui()

        # Otomatik yenileme (5 dakikada bir)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.load_data)
        self.refresh_timer.start(5 * 60 * 1000)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Başlık
        header = QHBoxLayout()

        title = QLabel("🔥 Kapasite Darboğazları")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        header.addWidget(title)

        header.addStretch()

        # Dönem seçici
        self.period_combo = QComboBox()
        self.period_combo.addItem("7 Gün", 7)
        self.period_combo.addItem("14 Gün", 14)
        self.period_combo.addItem("30 Gün", 30)
        self.period_combo.setCurrentIndex(2)
        self.period_combo.currentIndexChanged.connect(self._on_period_changed)
        self.period_combo.setFixedWidth(100)
        header.addWidget(self.period_combo)

        # Yenile butonu
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedSize(32, 32)
        self.refresh_btn.setToolTip("Yenile")
        self.refresh_btn.clicked.connect(self.load_data)
        header.addWidget(self.refresh_btn)

        layout.addLayout(header)

        # Darboğaz tablosu
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "İstasyon", "Tarih", "Doluluk", "Fazla Yük", "Aksiyon"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 80)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        # Özet
        self.summary_frame = QFrame()
        self.summary_frame.setStyleSheet(
            "background-color: #fef3c7; border-radius: 4px; padding: 8px;"
        )
        summary_layout = QHBoxLayout(self.summary_frame)
        summary_layout.setContentsMargins(8, 4, 8, 4)

        self.summary_label = QLabel("Yükleniyor...")
        summary_layout.addWidget(self.summary_label)

        summary_layout.addStretch()

        self.balance_all_btn = QPushButton("Tümünü Dengele")
        self.balance_all_btn.setVisible(False)
        self.balance_all_btn.clicked.connect(self._balance_all)
        summary_layout.addWidget(self.balance_all_btn)

        layout.addWidget(self.summary_frame)

    def set_service(self, aps_service):
        """APS servisini ayarla."""
        self.aps_service = aps_service
        self.load_data()

    def load_data(self):
        """Darboğaz verilerini yükle."""
        if not self.aps_service:
            self.summary_label.setText("Servis bağlantısı yok")
            return

        start = date.today()
        end = start + timedelta(days=self.period_days)

        # Arka planda yükle
        def fetch():
            return self.aps_service.get_bottleneck_stations(
                start, end, self.threshold
            )

        def on_result(bottlenecks):
            self.bottlenecks = bottlenecks
            self._update_table()

        def on_error(error):
            self.summary_label.setText(f"Hata: {str(error)}")

        WorkerManager().run_task(fetch, on_result=on_result, on_error=on_error)

    def _update_table(self):
        """Tabloyu güncelle."""
        self.table.setRowCount(len(self.bottlenecks))

        for row, bn in enumerate(self.bottlenecks):
            # İstasyon
            station_item = QTableWidgetItem(
                f"{bn['station_code']} - {bn['station_name']}"
            )
            self.table.setItem(row, 0, station_item)

            # Tarih
            date_item = QTableWidgetItem(bn["date"].strftime("%d.%m.%Y"))
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, date_item)

            # Doluluk barı
            bar = CapacityBar(bn["utilization"])
            self.table.setCellWidget(row, 2, bar)

            # Fazla yük
            overload_item = QTableWidgetItem(f"{bn['overload_minutes']} dk")
            overload_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if bn["overload_minutes"] > 0:
                overload_item.setForeground(QColor("#ef4444"))
            self.table.setItem(row, 3, overload_item)

            # Dengele butonu
            balance_btn = QPushButton("Dengele")
            balance_btn.setFixedSize(70, 24)
            balance_btn.clicked.connect(
                lambda checked, s=bn["station_id"], d=bn["date"]:
                    self._on_balance_clicked(s, d)
            )

            # Alternatif yoksa disable et
            if not bn.get("alternatives"):
                balance_btn.setEnabled(False)
                balance_btn.setToolTip("Alternatif istasyon yok")

            self.table.setCellWidget(row, 4, balance_btn)

        # Özet güncelle
        total = len(self.bottlenecks)
        critical = sum(1 for bn in self.bottlenecks if bn["utilization"] >= 120)

        if total == 0:
            self.summary_frame.setStyleSheet(
                "background-color: #d1fae5; border-radius: 4px; padding: 8px;"
            )
            self.summary_label.setText("✅ Darboğaz tespit edilmedi")
            self.balance_all_btn.setVisible(False)
        else:
            color = "#fef3c7" if critical == 0 else "#fee2e2"
            self.summary_frame.setStyleSheet(
                f"background-color: {color}; border-radius: 4px; padding: 8px;"
            )
            self.summary_label.setText(
                f"⚠️ {total} darboğaz ({critical} kritik) - "
                f"Gelecek {self.period_days} gün içinde"
            )
            self.balance_all_btn.setVisible(total > 0)

    def _on_period_changed(self, index):
        """Dönem değiştiğinde."""
        self.period_days = self.period_combo.currentData()
        self.load_data()

    def _on_balance_clicked(self, station_id: int, target_date: date):
        """Dengele butonuna tıklandığında."""
        self.balance_requested.emit(station_id, target_date)

        # Veya direkt denge işlemi yap
        if self.aps_service:
            def balance():
                return self.aps_service.balance_load(station_id, target_date)

            def on_result(result):
                moved = len(result.get("moved_operations", []))
                if moved > 0:
                    QMessageBox.information(
                        self,
                        "Yük Dengeleme",
                        f"{moved} operasyon taşındı.\n"
                        f"Yeni doluluk: %{result.get('new_utilization', 0):.0f}",
                    )
                else:
                    QMessageBox.information(
                        self,
                        "Yük Dengeleme",
                        "Taşınabilir operasyon bulunamadı.",
                    )
                self.load_data()

            def on_error(error):
                QMessageBox.warning(
                    self,
                    "Hata",
                    f"Yük dengeleme başarısız: {str(error)}",
                )

            WorkerManager().run_task(balance, on_result=on_result, on_error=on_error)

    def _balance_all(self):
        """Tüm darboğazları dengele."""
        if not self.aps_service:
            return

        reply = QMessageBox.question(
            self,
            "Tümünü Dengele",
            f"{len(self.bottlenecks)} darboğaz için yük dengeleme yapılacak.\n"
            "Devam etmek istiyor musunuz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        def balance_all():
            total_moved = 0
            for bn in self.bottlenecks:
                result = self.aps_service.balance_load(bn["station_id"], bn["date"])
                total_moved += len(result.get("moved_operations", []))
            return total_moved

        def on_result(total):
            QMessageBox.information(
                self,
                "Yük Dengeleme",
                f"Toplam {total} operasyon taşındı.",
            )
            self.load_data()

        WorkerManager().run_task(balance_all, on_result=on_result)
