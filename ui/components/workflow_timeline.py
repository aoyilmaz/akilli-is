"""
Akıllı İş - Workflow Timeline Widget

Döküman onay sürecini görsel timeline olarak gösteren widget.
Onay/red butonları ve tarihçe görüntüleme.
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
    QGroupBox,
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


class TimelineNode(QFrame):
    """Timeline düğümü"""

    def __init__(self, data: dict):
        super().__init__()
        self.data = data
        self.setup_ui()

    def setup_ui(self):
        node_type = self.data.get("type", "pending")

        # Tip bazlı renk ve ikon
        colors = {
            "start": ("#4ec9b0", "🚀"),  # Başlatıldı
            "approve": ("#4CAF50", "✅"),  # Onaylandı
            "reject": ("#f44336", "❌"),  # Reddedildi
            "delegate": ("#FF9800", "🔄"),  # Devredildi
            "request_info": ("#2196F3", "❓"),  # Bilgi talebi
            "pending": ("#9E9E9E", "⏳"),  # Bekliyor
            "complete": ("#4CAF50", "🏁"),  # Tamamlandı
        }

        color, icon = colors.get(node_type, ("#9E9E9E", "📋"))

        self.setStyleSheet(
            f"""
            TimelineNode {{
                background-color: {Colors.SECONDARY};
                border-left: 3px solid {color};
                border-radius: 4px;
                padding: 8px;
                margin-left: 12px;
            }}
        """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Header: Icon + Step Name + Timestamp
        header = QHBoxLayout()

        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 14px;")
        header.addWidget(lbl_icon)

        step_name = self.data.get("step_name", "Adım")
        lbl_step = QLabel(step_name)
        lbl_step.setStyleSheet(f"font-weight: bold; color: {color};")
        header.addWidget(lbl_step)

        header.addStretch()

        timestamp = self.data.get("timestamp", "")
        if timestamp:
            if hasattr(timestamp, "strftime"):
                timestamp = timestamp.strftime("%d.%m.%Y %H:%M")
            else:
                timestamp = str(timestamp)[:16].replace("T", " ")

        lbl_time = QLabel(timestamp)
        lbl_time.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 11px;")
        header.addWidget(lbl_time)

        layout.addLayout(header)

        # User info
        user_name = self.data.get("user_name", "")
        if user_name:
            action_text = self.data.get("action", "")
            action_labels = {
                "approve": "tarafından onaylandı",
                "reject": "tarafından reddedildi",
                "delegate": "tarafından devredildi",
                "request_info": "bilgi talep etti",
            }
            action_label = action_labels.get(action_text, "")

            lbl_user = QLabel(f"{user_name} {action_label}")
            lbl_user.setStyleSheet(f"color: {Colors.TEXT}; font-size: 12px;")
            layout.addWidget(lbl_user)

        # Comment
        comment = self.data.get("comment", "")
        if comment:
            lbl_comment = QLabel(f'"{comment}"')
            lbl_comment.setStyleSheet(
                f"color: {Colors.TEXT_MUTED}; font-style: italic; font-size: 11px;"
            )
            lbl_comment.setWordWrap(True)
            layout.addWidget(lbl_comment)


class WorkflowTimelineWidget(QWidget):
    """
    Workflow Timeline Widget

    Dökümanın onay sürecini görsel olarak gösterir.
    Onay/red butonları mevcut kullanıcının yetkisine göre görünür.

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
            QGroupBox {{
                background-color: {Colors.BACKGROUND};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 8px;
                font-weight: bold;
                color: {Colors.TEXT};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }}
        """
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # Workflow grubu
        self.group_box = QGroupBox("Onay Süreci")
        group_layout = QVBoxLayout(self.group_box)
        group_layout.setSpacing(8)

        # Status badge
        self.lbl_status = QLabel("Durum: -")
        self.lbl_status.setStyleSheet(
            f"""
            padding: 6px 12px;
            border-radius: 4px;
            background-color: {Colors.SECONDARY};
            color: {Colors.TEXT};
            font-weight: bold;
        """
        )
        group_layout.addWidget(self.lbl_status)

        # Timeline scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background: {Colors.SECONDARY};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {Colors.BORDER};
                border-radius: 4px;
            }}
        """
        )

        self.timeline_container = QWidget()
        self.timeline_layout = QVBoxLayout(self.timeline_container)
        self.timeline_layout.setSpacing(8)
        self.timeline_layout.setContentsMargins(4, 4, 4, 4)
        self.timeline_layout.addStretch()

        scroll.setWidget(self.timeline_container)
        scroll.setMinimumHeight(150)
        scroll.setMaximumHeight(300)
        group_layout.addWidget(scroll)

        # Aksiyon butonları
        self.action_buttons = QHBoxLayout()
        self.action_buttons.setSpacing(8)

        self.btn_approve = QPushButton("✅ Onayla")
        self.btn_approve.setStyleSheet(
            f"""
            QPushButton {{
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #45a049;
            }}
            QPushButton:pressed {{
                background-color: #3d8b40;
            }}
        """
        )
        self.btn_approve.clicked.connect(self._on_approve_clicked)
        self.btn_approve.setVisible(False)

        self.btn_reject = QPushButton("❌ Reddet")
        self.btn_reject.setStyleSheet(
            f"""
            QPushButton {{
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #da190b;
            }}
            QPushButton:pressed {{
                background-color: #c41508;
            }}
        """
        )
        self.btn_reject.clicked.connect(self._on_reject_clicked)
        self.btn_reject.setVisible(False)

        self.action_buttons.addStretch()
        self.action_buttons.addWidget(self.btn_approve)
        self.action_buttons.addWidget(self.btn_reject)

        group_layout.addLayout(self.action_buttons)

        main_layout.addWidget(self.group_box)

        # Workflow yoksa gizle
        self.group_box.setVisible(False)

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
                self.group_box.setVisible(False)
                return

            self.group_box.setVisible(True)
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
            self.group_box.setVisible(False)

    def _update_status_badge(self, status: str):
        """Status badge'i güncelle"""
        status_config = {
            "pending": ("Onay Bekliyor", "#FF9800", "#FFF3E0"),
            "approved": ("Onaylandı", "#4CAF50", "#E8F5E9"),
            "rejected": ("Reddedildi", "#f44336", "#FFEBEE"),
            "cancelled": ("İptal Edildi", "#9E9E9E", "#F5F5F5"),
        }

        text, color, bg = status_config.get(status, ("Bilinmiyor", "#9E9E9E", "#F5F5F5"))

        self.lbl_status.setText(f"Durum: {text}")
        self.lbl_status.setStyleSheet(
            f"""
            padding: 6px 12px;
            border-radius: 4px;
            background-color: {bg};
            color: {color};
            font-weight: bold;
        """
        )

    def _render_timeline(self, timeline_data: list):
        """Timeline düğümlerini render et"""
        # Mevcut düğümleri temizle
        while self.timeline_layout.count() > 1:
            item = self.timeline_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Yeni düğümleri ekle
        for event in timeline_data:
            node = TimelineNode(event)
            self.timeline_layout.insertWidget(self.timeline_layout.count() - 1, node)

        # Boş mesaj
        if not timeline_data:
            lbl_empty = QLabel("Henüz işlem yapılmadı")
            lbl_empty.setStyleSheet(
                f"color: {Colors.TEXT_MUTED}; padding: 20px; text-align: center;"
            )
            lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        self.group_box.setVisible(False)
