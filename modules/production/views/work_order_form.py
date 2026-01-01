"""
Akıllı İş - İş Emri Form Sayfası
"""

from typing import Optional
from decimal import Decimal
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QDoubleSpinBox, QSpinBox,
    QFrame, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QTabWidget, QGridLayout,
    QDateTimeEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QDateTime
from PyQt6.QtGui import QColor


class WorkOrderFormPage(QWidget):
    """İş emri formu"""
    
    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()
    order_no_requested = pyqtSignal()
    bom_selected = pyqtSignal(int)
    
    def __init__(self, wo_data: Optional[dict] = None, parent=None):
        super().__init__(parent)
        self.wo_data = wo_data
        self.is_edit_mode = wo_data is not None
        self.materials = []
        self.setup_ui()
        if self.is_edit_mode:
            self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Başlık
        header_layout = QHBoxLayout()
        
        back_btn = QPushButton("← Geri")
        back_btn.setStyleSheet("""
            QPushButton { background-color: transparent; border: 1px solid #334155;
                color: #94a3b8; padding: 8px 16px; border-radius: 8px; }
            QPushButton:hover { background-color: #334155; color: #f8fafc; }
        """)
        back_btn.clicked.connect(self.cancelled.emit)
        header_layout.addWidget(back_btn)
        
        title_text = "İş Emri Düzenle" if self.is_edit_mode else "Yeni İş Emri"
        title = QLabel(f"📋 {title_text}")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f8fafc; margin-left: 16px;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        save_btn = QPushButton("💾 Kaydet")
        save_btn.setStyleSheet("""
            QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #a855f7);
                border: none; color: white; font-weight: 600; padding: 12px 24px; border-radius: 12px; }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #9333ea); }
        """)
        save_btn.clicked.connect(self._on_save)
        header_layout.addWidget(save_btn)
        
        layout.addLayout(header_layout)
        
        # Tab Widget
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #334155; border-radius: 12px; background-color: rgba(30, 41, 59, 0.5); }
            QTabBar::tab { background-color: #1e293b; color: #94a3b8; padding: 12px 24px; margin-right: 4px;
                border-top-left-radius: 8px; border-top-right-radius: 8px; }
            QTabBar::tab:selected { background-color: #334155; color: #f8fafc; }
        """)
        
        tabs.addTab(self._create_general_tab(), "📝 Genel Bilgiler")
        tabs.addTab(self._create_materials_tab(), "📦 Malzemeler")
        tabs.addTab(self._create_schedule_tab(), "📅 Planlama")
        
        layout.addWidget(tabs)
        
    def _create_general_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        form_frame = QFrame()
        form_frame.setStyleSheet("QFrame { background-color: rgba(30, 41, 59, 0.3); border: 1px solid #334155; border-radius: 12px; }")
        form_layout = QGridLayout(form_frame)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(16)
        
        # İş Emri No
        form_layout.addWidget(QLabel("İş Emri No *"), 0, 0)
        no_layout = QHBoxLayout()
        self.order_no_input = QLineEdit()
        self.order_no_input.setPlaceholderText("WO202501001")
        self._style_input(self.order_no_input)
        no_layout.addWidget(self.order_no_input)
        
        auto_btn = QPushButton("🔄")
        auto_btn.setFixedSize(40, 40)
        auto_btn.setStyleSheet("QPushButton { background-color: #334155; border: none; border-radius: 8px; } QPushButton:hover { background-color: #475569; }")
        auto_btn.clicked.connect(self.order_no_requested.emit)
        no_layout.addWidget(auto_btn)
        form_layout.addLayout(no_layout, 0, 1)
        
        # Mamul Seçimi
        form_layout.addWidget(QLabel("Mamul *"), 1, 0)
        self.product_combo = QComboBox()
        self._style_combo(self.product_combo)
        self.product_combo.currentIndexChanged.connect(self._on_product_changed)
        form_layout.addWidget(self.product_combo, 1, 1)
        
        # Reçete Seçimi
        form_layout.addWidget(QLabel("Reçete *"), 2, 0)
        self.bom_combo = QComboBox()
        self._style_combo(self.bom_combo)
        self.bom_combo.currentIndexChanged.connect(self._on_bom_changed)
        form_layout.addWidget(self.bom_combo, 2, 1)
        
        # Üretim Miktarı
        form_layout.addWidget(QLabel("Üretim Miktarı *"), 3, 0)
        qty_layout = QHBoxLayout()
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setRange(0.0001, 999999999)
        self.quantity_input.setDecimals(4)
        self.quantity_input.setValue(1)
        self._style_spinbox(self.quantity_input)
        self.quantity_input.valueChanged.connect(self._update_materials)
        qty_layout.addWidget(self.quantity_input)
        
        self.unit_label = QLabel("ADET")
        self.unit_label.setStyleSheet("color: #94a3b8; min-width: 60px;")
        qty_layout.addWidget(self.unit_label)
        form_layout.addLayout(qty_layout, 3, 1)
        
        # Öncelik
        form_layout.addWidget(QLabel("Öncelik"), 4, 0)
        self.priority_combo = QComboBox()
        self.priority_combo.addItem("Düşük", "low")
        self.priority_combo.addItem("Normal", "normal")
        self.priority_combo.addItem("Yüksek", "high")
        self.priority_combo.addItem("Acil", "urgent")
        self.priority_combo.setCurrentIndex(1)
        self._style_combo(self.priority_combo)
        form_layout.addWidget(self.priority_combo, 4, 1)
        
        # Kaynak Depo
        form_layout.addWidget(QLabel("Hammadde Deposu"), 5, 0)
        self.source_warehouse_combo = QComboBox()
        self._style_combo(self.source_warehouse_combo)
        form_layout.addWidget(self.source_warehouse_combo, 5, 1)
        
        # Hedef Depo
        form_layout.addWidget(QLabel("Mamul Deposu"), 6, 0)
        self.target_warehouse_combo = QComboBox()
        self._style_combo(self.target_warehouse_combo)
        form_layout.addWidget(self.target_warehouse_combo, 6, 1)
        
        # Açıklama
        form_layout.addWidget(QLabel("Açıklama"), 7, 0)
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self._style_textedit(self.description_input)
        form_layout.addWidget(self.description_input, 7, 1)
        
        layout.addWidget(form_frame)
        
        # Maliyet özeti
        cost_frame = QFrame()
        cost_frame.setStyleSheet("QFrame { background-color: rgba(16, 185, 129, 0.1); border: 1px solid #10b98140; border-radius: 12px; }")
        cost_layout = QHBoxLayout(cost_frame)
        cost_layout.setContentsMargins(20, 16, 20, 16)
        
        self.material_cost_label = QLabel("Malzeme: ₺0")
        self.material_cost_label.setStyleSheet("color: #10b981; font-weight: 600; background: transparent;")
        cost_layout.addWidget(self.material_cost_label)
        
        cost_layout.addStretch()
        
        self.total_cost_label = QLabel("Toplam Tahmini Maliyet: ₺0")
        self.total_cost_label.setStyleSheet("color: #10b981; font-size: 16px; font-weight: bold; background: transparent;")
        cost_layout.addWidget(self.total_cost_label)
        
        layout.addWidget(cost_frame)
        layout.addStretch()
        
        return tab
        
    def _create_materials_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Bilgi
        info_label = QLabel("ℹ️ Malzemeler seçilen reçeteye göre otomatik hesaplanır")
        info_label.setStyleSheet("color: #94a3b8; background-color: #1e293b; padding: 12px; border-radius: 8px;")
        layout.addWidget(info_label)
        
        # Tablo
        self.materials_table = QTableWidget()
        columns = [
            ("Malzeme Kodu", 120),
            ("Malzeme Adı", 200),
            ("Gerekli Miktar", 120),
            ("Birim", 80),
            ("Mevcut Stok", 120),
            ("Eksik", 100),
            ("Birim Maliyet", 110),
            ("Toplam Maliyet", 120),
        ]
        
        self.materials_table.setColumnCount(len(columns))
        self.materials_table.setHorizontalHeaderLabels([c[0] for c in columns])
        
        header = self.materials_table.horizontalHeader()
        for i, (_, width) in enumerate(columns):
            if i == 1:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                self.materials_table.setColumnWidth(i, width)
        
        self.materials_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.materials_table.verticalHeader().setVisible(False)
        self.materials_table.setStyleSheet("""
            QTableWidget { background-color: rgba(15, 23, 42, 0.5); border: 1px solid #334155; border-radius: 8px; }
            QTableWidget::item { padding: 8px; border-bottom: 1px solid #334155; }
            QTableWidget::item:selected { background-color: rgba(99, 102, 241, 0.2); }
            QHeaderView::section { background-color: #1e293b; color: #94a3b8; font-weight: 600; padding: 8px; border: none; }
        """)
        layout.addWidget(self.materials_table)
        
        # Özet
        summary_layout = QHBoxLayout()
        
        self.materials_count_label = QLabel("Toplam: 0 malzeme")
        self.materials_count_label.setStyleSheet("color: #94a3b8;")
        summary_layout.addWidget(self.materials_count_label)
        
        summary_layout.addStretch()
        
        self.shortage_label = QLabel("")
        self.shortage_label.setStyleSheet("color: #ef4444; font-weight: 600;")
        summary_layout.addWidget(self.shortage_label)
        
        layout.addLayout(summary_layout)
        
        return tab
        
    def _create_schedule_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        form_frame = QFrame()
        form_frame.setStyleSheet("QFrame { background-color: rgba(30, 41, 59, 0.3); border: 1px solid #334155; border-radius: 12px; }")
        form_layout = QGridLayout(form_frame)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(16)
        
        # Planlanan Başlangıç
        form_layout.addWidget(QLabel("Planlanan Başlangıç"), 0, 0)
        self.planned_start_input = QDateTimeEdit()
        self.planned_start_input.setDateTime(QDateTime.currentDateTime())
        self.planned_start_input.setCalendarPopup(True)
        self._style_datetime(self.planned_start_input)
        form_layout.addWidget(self.planned_start_input, 0, 1)
        
        # Planlanan Bitiş
        form_layout.addWidget(QLabel("Planlanan Bitiş"), 1, 0)
        self.planned_end_input = QDateTimeEdit()
        self.planned_end_input.setDateTime(QDateTime.currentDateTime().addDays(1))
        self.planned_end_input.setCalendarPopup(True)
        self._style_datetime(self.planned_end_input)
        form_layout.addWidget(self.planned_end_input, 1, 1)
        
        # Tahmini Süre (bilgi)
        form_layout.addWidget(QLabel("Tahmini Süre"), 2, 0)
        self.estimated_time_label = QLabel("Reçeteden hesaplanacak")
        self.estimated_time_label.setStyleSheet("color: #94a3b8;")
        form_layout.addWidget(self.estimated_time_label, 2, 1)
        
        layout.addWidget(form_frame)
        layout.addStretch()
        
        return tab
        
    def set_products(self, products: list):
        """Mamul listesini ayarla"""
        self.product_combo.clear()
        self.product_combo.addItem("Seçiniz...", None)
        for p in products:
            self.product_combo.addItem(f"{p.code} - {p.name}", p.id)
            
    def set_boms_for_product(self, boms: list):
        """Seçilen mamulün reçetelerini ayarla"""
        self.bom_combo.clear()
        self.bom_combo.addItem("Seçiniz...", None)
        for b in boms:
            status_icon = "✅" if b.status.value == "active" else "🟡"
            self.bom_combo.addItem(f"{status_icon} {b.code} - {b.name}", b.id)
            
    def set_warehouses(self, warehouses: list):
        """Depoları ayarla"""
        self.source_warehouse_combo.clear()
        self.target_warehouse_combo.clear()
        self.source_warehouse_combo.addItem("Seçiniz...", None)
        self.target_warehouse_combo.addItem("Seçiniz...", None)
        for w in warehouses:
            self.source_warehouse_combo.addItem(f"{w.code} - {w.name}", w.id)
            self.target_warehouse_combo.addItem(f"{w.code} - {w.name}", w.id)
            
    def set_generated_order_no(self, order_no: str):
        self.order_no_input.setText(order_no)
        
    def set_bom_materials(self, materials: list):
        """Reçeteden gelen malzemeleri ayarla"""
        self.materials = materials
        self._update_materials()
        
    def _on_product_changed(self):
        """Mamul değiştiğinde"""
        product_id = self.product_combo.currentData()
        if product_id:
            self.bom_selected.emit(product_id)
        else:
            self.bom_combo.clear()
            self.bom_combo.addItem("Önce mamul seçin...", None)
            self.materials = []
            self._update_materials()
            
    def _on_bom_changed(self):
        """Reçete değiştiğinde malzemeleri yükle"""
        bom_id = self.bom_combo.currentData()
        if bom_id:
            # Parent'tan malzemeler alınacak
            pass
            
    def _update_materials(self):
        """Malzeme tablosunu güncelle"""
        quantity = Decimal(str(self.quantity_input.value()))
        
        self.materials_table.setRowCount(len(self.materials))
        
        total_cost = Decimal(0)
        shortage_count = 0
        
        for row, mat in enumerate(self.materials):
            # Malzeme Kodu
            code_item = QTableWidgetItem(mat.get("item_code", ""))
            code_item.setForeground(QColor("#818cf8"))
            self.materials_table.setItem(row, 0, code_item)
            
            # Malzeme Adı
            self.materials_table.setItem(row, 1, QTableWidgetItem(mat.get("item_name", "")))
            
            # Gerekli Miktar - Decimal'e dönüştür
            base_qty = mat.get("quantity", Decimal(0))
            if not isinstance(base_qty, Decimal):
                base_qty = Decimal(str(base_qty))
            required_qty = base_qty * quantity
            req_item = QTableWidgetItem(f"{required_qty:,.4f}")
            req_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.materials_table.setItem(row, 2, req_item)
            
            # Birim
            self.materials_table.setItem(row, 3, QTableWidgetItem(mat.get("unit_code", "ADET")))
            
            # Mevcut Stok - Decimal'e dönüştür
            stock = mat.get("stock", 0)
            if not isinstance(stock, Decimal):
                stock = Decimal(str(stock))
            stock_item = QTableWidgetItem(f"{stock:,.4f}")
            stock_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.materials_table.setItem(row, 4, stock_item)
            
            # Eksik
            shortage = max(Decimal(0), required_qty - stock)
            shortage_item = QTableWidgetItem(f"{shortage:,.4f}" if shortage > 0 else "-")
            shortage_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if shortage > 0:
                shortage_item.setForeground(QColor("#ef4444"))
                shortage_count += 1
            self.materials_table.setItem(row, 5, shortage_item)
            
            # Birim Maliyet - Decimal'e dönüştür
            unit_cost = mat.get("unit_cost", 0)
            if not isinstance(unit_cost, Decimal):
                unit_cost = Decimal(str(unit_cost))
            cost_item = QTableWidgetItem(f"₺{unit_cost:,.2f}")
            cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.materials_table.setItem(row, 6, cost_item)
            
            # Toplam Maliyet
            line_cost = required_qty * unit_cost
            total_cost += line_cost
            line_cost_item = QTableWidgetItem(f"₺{line_cost:,.2f}")
            line_cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            line_cost_item.setForeground(QColor("#10b981"))
            self.materials_table.setItem(row, 7, line_cost_item)
        
        self.materials_count_label.setText(f"Toplam: {len(self.materials)} malzeme")
        self.material_cost_label.setText(f"Malzeme: ₺{total_cost:,.2f}")
        self.total_cost_label.setText(f"Toplam Tahmini Maliyet: ₺{total_cost:,.2f}")
        
        if shortage_count > 0:
            self.shortage_label.setText(f"⚠️ {shortage_count} malzemede stok eksik!")
        else:
            self.shortage_label.setText("")
        
    def load_data(self):
        """Düzenleme modunda verileri yükle"""
        if not self.wo_data:
            return
        
        self.order_no_input.setText(self.wo_data.get("order_no", ""))
        self.description_input.setPlainText(self.wo_data.get("description", ""))
        self.quantity_input.setValue(float(self.wo_data.get("planned_quantity", 1)))
        
        # Tarihler
        if self.wo_data.get("planned_start"):
            self.planned_start_input.setDateTime(QDateTime(self.wo_data["planned_start"]))
        if self.wo_data.get("planned_end"):
            self.planned_end_input.setDateTime(QDateTime(self.wo_data["planned_end"]))
        
    def _on_save(self):
        """Kaydet"""
        order_no = self.order_no_input.text().strip()
        if not order_no:
            QMessageBox.warning(self, "Uyarı", "İş emri numarası zorunludur!")
            return
            
        product_id = self.product_combo.currentData()
        if not product_id:
            QMessageBox.warning(self, "Uyarı", "Mamul seçimi zorunludur!")
            return
            
        bom_id = self.bom_combo.currentData()
        if not bom_id:
            QMessageBox.warning(self, "Uyarı", "Reçete seçimi zorunludur!")
            return
        
        data = {
            "order_no": order_no,
            "description": self.description_input.toPlainText().strip(),
            "item_id": product_id,
            "bom_id": bom_id,
            "planned_quantity": Decimal(str(self.quantity_input.value())),
            "priority": self.priority_combo.currentData(),
            "source_warehouse_id": self.source_warehouse_combo.currentData(),
            "target_warehouse_id": self.target_warehouse_combo.currentData(),
            "planned_start": self.planned_start_input.dateTime().toPyDateTime(),
            "planned_end": self.planned_end_input.dateTime().toPyDateTime(),
        }
        
        if self.is_edit_mode and self.wo_data:
            data["id"] = self.wo_data.get("id")
        
        self.saved.emit(data)
        
    def _style_input(self, w):
        w.setStyleSheet("QLineEdit { background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 10px; color: #f8fafc; } QLineEdit:focus { border-color: #6366f1; }")
        
    def _style_combo(self, c):
        c.setStyleSheet("QComboBox { background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 10px; color: #f8fafc; } QComboBox::drop-down { border: none; } QComboBox QAbstractItemView { background-color: #1e293b; border: 1px solid #334155; color: #f8fafc; selection-background-color: #334155; }")
        
    def _style_spinbox(self, s):
        s.setStyleSheet("QDoubleSpinBox, QSpinBox { background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 10px; color: #f8fafc; } QDoubleSpinBox:focus, QSpinBox:focus { border-color: #6366f1; }")
        
    def _style_textedit(self, t):
        t.setStyleSheet("QTextEdit { background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 10px; color: #f8fafc; } QTextEdit:focus { border-color: #6366f1; }")
        
    def _style_datetime(self, dt):
        dt.setStyleSheet("""
            QDateTimeEdit { background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 10px; color: #f8fafc; }
            QDateTimeEdit:focus { border-color: #6366f1; }
            QDateTimeEdit::drop-down { border: none; }
            QCalendarWidget { background-color: #1e293b; color: #f8fafc; }
        """)
