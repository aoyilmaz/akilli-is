"""
Akıllı İş ERP - Audit Log Görüntüleme Ekranı

İşlem geçmişini görüntüleme, filtreleme ve export özellikleri.
"""

from datetime import datetime, timedelta
from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
    QDialog,
    QLabel,
    QLineEdit,
    QComboBox,
    QFormLayout,
    QMessageBox,
    QDateEdit,
    QTextEdit,
    QGroupBox,
    QSplitter,
    QAbstractItemView,
    QFileDialog,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
import qtawesome as qta

from database.base import get_session
from database.models.user import AuditLog, User
from config.themes import get_theme


# İşlem türleri ve renkleri
ACTION_COLORS = {
    "CREATE": "#27ae60",  # Yeşil
    "UPDATE": "#3498db",  # Mavi
    "DELETE": "#e74c3c",  # Kırmızı
    "LOGIN": "#9b59b6",   # Mor
    "LOGOUT": "#95a5a6",  # Gri
    "EXPORT": "#f39c12",  # Turuncu
    "IMPORT": "#1abc9c",  # Turkuaz
}

# Modül isimleri (Türkçe)
MODULE_NAMES = {
    "auth": "Yetkilendirme",
    "inventory": "Stok",
    "sales": "Satış",
    "purchase": "Satın Alma",
    "finance": "Finans",
    "accounting": "Muhasebe",
    "production": "Üretim",
    "hr": "İnsan Kaynakları",
    "crm": "CRM",
    "maintenance": "Bakım",
    "system": "Sistem",
    "common": "Ortak",
    "other": "Diğer",
}


class AuditLogDetailDialog(QDialog):
    """Audit log detay dialogu"""

    def __init__(self, log: AuditLog, parent=None):
        super().__init__(parent)
        self.log = log
        self.setWindowTitle(f"İşlem Detayı - #{log.id}")
        self.setMinimumSize(600, 500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Temel bilgiler
        info_group = QGroupBox("İşlem Bilgileri")
        info_layout = QFormLayout(info_group)

        info_layout.addRow("ID:", QLabel(str(self.log.id)))
        info_layout.addRow("Tarih:", QLabel(self.log.created_at.strftime("%d.%m.%Y %H:%M:%S")))
        info_layout.addRow("Kullanıcı:", QLabel(self.log.username or "-"))
        info_layout.addRow("IP Adresi:", QLabel(self.log.ip_address or "-"))

        action_label = QLabel(self.log.action)
        action_label.setStyleSheet(f"color: {ACTION_COLORS.get(self.log.action, '#333')}; font-weight: bold;")
        info_layout.addRow("İşlem:", action_label)

        info_layout.addRow("Modül:", QLabel(MODULE_NAMES.get(self.log.module, self.log.module)))
        info_layout.addRow("Tablo:", QLabel(self.log.table_name or "-"))
        info_layout.addRow("Kayıt ID:", QLabel(str(self.log.record_id) if self.log.record_id else "-"))
        info_layout.addRow("Açıklama:", QLabel(self.log.description or "-"))

        layout.addWidget(info_group)

        # Değerler
        if self.log.old_values or self.log.new_values:
            values_splitter = QSplitter(Qt.Orientation.Horizontal)

            # Eski değerler
            if self.log.old_values:
                old_group = QGroupBox("Eski Değerler")
                old_layout = QVBoxLayout(old_group)
                old_text = QTextEdit()
                old_text.setReadOnly(True)
                old_text.setPlainText(self._format_values(self.log.old_values))
                old_layout.addWidget(old_text)
                values_splitter.addWidget(old_group)

            # Yeni değerler
            if self.log.new_values:
                new_group = QGroupBox("Yeni Değerler")
                new_layout = QVBoxLayout(new_group)
                new_text = QTextEdit()
                new_text.setReadOnly(True)
                new_text.setPlainText(self._format_values(self.log.new_values))
                new_layout.addWidget(new_text)
                values_splitter.addWidget(new_group)

            layout.addWidget(values_splitter, 1)

        # Kapat butonu
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_close = QPushButton("Kapat")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

    def _format_values(self, values: dict) -> str:
        """Değerleri okunabilir formata çevirir"""
        if not values:
            return ""
        lines = []
        for key, value in values.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)


class AuditLogViewer(QWidget):
    """Audit Log Görüntüleme Widget'ı"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logs: List[AuditLog] = []
        self.current_page = 0
        self.page_size = 50
        self.total_count = 0

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Başlık
        header = QHBoxLayout()
        title = QLabel("İşlem Geçmişi (Audit Log)")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()

        # Yenile butonu
        btn_refresh = QPushButton()
        btn_refresh.setIcon(qta.icon("fa5s.sync-alt"))
        btn_refresh.setToolTip("Yenile")
        btn_refresh.clicked.connect(self.load_data)
        header.addWidget(btn_refresh)

        # Export butonu
        btn_export = QPushButton()
        btn_export.setIcon(qta.icon("fa5s.file-export"))
        btn_export.setToolTip("CSV Olarak Dışa Aktar")
        btn_export.clicked.connect(self.export_csv)
        header.addWidget(btn_export)

        layout.addLayout(header)

        # Filtreler
        filter_group = QGroupBox("Filtreler")
        filter_layout = QHBoxLayout(filter_group)

        # Tarih aralığı
        filter_layout.addWidget(QLabel("Başlangıç:"))
        self.date_start = QDateEdit()
        self.date_start.setCalendarPopup(True)
        self.date_start.setDate(QDate.currentDate().addDays(-7))
        filter_layout.addWidget(self.date_start)

        filter_layout.addWidget(QLabel("Bitiş:"))
        self.date_end = QDateEdit()
        self.date_end.setCalendarPopup(True)
        self.date_end.setDate(QDate.currentDate())
        filter_layout.addWidget(self.date_end)

        # Kullanıcı filtresi
        filter_layout.addWidget(QLabel("Kullanıcı:"))
        self.cmb_user = QComboBox()
        self.cmb_user.setMinimumWidth(150)
        self.cmb_user.addItem("Tümü", None)
        self._load_users()
        filter_layout.addWidget(self.cmb_user)

        # Modül filtresi
        filter_layout.addWidget(QLabel("Modül:"))
        self.cmb_module = QComboBox()
        self.cmb_module.setMinimumWidth(120)
        self.cmb_module.addItem("Tümü", None)
        for code, name in MODULE_NAMES.items():
            self.cmb_module.addItem(name, code)
        filter_layout.addWidget(self.cmb_module)

        # İşlem türü filtresi
        filter_layout.addWidget(QLabel("İşlem:"))
        self.cmb_action = QComboBox()
        self.cmb_action.setMinimumWidth(100)
        self.cmb_action.addItem("Tümü", None)
        for action in ["CREATE", "UPDATE", "DELETE", "LOGIN", "LOGOUT", "EXPORT", "IMPORT"]:
            self.cmb_action.addItem(action, action)
        filter_layout.addWidget(self.cmb_action)

        # Arama
        filter_layout.addWidget(QLabel("Arama:"))
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Tablo adı veya açıklama...")
        self.txt_search.setMinimumWidth(150)
        filter_layout.addWidget(self.txt_search)

        # Filtrele butonu
        btn_filter = QPushButton("Filtrele")
        btn_filter.setIcon(qta.icon("fa5s.filter"))
        btn_filter.clicked.connect(self.load_data)
        filter_layout.addWidget(btn_filter)

        # Temizle butonu
        btn_clear = QPushButton("Temizle")
        btn_clear.clicked.connect(self.clear_filters)
        filter_layout.addWidget(btn_clear)

        filter_layout.addStretch()
        layout.addWidget(filter_group)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Tarih", "Kullanıcı", "İşlem", "Modül", "Tablo", "Kayıt ID", "Açıklama"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.show_detail)

        # Sütun genişlikleri
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)

        self.table.setColumnWidth(0, 60)   # ID
        self.table.setColumnWidth(1, 140)  # Tarih
        self.table.setColumnWidth(2, 120)  # Kullanıcı
        self.table.setColumnWidth(3, 80)   # İşlem
        self.table.setColumnWidth(4, 100)  # Modül
        self.table.setColumnWidth(5, 120)  # Tablo
        self.table.setColumnWidth(6, 80)   # Kayıt ID

        layout.addWidget(self.table, 1)

        # Sayfalama
        pagination = QHBoxLayout()

        self.lbl_info = QLabel()
        pagination.addWidget(self.lbl_info)

        pagination.addStretch()

        self.btn_prev = QPushButton("Önceki")
        self.btn_prev.setIcon(qta.icon("fa5s.chevron-left"))
        self.btn_prev.clicked.connect(self.prev_page)
        pagination.addWidget(self.btn_prev)

        self.lbl_page = QLabel("Sayfa 1")
        pagination.addWidget(self.lbl_page)

        self.btn_next = QPushButton("Sonraki")
        self.btn_next.setIcon(qta.icon("fa5s.chevron-right"))
        self.btn_next.clicked.connect(self.next_page)
        pagination.addWidget(self.btn_next)

        layout.addLayout(pagination)

    def _load_users(self):
        """Kullanıcı listesini yükler"""
        session = get_session()
        try:
            users = session.query(User).filter(User.is_active == True).order_by(User.username).all()
            for user in users:
                self.cmb_user.addItem(f"{user.username} ({user.full_name})", user.id)
        finally:
            session.close()

    def load_data(self):
        """Verileri yükler"""
        session = get_session()
        try:
            query = session.query(AuditLog)

            # Tarih filtresi
            start_date = self.date_start.date().toPyDate()
            end_date = self.date_end.date().toPyDate()
            # Bitiş tarihinin sonuna kadar dahil et
            end_datetime = datetime.combine(end_date, datetime.max.time())

            query = query.filter(AuditLog.created_at >= start_date)
            query = query.filter(AuditLog.created_at <= end_datetime)

            # Kullanıcı filtresi
            user_id = self.cmb_user.currentData()
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)

            # Modül filtresi
            module = self.cmb_module.currentData()
            if module:
                query = query.filter(AuditLog.module == module)

            # İşlem filtresi
            action = self.cmb_action.currentData()
            if action:
                query = query.filter(AuditLog.action == action)

            # Arama filtresi
            search = self.txt_search.text().strip()
            if search:
                search_filter = f"%{search}%"
                query = query.filter(
                    (AuditLog.table_name.ilike(search_filter)) |
                    (AuditLog.description.ilike(search_filter))
                )

            # Toplam sayı
            self.total_count = query.count()

            # Sayfalama
            offset = self.current_page * self.page_size
            self.logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(self.page_size).all()

            self._populate_table()
            self._update_pagination()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veriler yüklenirken hata: {e}")
        finally:
            session.close()

    def _populate_table(self):
        """Tabloyu doldurur"""
        self.table.setRowCount(len(self.logs))

        for row, log in enumerate(self.logs):
            # ID
            self.table.setItem(row, 0, QTableWidgetItem(str(log.id)))

            # Tarih
            date_str = log.created_at.strftime("%d.%m.%Y %H:%M")
            self.table.setItem(row, 1, QTableWidgetItem(date_str))

            # Kullanıcı
            self.table.setItem(row, 2, QTableWidgetItem(log.username or "-"))

            # İşlem (renkli)
            action_item = QTableWidgetItem(log.action)
            action_color = ACTION_COLORS.get(log.action, "#333333")
            action_item.setForeground(QColor(action_color))
            self.table.setItem(row, 3, action_item)

            # Modül
            module_name = MODULE_NAMES.get(log.module, log.module)
            self.table.setItem(row, 4, QTableWidgetItem(module_name))

            # Tablo
            self.table.setItem(row, 5, QTableWidgetItem(log.table_name or "-"))

            # Kayıt ID
            record_id = str(log.record_id) if log.record_id else "-"
            self.table.setItem(row, 6, QTableWidgetItem(record_id))

            # Açıklama
            desc = log.description or ""
            if len(desc) > 50:
                desc = desc[:50] + "..."
            self.table.setItem(row, 7, QTableWidgetItem(desc))

    def _update_pagination(self):
        """Sayfalama bilgilerini günceller"""
        total_pages = max(1, (self.total_count + self.page_size - 1) // self.page_size)

        self.lbl_page.setText(f"Sayfa {self.current_page + 1} / {total_pages}")
        self.lbl_info.setText(f"Toplam {self.total_count} kayıt")

        self.btn_prev.setEnabled(self.current_page > 0)
        self.btn_next.setEnabled(self.current_page < total_pages - 1)

    def prev_page(self):
        """Önceki sayfa"""
        if self.current_page > 0:
            self.current_page -= 1
            self.load_data()

    def next_page(self):
        """Sonraki sayfa"""
        total_pages = (self.total_count + self.page_size - 1) // self.page_size
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.load_data()

    def clear_filters(self):
        """Filtreleri temizler"""
        self.date_start.setDate(QDate.currentDate().addDays(-7))
        self.date_end.setDate(QDate.currentDate())
        self.cmb_user.setCurrentIndex(0)
        self.cmb_module.setCurrentIndex(0)
        self.cmb_action.setCurrentIndex(0)
        self.txt_search.clear()
        self.current_page = 0
        self.load_data()

    def show_detail(self):
        """Seçili kaydın detayını gösterir"""
        row = self.table.currentRow()
        if row < 0 or row >= len(self.logs):
            return

        log = self.logs[row]
        dialog = AuditLogDetailDialog(log, self)
        dialog.exec()

    def export_csv(self):
        """CSV olarak dışa aktarır"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "CSV Kaydet", "", "CSV Dosyası (*.csv)"
        )

        if not file_path:
            return

        try:
            session = get_session()

            # Filtreleri uygula (sayfalama olmadan)
            query = session.query(AuditLog)

            start_date = self.date_start.date().toPyDate()
            end_date = self.date_end.date().toPyDate()
            end_datetime = datetime.combine(end_date, datetime.max.time())

            query = query.filter(AuditLog.created_at >= start_date)
            query = query.filter(AuditLog.created_at <= end_datetime)

            user_id = self.cmb_user.currentData()
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)

            module = self.cmb_module.currentData()
            if module:
                query = query.filter(AuditLog.module == module)

            action = self.cmb_action.currentData()
            if action:
                query = query.filter(AuditLog.action == action)

            search = self.txt_search.text().strip()
            if search:
                search_filter = f"%{search}%"
                query = query.filter(
                    (AuditLog.table_name.ilike(search_filter)) |
                    (AuditLog.description.ilike(search_filter))
                )

            logs = query.order_by(AuditLog.created_at.desc()).limit(10000).all()

            # CSV yaz
            with open(file_path, "w", encoding="utf-8-sig") as f:
                # Header
                f.write("ID;Tarih;Kullanıcı;IP Adresi;İşlem;Modül;Tablo;Kayıt ID;Açıklama\n")

                for log in logs:
                    date_str = log.created_at.strftime("%d.%m.%Y %H:%M:%S")
                    module_name = MODULE_NAMES.get(log.module, log.module)
                    desc = (log.description or "").replace(";", ",").replace("\n", " ")

                    f.write(f"{log.id};{date_str};{log.username or ''};{log.ip_address or ''};"
                           f"{log.action};{module_name};{log.table_name or ''};{log.record_id or ''};"
                           f"{desc}\n")

            session.close()

            QMessageBox.information(
                self, "Başarılı",
                f"{len(logs)} kayıt dışa aktarıldı:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Dışa aktarma hatası: {e}")
