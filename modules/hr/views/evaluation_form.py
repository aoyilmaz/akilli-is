"""
Performans Değerlendirme Formu (Sihirbaz)
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QWidget,
    QLabel,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
    QMessageBox,
    QFormLayout,
    QDoubleSpinBox,
    QInputDialog,
    QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from database.models.performance import (
    EvaluationStatus,
    PerformanceRating,
    PerformanceEvaluation,
)
from config import COLORS


class PerformanceEvaluationForm(QDialog):
    """Değerlendirme Süreç Formu"""

    def __init__(
        self, parent=None, evaluation_id=None, service=None, current_user_id=None
    ):
        super().__init__(parent)
        self.evaluation_id = evaluation_id
        self.service = service
        self.current_user_id = current_user_id

        self.evaluation = None
        if evaluation_id:
            self.evaluation = self.service.get_evaluation(evaluation_id)

        self.setWindowTitle(
            f"Performans Değerlendirme - {self.evaluation.employee.first_name if self.evaluation else ''}"
        )
        self.resize(900, 700)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Üst Bilgi Paneli
        info_frame = QFrame()
        info_frame.setStyleSheet(
            "background-color: #f5f5f5; border-radius: 5px; padding: 10px;"
        )
        info_layout = QHBoxLayout(info_frame)

        if self.evaluation:
            info_layout.addWidget(
                QLabel(
                    f"<b>Çalışan:</b> {self.evaluation.employee.first_name} {self.evaluation.employee.last_name}"
                )
            )
            info_layout.addWidget(
                QLabel(f"<b>Dönem:</b> {self.evaluation.period.name}")
            )
            info_layout.addWidget(
                QLabel(f"<b>Durum:</b> {self.evaluation.status.value}")
            )

        layout.addWidget(info_frame)

        # Sekmeler
        self.tabs = QTabWidget()
        self.overview_tab = QWidget()
        self.goals_tab = QWidget()
        self.competencies_tab = QWidget()
        self.result_tab = QWidget()
        self.approval_tab = QWidget()

        self.setup_overview_tab()
        self.setup_goals_tab()
        self.setup_competencies_tab()
        self.setup_result_tab()
        self.setup_approval_tab()

        self.tabs.addTab(self.overview_tab, "Genel Bakış")
        self.tabs.addTab(self.goals_tab, "Hedefler")
        self.tabs.addTab(self.competencies_tab, "Yetkinlikler")
        self.tabs.addTab(self.result_tab, "Sonuç")
        self.tabs.addTab(self.approval_tab, "Onay")

        layout.addWidget(self.tabs)

        # Alt Butonlar
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Kaydet")
        self.save_btn.clicked.connect(self.save_current_tab)

        self.submit_btn = QPushButton("Gönder / Tamamla")
        self.submit_btn.setStyleSheet(
            f"background-color: {COLORS['success']}; color: white; font-weight: bold;"
        )
        self.submit_btn.clicked.connect(self.submit_process)

        self.close_btn = QPushButton("Kapat")
        self.close_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.submit_btn)
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)

    def setup_overview_tab(self):
        layout = QVBoxLayout(self.overview_tab)
        # Basit özet bilgileri
        form = QFormLayout()
        if self.evaluation:
            form.addRow(
                "Değerlendirici:",
                QLabel(
                    f"{self.evaluation.evaluator.first_name} {self.evaluation.evaluator.last_name}"
                    if self.evaluation.evaluator
                    else "-"
                ),
            )
            form.addRow("Başlangıç:", QLabel(str(self.evaluation.period.start_date)))
            form.addRow("Bitiş:", QLabel(str(self.evaluation.period.end_date)))
        layout.addLayout(form)
        layout.addStretch()

    def setup_goals_tab(self):
        layout = QVBoxLayout(self.goals_tab)

        # Hedef Tablosu
        self.goals_table = QTableWidget()
        self.goals_table.setColumnCount(6)
        self.goals_table.setHorizontalHeaderLabels(
            ["Hedef", "Ağırlık %", "Hedef Değer", "Gerçekleşen", "Başarı %", "Yorum"]
        )
        self.goals_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )

        layout.addWidget(self.goals_table)

        # Hedef Ekleme Butonu (Sadece Taslak aşamasında)
        self.add_goal_btn = QPushButton("+ Hedef Ekle")
        self.add_goal_btn.clicked.connect(self.add_new_goal)
        layout.addWidget(self.add_goal_btn)

        if self.evaluation:
            self.load_goals()

    def setup_competencies_tab(self):
        layout = QVBoxLayout(self.competencies_tab)

        self.comp_table = QTableWidget()
        self.comp_table.setColumnCount(5)
        self.comp_table.setHorizontalHeaderLabels(
            ["Yetkinlik", "Kategori", "Ağırlık", "Öz Puan (1-5)", "Yönetici Puan (1-5)"]
        )
        self.comp_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )

        layout.addWidget(self.comp_table)
        if self.evaluation:
            self.load_competencies()

    def setup_result_tab(self):
        layout = QVBoxLayout(self.result_tab)

        form = QFormLayout()

        self.self_score_lbl = QLabel("-")
        form.addRow("Özdeğerlendirme Puanı:", self.self_score_lbl)

        self.mgr_score_lbl = QLabel("-")
        form.addRow("Yönetici Puanı:", self.mgr_score_lbl)

        self.final_score_spin = QDoubleSpinBox()
        self.final_score_spin.setRange(0, 5)
        self.final_score_spin.setSingleStep(0.1)
        form.addRow("Nihai Puan:", self.final_score_spin)

        self.strengths_txt = QTextEdit()
        form.addRow("Güçlü Yönler:", self.strengths_txt)

        self.areas_txt = QTextEdit()
        form.addRow("Gelişim Alanları:", self.areas_txt)

        layout.addLayout(form)

    def setup_approval_tab(self):
        layout = QVBoxLayout(self.approval_tab)

        form = QFormLayout()
        self.hr_comment_txt = QTextEdit()
        form.addRow("İK Yorumu:", self.hr_comment_txt)

        self.dev_plan_txt = QTextEdit()
        form.addRow("Gelişim Planı:", self.dev_plan_txt)

        layout.addLayout(form)

    # --- Data Loading ---

    def load_goals(self):
        self.goals_table.setRowCount(0)
        for goal in self.evaluation.goals:
            row = self.goals_table.rowCount()
            self.goals_table.insertRow(row)
            self.goals_table.setItem(row, 0, QTableWidgetItem(goal.title))
            self.goals_table.setItem(row, 1, QTableWidgetItem(str(goal.weight)))
            self.goals_table.setItem(
                row, 2, QTableWidgetItem(str(goal.target_value or "-"))
            )
            self.goals_table.setItem(
                row, 3, QTableWidgetItem(str(goal.actual_value or "-"))
            )
            self.goals_table.setItem(
                row, 4, QTableWidgetItem(str(goal.achievement_rate or "-"))
            )
            self.goals_table.setItem(
                row,
                5,
                QTableWidgetItem(goal.employee_comment or goal.manager_comment or ""),
            )

    def load_competencies(self):
        self.comp_table.setRowCount(0)
        for score in self.evaluation.competency_scores:
            row = self.comp_table.rowCount()
            self.comp_table.insertRow(row)
            self.comp_table.setItem(row, 0, QTableWidgetItem(score.competency.name))
            self.comp_table.setItem(
                row, 1, QTableWidgetItem(score.competency.category.value)
            )
            self.comp_table.setItem(
                row, 2, QTableWidgetItem(str(score.competency.weight))
            )

            # Input handling based on role/status could be added here
            self_item = QTableWidgetItem(str(score.self_score or ""))
            mgr_item = QTableWidgetItem(str(score.manager_score or ""))

            self.comp_table.setItem(row, 3, self_item)
            self.comp_table.setItem(row, 4, mgr_item)

    # --- Actions ---

    def add_new_goal(self):
        text, ok = QInputDialog.getText(self, "Hedef Ekle", "Hedef Başlığı:")
        if ok and text:
            try:
                self.service.add_goal(self.evaluation.id, title=text)
                self.load_goals()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))

    def save_current_tab(self):
        # Kaydetme mantığı buraya (şimdilik placeholder)
        QMessageBox.information(
            self, "Bilgi", "Değişiklikler taslak olarak kaydedildi."
        )

    def submit_process(self):
        # Duruma göre işlem yap
        try:
            # self.service.submit_self_evaluation(...) vs.
            QMessageBox.information(self, "Başarılı", "İşlem başarıyla tamamlandı.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
