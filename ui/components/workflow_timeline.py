"""
Akıllı İş - Workflow Timeline Widget

Döküman onay sürecini görsel timeline olarak gösteren widget.
Onay/red butonları ve tarihçe görüntüleme.
Yatay (horizontal) ve minimal tasarım.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QFrame,
    QPushButton,
    QTextEdit,
    QDialog,
    QDialogButtonBox,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from config.styles import Colors


class ApprovalDialog(QDialog):
    """Onay/Red dialog'u"""

    def __init__(self, parent=None, action_type: str = "approve"):
        super().__init__(parent)
        self.action_type = action_type
        self.comment = ""
        self.setup_ui()

    def setup_ui(self):
        if self.action_type == "approve":
            self.setWindowTitle("Onay")
            title_text = "Onay Yorumu (Opsiyonel)"
            self.setStyleSheet(
                f"""
                QDialog {{
                    background-color: {Colors.BACKGROUND};
                }}
                QLabel {{
                    color: {Colors.TEXT};
                }}
                QTextEdit {{
                    background-color: {Colors.SECONDARY};
                    color: {Colors.TEXT};
                    border: 1px solid {Colors.BORDER};
                    border-radius: 4px;
                    padding: 8px;
                }}
            """
            )
        else:
            self.setWindowTitle("Reddet")
            title_text = "Red Gerekçesi (Zorunlu)"
            self.setStyleSheet(
                f"""
                QDialog {{
                    background-color: {Colors.BACKGROUND};
                }}
                QLabel {{
                    color: {Colors.TEXT};
                }}
                QTextEdit {{
                    background-color: {Colors.SECONDARY};
                    color: {Colors.TEXT};
                    border: 1px solid {Colors.DANGER};
                    border-radius: 4px;
                    padding: 8px;
                }}
            """
            )

        self.resize(400, 200)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Başlık
        lbl_title = QLabel(title_text)
        lbl_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(lbl_title)

        # Yorum alanı
        self.txt_comment = QTextEdit()
        self.txt_comment.setPlaceholderText(
            "Yorumunuzu girin..."
            if self.action_type == "approve"
            else "Red gerekçesini girin..."
        )
        self.txt_comment.setMinimumHeight(80)
        layout.addWidget(self.txt_comment)

        # Butonlar
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self):
        self.comment = self.txt_comment.toPlainText().strip()

        # Red için yorum zorunlu
        if self.action_type == "reject" and not self.comment:
            self.txt_comment.setFocus()
            return

        super().accept()

    def get_comment(self) -> str:
        return self.comment


class TimelineNodeCompact(QFrame):
    """Kompakt yatay timeline düğümü - sadece ikon ve adım adı"""

    def __init__(self, data: dict):
        super().__init__()
        self.data = data
        self.setup_ui()

    def setup_ui(self):
        node_type = self.data.get("type", "pending")

        # Tip bazlı renk ve ikon
        colors = {
            "start": ("#4ec9b0", "🚀"),
            "approve": ("#4CAF50", "✓"),
            "reject": ("#f44336", "✗"),
            "delegate": ("#FF9800", "→"),
            "request_info": ("#2196F3", "?"),
            "pending": ("#9E9E9E", "⏳"),
            "complete": ("#4CAF50", "✓"),
        }

        color, icon = colors.get(node_type, ("#9E9E9E", "•"))

        self.setFixedHeight(32)
        self.setStyleSheet(
            f"""
            TimelineNodeCompact {{
                background-color: {color}20;
                border: 1px solid {color};
                border-radius: 16px;
                padding: 0 8px;
            }}
        """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        # İkon
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet(f"color: {color}; font-size: 12px; border: none; background: transparent;")
        layout.addWidget(lbl_icon)

        # Adım adı (kısa)
        step_name = self.data.get("step_name") or ""
        if len(step_name) > 15:
            step_name = step_name[:12] + "..."
        lbl_step = QLabel(step_name)
        lbl_step.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold; border: none; background: transparent;")
        layout.addWidget(lbl_step)

        # Tooltip ile detay
        user_name = self.data.get("user_name") or ""
        # Service "date" kullanıyor, widget "timestamp" bekliyor
        timestamp = self.data.get("timestamp") or self.data.get("date") or ""
        if timestamp and hasattr(timestamp, "strftime"):
            timestamp = timestamp.strftime("%d.%m.%Y %H:%M")
        comment = self.data.get("comment", "")

        tooltip_parts = []
        if user_name:
            tooltip_parts.append(f"Kullanıcı: {user_name}")
        if timestamp:
            tooltip_parts.append(f"Tarih: {timestamp}")
        if comment:
            tooltip_parts.append(f"Yorum: {comment}")

        if tooltip_parts:
            self.setToolTip("\n".join(tooltip_parts))


class WorkflowTimelineWidget(QWidget):
    """
    Workflow Timeline Widget - Yatay ve Minimal

    Dökümanın onay sürecini yatay olarak gösterir.
    Status | Timeline Nodes | Action Buttons

    Signals:
        action_taken(instance_id, action, comment): Aksiyon alındığında emit edilir
    """

    action_taken = pyqtSignal(int, str, str)  # instance_id, action, comment

    def __init__(self, parent=None):
        super().__init__(parent)
        self.instance_id = None
        self.can_approve = False
        self.current_user_id = None
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: transparent;
            }}
        """
        )

        # Tek satır yatay layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 8, 0, 8)
        main_layout.setSpacing(12)

        # Sol: Status badge
        self.lbl_status = QLabel("⏳ Bekliyor")
        self.lbl_status.setFixedHeight(32)
        self.lbl_status.setStyleSheet(
            f"""
            padding: 4px 12px;
            border-radius: 16px;
            background-color: {Colors.SECONDARY};
            color: {Colors.TEXT};
            font-weight: bold;
            font-size: 11px;
        """
        )
        main_layout.addWidget(self.lbl_status)

        # Ayraç
        separator = QLabel("│")
        separator.setStyleSheet(f"color: {Colors.BORDER}; font-size: 14px;")
        main_layout.addWidget(separator)

        # Orta: Timeline düğümleri (yatay scroll)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFixedHeight(48)
        scroll.setStyleSheet(
            f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:horizontal {{
                background: {Colors.SECONDARY};
                height: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:horizontal {{
                background: {Colors.BORDER};
                border-radius: 3px;
                min-width: 20px;
            }}
        """
        )

        self.timeline_container = QWidget()
        self.timeline_container.setStyleSheet("background-color: transparent;")
        self.timeline_layout = QHBoxLayout(self.timeline_container)
        self.timeline_layout.setSpacing(8)
        self.timeline_layout.setContentsMargins(4, 8, 4, 8)
        self.timeline_layout.addStretch()

        scroll.setWidget(self.timeline_container)
        main_layout.addWidget(scroll, 1)  # stretch factor

        # Ayraç
        separator2 = QLabel("│")
        separator2.setStyleSheet(f"color: {Colors.BORDER}; font-size: 14px;")
        main_layout.addWidget(separator2)

        # Sağ: Aksiyon butonları
        self.btn_approve = QPushButton("✓ Onayla")
        self.btn_approve.setFixedHeight(32)
        self.btn_approve.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_approve.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 4px 12px;
                border-radius: 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """
        )
        self.btn_approve.clicked.connect(self._on_approve_clicked)
        self.btn_approve.setVisible(False)
        main_layout.addWidget(self.btn_approve)

        self.btn_reject = QPushButton("✗ Reddet")
        self.btn_reject.setFixedHeight(32)
        self.btn_reject.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reject.setStyleSheet(
            """
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 4px 12px;
                border-radius: 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c41508;
            }
        """
        )
        self.btn_reject.clicked.connect(self._on_reject_clicked)
        self.btn_reject.setVisible(False)
        main_layout.addWidget(self.btn_reject)

        # Başlangıçta gizle
        self.setVisible(False)

    def load_workflow(
        self, table_name: str, document_id: int, current_user_id: int = None
    ):
        """
        Döküman için workflow timeline'ı yükle.

        Args:
            table_name: Tablo adı (örn: "purchase_requests")
            document_id: Döküman ID'si
            current_user_id: Mevcut kullanıcı ID'si (yetki kontrolü için)
        """
        self.current_user_id = current_user_id

        try:
            from modules.workflow.bridge import (
                get_document_workflow_status,
                get_workflow_timeline,
            )

            # Workflow durumunu al
            workflow_data = get_document_workflow_status(table_name, document_id)

            if not workflow_data:
                self.setVisible(False)
                return

            self.setVisible(True)
            self.instance_id = workflow_data.get("instance_id")

            # Status badge güncelle
            status = workflow_data.get("status", "pending")
            self._update_status_badge(status)

            # Can approve?
            self.can_approve = workflow_data.get("can_approve", False)
            self.btn_approve.setVisible(self.can_approve and status == "pending")
            self.btn_reject.setVisible(self.can_approve and status == "pending")

            # Timeline'ı yükle
            timeline_data = get_workflow_timeline(self.instance_id)
            self._render_timeline(timeline_data)

        except Exception as e:
            print(f"[WorkflowTimeline] Yükleme hatası: {e}")
            self.setVisible(False)

    def _update_status_badge(self, status: str):
        """Status badge'i güncelle"""
        status_config = {
            "pending": ("⏳ Onay Bekliyor", "#FF9800", "#FFF3E0"),
            "approved": ("✓ Onaylandı", "#4CAF50", "#E8F5E9"),
            "rejected": ("✗ Reddedildi", "#f44336", "#FFEBEE"),
            "cancelled": ("⊘ İptal", "#9E9E9E", "#F5F5F5"),
        }

        text, color, bg = status_config.get(status, ("? Bilinmiyor", "#9E9E9E", "#F5F5F5"))

        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(
            f"""
            padding: 4px 12px;
            border-radius: 16px;
            background-color: {bg};
            color: {color};
            font-weight: bold;
            font-size: 11px;
        """
        )

    def _render_timeline(self, timeline_data: list):
        """Timeline düğümlerini render et"""
        # Mevcut düğümleri temizle (stretch hariç)
        while self.timeline_layout.count() > 1:
            item = self.timeline_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # None kontrolü
        if timeline_data is None:
            timeline_data = []

        # Yeni düğümleri ekle (yatay sırayla)
        for event in timeline_data:
            node = TimelineNodeCompact(event)
            self.timeline_layout.insertWidget(
                self.timeline_layout.count() - 1, node
            )

        # Boş mesaj
        if not timeline_data:
            lbl_empty = QLabel("Henüz işlem yok")
            lbl_empty.setStyleSheet(
                f"color: {Colors.TEXT_MUTED}; font-size: 11px; font-style: italic;"
            )
            self.timeline_layout.insertWidget(0, lbl_empty)

    def _on_approve_clicked(self):
        """Onayla butonuna tıklandı"""
        dialog = ApprovalDialog(self, action_type="approve")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            comment = dialog.get_comment()
            self._process_action("approve", comment)

    def _on_reject_clicked(self):
        """Reddet butonuna tıklandı"""
        dialog = ApprovalDialog(self, action_type="reject")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            comment = dialog.get_comment()
            self._process_action("reject", comment)

    def _process_action(self, action: str, comment: str):
        """Aksiyonu işle"""
        if not self.instance_id or not self.current_user_id:
            return

        try:
            from modules.workflow.bridge import process_workflow_action

            success = process_workflow_action(
                instance_id=self.instance_id,
                user_id=self.current_user_id,
                action=action,
                comment=comment,
            )

            if success:
                self.action_taken.emit(self.instance_id, action, comment)
                # Timeline'ı yenile (parent form yapmalı)
            else:
                print(f"[WorkflowTimeline] Aksiyon başarısız: {action}")

        except Exception as e:
            print(f"[WorkflowTimeline] Aksiyon hatası: {e}")

    def clear(self):
        """Widget'ı temizle"""
        self.instance_id = None
        self.can_approve = False
        self.setVisible(False)
