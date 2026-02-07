"""
Akıllı İş - İK Dashboard Modülü

İnsan Kaynakları ana dashboard UI.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QScrollArea,
)
from PyQt6.QtCore import Qt
import qtawesome as qta
from config.icons import ICONS
from config.themes import get_theme

from ui.components import (
    PageHeader,
    MiniStatCard,
    ScrollableCardContainer,
)
from modules.hr.services import HRDashboardService


class HRDashboardModule(QWidget):
    """İK Dashboard Modülü"""

    page_title = "İK Dashboard"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header
        self.header = PageHeader(
            title="İK Dashboard",
            icon=ICONS.DASHBOARD,
            show_search=False,
            show_add=False,
            parent=self,
        )
        self.header.refresh_clicked.connect(self._load_data)
        layout.addWidget(self.header)

        # Scroll Area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(24)

        # Üst kart satırı (ScrollableCardContainer)
        stats_container = ScrollableCardContainer()

        self.total_card = MiniStatCard(
            "Toplam Çalışan", "0", "info", icon=ICONS.USERS, icon_color="#3b82f6"
        )
        self.present_card = MiniStatCard(
            "Bugün Katılım", "0%", "success", icon=ICONS.CHECK, icon_color="#10b981"
        )
        self.leave_card = MiniStatCard(
            "İzinli", "0", "warning", icon=ICONS.CALENDAR, icon_color="#f59e0b"
        )
        self.pending_card = MiniStatCard(
            "Bekleyen İzin", "0", "error", icon=ICONS.TIME, icon_color="#ef4444"
        )

        stats_container.add_card(self.total_card)
        stats_container.add_card(self.present_card)
        stats_container.add_card(self.leave_card)
        stats_container.add_card(self.pending_card)
        stats_container.add_stretch()
        content_layout.addWidget(stats_container)

        # Orta bölüm: İki sütun
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(24)

        # Sol: Yaklaşan doğum günleri
        self._setup_birthdays_section(middle_layout)

        # Sağ: Son işe alımlar ve izinler
        right_panel = QVBoxLayout()
        right_panel.setSpacing(24)
        self._setup_recent_hires_section(right_panel)
        middle_layout.addLayout(right_panel, 1)

        content_layout.addLayout(middle_layout)

        # Alt bölüm: Kıdem dağılımı
        t = get_theme()
        tenure_group = QFrame()
        tenure_group.setStyleSheet(
            f"""
            QFrame {{
                background: {t.card_bg};
                border: 1px solid {t.border};
                border-radius: 12px;
                padding: 16px;
            }}
        """
        )
        tenure_layout = QVBoxLayout(tenure_group)

        tenure_title = QLabel("📊 Kıdem Dağılımı")
        tenure_title.setStyleSheet(
            f"color: {t.text_primary}; font-size: 16px; font-weight: bold;"
        )
        tenure_layout.addWidget(tenure_title)

        self.tenure_layout = QHBoxLayout()
        self.tenure_layout.setSpacing(12)
        tenure_layout.addLayout(self.tenure_layout)

        content_layout.addWidget(tenure_group)
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def showEvent(self, event):
        super().showEvent(event)
        self._ensure_service()
        self._load_data()

    def _ensure_service(self):
        if not self.service:
            self.service = HRDashboardService()

    def _load_data(self):
        self._ensure_service()
        try:
            data = self.service.get_dashboard_data()

            # Kartları güncelle
            emp_counts = data.get("employee_counts", {})
            self.total_card.update_value(str(emp_counts.get("total", 0)))

            att_summary = data.get("attendance_summary", {})
            rate = att_summary.get("attendance_rate", 0)
            self.present_card.update_value(f"{rate}%")
            self.leave_card.update_value(str(att_summary.get("on_leave", 0)))

            leave_summary = data.get("leave_summary", {})
            self.pending_card.update_value(str(leave_summary.get("pending", 0)))

            # Doğum günleri
            birthdays = data.get("upcoming_birthdays", [])
            self.birthdays_table.setRowCount(min(len(birthdays), 5))
            for i, b in enumerate(birthdays[:5]):
                self.birthdays_table.setItem(i, 0, QTableWidgetItem(b["name"]))
                self.birthdays_table.setItem(i, 1, QTableWidgetItem(b["birth_date"]))
                self.birthdays_table.setItem(
                    i, 2, QTableWidgetItem(f"{b['days_until']} gün")
                )

            # Yeni işe alımlar
            hires = data.get("new_hires", [])
            self.hires_table.setRowCount(min(len(hires), 5))
            for i, h in enumerate(hires[:5]):
                self.hires_table.setItem(i, 0, QTableWidgetItem(h["name"]))
                self.hires_table.setItem(
                    i, 1, QTableWidgetItem(h.get("department") or "")
                )
                self.hires_table.setItem(
                    i, 2, QTableWidgetItem(h.get("hire_date") or "")
                )

            # Kıdem dağılımı
            tenure = data.get("tenure_distribution", {})
            self._update_tenure_chart(tenure)

        except Exception as e:
            print(f"Dashboard yükleme hatası: {e}")

    def _update_tenure_chart(self, tenure: dict):
        """Kıdem dağılımı görselini güncelle"""
        while self.tenure_layout.count():
            item = self.tenure_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        chart_colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"]
        labels = ["0-1 Yıl", "1-3 Yıl", "3-5 Yıl", "5-10 Yıl", "10+ Yıl"]
        keys = ["0-1", "1-3", "3-5", "5-10", "10+"]

        total = sum(tenure.values())
        if total == 0:
            total = 1

        for i, key in enumerate(keys):
            val = tenure.get(key, 0)
            pct = round(val / total * 100)

            item = QFrame()
            item.setStyleSheet(
                f"background: {chart_colors[i]}; border-radius: 8px; padding: 12px;"
            )
            item_layout = QVBoxLayout(item)
            item_layout.setContentsMargins(8, 8, 8, 8)

            lbl = QLabel(labels[i])
            lbl.setStyleSheet("color: white; font-size: 12px;")
            item_layout.addWidget(lbl)

            val_lbl = QLabel(f"{val} ({pct}%)")
            val_lbl.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
            item_layout.addWidget(val_lbl)

            self.tenure_layout.addWidget(item)

    def _setup_birthdays_section(self, layout):
        t = get_theme()
        section = QFrame()
        section.setStyleSheet(
            f"background: {t.card_bg}; border: 1px solid {t.border}; border-radius: 12px; padding: 16px;"
        )
        s_layout = QVBoxLayout(section)

        title = QLabel("🎂 Yaklaşan Doğum Günleri")
        title.setStyleSheet(
            f"color: {t.text_primary}; font-size: 16px; font-weight: bold;"
        )
        s_layout.addWidget(title)

        self.birthdays_table = QTableWidget()
        self.birthdays_table.setColumnCount(3)
        self.birthdays_table.setHorizontalHeaderLabels(["Çalışan", "Tarih", "Kalan"])
        self.birthdays_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.birthdays_table.verticalHeader().hide()
        self.birthdays_table.setStyleSheet("border: none; background: transparent;")
        s_layout.addWidget(self.birthdays_table)

        layout.addWidget(section, 1)

    def _setup_recent_hires_section(self, layout):
        t = get_theme()
        section = QFrame()
        section.setStyleSheet(
            f"background: {t.card_bg}; border: 1px solid {t.border}; border-radius: 12px; padding: 16px;"
        )
        s_layout = QVBoxLayout(section)

        title = QLabel("🆕 Son İşe Alımlar")
        title.setStyleSheet(
            f"color: {t.text_primary}; font-size: 16px; font-weight: bold;"
        )
        s_layout.addWidget(title)

        self.hires_table = QTableWidget()
        self.hires_table.setColumnCount(3)
        self.hires_table.setHorizontalHeaderLabels(["Çalışan", "Departman", "Tarih"])
        self.hires_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.hires_table.verticalHeader().hide()
        self.hires_table.setStyleSheet("border: none; background: transparent;")
        s_layout.addWidget(self.hires_table)

        layout.addWidget(section)

    def closeEvent(self, event):
        if self.service:
            self.service.close()
        super().closeEvent(event)
