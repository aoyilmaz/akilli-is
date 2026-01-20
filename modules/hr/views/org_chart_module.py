"""
Akıllı İş - Organizasyon Şeması Modülü
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QHeaderView,
    QComboBox,
)
from PyQt6.QtGui import QColor, QFont

from modules.hr.services import HRService


class OrgChartModule(QWidget):
    """Organizasyon Şeması Sayfası"""

    page_title = "Organizasyon Şeması"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = HRService()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # === Header - PageHeader kullanarak ===
        from ui.components.page_header import PageHeader

        self.header = PageHeader(
            title="Organizasyon Şeması",
            icon="🏢",
            show_search=False,
            show_refresh=True,
            show_add=False,
            parent=self,
        )
        self.header.refresh_clicked.connect(self._load_data)

        # Header Layout - View Combo
        h_layout = self.header.header_layout()

        self.view_combo = QComboBox()
        self.view_combo.addItem("Departmana Göre", "department")
        self.view_combo.addItem("Yöneticiye Göre", "manager")
        self.view_combo.setFixedHeight(36)
        self.view_combo.currentIndexChanged.connect(self._load_data)
        h_layout.addWidget(self.view_combo)

        layout.addWidget(self.header)

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
