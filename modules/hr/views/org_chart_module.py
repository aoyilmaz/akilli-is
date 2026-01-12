"""
Akıllı İş - Organizasyon Şeması Modülü
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QHeaderView,
    QComboBox,
    QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

from config.themes import get_theme, ThemeManager
from modules.hr.services import HRService


class OrgChartModule(QWidget):
    """Organizasyon Şeması Sayfası"""

    page_title = "Organizasyon Şeması"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = HRService()
        self.setup_ui()
        self._apply_theme()
        ThemeManager.register_callback(self._on_theme_changed)

    def _on_theme_changed(self, theme):
        self._apply_theme()

    def _apply_theme(self):
        t = get_theme()
        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: {t.bg_primary};
                color: {t.text_primary};
            }}
            QTreeWidget {{
                background-color: {t.bg_secondary};
                border: 1px solid {t.border};
                border-radius: 8px;
                color: {t.text_primary};
            }}
            QTreeWidget::item {{
                padding: 6px;
            }}
            QTreeWidget::item:hover {{
                background-color: {t.bg_hover};
            }}
            QTreeWidget::item:selected {{
                background-color: {t.accent_primary}20;
            }}
            QPushButton {{
                background-color: {t.bg_secondary};
                border: 1px solid {t.border};
                border-radius: 6px;
                padding: 8px 16px;
                color: {t.text_primary};
            }}
            QPushButton:hover {{
                background-color: {t.bg_hover};
            }}
            QComboBox {{
                background-color: {t.bg_secondary};
                border: 1px solid {t.border};
                border-radius: 6px;
                padding: 6px 12px;
                color: {t.text_primary};
            }}
            QLabel {{
                background: transparent;
            }}
        """
        )

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Başlık
        header = QHBoxLayout()
        title = QLabel("🏢 Organizasyon Şeması")
        title.setFont(QFont("", 16, QFont.Weight.Bold))
        header.addWidget(title)
        header.addStretch()

        # Görünüm seçimi
        self.view_combo = QComboBox()
        self.view_combo.addItem("Departmana Göre", "department")
        self.view_combo.addItem("Yöneticiye Göre", "manager")
        self.view_combo.currentIndexChanged.connect(self._load_data)
        header.addWidget(self.view_combo)

        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.clicked.connect(self._load_data)
        header.addWidget(refresh_btn)

        layout.addLayout(header)

        # Ağaç görünümü
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Ad", "Pozisyon", "Email", "Telefon"])
        self.tree.setAlternatingRowColors(True)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.setColumnWidth(1, 150)
        self.tree.setColumnWidth(2, 200)
        self.tree.setColumnWidth(3, 120)
        layout.addWidget(self.tree)

        # Özet
        self.summary_label = QLabel()
        layout.addWidget(self.summary_label)

    def showEvent(self, event):
        super().showEvent(event)
        self._load_data()

    def _load_data(self):
        """Organizasyon verilerini yükle"""
        view_type = self.view_combo.currentData()

        if view_type == "department":
            self._load_by_department()
        else:
            self._load_by_manager()

    def _load_by_department(self):
        """Departmana göre görünüm"""
        self.tree.clear()

        try:
            departments = self.service.get_all_departments()
            employees = self.service.get_all_employees(limit=1000)

            total = 0
            for dept in departments:
                dept_employees = [e for e in employees if e.department_id == dept.id]
                if not dept_employees:
                    continue

                dept_item = QTreeWidgetItem(
                    [f"📁 {dept.name}", "", f"{len(dept_employees)} kişi", ""]
                )
                dept_item.setFont(0, QFont("", 10, QFont.Weight.Bold))
                dept_item.setForeground(0, QColor("#818cf8"))

                # Pozisyonlara göre grupla
                positions = {}
                for emp in dept_employees:
                    pos_name = emp.position.name if emp.position else "Belirsiz"
                    if pos_name not in positions:
                        positions[pos_name] = []
                    positions[pos_name].append(emp)
                    total += 1

                for pos_name, pos_employees in positions.items():
                    pos_item = QTreeWidgetItem(
                        [f"  📋 {pos_name}", "", f"{len(pos_employees)} kişi", ""]
                    )
                    pos_item.setForeground(0, QColor("#a78bfa"))

                    for emp in pos_employees:
                        gender_icon = "👨" if str(emp.gender) == "Gender.MALE" else "👩"
                        emp_item = QTreeWidgetItem(
                            [
                                f"      {gender_icon} {emp.full_name}",
                                "",
                                emp.email or "-",
                                emp.phone or emp.mobile or "-",
                            ]
                        )
                        pos_item.addChild(emp_item)

                    dept_item.addChild(pos_item)

                self.tree.addTopLevelItem(dept_item)
                dept_item.setExpanded(True)

            self.summary_label.setText(f"Toplam: {total} çalışan")

        except Exception as e:
            print(f"Organizasyon yükleme hatası: {e}")

    def _load_by_manager(self):
        """Yöneticiye göre görünüm"""
        self.tree.clear()

        try:
            employees = self.service.get_all_employees(limit=1000)

            # Yöneticisi olmayanları bul (üst düzey)
            top_level = [e for e in employees if not e.manager_id]

            def add_subordinates(parent_item, manager_id):
                subordinates = [e for e in employees if e.manager_id == manager_id]
                for emp in subordinates:
                    gender_icon = "👨" if str(emp.gender) == "Gender.MALE" else "👩"
                    pos_name = emp.position.name if emp.position else ""
                    emp_item = QTreeWidgetItem(
                        [
                            f"{gender_icon} {emp.full_name}",
                            pos_name,
                            emp.email or "-",
                            emp.phone or emp.mobile or "-",
                        ]
                    )
                    parent_item.addChild(emp_item)
                    add_subordinates(emp_item, emp.id)

            for emp in top_level:
                gender_icon = "👨" if str(emp.gender) == "Gender.MALE" else "👩"
                pos_name = emp.position.name if emp.position else ""
                dept_name = emp.department.name if emp.department else ""
                emp_item = QTreeWidgetItem(
                    [
                        f"👑 {gender_icon} {emp.full_name}",
                        f"{pos_name} - {dept_name}",
                        emp.email or "-",
                        emp.phone or emp.mobile or "-",
                    ]
                )
                emp_item.setFont(0, QFont("", 10, QFont.Weight.Bold))
                emp_item.setForeground(0, QColor("#f59e0b"))
                self.tree.addTopLevelItem(emp_item)
                add_subordinates(emp_item, emp.id)
                emp_item.setExpanded(True)

            self.summary_label.setText(f"Toplam: {len(employees)} çalışan")

        except Exception as e:
            print(f"Organizasyon yükleme hatası: {e}")

    def closeEvent(self, event):
        self.service.close()
        super().closeEvent(event)
