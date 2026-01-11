"""
Akıllı İş - MRP Çalıştırma Sayfası
"""

from datetime import date

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QCheckBox,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QMessageBox,
    QProgressBar,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor

from modules.mrp.services import MRPService
from database.models.mrp import MRPRunStatus
from config.styles import (
    BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BG_HOVER, BORDER,
    TEXT_PRIMARY, TEXT_MUTED, ACCENT, SUCCESS, WARNING, ERROR,
    INPUT_BG, INPUT_BORDER, INPUT_FOCUS,
    get_table_style, get_button_style, get_input_style, get_card_style
)

class MRPWorker(QThread):
    """MRP hesaplama thread'i"""

    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(
        self, horizon: int, safety: bool, work_orders: bool, sales_orders: bool
    ):
        super().__init__()
        self.horizon = horizon
        self.safety = safety
        self.work_orders = work_orders
        self.sales_orders = sales_orders

    def run(self):
        try:
            service = MRPService()
            result = service.run_mrp(
                horizon_days=self.horizon,
                consider_safety=self.safety,
                include_work_orders=self.work_orders,
                include_sales_orders=self.sales_orders,
            )
            # Session kapatmadan önce gerekli bilgileri al
            run_data = {
                "id": result.id,
                "run_no": result.run_no,
                "total_items": result.total_items,
                "items_with_shortage": result.items_with_shortage,
                "total_suggestions": result.total_suggestions,
            }
            service.close()
            self.finished.emit(run_data)
        except Exception as e:
            self.error.emit(str(e))

class MRPRunPage(QWidget):
    """MRP çalıştırma sayfası"""

    mrp_completed = pyqtSignal(int)  # run_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.setup_ui()
        self.load_history()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Başlık
        title = QLabel("MRP Calistir")
        layout.addWidget(title)

        # Parametreler
        params_frame = QFrame()
        params_layout = QVBoxLayout(params_frame)

        # Planlama ufku
        horizon_row = QHBoxLayout()
        horizon_row.addWidget(QLabel("Planlama Ufku:"))
        self.horizon_spin = QSpinBox()
        self.horizon_spin.setRange(7, 365)
        self.horizon_spin.setValue(30)
        self.horizon_spin.setSuffix(" gün")
        horizon_row.addWidget(self.horizon_spin)
        horizon_row.addStretch()
        params_layout.addLayout(horizon_row)

        # Checkboxlar
        self.safety_check = QCheckBox("Emniyet stoğunu dahil et")
        self.safety_check.setChecked(True)
        params_layout.addWidget(self.safety_check)

        self.wo_check = QCheckBox("İş emirlerini dahil et")
        self.wo_check.setChecked(True)
        params_layout.addWidget(self.wo_check)

        self.so_check = QCheckBox("Satış siparişlerini dahil et")
        self.so_check.setChecked(True)
        params_layout.addWidget(self.so_check)

        # Çalıştır butonu
        btn_row = QHBoxLayout()
        self.run_btn = QPushButton("MRP Calistir")
        self.run_btn.clicked.connect(self._run_mrp)
        btn_row.addWidget(self.run_btn)
        btn_row.addStretch()
        params_layout.addLayout(btn_row)

        # Progress
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        params_layout.addWidget(self.progress)

        layout.addWidget(params_frame)

        # Geçmiş çalışmalar
        history_label = QLabel("Gecmis Calismalar")
        layout.addWidget(history_label)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels(
            ["Çalışma No", "Tarih", "Ufuk", "Toplam", "Eksik", "Durum"]
        )

        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.history_table.setColumnWidth(1, 150)
        self.history_table.setColumnWidth(2, 80)
        self.history_table.setColumnWidth(3, 80)
        self.history_table.setColumnWidth(4, 80)
        self.history_table.setColumnWidth(5, 100)

        self.history_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.doubleClicked.connect(self._on_history_double_click)
        layout.addWidget(self.history_table)

    def _run_mrp(self):
        """MRP çalıştır"""
        self.run_btn.setEnabled(False)
        self.progress.setVisible(True)

        self.worker = MRPWorker(
            horizon=self.horizon_spin.value(),
            safety=self.safety_check.isChecked(),
            work_orders=self.wo_check.isChecked(),
            sales_orders=self.so_check.isChecked(),
        )
        self.worker.finished.connect(self._on_mrp_finished)
        self.worker.error.connect(self._on_mrp_error)
        self.worker.start()

    def _on_mrp_finished(self, run_data):
        """MRP tamamlandı"""
        self.run_btn.setEnabled(True)
        self.progress.setVisible(False)

        self.load_history()

        QMessageBox.information(
            self,
            "MRP Tamamlandı",
            f"Çalışma: {run_data['run_no']}\n\n"
            f"Toplam Ürün: {run_data['total_items']}\n"
            f"Eksik Olan: {run_data['items_with_shortage']}\n"
            f"Öneri Sayısı: {run_data['total_suggestions']}",
        )

        self.mrp_completed.emit(run_data["id"])

    def _on_mrp_error(self, error):
        """MRP hatası"""
        self.run_btn.setEnabled(True)
        self.progress.setVisible(False)

        QMessageBox.critical(self, "Hata", f"MRP çalıştırılırken hata:\n{error}")

    def load_history(self):
        """Geçmiş çalışmaları yükle"""
        try:
            service = MRPService()
            runs = service.get_all_runs(limit=20)
            service.close()

            self.history_table.setRowCount(len(runs))
            for row, run in enumerate(runs):
                # No
                no_item = QTableWidgetItem(run.run_no)
                no_item.setData(Qt.ItemDataRole.UserRole, run.id)
                self.history_table.setItem(row, 0, no_item)

                # Tarih
                date_str = run.run_date.strftime("%d.%m.%Y %H:%M")
                self.history_table.setItem(row, 1, QTableWidgetItem(date_str))

                # Ufuk
                self.history_table.setItem(
                    row, 2, QTableWidgetItem(f"{run.planning_horizon_days} gün")
                )

                # Toplam
                self.history_table.setItem(
                    row, 3, QTableWidgetItem(str(run.total_items))
                )

                # Eksik
                shortage_item = QTableWidgetItem(str(run.items_with_shortage))
                if run.items_with_shortage > 0:
                    shortage_item.setForeground(QColor(ERROR))
                self.history_table.setItem(row, 4, shortage_item)

                # Durum
                status_text = {
                    MRPRunStatus.PENDING: "Bekliyor",
                    MRPRunStatus.COMPLETED: "Tamamlandı",
                    MRPRunStatus.APPLIED: "Uygulandı",
                    MRPRunStatus.CANCELLED: "İptal",
                }.get(run.status, "")
                status_item = QTableWidgetItem(status_text)
                if run.status == MRPRunStatus.COMPLETED:
                    status_item.setForeground(QColor(SUCCESS))
                self.history_table.setItem(row, 5, status_item)

        except Exception as e:
            print(f"History load error: {e}")

    def _on_history_double_click(self, index):
        """Çalışma detayı"""
        row = index.row()
        run_id = self.history_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if run_id:
            self.mrp_completed.emit(run_id)

    def get_selected_run_id(self) -> int:
        """Seçili çalışma ID'si"""
        row = self.history_table.currentRow()
        if row >= 0:
            return self.history_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        return None
