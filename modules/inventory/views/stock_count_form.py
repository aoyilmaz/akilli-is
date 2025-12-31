"""
Akıllı İş - Stok Sayımı Form Sayfası
"""

from typing import Optional
from decimal import Decimal
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QDoubleSpinBox, QFrame,
    QFormLayout, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QDateTimeEdit, QAbstractItemView, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDateTime
from PyQt6.QtGui import QColor

from config import COLORS


class StockCountFormPage(QWidget):
    """Stok sayımı formu"""
    
    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()
    completed = pyqtSignal(dict)  # Sayım tamamlandı
    
    def __init__(self, count_data: Optional[dict] = None, parent=None):
        super().__init__(parent)
        self.count_data = count_data
        self.is_edit_mode = count_data is not None
        self.items_data = []
        self.count_lines = []
        self.setup_ui()
        if self.is_edit_mode:
            self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # === Başlık ===
        header_layout = QHBoxLayout()
        
        back_btn = QPushButton("← Geri")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #334155;
                color: #94a3b8;
                padding: 8px 16px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #334155; color: #f8fafc; }
        """)
        back_btn.clicked.connect(self.cancelled.emit)
        header_layout.addWidget(back_btn)
        
        title_text = "Sayım Düzenle" if self.is_edit_mode else "Yeni Stok Sayımı"
        title = QLabel(f"📋 {title_text}")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f8fafc; margin-left: 16px;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Taslak kaydet
        draft_btn = QPushButton("💾 Taslak Kaydet")
        self._style_button(draft_btn)
        draft_btn.clicked.connect(lambda: self._on_save("draft"))
        header_layout.addWidget(draft_btn)
        
        # Tamamla
        complete_btn = QPushButton("✅ Sayımı Tamamla")
        complete_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                border: none;
                color: white;
                font-weight: 600;
                padding: 12px 24px;
                border-radius: 12px;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        complete_btn.clicked.connect(lambda: self._on_save("completed"))
        header_layout.addWidget(complete_btn)
        
        layout.addLayout(header_layout)
        
        # === Sayım Bilgileri ===
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 41, 59, 0.5);
                border: 1px solid #334155;
                border-radius: 12px;
            }
        """)
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(16, 16, 16, 16)
        info_layout.setSpacing(24)
        
        # Sayım No
        no_layout = QVBoxLayout()
        no_layout.addWidget(QLabel("Sayım No"))
        self.count_no_input = QLineEdit()
        self.count_no_input.setPlaceholderText("Otomatik")
        self._style_input(self.count_no_input)
        no_layout.addWidget(self.count_no_input)
        info_layout.addLayout(no_layout)
        
        # Tarih
        date_layout = QVBoxLayout()
        date_layout.addWidget(QLabel("Sayım Tarihi"))
        self.datetime_input = QDateTimeEdit()
        self.datetime_input.setDateTime(QDateTime.currentDateTime())
        self.datetime_input.setCalendarPopup(True)
        self._style_datetime(self.datetime_input)
        date_layout.addWidget(self.datetime_input)
        info_layout.addLayout(date_layout)
        
        # Depo
        wh_layout = QVBoxLayout()
        wh_layout.addWidget(QLabel("Depo *"))
        self.warehouse_combo = QComboBox()
        self._style_combo(self.warehouse_combo)
        self.warehouse_combo.currentIndexChanged.connect(self._on_warehouse_changed)
        wh_layout.addWidget(self.warehouse_combo)
        info_layout.addLayout(wh_layout)
        
        # Kategori Filtresi
        cat_layout = QVBoxLayout()
        cat_layout.addWidget(QLabel("Kategori (Opsiyonel)"))
        self.category_combo = QComboBox()
        self.category_combo.addItem("Tüm Kategoriler", None)
        self._style_combo(self.category_combo)
        cat_layout.addWidget(self.category_combo)
        info_layout.addLayout(cat_layout)
        
        info_layout.addStretch()
        
        layout.addWidget(info_frame)
        
        # === Ürün Yükleme ===
        load_frame = QFrame()
        load_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 41, 59, 0.3);
                border: 1px solid #334155;
                border-radius: 12px;
            }
        """)
        load_layout = QHBoxLayout(load_frame)
        load_layout.setContentsMargins(16, 12, 16, 12)
        
        load_layout.addWidget(QLabel("Ürünleri depodan yükle:"))
        
        load_btn = QPushButton("📦 Ürünleri Yükle")
        load_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                border: none;
                color: white;
                font-weight: 600;
                padding: 10px 20px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #4f46e5; }
        """)
        load_btn.clicked.connect(self._load_items_from_warehouse)
        load_layout.addWidget(load_btn)
        
        load_layout.addStretch()
        
        # Sıfır stokları dahil et
        self.include_zero_check = QCheckBox("Sıfır stokları dahil et")
        self.include_zero_check.setStyleSheet("color: #f8fafc;")
        load_layout.addWidget(self.include_zero_check)
        
        layout.addWidget(load_frame)
        
        # === Sayım Tablosu ===
        self.table = QTableWidget()
        self._setup_table()
        layout.addWidget(self.table)
        
        # === Alt Bilgi ===
        footer_frame = QFrame()
        footer_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 41, 59, 0.5);
                border: 1px solid #334155;
                border-radius: 12px;
            }
        """)
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(16, 12, 16, 12)
        
        # Açıklama
        desc_layout = QVBoxLayout()
        desc_layout.addWidget(QLabel("Açıklama"))
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(60)
        self.description_input.setPlaceholderText("Sayım notu...")
        self._style_textedit(self.description_input)
        desc_layout.addWidget(self.description_input)
        footer_layout.addLayout(desc_layout, 2)
        
        footer_layout.addStretch()
        
        # Özet
        summary_layout = QVBoxLayout()
        summary_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.item_count_label = QLabel("Toplam Ürün: 0")
        self.item_count_label.setStyleSheet("color: #94a3b8;")
        summary_layout.addWidget(self.item_count_label)
        
        self.counted_label = QLabel("Sayılan: 0")
        self.counted_label.setStyleSheet("color: #94a3b8;")
        summary_layout.addWidget(self.counted_label)
        
        self.diff_label = QLabel("Fark: ₺0,00")
        self.diff_label.setStyleSheet("color: #f8fafc; font-size: 18px; font-weight: bold;")
        summary_layout.addWidget(self.diff_label)
        
        footer_layout.addLayout(summary_layout)
        
        layout.addWidget(footer_frame)
        
    def _setup_table(self):
        columns = [
            ("Stok Kodu", 100),
            ("Stok Adı", 200),
            ("Birim", 60),
            ("Sistem Stoku", 110),
            ("Sayılan Miktar", 120),
            ("Fark", 100),
            ("Birim Maliyet", 110),
            ("Fark Tutarı", 120),
            ("Not", 150),
        ]
        
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels([c[0] for c in columns])
        
        header = self.table.horizontalHeader()
        for i, (_, width) in enumerate(columns):
            if i == 1 or i == 8:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                self.table.setColumnWidth(i, width)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(30, 41, 59, 0.3);
                border: 1px solid #334155;
                border-radius: 12px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #334155;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #94a3b8;
                font-weight: 600;
                padding: 10px 8px;
                border: none;
            }
        """)
        
    def load_warehouses(self, warehouses: list):
        """Depoları yükle"""
        self.warehouse_combo.clear()
        self.warehouse_combo.addItem("Seçiniz...", None)
        for wh in warehouses:
            self.warehouse_combo.addItem(f"{wh.code} - {wh.name}", wh.id)
            
    def load_categories(self, categories: list):
        """Kategorileri yükle"""
        self.category_combo.clear()
        self.category_combo.addItem("Tüm Kategoriler", None)
        for cat in categories:
            self.category_combo.addItem(cat.name, cat.id)
            
    def set_items_data(self, items: list):
        """Stok kartlarını ayarla"""
        self.items_data = []
        for item in items:
            self.items_data.append({
                "id": item.id,
                "code": item.code,
                "name": item.name,
                "unit_code": item.unit.code if item.unit else "ADET",
                "unit_cost": float(item.purchase_price or 0),
            })
            
    def _on_warehouse_changed(self):
        """Depo değiştiğinde"""
        # Tabloyu temizle
        self.count_lines = []
        self._refresh_table()
        
    def _load_items_from_warehouse(self):
        """Depodan ürünleri yükle"""
        warehouse_id = self.warehouse_combo.currentData()
        if not warehouse_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir depo seçin!")
            return
        
        # Bu sinyal ile parent'tan veri isteyeceğiz
        # Şimdilik items_data'yı kullan
        include_zero = self.include_zero_check.isChecked()
        category_id = self.category_combo.currentData()
        
        self.count_lines = []
        for item in self.items_data:
            # TODO: Gerçek stok bakiyesini al
            system_qty = 0  # Burası servis'ten gelecek
            
            if not include_zero and system_qty == 0:
                continue
                
            self.count_lines.append({
                "item_id": item["id"],
                "item_code": item["code"],
                "item_name": item["name"],
                "unit_code": item["unit_code"],
                "system_quantity": Decimal(str(system_qty)),
                "counted_quantity": None,  # Henüz sayılmadı
                "unit_cost": Decimal(str(item["unit_cost"])),
                "note": "",
            })
        
        self._refresh_table()
        QMessageBox.information(self, "Bilgi", f"{len(self.count_lines)} ürün yüklendi.")
        
    def _refresh_table(self):
        """Tabloyu yenile"""
        self.table.setRowCount(len(self.count_lines))
        
        total_items = len(self.count_lines)
        counted_items = 0
        total_diff_amount = Decimal(0)
        
        for row, line in enumerate(self.count_lines):
            # Stok Kodu
            code_item = QTableWidgetItem(line["item_code"])
            code_item.setForeground(QColor("#818cf8"))
            self.table.setItem(row, 0, code_item)
            
            # Stok Adı
            self.table.setItem(row, 1, QTableWidgetItem(line["item_name"]))
            
            # Birim
            self.table.setItem(row, 2, QTableWidgetItem(line["unit_code"]))
            
            # Sistem Stoku
            sys_qty = line["system_quantity"]
            sys_item = QTableWidgetItem(f"{sys_qty:,.2f}")
            sys_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 3, sys_item)
            
            # Sayılan Miktar (düzenlenebilir)
            counted_spin = QDoubleSpinBox()
            counted_spin.setRange(0, 999999999)
            counted_spin.setDecimals(4)
            counted_spin.setStyleSheet("""
                QDoubleSpinBox {
                    background-color: #1e293b;
                    border: 1px solid #334155;
                    border-radius: 4px;
                    padding: 4px;
                    color: #f8fafc;
                }
            """)
            if line["counted_quantity"] is not None:
                counted_spin.setValue(float(line["counted_quantity"]))
                counted_items += 1
            counted_spin.valueChanged.connect(lambda val, r=row: self._on_counted_changed(r, val))
            self.table.setCellWidget(row, 4, counted_spin)
            
            # Fark
            if line["counted_quantity"] is not None:
                diff = line["counted_quantity"] - sys_qty
                diff_item = QTableWidgetItem(f"{diff:+,.2f}")
                diff_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if diff < 0:
                    diff_item.setForeground(QColor(COLORS["error"]))
                elif diff > 0:
                    diff_item.setForeground(QColor(COLORS["success"]))
                self.table.setItem(row, 5, diff_item)
                
                # Fark tutarı
                diff_amount = diff * line["unit_cost"]
                total_diff_amount += diff_amount
                amount_item = QTableWidgetItem(f"₺{diff_amount:+,.2f}")
                amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if diff_amount < 0:
                    amount_item.setForeground(QColor(COLORS["error"]))
                elif diff_amount > 0:
                    amount_item.setForeground(QColor(COLORS["success"]))
                self.table.setItem(row, 7, amount_item)
            else:
                self.table.setItem(row, 5, QTableWidgetItem("-"))
                self.table.setItem(row, 7, QTableWidgetItem("-"))
            
            # Birim Maliyet
            cost_item = QTableWidgetItem(f"₺{line['unit_cost']:,.2f}")
            cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 6, cost_item)
            
            # Not
            note_input = QLineEdit()
            note_input.setText(line.get("note", ""))
            note_input.setPlaceholderText("Not...")
            note_input.setStyleSheet("""
                QLineEdit {
                    background-color: #1e293b;
                    border: 1px solid #334155;
                    border-radius: 4px;
                    padding: 4px;
                    color: #f8fafc;
                }
            """)
            note_input.textChanged.connect(lambda text, r=row: self._on_note_changed(r, text))
            self.table.setCellWidget(row, 8, note_input)
        
        # Özeti güncelle
        self.item_count_label.setText(f"Toplam Ürün: {total_items}")
        self.counted_label.setText(f"Sayılan: {counted_items}")
        
        diff_color = COLORS["error"] if total_diff_amount < 0 else COLORS["success"] if total_diff_amount > 0 else "#f8fafc"
        self.diff_label.setText(f"Fark: ₺{total_diff_amount:+,.2f}")
        self.diff_label.setStyleSheet(f"color: {diff_color}; font-size: 18px; font-weight: bold;")
        
    def _on_counted_changed(self, row: int, value: float):
        """Sayılan miktar değiştiğinde"""
        if 0 <= row < len(self.count_lines):
            self.count_lines[row]["counted_quantity"] = Decimal(str(value))
            self._refresh_table()
            
    def _on_note_changed(self, row: int, text: str):
        """Not değiştiğinde"""
        if 0 <= row < len(self.count_lines):
            self.count_lines[row]["note"] = text
            
    def load_data(self):
        """Düzenleme modunda verileri yükle"""
        if not self.count_data:
            return
        
        self.count_no_input.setText(self.count_data.get("count_no", ""))
        self.description_input.setPlainText(self.count_data.get("description", ""))
        
        # Satırları yükle
        self.count_lines = self.count_data.get("lines", [])
        self._refresh_table()
        
    def _on_save(self, status: str):
        """Kaydet"""
        if not self._validate():
            return
        
        data = self.get_form_data()
        data["status"] = status
        
        if status == "completed":
            self.completed.emit(data)
        else:
            self.saved.emit(data)
            
    def _validate(self) -> bool:
        if not self.warehouse_combo.currentData():
            QMessageBox.warning(self, "Uyarı", "Lütfen bir depo seçin!")
            return False
        return True
        
    def get_form_data(self) -> dict:
        return {
            "count_no": self.count_no_input.text().strip() or None,
            "count_date": self.datetime_input.dateTime().toPyDateTime(),
            "warehouse_id": self.warehouse_combo.currentData(),
            "description": self.description_input.toPlainText().strip() or None,
            "lines": self.count_lines,
        }
    
    def _style_input(self, widget):
        widget.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px 12px;
                color: #f8fafc;
            }
            QLineEdit:focus { border-color: #6366f1; }
        """)
        
    def _style_combo(self, widget):
        widget.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px 12px;
                color: #f8fafc;
                min-width: 180px;
            }
        """)
        
    def _style_datetime(self, widget):
        widget.setStyleSheet("""
            QDateTimeEdit {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px 12px;
                color: #f8fafc;
            }
        """)
        
    def _style_textedit(self, widget):
        widget.setStyleSheet("""
            QTextEdit {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 8px;
                color: #f8fafc;
            }
        """)
        
    def _style_button(self, btn):
        btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                border: 1px solid #334155;
                color: #f8fafc;
                padding: 10px 20px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #334155; }
        """)
