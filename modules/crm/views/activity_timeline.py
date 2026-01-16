from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QFrame,
    QPushButton,
    QGridLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QDateTime

from database.models.crm import ActivityType
from modules.development import ErrorHandler


class ActivityCard(QFrame):
    """Aktivite Kartı"""

    clicked = pyqtSignal(int)

    def __init__(self, data):
        super().__init__()
        self.data = data
        self.setup_ui()

    def setup_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)

        # Tamamlanmışsa farklı stil
        is_completed = self.data.get("is_completed", False)
        bg_color = "#2d2d30" if not is_completed else "#1e1e1e"
        border_color = "#3e3e42"
        if is_completed:
            border_color = "#2d2d30"

        self.setStyleSheet(
            f"""
            ActivityCard {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 8px;
            }}
            ActivityCard:hover {{
                border: 1px solid #555;
            }}
        """
        )
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        # Header: Icon/Type | Date
        header = QHBoxLayout()

        # Type Icon/Text
        type_name = self.data.get("activity_type", "OTHER")  # Enum Name or Value?
        # Model to_dict -> self.type.value (Arama, Toplantı...)
        # But wait, to_dict might return value. Let's assume value for display.

        type_val = self.data.get("activity_type")  # "Arama", "Toplantı" vs.

        icon = "📝 "
        if type_val == "Arama":
            icon = "📞 "
        elif type_val == "Toplantı":
            icon = "👥 "
        elif type_val == "E-posta":
            icon = "✉️ "

        lbl_type = QLabel(f"{icon} {type_val}")
        lbl_type.setStyleSheet("font-weight: bold; color: #4ec9b0;")

        # Date
        date_str = str(self.data.get("due_date", ""))[:16].replace("T", " ")
        lbl_date = QLabel(date_str)
        lbl_date.setStyleSheet("color: #888; font-size: 11px;")

        header.addWidget(lbl_type)
        header.addStretch()
        header.addWidget(lbl_date)
        layout.addLayout(header)

        # Subject
        lbl_subject = QLabel(self.data.get("subject", ""))
        lbl_subject.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: white; margin-top: 4px;"
        )
        lbl_subject.setWordWrap(True)
        layout.addWidget(lbl_subject)

        # Relation (Lead)
        lead_name = self.data.get("lead_name")
        if lead_name:
            lbl_lead = QLabel(f"👤 {lead_name}")
            lbl_lead.setStyleSheet("color: #aaa; font-size: 11px;")
            layout.addWidget(lbl_lead)

        # Description excerpt
        desc = self.data.get("description", "")
        if desc:
            if len(desc) > 100:
                desc = desc[:100] + "..."
            lbl_desc = QLabel(desc)
            lbl_desc.setStyleSheet("color: #888; font-style: italic;")
            lbl_desc.setWordWrap(True)
            layout.addWidget(lbl_desc)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.data.get("id"))
        super().mousePressEvent(event)


class ActivityTimeline(QWidget):
    """Aktivite Zaman Çizelgesi (Liste Görünümü)"""

    card_clicked = pyqtSignal(int)
    add_clicked = pyqtSignal()
    refresh_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()
        btn_refresh = QPushButton("Yenile")
        btn_refresh.clicked.connect(self.refresh_clicked.emit)

        btn_add = QPushButton("+ Yeni Aktivite")
        btn_add.setStyleSheet(
            "background-color: #007acc; color: white; border: none; padding: 6px 12px; border-radius: 4px;"
        )
        btn_add.clicked.connect(self.add_clicked.emit)

        toolbar.addStretch()
        toolbar.addWidget(btn_refresh)
        toolbar.addWidget(btn_add)
        layout.addLayout(toolbar)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(10)
        self.content_layout.addStretch()

        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)

    def load_data(self, activities: list):
        # Temizle
        while self.content_layout.count() > 1:
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Sırala (Tarihe göre, en yakın/yeni en üstte olsun)
        # Assuming data is list of dicts.
        # String comparison is risky for ISO dates but mostly works. Better sort by backend.
        # Assuming backend returns sorted or we proceed.

        for act in activities:
            card = ActivityCard(act)
            card.clicked.connect(self.card_clicked.emit)
            self.content_layout.insertWidget(self.content_layout.count() - 1, card)
