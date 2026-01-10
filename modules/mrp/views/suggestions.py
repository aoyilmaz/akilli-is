"""
Akıllı İş - MRP Tedarik Önerileri Sayfası
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QMessageBox,
    QComboBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from modules.mrp.services import MRPService
from database.models.mrp import SuggestionType
from config.styles import (
    BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BG_HOVER, BORDER,
    TEXT_PRIMARY, TEXT_MUTED, ACCENT, SUCCESS, WARNING, ERROR, INFO,
    INPUT_BG, INPUT_BORDER, INPUT_FOCUS,
    BTN_SUCCESS_BG, BTN_SUCCESS_HOVER,
    get_table_style, get_button_style, get_input_style
)


class SuggestionsPage(QWidget):
    """Tedarik önerileri sayfası"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_run_id = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Başlık
        header = QHBoxLayout()

        title = QLabel("Tedarik Onerileri")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {TEXT_PRIMARY};")
        header.addWidget(title)

        header.addStretch()

        # Tümünü uygula
        apply_all_btn = QPushButton("Tumunu Uygula")
        apply_all_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {BTN_SUCCESS_BG};
                border: none;
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {BTN_SUCCESS_HOVER}; }}
        """
        )
        apply_all_btn.clicked.connect(self._apply_all)
        header.addWidget(apply_all_btn)

        layout.addLayout(header)

        # Filtre
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Tür:"))

        self.type_filter = QComboBox()
        self.type_filter.addItem("Tümü", None)
        self.type_filter.addItem("🛒 Satınalma", SuggestionType.PURCHASE)
        self.type_filter.addItem("🏭 Üretim", SuggestionType.MANUFACTURE)
        self.type_filter.setStyleSheet(
            f"""
            QComboBox {{
                background-color: {INPUT_BG};
                border: 1px solid {INPUT_BORDER};
                border-radius: 6px;
                padding: 8px;
                color: {TEXT_PRIMARY};
                min-width: 150px;
            }}
            QComboBox:focus {{
                border: 1px solid {INPUT_FOCUS};
            }}
            QComboBox QAbstractItemView {{
                background-color: {BG_SECONDARY};
                border: 1px solid {BORDER};
                selection-background-color: {BG_HOVER};
            }}
        """
        )
        self.type_filter.currentIndexChanged.connect(self._filter_changed)
        filter_row.addWidget(self.type_filter)

        filter_row.addStretch()

        self.count_label = QLabel("0 oneri")
        self.count_label.setStyleSheet(f"color: {TEXT_MUTED};")
        filter_row.addWidget(self.count_label)

        layout.addLayout(filter_row)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            [
                "Ürün Kodu",
                "Ürün Adı",
                "Miktar",
                "Sipariş Tarihi",
                "Tür",
                "Kaynak",
                "Aksiyon",
            ]
        )

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 120)
        self.table.setColumnWidth(6, 100)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(get_table_style())

        layout.addWidget(self.table)

    def load_suggestions(self, run_id: int):
        """Önerileri yükle"""
        self.current_run_id = run_id

        try:
            service = MRPService()
            suggestions = service.get_suggestions(run_id)
            service.close()

            self._populate_table(suggestions)
            self.count_label.setText(f"{len(suggestions)} oneri")

        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Yüklenirken hata:\n{e}")

    def _populate_table(self, suggestions):
        """Tabloyu doldur"""
        self.table.setRowCount(len(suggestions))

        for row, sug in enumerate(suggestions):
            # Ürün kodu
            code_item = QTableWidgetItem(sug.item.code if sug.item else "")
            code_item.setData(Qt.ItemDataRole.UserRole, sug.id)
            self.table.setItem(row, 0, code_item)

            # Ürün adı
            self.table.setItem(
                row, 1, QTableWidgetItem(sug.item.name if sug.item else "")
            )

            # Miktar
            qty_item = QTableWidgetItem(f"{sug.suggested_qty:,.2f}")
            qty_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row, 2, qty_item)

            # Tarih
            date_str = (
                sug.suggested_date.strftime("%d.%m.%Y") if sug.suggested_date else ""
            )
            self.table.setItem(row, 3, QTableWidgetItem(date_str))

            # Tür
            if sug.suggestion_type == SuggestionType.PURCHASE:
                type_text = "Satinalma"
                type_color = INFO
            else:
                type_text = "Uretim"
                type_color = ACCENT
            type_item = QTableWidgetItem(type_text)
            type_item.setForeground(QColor(type_color))
            self.table.setItem(row, 4, type_item)

            # Kaynak
            source_text = sug.demand_source_ref or ""
            self.table.setItem(row, 5, QTableWidgetItem(source_text))

            # Aksiyon butonu
            apply_btn = QPushButton("Uygula")
            apply_btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {BG_TERTIARY};
                    border: 1px solid {BORDER};
                    color: {TEXT_PRIMARY};
                    padding: 6px 12px;
                    border-radius: 4px;
                }}
                QPushButton:hover {{ background-color: {BG_HOVER}; }}
            """
            )
            apply_btn.clicked.connect(
                lambda checked, lid=sug.id: self._apply_single(lid)
            )
            self.table.setCellWidget(row, 6, apply_btn)

    def _apply_single(self, line_id: int):
        """Tek öneriyi uygula"""
        # Kullanıcıya sor
        reply = QMessageBox.question(
            self,
            "Öneriyi Uygula",
            "Sipariş/İş Emri otomatik oluşturulsun mu?\n\n"
            "Evet: Satınalma Talebi veya İş Emri oluşturulur\n"
            "Hayır: Sadece işaretlenir",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        auto_create = reply == QMessageBox.StandardButton.Yes

        try:
            service = MRPService()
            result = service.apply_suggestion(line_id, auto_create=auto_create)
            service.close()

            QMessageBox.information(
                self,
                "Öneri Uygulandı",
                f"Tür: {result.get('type')}\n" f"Bilgi: {result.get('message')}",
            )

            # Yenile
            if self.current_run_id:
                self.load_suggestions(self.current_run_id)

        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))

    def _apply_all(self):
        """Tüm önerileri uygula"""
        if not self.current_run_id:
            return

        # Kullanıcıya sor
        reply = QMessageBox.question(
            self,
            "Tüm Önerileri Uygula",
            "Tüm öneriler için sipariş/iş emri oluşturulsun mu?\n\n"
            "Evet: Otomatik oluşturulur\n"
            "Hayır: Sadece işaretlenir",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
            | QMessageBox.StandardButton.Cancel,
        )

        if reply == QMessageBox.StandardButton.Cancel:
            return

        auto_create = reply == QMessageBox.StandardButton.Yes

        try:
            service = MRPService()
            result = service.apply_all_suggestions(
                self.current_run_id, auto_create=auto_create
            )
            service.close()

            # Sonuç mesajı
            msg = f"Toplam: {result['total']} öneri\n"
            if auto_create:
                msg += f"Satınalma Talebi: {result['purchase_requests']}\n"
                msg += f"İş Emri: {result['work_orders']}\n"
            else:
                msg += "Tümü işaretlendi (sipariş oluşturulmadı)"

            if result.get("errors"):
                msg += f"\n\nHatalar:\n" + "\n".join(result["errors"])

            QMessageBox.information(self, "Tamamlandı", msg)
            self.load_suggestions(self.current_run_id)

        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))

    def _filter_changed(self):
        """Filtre değişti"""
        # TODO: Filtreleme
        pass
