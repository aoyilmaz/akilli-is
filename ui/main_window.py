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
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTabWidget,
    QStatusBar,
    QSizePolicy,
    QTreeWidget,
    QTreeWidgetItem,
    QTreeWidgetItemIterator,
    QSizeGrip,
    QScrollArea,
    QFrame,
    QLineEdit,
    QAbstractItemView,
    QStackedWidget,
)

from PyQt6.QtCore import (
    Qt,
    pyqtSignal,
    QPointF,
    QSize,
)

from PyQt6.QtGui import (
    QIcon,
    QFont,
    QColor,
    QPainter,
    QPainterPath,
    QPen,
    QBrush,
    QLinearGradient,
    QPixmap,
)

try:
    import qtawesome as qta
except ImportError:
    pass

from config import APP_NAME, APP_DESCRIPTION
from config.themes import ThemeManager, get_theme
from config.menu_data import MENU_DATA

# --- IMPORTLAR ---
from ui.pages.placeholder import PlaceholderPage
from ui.pages.dashboard import DashboardPage
from ui.components.toast import show_toast
from ui.components.empty_state import EmptyStateWidget


class MissingModule(PlaceholderPage):
    """Eksik bağımlılık durumunda kullanılacak sarmalayıcı sınıf"""

    def __init__(self, parent=None):
        super().__init__("Modül Yüklenemedi", "⚠️", parent)


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
        LocationManagementPage,
        WarehouseOperatorPage,
        SSCCModule,  # Added SSCCModule to imports
    )
except ImportError:
    InventoryModule = WarehouseModule = MovementModule = CategoryModule = (
        StockReportsModule
    ) = StockCountModule = UnitModule = LocationManagementPage = (
        WarehouseOperatorPage
    ) = SSCCModule = MissingModule

try:
    from modules.production import (
        BOMModule,
        WorkOrderModule,
        PlanningModule,
        WorkStationModule,
    )
    from modules.production.views.calendar_module import CalendarModule
    from modules.production.views.operator_panel import OperatorPanel
except ImportError:
    BOMModule = WorkOrderModule = PlanningModule = WorkStationModule = (
        CalendarModule
    ) = OperatorPanel = MissingModule

try:
    from modules.purchasing import (
        SupplierModule,
        PurchaseRequestModule,
        GoodsReceiptModule,
        PurchaseOrderModule,
    )
    from modules.rfq.views.rfq_module import RFQModule
except ImportError:
    SupplierModule = PurchaseRequestModule = GoodsReceiptModule = (
        PurchaseOrderModule
    ) = RFQModule = MissingModule

try:
    from modules.development.views import DevelopmentModule, ThemeSettingsPage
    from modules.development.views.company_card import CompanyCard
except ImportError:
    DevelopmentModule = CompanyCard = ThemeSettingsPage = MissingModule

try:
    from modules.system import UserManagement, LabelTemplatesPage, AuditLogViewer
except ImportError:
    UserManagement = LabelTemplatesPage = AuditLogViewer = MissingModule

try:
    from modules.crm.views import CRMModule, OpportunityModule, ActivityModule
except ImportError:
    CRMModule = MissingModule
    OpportunityModule = MissingModule
    ActivityModule = MissingModule

try:
    from modules.sales import (
        CustomerModule,
        SalesQuoteModule,
        SalesOrderModule,
        DeliveryNoteModule,
        InvoiceModule,
    )
    from modules.sales.views.price_list_module import PriceListModule
    from modules.returns.views.return_module import ReturnModule
    from modules.contracts.views.contract_module import ContractModule
except ImportError:
    CustomerModule = SalesQuoteModule = SalesOrderModule = DeliveryNoteModule = (
        InvoiceModule
    ) = PriceListModule = ReturnModule = ContractModule = MissingModule

try:
    from modules.purchasing.views.purchase_invoice_module import PurchaseInvoiceModule
except ImportError:
    PurchaseInvoiceModule = MissingModule

try:
    from modules.einvoice import EInvoiceModule
except ImportError:
    EInvoiceModule = MissingModule

try:
    from modules.accounting.views.account_module import AccountModule
    from modules.accounting.views.journal_module import JournalModule
    from modules.accounting.views.reports_module import AccountingReportsModule
    from modules.accounting.views.budget_module import BudgetModule
except ImportError:
    AccountModule = JournalModule = AccountingReportsModule = BudgetModule = (
        MissingModule
    )

try:
    from modules.fixed_assets import FixedAssetModule
except ImportError:
    FixedAssetModule = MissingModule

try:
    from modules.finance.views.receipt_module import ReceiptModule
    from modules.finance.views.payment_module import PaymentModule
    from modules.finance.views.reconciliation_module import ReconciliationModule
    from modules.finance.views.account_statement_module import AccountStatementModule
except ImportError:
    ReceiptModule = PaymentModule = ReconciliationModule = AccountStatementModule = (
        MissingModule
    )

try:
    from modules.mrp.views.mrp_module import MRPModule
except ImportError:
    MRPModule = MissingModule

try:
    from modules.planning.views.mps_cockpit import MPSCockpitPage
    from modules.planning.views.plan_list import MPSPlanListPage
    from modules.planning.views.capacity_page import CapacityAnalysisPage
except ImportError:
    MPSCockpitPage = MPSPlanListPage = CapacityAnalysisPage = MissingModule

try:
    from modules.reports.views.sales_reports_module import SalesReportsModule
    from modules.reports.views.stock_aging_module import StockAgingModule
    from modules.reports.views.production_oee_module import ProductionOEEModule
    from modules.reports.views.supplier_performance_module import (
        SupplierPerformanceModule,
    )
    from modules.reports.views.receivables_aging_module import ReceivablesAgingModule
    from modules.reports.views.oee_monitoring_module import OEEMonitoringModule
except ImportError:
    SalesReportsModule = StockAgingModule = ProductionOEEModule = (
        SupplierPerformanceModule
    ) = ReceivablesAgingModule = OEEMonitoringModule = MissingModule

try:
    from modules.hr.views.employee_module import EmployeeModule
    from modules.hr.views.department_module import DepartmentModule
    from modules.hr.views.position_module import PositionModule
    from modules.hr.views.leave_module import LeaveModule
    from modules.hr.views.org_chart_module import OrgChartModule
    from modules.hr.views.shift_team_overview import ShiftTeamOverview
    from modules.hr.views.attendance_module import AttendanceModule
    from modules.hr.views.performance_module import PerformanceModule
    from modules.hr.views.training_module import TrainingModule
    from modules.hr.views.personnel_module import PersonnelModule
    from modules.hr.views.hr_dashboard_module import HRDashboardModule
    from modules.hr.views.shift_planning_module import ShiftPlanningModule
    from modules.hr.views.recruitment_module import RecruitmentModule
except ImportError:
    EmployeeModule = DepartmentModule = PositionModule = LeaveModule = MissingModule
    OrgChartModule = ShiftTeamOverview = AttendanceModule = MissingModule
    PerformanceModule = TrainingModule = PersonnelModule = MissingModule
    HRDashboardModule = ShiftPlanningModule = RecruitmentModule = MissingModule

try:
    from modules.maintenance.views import (
        EquipmentListWidget,
        MaintenanceRequestWidget,
        WorkOrderManagerWidget,
        MaintenancePlanWidget,
        ReportingWidget,
    )
except ImportError:
    EquipmentListWidget = MaintenanceRequestWidget = WorkOrderManagerWidget = (
        MaintenancePlanWidget
    ) = ReportingWidget = MissingModule

try:
    from modules.shipping import ShippingMainModule, FleetMainModule
except ImportError:
    ShippingMainModule = FleetMainModule = MissingModule

try:
    from modules.quality.views import (
        InspectionModule,
        NCRModule,
        ComplaintModule,
        CAPAModule,
        TemplateModule,
        SPCModule,
    )
except ImportError:
    InspectionModule = NCRModule = ComplaintModule = CAPAModule = TemplateModule = (
        SPCModule
    ) = MissingModule


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
            btn_new_order.setIcon(qta.icon("ph.plus", color="white"))
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
            btn_stock_in.setIcon(qta.icon("ph.package", color="white"))
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
                "ph.chart-line",
                t.accent_primary,
                [10, 25, 15, 30, 40, 35, 50, 45, 60],
            ),
            (
                "İş Emirleri",
                "24 Adet",
                "▼ 2 gecikme",
                "ph.gear",
                t.accent_secondary,
                [5, 8, 6, 9, 12, 10, 15],
            ),
            (
                "Stok Değeri",
                "₺ 1.2M",
                "● 5 kritik",
                "ph.buildings",
                t.warning,
                [20, 20, 21, 22, 21, 23, 22],
            ),
            (
                "Borçlar",
                "₺ 45K",
                "■ 3 gün vade",
                "ph.receipt",
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


# --- BİLEŞENLER ---


class WindowControls(QWidget):
    """Pencere kontrol butonları (Min, Max, Close)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(150, 38)  # Tab yüksekliğiyle aynı, genişlik artırıldı
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 16, 0)  # Sağ boşluk artırıldı
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Yeşil (minimize)
        self.btn_min = QPushButton()
        self.btn_min.setFixedSize(14, 14)
        self.btn_min.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_min.setStyleSheet(
            """
            QPushButton {
                background-color: #28c940;
                border-radius: 7px;
                border: none;
            }
            QPushButton:hover {
                background-color: #21a835;
            }
            """
        )
        self.btn_min.clicked.connect(self.window().showMinimized)
        layout.addWidget(self.btn_min)

        # Sarı (maximize)
        self.btn_max = QPushButton()
        self.btn_max.setFixedSize(14, 14)
        self.btn_max.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_max.setStyleSheet(
            """
            QPushButton {
                background-color: #ffbd2e;
                border-radius: 7px;
                border: none;
            }
            QPushButton:hover {
                background-color: #e0a628;
            }
            """
        )
        self.btn_max.clicked.connect(self._toggle_max)
        layout.addWidget(self.btn_max)

        # Kırmızı (close)
        self.btn_close = QPushButton()
        self.btn_close.setFixedSize(14, 14)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setStyleSheet(
            """
            QPushButton {
                background-color: #ff5f57;
                border-radius: 7px;
                border: none;
            }
            QPushButton:hover {
                background-color: #e0534c;
            }
            """
        )
        self.btn_close.clicked.connect(lambda: self.window().close())
        layout.addWidget(self.btn_close)

    def _toggle_max(self):
        win = self.window()
        if win.isMaximized():
            win.showNormal()
        else:
            win.showMaximized()


class SideBar(QFrame):
    pageSelected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SideBar")
        self.setFixedWidth(220)  # Genişlik azaltıldı

        # Ana Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- ÜST KISIM: Logo ve Arama ---
        header_frame = QFrame()
        header_frame.setObjectName("SideBarHeader")
        header_frame.setFixedHeight(32)  # Tab yüksekliğiyle kesin eşleşme (32px)
        header_frame.setStyleSheet(
            """
            #SideBarHeader {
                background: transparent; 
                border-bottom: 1px solid #3e3e42;
            }
            """
        )
        header_layout = QHBoxLayout(header_frame)  # Yatay layout
        header_layout.setContentsMargins(10, 0, 10, 0)
        header_layout.setSpacing(8)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Logo
        self.logo_btn = QPushButton()
        self.logo_btn.setFixedSize(28, 28)
        self.logo_btn.setStyleSheet("border: none; background: transparent;")

        logo_path = os.path.join(current_dir, "resources", "icons", "logo.svg")
        if os.path.exists(logo_path):
            self.logo_btn.setIcon(QIcon(logo_path))
        elif "qta" in globals():
            self.logo_btn.setIcon(qta.icon("ph.cube", color="#a855f7"))

        self.logo_btn.setIconSize(QSize(24, 24))
        header_layout.addWidget(self.logo_btn)

        # Arama Kutusu
        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Ara...")
        self.search_input.textChanged.connect(self.filter_menu)
        self.search_input.setFixedHeight(26)  # Yükseklik 26px yapıldı
        self.search_input.setStyleSheet(
            """
            QLineEdit {
                background-color: #2d2d30;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                color: #cccccc;
                padding: 0 8px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #a855f7;
                background-color: #1e1e1e;
            }
        """
        )
        header_layout.addWidget(self.search_input)

        layout.addWidget(header_frame)

        # --- AĞAÇ YAPISI (TreeWidget) ---
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(20)
        self.tree.setFrameShape(QFrame.Shape.NoFrame)
        self.tree.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.tree.setStyleSheet(
            """
            QTreeWidget {
                background: transparent;
                border: none;
                outline: none;
            }
            QTreeWidget::item {
                padding: 6px 4px;
                color: #cccccc;
                border: none;
            }
            QTreeWidget::item:hover {
                background-color: #37373d;
                color: #ffffff;
            }
            QTreeWidget::item:selected {
                background-color: #252526;
                color: #ffffff;
                border-left: 3px solid #a855f7;
            }
            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings {
                border-image: none;
                image: none; /* Standart okları kaldırıp ikon kullanacağız */
            }
            QTreeView::branch:open:has-children:!has-siblings,
            QTreeView::branch:open:has-children:has-siblings {
                border-image: none;
                image: none;
            }
        """
        )
        self.tree.itemClicked.connect(self.on_item_clicked)
        # Mouse hover efektleri için
        self.tree.setMouseTracking(True)
        layout.addWidget(self.tree)

        # Tüm menüleri yükle
        self.load_all_menus()

    def load_all_menus(self):
        """Tüm modülleri ağaç yapısında yükle"""
        self.search_input.clear()
        self.tree.clear()
        self.all_items = (
            []
        )  # Arama için referans tut (parent_item, [(child_name, icon, pid)])

        font_parent = QFont()
        font_parent.setPointSize(11)
        font_parent.setBold(True)

        font_child = QFont()
        font_child.setPointSize(11)

        # Tema renkleri (varsayılan)
        # Akıllı İş Moru: #a855f7 (Logo rengi)
        icon_color = "#a855f7"
        text_color = "#eeeeee"

        for key, data in MENU_DATA.items():
            # Üst Modül (Parent)
            parent = QTreeWidgetItem(self.tree)
            parent.setText(0, data["title"])
            parent.setFont(0, font_parent)
            parent.setForeground(0, QColor(text_color))

            # Modül ikonu bulmaya çalışalım (veri yapısında yoksa varsayılan)
            # Veri yapısında modül ikonu olmadığı için ilk elemanın ikonunu veya genel bir ikon kullanabiliriz.
            # Şimdilik genel bir klasör ikonu koyalım veya Data yapısına ekleyebilirdik.
            if "qta" in globals():
                # Her modüle özel ikon atayabiliriz manuel olarak veya generic
                module_icons = {
                    "dashboard": "ph.house",
                    "inventory": "ph.package",
                    "planning": "ph.calendar",
                    "purchasing": "ph.shopping-cart",
                    "sales": "ph.currency-dollar",
                    "production": "ph.factory",
                    "shipping": "ph.truck",
                    "accounting": "ph.calculator",
                    "finance": "ph.bank",
                    "hr": "ph.users",
                    "maintenance": "ph.wrench",
                    "reports": "ph.chart-pie",
                    "settings": "ph.gear",
                    "crm": "ph.handshake",
                }
                icon_name = module_icons.get(key, "ph.folder")
                parent.setIcon(0, qta.icon(icon_name, color=icon_color))

            # Alt Elemanlar (Children)
            children_data = []  # Arama için sakla
            for name, icon, page_id in data["items"]:
                child = QTreeWidgetItem(parent)
                child.setText(0, name)
                child.setData(0, Qt.ItemDataRole.UserRole, page_id)
                child.setFont(0, font_child)
                child.setForeground(0, QColor("#cccccc"))

                if "qta" in globals():
                    child.setIcon(
                        0, qta.icon(icon, color="#a855f7")
                    )  # Alt ikonlar da mor olsun

                children_data.append((name, icon, page_id))

            self.all_items.append((parent, children_data))

            # Collapse (Kapalı) vaziyette başlasın
            parent.setExpanded(False)

    def filter_menu(self, text):
        """Arama metnine göre ağacı filtrele"""
        search_text = text.lower()
        if not search_text:
            # Arama temizlendiyse hepsini göster ve kapat
            for i in range(self.tree.topLevelItemCount()):
                item = self.tree.topLevelItem(i)
                item.setHidden(False)
                item.setExpanded(False)
                for j in range(item.childCount()):
                    item.child(j).setHidden(False)
            return

        # Arama yapılıyor
        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            parent_match = search_text in parent.text(0).lower()
            has_visible_child = False

            for j in range(parent.childCount()):
                child = parent.child(j)
                child_match = search_text in child.text(0).lower()

                if child_match or parent_match:
                    child.setHidden(False)
                    has_visible_child = True
                else:
                    child.setHidden(True)

            # Eğer parent eşleştiyse veya altından biri eşleştiyse parent'ı göster ve genişlet
            if parent_match or has_visible_child:
                parent.setHidden(False)
                parent.setExpanded(True)
            else:
                parent.setHidden(True)

    def get_breadcrumb_data(self, page_id):
        """Page ID'ye göre (parent_text, parent_icon, item_text, item_icon) döndür"""
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            if item.data(0, Qt.ItemDataRole.UserRole) == page_id:
                parent = item.parent()
                if parent:
                    return {
                        "group_title": parent.text(0),
                        "group_icon": parent.icon(0),
                        "item_title": item.text(0),
                        "item_icon": item.icon(0),
                    }
                else:
                    return {
                        "group_title": item.text(0),
                        "group_icon": item.icon(0),
                        "item_title": "",
                        "item_icon": None,
                    }
            iterator += 1
        return None

    def on_item_clicked(self, item, col):
        # Sadece yaprakların (alt eleman) tıklanması sayfa açar
        # Parent'a tıklanınca aç/kapa yapar (varsayılan davranış)
        pid = item.data(0, Qt.ItemDataRole.UserRole)
        if pid:
            self.pageSelected.emit(pid)
        else:
            # Parent tıklandıysa aç/kapa durumunu tersine çevir (isteğe bağlı, qtree bunu zaten yapar ama icon tıklaması bazen sorun olur)
            item.setExpanded(not item.isExpanded())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

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
        # Pencerenin ekran boyutunu aşmasını engelle
        self.setMaximumSize(screen.width(), screen.height())
        self.move(
            (screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2
        )

    def setup_pages_dict(self):
        self.pages = {}
        self.pages["dashboard"] = DashboardPage()
        # Stok modülü sayfaları
        self.pages["stock-cards"] = InventoryModule()
        self.pages["categories"] = CategoryModule()
        self.pages["units"] = UnitModule()
        self.pages["warehouses"] = WarehouseModule()
        self.pages["locations"] = LocationManagementPage()
        self.pages["movements"] = MovementModule()
        self.pages["item-movements"] = MovementModule()
        self.pages["sscc-units"] = SSCCModule()
        self.pages["stock-count"] = StockCountModule()
        self.pages["warehouse-operator"] = WarehouseOperatorPage()
        self.pages["stock-reports"] = StockReportsModule()
        # Üretim modülü sayfaları
        self.pages["work-orders"] = WorkOrderModule()
        self.pages["bom"] = BOMModule()
        self.pages["planning"] = PlanningModule()
        self.pages["work-stations"] = WorkStationModule()
        self.pages["calendar"] = CalendarModule()
        self.pages["calendar"] = CalendarModule()
        self.pages["mrp"] = MRPModule()
        self.pages["mps-cockpit"] = MPSCockpitPage()
        self.pages["plan-list"] = MPSPlanListPage()
        self.pages["capacity-analysis"] = CapacityAnalysisPage()
        self.pages["operator-panel"] = OperatorPanel()
        # Kalite modülü sayfaları
        self.pages["quality-inspections"] = InspectionModule()
        self.pages["quality-ncr"] = NCRModule()
        self.pages["quality-complaints"] = ComplaintModule()
        self.pages["quality-capa"] = CAPAModule()
        self.pages["quality-templates"] = TemplateModule()
        self.pages["quality-spc"] = SPCModule()
        # Satınalma modülü sayfaları
        self.pages["suppliers"] = SupplierModule()
        self.pages["purchase-requests"] = PurchaseRequestModule()
        self.pages["goods-receipts"] = GoodsReceiptModule()
        self.pages["purchase-orders"] = PurchaseOrderModule()
        self.pages["purchase-invoices"] = PurchaseInvoiceModule()
        self.pages["rfq"] = RFQModule()
        # Satış modülü sayfaları
        self.pages["customers"] = CustomerModule()
        self.pages["sales-quotes"] = SalesQuoteModule()
        self.pages["sales-orders"] = SalesOrderModule()
        self.pages["sales-returns"] = ReturnModule()
        self.pages["sales-contracts"] = ContractModule()
        self.pages["delivery-notes"] = DeliveryNoteModule()
        self.pages["invoices"] = InvoiceModule()
        self.pages["price-lists"] = PriceListModule()
        # Sevkiyat modülü sayfaları
        self.pages["shipping"] = ShippingMainModule()
        self.pages["fleet-management"] = FleetMainModule()
        # e-Dönüşüm modülü sayfaları
        self.pages["einvoices"] = EInvoiceModule()
        # Muhasebe modülü sayfaları
        self.pages["accounts"] = AccountModule()
        self.pages["journals"] = JournalModule()
        self.pages["accounting-reports"] = AccountingReportsModule()
        self.pages["fixed-assets"] = FixedAssetModule()
        self.pages["budgets"] = BudgetModule()
        # Finans modülü sayfaları
        self.pages["receipts"] = ReceiptModule()
        self.pages["payments"] = PaymentModule()
        self.pages["reconciliation"] = ReconciliationModule()
        self.pages["account-statements"] = AccountStatementModule()
        # Raporlar modulu sayfalari
        self.pages["sales-reports"] = SalesReportsModule()
        self.pages["stock-aging"] = StockAgingModule()
        self.pages["production-oee"] = ProductionOEEModule()
        self.pages["oee-monitoring"] = OEEMonitoringModule()
        self.pages["supplier-performance"] = SupplierPerformanceModule()
        self.pages["receivables-aging"] = ReceivablesAgingModule()
        # Geliştirme modülü
        self.pages["error-logs"] = DevelopmentModule()
        try:
            from modules.development.views.trace_viewer_module import TraceViewerModule

            self.pages["trace-viewer"] = TraceViewerModule()
        except ImportError:
            self.pages["trace-viewer"] = MissingModule("TraceViewerModule yüklenemedi")
        # İnsan Kaynakları modülü
        self.pages["employees"] = EmployeeModule()
        self.pages["departments"] = DepartmentModule()
        self.pages["positions"] = PositionModule()
        self.pages["leaves"] = LeaveModule()
        self.pages["attendance"] = AttendanceModule()
        self.pages["org-chart"] = OrgChartModule()
        self.pages["shift-teams"] = ShiftTeamOverview()
        self.pages["performance"] = PerformanceModule()
        self.pages["trainings"] = TrainingModule()
        self.pages["personnel"] = PersonnelModule()
        self.pages["hr-dashboard"] = HRDashboardModule()
        self.pages["shift-planning"] = ShiftPlanningModule()
        self.pages["hr-recruitment"] = RecruitmentModule()
        # Proje Yönetimi
        self.pages["project-management"] = ProjectMainModule()
        # Sistem ayarları
        self.pages["settings"] = PlaceholderPage("Ayarlar", "")
        self.pages["users"] = UserManagement()
        self.pages["theme-settings"] = ThemeSettingsPage()
        self.pages["label-templates"] = LabelTemplatesPage()
        self.pages["audit-logs"] = AuditLogViewer()
        self.pages["company-card"] = CompanyCard()

        # Workflow Admin Modülü
        from modules.workflow.views import WorkflowAdminModule

        self.pages["workflow-admin"] = WorkflowAdminModule()

        # Bakım ve Onarım Modülü
        self.pages["equipments"] = EquipmentListWidget()
        self.pages["maintenance-requests"] = MaintenanceRequestWidget()
        self.pages["maintenance-work-orders"] = WorkOrderManagerWidget()
        self.pages["maintenance-plans"] = MaintenancePlanWidget()
        self.pages["maintenance-reports"] = ReportingWidget()

        # CRM Modülü
        self.pages["leads"] = CRMModule()
        self.pages["opportunities"] = OpportunityModule()
        self.pages["activities"] = ActivityModule()

    def setup_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)

        # Ana yatay layout (Sidebar | İçerik)
        root = QHBoxLayout(central_widget)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # --- Sidebar ---
        self.sidebar = SideBar()
        root.addWidget(self.sidebar)

        # --- Tabs (Titlebar merged) ---
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setMovable(True)
        self.tabs.setTabsClosable(True)

        # Sekme genişliği kontrolü - pencerenin sağa uzamasını önle
        tab_bar = self.tabs.tabBar()
        tab_bar.setElideMode(Qt.TextElideMode.ElideRight)  # Uzun isimleri kısalt
        tab_bar.setExpanding(False)  # Sekmelerin genişlemesini engelle
        tab_bar.setUsesScrollButtons(
            True
        )  # Çok fazla sekme olunca scroll butonları göster

        # === STACKED WIDGET (Tabs vs Empty State) ===
        self.stacked_widget = QStackedWidget()
        # İçeriğin pencereyi genişletmesini engelle
        self.stacked_widget.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored
        )

        # 1. Tabs View
        self.stacked_widget.addWidget(self.tabs)

        # 2. Empty State View
        self.empty_state = EmptyStateWidget()
        self.stacked_widget.addWidget(self.empty_state)

        # Stil (Tab Widget)
        self.tabs.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        # Window Controls in Top Right
        # System title bar restored, custom controls removed.
        # self.window_controls = WindowControls()
        # self.tabs.setCornerWidget(self.window_controls, Qt.Corner.TopRightCorner)

        # Styling to mimic titlebar integration
        self.tabs.setStyleSheet(
            """
            QTabWidget::pane {
                border: none;
                border-left: 1px solid #3e3e42;
                top: -1px;
                margin: 0;
                padding: 0;
            }
            QTabBar::tab {
                height: 32px;
                border: none;
                border-right: 1px solid #2d2d30;
                padding: 0 10px;
                background: #1e1e1e;
                color: #888888;
                max-width: 180px;
                min-width: 80px;
            }
            QTabBar::tab:selected {
                background: #252526;
                color: #ffffff;
                border-top: 2px solid #a855f7;
            }
            QTabBar::tab:hover {
                background: #2d2d30;
            }
        """
        )

        # === STATUSBAR ===
        self.status_bar = QStatusBar()
        self.status_bar.setFixedHeight(28)
        self.setStatusBar(self.status_bar)

        # Logo
        logo_path = os.path.join(current_dir, "resources", "icons", "logo.png")
        if os.path.exists(logo_path):
            self.status_logo_label = QLabel()
            pixmap = QPixmap(logo_path)
            self.status_logo_label.setPixmap(
                pixmap.scaled(
                    20,
                    20,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            self.status_logo_label.setStyleSheet(
                "padding-left: 10px; padding-right: 5px; border: none; background: transparent;"
            )
            self.status_bar.addWidget(self.status_logo_label)

        # Breadcrumb Container (İkonlar ve Yazılar için)
        self.breadcrumb_container = QWidget()
        self.breadcrumb_container.setStyleSheet(
            "background: transparent; border: none;"
        )
        self.breadcrumb_layout = QHBoxLayout(self.breadcrumb_container)
        self.breadcrumb_layout.setContentsMargins(10, 0, 0, 0)
        self.breadcrumb_layout.setSpacing(4)
        self.status_bar.addWidget(self.breadcrumb_container)

        # Sağ taraf: Kullanıcı
        self.status_user_container = QWidget()
        self.status_user_container.setStyleSheet(
            "background: transparent; border: none;"
        )
        self.status_user_layout = QHBoxLayout(self.status_user_container)
        self.status_user_layout.setContentsMargins(0, 0, 10, 0)
        self.status_user_layout.setSpacing(4)

        self.status_user_icon_label = QLabel()
        self.status_user_label = QLabel("Admin")
        self.status_user_label.setStyleSheet("font-weight: 500; color: #cccccc;")

        self.status_user_layout.addWidget(self.status_user_icon_label)
        self.status_user_layout.addWidget(self.status_user_label)

        # Trace toggle butonu
        self._setup_trace_button()

        self.status_bar.addPermanentWidget(self.status_user_container)

        QSizeGrip(self.status_bar)

        self.tabs.tabCloseRequested.connect(self.close_tab)
        # Tab değişince status bar güncelle
        self.tabs.currentChanged.connect(self.update_status_bar)

        self.open_tab("dashboard")  # Başlangıçta dashboard aç

        root.addWidget(self.stacked_widget)

        self.check_tabs_state()

    def connect_signals(self):
        # self.activity_bar.moduleSelected.connect(self.open_menu)
        self.sidebar.pageSelected.connect(self.open_tab)
        # self.sidebar.closeRequested.connect(self.close_menu_if_not_locked)
        # self.title_bar.btn_toggle.toggled.connect(self.toggle_sidebar_lock)

    def _on_theme_changed(self, theme):
        self._apply_theme()

    def _apply_theme(self):
        t = get_theme()
        # Font ölçeğini al
        font_multiplier = ThemeManager.get_font_scale_multiplier()
        base_font = int(t.font_size * font_multiplier)
        small_font = int(t.font_size_small * font_multiplier)

        self.setStyleSheet(
            f"""
        QMainWindow, #CentralWidget {{ background-color: {t.bg_primary}; }}
        QWidget {{
            color: {t.text_primary};
            font-family: {t.font_family};
            font-size: {base_font}px;
        }}

        #SearchInput {{
            background-color: {t.bg_tertiary};
            border: 1px solid {t.border};
            border-radius: 3px;
            color: {t.text_primary};
            padding: 1px 10px;
            height: 22px;
        }}
        #SearchInput:focus {{
            border: 1px solid {t.accent_primary};
            background-color: {t.bg_hover};
        }}

        #SideBar {{
            background-color: {t.sidebar_bg};
            border-right: none;
        }}
        #SideBarHeader {{
            background-color: {t.bg_tertiary};
            border-bottom: 1px solid {t.border};
            border-right: none;
        }}
        QTreeWidget {{
            background-color: {t.sidebar_bg};
            border: none;
            border-right: 1px solid {t.border};
            outline: none;
        }}
        QTreeWidget::item {{
            padding: 6px;
            color: {t.text_primary};
            border: none;
        }}
        QTreeWidget::item:hover {{
            background-color: {t.bg_hover};
        }}
        QTreeWidget::item:selected {{
            background-color: {t.bg_selected};
            color: white;
            border-left: 2px solid {t.accent_primary};
        }}

        QTabWidget::pane {{
            border: none;
            background-color: {t.bg_primary};
            border-top: 1px solid {t.border};
            margin: 0;
            padding: 0;
        }}
        QTabBar::tab {{
            background: {t.bg_tertiary};
            color: {t.text_muted};
            padding: 0 10px;
            border-right: 1px solid {t.border};
            border-top: 1px solid transparent;
            height: 32px;
            max-width: 180px;
            min-width: 80px;
        }}
        QTabBar::tab:selected {{
            background: {t.bg_primary};
            color: {t.text_primary};
            border-top: 2px solid {t.accent_primary};
            border-bottom: 1px solid {t.bg_primary};
        }}
        QTabBar::tab:hover {{
            background: {t.bg_secondary};
            color: {t.text_primary};
        }}
        QTabBar::close-button {{ width: 0px; height: 0px; }}
        QTabBar::close-button:selected {{ width: 16px; height: 16px; margin-left: 5px; }}

        QStatusBar {{
            background-color: {t.bg_primary};
            color: {t.text_secondary};
            border-top: 1px solid {t.border};
            min-height: 22px;
        }}
        QStatusBar::item {{
            border: none;
            background: transparent;
        }}
        QStatusBar QLabel {{
            background: transparent;
            font-size: {small_font}px;
            color: {t.text_secondary};
            border: none;
        }}

        /* Genel widget stilleri */
        QScrollArea {{ background: transparent; border: none; }}
        QFrame {{ background-color: {t.bg_secondary}; }}
        QLabel {{ background: transparent; border: none; }}
        QPushButton {{
            background-color: {t.bg_tertiary};
            border: 1px solid {t.border};
            border-radius: {t.radius_small}px;
            padding: 6px 12px;
            color: {t.text_primary};
        }}
        QPushButton:hover {{
            background-color: {t.bg_hover};
            border-color: {t.accent_primary};
        }}
        QPushButton:pressed {{
            background-color: {t.bg_selected};
        }}

        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {t.input_bg};
            border: 1px solid {t.border};
            border-radius: {t.radius_small}px;
            padding: 6px;
            color: {t.text_primary};
        }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {t.accent_primary};
        }}

        QComboBox {{
            background-color: {t.input_bg};
            border: 1px solid {t.border};
            border-radius: {t.radius_small}px;
            padding: 6px;
            color: {t.text_primary};
        }}
        QComboBox:hover {{
            border-color: {t.accent_primary};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {t.bg_secondary};
            border: 1px solid {t.border};
            selection-background-color: {t.bg_selected};
        }}

        QTableWidget, QTableView {{
            background-color: {t.bg_primary};
            alternate-background-color: {t.bg_secondary};
            border: 1px solid {t.border};
            gridline-color: {t.border};
            color: {t.text_primary};
        }}
        QTableWidget::item:selected, QTableView::item:selected {{
            background-color: {t.bg_selected};
            color: white;
        }}
        QHeaderView::section {{
            background-color: {t.bg_tertiary};
            color: {t.text_primary};
            padding: 6px;
            border: none;
            border-right: 1px solid {t.border};
            border-bottom: 1px solid {t.border};
        }}

        QScrollBar:vertical {{
            background: {t.bg_secondary};
            width: 10px;
            border-radius: 5px;
        }}
        QScrollBar::handle:vertical {{
            background: {t.bg_tertiary};
            border-radius: 5px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {t.border_light};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QScrollBar:horizontal {{
            background: {t.bg_secondary};
            height: 10px;
            border-radius: 5px;
        }}
        QScrollBar::handle:horizontal {{
            background: {t.bg_tertiary};
            border-radius: 5px;
            min-width: 30px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {t.border_light};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        """
        )

    def show_notification(self, message: str, level: str = "INFO"):
        """
        Yeni modern toast bildirim sistemini kullanarak mesaj gösterir.
        """
        # Yeni Toast Bildirimi (Sağ alt köşede çıkar)
        show_toast(message, level)

        # Durum çubuğunda da kısa süreli (5sn) göster
        icons = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "⛔"}
        self.status_bar.showMessage(f"  {icons.get(level, '')}  {message}", 5000)

    def update_status_bar(self, index=None):
        """Update status bar based on current context"""
        from config.themes import get_theme
        from PyQt6.QtWidgets import QTabWidget, QStackedWidget, QLabel
        from PyQt6.QtGui import QIcon

        t = get_theme()

        # Kullanıcı Adı (AuthService'den al)
        try:
            from core.auth_service import AuthService

            user = AuthService.get_current_user()
            display_name = (
                user.full_name
                if user and user.full_name
                else (user.username if user else "Admin")
            )
        except Exception:
            display_name = "Admin"

        if "qta" in globals():
            user_icon = qta.icon("ph.user-circle", color=t.accent_primary)
            self.status_user_icon_label.setPixmap(user_icon.pixmap(18, 18))
            self.status_user_label.setText(display_name)
        else:
            self.status_user_label.setText(f"👤 {display_name}")

        current_widget = self.tabs.currentWidget()
        if not current_widget:
            # Breadcrumb Temizle
            while self.breadcrumb_layout.count():
                item = self.breadcrumb_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            return

        # Dinamik içerik takibi (Yeni eklenen tab/stackleri yakala)
        # Her değişimi dinlemek için çocukları geziyoruz
        for child in current_widget.findChildren((QTabWidget, QStackedWidget)):
            try:
                child.currentChanged.disconnect(self.update_status_bar)
            except (TypeError, RuntimeError):
                pass
            child.currentChanged.connect(self.update_status_bar)

        # Breadcrumb Temizle
        while self.breadcrumb_layout.count():
            item = self.breadcrumb_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        page_id = current_widget.property("page_id")
        if not page_id:
            return

        b_data = self.sidebar.get_breadcrumb_data(page_id)
        if not b_data:
            return

        # Navigasyon Parçalarını Oluştur
        nav_items = []
        # 1. Modül
        nav_items.append((b_data["group_title"], b_data["group_icon"]))
        # 2. Sayfa
        if b_data["item_title"]:
            nav_items.append((b_data["item_title"], b_data["item_icon"]))

        # 3. Form / Sub-Page (StackedWidget kontrolü)
        stacks = current_widget.findChildren(QStackedWidget)
        for stack in stacks:
            if stack.isVisible() and stack.currentIndex() >= 0:
                current_stack_widget = stack.currentWidget()
                if current_stack_widget:
                    from ui.components.page_header import PageHeader

                    headers = current_stack_widget.findChildren(PageHeader)
                    if headers:
                        header = headers[0]
                        h_title = header.title_label.text()
                        h_icon = None

                        # PageHeader'dan ikonu al (Gelişmiş Mantık)
                        h_icon = None
                        if hasattr(header, "resolved_icon") and header.resolved_icon:
                            try:
                                h_icon = qta.icon(
                                    header.resolved_icon, color=t.accent_primary
                                )
                            except Exception:
                                pass

                        if not h_icon or h_icon.isNull():
                            # Header içindeki ikon label'ını bulmaya çalış (fallback)
                            for child in header.findChildren(QLabel):
                                pix = child.pixmap()
                                if pix and not pix.isNull():
                                    h_icon = QIcon(pix)
                                    break

                        # Fallback: Eğer hala ikon yoksa sayfa ikonunu kullan
                        if not h_icon or h_icon.isNull():
                            h_icon = b_data["item_icon"]

                        # Eğer modül başlığı ile aynıysa (liste görünümü), ekleme
                        # Başlıkları normalize ederek karşılaştır
                        if (
                            h_title.strip().lower()
                            != b_data["item_title"].strip().lower()
                        ):
                            nav_items.append((h_title, h_icon))

        # 4. Sekme (TabWidget kontrolü)
        inner_tabs = current_widget.findChildren(QTabWidget)
        for tab in inner_tabs:
            if tab.isVisible() and tab.count() > 0:
                text = tab.tabText(tab.currentIndex())
                icon = tab.tabIcon(tab.currentIndex())
                if not icon or icon.isNull():
                    # Sekme ikonu yoksa sayfa ikonunu kullan
                    icon = b_data["item_icon"]
                nav_items.append((text, icon))
                break

        # UI'a Ekle
        for i, (text, icon) in enumerate(nav_items):
            if i > 0:
                sep = QLabel(">")
                sep.setStyleSheet(
                    "color: #ffffff; margin: 0 4px; "
                    "background: transparent; font-weight: bold;"
                )
                self.breadcrumb_layout.addWidget(sep)

            if icon:
                ico_lbl = QLabel()
                ico_lbl.setPixmap(icon.pixmap(16, 16))
                ico_lbl.setStyleSheet("margin-right: 0px; background: transparent;")
                self.breadcrumb_layout.addWidget(ico_lbl)

            txt_lbl = QLabel(text)
            txt_lbl.setStyleSheet(
                "color: white; font-weight: 500; background: transparent;"
            )
            self.breadcrumb_layout.addWidget(txt_lbl)

        self.breadcrumb_layout.addStretch()

    def open_tab(self, page_id):
        # İzin kontrolü
        try:
            from core.auth_service import AuthService

            if AuthService.is_authenticated():
                if not AuthService.can_access_page(page_id):
                    self.show_notification(
                        f"'{page_id}' sayfasına erişim izniniz yok", "WARNING"
                    )
                    return
        except ImportError:
            pass  # Development mode

        page_widget = self.pages.get(page_id)
        if not page_widget:
            return

        # Set property for breadcrumb lookup
        page_widget.setProperty("page_id", page_id)

        for i in range(self.tabs.count()):
            if self.tabs.widget(i) == page_widget:
                self.tabs.setCurrentIndex(i)
                return

        # Maksimum sekme kontrolü
        if self.tabs.count() >= 10:
            self.show_notification(
                "Maksimum 10 sekme açabilirsiniz. Lütfen bazı sekmeleri kapatın.",
                "WARNING",
            )
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
        self.check_tabs_state()

    def close_tab(self, index):
        self.tabs.removeTab(index)
        self.check_tabs_state()

    def check_tabs_state(self):
        """Sekme sayısına göre görünümü güncelle"""
        if self.tabs.count() == 0:
            self.stacked_widget.setCurrentWidget(self.empty_state)
        else:
            self.stacked_widget.setCurrentWidget(self.tabs)

    def go_prev_tab(self):
        if (i := self.tabs.currentIndex()) > 0:
            self.tabs.setCurrentIndex(i - 1)

    def go_next_tab(self):
        if (i := self.tabs.currentIndex()) < self.tabs.count() - 1:
            self.tabs.setCurrentIndex(i + 1)

    # ==================== TRACE SYSTEM ====================

    def _setup_trace_button(self):
        """Trace toggle butonunu status bar'a ekle"""
        self.trace_button = QPushButton()
        self.trace_button.setCheckable(True)
        self.trace_button.setChecked(False)
        self.trace_button.setText("Destek Modu")
        self.trace_button.setToolTip(
            "Hata izleme modunu baslatin.\n"
            "Aktifken tum islemleriniz kaydedilir.\n"
            "Hata aldiginizda otomatik durur ve rapor olusturulur."
        )
        self.trace_button.setStyleSheet(
            """
            QPushButton {
                background-color: transparent;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 2px 8px;
                color: #aaa;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border-color: #666;
            }
            QPushButton:checked {
                background-color: #8B0000;
                border-color: #FF4444;
                color: #fff;
            }
            QPushButton:checked:hover {
                background-color: #A00000;
            }
        """
        )
        self.trace_button.toggled.connect(self._on_trace_toggled)
        self.status_bar.addPermanentWidget(self.trace_button)

        # Trace sinyallerini bağla
        self._connect_trace_signals()

    def _connect_trace_signals(self):
        """Trace service sinyallerini bağla"""
        try:
            from modules.development.trace_service import TraceService

            # Sinyalleri bağla
            TraceService().signals.trace_started.connect(self._on_trace_started)
            TraceService().signals.trace_stopped.connect(self._on_trace_stopped)
            TraceService().signals.trace_timeout.connect(self._on_trace_timeout)
        except Exception as e:
            print(f"[MainWindow] Trace signals connection failed: {e}")

    def _on_trace_toggled(self, checked: bool):
        """Trace butonu toggle edildiğinde"""
        try:
            from modules.development.trace_service import TraceService
            from modules.development.event_interceptor import trace_event_filter
            from modules.development.sql_tracer import sql_tracer

            if checked:
                # Trace başlat
                user_id = (
                    self._current_user.id
                    if hasattr(self, "_current_user") and self._current_user
                    else 1
                )
                session_id = TraceService.start_trace(user_id=user_id, reason="manual")

                if session_id:
                    # Event filter'ı install et
                    trace_event_filter.install()
                    trace_event_filter.set_breadcrumb_provider(
                        self._get_current_breadcrumb
                    )

                    # SQL tracer'ı etkinleştir
                    sql_tracer.init_listeners()
                    sql_tracer.enable()

                    self.trace_button.setText("Kayit Aliniyor...")
                    self.show_notification("Hata izleme modu baslatildi", "info")
                else:
                    # Zaten aktif
                    self.trace_button.setChecked(False)
            else:
                # Trace durdur
                user_id = (
                    self._current_user.id
                    if hasattr(self, "_current_user") and self._current_user
                    else None
                )
                TraceService.stop_trace(user_id=user_id)

                # Event filter'ı kaldır
                trace_event_filter.uninstall()

                # SQL tracer'ı devre dışı bırak
                sql_tracer.disable()

                self.trace_button.setText("Destek Modu")
                self.show_notification("Hata izleme modu durduruldu", "info")

        except Exception as e:
            print(f"[MainWindow] Trace toggle error: {e}")
            self.trace_button.setChecked(False)

    def _on_trace_started(self, session_id: int):
        """Trace başladığında"""
        self.trace_button.setChecked(True)
        self.trace_button.setText("Kayit Aliniyor...")

    def _on_trace_stopped(self, session_id: int):
        """Trace durduğunda"""
        self.trace_button.setChecked(False)
        self.trace_button.setText("Destek Modu")

    def _on_trace_timeout(self, user_id: int):
        """Trace timeout olduğunda"""
        self.trace_button.setChecked(False)
        self.trace_button.setText("Destek Modu")
        self.show_notification("Hata izleme modu zaman asimina ugradi", "warning")

    def _get_current_breadcrumb(self) -> str:
        """Mevcut breadcrumb'ı döndür (trace için)"""
        try:
            # Mevcut tab'daki sayfanın path'ini al
            current_widget = self.tabs.currentWidget()
            if current_widget and hasattr(current_widget, "page_title"):
                return current_widget.page_title
            return self.tabs.tabText(self.tabs.currentIndex())
        except Exception:
            return ""


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
