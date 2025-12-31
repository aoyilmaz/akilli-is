"""
Akıllı İş - Kategori Form Sayfası
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QCheckBox, QFrame,
    QFormLayout, QMessageBox, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal

from database.models import ItemCategory


# Emoji seçenekleri
CATEGORY_ICONS = [
    "📁", "📂", "🗂️", "📦", "📋", "🏷️",
    "🧱", "⚙️", "🔧", "🔩", "🛠️", "⚡",
    "🎨", "🧪", "💊", "🧴", "🧹", "📱",
    "💻", "🖥️", "⌨️", "🖨️", "📷", "🔌",
    "🍎", "🥤", "🍞", "🧀", "🥩", "🐟",
    "👕", "👖", "👟", "👜", "💍", "⌚",
    "🚗", "✈️", "🚢", "🏠", "🏢", "🏭",
]


class CategoryFormPage(QWidget):
    """Kategori ekleme/düzenleme formu"""
    
    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()
    
    def __init__(self, category: Optional[ItemCategory] = None, parent_id: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.category = category
        self.parent_id = parent_id  # Alt kategori eklerken üst kategori ID'si
        self.is_edit_mode = category is not None
        self.selected_icon = "📁"
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
        
        title_text = "Kategori Düzenle" if self.is_edit_mode else "Yeni Kategori"
        title = QLabel(title_text)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f8fafc; margin-left: 16px;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        save_btn = QPushButton("💾 Kaydet")
        save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #a855f7);
                border: none;
                color: white;
                font-weight: 600;
                padding: 12px 32px;
                border-radius: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #9333ea);
            }
        """)
        save_btn.clicked.connect(self._on_save)
        header_layout.addWidget(save_btn)
        
        layout.addLayout(header_layout)
        
        # === Form ===
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 41, 59, 0.5);
                border: 1px solid #334155;
                border-radius: 16px;
            }
        """)
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(24, 24, 24, 24)
        form_layout.setSpacing(20)
        
        # --- İkon Seçimi ---
        icon_section = QVBoxLayout()
        icon_label = QLabel("📁 Kategori İkonu")
        icon_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #f8fafc;")
        icon_section.addWidget(icon_label)
        
        icon_grid = QGridLayout()
        icon_grid.setSpacing(8)
        
        self.icon_buttons = []
        for i, icon in enumerate(CATEGORY_ICONS):
            btn = QPushButton(icon)
            btn.setFixedSize(48, 48)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1e293b;
                    border: 2px solid #334155;
                    border-radius: 8px;
                    font-size: 20px;
                }
                QPushButton:hover {
                    background-color: #334155;
                    border-color: #6366f1;
                }
                QPushButton:checked {
                    background-color: #4f46e5;
                    border-color: #818cf8;
                }
            """)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, ic=icon, b=btn: self._select_icon(ic, b))
            icon_grid.addWidget(btn, i // 12, i % 12)
            self.icon_buttons.append(btn)
            
            # İlk ikonu seç
            if i == 0:
                btn.setChecked(True)
        
        icon_section.addLayout(icon_grid)
        form_layout.addLayout(icon_section)
        
        # --- Temel Bilgiler ---
        basic_layout = QHBoxLayout()
        basic_layout.setSpacing(24)
        
        # Sol kolon
        left_form = QFormLayout()
        left_form.setSpacing(16)
        
        # Kod
        code_layout = QHBoxLayout()
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("KAT001")
        self._style_input(self.code_input)
        
        auto_btn = QPushButton("🔄")
        auto_btn.setFixedWidth(40)
        auto_btn.clicked.connect(self._generate_code)
        self._style_button_small(auto_btn)
        
        code_layout.addWidget(self.code_input)
        code_layout.addWidget(auto_btn)
        left_form.addRow("Kategori Kodu *", code_layout)
        
        # Ad
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Kategori adı")
        self._style_input(self.name_input)
        left_form.addRow("Kategori Adı *", self.name_input)
        
        # Üst Kategori
        self.parent_combo = QComboBox()
        self.parent_combo.addItem("— Ana Kategori —", None)
        self._style_combo(self.parent_combo)
        left_form.addRow("Üst Kategori", self.parent_combo)
        
        basic_layout.addLayout(left_form)
        
        # Sağ kolon
        right_form = QFormLayout()
        right_form.setSpacing(16)
        
        # Renk
        self.color_input = QLineEdit()
        self.color_input.setPlaceholderText("#6366f1")
        self.color_input.setMaxLength(7)
        self._style_input(self.color_input)
        right_form.addRow("Renk (Hex)", self.color_input)
        
        # Açıklama
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Kategori açıklaması...")
        self.description_input.setMaximumHeight(80)
        self._style_textedit(self.description_input)
        right_form.addRow("Açıklama", self.description_input)
        
        # Aktif
        self.is_active_check = QCheckBox("Aktif")
        self.is_active_check.setChecked(True)
        self.is_active_check.setStyleSheet("color: #f8fafc;")
        right_form.addRow("", self.is_active_check)
        
        basic_layout.addLayout(right_form)
        
        form_layout.addLayout(basic_layout)
        
        layout.addWidget(form_frame)
        layout.addStretch()
        
    def load_categories(self, categories: list):
        """Üst kategori listesini yükle"""
        self.parent_combo.clear()
        self.parent_combo.addItem("— Ana Kategori —", None)
        
        for cat in categories:
            # Kendisini ve alt kategorilerini hariç tut
            if self.category and (cat.id == self.category.id):
                continue
            
            indent = "  " * (cat.level or 0)
            icon = cat.icon or "📁"
            self.parent_combo.addItem(f"{indent}{icon} {cat.name}", cat.id)
        
        # Varsayılan üst kategori
        if self.parent_id:
            for i in range(self.parent_combo.count()):
                if self.parent_combo.itemData(i) == self.parent_id:
                    self.parent_combo.setCurrentIndex(i)
                    break
                    
    def load_data(self):
        """Düzenleme modunda verileri yükle"""
        if not self.category:
            return
        
        self.code_input.setText(self.category.code)
        self.name_input.setText(self.category.name)
        self.description_input.setPlainText(self.category.description or "")
        self.color_input.setText(self.category.color or "")
        self.is_active_check.setChecked(self.category.is_active)
        
        # İkon
        if self.category.icon:
            self.selected_icon = self.category.icon
            for btn in self.icon_buttons:
                if btn.text() == self.category.icon:
                    btn.setChecked(True)
                else:
                    btn.setChecked(False)
        
        # Üst kategori
        if self.category.parent_id:
            self.parent_id = self.category.parent_id
            
    def _select_icon(self, icon: str, button: QPushButton):
        """İkon seç"""
        self.selected_icon = icon
        for btn in self.icon_buttons:
            btn.setChecked(btn == button)
            
    def _generate_code(self):
        """Otomatik kod üret"""
        import random
        code = f"KAT{random.randint(100, 999)}"
        self.code_input.setText(code)
        
    def _on_save(self):
        if not self._validate():
            return
        data = self.get_form_data()
        self.saved.emit(data)
        
    def _validate(self) -> bool:
        if not self.code_input.text().strip():
            QMessageBox.warning(self, "Uyarı", "Kategori kodu zorunludur!")
            self.code_input.setFocus()
            return False
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Uyarı", "Kategori adı zorunludur!")
            self.name_input.setFocus()
            return False
        return True
        
    def get_form_data(self) -> dict:
        parent_id = self.parent_combo.currentData()
        
        # Seviye hesapla
        level = 0
        if parent_id:
            # Üst kategorinin seviyesine göre hesaplanacak
            level = 1  # Basit hesaplama
        
        return {
            "code": self.code_input.text().strip(),
            "name": self.name_input.text().strip(),
            "description": self.description_input.toPlainText().strip() or None,
            "parent_id": parent_id,
            "level": level,
            "icon": self.selected_icon,
            "color": self.color_input.text().strip() or None,
            "is_active": self.is_active_check.isChecked(),
        }
    
    def _style_input(self, widget):
        widget.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px 12px;
                color: #f8fafc;
                font-size: 14px;
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
                min-width: 200px;
            }
            QComboBox:focus { border-color: #6366f1; }
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
        
    def _style_button_small(self, widget):
        widget.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #f8fafc;
                padding: 8px;
            }
            QPushButton:hover { background-color: #334155; }
        """)
