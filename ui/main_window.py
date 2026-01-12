"""
Akıllı İş ERP - Ana Pencere
Versiyon: 2.5.0 (Layout Fixes)
"""

import sys
import os
from datetime import datetime

# Proje kök dizinini yola ekle
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QApplication,
    QSizeGrip,
    QStatusBar,
    QScrollArea,
    QSizePolicy,
)
from PyQt6.QtCore import (
    Qt,
    QPoint,
    QPropertyAnimation,
    QEasingCurve,
    QSize,
    pyqtSignal,
    QPointF,
    QTimer,
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

from config import APP_NAME, APP_DESCRIPTION
from config.themes import ThemeManager, get_theme

# --- IMPORTLAR ---
from ui.pages.placeholder import PlaceholderPage

# Modül Importları (Güvenli Blok)
try:
    from modules.inventory import InventoryModule
    from modules.inventory.views import (
        WarehouseModule,
        MovementModule,
        CategoryModule,
        StockReportsModule,
        StockCountModule,
        UnitModule,
    )
except ImportError:
    InventoryModule = WarehouseModule = MovementModule = CategoryModule = (
        StockReportsModule
    ) = StockCountModule = UnitModule = PlaceholderPage

try:
    from modules.production import (
        BOMModule,
        WorkOrderModule,
        PlanningModule,
        WorkStationModule,
    )
    from modules.production.views.calendar_module import CalendarModule
except ImportError:
    BOMModule = WorkOrderModule = PlanningModule = WorkStationModule = (
        CalendarModule
    ) = PlaceholderPage

try:
    from modules.purchasing import (
        SupplierModule,
        PurchaseRequestModule,
        GoodsReceiptModule,
        PurchaseOrderModule,
    )
except ImportError:
    SupplierModule = PurchaseRequestModule = GoodsReceiptModule = (
        PurchaseOrderModule
    ) = PlaceholderPage

try:
    from modules.development.views import DevelopmentModule
except ImportError:
    DevelopmentModule = PlaceholderPage

try:
    from modules.sales import (
        CustomerModule,
        SalesQuoteModule,
        SalesOrderModule,
        DeliveryNoteModule,
        InvoiceModule,
    )
    from modules.sales.views.price_list_module import PriceListModule
except ImportError:
    CustomerModule = SalesQuoteModule = SalesOrderModule = DeliveryNoteModule = (
        InvoiceModule
    ) = PriceListModule = PlaceholderPage

try:
    from modules.purchasing.views.purchase_invoice_module import PurchaseInvoiceModule
except ImportError:
    PurchaseInvoiceModule = PlaceholderPage

try:
    from modules.accounting.views.account_module import AccountModule
    from modules.accounting.views.journal_module import JournalModule
    from modules.accounting.views.reports_module import AccountingReportsModule
except ImportError:
    AccountModule = JournalModule = AccountingReportsModule = PlaceholderPage

try:
    from modules.finance.views.receipt_module import ReceiptModule
    from modules.finance.views.payment_module import PaymentModule
    from modules.finance.views.reconciliation_module import ReconciliationModule
    from modules.finance.views.account_statement_module import AccountStatementModule
except ImportError:
    ReceiptModule = PaymentModule = ReconciliationModule = AccountStatementModule = (
        PlaceholderPage
    )

try:
    from modules.mrp.views.mrp_module import MRPModule
except ImportError:
    MRPModule = PlaceholderPage

try:
    from modules.reports.views.sales_reports_module import SalesReportsModule
    from modules.reports.views.stock_aging_module import StockAgingModule
    from modules.reports.views.production_oee_module import ProductionOEEModule
    from modules.reports.views.supplier_performance_module import (
        SupplierPerformanceModule,
    )
    from modules.reports.views.receivables_aging_module import ReceivablesAgingModule
except ImportError:
    SalesReportsModule = StockAgingModule = ProductionOEEModule = (
        SupplierPerformanceModule
    ) = ReceivablesAgingModule = PlaceholderPage

try:
    from modules.hr.views.employee_module import EmployeeModule
    from modules.hr.views.department_module import DepartmentModule
    from modules.hr.views.position_module import PositionModule
    from modules.hr.views.leave_module import LeaveModule
    from modules.hr.views.org_chart_module import OrgChartModule
    from modules.hr.views.shift_team_overview import ShiftTeamOverview
except ImportError:
    EmployeeModule = DepartmentModule = PositionModule = LeaveModule = PlaceholderPage
    OrgChartModule = ShiftTeamOverview = PlaceholderPage


# --- DASHBOARD BİLEŞENLERİ ---


class ModernGraphWidget(QWidget):
    def __init__(self, data, color="#007acc", parent=None):
        super().__init__(parent)
        self.data = data
        self.color = QColor(color)
        self.setFixedHeight(60)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self.data:
            return
        w, h = self.width(), self.height()
        max_val = max(self.data) if max(self.data) > 0 else 1
        min_val = min(self.data)
        path = QPainterPath()
        x_step = w / (len(self.data) - 1)
        points = []
        for i, val in enumerate(self.data):
            x = i * x_step
            normalized = (
                (val - min_val) / (max_val - min_val) if max_val > min_val else 0.5
            )
            y = h - (normalized * (h - 10)) - 5
            points.append(QPointF(x, y))
        path.moveTo(points[0])
        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i + 1]
            c1 = QPointF((p1.x() + p2.x()) / 2, p1.y())
            c2 = QPointF((p1.x() + p2.x()) / 2, p2.y())
            path.cubicTo(c1, c2, p2)
        fill_path = QPainterPath(path)
        fill_path.lineTo(w, h)
        fill_path.lineTo(0, h)
        fill_path.closeSubpath()
        grad = QLinearGradient(0, 0, 0, h)
        c_start = QColor(self.color)
        c_start.setAlpha(100)
        c_end = QColor(self.color)
        c_end.setAlpha(0)
        grad.setColorAt(0, c_start)
        grad.setColorAt(1, c_end)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(grad)
        painter.drawPath(fill_path)
        painter.setPen(QPen(self.color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)


class KPICard(QFrame):
    def __init__(
        self, title, value, subtext, icon, color, graph_data=None, parent=None
    ):
        super().__init__(parent)
        t = get_theme()
        self.setStyleSheet(
            f"QFrame {{ background-color: {t.card_bg}; border: 1px solid {t.border}; border-radius: {t.radius_large}px; }} QFrame:hover {{ border: 1px solid {color}; }}"
        )
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 10)
        top = QHBoxLayout()
        icon_lbl = QLabel()
        if "qta" in globals():
            icon_lbl.setPixmap(qta.icon(icon, color=color).pixmap(24, 24))
        top.addWidget(icon_lbl)
        top.addWidget(
            QLabel(
                title,
                styleSheet=f"color: {t.text_muted}; font-size: 14px; font-weight: 500; border: none;",
            )
        )
        top.addStretch()
        layout.addLayout(top)
        layout.addWidget(
            QLabel(
                value,
                styleSheet=f"color: {t.text_primary}; font-size: 28px; font-weight: bold; border: none; background: transparent;",
            )
        )
        if graph_data:
            layout.addWidget(ModernGraphWidget(graph_data, color))
        else:
            layout.addStretch()
        layout.addWidget(
            QLabel(
                subtext,
                styleSheet=f"color: {t.text_secondary}; font-size: 12px; margin-top: 5px; border: none; background: transparent;",
            )
        )


class TaskItem(QFrame):
    def __init__(self, title, desc, status_color, parent=None):
        super().__init__(parent)
        t = get_theme()
        self.setStyleSheet(
            f"QFrame {{ background-color: {t.bg_primary}; border-radius: 6px; border-left: 3px solid {status_color}; }} QLabel {{ border: none; background: transparent; }}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.addWidget(
            QLabel(title, styleSheet=f"color: {t.text_primary}; font-weight: bold;")
        )
        layout.addWidget(
            QLabel(desc, styleSheet=f"color: {t.text_muted}; font-size: 11px;")
        )


class DashboardLogo(QWidget):
    def __init__(self, size=56, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = self.width() / 2
        s = self.width() / 100
        g = QLinearGradient(0, 0, self.width(), self.height())
        g.setColorAt(0, QColor("#007acc"))
        g.setColorAt(1, QColor("#a855f7"))
        pen = QPen(QBrush(g), 5 * s)
        pen.setStyle(Qt.PenStyle.CustomDashLine)
        pen.setDashPattern([6, 3])
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(c, c), 38 * s, 38 * s)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(c, c), 12 * s, 12 * s)


class HomeDashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        t = get_theme()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        h = QHBoxLayout()
        h.addWidget(DashboardLogo(50))
        tl = QVBoxLayout()
        tl.addWidget(
            QLabel(
                "Genel Bakış",
                styleSheet=f"font-size: 26px; font-weight: bold; color: {t.text_primary};",
            )
        )
        tl.addWidget(
            QLabel(
                datetime.now().strftime("%d %B %Y, %A"),
                styleSheet=f"font-size: 14px; color: {t.text_muted};",
            )
        )
        h.addLayout(tl)
        h.addStretch()

        btn_new_order = QPushButton("Yeni Sipariş")
        if "qta" in globals():
            btn_new_order.setIcon(qta.icon("fa5s.plus", color="white"))
        btn_new_order.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_new_order.setStyleSheet(
            f"background-color: {t.success}; color: white; border-radius: 6px; padding: 8px 15px; font-weight: 600;"
        )
        btn_new_order.clicked.connect(
            lambda: self.window().show_notification(
                "Sipariş başarıyla oluşturuldu!", "SUCCESS"
            )
        )
        h.addWidget(btn_new_order)

        btn_stock_in = QPushButton("Stok Girişi")
        if "qta" in globals():
            btn_stock_in.setIcon(qta.icon("fa5s.box-open", color="white"))
        btn_stock_in.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_stock_in.setStyleSheet(
            f"background-color: {t.accent_primary}; color: white; border-radius: 6px; padding: 8px 15px; font-weight: 600;"
        )
        btn_stock_in.clicked.connect(
            lambda: self.window().show_notification(
                "Dikkat: Depo kapasitesi %90 dolu!", "WARNING"
            )
        )
        h.addWidget(btn_stock_in)

        layout.addLayout(h)

        kl = QHBoxLayout()
        kl.setSpacing(20)
        kpis = [
            (
                "Toplam Ciro",
                "₺ 482.5K",
                "▲ %12",
                "fa5s.chart-line",
                t.accent_primary,
                [10, 25, 15, 30, 40, 35, 50, 45, 60],
            ),
            (
                "İş Emirleri",
                "24 Adet",
                "▼ 2 gecikme",
                "fa5s.cogs",
                t.accent_secondary,
                [5, 8, 6, 9, 12, 10, 15],
            ),
            (
                "Stok Değeri",
                "₺ 1.2M",
                "● 5 kritik",
                "fa5s.warehouse",
                t.warning,
                [20, 20, 21, 22, 21, 23, 22],
            ),
            (
                "Borçlar",
                "₺ 45K",
                "■ 3 gün vade",
                "fa5s.file-invoice-dollar",
                t.error,
                [10, 5, 8, 3, 2, 10, 5],
            ),
        ]
        for k in kpis:
            kl.addWidget(KPICard(*k))
        layout.addLayout(kl)

        ml = QHBoxLayout()
        tf = QFrame()
        tf.setStyleSheet(
            f"background-color: {t.card_bg}; border-radius: {t.radius_large}px; border: 1px solid {t.border};"
        )
        tfl = QVBoxLayout(tf)
        tfl.addWidget(
            QLabel(
                "Son Hareketler",
                styleSheet=f"font-size:16px; font-weight:bold; color:{t.text_primary}; border:none;",
            )
        )
        hr = QHBoxLayout()
        for head in ["Kod", "İşlem", "Miktar", "Tarih", "Durum"]:
            hr.addWidget(
                QLabel(
                    head,
                    styleSheet=f"color:{t.text_muted}; font-weight:bold; border:none;",
                )
            )
        tfl.addLayout(hr)
        for c, o, q, tm, s, clr in [
            ("STK-001", "Satınalma", "+500", "10:42", "Tamamlandı", t.success),
            ("PRD-202", "Üretim", "-120", "09:15", "Tamamlandı", t.success),
        ]:
            r = QFrame()
            rl = QHBoxLayout(r)
            rl.setContentsMargins(0, 5, 0, 5)
            r.setStyleSheet(
                f"border-bottom: 1px solid {t.border}; border-radius:0; background:transparent;"
            )
            for i, txt in enumerate([c, o, q, tm, s]):
                st = f"color:{t.text_primary}; border:none;"
                if i == 4:
                    st = f"color:{clr}; font-weight:bold; border:none;"
                rl.addWidget(QLabel(txt, styleSheet=st))
            tfl.addWidget(r)
        tfl.addStretch()
        ml.addWidget(tf, 2)

        tsk = QFrame()
        tsk.setStyleSheet(
            f"background-color: {t.card_bg}; border-radius: {t.radius_large}px; border: 1px solid {t.border};"
        )
        tskl = QVBoxLayout(tsk)
        tskl.addWidget(
            QLabel(
                "İş Takibi",
                styleSheet=f"font-size:16px; font-weight:bold; color:{t.text_primary}; border:none;",
            )
        )
        for tt, td, tc in [
            ("KDV Ödemesi", "Yarın", t.error),
            ("Maaşlar", "Ayın 1'i", t.info),
        ]:
            tskl.addWidget(TaskItem(tt, td, tc))
        tskl.addStretch()
        ml.addWidget(tsk, 1)
        layout.addLayout(ml)
        layout.addStretch()
        scroll.setWidget(container)
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.addWidget(scroll)


# --- MENÜ VERİSİ ---
MENU_DATA = {
    "dashboard": {
        "title": "GENEL BAKIŞ",
        "items": [("Dashboard", "fa5s.home", "dashboard")],
    },
    "inventory": {
        "title": "STOK YÖNETİMİ",
        "items": [
            ("Stok Kartları", "fa5s.box", "stock-cards"),
            ("Kategoriler", "fa5s.tags", "categories"),
            ("Birimler", "fa5s.ruler", "units"),
            ("Depolar", "fa5s.warehouse", "warehouses"),
            ("Hareketler", "fa5s.exchange-alt", "movements"),
            ("Sayım İşlemleri", "fa5s.clipboard-list", "stock-count"),
            ("Raporlar", "fa5s.chart-bar", "stock-reports"),
        ],
    },
    "purchasing": {
        "title": "SATINALMA",
        "items": [
            ("Tedarikçiler", "fa5s.truck", "suppliers"),
            ("Talepler", "fa5s.file-signature", "purchase-requests"),
            ("Siparişler", "fa5s.file-invoice-dollar", "purchase-orders"),
            ("Mal Kabul", "fa5s.dolly", "goods-receipts"),
            ("Faturalar", "fa5s.file-alt", "purchase-invoices"),
        ],
    },
    "production": {
        "title": "ÜRETİM",
        "items": [
            ("İş Emirleri", "fa5s.clipboard-check", "work-orders"),
            ("Ürün Reçeteleri", "fa5s.scroll", "bom"),
            ("Planlama", "fa5s.calendar-alt", "planning"),
            ("İş İstasyonları", "fa5s.cogs", "work-stations"),
            ("Takvim", "fa5s.calendar-day", "calendar"),
            ("MRP", "fa5s.project-diagram", "mrp"),
        ],
    },
    "sales": {
        "title": "SATIŞ",
        "items": [
            ("Müşteriler", "fa5s.users", "customers"),
            ("Teklifler", "fa5s.file-invoice", "sales-quotes"),
            ("Siparişler", "fa5s.shopping-cart", "sales-orders"),
            ("İrsaliyeler", "fa5s.truck", "delivery-notes"),
            ("Faturalar", "fa5s.file-invoice-dollar", "invoices"),
            ("Fiyat Listeleri", "fa5s.list-alt", "price-lists"),
        ],
    },
    "accounting": {
        "title": "MUHASEBE",
        "items": [
            ("Hesap Planı", "fa5s.sitemap", "accounts"),
            ("Yevmiye Fişleri", "fa5s.book", "journals"),
            ("Muhasebe Raporları", "fa5s.file-alt", "accounting-reports"),
        ],
    },
    "finance": {
        "title": "FİNANS",
        "items": [
            ("Tahsilatlar", "fa5s.hand-holding-usd", "receipts"),
            ("Ödemeler", "fa5s.money-check-alt", "payments"),
            ("Mutabakat", "fa5s.balance-scale", "reconciliation"),
            ("Cari Hesaplar", "fa5s.address-book", "account-statements"),
        ],
    },
    "reports": {
        "title": "RAPORLAR",
        "items": [
            ("Satış Raporları", "fa5s.chart-line", "sales-reports"),
            ("Stok Yaşlandırma", "fa5s.boxes", "stock-aging"),
            ("Üretim OEE", "fa5s.tachometer-alt", "production-oee"),
            ("Tedarikçi Performans", "fa5s.industry", "supplier-performance"),
            ("Alacak Yaşlandırma", "fa5s.credit-card", "receivables-aging"),
        ],
    },
    "development": {
        "title": "GELİŞTİRME",
        "items": [
            ("Hata Kayıtları", "fa5s.bug", "error-logs"),
        ],
    },
    "settings": {
        "title": "SİSTEM AYARLARI",
        "items": [
            ("Genel Ayarlar", "fa5s.sliders-h", "settings"),
        ],
    },
    "hr": {
        "title": "İNSAN KAYNAKLARI",
        "items": [
            ("Çalışanlar", "fa5s.user-tie", "employees"),
            ("Departmanlar", "fa5s.building", "departments"),
            ("Pozisyonlar", "fa5s.id-badge", "positions"),
            ("İzin Yönetimi", "fa5s.calendar-check", "leaves"),
            ("Organizasyon", "fa5s.sitemap", "org-chart"),
            ("Vardiya Ekipleri", "fa5s.users-cog", "shift-teams"),
        ],
    },
}

# --- BİLEŞENLER ---


class CustomTitleBar(QFrame):
    """Özelleştirilmiş Başlık Çubuğu - Örnek 1 Tasarımı"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(38)
        self.setObjectName("TitleBar")
        self.setStyleSheet(
            """
            #TitleBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2d2d30, stop:1 #1e1e1e);
                border-bottom: 1px solid #3e3e42;
            }
        """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(12)

        # === SOL: Logo ve Uygulama Adı ===
        self.btn_toggle = QPushButton()
        self.btn_toggle.setObjectName("BtnToggle")
        logo_path = os.path.join(current_dir, "resources", "icons", "logo.svg")
        if os.path.exists(logo_path):
            self.btn_toggle.setIcon(QIcon(logo_path))
        elif "qta" in globals():
            self.btn_toggle.setIcon(qta.icon("fa5s.cube", color="#007acc"))
        self.btn_toggle.setIconSize(QSize(24, 24))
        self.btn_toggle.setFixedSize(32, 32)
        self.btn_toggle.setCheckable(True)
        self.btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
            }
        """
        )
        layout.addWidget(self.btn_toggle)

        self.title_label = QLabel("Akıllı İş ERP")
        self.title_label.setStyleSheet(
            """
            font-weight: 600;
            font-size: 14px;
            color: #ffffff;
            border: none;
            background: transparent;
        """
        )
        layout.addWidget(self.title_label)

        layout.addStretch()  # Sol stretch

        # === ORTA: Arama Kutusu (Kompakt, Ortalı) ===
        search_container = QFrame()
        search_container.setFixedHeight(22)
        search_container.setFixedWidth(100)
        search_container.setStyleSheet(
            """
            QFrame {
                background: #3c3c3c;
                border: 1px solid #4a4a4a;
                border-radius: 11px;
            }
            QFrame:focus-within {
                border-color: #007acc;
            }
        """
        )
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(3)
        search_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("border: none; font-size: 10px;")
        search_layout.addWidget(search_icon)

        search_text = QLabel("Ara")
        search_text.setStyleSheet("border: none; font-size: 10px; color: #808080;")
        search_layout.addWidget(search_text)

        layout.addWidget(search_container)

        layout.addStretch()  # Sağ stretch

        # === SAĞ: macOS Tarzı Pencere Butonları ===
        btn_container = QWidget()
        btn_container.setStyleSheet("background: transparent;")
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(8)

        # Yeşil (minimize)
        self.btn_min = QPushButton()
        self.btn_min.setFixedSize(14, 14)
        self.btn_min.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_min.setStyleSheet(
            """
            QPushButton {
                background: #28c840;
                border: none;
                border-radius: 7px;
            }
            QPushButton:hover {
                background: #3dd654;
            }
        """
        )

        # Sarı (maximize)
        self.btn_max = QPushButton()
        self.btn_max.setFixedSize(14, 14)
        self.btn_max.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_max.setStyleSheet(
            """
            QPushButton {
                background: #febc2e;
                border: none;
                border-radius: 7px;
            }
            QPushButton:hover {
                background: #ffc944;
            }
        """
        )

        # Kırmızı (close)
        self.btn_close = QPushButton()
        self.btn_close.setFixedSize(14, 14)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setStyleSheet(
            """
            QPushButton {
                background: #ff5f57;
                border: none;
                border-radius: 7px;
            }
            QPushButton:hover {
                background: #ff7369;
            }
        """
        )

        btn_layout.addWidget(self.btn_min)
        btn_layout.addWidget(self.btn_max)
        btn_layout.addWidget(self.btn_close)
        layout.addWidget(btn_container)

        # Sinyaller
        self.btn_close.clicked.connect(self.parent.close)
        self.btn_min.clicked.connect(self.parent.showMinimized)
        self.btn_max.clicked.connect(self.toggle_max)

        # Sürükleme için
        self.start = QPoint(0, 0)
        self.pressing = False

    def update_module_indicator(self, module: str, page: str = ""):
        """Geriye uyumluluk için (artık görsel yok)"""
        pass

    def toggle_max(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
        else:
            self.parent.showMaximized()

    def mousePressEvent(self, e):
        self.start = self.mapToGlobal(e.pos())
        self.pressing = True

    def mouseMoveEvent(self, e):
        if self.pressing and not self.parent.isMaximized():
            self.end = self.mapToGlobal(e.pos())
            self.parent.move(self.parent.pos() + self.end - self.start)
            self.start = self.end

    def mouseReleaseEvent(self, e):
        self.pressing = False


class ActivityBar(QFrame):
    moduleSelected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ActivityBar")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(8)
        for key, icon, tip in [
            ("dashboard", "fa5s.home", "Genel Bakış"),
            ("inventory", "fa5s.boxes", "Stok"),
            ("purchasing", "fa5s.shopping-cart", "Satınalma"),
            ("sales", "fa5s.cash-register", "Satış"),
            ("production", "fa5s.industry", "Üretim"),
            ("accounting", "fa5s.calculator", "Muhasebe"),
            ("finance", "fa5s.wallet", "Finans"),
            ("hr", "fa5s.users", "İnsan Kaynakları"),
            ("reports", "fa5s.chart-pie", "Raporlar"),
            ("development", "fa5s.bug", "Geliştirme"),
            ("settings", "fa5s.cog", "Ayarlar"),
        ]:
            btn = QPushButton()
            if "qta" in globals():
                btn.setIcon(qta.icon(icon, color="#858585"))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(tip)
            btn.setIconSize(QSize(22, 22))
            btn.clicked.connect(lambda checked, k=key: self.moduleSelected.emit(k))
            layout.addWidget(btn)
        layout.addStretch()
        btn_user = QPushButton()
        if "qta" in globals():
            btn_user.setIcon(qta.icon("fa5s.user-circle", color="#858585"))
        btn_user.setIconSize(QSize(22, 22))
        layout.addWidget(btn_user)


class SideBar(QFrame):
    pageSelected = pyqtSignal(str)
    closeRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SideBar")
        self.setFixedWidth(220)
        self.is_locked = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.lbl_title = QLabel("MODÜL")
        self.lbl_title.setStyleSheet(
            "padding: 10px; font-weight: bold; color: #bbbbbb; border-bottom: 1px solid #3e3e42; font-size: 11px;"
        )
        layout.addWidget(self.lbl_title)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(15)
        self.tree.setIconSize(QSize(14, 14))
        self.tree.setStyleSheet("border: none;")
        self.tree.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.tree)

    def load_menu(self, key):
        self.tree.clear()
        data = MENU_DATA.get(key)
        if not data:
            return
        self.lbl_title.setText(data["title"])
        font = self.tree.font()
        font.setPointSize(10)
        for name, icon, page_id in data["items"]:
            item = QTreeWidgetItem(self.tree)
            item.setText(0, name)
            item.setData(0, Qt.ItemDataRole.UserRole, page_id)
            item.setFont(0, font)
            if "qta" in globals():
                item.setIcon(0, qta.icon(icon, color="#cccccc"))

    def load_all_menus(self):
        self.tree.clear()
        self.lbl_title.setText("ANA MENÜ")
        fh = self.tree.font()
        fh.setPointSize(10)
        fh.setBold(True)
        fi = self.tree.font()
        fi.setPointSize(10)
        for key, data in MENU_DATA.items():
            p = QTreeWidgetItem(self.tree)
            p.setText(0, data["title"])
            p.setFont(0, fh)
            if "qta" in globals():
                p.setIcon(0, qta.icon("fa5s.folder", color="#888888"))
            for name, icon, page_id in data["items"]:
                c = QTreeWidgetItem(p)
                c.setText(0, name)
                c.setData(0, Qt.ItemDataRole.UserRole, page_id)
                c.setFont(0, fi)
                if "qta" in globals():
                    c.setIcon(0, qta.icon(icon, color="#cccccc"))
            p.setExpanded(True)

    def on_item_clicked(self, item, col):
        pid = item.data(0, Qt.ItemDataRole.UserRole)
        if pid:
            self.pageSelected.emit(pid)

    def leaveEvent(self, e):
        if not self.is_locked:
            self.closeRequested.emit()
        super().leaveEvent(e)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        # Mock user for development (TODO: Replace with actual login)
        self._setup_mock_user()

        self.setup_window()
        self.setup_pages_dict()
        self.setup_ui()
        self.connect_signals()
        self._apply_theme()
        ThemeManager.register_callback(self._on_theme_changed)

    def _setup_mock_user(self):
        """Setup mock user for ErrorHandler (geçici)"""
        try:
            from modules.development import ErrorHandler
            from database.models.user import User
            from database.base import get_session

            # Admin kullanıcıyı al veya oluştur
            session = get_session()
            user = session.query(User).filter(User.username == "admin").first()

            if user:
                ErrorHandler.set_current_user(user)

            session.close()
        except Exception as e:
            print(f"Warning: Could not setup ErrorHandler user: {e}")

    def setup_window(self):
        self.setWindowTitle(f"{APP_NAME} - {APP_DESCRIPTION}")
        self.resize(1280, 800)
        screen = self.screen().availableGeometry()
        self.move(
            (screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2
        )

    def setup_pages_dict(self):
        self.pages = {}
        self.pages["dashboard"] = HomeDashboard()
        # Stok modülü sayfaları
        self.pages["stock-cards"] = InventoryModule()
        self.pages["categories"] = CategoryModule()
        self.pages["units"] = UnitModule()
        self.pages["warehouses"] = WarehouseModule()
        self.pages["movements"] = MovementModule()
        self.pages["stock-count"] = StockCountModule()
        self.pages["stock-reports"] = StockReportsModule()
        # Üretim modülü sayfaları
        self.pages["work-orders"] = WorkOrderModule()
        self.pages["bom"] = BOMModule()
        self.pages["planning"] = PlanningModule()
        self.pages["work-stations"] = WorkStationModule()
        self.pages["calendar"] = CalendarModule()
        self.pages["mrp"] = MRPModule()
        # Satınalma modülü sayfaları
        self.pages["suppliers"] = SupplierModule()
        self.pages["purchase-requests"] = PurchaseRequestModule()
        self.pages["goods-receipts"] = GoodsReceiptModule()
        self.pages["purchase-orders"] = PurchaseOrderModule()
        self.pages["purchase-invoices"] = PurchaseInvoiceModule()
        # Satış modülü sayfaları
        self.pages["customers"] = CustomerModule()
        self.pages["sales-quotes"] = SalesQuoteModule()
        self.pages["sales-orders"] = SalesOrderModule()
        self.pages["delivery-notes"] = DeliveryNoteModule()
        self.pages["invoices"] = InvoiceModule()
        self.pages["price-lists"] = PriceListModule()
        # Muhasebe modülü sayfaları
        self.pages["accounts"] = AccountModule()
        self.pages["journals"] = JournalModule()
        self.pages["accounting-reports"] = AccountingReportsModule()
        # Finans modülü sayfaları
        self.pages["receipts"] = ReceiptModule()
        self.pages["payments"] = PaymentModule()
        self.pages["reconciliation"] = ReconciliationModule()
        self.pages["account-statements"] = AccountStatementModule()
        # Raporlar modulu sayfalari
        self.pages["sales-reports"] = SalesReportsModule()
        self.pages["stock-aging"] = StockAgingModule()
        self.pages["production-oee"] = ProductionOEEModule()
        self.pages["supplier-performance"] = SupplierPerformanceModule()
        self.pages["receivables-aging"] = ReceivablesAgingModule()
        # Geliştirme modülü
        self.pages["error-logs"] = DevelopmentModule()
        # İnsan Kaynakları modülü
        self.pages["employees"] = EmployeeModule()
        self.pages["departments"] = DepartmentModule()
        self.pages["positions"] = PositionModule()
        self.pages["leaves"] = LeaveModule()
        self.pages["org-chart"] = OrgChartModule()
        self.pages["shift-teams"] = ShiftTeamOverview()
        # Sistem ayarları
        self.pages["settings"] = PlaceholderPage("Ayarlar", "")

    def setup_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)
        root = QVBoxLayout(central_widget)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.title_bar = CustomTitleBar(self)
        root.addWidget(self.title_bar)

        body = QHBoxLayout()
        body.setSpacing(0)
        self.activity_bar = ActivityBar()
        body.addWidget(self.activity_bar)

        # Sidebar için Container - Fixed genişlik yerine animasyonla yönetiliyor ama
        # Yanındaki content sıkışsın diye Policy ayarı önemli.
        self.sidebar_container = QWidget()
        self.sidebar_container.setMaximumWidth(0)
        self.sidebar_container.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred
        )

        sidebar_lay = QVBoxLayout(self.sidebar_container)
        sidebar_lay.setContentsMargins(0, 0, 0, 0)
        self.sidebar = SideBar()
        sidebar_lay.addWidget(self.sidebar)
        body.addWidget(self.sidebar_container)

        content = QWidget()
        c_lay = QVBoxLayout(content)
        c_lay.setContentsMargins(0, 0, 0, 0)
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)
        # İçerik alanı (Tabs) sıkışabilir olmalı
        self.tabs.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        # Minimum genişlik küçük tutulmalı ki pencereyi genişletmeye zorlamasın
        self.tabs.setMinimumWidth(100)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.open_tab("dashboard")
        c_lay.addWidget(self.tabs)
        body.addWidget(content)
        root.addLayout(body)

        # === STATUSBAR - Örnek 1 Tasarımı ===
        self.status_bar = QStatusBar()
        self.status_bar.setFixedHeight(28)
        self.status_bar.setStyleSheet(
            """
            QStatusBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #252526, stop:1 #1e1e1e);
                border-top: 1px solid #3e3e42;
            }
            QStatusBar::item { border: none; }
            QLabel {
                color: #808080;
                font-size: 11px;
                padding: 0 6px;
                border: none;
                background: transparent;
            }
        """
        )
        self.setStatusBar(self.status_bar)

        # === SOL: Kullanıcı Bilgisi ===
        # Avatar
        avatar_label = QLabel("👤")
        avatar_label.setStyleSheet(
            """
            font-size: 14px;
            padding: 2px 4px;
            background: #3c3c3c;
            border-radius: 4px;
        """
        )
        self.status_bar.addWidget(avatar_label)

        # Kullanıcı adı
        self.status_user_name = QLabel("Ahmet Yılmaz")
        self.status_user_name.setStyleSheet("color: #cccccc; font-weight: 500;")
        self.status_bar.addWidget(self.status_user_name)

        # Rol badge
        self.status_role_badge = QLabel("Yönetici")
        self.status_role_badge.setStyleSheet(
            """
            background: #007acc;
            color: white;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: bold;
        """
        )
        self.status_bar.addWidget(self.status_role_badge)

        # Ayırıcı
        separator1 = QLabel("|")
        separator1.setStyleSheet("color: #3e3e42; padding: 0 8px;")
        self.status_bar.addWidget(separator1)

        # === ORTA: Aktif Modül ===
        self.status_module = QLabel("📊 Aktif Modül: Dashboard")
        self.status_module.setStyleSheet("color: #808080;")
        self.status_bar.addWidget(self.status_module)

        # === SAĞ: Durum Bilgileri ===
        # Bağlantı durumu
        self.status_connection = QLabel("● Çevrimiçi")
        self.status_connection.setStyleSheet("color: #4ec9b0;")
        self.status_bar.addPermanentWidget(self.status_connection)

        # Sync durumu
        self.status_sync = QLabel("↻ Veritabanı Eşitleniyor...")
        self.status_sync.setStyleSheet("color: #808080;")
        self.status_bar.addPermanentWidget(self.status_sync)

        # Tarih/Saat
        from datetime import datetime

        now = datetime.now()
        date_str = (
            now.strftime("%d %B %Y %H:%M")
            .replace("January", "Ocak")
            .replace("February", "Şubat")
            .replace("March", "Mart")
            .replace("April", "Nisan")
            .replace("May", "Mayıs")
            .replace("June", "Haziran")
            .replace("July", "Temmuz")
            .replace("August", "Ağustos")
            .replace("September", "Eylül")
            .replace("October", "Ekim")
            .replace("November", "Kasım")
            .replace("December", "Aralık")
        )
        self.status_datetime = QLabel(date_str)
        self.status_datetime.setStyleSheet("color: #808080;")
        self.status_bar.addPermanentWidget(self.status_datetime)

        # Bildirim ikonu
        self.status_notification = QLabel("🔔")
        self.status_notification.setStyleSheet(
            """
            font-size: 14px;
            padding: 2px 8px;
            background: transparent;
        """
        )
        self.status_bar.addPermanentWidget(self.status_notification)

        QSizeGrip(self.status_bar)

        self.anim = QPropertyAnimation(self.sidebar_container, b"maximumWidth")
        self.anim.setDuration(200)
        self.anim.setEasingCurve(QEasingCurve.Type.OutQuad)

    def connect_signals(self):
        self.activity_bar.moduleSelected.connect(self.open_menu)
        self.sidebar.pageSelected.connect(self.open_tab)
        self.sidebar.closeRequested.connect(self.close_menu_if_not_locked)
        self.title_bar.btn_toggle.toggled.connect(self.toggle_sidebar_lock)

    def _on_theme_changed(self, theme):
        self._apply_theme()

    def _apply_theme(self):
        t = get_theme()
        self.setStyleSheet(
            f"""
        QMainWindow, #CentralWidget {{ background-color: {t.bg_primary}; }}
        QWidget {{ color: #cccccc; font-family: 'Segoe UI', sans-serif; font-size: 13px; }}
        
        #TitleBar {{ background-color: #3c3c3c; border-bottom: 1px solid #3e3e42; }}
        #SearchInput {{ background-color: #252526; border: 1px solid #3e3e42; border-radius: 3px; color: #cccccc; padding: 1px 10px; height: 22px; }}
        #SearchInput:focus {{ border: 1px solid #007acc; background-color: #3c3c3c; }}
        QPushButton#BtnClose:hover {{ background-color: #e81123; color: white; }}
        QPushButton#BtnMaximize:hover, QPushButton#BtnMinimize:hover {{ background-color: #4c4c4c; }}
        
        QPushButton#BtnToggle {{ background: transparent; border: none; }}
        QPushButton#BtnToggle:checked {{ background-color: #333333; }}
        
        #ActivityBar {{ background-color: #333333; border-right: 1px solid #252526; min-width: 50px; max-width: 50px; }}
        #ActivityBar QPushButton {{ border: none; background-color: transparent; padding: 10px; border-left: 2px solid transparent; }}
        #ActivityBar QPushButton:hover {{ background-color: #2a2d2e; }}
        #ActivityBar QPushButton:pressed {{ border-left: 2px solid #007acc; background-color: #1e1e1e; }}
        
        #SideBar {{ background-color: #252526; border-right: 1px solid #3e3e42; }}
        QTreeWidget {{ background-color: #252526; border: none; outline: none; }}
        QTreeWidget::item {{ padding: 6px; color: #cccccc; border: none; }}
        QTreeWidget::item:hover {{ background-color: #2a2d2e; }}
        QTreeWidget::item:selected {{ background-color: #37373d; color: white; border-left: 2px solid #007acc; }}
        
        QTabWidget::pane {{ border: none; background-color: #1e1e1e; border-top: 1px solid #3e3e42; }}
        QTabBar::tab {{ background: #2d2d2d; color: #969696; padding: 6px 15px; border-right: 1px solid #252526; border-top: 1px solid transparent; min-width: 100px; height: 20px; }}
        QTabBar::tab:selected {{ background: #1e1e1e; color: white; border-top: 1px solid #007acc; }}
        QTabBar::tab:hover {{ background: #2d2d2d; color: white; }}
        QTabBar::close-button {{ width: 0px; height: 0px; }}
        QTabBar::close-button:selected {{ width: 16px; height: 16px; margin-left: 5px; }}
        
        QStatusBar {{ background-color: #5e3b8e; color: white; border-top: 1px solid #3e3e42; min-height: 22px; }}
        QStatusBar QLabel {{ background: transparent; font-size: 11px; }}
        """
        )

    def show_notification(self, message: str, level: str = "INFO"):
        t = get_theme()
        colors = {
            "INFO": t.accent_primary,
            "SUCCESS": t.success,
            "WARNING": t.warning,
            "ERROR": t.error,
        }
        bg_color = colors.get(level, t.accent_primary)
        text_color = "white" if level != "WARNING" else "black"
        self.status_bar.setStyleSheet(
            f"QStatusBar {{ background-color: {bg_color}; color: {text_color}; border-top: 1px solid {t.border}; font-weight: bold; min-height: 22px; }}"
        )
        icons = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "⛔"}
        self.status_bar.showMessage(f"  {icons.get(level, '')}  {message}")
        QTimer.singleShot(3000, self._reset_statusbar)

    def _reset_statusbar(self):
        self.status_bar.clearMessage()
        t = get_theme()
        self.status_bar.setStyleSheet(
            f"QStatusBar {{ background-color: #5e3b8e; color: white; border-top: 1px solid #3e3e42; min-height: 22px; }}"
        )
        self.status_bar.showMessage(" Hazır")

    def toggle_sidebar_lock(self, checked):
        self.sidebar.is_locked = checked
        if checked:
            self.sidebar.load_all_menus()
            self._animate_sidebar(True)
        else:
            self._animate_sidebar(False)

    def open_menu(self, module_key):
        self.sidebar.load_menu(module_key)
        if not self.sidebar.is_locked:
            self._animate_sidebar(True)

    def close_menu_if_not_locked(self):
        if not self.sidebar.is_locked:
            self._animate_sidebar(False)

    def _animate_sidebar(self, open_sidebar):
        width = 220 if open_sidebar else 0
        if self.sidebar_container.width() != width:
            self.anim.stop()
            self.anim.setStartValue(self.sidebar_container.width())
            self.anim.setEndValue(width)
            self.anim.start()

    def open_tab(self, page_id):
        page_widget = self.pages.get(page_id)
        if not page_widget:
            return
        for i in range(self.tabs.count()):
            if self.tabs.widget(i) == page_widget:
                self.tabs.setCurrentIndex(i)
                return

        title = page_id.title()
        icon = QIcon()
        for grp in MENU_DATA.values():
            for name, icon_name, pid in grp["items"]:
                if pid == page_id:
                    title = name
                    if "qta" in globals():
                        icon = qta.icon(icon_name, color="#cccccc")
                    break
        self.tabs.addTab(page_widget, icon, title)
        self.tabs.setCurrentWidget(page_widget)

    def close_tab(self, index):
        self.tabs.removeTab(index)

    def go_prev_tab(self):
        if (i := self.tabs.currentIndex()) > 0:
            self.tabs.setCurrentIndex(i - 1)

    def go_next_tab(self):
        if (i := self.tabs.currentIndex()) < self.tabs.count() - 1:
            self.tabs.setCurrentIndex(i + 1)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
