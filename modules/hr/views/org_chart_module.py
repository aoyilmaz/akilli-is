"""
Akıllı İş - Organizasyon Şeması Modülü
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QHeaderView,
    QComboBox,
    QTabWidget,
    QGraphicsView,
    QGraphicsScene,
)
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QColor, QFont, QPen, QBrush, QPainter
import qtawesome as qta

from config.icons import ICONS
from config.themes import get_theme
from modules.hr.services import HRService
from ui.components.page_header import PageHeader


class OrgChartModule(QWidget):
    """Organizasyon Şeması Sayfası"""

    page_title = "Organizasyon Şeması"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = HRService()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # === Header ===
        self.header = PageHeader(
            title="Organizasyon Şeması",
            icon=ICONS.CHART,
            show_search=False,
            show_add=False,
            parent=self,
        )
        self.header.refresh_clicked.connect(self._load_data)

        h_layout = self.header.header_layout()
        self.view_combo = QComboBox()
        self.view_combo.addItem("Departmana Göre", "department")
        self.view_combo.addItem("Yöneticiye Göre", "manager")
        self.view_combo.setFixedHeight(36)
        self.view_combo.setFixedWidth(180)
        self.view_combo.currentIndexChanged.connect(self._load_data)
        h_layout.addWidget(self.view_combo)
        layout.addWidget(self.header)

        # === Tabs ===
        self.tabs = QTabWidget()

        # --- List View Tab ---
        list_tab = QWidget()
        list_layout = QVBoxLayout(list_tab)
        list_layout.setContentsMargins(0, 10, 0, 0)

        t = get_theme()
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Ad Soyad / Birim", "Pozisyon", "Email", "Telefon"])
        self.tree.setAlternatingRowColors(True)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.setStyleSheet(
            f"""
            QTreeWidget {{
                background-color: {t.card_bg};
                border: 1px solid {t.border};
                border-radius: 8px;
            }}
            QTreeWidget::item {{
                height: 32px;
            }}
        """
        )
        list_layout.addWidget(self.tree)
        self.tabs.addTab(list_tab, "Liste Görünümü")

        # --- Visual View Tab ---
        visual_tab = QWidget()
        visual_layout = QVBoxLayout(visual_tab)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setStyleSheet(
            f"background-color: {t.card_bg}; border: 1px solid {t.border}; border-radius: 8px;"
        )
        visual_layout.addWidget(self.view)

        self.tabs.addTab(visual_tab, "Görsel Şema")

        layout.addWidget(self.tabs)

        self.summary_label = QLabel()
        self.summary_label.setStyleSheet(
            f"color: {t.text_secondary}; font-weight: bold;"
        )
        layout.addWidget(self.summary_label)

    def showEvent(self, event):
        super().showEvent(event)
        self._load_data()

    def _load_data(self):
        v = self.view_combo.currentData()
        if v == "department":
            self._load_by_department()
        else:
            self._load_by_manager()

        # Görsel şemayı her durumda güncelle (Yönetici hiyerarşisi esaslı)
        try:
            emps = self.service.get_all_employees(limit=1000)
            tops = [e for e in emps if not e.manager_id]
            self._render_visual_chart(tops, emps)
        except Exception:
            pass

    def _load_by_department(self):
        self.tree.clear()
        try:
            depts = self.service.get_all_departments()
            emps = self.service.get_all_employees(limit=1000)
            total = 0
            for d in depts:
                ds = [e for e in emps if e.department_id == d.id]
                if not ds:
                    continue
                di = QTreeWidgetItem([d.name, "", f"{len(ds)} kişi", ""])
                di.setIcon(0, qta.icon(ICONS.FOLDER, color="#818cf8"))
                di.setFont(0, QFont("", 10, QFont.Weight.Bold))
                di.setForeground(0, QColor("#818cf8"))
                poss = {}
                for e in ds:
                    pn = e.position.name if e.position else "Belirsiz"
                    if pn not in poss:
                        poss[pn] = []
                    poss[pn].append(e)
                    total += 1
                for pn, pes in poss.items():
                    pi = QTreeWidgetItem([pn, "", f"{len(pes)} kişi", ""])
                    pi.setIcon(0, qta.icon(ICONS.LIST, color="#a78bfa"))
                    pi.setForeground(0, QColor("#a78bfa"))
                    for e in pes:
                        ei = QTreeWidgetItem(
                            [
                                e.full_name,
                                "",
                                e.email or "-",
                                e.phone or e.mobile or "-",
                            ]
                        )
                        ei.setIcon(0, qta.icon(ICONS.USER, color="#9ca3af"))
                        pi.addChild(ei)
                    di.addChild(pi)
                self.tree.addTopLevelItem(di)
                di.setExpanded(True)
            self.summary_label.setText(f"Toplam: {total} çalışan")
        except Exception as e:
            print(f"Org chart error: {e}")

    def _load_by_manager(self):
        self.tree.clear()
        try:
            emps = self.service.get_all_employees(limit=1000)
            tops = [e for e in emps if not e.manager_id]

            def add_subs(pi, mid):
                subs = [e for e in emps if e.manager_id == mid]
                for e in subs:
                    pn = e.position.name if e.position else ""
                    ei = QTreeWidgetItem(
                        [e.full_name, pn, e.email or "-", e.phone or e.mobile or "-"]
                    )
                    ei.setIcon(0, qta.icon(ICONS.USER, color="#9ca3af"))
                    pi.addChild(ei)
                    add_subs(ei, e.id)

            for e in tops:
                gi = ICONS.USER
                pn, dn = e.position.name if e.position else "", (
                    e.department.name if e.department else ""
                )
                ei = QTreeWidgetItem(
                    [
                        e.full_name,
                        f"{pn} - {dn}",
                        e.email or "-",
                        e.phone or e.mobile or "-",
                    ]
                )
                ei.setIcon(0, qta.icon(ICONS.CHART, color="#f59e0b"))
                ei.setFont(0, QFont("", 10, QFont.Weight.Bold))
                ei.setForeground(0, QColor("#f59e0b"))
                self.tree.addTopLevelItem(ei)
                add_subs(ei, e.id)
                ei.setExpanded(True)
            self.summary_label.setText(f"Toplam: {len(emps)} çalışan")
            self._render_visual_chart(tops, emps)
        except Exception as e:
            print(f"Org chart error: {e}")

    def _render_visual_chart(self, tops, all_employees):
        """Görsel şemayı pozisyon bazlı ve gruplanmış olarak çiz"""
        self.scene.clear()
        if not tops:
            return

        node_width = 200
        node_height = 60
        h_spacing = 50
        v_spacing = 100

        # En üst seviyeyi (yöneticisizler) pozisyona göre grupla
        top_groups = {}
        for e in tops:
            pid = e.position_id
            if pid not in top_groups:
                top_groups[pid] = []
            top_groups[pid].append(e)

        def get_subtree_width(employees):
            """Bir grubun alt ağacının toplam genişliğini hesapla"""
            # Bu grubun tüm alt çalışanlarını bul
            all_subs = []
            for emp in employees:
                subs = [e for e in all_employees if e.manager_id == emp.id]
                all_subs.extend(subs)

            if not all_subs:
                return node_width

            # Altındakileri pozisyona göre grupla
            sub_groups = {}
            for sub in all_subs:
                pid = sub.position_id
                if pid not in sub_groups:
                    sub_groups[pid] = []
                sub_groups[pid].append(sub)

            total_w = 0
            for g_emps in sub_groups.values():
                total_w += get_subtree_width(g_emps)
            total_w += (len(sub_groups) - 1) * h_spacing
            return max(node_width, total_w)

        def draw_grouped_node(employees, x, y):
            if not employees:
                return

            sample = employees[0]
            pos_name = sample.position.name if sample.position else "Belirsiz"
            count = len(employees)

            # Kutu rengi (yönetici ise farklı)
            is_manager = any(
                e
                for e in all_employees
                if e.manager_id in [emp.id for emp in employees]
            )
            bg_color = QColor("#1e293b")
            border_color = QColor("#818cf8") if is_manager else QColor("#475569")

            # Kutu çiz
            self.scene.addRect(
                QRectF(x, y, node_width, node_height),
                QPen(border_color, 2),
                QBrush(bg_color),
            )

            # Pozisyon Adı
            pos_text = self.scene.addText(pos_name)
            pos_text.setDefaultTextColor(QColor("white"))
            pos_text.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            pos_text.setPos(x + 5, y + 10)

            # Çalışan Sayısı
            count_text = self.scene.addText(f"{count} Kişi")
            count_text.setDefaultTextColor(QColor("#94a3b8"))
            count_text.setFont(QFont("Arial", 9))
            count_text.setPos(x + 5, y + 30)

            # Alt çalışanları bul ve grupla
            all_subs = []
            for emp in employees:
                subs = [e for e in all_employees if e.manager_id == emp.id]
                all_subs.extend(subs)

            if all_subs:
                sub_groups = {}
                for sub in all_subs:
                    pid = sub.position_id
                    if pid not in sub_groups:
                        sub_groups[pid] = []
                    sub_groups[pid].append(sub)

                # Alt ağaçların toplam genişliği
                total_w = 0
                widths = []
                for g_pid in sub_groups:
                    w = get_subtree_width(sub_groups[g_pid])
                    widths.append(w)
                    total_w += w
                total_w += (len(sub_groups) - 1) * h_spacing

                start_x = x + (node_width / 2) - (total_w / 2)
                current_x = start_x

                for i, g_pid in enumerate(sub_groups):
                    sub_group_emps = sub_groups[g_pid]
                    sub_w = widths[i]
                    sub_x = current_x + (sub_w / 2) - (node_width / 2)
                    sub_y = y + node_height + v_spacing

                    # Çizgi çek (Dirsekli çizgi şık durur ama şimdilik düz)
                    self.scene.addLine(
                        x + node_width / 2,
                        y + node_height,
                        sub_x + node_width / 2,
                        sub_y,
                        QPen(QColor("#475569"), 1),
                    )

                    draw_grouped_node(sub_group_emps, sub_x, sub_y)
                    current_x += sub_w + h_spacing

        # Başlangıç
        current_x = 0
        total_top_w = 0
        top_widths = []
        for pid in top_groups:
            w = get_subtree_width(top_groups[pid])
            top_widths.append(w)
            total_top_w += w
        total_top_w += (len(top_groups) - 1) * h_spacing

        current_x = -total_top_w / 2
        for i, pid in enumerate(top_groups):
            g_w = top_widths[i]
            node_x = current_x + (g_w / 2) - (node_width / 2)
            draw_grouped_node(top_groups[pid], node_x, 0)
            current_x += g_w + h_spacing

        # Sahneyi güncelle ve ortala
        self.scene.setSceneRect(self.scene.itemsBoundingRect())
        self.view.centerOn(0, 0)

    def closeEvent(self, event):
        self.service.close()
        super().closeEvent(event)
