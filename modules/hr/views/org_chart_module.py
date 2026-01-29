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
import qtawesome as qta

from config.icons import ICONS
from modules.hr.services import HRService
from ui.components.page_header import PageHeader


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
        self.header = PageHeader(
            title="Organizasyon Şeması",
            icon=ICONS.BUILDING,
            show_search=False,
            show_refresh=True,
            show_add=False,
            parent=self,
        )
        self.header.refresh_clicked.connect(self._load_data)
        h_layout = self.header.header_layout()
        self.view_combo = QComboBox()
        self.view_combo.addItem("Departmana Göre", "department")
        self.view_combo.addItem("Yöneticiye Göre", "manager")
        self.view_combo.setFixedHeight(36)
        self.view_combo.currentIndexChanged.connect(self._load_data)
        h_layout.addWidget(self.view_combo)
        layout.addWidget(self.header)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Ad", "Pozisyon", "Email", "Telefon"])
        self.tree.setAlternatingRowColors(True)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.setColumnWidth(1, 150)
        self.tree.setColumnWidth(2, 200)
        self.tree.setColumnWidth(3, 120)
        layout.addWidget(self.tree)
        self.summary_label = QLabel()
        layout.addWidget(self.summary_label)

    def showEvent(self, event):
        super().showEvent(event)
        self._load_data()

    def _load_data(self):
        v = self.view_combo.currentData()
        if v == "department":
            self._load_by_department()
        else:
            self._load_by_manager()

    def _load_by_department(self):
        self.tree.clear()
        try:
            depts = self.service.get_all_departments()
            emps = self.service.get_all_employees(limit=1000)
            total = 0
            for d in depts:
                ds = [e for e in emps if e.department_id == d.id]
                if not ds:
                    continue
                di = QTreeWidgetItem([d.name, "", f"{len(ds)} kişi", ""])
                di.setIcon(0, qta.icon(ICONS.FOLDER, color="#818cf8"))
                di.setFont(0, QFont("", 10, QFont.Weight.Bold))
                di.setForeground(0, QColor("#818cf8"))
                poss = {}
                for e in ds:
                    pn = e.position.name if e.position else "Belirsiz"
                    if pn not in poss:
                        poss[pn] = []
                    poss[pn].append(e)
                    total += 1
                for pn, pes in poss.items():
                    pi = QTreeWidgetItem([pn, "", f"{len(pes)} kişi", ""])
                    pi.setIcon(0, qta.icon(ICONS.LIST, color="#a78bfa"))
                    pi.setForeground(0, QColor("#a78bfa"))
                    for e in pes:
                        gi = ICONS.USER
                        ei = QTreeWidgetItem(
                            [
                                e.full_name,
                                "",
                                e.email or "-",
                                e.phone or e.mobile or "-",
                            ]
                        )
                        ei.setIcon(0, qta.icon(gi, color="#9ca3af"))
                        pi.addChild(ei)
                    di.addChild(pi)
                self.tree.addTopLevelItem(di)
                di.setExpanded(True)
            self.summary_label.setText(f"Toplam: {total} çalışan")
        except Exception as e:
            print(f"Org chart error: {e}")

    def _load_by_manager(self):
        self.tree.clear()
        try:
            emps = self.service.get_all_employees(limit=1000)
            tops = [e for e in emps if not e.manager_id]

            def add_subs(pi, mid):
                subs = [e for e in emps if e.manager_id == mid]
                for e in subs:
                    gi = ICONS.USER
                    pn = e.position.name if e.position else ""
                    ei = QTreeWidgetItem(
                        [e.full_name, pn, e.email or "-", e.phone or e.mobile or "-"]
                    )
                    ei.setIcon(0, qta.icon(gi, color="#9ca3af"))
                    pi.addChild(ei)
                    add_subs(ei, e.id)

            for e in tops:
                gi = ICONS.USER
                pn, dn = e.position.name if e.position else "", (
                    e.department.name if e.department else ""
                )
                ei = QTreeWidgetItem(
                    [
                        e.full_name,
                        f"{pn} - {dn}",
                        e.email or "-",
                        e.phone or e.mobile or "-",
                    ]
                )
                ei.setIcon(0, qta.icon(ICONS.CHART, color="#f59e0b"))
                ei.setFont(0, QFont("", 10, QFont.Weight.Bold))
                ei.setForeground(0, QColor("#f59e0b"))
                self.tree.addTopLevelItem(ei)
                add_subs(ei, e.id)
                ei.setExpanded(True)
            self.summary_label.setText(f"Toplam: {len(emps)} çalışan")
        except Exception as e:
            print(f"Org chart error: {e}")

    def closeEvent(self, event):
        self.service.close()
        super().closeEvent(event)
