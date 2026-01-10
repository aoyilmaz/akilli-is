"""
Akıllı İş - Alacak Yaşlandırma Raporu
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from config.styles import (
    BG_SECONDARY,
    BG_TERTIARY,
    BORDER,
    TEXT_PRIMARY,
    TEXT_MUTED,
    ACCENT,
    SUCCESS,
    WARNING,
    ERROR,
    get_table_style,
    get_button_style,
)


class ReceivablesAgingPage(QWidget):
    """Alacak yaşlandırma raporu sayfası"""

    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Başlık
        header_layout = QHBoxLayout()

        info = QLabel(
            "Vadesi geçmiş ve açık faturalar müşteri bazında gruplandırılmıştır"
        )
        info.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px;")
        header_layout.addWidget(info)

        header_layout.addStretch()

        refresh_btn = QPushButton("Yenile")
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        refresh_btn.setStyleSheet(get_button_style())
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Yaşlandırma kartları
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        self.card_0_30 = self._create_card("0-30 Gün", "₺0", SUCCESS, "Normal")
        cards_layout.addWidget(self.card_0_30)

        self.card_31_60 = self._create_card("31-60 Gün", "₺0", WARNING, "Takip")
        cards_layout.addWidget(self.card_31_60)

        self.card_61_90 = self._create_card("61-90 Gün", "₺0", "#f97316", "Riskli")
        cards_layout.addWidget(self.card_61_90)

        self.card_90_plus = self._create_card("90+ Gün", "₺0", ERROR, "Kritik")
        cards_layout.addWidget(self.card_90_plus)

        layout.addLayout(cards_layout)

        # Toplam özet
        summary_frame = QFrame()
        summary_frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_SECONDARY};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
        """
        )
        summary_layout = QHBoxLayout(summary_frame)

        self.total_label = QLabel("Toplam Alacak: ₺0")
        self.total_label.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 18px; font-weight: bold;"
        )
        summary_layout.addWidget(self.total_label)

        summary_layout.addStretch()

        self.customer_count_label = QLabel("0 müşteri")
        self.customer_count_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 14px;")
        summary_layout.addWidget(self.customer_count_label)

        layout.addWidget(summary_frame)

        # Müşteri tablosu
        self.table = QTableWidget()
        self._setup_table(
            self.table,
            [
                ("Risk", 60),
                ("Müşteri Kodu", 100),
                ("Müşteri Adı", 200),
                ("Fatura Sayısı", 100),
                ("Toplam Bakiye", 150),
                ("En Eski Vade", 100),
            ],
        )
        layout.addWidget(self.table)

    def _create_card(self, title: str, value: str, color: str, subtitle: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_TERTIARY};
                border: 1px solid {color}40;
                border-radius: 8px;
            }}
        """
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet(
            f"color: {color}; font-size: 24px; font-weight: bold;"
        )
        layout.addWidget(value_label)

        count_label = QLabel("0 müşteri")
        count_label.setObjectName("count")
        count_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(count_label)

        return card

    def _setup_table(self, table: QTableWidget, columns: list):
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels([c[0] for c in columns])

        header = table.horizontalHeader()
        for i, (_, width) in enumerate(columns):
            if i == 2:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                table.setColumnWidth(i, width)

        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)

        table.setStyleSheet(get_table_style())

    def load_data(self, data: dict):
        groups = data.get("groups", {})

        # Kartları güncelle
        self._update_group_card(self.card_0_30, groups.get("0-30", {}))
        self._update_group_card(self.card_31_60, groups.get("31-60", {}))
        self._update_group_card(self.card_61_90, groups.get("61-90", {}))
        self._update_group_card(self.card_90_plus, groups.get("90+", {}))

        # Toplam
        total = data.get("total_receivables", 0)
        self.total_label.setText(f"Toplam Alacak: ₺{total:,.2f}")

        total_customers = data.get("total_customers", 0)
        self.customer_count_label.setText(f"{total_customers} müşteri")

        # Tüm müşterileri tabloya ekle
        all_customers = []
        risk_config = {
            "0-30": {"icon": "●", "color": SUCCESS},
            "31-60": {"icon": "●", "color": WARNING},
            "61-90": {"icon": "●", "color": "#f97316"},
            "90+": {"icon": "●", "color": ERROR},
        }

        for group_name, group_data in groups.items():
            config = risk_config.get(group_name, {})
            for customer in group_data.get("customers", []):
                customer["risk_icon"] = config.get("icon", "")
                customer["risk_color"] = config.get("color", "#ffffff")
                customer["risk_group"] = group_name
                all_customers.append(customer)

        # Günlere göre sırala (en kritik en üstte)
        all_customers.sort(key=lambda x: x.get("max_days", 0), reverse=True)

        self.table.setRowCount(len(all_customers))
        for row, customer in enumerate(all_customers):
            risk_item = QTableWidgetItem(customer.get("risk_icon", ""))
            risk_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            risk_item.setForeground(QColor(customer.get("risk_color", "#ffffff")))
            self.table.setItem(row, 0, risk_item)

            self.table.setItem(
                row, 1, QTableWidgetItem(customer.get("customer_code", ""))
            )
            self.table.setItem(
                row, 2, QTableWidgetItem(customer.get("customer_name", ""))
            )

            count = customer.get("invoice_count", 0)
            count_item = QTableWidgetItem(str(count))
            count_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row, 3, count_item)

            balance = customer.get("total_balance", 0)
            balance_item = QTableWidgetItem(f"₺{balance:,.2f}")
            balance_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            balance_item.setForeground(QColor(customer.get("risk_color", "#ffffff")))
            self.table.setItem(row, 4, balance_item)

            days = customer.get("max_days", 0)
            days_item = QTableWidgetItem(f"{days} gün")
            days_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            if days > 90:
                days_item.setForeground(QColor(ERROR))
            elif days > 60:
                days_item.setForeground(QColor("#f97316"))
            elif days > 30:
                days_item.setForeground(QColor(WARNING))
            self.table.setItem(row, 5, days_item)

    def _update_group_card(self, card: QFrame, group_data: dict):
        value = group_data.get("total", 0)
        count = group_data.get("count", 0)

        value_label = card.findChild(QLabel, "value")
        if value_label:
            value_label.setText(f"₺{value:,.2f}")

        count_label = card.findChild(QLabel, "count")
        if count_label:
            count_label.setText(f"{count} müşteri")
