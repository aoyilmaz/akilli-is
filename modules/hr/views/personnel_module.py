"""
Akıllı İş - Özlük Dosyası Modülü
"""

from datetime import date
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidgetItem,
    QTabWidget,
    QDialog,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QDateEdit,
    QCheckBox,
    QMessageBox,
    QFileDialog,
)
from PyQt6.QtCore import Qt, QDate
import qtawesome as qta

from config.icons import ICONS
from modules.hr.services import PersonnelService
from database.models.personnel import DocumentType, DocumentStatus
from ui.components.page_header import PageHeader
from ui.components.enhanced_table import EnhancedTableWidget, ColumnConfig


class DocumentDialog(QDialog):
    """Belge ekleme dialogu"""

    def __init__(self, employees: list, parent=None):
        super().__init__(parent)
        self.employees = employees
        self.file_path = None
        self.setWindowTitle("Belge Ekle")
        self.setMinimumWidth(450)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)
        self.employee_combo = QComboBox()
        for emp in self.employees:
            self.employee_combo.addItem(f"{emp.first_name} {emp.last_name}", emp.id)
        layout.addRow("Çalışan:", self.employee_combo)

        self.type_combo = QComboBox()
        types = [
            ("İş Sözleşmesi", DocumentType.CONTRACT),
            ("Kimlik", DocumentType.ID_CARD),
            ("Diploma", DocumentType.DIPLOMA),
            ("Sertifika", DocumentType.CERTIFICATE),
            ("Sağlık Raporu", DocumentType.HEALTH_REPORT),
            ("Adli Sicil", DocumentType.CRIMINAL_RECORD),
            ("Fotoğraf", DocumentType.PHOTO),
            ("Diğer", DocumentType.OTHER),
        ]
        for lbl, val in types:
            self.type_combo.addItem(lbl, val)
        layout.addRow("Belge Türü:", self.type_combo)

        self.name_edit = QLineEdit()
        layout.addRow("Belge Adı:", self.name_edit)

        f_layout = QHBoxLayout()
        self.file_label = QLabel("Dosya seçilmedi")
        f_btn = QPushButton("Dosya Seç")
        f_btn.setIcon(qta.icon(ICONS.FOLDER, color="#ffffff"))
        f_btn.setProperty("class", "btn-secondary")
        f_btn.clicked.connect(self._select_file)
        f_layout.addWidget(self.file_label, 1)
        f_layout.addWidget(f_btn)
        layout.addRow("Dosya:", f_layout)

        self.issue_date = QDateEdit()
        self.issue_date.setCalendarPopup(True)
        self.issue_date.setDate(QDate.currentDate())
        layout.addRow("Verilme Tarihi:", self.issue_date)
        self.expiry_date = QDateEdit()
        self.expiry_date.setCalendarPopup(True)
        self.expiry_date.setSpecialValueText("Süresiz")
        layout.addRow("Son Geçerlilik:", self.expiry_date)

        self.mandatory_check = QCheckBox("Bu belge zorunludur")
        layout.addRow("", self.mandatory_check)
        self.description = QTextEdit()
        self.description.setMaximumHeight(60)
        layout.addRow("Açıklama:", self.description)

        b_layout = QHBoxLayout()
        save_btn = QPushButton("Kaydet")
        save_btn.setIcon(qta.icon(ICONS.ADD, color="#ffffff"))
        save_btn.setProperty("class", "btn-primary")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        b_layout.addStretch()
        b_layout.addWidget(save_btn)
        b_layout.addWidget(cancel_btn)
        layout.addRow(b_layout)

    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Dosya Seç",
            "",
            "Tüm Dosyalar (*);;PDF (*.pdf);;Resimler (*.jpg *.png)",
        )
        if path:
            self.file_path = path
            self.file_label.setText(path.split("/")[-1])

    def get_data(self) -> dict:
        exp = self.expiry_date.date().toPyDate()
        return {
            "employee_id": self.employee_combo.currentData(),
            "document_type": self.type_combo.currentData(),
            "name": self.name_edit.text(),
            "file_path": self.file_path,
            "issue_date": self.issue_date.date().toPyDate(),
            "expiry_date": None if exp == date(2000, 1, 1) else exp,
            "is_mandatory": self.mandatory_check.isChecked(),
            "description": self.description.toPlainText(),
        }


class PersonnelModule(QWidget):
    """Özlük Dosyası Modülü"""

    page_title = "Özlük Dosyası"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.header = PageHeader(
            title="Özlük Dosyası",
            icon=ICONS.FOLDER,
            show_search=False,
            show_refresh=False,
            show_add=True,
            add_text="Belge Ekle",
            parent=self,
        )
        self.header.add_clicked.connect(self._add_document)
        h_layout = self.header.header_layout()
        h_layout.addWidget(QLabel("Tür:"))
        self.type_filter = QComboBox()
        self.type_filter.addItem("Tümü", None)
        for lbl, val in [
            ("İş Sözleşmesi", DocumentType.CONTRACT),
            ("Kimlik", DocumentType.ID_CARD),
            ("Sağlık Raporu", DocumentType.HEALTH_REPORT),
        ]:
            self.type_filter.addItem(lbl, val)
        self.type_filter.setFixedWidth(140)
        self.type_filter.setFixedHeight(36)
        self.type_filter.currentIndexChanged.connect(self._load_documents)
        h_layout.addWidget(self.type_filter)
        layout.addWidget(self.header)

        self.tabs = QTabWidget()
        self._setup_docs_tab()
        self._setup_exp_tab()
        self._setup_miss_tab()
        layout.addWidget(self.tabs)

    def _setup_docs_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        cols = [
            ColumnConfig("emp", "Çalışan", width=180),
            ColumnConfig("type", "Belge Türü", width=140),
            ColumnConfig("name", "Belge Adı", stretch=True),
            ColumnConfig("issue", "Verilme", width=100),
            ColumnConfig("exp", "Bitiş", width=100),
            ColumnConfig("stat", "Durum", width=100),
            ColumnConfig("req", "Zorunlu", width=80),
        ]
        self.docs_table = EnhancedTableWidget(
            table_id="hr_personnel_docs", columns=cols, parent=tab
        )
        l.addWidget(self.docs_table)
        self.tabs.addTab(tab, "📄 Belgeler")

    def _setup_exp_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        l.addWidget(
            QLabel("⚠️ Önümüzdeki 30 gün içinde süresi dolacak veya dolmuş belgeler.")
        )
        cols = [
            ColumnConfig("emp", "Çalışan", width=180),
            ColumnConfig("doc", "Belge", stretch=True),
            ColumnConfig("exp", "Bitiş Tarihi", width=120),
            ColumnConfig("rem", "Kalan Gün", width=100),
            ColumnConfig("stat", "Durum", width=120),
        ]
        self.exp_table = EnhancedTableWidget(
            table_id="hr_personnel_exp", columns=cols, parent=tab
        )
        l.addWidget(self.exp_table)
        self.tabs.addTab(tab, "⚠️ Süresi Dolanlar")

    def _setup_miss_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)
        l.addWidget(QLabel("❌ Zorunlu belgesi eksik olan çalışanlar."))
        cols = [
            ColumnConfig("emp", "Çalışan", stretch=True),
            ColumnConfig("type", "Eksik Belge Türü", width=200),
            ColumnConfig("act", "İşlem", width=100),
        ]
        self.miss_table = EnhancedTableWidget(
            table_id="hr_personnel_miss", columns=cols, parent=tab
        )
        l.addWidget(self.miss_table)
        self.tabs.addTab(tab, "❌ Eksik Belgeler")

    def showEvent(self, e):
        super().showEvent(e)
        self._ensure_service()
        self._load_data()

    def _ensure_service(self):
        if not self.service:
            self.service = PersonnelService()

    def _load_data(self):
        self._load_documents()
        self._load_expiring()
        self._load_missing()

    def _load_documents(self):
        from database.models.personnel import EmployeeDocument
        from database.base import get_session

        s = get_session()
        docs = s.query(EmployeeDocument).limit(100).all()
        self.docs_table.setRowCount(len(docs))
        t_names = {
            DocumentType.CONTRACT: "İş Sözleşmesi",
            DocumentType.ID_CARD: "Kimlik",
            DocumentType.DIPLOMA: "Diploma",
            DocumentType.CERTIFICATE: "Sertifika",
            DocumentType.HEALTH_REPORT: "Sağlık Raporu",
            DocumentType.CRIMINAL_RECORD: "Adli Sicil",
            DocumentType.PHOTO: "Fotoğraf",
            DocumentType.OTHER: "Diğer",
        }
        for i, d in enumerate(docs):
            en = f"{d.employee.first_name} {d.employee.last_name}" if d.employee else ""
            self.docs_table.setItem(i, 0, QTableWidgetItem(en))
            self.docs_table.setItem(
                i, 1, QTableWidgetItem(t_names.get(d.document_type, ""))
            )
            self.docs_table.setItem(i, 2, QTableWidgetItem(d.name))
            self.docs_table.setItem(
                i,
                3,
                QTableWidgetItem(
                    d.issue_date.strftime("%d.%m.%Y") if d.issue_date else ""
                ),
            )
            self.docs_table.setItem(
                i,
                4,
                QTableWidgetItem(
                    d.expiry_date.strftime("%d.%m.%Y") if d.expiry_date else "Süresiz"
                ),
            )
            ic = {
                DocumentStatus.VALID: "✅",
                DocumentStatus.EXPIRING_SOON: "⚠️",
                DocumentStatus.EXPIRED: "❌",
                DocumentStatus.MISSING: "❓",
            }.get(d.status, "")
            self.docs_table.setItem(i, 5, QTableWidgetItem(ic))
            self.docs_table.setItem(
                i, 6, QTableWidgetItem("✅" if d.is_mandatory else "")
            )
        s.close()

    def _load_expiring(self):
        self._ensure_service()
        docs = self.service.get_expiring_documents(days_ahead=30)
        self.exp_table.setRowCount(len(docs))
        for i, d in enumerate(docs):
            en = f"{d.employee.first_name} {d.employee.last_name}" if d.employee else ""
            self.exp_table.setItem(i, 0, QTableWidgetItem(en))
            self.exp_table.setItem(i, 1, QTableWidgetItem(d.name))
            self.exp_table.setItem(
                i,
                2,
                QTableWidgetItem(
                    d.expiry_date.strftime("%d.%m.%Y") if d.expiry_date else ""
                ),
            )
            rem = (d.expiry_date - date.today()).days if d.expiry_date else 0
            self.exp_table.setItem(i, 3, QTableWidgetItem(str(rem)))
            self.exp_table.setItem(
                i, 4, QTableWidgetItem("⚠️ Yaklaşıyor" if rem > 0 else "❌ Dolmuş")
            )

    def _load_missing(self):
        self._ensure_service()
        missing = self.service.get_missing_mandatory_documents()
        self.miss_table.setRowCount(len(missing))
        t_names = {
            "contract": "İş Sözleşmesi",
            "id_card": "Kimlik",
            "health_report": "Sağlık Raporu",
            "criminal_record": "Adli Sicil",
        }
        for i, it in enumerate(missing):
            self.miss_table.setItem(i, 0, QTableWidgetItem(it["employee_name"]))
            self.miss_table.setItem(
                i,
                1,
                QTableWidgetItem(t_names.get(it["document_type"], it["document_type"])),
            )
            self.miss_table.setItem(i, 2, QTableWidgetItem("📄 Ekle"))

    def _add_document(self):
        from database.models.hr import Employee
        from database.base import get_session

        s = get_session()
        employees = (
            s.query(Employee)
            .filter(Employee.is_active == True)
            .order_by(Employee.first_name)
            .all()
        )
        if not employees:
            QMessageBox.warning(self, "Uyarı", "Sistemde kayıtlı çalışan bulunamadı.")
            return
        dialog = DocumentDialog(employees, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                self._ensure_service()
                self.service.add_document(**dialog.get_data())
                self._load_documents()
                QMessageBox.information(self, "Başarılı", "Belge başarıyla eklendi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))
        s.close()
