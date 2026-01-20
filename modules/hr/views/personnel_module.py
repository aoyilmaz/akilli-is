"""
Akıllı İş - Özlük Dosyası Modülü

Personel belgeleri yönetimi UI.
"""

from datetime import date

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
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

from config.styles import ICONS
from modules.hr.services import PersonnelService
from database.models.personnel import DocumentType, DocumentStatus


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

        # Çalışan
        self.employee_combo = QComboBox()
        for emp in self.employees:
            self.employee_combo.addItem(f"{emp.first_name} {emp.last_name}", emp.id)
        layout.addRow("Çalışan:", self.employee_combo)

        # Belge türü
        self.type_combo = QComboBox()
        self.type_combo.addItem("İş Sözleşmesi", DocumentType.CONTRACT)
        self.type_combo.addItem("Kimlik", DocumentType.ID_CARD)
        self.type_combo.addItem("Diploma", DocumentType.DIPLOMA)
        self.type_combo.addItem("Sertifika", DocumentType.CERTIFICATE)
        self.type_combo.addItem("Sağlık Raporu", DocumentType.HEALTH_REPORT)
        self.type_combo.addItem("Adli Sicil", DocumentType.CRIMINAL_RECORD)
        self.type_combo.addItem("Fotoğraf", DocumentType.PHOTO)
        self.type_combo.addItem("Diğer", DocumentType.OTHER)
        layout.addRow("Belge Türü:", self.type_combo)

        # Belge adı
        self.name_edit = QLineEdit()
        layout.addRow("Belge Adı:", self.name_edit)

        # Dosya seçimi
        file_layout = QHBoxLayout()
        self.file_label = QLabel("Dosya seçilmedi")
        file_btn = QPushButton("📁 Dosya Seç")
        file_btn.clicked.connect(self._select_file)
        file_layout.addWidget(self.file_label, 1)
        file_layout.addWidget(file_btn)
        layout.addRow("Dosya:", file_layout)

        # Tarihler
        self.issue_date = QDateEdit()
        self.issue_date.setCalendarPopup(True)
        self.issue_date.setDate(QDate.currentDate())
        layout.addRow("Verilme Tarihi:", self.issue_date)

        self.expiry_date = QDateEdit()
        self.expiry_date.setCalendarPopup(True)
        self.expiry_date.setSpecialValueText("Süresiz")
        layout.addRow("Son Geçerlilik:", self.expiry_date)

        # Zorunlu mu
        self.mandatory_check = QCheckBox("Bu belge zorunludur")
        layout.addRow("", self.mandatory_check)

        # Açıklama
        self.description = QTextEdit()
        self.description.setMaximumHeight(60)
        layout.addRow("Açıklama:", self.description)

        # Butonlar
        btn_layout = QHBoxLayout()
        save_btn = QPushButton(f"{ICONS['add']} Kaydet")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

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
        expiry = self.expiry_date.date().toPyDate()
        if expiry == date(2000, 1, 1):
            expiry = None

        return {
            "employee_id": self.employee_combo.currentData(),
            "document_type": self.type_combo.currentData(),
            "name": self.name_edit.text(),
            "file_path": self.file_path,
            "issue_date": self.issue_date.date().toPyDate(),
            "expiry_date": expiry,
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

        # === Header - PageHeader kullanarak ===
        from ui.components.page_header import PageHeader

        self.header = PageHeader(
            title="Özlük Dosyası",
            icon="📂",
            show_search=False,
            show_refresh=False,
            show_add=True,
            add_text="Belge Ekle",
            parent=self,
        )
        self.header.add_clicked.connect(self._add_document)

        h_layout = self.header.header_layout()

        # Filtre - Header içine taşındı
        h_layout.addWidget(QLabel("Tür:"))
        self.type_filter = QComboBox()
        self.type_filter.addItem("Tümü", None)
        self.type_filter.addItem("İş Sözleşmesi", DocumentType.CONTRACT)
        self.type_filter.addItem("Kimlik", DocumentType.ID_CARD)
        self.type_filter.addItem("Sağlık Raporu", DocumentType.HEALTH_REPORT)
        self.type_filter.setFixedWidth(140)
        self.type_filter.setFixedHeight(36)
        self.type_filter.currentIndexChanged.connect(self._load_documents)
        h_layout.addWidget(self.type_filter)

        layout.addWidget(self.header)

        # Sekme widget
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_documents_tab(), "📄 Belgeler")
        self.tabs.addTab(self._create_expiring_tab(), "⚠️ Süresi Dolanlar")
        self.tabs.addTab(self._create_missing_tab(), "❌ Eksik Belgeler")
        layout.addWidget(self.tabs)

    def _create_documents_tab(self) -> QWidget:
        """Belgeler sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        # Toolbar kaldırıldı çünkü header'a taşındı

        # Tablo
        self.documents_table = QTableWidget()
        self.documents_table.setColumnCount(7)
        self.documents_table.setHorizontalHeaderLabels(
            [
                "Çalışan",
                "Belge Türü",
                "Belge Adı",
                "Verilme",
                "Bitiş",
                "Durum",
                "Zorunlu",
            ]
        )
        self.documents_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.documents_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        layout.addWidget(self.documents_table)

        return widget

    def _create_expiring_tab(self) -> QWidget:
        """Süresi dolanlar sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Açıklama
        info = QLabel(
            "⚠️ Önümüzdeki 30 gün içinde süresi dolacak veya "
            "dolmuş belgeler aşağıda listelenmiştir."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Tablo
        self.expiring_table = QTableWidget()
        self.expiring_table.setColumnCount(5)
        self.expiring_table.setHorizontalHeaderLabels(
            ["Çalışan", "Belge", "Bitiş Tarihi", "Kalan Gün", "Durum"]
        )
        self.expiring_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.expiring_table)

        return widget

    def _create_missing_tab(self) -> QWidget:
        """Eksik belgeler sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Açıklama
        info = QLabel(
            "❌ Aşağıda zorunlu belgesi eksik olan çalışanlar " "listelenmiştir."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Tablo
        self.missing_table = QTableWidget()
        self.missing_table.setColumnCount(3)
        self.missing_table.setHorizontalHeaderLabels(
            ["Çalışan", "Eksik Belge Türü", "İşlem"]
        )
        self.missing_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.missing_table)

        return widget

    def showEvent(self, event):
        super().showEvent(event)
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
        self._ensure_service()

        # Basit bir şekilde tüm belgeleri çek
        # Gerçek uygulamada filtre uygulanmalı
        from database.models.personnel import EmployeeDocument
        from database.base import get_session

        session = get_session()
        docs = session.query(EmployeeDocument).limit(100).all()

        self.documents_table.setRowCount(len(docs))

        type_names = {
            DocumentType.CONTRACT: "İş Sözleşmesi",
            DocumentType.ID_CARD: "Kimlik",
            DocumentType.DIPLOMA: "Diploma",
            DocumentType.CERTIFICATE: "Sertifika",
            DocumentType.HEALTH_REPORT: "Sağlık Raporu",
            DocumentType.CRIMINAL_RECORD: "Adli Sicil",
            DocumentType.PHOTO: "Fotoğraf",
            DocumentType.OTHER: "Diğer",
        }

        status_icons = {
            DocumentStatus.VALID: "✅",
            DocumentStatus.EXPIRING_SOON: "⚠️",
            DocumentStatus.EXPIRED: "❌",
            DocumentStatus.MISSING: "❓",
        }

        for i, doc in enumerate(docs):
            emp_name = ""
            if doc.employee:
                emp_name = f"{doc.employee.first_name} {doc.employee.last_name}"

            self.documents_table.setItem(i, 0, QTableWidgetItem(emp_name))
            self.documents_table.setItem(
                i, 1, QTableWidgetItem(type_names.get(doc.document_type, ""))
            )
            self.documents_table.setItem(i, 2, QTableWidgetItem(doc.name))
            self.documents_table.setItem(
                i,
                3,
                QTableWidgetItem(
                    doc.issue_date.strftime("%d.%m.%Y") if doc.issue_date else ""
                ),
            )
            self.documents_table.setItem(
                i,
                4,
                QTableWidgetItem(
                    doc.expiry_date.strftime("%d.%m.%Y")
                    if doc.expiry_date
                    else "Süresiz"
                ),
            )
            self.documents_table.setItem(
                i, 5, QTableWidgetItem(status_icons.get(doc.status, ""))
            )
            self.documents_table.setItem(
                i, 6, QTableWidgetItem("✅" if doc.is_mandatory else "")
            )

        session.close()

    def _load_expiring(self):
        self._ensure_service()
        docs = self.service.get_expiring_documents(days_ahead=30)

        self.expiring_table.setRowCount(len(docs))

        for i, doc in enumerate(docs):
            emp_name = ""
            if doc.employee:
                emp_name = f"{doc.employee.first_name} {doc.employee.last_name}"

            self.expiring_table.setItem(i, 0, QTableWidgetItem(emp_name))
            self.expiring_table.setItem(i, 1, QTableWidgetItem(doc.name))
            self.expiring_table.setItem(
                i,
                2,
                QTableWidgetItem(
                    doc.expiry_date.strftime("%d.%m.%Y") if doc.expiry_date else ""
                ),
            )

            days_left = (doc.expiry_date - date.today()).days if doc.expiry_date else 0
            self.expiring_table.setItem(i, 3, QTableWidgetItem(str(days_left)))

            status = "⚠️ Yaklaşıyor" if days_left > 0 else "❌ Dolmuş"
            self.expiring_table.setItem(i, 4, QTableWidgetItem(status))

    def _load_missing(self):
        self._ensure_service()
        missing = self.service.get_missing_mandatory_documents()

        self.missing_table.setRowCount(len(missing))

        type_names = {
            "contract": "İş Sözleşmesi",
            "id_card": "Kimlik",
            "health_report": "Sağlık Raporu",
            "criminal_record": "Adli Sicil",
        }

        for i, item in enumerate(missing):
            self.missing_table.setItem(i, 0, QTableWidgetItem(item["employee_name"]))
            self.missing_table.setItem(
                i,
                1,
                QTableWidgetItem(
                    type_names.get(item["document_type"], item["document_type"])
                ),
            )
            self.missing_table.setItem(i, 2, QTableWidgetItem("📄 Ekle"))

    def _add_document(self):
        from database.models.hr import Employee
        from database.base import get_session

        session = get_session()
        employees = (
            session.query(Employee)
            .filter(Employee.is_active == True)
            .order_by(Employee.first_name)
            .all()
        )

        if not employees:
            QMessageBox.warning(self, "Uyarı", "Sistemde kayıtlı çalışan bulunamadı.")
            return

        dialog = DocumentDialog(employees, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                self._ensure_service()
                self.service.add_document(**data)
                self._load_documents()
                QMessageBox.information(self, "Başarılı", "Belge başarıyla eklendi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))

        session.close()
