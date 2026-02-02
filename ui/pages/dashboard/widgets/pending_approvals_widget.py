"""
Akıllı İş - PendingApprovalsWidget

Kullanıcının onay bekleyen dökümanlarını listeleyen widget.
"""

from typing import Optional, List
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from config.styles import COLORS, FONT_FAMILY_QT
from .base import BaseWidget, WidgetConfig


# Tablo adlarına göre Türkçe etiketler
TABLE_LABELS = {
    "purchase_requests": ("Satın Alma Talebi", "#2196F3"),
    "purchase_orders": ("Satın Alma Siparişi", "#1976D2"),
    "leaves": ("İzin Talebi", "#4CAF50"),
    "sales_orders": ("Satış Siparişi", "#FF9800"),
    "invoices": ("Fatura", "#9C27B0"),
}


class ApprovalItem(QFrame):
    """Tek bir onay öğesi"""

    clicked = pyqtSignal(int, str, int)  # instance_id, table, document_id

    def __init__(
        self,
        instance_id: int,
        document_table: str,
        document_id: int,
        document_no: str,
        workflow_name: str,
        step_name: str,
        initiated_at: datetime,
        parent=None,
    ):
        super().__init__(parent)
        self.instance_id = instance_id
        self.document_table = document_table
        self.document_id = document_id

        self._setup_ui(document_no, workflow_name, step_name, initiated_at)
        self._setup_style()

    def _setup_ui(
        self,
        document_no: str,
        workflow_name: str,
        step_name: str,
        initiated_at: datetime,
    ):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        # Üst satır: Döküman türü ve no
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # Tür göstergesi
        table_label, color = TABLE_LABELS.get(
            self.document_table, ("Döküman", "#9E9E9E")
        )
        type_indicator = QLabel("●")
        type_indicator.setFixedWidth(12)
        type_indicator.setStyleSheet(f"color: {color}; font-size: 8px;")
        header_layout.addWidget(type_indicator)

        # Döküman bilgisi
        doc_text = f"{table_label}: {document_no or f'#{self.document_id}'}"
        title_label = QLabel(doc_text)
        title_label.setFont(QFont(FONT_FAMILY_QT, 10, QFont.Weight.DemiBold))
        title_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        title_label.setWordWrap(True)
        header_layout.addWidget(title_label, 1)

        # Zaman
        time_str = self._format_time(initiated_at)
        time_label = QLabel(time_str)
        time_label.setFont(QFont(FONT_FAMILY_QT, 9))
        time_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        header_layout.addWidget(time_label)

        layout.addLayout(header_layout)

        # Alt satır: Workflow ve adım bilgisi
        step_text = f"{step_name}" if step_name else workflow_name
        step_label = QLabel(step_text)
        step_label.setFont(QFont(FONT_FAMILY_QT, 9))
        step_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        step_label.setWordWrap(True)
        layout.addWidget(step_label)

    def _setup_style(self):
        _, color = TABLE_LABELS.get(self.document_table, ("", "#9E9E9E"))
        self.setStyleSheet(
            f"""
            ApprovalItem {{
                background: {COLORS['bg_secondary']};
                border-radius: 4px;
                border-left: 3px solid {color};
            }}
            ApprovalItem:hover {{
                background: {COLORS['bg_hover']};
            }}
        """
        )
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _format_time(self, dt: datetime) -> str:
        """Zamanı formatlar"""
        if not dt:
            return ""
        now = datetime.now()
        diff = now - dt

        if diff.days == 0:
            if diff.seconds < 60:
                return "Az önce"
            elif diff.seconds < 3600:
                return f"{diff.seconds // 60} dk önce"
            else:
                return f"{diff.seconds // 3600} saat önce"
        elif diff.days == 1:
            return "Dün"
        elif diff.days < 7:
            return f"{diff.days} gün önce"
        else:
            return dt.strftime("%d.%m.%Y")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(
                self.instance_id, self.document_table, self.document_id
            )
        super().mousePressEvent(event)


class PendingApprovalsWidget(BaseWidget):
    """
    Bekleyen Onaylar Widget'ı

    Kullanıcının onay bekleyen dökümanlarını listeler.
    """

    widget_code = "pending_approvals"
    widget_name = "Bekleyen Onaylarım"
    widget_type = "list"
    widget_description = "Onay bekleyen dökümanlar listesi"
    widget_icon = "check-circle"
    min_size = (1, 1)
    default_size = (1, 2)
    max_size = (2, 2)
    refresh_interval = 60  # 1 dakika

    # Signals
    approval_clicked = pyqtSignal(int, str, int)  # instance_id, table, doc_id

    def __init__(
        self,
        config: Optional[WidgetConfig] = None,
        edit_mode: bool = False,
        parent: Optional[QWidget] = None,
    ):
        self._approvals: List[dict] = []
        self._current_user_id = 1  # TODO: Gerçek kullanıcı ID'si
        super().__init__(config, edit_mode, parent)

    def create_content(self):
        """Widget içeriğini oluşturur"""
        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setStyleSheet(
            f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['border']};
                border-radius: 3px;
            }}
        """
        )

        # İçerik container
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(4)
        self.list_layout.addStretch()

        self.scroll_area.setWidget(self.list_container)
        self.content_layout.addWidget(self.scroll_area, 1)

        # Boş durum mesajı
        self.empty_label = QLabel("Bekleyen onay yok ✓")
        self.empty_label.setFont(QFont(FONT_FAMILY_QT, 10))
        self.empty_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setVisible(False)
        self.content_layout.addWidget(self.empty_label)

    def refresh_data(self):
        """Veriyi yeniler"""
        try:
            from modules.workflow.bridge import get_pending_approvals_for_user

            self._approvals = get_pending_approvals_for_user(
                self._current_user_id
            )
            self._render_approvals()
        except Exception as e:
            print(f"[PendingApprovalsWidget] Veri yükleme hatası: {e}")
            self._approvals = []
            self._render_approvals()

    def _render_approvals(self):
        """Onayları listele"""
        # Mevcut öğeleri temizle
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Boş mesajı göster/gizle
        if not self._approvals:
            self.empty_label.setVisible(True)
            self.scroll_area.setVisible(False)
            return

        self.empty_label.setVisible(False)
        self.scroll_area.setVisible(True)

        # Onayları ekle
        for approval in self._approvals[:10]:  # Max 10 göster
            item = ApprovalItem(
                instance_id=approval.get("instance_id", 0),
                document_table=approval.get("document_table", ""),
                document_id=approval.get("document_id", 0),
                document_no=approval.get("document_no", ""),
                workflow_name=approval.get("workflow_name", ""),
                step_name=approval.get("step_name", ""),
                initiated_at=approval.get("initiated_at"),
                parent=self.list_container,
            )
            item.clicked.connect(self._on_approval_clicked)
            self.list_layout.insertWidget(
                self.list_layout.count() - 1, item
            )

        # Başlığı güncelle
        count = len(self._approvals)
        if count > 0:
            self.title_label.setText(f"Bekleyen Onaylarım ({count})")
        else:
            self.title_label.setText("Bekleyen Onaylarım")

    def _on_approval_clicked(
        self, instance_id: int, table: str, document_id: int
    ):
        """Onay öğesine tıklandığında"""
        self.approval_clicked.emit(instance_id, table, document_id)
        # TODO: İlgili döküman formunu aç
