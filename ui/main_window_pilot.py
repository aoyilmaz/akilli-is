"""
Akıllı İş ERP - Modern UI (Glass & Card Concept)
Pilot Kokpiti Yaklaşımı: Odaklı, Temiz, Akışkan.
"""

import sys
import os
from datetime import datetime

# --- YOL AYARLAMASI (Path Fix) ---
# Bu dosya 'ui' klasöründe olduğu için, bir üst dizini (proje kökünü) yola ekliyoruz.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

# --- IMPORTLAR ---
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QScrollArea,
    QSizePolicy,
    QGridLayout,
    QGraphicsDropShadowEffect,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QDialog,
    QApplication,
)
from PyQt6.QtCore import (
    Qt,
    QPoint,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    QSize,
    pyqtSignal,
    QRect,
)
from PyQt6.QtGui import (
    QIcon,
    QFont,
    QColor,
    QPainter,
    QPen,
    QBrush,
    QLinearGradient,
    QPainterPath,
)

try:
    import qtawesome as qta
except ImportError:
    pass

# --- CONFIG VE MODÜL GÜVENLİĞİ (Safety Blocks) ---
# Config dosyası bulunamazsa varsayılan değerlerle çalışmaya devam et.
try:
    from config import APP_NAME
except ImportError:
    APP_NAME = "Akıllı İş ERP"


# --- TEMA VE RENK PALETİ (SOPHITISCATED DARK) ---
class ModernTheme:
    bg_main = "#121212"  # Çok koyu, derinlik hissi için
    bg_card = "#1e1e1e"  # Kart rengi
    bg_hover = "#2c2c2c"

    primary = "#3b82f6"  # Canlı Modern Mavi (Focus rengi)
    secondary = "#8b5cf6"  # Mor

    text_main = "#ffffff"
    text_muted = "#a1a1aa"  # Göz yormayan gri metin

    border = "#27272a"  # Çok silik kenarlık

    success = "#10b981"  # Zümrüt Yeşili
    danger = "#ef4444"  # Canlı Kırmızı
    warning = "#f59e0b"  # Amber

    radius = 12  # Yuvarlatılmış köşeler


T = ModernTheme()

# --- CSS STİLLERİ ---
GLOBAL_STYLES = f"""
QMainWindow {{ background-color: {T.bg_main}; }}
QWidget {{ font-family: 'Segoe UI', sans-serif; color: {T.text_main}; font-size: 14px; }}

/* Scrollbar */
QScrollBar:vertical {{ border: none; background: {T.bg_main}; width: 8px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {T.border}; min-height: 20px; border-radius: 4px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}

/* Tooltip */
QToolTip {{ background-color: {T.primary}; color: white; border: none; padding: 5px; border-radius: 4px; }}
"""

# --- YARDIMCI GÖRSEL BİLEŞENLER ---


def add_shadow(widget, blur=20, offset=0, alpha=50):
    """Bir widget'a modern gölge efekti ekler"""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setXOffset(0)
    shadow.setYOffset(offset)
    shadow.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(shadow)


class ModernCard(QFrame):
    """Yuvarlak köşeli, gölgeli, 'Card' yapısı"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"""
            ModernCard {{
                background-color: {T.bg_card};
                border-radius: {T.radius}px;
                border: 1px solid {T.border};
            }}
        """
        )
        add_shadow(self, blur=25, offset=4, alpha=40)


class ModernButton(QPushButton):
    """Hafif, ikonlu, modern buton"""

    def __init__(self, text, icon_name=None, bg_color=T.primary, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if icon_name and "qta" in globals():
            self.setIcon(qta.icon(icon_name, color="white"))

        self.setFixedHeight(36)
        self.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border-radius: 8px;
                padding: 0 16px;
                font-weight: 600;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {bg_color}dd;
                margin-top: -1px; 
            }}
            QPushButton:pressed {{
                margin-top: 1px;
            }}
        """
        )


class ModernInput(QFrame):
    """Floating Label Etkili Input Grubu"""

    def __init__(self, placeholder, icon_name=None, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)
        self.setStyleSheet(
            f"""
            .ModernInput {{
                background-color: {T.bg_card};
                border: 1px solid {T.border};
                border-radius: 8px;
            }}
            .ModernInput:hover {{ border: 1px solid {T.text_muted}; }}
        """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(0)

        self.lbl_title = QLabel(placeholder)
        self.lbl_title.setStyleSheet(
            f"color: {T.text_muted}; font-size: 11px; font-weight: bold;"
        )

        self.inp = QLineEdit()
        self.inp.setPlaceholderText("...")
        self.inp.setStyleSheet(
            "border: none; background: transparent; font-size: 14px; color: white; padding: 0;"
        )

        layout.addWidget(self.lbl_title)
        layout.addWidget(self.inp)

        self.inp.focusInEvent = self.on_focus
        self.inp.focusOutEvent = self.on_blur

    def on_focus(self, event):
        self.setStyleSheet(
            f".ModernInput {{ background-color: {T.bg_card}; border: 1px solid {T.primary}; border-radius: 8px; }}"
        )
        self.lbl_title.setStyleSheet(
            f"color: {T.primary}; font-size: 11px; font-weight: bold;"
        )
        QLineEdit.focusInEvent(self.inp, event)

    def on_blur(self, event):
        self.setStyleSheet(
            f".ModernInput {{ background-color: {T.bg_card}; border: 1px solid {T.border}; border-radius: 8px; }}"
        )
        self.lbl_title.setStyleSheet(
            f"color: {T.text_muted}; font-size: 11px; font-weight: bold;"
        )
        QLineEdit.focusOutEvent(self.inp, event)


# --- APP LAUNCHER (MEGA MENÜ) ---
class AppLauncherOverlay(QWidget):
    """Logoya basınca açılan tam ekran uygulama menüsü"""

    menu_item_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Pencere tipi ayarı
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.SubWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.hide()

        # Arka Plan (Blur Simülasyonu)
        self.bg = QFrame(self)
        self.bg.setStyleSheet("background-color: rgba(18, 18, 18, 240);")

        layout = QVBoxLayout(self.bg)
        layout.setContentsMargins(50, 50, 50, 50)

        lbl = QLabel("Uygulamalar")
        lbl.setStyleSheet(
            f"font-size: 32px; font-weight: bold; color: {T.text_main}; margin-bottom: 20px;"
        )
        layout.addWidget(lbl)

        grid = QGridLayout()
        grid.setSpacing(20)

        modules = [
            ("Stok Yönetimi", "fa5s.boxes", "inventory", "#3b82f6"),
            ("Satınalma", "fa5s.shopping-cart", "purchasing", "#10b981"),
            ("Üretim", "fa5s.industry", "production", "#f59e0b"),
            ("Finans", "fa5s.wallet", "finance", "#8b5cf6"),
            ("İnsan Kaynakları", "fa5s.users", "hr", "#ec4899"),
            ("Raporlar", "fa5s.chart-pie", "reports", "#ef4444"),
            ("Ayarlar", "fa5s.cog", "settings", "#64748b"),
        ]

        row, col = 0, 0
        for title, icon, pid, color in modules:
            btn = self.create_app_card(title, icon, pid, color)
            grid.addWidget(btn, row, col)
            col += 1
            if col > 3:
                col = 0
                row += 1

        layout.addLayout(grid)
        layout.addStretch()

        btn_close = QPushButton("Kapat")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet(
            f"background: transparent; color: {T.text_muted}; font-size: 16px; border: 1px solid {T.border}; border-radius: 20px; padding: 10px 30px;"
        )
        btn_close.clicked.connect(self.hide_launcher)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)

    def create_app_card(self, title, icon, pid, color):
        btn = QPushButton()
        btn.setFixedSize(160, 140)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)

        l = QVBoxLayout(btn)

        icon_lbl = QLabel()
        if "qta" in globals():
            icon_lbl.setPixmap(qta.icon(icon, color=color).pixmap(48, 48))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        txt_lbl = QLabel(title)
        txt_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        txt_lbl.setStyleSheet("font-weight: 600; font-size: 14px; margin-top: 10px;")

        l.addStretch()
        l.addWidget(icon_lbl)
        l.addWidget(txt_lbl)
        l.addStretch()

        btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {T.bg_card};
                border: 1px solid {T.border};
                border-radius: 16px;
                color: {T.text_main};
            }}
            QPushButton:hover {{
                background-color: {T.bg_hover};
                border: 1px solid {color};
            }}
        """
        )
        btn.clicked.connect(lambda: self.on_app_clicked(pid))
        return btn

    def on_app_clicked(self, pid):
        self.menu_item_clicked.emit(pid)
        self.hide_launcher()

    def show_launcher(self):
        self.resize(self.parent().size())
        self.bg.resize(self.size())
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(200)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.show()
        self.anim.start()

    def hide_launcher(self):
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(200)
        self.anim.setStartValue(1)
        self.anim.setEndValue(0)
        self.anim.finished.connect(self.hide)
        self.anim.start()


# --- TOAST BİLDİRİMİ ---
class ToastNotification(QFrame):
    """Sağ üst köşeden çıkan bildirim balonu"""

    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedSize(300, 70)
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {T.bg_card};
                border-radius: 8px;
                border-left: 5px solid {T.primary};
            }}
            QLabel {{ color: {T.text_main}; border: none; }}
        """
        )
        add_shadow(self)

        layout = QHBoxLayout(self)
        self.icon_lbl = QLabel()
        layout.addWidget(self.icon_lbl)

        text_layout = QVBoxLayout()
        self.lbl_title = QLabel("Bildirim")
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.lbl_msg = QLabel("Mesaj içeriği...")
        self.lbl_msg.setStyleSheet(f"color: {T.text_muted}; font-size: 12px;")

        text_layout.addWidget(self.lbl_title)
        text_layout.addWidget(self.lbl_msg)
        layout.addLayout(text_layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.hide_toast)
        self.hide()

    def show_message(self, title, message, type="SUCCESS"):
        colors = {
            "SUCCESS": T.success,
            "ERROR": T.danger,
            "WARNING": T.warning,
            "INFO": T.primary,
        }
        icons = {
            "SUCCESS": "fa5s.check-circle",
            "ERROR": "fa5s.exclamation-circle",
            "WARNING": "fa5s.exclamation-triangle",
            "INFO": "fa5s.info-circle",
        }

        col = colors.get(type, T.primary)
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {T.bg_card};
                border-radius: 8px;
                border: 1px solid {T.border};
                border-left: 5px solid {col};
            }}
            QLabel {{ border: none; background: transparent; }}
        """
        )

        self.lbl_title.setText(title)
        self.lbl_msg.setText(message)
        if "qta" in globals():
            self.icon_lbl.setPixmap(
                qta.icon(icons.get(type, "fa5s.info"), color=col).pixmap(24, 24)
            )

        p = self.parent()
        self.move(p.width() - 320, 80)

        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(300)
        self.anim.setStartValue(QPoint(p.width() + 10, 80))
        self.anim.setEndValue(QPoint(p.width() - 320, 80))
        self.anim.setEasingCurve(QEasingCurve.Type.OutBack)

        self.show()
        self.anim.start()
        self.timer.start(4000)

    def hide_toast(self):
        self.timer.stop()
        p = self.parent()
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(300)
        self.anim.setStartValue(self.pos())
        self.anim.setEndValue(QPoint(p.width() + 10, 80))
        self.anim.finished.connect(self.hide)
        self.anim.start()


# --- ANA DÜZEN ELEMANLARI ---


class SlimSidebar(QFrame):
    """Sadece ikonlardan oluşan ince sol şerit"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(70)
        self.setStyleSheet(
            f"""
            QFrame {{ background-color: {T.bg_main}; border-right: 1px solid {T.border}; }}
        """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(15)

        self.btn_logo = QPushButton()
        self.btn_logo.setFixedSize(48, 48)
        self.btn_logo.setCursor(Qt.CursorShape.PointingHandCursor)
        if "qta" in globals():
            self.btn_logo.setIcon(qta.icon("fa5s.th", color=T.primary))
        self.btn_logo.setIconSize(QSize(24, 24))
        self.btn_logo.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {T.bg_card};
                border-radius: 12px;
                border: 1px solid {T.border};
            }}
            QPushButton:hover {{
                background-color: {T.bg_hover};
                border: 1px solid {T.primary};
            }}
        """
        )
        layout.addWidget(self.btn_logo)

        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background: {T.border};")
        layout.addWidget(line)

        self.add_icon_btn(layout, "fa5s.home", "Dashboard")
        self.add_icon_btn(layout, "fa5s.box", "Stok")
        self.add_icon_btn(layout, "fa5s.shopping-cart", "Satınalma")

        layout.addStretch()

        self.add_icon_btn(layout, "fa5s.user-circle", "Profil", bottom=True)

    def add_icon_btn(self, layout, icon, tooltip, bottom=False):
        btn = QPushButton()
        btn.setFixedSize(48, 48)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(tooltip)
        if "qta" in globals():
            btn.setIcon(qta.icon(icon, color=T.text_muted))
        btn.setIconSize(QSize(22, 22))
        btn.setStyleSheet(
            f"""
            QPushButton {{ background: transparent; border-radius: 12px; }}
            QPushButton:hover {{ background-color: {T.bg_hover}; }}
        """
        )
        layout.addWidget(btn)


class Header(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self.setStyleSheet(
            f"background: {T.bg_main}; border-bottom: 1px solid {T.border};"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)

        self.lbl_path = QLabel("Ana Sayfa > Dashboard")
        self.lbl_path.setStyleSheet(f"color: {T.text_muted}; font-size: 13px;")
        layout.addWidget(self.lbl_path)

        layout.addStretch()

        self.search = QLineEdit()
        self.search.setPlaceholderText("Global Arama (Ctrl+K)...")
        self.search.setFixedWidth(300)
        self.search.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {T.bg_card};
                border: 1px solid {T.border};
                border-radius: 18px;
                padding: 6px 15px;
                color: {T.text_main};
            }}
            QLineEdit:focus {{ border: 1px solid {T.primary}; }}
        """
        )
        layout.addWidget(self.search)

        btn_notif = QPushButton()
        if "qta" in globals():
            btn_notif.setIcon(qta.icon("fa5s.bell", color=T.text_muted))
        btn_notif.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(btn_notif)


class DashboardContent(QWidget):
    """Dashboard İçeriği"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        lbl_welcome = QLabel("Hoş Geldiniz, Yönetici")
        lbl_welcome.setStyleSheet(
            f"font-size: 24px; font-weight: bold; color: {T.text_main};"
        )
        layout.addWidget(lbl_welcome)

        grid = QHBoxLayout()
        grid.setSpacing(20)

        grid.addWidget(
            self.create_kpi_card(
                "Toplam Stok", "1,540", "Adet", T.primary, "fa5s.cubes"
            )
        )
        grid.addWidget(
            self.create_kpi_card(
                "Aylık Ciro", "₺482.5K", "+%12", T.success, "fa5s.chart-line"
            )
        )
        grid.addWidget(
            self.create_kpi_card(
                "Bekleyen Sipariş", "12", "Acil", T.warning, "fa5s.clock"
            )
        )

        layout.addLayout(grid)

        split = QHBoxLayout()

        table_card = ModernCard()
        table_layout = QVBoxLayout(table_card)

        lbl_tbl = QLabel("Son Hareketler")
        lbl_tbl.setStyleSheet(
            "font-weight: bold; font-size: 16px; margin-bottom: 10px;"
        )
        table_layout.addWidget(lbl_tbl)

        table = QTableWidget(5, 4)
        table.setHorizontalHeaderLabels(["Ürün", "İşlem", "Tarih", "Durum"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setAlternatingRowColors(False)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        table.setStyleSheet(
            f"""
            QTableWidget {{
                background-color: transparent;
                border: none;
                gridline-color: {T.border};
            }}
            QHeaderView::section {{
                background-color: transparent;
                color: {T.text_muted};
                border: none;
                font-weight: bold;
                padding: 10px;
                text-align: left;
            }}
            QTableWidget::item {{
                padding: 10px;
                border-bottom: 1px solid {T.border};
            }}
            QTableWidget::item:selected {{
                background-color: {T.bg_hover};
                color: {T.text_main};
            }}
        """
        )

        data = [
            ("iPhone 15 Pro", "Satış", "Bugün, 14:30", "Tamamlandı"),
            ("Samsung S24", "Stok Girişi", "Bugün, 10:00", "Bekliyor"),
            ("MacBook Air", "İade", "Dün", "İnceleniyor"),
        ]

        for r, (prod, op, date, status) in enumerate(data):
            table.setItem(r, 0, QTableWidgetItem(prod))
            table.setItem(r, 1, QTableWidgetItem(op))
            table.setItem(r, 2, QTableWidgetItem(date))
            item_status = QTableWidgetItem(status)
            if status == "Tamamlandı":
                item_status.setForeground(QBrush(QColor(T.success)))
            elif status == "Bekliyor":
                item_status.setForeground(QBrush(QColor(T.warning)))
            table.setItem(r, 3, item_status)

        table_layout.addWidget(table)
        split.addWidget(table_card, 2)

        action_card = ModernCard()
        action_layout = QVBoxLayout(action_card)
        action_layout.addWidget(
            QLabel("Hızlı İşlemler", styleSheet="font-weight: bold; font-size: 16px;")
        )

        inp1 = ModernInput("Ürün Adı / Barkod")
        inp2 = ModernInput("Miktar")
        btn_add = ModernButton("Hızlı Ekle", "fa5s.plus", T.primary)

        btn_add.clicked.connect(
            lambda: self.window().toast.show_message(
                "Başarılı", "Hızlı giriş işlemi kaydedildi.", "SUCCESS"
            )
        )

        action_layout.addWidget(inp1)
        action_layout.addWidget(inp2)
        action_layout.addWidget(btn_add)
        action_layout.addStretch()

        split.addWidget(action_card, 1)

        layout.addLayout(split)
        layout.addStretch()

    def create_kpi_card(self, title, value, sub, color, icon):
        card = ModernCard()
        l = QVBoxLayout(card)
        h = QHBoxLayout()
        icn = QLabel()
        if "qta" in globals():
            icn.setPixmap(qta.icon(icon, color=color).pixmap(24, 24))
        tit = QLabel(title)
        tit.setStyleSheet(f"color: {T.text_muted};")
        h.addWidget(icn)
        h.addWidget(tit)
        h.addStretch()
        val = QLabel(value)
        val.setStyleSheet("font-size: 28px; font-weight: bold; margin-top: 10px;")
        s = QLabel(sub)
        s.setStyleSheet(f"color: {color}; font-size: 12px;")
        l.addLayout(h)
        l.addWidget(val)
        l.addWidget(s)
        return card


# --- MAIN WINDOW ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1280, 800)
        self.setStyleSheet(GLOBAL_STYLES)

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = SlimSidebar()
        main_layout.addWidget(self.sidebar)

        content_col = QWidget()
        content_layout = QVBoxLayout(content_col)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.header = Header()
        content_layout.addWidget(self.header)

        self.dashboard = DashboardContent()
        content_layout.addWidget(self.dashboard)

        main_layout.addWidget(content_col)

        self.launcher = AppLauncherOverlay(self)
        self.toast = ToastNotification(self)

        self.sidebar.btn_logo.clicked.connect(self.launcher.show_launcher)
        self.launcher.menu_item_clicked.connect(self.on_menu_click)

    def resizeEvent(self, event):
        if self.launcher.isVisible():
            self.launcher.resize(self.size())
            self.launcher.bg.resize(self.size())
        super().resizeEvent(event)

    def on_menu_click(self, pid):
        self.toast.show_message(
            "Yükleniyor", f"{pid.title()} modülü açılıyor...", "INFO"
        )
        self.header.lbl_path.setText(f"Ana Sayfa > {pid.title()}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
