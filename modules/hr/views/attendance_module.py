"""
Akıllı İş - Puantaj Yönetim Modülü

PDKS verilerini görüntüler, import eder ve yönetir.
"""

from datetime import date, datetime
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidgetItem,
    QDialog,
    QFormLayout,
    QMessageBox,
    QLabel,
    QComboBox,
    QSpinBox,
    QFileDialog,
    QFrame,
)
from PyQt6.QtCore import Qt, QDate, QTimer
import qtawesome as qta

from config.icons import ICONS
from config.themes import get_theme
from ui.components import PageHeader, MiniStatCard
from ui.components.enhanced_table import EnhancedTableWidget, ColumnConfig
from modules.hr.services import HRService, PDKSService


class ImportDialog(QDialog):
    """PDKS Veri Import Dialogu"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_path = None
        self.setWindowTitle("PDKS Verisi İçe Aktar")
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(12)

        # Cihaz seçimi
        self.device_combo = QComboBox()
        self.device_combo.addItems(["ZKTeco", "Meyer", "Polimek", "Excel / CSV"])
        layout.addRow("Cihaz Türü:", self.device_combo)

        # Dosya seçimi
        f_layout = QHBoxLayout()
        self.file_label = QLabel("Dosya seçilmedi")
        f_btn = QPushButton("Dosya Seç")
        f_btn.setIcon(qta.icon(ICONS.FOLDER, color="white"))
        f_btn.setProperty("class", "btn-secondary")
        f_btn.clicked.connect(self._select_file)
        f_layout.addWidget(self.file_label, 1)
        f_layout.addWidget(f_btn)
        layout.addRow("Dosya:", f_layout)

        # Dönem
        self.month_combo = QComboBox()
        months = [
            "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
            "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
        ]
        for i, m in enumerate(months, 1):
            self.month_combo.addItem(m, i)
        self.month_combo.setCurrentIndex(date.today().month - 1)
        layout.addRow("Dönem Ayı:", self.month_combo)

        # Butonlar
        btn_layout = QHBoxLayout()
        import_btn = QPushButton("İçe Aktar")
        import_btn.setIcon(qta.icon(ICONS.SAVE, color="white"))
        import_btn.setProperty("class", "btn-primary")
        import_btn.setFixedHeight(36)
        import_btn.clicked.connect(self.accept)

        cancel_btn = QPushButton("İptal")
        cancel_btn.setFixedHeight(36)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(import_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Dosya Seç", "", "Data Files (*.dat *.txt *.csv *.xlsx)"
        )
        if path:
            self.file_path = path
            self.file_label.setText(path.split("/")[-1])


class AttendanceModule(QWidget):
    """Puantaj yönetim modülü"""

    page_title = "Puantaj"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hr_service = None
        self.pdks_service = None
        self._total_count = 0
        self.setup_ui()
        self.load_data()

        # Otomatik yenileme
        self._auto_refresh_timer = QTimer(self)
        self._auto_refresh_timer.timeout.connect(self.load_data)
        self._auto_refresh_timer.start(30000)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        self.header = PageHeader(
            title="Puantaj Yönetimi",
            icon=ICONS.CALENDAR,
            show_search=True,
            parent=self,
        )
        self.header.search_changed.connect(self.load_data)

        h_layout = self.header.header_layout()

        # Ek aksiyon butonları
        t = get_theme()
        import_btn = QPushButton("Veri İçe Aktar")
        import_btn.setIcon(qta.icon(ICONS.SAVE, color=t.success))
        import_btn.setProperty("class", "btn-secondary")
        import_btn.clicked.connect(self._import_data)
        h_layout.addWidget(import_btn)

        calc_btn = QPushButton("Puantaj Hesapla")
        calc_btn.setIcon(qta.icon(ICONS.DASHBOARD, color=t.accent_primary))
        calc_btn.setProperty("class", "btn-secondary")
        calc_btn.clicked.connect(self._calculate_attendance)
        h_layout.addWidget(calc_btn)

        layout.addWidget(self.header)

        # Dönem Seçimi ve Filtreler
        filter_card = QFrame()
        filter_card.setStyleSheet(
            f"""
            QFrame {{
                background: {t.card_bg};
                border: 1px solid {t.border};
                border-radius: 8px;
            }}
        """
        )
        filter_layout = QHBoxLayout(filter_card)

        filter_layout.addWidget(QLabel("Dönem:"))
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2020, 2100)
        self.year_spin.setValue(date.today().year)
        self.year_spin.setFixedHeight(36)
        self.year_spin.valueChanged.connect(self.load_data)
        filter_layout.addWidget(self.year_spin)

        self.month_filter = QComboBox()
        months = [
            "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
            "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
        ]
        for i, m in enumerate(months, 1):
            self.month_filter.addItem(m, i)
        self.month_filter.setCurrentIndex(date.today().month - 1)
        self.month_filter.setFixedHeight(36)
        self.month_filter.setFixedWidth(120)
        self.month_filter.currentIndexChanged.connect(self.load_data)
        filter_layout.addWidget(self.month_filter)

        filter_layout.addSpacing(20)
        filter_layout.addWidget(QLabel("Departman:"))
        self.dept_combo = QComboBox()
        self.dept_combo.setFixedWidth(200)
        self.dept_combo.setFixedHeight(36)
        self.dept_combo.currentIndexChanged.connect(self.load_data)
        filter_layout.addWidget(self.dept_combo)

        filter_layout.addStretch()
        layout.addWidget(filter_card)

        # Tablo
        columns = [
            ColumnConfig("employee_no", "Sicil No", width=100),
            ColumnConfig("employee_name", "Çalışan", width=200, stretch=True),
            ColumnConfig("department", "Departman", width=150),
            ColumnConfig("present_days", "Mevcut", width=80),
            ColumnConfig("late_days", "Geç", width=80),
            ColumnConfig("absent_days", "Devamsız", width=80),
            ColumnConfig("leave_days", "İzin", width=80),
            ColumnConfig("total_hours", "Toplam Saat", width=100),
        ]
        self.table = EnhancedTableWidget(
            table_id="attendance_summary", columns=columns, parent=self
        )
        self.table.set_standard_row_height(48)
        self.table.filter_changed.connect(self._update_visible_count)

        layout.addWidget(self.table)

        # Footer
        self._setup_footer(layout)

    def _setup_footer(self, layout: QVBoxLayout):
        """Footer - kayıt sayısı ve istatistikler"""
        footer = QFrame()
        footer.setProperty("class", "table-footer")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(0, 8, 0, 0)
        footer_layout.setSpacing(16)

        # Sol: Kayıt sayısı
        self.count_label = QLabel("Toplam: 0 çalışan")
        self.count_label.setProperty("class", "footer-count")
        footer_layout.addWidget(self.count_label)

        # İstatistik kartları (horizontal)
        self.stat_cards = {
            "present": MiniStatCard(
                "Mevcut", "0", "success", orientation="horizontal", icon=ICONS.CHECK
            ),
            "late": MiniStatCard(
                "Geç Kalan", "0", "warning", orientation="horizontal", icon=ICONS.TIME
            ),
            "absent": MiniStatCard(
                "Devamsız", "0", "error", orientation="horizontal", icon=ICONS.CLOSE
            ),
            "leave": MiniStatCard(
                "İzinli", "0", "info", orientation="horizontal", icon=ICONS.CALENDAR
            ),
        }
        for card in self.stat_cards.values():
            footer_layout.addWidget(card)

        footer_layout.addStretch()

        # Sağ: Otomatik yenileme göstergesi
        refresh_indicator = QLabel("⟳")
        refresh_indicator.setProperty("class", "refresh-indicator")
        refresh_indicator.setToolTip("Otomatik yenileme: 30s")
        footer_layout.addWidget(refresh_indicator)

        layout.addWidget(footer)

    def _get_hr_service(self):
        if self.hr_service is None:
            self.hr_service = HRService()
        return self.hr_service

    def _get_pdks_service(self):
        if self.pdks_service is None:
            self.pdks_service = PDKSService()
        return self.pdks_service

    def _close_services(self):
        if self.hr_service:
            self.hr_service.close()
            self.hr_service = None
        if self.pdks_service:
            self.pdks_service.close()
            self.pdks_service = None

    def load_data(self):
        """Puantaj verilerini yükle"""
        try:
            hr_service = self._get_hr_service()
            pdks_service = self._get_pdks_service()

            # Departman combobox'ı doldur (ilk yüklemede)
            if self.dept_combo.count() == 0:
                self.dept_combo.addItem("Tümü", None)
                for dept in hr_service.get_all_departments():
                    self.dept_combo.addItem(dept.name, dept.id)

            year = self.year_spin.value()
            month = self.month_filter.currentData()
            dept_id = self.dept_combo.currentData()
            search = self.header.get_search_text() or None

            # PDKS servisi üzerinden verileri al
            summary = pdks_service.get_monthly_summary(
                year=year, month=month, department_id=dept_id, search=search
            )

            self.table.setRowCount(len(summary))
            visible_cols = self.table.get_visible_columns()

            total_present = 0
            total_late = 0
            total_absent = 0
            total_leave = 0

            for row, data in enumerate(summary):
                self._populate_row(row, data, visible_cols)
                total_present += data.get("present_days", 0)
                total_late += data.get("late_days", 0)
                total_absent += data.get("absent_days", 0)
                total_leave += data.get("leave_days", 0)

            # İstatistikleri güncelle
            self.stat_cards["present"].update_value(str(total_present))
            self.stat_cards["late"].update_value(str(total_late))
            self.stat_cards["absent"].update_value(str(total_absent))
            self.stat_cards["leave"].update_value(str(total_leave))
            self._total_count = len(summary)
            self.count_label.setText(f"Toplam: {self._total_count} çalışan")

        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Veriler yüklenirken hata:\n{str(e)}")
        finally:
            self._close_services()

    def _update_visible_count(self, filters: dict = None):
        """Görünen satır sayısını güncelle"""
        visible_count = sum(
            1 for row in range(self.table.rowCount())
            if not self.table.isRowHidden(row)
        )
        if visible_count == self._total_count:
            self.count_label.setText(f"Toplam: {self._total_count} çalışan")
        else:
            self.count_label.setText(
                f"Gösterilen: {visible_count} / {self._total_count} çalışan"
            )

    def _populate_row(self, row, data, visible_cols):
        for col_idx, col_key in enumerate(visible_cols):
            val = data.get(col_key, "-")
            if isinstance(val, (int, float)):
                val = str(val)
            item = QTableWidgetItem(val)
            self.table.setItem(row, col_idx, item)

    def _import_data(self):
        """Veri içe aktar"""
        dialog = ImportDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()

    def _calculate_attendance(self):
        """Puantaj hesapla"""
        year = self.year_spin.value()
        month = self.month_filter.currentData()

        reply = QMessageBox.question(
            self,
            "Puantaj Hesapla",
            f"{self.month_filter.currentText()} {year} dönemi için puantaj hesaplanacaktır.\nEmin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                pdks_service = self._get_pdks_service()
                pdks_service.calculate_monthly_attendance(year, month)
                QMessageBox.information(
                    self, "Başarılı", "Puantaj hesaplama tamamlandı."
                )
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Puantaj hesaplanamadı:\n{str(e)}")
            finally:
                self._close_services()

    def showEvent(self, event):
        super().showEvent(event)
        self._auto_refresh_timer.start(30000)

    def hideEvent(self, event):
        super().hideEvent(event)
        self._auto_refresh_timer.stop()
