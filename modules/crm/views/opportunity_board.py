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
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData
from PyQt6.QtGui import QDrag, QPixmap

from database.models.crm import OpportunityStage
from modules.development import ErrorHandler


class KanbanCard(QFrame):
    """Kanban Kartı Bileşeni"""

    clicked = pyqtSignal(int)  # opportunity_id

    def __init__(self, data):
        super().__init__()
        self.data = data
        self.setup_ui()

    def setup_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        # Kart stili - Modern ve temiz
        self.setStyleSheet(
            """
            KanbanCard {
                background-color: #333333;
                border: 1px solid #444;
                border-radius: 6px;
                margin-bottom: 8px;
            }
            KanbanCard:hover {
                background-color: #3e3e3e;
                border: 1px solid #007acc;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """
        )
        self.setFixedWidth(240)
        self.setMinimumHeight(100)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)

        # Üst kısım: Başlık ve Gelir
        top_layout = QHBoxLayout()
        lbl_name = QLabel(self.data.get("name", "İsimsiz"))
        lbl_name.setStyleSheet("font-weight: bold; font-size: 13px; color: #ffffff;")
        lbl_name.setWordWrap(True)
        layout.addWidget(lbl_name)

        # Müşteri/Aday adı
        lead_name = self.data.get("lead_name", "") or self.data.get("customer_name", "")
        if lead_name:
            lbl_lead = QLabel(f"👤 {lead_name}")
            lbl_lead.setStyleSheet("font-size: 11px; color: #aaaaaa;")
            layout.addWidget(lbl_lead)

        # Tutar ve Olasılık satırı
        revenue = float(self.data.get("expected_revenue", 0))
        prob = int(self.data.get("probability", 0))

        info_layout = QHBoxLayout()
        lbl_rev = QLabel(f"{revenue:,.0f} ₺")
        lbl_rev.setStyleSheet("color: #4ec9b0; font-weight: bold;")

        lbl_prob = QLabel(f"%{prob}")
        lbl_prob.setStyleSheet("color: #ce9178;")

        info_layout.addWidget(lbl_rev)
        info_layout.addStretch()
        info_layout.addWidget(lbl_prob)
        layout.addLayout(info_layout)

        # Tarih
        date_str = str(self.data.get("closing_date", ""))[:10]
        if date_str:
            lbl_date = QLabel(f"📅 {date_str}")
            lbl_date.setStyleSheet("font-size: 10px; color: #808080; margin-top: 4px;")
            layout.addWidget(lbl_date)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.data.get("id"))
        super().mousePressEvent(event)


class KanbanColumn(QWidget):
    """Kanban Sütunu"""

    def __init__(self, stage: OpportunityStage, title: str):
        super().__init__()
        self.stage = stage
        self.title = title
        self.cards = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Sütun Başlığı
        header = QFrame()
        header.setStyleSheet(
            """
            background-color: #252526;
            border-radius: 4px;
            padding: 8px;
            margin-bottom: 4px;
        """
        )
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(4, 4, 4, 4)

        lbl_title = QLabel(self.title.upper())
        lbl_title.setStyleSheet("font-weight: bold; color: #cccccc;")
        self.lbl_count = QLabel("0")
        self.lbl_count.setStyleSheet(
            """
            background-color: #444; 
            color: white; 
            border-radius: 10px; 
            padding: 2px 8px;
            font-size: 11px;
        """
        )

        h_lay.addWidget(lbl_title)
        h_lay.addStretch()
        h_lay.addWidget(self.lbl_count)
        layout.addWidget(header)

        # Kartlar için Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")
        self.card_layout = QVBoxLayout(self.content_widget)
        self.card_layout.setSpacing(8)
        self.card_layout.addStretch()  # Kartları yukarı itmek için

        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)

    def add_card(self, card: KanbanCard):
        # Stretch item'dan hemen önce ekle
        self.card_layout.insertWidget(self.card_layout.count() - 1, card)
        self.cards.append(card)
        self.update_count()

    def clear_cards(self):
        # Tüm kartları sil (stretch hariç)
        while self.card_layout.count() > 1:
            item = self.card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.cards = []
        self.update_count()

    def update_count(self):
        self.lbl_count.setText(str(len(self.cards)))


class OpportunityBoard(QWidget):
    """Fırsat Kanban Görünümü"""

    card_clicked = pyqtSignal(int)  # opportunity_id
    add_clicked = pyqtSignal()
    refresh_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.columns = {}  # stage -> KanbanColumn
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()
        btn_refresh = QPushButton("Yenile")
        btn_refresh.clicked.connect(self.refresh_clicked.emit)

        btn_add = QPushButton("+ Yeni Fırsat")
        btn_add.setStyleSheet(
            "background-color: #007acc; color: white; border: none; padding: 6px 12px; border-radius: 4px;"
        )
        btn_add.clicked.connect(self.add_clicked.emit)

        toolbar.addStretch()
        toolbar.addWidget(btn_refresh)
        toolbar.addWidget(btn_add)
        main_layout.addLayout(toolbar)

        # Kanban Board Scroll Area (Yatay Kaydırma)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        board_widget = QWidget()
        self.board_layout = QHBoxLayout(board_widget)
        self.board_layout.setSpacing(12)

        # Sütunları oluştur
        # Enum sırasına göre
        stages = [
            (OpportunityStage.NEW, "Yeni"),
            (OpportunityStage.QUALIFIED, "Kalifiye"),
            (OpportunityStage.PROPOSITION, "Teklif"),
            (OpportunityStage.NEGOTIATION, "Pazarlık"),
            (OpportunityStage.WON, "Kazanıldı"),
            (OpportunityStage.LOST, "Kaybedildi"),
        ]

        for stage_enum, title in stages:
            col = KanbanColumn(stage_enum, title)
            self.board_layout.addWidget(col)
            self.columns[stage_enum.name] = col  # Enum name string key

        self.board_layout.addStretch()
        scroll.setWidget(board_widget)
        main_layout.addWidget(scroll)

    def load_data(self, opportunities: list):
        """Fırsatları panoya yükle"""
        # Önce temizle
        for col in self.columns.values():
            col.clear_cards()

        # Kartları dağıt
        for opp in opportunities:
            # opp bir dict olmalı (to_dict() çıktısı)
            stage_name = opp.get(
                "stage_name"
            )  # Enum name expected from service/model conversion
            # Modelde status -> value dönerken, burada enum key lazım olabilir.
            # CRMService list_opportunities result should check serialization.
            # Model'de `to_dict`te value dönüyor ama bize key lazım olabilir veya value ile match edebiliriz.
            # Model to_dict: "stage": self.stage.value if self.stage else None
            # Enum VALUE (örn "Yeni") geliyor.

            # O yüzden map lazım.
            stage_enum_name = self._find_stage_key_by_value(opp.get("stage"))

            if stage_enum_name and stage_enum_name in self.columns:
                card = KanbanCard(opp)
                card.clicked.connect(self.card_clicked.emit)
                self.columns[stage_enum_name].add_card(card)

    def _find_stage_key_by_value(self, value):
        for stage in OpportunityStage:
            if stage.value == value:
                return stage.name
        return None
