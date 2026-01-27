"""
Akıllı İş - Operasyon Taşıma Çakışma Diyaloğu

Gantt şemasında sürükle-bırak ile operasyon taşındığında
çakışma varsa kullanıcıya seçenekler sunar.
"""

from typing import List, Dict
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QButtonGroup,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

from config.styles import WARNING, WARNING_BG, ACCENT

# WARNING_TEXT için fallback (styles.py'da tanımlı değil)
WARNING_TEXT = "#fbbf24"  # Amber text for warnings


class MoveConflictDialog(QDialog):
    """
    Operasyon taşıma çakışma diyaloğu.

    Kullanıcıya üç seçenek sunar:
    1. Diğerlerini Kaydır (shift): Çakışan operasyonları ileri kaydır
    2. Araya Sıkıştır (insert): Mümkünse araya yerleştir, değilse kaydır
    3. İptal: Taşımayı iptal et
    """

    RESOLUTION_SHIFT = "shift"
    RESOLUTION_INSERT = "insert"
    RESOLUTION_CANCEL = "cancel"

    def __init__(
        self,
        operation_id: int,
        conflicts: List[Dict],
        warnings: List[str] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.operation_id = operation_id
        self.conflicts = conflicts
        self.warnings = warnings or []
        self.selected_resolution = None

        self.setWindowTitle("Planlama Çakışması")
        self.setMinimumWidth(500)
        self.setMinimumHeight(350)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Başlık
        title = QLabel("⚠️ Operasyon Taşıma Çakışması")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Açıklama
        conflict_count = len(self.conflicts)
        desc = QLabel(
            f"Bu operasyonu taşımak <b>{conflict_count}</b> diğer operasyonla çakışacak."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Uyarılar
        if self.warnings:
            warning_frame = QFrame()
            warning_frame.setStyleSheet(
                f"background-color: {WARNING_BG}; "
                f"border: 1px solid {WARNING}; "
                "border-radius: 4px; padding: 8px;"
            )
            warning_layout = QVBoxLayout(warning_frame)
            warning_layout.setContentsMargins(8, 8, 8, 8)
            warning_layout.setSpacing(4)

            for warning in self.warnings:
                warn_label = QLabel(f"⚠ {warning}")
                warn_label.setStyleSheet(f"color: {WARNING_TEXT};")
                warning_layout.addWidget(warn_label)

            layout.addWidget(warning_frame)

        # Çakışma listesi
        if self.conflicts:
            conflict_group = QGroupBox("Etkilenen Operasyonlar")
            conflict_layout = QVBoxLayout(conflict_group)

            self.conflict_table = QTableWidget()
            self.conflict_table.setColumnCount(4)
            self.conflict_table.setHorizontalHeaderLabels([
                "İş Emri", "Operasyon", "Başlangıç", "Bitiş"
            ])
            self.conflict_table.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeMode.Stretch
            )
            self.conflict_table.setRowCount(len(self.conflicts))
            self.conflict_table.setMaximumHeight(150)

            for row, conflict in enumerate(self.conflicts):
                self.conflict_table.setItem(
                    row, 0, QTableWidgetItem(conflict.get("work_order_no", ""))
                )
                self.conflict_table.setItem(
                    row, 1, QTableWidgetItem(conflict.get("operation_name", ""))
                )

                # Tarihleri formatla
                start = conflict.get("current_start", "")
                end = conflict.get("current_end", "")
                if start:
                    start = start.replace("T", " ")[:16]
                if end:
                    end = end.replace("T", " ")[:16]

                self.conflict_table.setItem(row, 2, QTableWidgetItem(start))
                self.conflict_table.setItem(row, 3, QTableWidgetItem(end))

            conflict_layout.addWidget(self.conflict_table)
            layout.addWidget(conflict_group)

        # Çözüm seçenekleri
        options_group = QGroupBox("Çözüm Seçin")
        options_layout = QVBoxLayout(options_group)
        options_layout.setSpacing(12)

        self.button_group = QButtonGroup(self)

        # Seçenek 1: Kaydır
        self.shift_radio = QRadioButton("Diğerlerini İleri Kaydır")
        self.shift_radio.setChecked(True)
        shift_desc = QLabel(
            "Çakışan operasyonlar otomatik olarak ileri kaydırılır."
        )
        shift_desc.setStyleSheet("color: #6b7280; margin-left: 24px;")
        options_layout.addWidget(self.shift_radio)
        options_layout.addWidget(shift_desc)
        self.button_group.addButton(self.shift_radio, 1)

        # Seçenek 2: Araya Sıkıştır
        self.insert_radio = QRadioButton("Araya Sıkıştır (Mümkünse)")
        insert_desc = QLabel(
            "Önce boşluk aranır, yoksa kaydırma yapılır."
        )
        insert_desc.setStyleSheet("color: #6b7280; margin-left: 24px;")
        options_layout.addWidget(self.insert_radio)
        options_layout.addWidget(insert_desc)
        self.button_group.addButton(self.insert_radio, 2)

        # Seçenek 3: İptal
        self.cancel_radio = QRadioButton("Taşımayı İptal Et")
        cancel_desc = QLabel("Operasyon mevcut konumunda kalır.")
        cancel_desc.setStyleSheet("color: #6b7280; margin-left: 24px;")
        options_layout.addWidget(self.cancel_radio)
        options_layout.addWidget(cancel_desc)
        self.button_group.addButton(self.cancel_radio, 3)

        layout.addWidget(options_group)

        # Butonlar
        layout.addStretch()

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("Vazgeç")
        cancel_btn.setFixedWidth(100)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        apply_btn = QPushButton("Uygula")
        apply_btn.setFixedWidth(100)
        apply_btn.setDefault(True)
        apply_btn.setStyleSheet(
            f"background-color: {ACCENT}; "
            "color: white; font-weight: bold;"
        )
        apply_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(apply_btn)

        layout.addLayout(buttons_layout)

    def accept(self):
        """Seçilen çözümü kaydet ve kapat."""
        if self.shift_radio.isChecked():
            self.selected_resolution = self.RESOLUTION_SHIFT
        elif self.insert_radio.isChecked():
            self.selected_resolution = self.RESOLUTION_INSERT
        else:
            self.selected_resolution = self.RESOLUTION_CANCEL

        super().accept()

    def reject(self):
        """İptal et."""
        self.selected_resolution = self.RESOLUTION_CANCEL
        super().reject()

    def get_resolution(self) -> str:
        """Seçilen çözümü döndür."""
        return self.selected_resolution or self.RESOLUTION_CANCEL
