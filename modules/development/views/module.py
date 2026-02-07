"""
Akıllı İş - Geliştirme Modülü
Hata Kayıtları ve Loglama
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QComboBox,
    QCheckBox,
    QMessageBox,
    QHeaderView,
    QAbstractItemView,
    QGroupBox,
    QTextEdit,
    QDialog,
    QTabWidget,
)
from PyQt6.QtCore import Qt
from datetime import datetime, timedelta

from modules.development.services import ErrorLogService
from database.models.development import ErrorSeverity


class ErrorDetailDialog(QDialog):
    """Hata detayı göster dialog"""

    def __init__(self, error_log, parent=None):
        super().__init__(parent)
        self.error_log = error_log
        self.setWindowTitle(f"Hata Detayı - #{error_log.id}")
        self.resize(800, 600)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Başlık bilgileri
        info_layout = QHBoxLayout()

        # Sol taraf
        left_info = QVBoxLayout()
        left_info.addWidget(QLabel(f"<b>Hata Türü:</b> {self.error_log.error_type}"))
        left_info.addWidget(
            QLabel(f"<b>Modül:</b> {self.error_log.module_name or 'N/A'}")
        )
        left_info.addWidget(
            QLabel(f"<b>Ekran:</b> {self.error_log.screen_name or 'N/A'}")
        )
        left_info.addWidget(
            QLabel(f"<b>Fonksiyon:</b> {self.error_log.function_name or 'N/A'}")
        )
        info_layout.addLayout(left_info)

        # Sağ taraf
        right_info = QVBoxLayout()
        right_info.addWidget(
            QLabel(f"<b>Kullanıcı:</b> {self.error_log.username or 'N/A'}")
        )
        right_info.addWidget(
            QLabel(
                f"<b>Tarih:</b> {self.error_log.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        )
        right_info.addWidget(
            QLabel(f"<b>Severity:</b> {self.error_log.severity.value}")
        )
        right_info.addWidget(
            QLabel(
                f"<b>Çözüldü:</b> {'Evet' if self.error_log.is_resolved else 'Hayır'}"
            )
        )
        info_layout.addLayout(right_info)

        layout.addLayout(info_layout)

        # Hata mesajı
        layout.addWidget(QLabel("<b>Hata Mesajı:</b>"))
        msg_text = QTextEdit()
        msg_text.setReadOnly(True)
        msg_text.setPlainText(self.error_log.error_message)
        msg_text.setMaximumHeight(80)
        layout.addWidget(msg_text)

        # Traceback
        layout.addWidget(QLabel("<b>Traceback:</b>"))
        traceback_text = QTextEdit()
        traceback_text.setReadOnly(True)
        traceback_text.setPlainText(self.error_log.error_traceback or "N/A")
        layout.addWidget(traceback_text)

        # Dosya bilgisi
        if self.error_log.file_path:
            file_info = f"{self.error_log.file_path}"
            if self.error_log.line_number:
                file_info += f":{self.error_log.line_number}"
            layout.addWidget(QLabel(f"<b>Dosya:</b> {file_info}"))

        # Kapat butonu
        close_btn = QPushButton("Kapat")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class ErrorLogsWidget(QWidget):
    """Hata kayıtları listesi widget'ı"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Başlık
        # header = QLabel("<h2>⚙️ Hata Kayıtları</h2>")
        # layout.addWidget(header)

        # Filtreler
        filter_group = QGroupBox("Filtreler")
        filter_layout = QHBoxLayout()

        # Modül filtresi
        filter_layout.addWidget(QLabel("Modül:"))
        self.module_combo = QComboBox()
        self.module_combo.addItem("Tümü", None)
        self.module_combo.addItem("inventory", "inventory")
        self.module_combo.addItem("production", "production")
        self.module_combo.addItem("purchasing", "purchasing")
        self.module_combo.currentIndexChanged.connect(self.load_data)
        filter_layout.addWidget(self.module_combo)

        # Severity filtresi
        filter_layout.addWidget(QLabel("Severity:"))
        self.severity_combo = QComboBox()
        self.severity_combo.addItem("Tümü", None)
        self.severity_combo.addItem("🔴 Critical", "critical")
        self.severity_combo.addItem("🔴 Error", "error")
        self.severity_combo.addItem("🟡 Warning", "warning")
        self.severity_combo.addItem("🔵 Info", "info")
        self.severity_combo.currentIndexChanged.connect(self.load_data)
        filter_layout.addWidget(self.severity_combo)

        # Çözüm durumu
        self.resolved_check = QCheckBox("Sadece çözülmemiş")
        self.resolved_check.setChecked(True)
        self.resolved_check.stateChanged.connect(self.load_data)
        filter_layout.addWidget(self.resolved_check)

        filter_layout.addStretch()

        # Yenile butonu
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.clicked.connect(self.load_data)
        filter_layout.addWidget(refresh_btn)

        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        # İstatistikler
        self.stats_label = QLabel()
        layout.addWidget(self.stats_label)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Tarih", "Modül", "Ekran", "Hata Türü", "Severity", "Çözüldü"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.show_detail)
        layout.addWidget(self.table)

        # Butonlar
        btn_layout = QHBoxLayout()

        detail_btn = QPushButton("📋 Detay")
        detail_btn.clicked.connect(self.show_detail)
        btn_layout.addWidget(detail_btn)

        resolve_btn = QPushButton("✅ Çözüme İşaretle")
        resolve_btn.clicked.connect(self.mark_resolved)
        btn_layout.addWidget(resolve_btn)

        btn_layout.addStretch()

        layout.addLayout(btn_layout)

    def _get_service(self):
        if self.service is None:
            self.service = ErrorLogService()

    def _close_service(self):
        if self.service:
            self.service.session.close()
            self.service = None

    def load_data(self):
        """Hata kayıtlarını yükle"""
        try:
            self._get_service()

            # Filtreler
            module = self.module_combo.currentData()
            severity_str = self.severity_combo.currentData()
            is_resolved = None if not self.resolved_check.isChecked() else False

            # Severity enum'a çevir
            severity = None
            if severity_str:
                severity_map = {
                    "critical": ErrorSeverity.CRITICAL,
                    "error": ErrorSeverity.ERROR,
                    "warning": ErrorSeverity.WARNING,
                    "info": ErrorSeverity.INFO,
                }
                severity = severity_map.get(severity_str)

            # Verileri çek
            errors = self.service.get_all(
                module=module, severity=severity, is_resolved=is_resolved, limit=200
            )

            # Tabloyu doldur
            self.table.setRowCount(len(errors))
            for row, error in enumerate(errors):
                # ID
                self.table.setItem(row, 0, QTableWidgetItem(str(error.id)))

                # Tarih
                date_str = error.created_at.strftime("%Y-%m-%d %H:%M:%S")
                self.table.setItem(row, 1, QTableWidgetItem(date_str))

                # Modül
                self.table.setItem(row, 2, QTableWidgetItem(error.module_name or "N/A"))

                # Ekran
                self.table.setItem(row, 3, QTableWidgetItem(error.screen_name or "N/A"))

                # Hata türü
                self.table.setItem(row, 4, QTableWidgetItem(error.error_type))

                # Severity
                severity_emoji = {
                    ErrorSeverity.CRITICAL: "🔴",
                    ErrorSeverity.ERROR: "🔴",
                    ErrorSeverity.WARNING: "🟡",
                    ErrorSeverity.INFO: "🔵",
                }
                severity_text = (
                    f"{severity_emoji.get(error.severity, '⚪')} {error.severity.value}"
                )
                self.table.setItem(row, 5, QTableWidgetItem(severity_text))

                # Çözüldü
                resolved_text = "✅ Evet" if error.is_resolved else "❌ Hayır"
                self.table.setItem(row, 6, QTableWidgetItem(resolved_text))

            # İstatistikler
            stats = self.service.get_statistics(module=module, days=7)
            stats_text = (
                f"Son 7 gün: <b>{stats['total']}</b> hata | "
                f"Çözülmemiş: <b>{stats['unresolved']}</b> | "
                f"🔴 Critical: <b>{stats['by_severity']['critical']}</b> | "
                f"🔴 Error: <b>{stats['by_severity']['error']}</b> | "
                f"🟡 Warning: <b>{stats['by_severity']['warning']}</b>"
            )
            self.stats_label.setText(stats_text)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veriler yüklenirken hata:\n{str(e)}")
            import traceback

            traceback.print_exc()
        finally:
            self._close_service()

    def show_detail(self):
        """Seçili hatanın detayını göster"""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir hata seçin!")
            return

        try:
            self._get_service()
            error_id = int(self.table.item(selected, 0).text())
            error = self.service.get_by_id(error_id)

            if error:
                dialog = ErrorDetailDialog(error, self)
                dialog.exec()
            else:
                QMessageBox.warning(self, "Uyarı", "Hata kaydı bulunamadı!")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Detay gösterilirken hata:\n{str(e)}")
        finally:
            self._close_service()

    def mark_resolved(self):
        """Seçili hatayı çözüme işaretle"""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir hata seçin!")
            return

        try:
            self._get_service()
            error_id = int(self.table.item(selected, 0).text())

            # TODO: Kullanıcı ID'sini al (şu an için 1 kullan)
            self.service.resolve(
                error_id, "Manuel olarak çözüme işaretlendi", user_id=1
            )

            QMessageBox.information(self, "Başarılı", "Hata çözüme işaretlendi!")
            self.load_data()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"İşlem sırasında hata:\n{str(e)}")
        finally:
            self._close_service()


class DevelopmentModule(QWidget):
    """
    Geliştirme Modülü Ana Wrapper
    Tab: Hata Kayıtları
    Tab: Trace İnceleme
    """

    page_title = "⚙️ Geliştirme"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Tab 1: Hata Kayıtları
        self.error_logs = ErrorLogsWidget()
        layout.addWidget(self.error_logs)
