"""
Akıllı İş - Vardiya Ekipleri Genel Bakış Modülü
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QFrame,
    QGridLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

from config.themes import get_theme, ThemeManager
from modules.hr.services import HRService


class StatCard(QFrame):
    """İstatistik kartı widget'ı"""

    def __init__(self, title: str, value: str, color: str = "#6366f1"):
        super().__init__()
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {color}20;
                border: 1px solid {color}40;
                border-radius: 8px;
                padding: 12px;
            }}
        """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {color}; font-size: 11px;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet(
            f"color: {color}; font-size: 24px; font-weight: bold;"
        )
        layout.addWidget(value_label)


class TeamTab(QWidget):
    """Tek bir ekip sekmesi"""

    def __init__(self, team, employees, parent=None):
        super().__init__(parent)
        self.team = team
        self.employees = employees
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Özet kartları
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        total = len(self.employees)
        male_count = sum(1 for e in self.employees if str(e.gender) == "Gender.MALE")
        female_count = sum(
            1 for e in self.employees if str(e.gender) == "Gender.FEMALE"
        )

        cards_layout.addWidget(StatCard("Toplam", str(total), "#6366f1"))
        cards_layout.addWidget(StatCard("👨 Erkek", str(male_count), "#3b82f6"))
        cards_layout.addWidget(StatCard("👩 Kadın", str(female_count), "#ec4899"))
        cards_layout.addStretch()

        layout.addLayout(cards_layout)

        # Pozisyon dağılımı
        positions = {}
        for emp in self.employees:
            pos_name = emp.position.name if emp.position else "Belirsiz"
            if pos_name not in positions:
                positions[pos_name] = []
            positions[pos_name].append(emp)

        # Pozisyon kartları
        pos_layout = QHBoxLayout()
        pos_layout.setSpacing(12)

        # Renk paleti
        colors = ["#f59e0b", "#10b981", "#8b5cf6", "#ef4444", "#06b6d4", "#84cc16"]

        for idx, (pos_name, pos_emps) in enumerate(
            sorted(positions.items(), key=lambda x: len(x[1]), reverse=True)
        ):
            color = colors[idx % len(colors)]
            card = StatCard(pos_name, str(len(pos_emps)), color)
            pos_layout.addWidget(card)

        pos_layout.addStretch()
        layout.addLayout(pos_layout)

        # Çalışan tablosu
        table_label = QLabel("📋 Ekip Üyeleri")
        table_label.setFont(QFont("", 12, QFont.Weight.Bold))
        layout.addWidget(table_label)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Ad Soyad", "Pozisyon", "Departman", "Cinsiyet", "Telefon"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)

        self._load_table()
        layout.addWidget(self.table)

    def _load_table(self):
        """Tabloyu doldur"""
        self.table.setRowCount(len(self.employees))

        for row, emp in enumerate(
            sorted(
                self.employees,
                key=lambda e: (e.position.name if e.position else "ZZZ", e.full_name),
            )
        ):
            # Ad Soyad
            name_item = QTableWidgetItem(emp.full_name)
            name_item.setForeground(QColor("#818cf8"))
            self.table.setItem(row, 0, name_item)

            # Pozisyon
            pos_name = emp.position.name if emp.position else "-"
            self.table.setItem(row, 1, QTableWidgetItem(pos_name))

            # Departman
            dept_name = emp.department.name if emp.department else "-"
            self.table.setItem(row, 2, QTableWidgetItem(dept_name))

            # Cinsiyet
            gender = "Erkek" if str(emp.gender) == "Gender.MALE" else "Kadın"
            self.table.setItem(row, 3, QTableWidgetItem(gender))

            # Telefon
            phone = emp.phone or emp.mobile or "-"
            self.table.setItem(row, 4, QTableWidgetItem(phone))


class ShiftTeamOverview(QWidget):
    """Vardiya Ekipleri Genel Bakış Sayfası"""

    page_title = "Vardiya Ekipleri"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = HRService()
        self.team_service = None
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
            QTabWidget::pane {{
                border: 1px solid {t.border};
                border-radius: 8px;
                background-color: {t.bg_secondary};
            }}
            QTabBar::tab {{
                background-color: {t.bg_tertiary};
                color: {t.text_muted};
                padding: 8px 16px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }}
            QTabBar::tab:selected {{
                background-color: {t.bg_secondary};
                color: {t.text_primary};
            }}
            QTableWidget {{
                background-color: {t.bg_secondary};
                border: 1px solid {t.border};
                border-radius: 8px;
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
        title = QLabel("👥 Vardiya Ekipleri")
        title.setFont(QFont("", 16, QFont.Weight.Bold))
        header.addWidget(title)
        header.addStretch()

        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.clicked.connect(self._load_data)
        header.addWidget(refresh_btn)

        layout.addLayout(header)

        # Tab widget - her ekip için bir sekme
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Özet
        self.summary_label = QLabel()
        layout.addWidget(self.summary_label)

    def showEvent(self, event):
        super().showEvent(event)
        self._ensure_services()
        self._load_data()

    def _ensure_services(self):
        if not self.team_service:
            try:
                from modules.production.calendar_services import ShiftTeamService

                self.team_service = ShiftTeamService()
            except Exception as e:
                print(f"Servis yükleme hatası: {e}")

    def _load_data(self):
        """Verileri yükle"""
        self.tabs.clear()

        if not self.team_service:
            return

        try:
            teams = self.team_service.get_all()
            employees = self.service.get_all_employees(limit=1000)

            total_assigned = 0

            for team in teams:
                team_employees = [e for e in employees if e.shift_team_id == team.id]
                total_assigned += len(team_employees)

                # Sekme oluştur
                tab = TeamTab(team, team_employees)
                icon = "🔵" if team.code == "A" else "🟢" if team.code == "B" else "🟡"
                self.tabs.addTab(
                    tab, f"{icon} {team.code} Ekibi ({len(team_employees)})"
                )

            # Atanmamış çalışanlar
            unassigned = [e for e in employees if not e.shift_team_id]
            if unassigned:
                tab = TeamTab(None, unassigned)
                self.tabs.addTab(tab, f"⚪ Atanmamış ({len(unassigned)})")

            self.summary_label.setText(
                f"Toplam: {len(employees)} çalışan, "
                f"{total_assigned} ekip atanmış, "
                f"{len(unassigned)} atanmamış"
            )

        except Exception as e:
            print(f"Vardiya ekibi yükleme hatası: {e}")

    def closeEvent(self, event):
        self.service.close()
        super().closeEvent(event)
