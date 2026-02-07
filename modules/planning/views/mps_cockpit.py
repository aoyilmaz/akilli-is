import sys
import os
from datetime import date, datetime, timedelta

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QTreeView,
    QTableView,
    QGroupBox,
    QLabel,
    QProgressBar,
    QComboBox,
    QPushButton,
    QHeaderView,
    QMessageBox,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
)
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, pyqtSignal
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QColor, QBrush, QFont
import qtawesome as qta

from ui.components.page_header import PageHeader
from config.icons import ICONS

# Servisler
try:
    from modules.planning.services import MPSService
    from modules.inventory.services.base import ItemService
    from database.models.production import ProductionPlanStatus
except ImportError:
    MPSService = None
    ItemService = None


# -----------------------------------------------------------------------------
# 1. Custom MPS Grid Model (Merkezi Planlama Izgarası Modeli)
# -----------------------------------------------------------------------------
class MPSGridModel(QAbstractTableModel):
    """
    MPS Izgarası için özel model.
    Satırlar: Brüt İhtiyaç, Beklenen Girişler, Projeksiyon Stok, MPS (Planlanan)
    Sütunlar: Satır Tipi + 6 Hafta
    """

    # (Hafta İndeksi, Yeni Değer)
    mps_updated = pyqtSignal(int, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.num_periods = 6
        self.headers = ["Satır Tipi"] + [
            f"Hafta {i+1}" for i in range(self.num_periods)
        ]
        self.period_dates = []  # Her sütunun tarih karşılığı (ISO format)

        # Sabit satır başlıkları
        self.row_types = [
            "Brüt İhtiyaç",
            "Beklenen Girişler",
            "Projeksiyon Stok",
            "MPS (PLANLANAN)",
        ]

        # Veri Matrisi (4 satır x N sütun)
        self.data_matrix = [[0] * self.num_periods for _ in range(4)]
        self.initial_stock = 0
        self.risks = ["none"] * self.num_periods
        self.safety_stock = 0.0

    def set_data(self, data: dict):
        """Servisten gelen veriyi modele yükle"""
        self.beginResetModel()

        # Headerları güncelle
        if "periods" in data:
            self.headers = ["Satır Tipi"] + data["periods"]
            self.period_dates = data.get("period_dates", [])
            self.num_periods = len(data["periods"])

        # Matrisi sıfırla ve doldur
        self.data_matrix = [[0] * self.num_periods for _ in range(4)]

        self.data_matrix[0] = data.get("demand", [0] * self.num_periods)
        self.data_matrix[1] = data.get("incoming", [0] * self.num_periods)
        self.data_matrix[3] = data.get("mps", [0] * self.num_periods)

        # Projeksiyon stok
        self.data_matrix[2] = data.get("projected_stock", [0] * self.num_periods)

        # Risk ve Emniyet Stoğu
        self.risks = data.get("risks", ["none"] * self.num_periods)
        self.safety_stock = data.get("safety_stock", 0.0)

        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self.row_types)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        # İlk sütun: Satır Başlıkları
        if col == 0:
            if role == Qt.ItemDataRole.DisplayRole:
                return self.row_types[row]
            elif role == Qt.ItemDataRole.FontRole:
                f = QFont()
                f.setBold(True)
                return f
            return None

        # Veri sütunları (col-1 çünkü 0. index başlık)
        data_col = col - 1

        if data_col >= self.num_periods:
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            val = self.data_matrix[row][data_col]
            if row == 2 and val < 0:
                return f"{val} !!"
            return str(val)

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            if section < len(self.headers):
                return self.headers[section]
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        # Sadece MPS satırı (index 3) ve veri sütunları (col > 0) düzenlenebilir
        if index.row() == 3 and index.column() > 0:
            return (
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsEditable
            )

        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if index.isValid() and role == Qt.ItemDataRole.EditRole:
            row = index.row()
            col = index.column()

            if row == 3 and col > 0:
                try:
                    new_val = float(value)
                    data_col = col - 1

                    self.data_matrix[row][data_col] = new_val
                    self.recalculate_projections()  # Client side update

                    self.dataChanged.emit(index, index)

                    # Projeksiyon satırını güncelle
                    proj_start = self.index(2, 1)
                    proj_end = self.index(2, self.num_periods)
                    self.dataChanged.emit(proj_start, proj_end)

                    # Sinyal gönder (View yakalasın ve servise yazsın)
                    self.mps_updated.emit(data_col, new_val)

                    return True
                except ValueError:
                    return False
        return False

    def recalculate_projections(self):
        """Client-side basit hesaplama (görsel hız için)"""
        # Not: Initial stock bilgisini servisten alıp saklamamız lazım.
        # Bu örnekte projected_stock[0] üzerinden geri mühendislik veya
        # önceki değerden fark alarak gidilebilir.
        # Basitlik için: Servis her save sonrası refresh yaparsa data tutarlı olur.
        pass


# -----------------------------------------------------------------------------
# 2. Custom Delegate
# -----------------------------------------------------------------------------
from PyQt6.QtWidgets import QStyledItemDelegate


class MPSDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        row = index.row()
        col = index.column()

        if col > 0:
            if row == 3:  # MPS Satırı
                # 60, 60, 65 -> #3c3c41
                option.backgroundBrush = QBrush(QColor(60, 60, 65))

            if row == 2:  # Projeksiyon
                model = index.model()
                if hasattr(model, "risks") and (col - 1) < len(model.risks):
                    risk = model.risks[col - 1]
                    if risk == "critical":
                        option.backgroundBrush = QBrush(QColor("#4d0000"))
                        option.palette.setColor(
                            option.palette.ColorGroup.Normal,
                            option.palette.ColorRole.Text,
                            QColor("white"),
                        )
                    elif risk == "warning":
                        option.backgroundBrush = QBrush(QColor("#4d4d00"))
                        option.palette.setColor(
                            option.palette.ColorGroup.Normal,
                            option.palette.ColorRole.Text,
                            QColor("white"),
                        )


# -----------------------------------------------------------------------------
# Capacity Widgets
# -----------------------------------------------------------------------------


class CapacityHeatmapWidget(QFrame):
    """
    İş istasyonu bazlı periyodik doluluk ısı haritası.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: transparent;")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)

        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setStyleSheet(
            """
            QTableWidget {
                border: none;
                gridline-color: #f0f0f0;
            }
        """
        )
        self.layout.addWidget(self.table)

    def set_data(self, data: dict):
        """Service'den gelen veriyi yükle"""
        if not data or not data.get("periods"):
            return

        periods = data["periods"]
        stations = data["stations"]

        self.table.setColumnCount(len(periods) + 1)
        self.table.setRowCount(len(stations))

        # Headers
        headers = ["İş Merkezi"] + periods
        self.table.setHorizontalHeaderLabels(headers)

        for r, station in enumerate(stations):
            # İstasyon Adı
            name_item = QTableWidgetItem(station["name"])
            name_item.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            self.table.setItem(r, 0, name_item)

            # Doluluklar
            for c, util in enumerate(station["utilizations"]):
                util_item = QTableWidgetItem(f"%{int(util)}")
                util_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # Renklendirme
                if util >= 100:
                    bg_color = QColor("#4d0000")  # Koyu Kırmızı
                    text_color = QColor("white")
                elif util >= 85:
                    bg_color = QColor(
                        "#4d4d00"
                    )  # Koyu Sarı/Turuncu (Kendi temamıza uygun)
                    text_color = QColor("white")
                elif util > 0:
                    bg_color = QColor("#223322")  # Koyu Yeşil (Dark theme uyumlu ise)
                    text_color = QColor("#ffffff")
                else:
                    bg_color = QColor("transparent")
                    text_color = QColor("#808080")

                util_item.setBackground(QBrush(bg_color))
                util_item.setForeground(QBrush(text_color))
                self.table.setItem(r, c + 1, util_item)


# -----------------------------------------------------------------------------
# 3. Main MPS Page Widget
# -----------------------------------------------------------------------------
class MPSCockpitPage(QWidget):
    def __init__(self):
        super().__init__()
        self.mps_service = None
        self.item_service = None
        self.current_plan_id = None
        self.current_item_id = None

        self.setup_ui()
        self.init_services()

    def init_services(self):
        if MPSService and ItemService:
            self.mps_service = MPSService()
            self.item_service = ItemService()
            self.setup_tree_data()
            self._ensure_active_plan()
        else:
            QMessageBox.critical(self, "Hata", "Servisler yüklenemedi!")

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 1. Page Header (Standart Bileşen)
        self.header = PageHeader(
            title="Ana Üretim Çizelgeleme (MPS) Merkezi",
            icon=ICONS.CHART_BAR if hasattr(ICONS, "CHART_BAR") else "ph.chart-bar",
            show_search=False,
            show_add=False,
            show_filter=False,  # Custom toolbar kullanacağız
            parent=self,
        )
        self.header.refresh_clicked.connect(self.refresh_data)
        main_layout.addWidget(self.header)

        # 2. Custom Toolbar (Filtreler ve Aksiyon Butonları)
        toolbar_container = QGroupBox()
        toolbar_container.setStyleSheet(
            "QGroupBox { border: none; padding: 0px; margin: 0px; }"
        )
        toolbar_layout = QHBoxLayout(toolbar_container)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(12)

        # Filtreler
        toolbar_layout.addWidget(QLabel("Dönem:"))
        self.combo_period = QComboBox()
        self.combo_period.addItems(
            ["Haftalık Görünüm", "6 Haftalık Görünüm", "Aylık Görünüm"]
        )
        self.combo_period.setFixedWidth(150)
        toolbar_layout.addWidget(self.combo_period)

        toolbar_layout.addWidget(QLabel("Hat:"))
        self.combo_line = QComboBox()
        self.combo_line.addItems(
            ["Tüm Hatlar", "PVC Hattı", "Alüminyum Hattı"]
        )  # Dummy
        self.combo_line.setFixedWidth(150)
        toolbar_layout.addWidget(self.combo_line)

        toolbar_layout.addStretch()

        # Butonlar
        btn_mrp = QPushButton("MRP ÇALIŞTIR")
        btn_mrp.setIcon(qta.icon("ph.gear", color="white"))
        btn_mrp.setStyleSheet(
            """
            QPushButton {
                background-color: #007acc; 
                color: white; 
                font-weight: bold; 
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #0062a3; }
        """
        )
        # TODO: Connect MRP logic
        btn_mrp.clicked.connect(self._run_mrp)

        btn_approve = QPushButton("PLANI ONAYLA")
        btn_approve.setIcon(qta.icon("ph.check", color="white"))
        btn_approve.setStyleSheet(
            """
            QPushButton {
                background-color: #2da44e; 
                color: white; 
                font-weight: bold; 
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #24823d; }
        """
        )
        btn_approve.clicked.connect(self._approve_plan)

        btn_variance = QPushButton("SAPMA RAPORU")
        btn_variance.setIcon(qta.icon("ph.chart-line-up", color="white"))
        btn_variance.setStyleSheet(
            """
            QPushButton {
                background-color: #6e5494; 
                color: white; 
                font-weight: bold; 
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #5a447a; }
        """
        )
        btn_variance.clicked.connect(self._show_variance_report)

        toolbar_layout.addWidget(btn_mrp)
        toolbar_layout.addWidget(btn_approve)
        toolbar_layout.addWidget(btn_variance)

        main_layout.addWidget(toolbar_container)

        # 3. Main Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Sol Panel: Ürün Ağacı
        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setMinimumWidth(220)
        # Sinyal bağlantısı setup_tree_data içinde yapılacak (model atandıktan sonra)

        # Sağ Panel: Merkezi Planlama Izgarası
        self.grid_view = QTableView()
        self.mps_model = MPSGridModel()
        self.mps_model.mps_updated.connect(self._on_mps_edited)

        self.grid_view.setModel(self.mps_model)
        self.delegate = MPSDelegate(self.grid_view)
        self.grid_view.setItemDelegate(self.delegate)

        self.grid_view.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.grid_view.verticalHeader().setVisible(False)
        self.grid_view.setAlternatingRowColors(True)
        self.grid_view.setStyleSheet(
            "QTableView { selection-background-color: #404040; }"
        )

        splitter.addWidget(self.tree_view)
        splitter.addWidget(self.grid_view)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)

        main_layout.addWidget(splitter)

        capacity_group = QGroupBox("KAPASİTE VE DARBOĞAZ ANALİZİ")
        capacity_group.setMinimumHeight(250)
        self.cap_layout = QVBoxLayout()
        self.cap_layout.setSpacing(8)

        self.cap_heatmap = CapacityHeatmapWidget()
        self.cap_layout.addWidget(self.cap_heatmap)

        capacity_group.setLayout(self.cap_layout)
        main_layout.addWidget(capacity_group)

    def _ensure_active_plan(self):
        """Aktif veya taslak planı bul, yoksa oluştur"""
        if not self.mps_service:
            return

        try:
            # Şimdilik basitçe: En son oluşturulan taslak planı al
            # Yoksa bu hafta için yeni oluştur
            plans = self.mps_service.get_all(status=ProductionPlanStatus.DRAFT)

            today = date.today()
            if plans:
                self.current_plan_id = plans[0].id
                # Başlık bilgisini güncelle (opsiyonel)
            else:
                # Yeni plan oluştur (Önümüzdeki 6 hafta için)
                start_date = today
                end_date = start_date + timedelta(weeks=6)
                new_plan = self.mps_service.create_plan(
                    period_start=start_date,
                    period_end=end_date,
                    name=f"MPS {start_date.strftime('%Y-%m')}",
                )
                self.current_plan_id = new_plan.id

        except Exception as e:
            print(f"Plan yükleme hatası: {e}")

    def setup_tree_data(self):
        if not self.item_service:
            return

        model = QStandardItemModel()
        root = model.invisibleRootItem()

        # Ürünleri çek ve kategorize et (Basitçe Items altında listele)
        # İdealde kategori ağacı kurulmalı ama şimdilik düz liste

        try:
            items = self.item_service.get_all(active_only=True)

            # Gruplama
            groups = {
                "manufactured": QStandardItem("Mamuller"),
                "semi_finished": QStandardItem("Yarı Mamuller"),
                "raw": QStandardItem("Hammadde"),
            }

            # İkonlar
            groups["manufactured"].setIcon(qta.icon("ph.package", color="#d4d4d4"))
            groups["semi_finished"].setIcon(qta.icon("ph.stack", color="#d4d4d4"))
            groups["raw"].setIcon(qta.icon("ph.cube", color="#d4d4d4"))

            # Grupları köke ekle
            root.appendRow(groups["manufactured"])
            root.appendRow(groups["semi_finished"])
            # Hammadde MPS'de planlanmaz genelde ama gösterelim

            for item in items:
                # item_type Enum veya string olabilir, kontrol et
                itype = (
                    item.item_type.value
                    if hasattr(item.item_type, "value")
                    else str(item.item_type)
                )

                if itype in groups:
                    child = QStandardItem(f"{item.name} ({item.code})")
                    child.setData(item.id, Qt.ItemDataRole.UserRole)
                    child.setEditable(False)
                    groups[itype].appendRow(child)

            self.tree_view.setModel(model)
            self.tree_view.expandAll()

            # Model set edildikten sonra selection model oluşur
            if self.tree_view.selectionModel():
                self.tree_view.selectionModel().selectionChanged.connect(
                    self._on_item_selected
                )

        except Exception as e:
            print(f"Ağaç veri hatası: {e}")

    def _on_item_selected(self, selected, deselected):
        indexes = selected.indexes()
        if not indexes:
            return

        index = indexes[0]
        item_id = index.data(Qt.ItemDataRole.UserRole)

        if item_id:
            self.current_item_id = item_id
            self.load_grid_data()
        else:
            self.current_item_id = None
            # Grid temizle
            self.mps_model.set_data({})

    def load_grid_data(self):
        if not self.mps_service or not self.current_plan_id or not self.current_item_id:
            return

        try:
            # Grid verisini servisten çek
            start_date = date.today()  # Veya plan başlangıcı

            data = self.mps_service.get_mps_grid_data(
                plan_id=self.current_plan_id,
                item_id=self.current_item_id,
                start_date=start_date,
                num_periods=6,
            )

            self.mps_model.set_data(data)
            self.load_capacity_data()

        except Exception as e:
            print(f"Grid yükleme hatası: {e}")

    def load_capacity_data(self):
        """Kapasite analiz verilerini yükle"""
        if not self.mps_service or not self.current_plan_id:
            return

        try:
            # Periyot bazlı veriyi çek
            data = self.mps_service.get_period_capacity_analysis(self.current_plan_id)
            if hasattr(self, "cap_heatmap"):
                self.cap_heatmap.set_data(data)
        except Exception as e:
            print(f"Kapasite yükleme hatası: {e}")

            if not data:
                lbl = QLabel("Kapasite verisi yok veya plan boş.")
                lbl.setStyleSheet("color: gray; font-style: italic;")
                self.cap_layout.addWidget(lbl)
                return

            for item in data:
                # "Montaj (120/100 sa)" gibi detay
                name = f"{item['station_name']} ({int(item['total_load_hours'])}/{int(item['available_hours'])} sa)"
                utilization = item["utilization"]
                self.cap_layout.addLayout(self.create_capacity_row(name, utilization))

        except Exception as e:
            print(f"Kapasite yükleme hatası: {e}")

    def _on_mps_edited(self, col_index, new_value):
        """Grid üzerinde MPS hücresi değiştiğinde"""
        if not self.mps_service or not self.current_plan_id or not self.current_item_id:
            return

        try:
            # Kolon indeksinden tarihi bul
            # Modelde saklanan tarihler string (ISO) geliyor
            date_str = self.mps_model.period_dates[col_index]
            target_date = datetime.fromisoformat(date_str).date()

            # Servise kaydet
            self.mps_service.update_mps_quantity(
                plan_id=self.current_plan_id,
                item_id=self.current_item_id,
                target_date=target_date,
                quantity=new_value,
            )

            # Verileri tazelemeye gerek yok (optimistic UI),
            # ama tam hesaplama için beklenebilir.

        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Kayıt başarısız: {e}")

    def refresh_data(self):
        self.setup_tree_data()
        self.load_grid_data()

    def _approve_plan(self):
        if not self.current_plan_id:
            return

        reply = QMessageBox.question(
            self,
            "Onay",
            "Bu planı onaylamak istediğinize emin misiniz? Onaylanan plan iş emirlerine dönüştürülebilir.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                from core.user_context import get_current_user_id

                user_id = get_current_user_id() or 1
                self.mps_service.approve_plan(self.current_plan_id, user_id)
                QMessageBox.information(
                    self, "Başarılı", "Plan onaylandı ve hammadde rezervasyonu yapıldı!"
                )
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Plan onaylanamadı: {str(e)}")

    def create_capacity_row(self, name, percentage):
        layout = QHBoxLayout()

        lbl_name = QLabel(name)
        lbl_name.setFixedWidth(250)

        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(min(percentage, 100))
        progress.setTextVisible(True)
        progress.setFormat(f"%{percentage}")

        if percentage > 100:
            lbl_name.setText(f"{name} - !!! DARBOĞAZ !!!")
            lbl_name.setStyleSheet("color: #ff4d4d; font-weight: bold;")
            progress.setStyleSheet(
                """
                QProgressBar {
                    border: 1px solid #444; border-radius: 4px; text-align: center;
                    background-color: #252526; color: white;
                }
                QProgressBar::chunk { background-color: #ff3333; }
            """
            )
        else:
            progress.setStyleSheet(
                """
                QProgressBar {
                    border: 1px solid #444; border-radius: 4px; text-align: center;
                    background-color: #252526; color: white;
                }
                QProgressBar::chunk { background-color: #2da44e; }
            """
            )

        layout.addWidget(lbl_name)
        layout.addWidget(progress)
        return layout

    def _show_variance_report(self):
        """Sapma raporu ekranını aç"""
        try:
            from modules.reports.views.planning_variance_report import (
                PlanningVarianceDialog,
            )

            dialog = PlanningVarianceDialog(self)
            dialog.exec()
        except ImportError as e:
            QMessageBox.warning(self, "Hata", f"Rapor modülü bulunamadı: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Rapor açılırken hata oluştu: {e}")

    def _run_mrp(self):
        """MRP ve Çizelgeleme Mantığını Çalıştır"""
        if not self.current_plan_id:
            QMessageBox.warning(self, "Uyarı", "Aktif bir plan bulunamadı!")
            return

        try:
            from PyQt6.QtWidgets import QApplication

            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

            # MRP / Backward Scheduling Çalıştır
            self.mps_service.backward_schedule_all(
                self.current_plan_id, check_capacity=True
            )

            # Verileri tazele
            self.refresh_data()

            QApplication.restoreOverrideCursor()
            QMessageBox.information(
                self,
                "Başarılı",
                "MRP hesaplaması ve çizelgeleme tamamlandı.\nKapasite ve tarih kısıtları kontrol edildi.",
            )

        except Exception as e:
            from PyQt6.QtWidgets import QApplication

            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Hata", f"MRP Çalıştırma Hatası: {e}")


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    # Temayı yükle
    app.setStyleSheet(
        """
        QWidget { background-color: #1e1e1e; color: #d4d4d4; }
        QHeaderView::section { background-color: #333; color: white; border: 1px solid #444; }
        QTreeView { background-color: #252526; border: 1px solid #333; }
        QTreeView::item { padding: 4px; }
        QTreeView::item:selected { background-color: #37373d; }
        QTableView { background-color: #252526; gridline-color: #444; border: 1px solid #333; }
        QGroupBox { border: 1px solid #444; margin-top: 20px; font-weight: bold; border-radius: 4px; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        QComboBox { background-color: #333; border: 1px solid #555; padding: 4px; color: white; }
    """
    )
    window = MPSCockpitPage()
    window.resize(1100, 750)
    window.show()
    sys.exit(app.exec())
