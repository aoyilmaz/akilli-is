from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QFont
import os
import qtawesome as qta
from config.themes import get_theme


class EmptyStateWidget(QWidget):
    """
    Tüm sekmeler kapatıldığında gösterilecek boş durum ekranı.
    Logo ve karşılama metni içerir.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        t = get_theme()

        # Logo Container
        logo_container = QFrame()
        logo_container.setFixedSize(120, 120)
        logo_container.setStyleSheet(
            f"""
            QFrame {{
                background-color: {t.bg_tertiary};
                border-radius: 20px;
                border: 2px solid {t.border};
            }}
        """
        )
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.setContentsMargins(0, 0, 0, 0)

        # Logo Image
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Go up two levels from ui/components/empty_state.py to get to ui/
        ui_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logo_path = os.path.join(ui_dir, "resources", "icons", "logo.png")

        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            logo_label.setPixmap(
                pixmap.scaled(
                    80,
                    80,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            # Fallback icon if image not found
            icon = qta.icon("ph.cube", color=t.accent_primary)
            logo_label.setPixmap(icon.pixmap(QSize(80, 80)))

        logo_layout.addWidget(logo_label)
        layout.addWidget(logo_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # Title
        title_label = QLabel("Akıllı İş")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(
            f"""
            font-size: 32px;
            font-weight: bold;
            color: {t.text_primary};
        """
        )
        layout.addWidget(title_label)

        # Subtitle
        subtitle_label = QLabel("Açık Kaynak ERP Uygulaması")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet(
            f"""
            font-size: 16px;
            color: {t.text_muted};
        """
        )
        layout.addWidget(subtitle_label)

    def paintEvent(self, event):
        # Update colors dynamically if needed (for theme switching support)
        # For now, simplistic approach is reloading style on show or init
        # Real dynamic update would need a method connected to theme change signal
        pass
