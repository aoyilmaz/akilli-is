"""
Akıllı İş - Vardiya Ekipleri Genel Bakış Modülü
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTabWidget,
    QTableWidgetItem,
)
from PyQt6.QtGui import QColor, QFont
import qtawesome as qta

from config.icons import ICONS
from modules.hr.services import HRService
from ui.components.page_header import PageHeader
from ui.components.stat_cards import MiniStatCard
from ui.components.enhanced_table import EnhancedTableWidget, ColumnConfig


class TeamTab(QWidget):
    """Tek bir ekip sekmesi"""

    def __init__(self, team, employees, parent=None):
        super().__init__(parent)
        self.team, self.employees = team, employees
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        c_layout = QHBoxLayout()
        c_layout.setSpacing(12)
        tot = len(self.employees)
        mal = sum(1 for e in self.employees if str(e.gender) == "Gender.MALE")
        fem = tot - mal
        c_layout.addWidget(MiniStatCard("Toplam", str(tot), "info", icon=ICONS.USER))
        c_layout.addWidget(MiniStatCard("Erkek", str(mal), "info", icon=ICONS.USER))
        c_layout.addWidget(MiniStatCard("Kadın", str(fem), "warning", icon=ICONS.USER))
        c_layout.addStretch()
        layout.addLayout(c_layout)

        poss = {}
        for e in self.employees:
            pn = e.position.name if e.position else "Belirsiz"
            if pn not in poss:
                poss[pn] = []
            poss[pn].append(e)

        p_layout = QHBoxLayout()
        p_layout.setSpacing(12)
        cols = ["info", "success", "warning", "error"]
        for i, (pn, pes) in enumerate(
            sorted(poss.items(), key=lambda x: len(x[1]), reverse=True)[:4]
        ):
            p_layout.addWidget(
                MiniStatCard(pn, str(len(pes)), cols[i % 4], icon=ICONS.LIST)
            )
        p_layout.addStretch()
        layout.addLayout(p_layout)

        l = QLabel("Ekip Üyeleri")
        l.setFont(QFont("", 12, QFont.Weight.Bold))
        layout.addWidget(l)
        tab_cols = [
            ColumnConfig("name", "Ad Soyad", stretch=True),
            ColumnConfig("pos", "Pozisyon", width=150),
            ColumnConfig("dept", "Departman", width=150),
            ColumnConfig("gen", "Cinsiyet", width=100),
            ColumnConfig("tel", "Telefon", width=120),
        ]
        self.table = EnhancedTableWidget(
            table_id=f"hr_team_{self.team.id if self.team else 'un'}",
            columns=tab_cols,
            parent=self,
        )
        self._load_table()
        layout.addWidget(self.table)

    def _load_table(self):
        self.table.setRowCount(len(self.employees))
        vcols = self.table.get_visible_columns()
        for i, e in enumerate(
            sorted(
                self.employees,
                key=lambda x: (x.position.name if x.position else "ZZZ", x.full_name),
            )
        ):
            for c, key in enumerate(vcols):
                if key == "name":
                    it = QTableWidgetItem(e.full_name)
                    it.setForeground(QColor("#818cf8"))
                    self.table.setItem(i, c, it)
                elif key == "pos":
                    self.table.setItem(
                        i, c, QTableWidgetItem(e.position.name if e.position else "-")
                    )
                elif key == "dept":
                    self.table.setItem(
                        i,
                        c,
                        QTableWidgetItem(e.department.name if e.department else "-"),
                    )
                elif key == "gen":
                    self.table.setItem(
                        i,
                        c,
                        QTableWidgetItem(
                            "Erkek" if str(e.gender) == "Gender.MALE" else "Kadın"
                        ),
                    )
                elif key == "tel":
                    self.table.setItem(
                        i, c, QTableWidgetItem(e.phone or e.mobile or "-")
                    )


class ShiftTeamOverview(QWidget):
    """Vardiya Ekipleri Genel Bakış Sayfası"""

    page_title = "Vardiya Ekipleri"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service, self.team_service = HRService(), None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        self.header = PageHeader(
            title="Vardiya Ekipleri",
            icon=ICONS.USER,
            show_search=False,
            show_refresh=True,
            show_add=False,
            parent=self,
        )
        self.header.refresh_clicked.connect(self._load_data)
        layout.addWidget(self.header)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self.summary_label = QLabel()
        h_layout = self.header.header_layout()
        h_layout.addStretch()
        h_layout.addWidget(self.summary_label)

    def showEvent(self, event):
        super().showEvent(event)
        self._ensure_services()
        self._load_data()

    def _ensure_services(self):
        if not self.team_service:
            try:
                from modules.production.calendar_services import ShiftTeamService

                self.team_service = ShiftTeamService()
            except:
                pass

    def _load_data(self):
        self.tabs.clear()
        if not self.team_service:
            return
        try:
            teams, emps = self.team_service.get_all(), self.service.get_all_employees(
                limit=1000
            )
            total_a = 0
            for t in teams:
                tes = [e for e in emps if e.shift_team_id == t.id]
                total_a += len(tes)
                self.tabs.addTab(TeamTab(t, tes), f"{t.code} Ekibi ({len(tes)})")
            un = [e for e in emps if not e.shift_team_id]
            if un:
                self.tabs.addTab(TeamTab(None, un), f"Atanmamış ({len(un)})")
            self.summary_label.setText(
                f"Toplam: {len(emps)} çalışan, {total_a} ekip atanmış, {len(un)} atanmamış"
            )
        except Exception as e:
            print(f"Vardiya ekibi yükleme hatası: {e}")

    def closeEvent(self, event):
        self.service.close()
        super().closeEvent(event)
