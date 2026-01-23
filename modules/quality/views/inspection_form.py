from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
    QMessageBox,
    QFrame,
    QGridLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor

from database.models.quality import InspectionStatus
from modules.quality.services import QualityService


class InspectionExecutionPage(QWidget):
    completed = pyqtSignal()

    def __init__(self, inspection_id):
        super().__init__()
        self.service = QualityService()
        self.inspection = self.service.get_inspection_by_id(inspection_id)
        self.results_map = {}  # criteria_id -> widget
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header_frame = QFrame()
        header_frame.setFrameShape(QFrame.Shape.StyledPanel)
        h_layout = QGridLayout(header_frame)

        h_layout.addWidget(QLabel("Muayene No:"), 0, 0)
        self.lbl_no = QLabel()
        h_layout.addWidget(self.lbl_no, 0, 1)

        h_layout.addWidget(QLabel("Tarih:"), 0, 2)
        self.lbl_date = QLabel()
        h_layout.addWidget(self.lbl_date, 0, 3)

        h_layout.addWidget(QLabel("Plan (Şablon):"), 1, 0)
        self.lbl_template = QLabel()
        h_layout.addWidget(self.lbl_template, 1, 1)

        h_layout.addWidget(QLabel("Durum:"), 1, 2)
        self.lbl_status = QLabel()
        h_layout.addWidget(self.lbl_status, 1, 3)

        layout.addWidget(header_frame)

        # Criteria Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Kriter", "Standart", "Min", "Max", "Ölçülen Değer", "Sonuç"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.table)

        # Action Buttons
        btn_layout = QHBoxLayout()

        pass_btn = QPushButton("✅ ONAYLA (GEÇTİ)")
        pass_btn.setStyleSheet(
            "background-color: #10b981; color: white; padding: 10px;"
        )
        pass_btn.clicked.connect(
            lambda: self.finish_inspection(InspectionStatus.PASSED)
        )
        btn_layout.addWidget(pass_btn)

        fail_btn = QPushButton("❌ REDDET (KALDI)")
        fail_btn.setStyleSheet(
            "background-color: #ef4444; color: white; padding: 10px;"
        )
        fail_btn.clicked.connect(
            lambda: self.finish_inspection(InspectionStatus.FAILED)
        )
        btn_layout.addWidget(fail_btn)

        layout.addLayout(btn_layout)

    def load_data(self):
        if not self.inspection:
            return

        self.lbl_no.setText(self.inspection.inspection_no)
        self.lbl_date.setText(str(self.inspection.inspection_date))
        self.lbl_status.setText(self.inspection.status.value)
        tmpl = self.inspection.template
        self.lbl_template.setText(tmpl.name if tmpl else "Serbest Kontrol")

        if tmpl:
            self.table.setRowCount(len(tmpl.criteria))
            for row, crit in enumerate(tmpl.criteria):
                self.table.setItem(row, 0, QTableWidgetItem(crit.name))
                self.table.setItem(
                    row,
                    1,
                    QTableWidgetItem(f"{crit.specification or ''} {crit.unit or ''}"),
                )
                self.table.setItem(
                    row, 2, QTableWidgetItem(str(crit.tolerance_min or "-"))
                )
                self.table.setItem(
                    row, 3, QTableWidgetItem(str(crit.tolerance_max or "-"))
                )

                # Input Field
                inp = QLineEdit()
                inp.setPlaceholderText("Değer girin")
                # Store reference to validate/save later
                # We store it in a way we can retrieve by row or criteria_id
                self.results_map[crit.id] = inp
                self.table.setCellWidget(row, 4, inp)

                # Result Indicator
                res_item = QTableWidgetItem("Bekleniyor")
                self.table.setItem(row, 5, res_item)

                # Should connect inputs to auto-validation logic
                inp.textChanged.connect(
                    lambda text, r=row, c=crit: self.validate_row(r, c)
                )

    def validate_row(self, row, criteria):
        inp = self.results_map[criteria.id]
        val_str = inp.text()
        item = self.table.item(row, 5)

        try:
            val = float(val_str)
            passed = True

            if criteria.tolerance_min is not None and val < float(
                criteria.tolerance_min
            ):
                passed = False
            if criteria.tolerance_max is not None and val > float(
                criteria.tolerance_max
            ):
                passed = False

            if passed:
                item.setText("OK")
                item.setForeground(QColor("green"))
            else:
                item.setText("RED")
                item.setForeground(QColor("red"))

        except ValueError:
            item.setText("...")
            item.setForeground(QColor("black"))

    def finish_inspection(self, status):
        # Save results first
        for crit in self.inspection.template.criteria:
            inp = self.results_map.get(crit.id)
            if inp:
                self.service.record_inspection_result(
                    self.inspection.id,
                    crit.id,
                    {
                        "result_value": inp.text(),
                        "is_passed": self.table.item(
                            self.get_row_for_crit(crit), 5
                        ).text()
                        == "OK",
                    },
                )

        self.service.complete_inspection(self.inspection.id, status)
        QMessageBox.information(self, "Bilgi", f"Muayene tamamlandı: {status.value}")
        self.completed.emit()

    def get_row_for_crit(self, crit):
        # Helper to find row index
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text() == crit.name:
                return row
        return 0
