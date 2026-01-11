"""
Akilli Is ERP - VS Code Dark Tema Stilleri
Tum modullerde kullanilacak ortak renk sabitleri
"""

# === ANA RENKLER ===
BG_PRIMARY = "#1e1e1e"  # Ana arka plan
BG_SECONDARY = "#252526"  # Panel, sidebar arka plani
BG_TERTIARY = "#2d2d2d"  # Kartlar, tabs, formlar
BG_HOVER = "#3e3e42"  # Hover durumu
BG_SELECTED = "#094771"  # Secili durum (VS Code selection)

# === KENAR CIZGILERI ===
BORDER = "#3e3e42"
BORDER_LIGHT = "#4c4c4c"

# === METIN RENKLERI ===
TEXT_PRIMARY = "#cccccc"  # Ana metin
TEXT_SECONDARY = "#d4d4d4"  # Ikincil metin
TEXT_MUTED = "#969696"  # Soluk metin
TEXT_ACCENT = "#007acc"  # Vurgulu metin

# === ACCENT RENKLER ===
ACCENT = "#007acc"  # VS Code mavisi
ACCENT_HOVER = "#1177bb"  # Hover durumu
ACCENT_SECONDARY = "#5e3b8e"  # Mor (status bar)

# === DURUM RENKLERI ===
SUCCESS = "#4ec9b0"  # Yesil
SUCCESS_BG = "#2d4a3e"  # Yesil arka plan
WARNING = "#dcdcaa"  # Sari
WARNING_BG = "#4a4a2d"  # Sari arka plan
ERROR = "#f14c4c"  # Kirmizi
ERROR_BG = "#4a2d2d"  # Kirmizi arka plan
INFO = "#3794ff"  # Mavi

# === TABLO RENKLERI ===
TABLE_BG = "#1e1e1e"
TABLE_HEADER_BG = "#252526"
TABLE_ROW_ALT = "#2a2a2a"
TABLE_SELECTED = "#094771"
TABLE_GRID = "#3e3e42"

# === INPUT RENKLERI ===
INPUT_BG = "#3c3c3c"
INPUT_BORDER = "#3e3e42"
INPUT_FOCUS = "#007acc"

# === BUTTON RENKLERI ===
BTN_PRIMARY_BG = "#007acc"
BTN_PRIMARY_HOVER = "#1177bb"
BTN_SECONDARY_BG = "#3c3c3c"
BTN_SECONDARY_HOVER = "#4c4c4c"
BTN_DANGER_BG = "#f14c4c"
BTN_DANGER_HOVER = "#d73a3a"
BTN_SUCCESS_BG = "#4ec9b0"
BTN_SUCCESS_HOVER = "#3eb89f"


def get_input_style():
    """Standart input stili"""
    return f"""
        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QComboBox {{
            background-color: {INPUT_BG};
            border: 1px solid {INPUT_BORDER};
            border-radius: 4px;
            padding: 8px 12px;
            color: {TEXT_PRIMARY};
        }}
        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus,
        QDoubleSpinBox:focus, QDateEdit:focus, QComboBox:focus {{
            border: 1px solid {INPUT_FOCUS};
        }}
        QComboBox::drop-down {{
            border: none;
            padding-right: 8px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {BG_SECONDARY};
            border: 1px solid {BORDER};
            selection-background-color: {BG_SELECTED};
        }}
    """


def get_button_style(btn_type="primary"):
    """Standart buton stili"""
    if btn_type == "primary":
        return f"""
            QPushButton {{
                background-color: {BTN_PRIMARY_BG};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: white;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {BTN_PRIMARY_HOVER};
            }}
            QPushButton:disabled {{
                background-color: {BG_HOVER};
                color: {TEXT_MUTED};
            }}
        """
    elif btn_type == "secondary":
        return f"""
            QPushButton {{
                background-color: {BTN_SECONDARY_BG};
                border: 1px solid {BORDER};
                border-radius: 4px;
                padding: 8px 16px;
                color: {TEXT_PRIMARY};
            }}
            QPushButton:hover {{
                background-color: {BTN_SECONDARY_HOVER};
            }}
        """
    elif btn_type == "danger":
        return f"""
            QPushButton {{
                background-color: {BTN_DANGER_BG};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: white;
            }}
            QPushButton:hover {{
                background-color: {BTN_DANGER_HOVER};
            }}
        """
    elif btn_type == "success":
        return f"""
            QPushButton {{
                background-color: {BTN_SUCCESS_BG};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: white;
            }}
            QPushButton:hover {{
                background-color: {BTN_SUCCESS_HOVER};
            }}
        """


def get_table_style():
    """Standart tablo stili"""
    return f"""
        QTableWidget {{
            background-color: {TABLE_BG};
            border: 1px solid {BORDER};
            border-radius: 4px;
            gridline-color: {TABLE_GRID};
        }}
        QTableWidget::item {{
            padding: 8px;
            border-bottom: 1px solid {TABLE_GRID};
        }}
        QTableWidget::item:selected {{
            background-color: {TABLE_SELECTED};
        }}
        QHeaderView::section {{
            background-color: {TABLE_HEADER_BG};
            color: {TEXT_MUTED};
            font-weight: 600;
            padding: 10px 8px;
            border: none;
            border-bottom: 1px solid {BORDER};
        }}
        QTableWidget QTableCornerButton::section {{
            background-color: {TABLE_HEADER_BG};
            border: none;
        }}
    """


def get_tab_style():
    """Standart tab stili"""
    return f"""
        QTabWidget::pane {{
            border: none;
            background-color: {BG_PRIMARY};
        }}
        QTabBar::tab {{
            background-color: {BG_TERTIARY};
            color: {TEXT_MUTED};
            padding: 10px 20px;
            border: none;
            border-bottom: 2px solid transparent;
        }}
        QTabBar::tab:selected {{
            background-color: {BG_PRIMARY};
            color: {TEXT_PRIMARY};
            border-bottom: 2px solid {ACCENT};
        }}
        QTabBar::tab:hover {{
            background-color: {BG_HOVER};
            color: {TEXT_PRIMARY};
        }}
    """


def get_card_style(accent_color=None):
    """Kart stili"""
    border_color = accent_color if accent_color else BORDER
    return f"""
        QFrame {{
            background-color: {BG_SECONDARY};
            border: 1px solid {border_color};
            border-radius: 8px;
        }}
    """


def get_list_style():
    """Liste stili"""
    return f"""
        QListWidget {{
            background-color: {BG_PRIMARY};
            border: 1px solid {BORDER};
            border-radius: 4px;
            outline: none;
        }}
        QListWidget::item {{
            padding: 10px 12px;
            border-bottom: 1px solid {BORDER};
            color: {TEXT_PRIMARY};
        }}
        QListWidget::item:hover {{
            background-color: {BG_HOVER};
        }}
        QListWidget::item:selected {{
            background-color: {BG_SELECTED};
            color: white;
        }}
    """


def get_tree_style():
    """Tree widget stili"""
    return f"""
        QTreeWidget {{
            background-color: {BG_PRIMARY};
            border: 1px solid {BORDER};
            border-radius: 4px;
            outline: none;
        }}
        QTreeWidget::item {{
            padding: 6px;
            border: none;
        }}
        QTreeWidget::item:hover {{
            background-color: {BG_HOVER};
        }}
        QTreeWidget::item:selected {{
            background-color: {BG_SELECTED};
            color: white;
        }}
        QTreeWidget::branch {{
            background-color: transparent;
        }}
    """


def get_scroll_style():
    """Scrollbar stili"""
    return f"""
        QScrollBar:vertical {{
            background: {BG_SECONDARY};
            width: 10px;
            border-radius: 5px;
            margin: 2px;
        }}
        QScrollBar::handle:vertical {{
            background: {BG_HOVER};
            border-radius: 5px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {BORDER_LIGHT};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar:horizontal {{
            background: {BG_SECONDARY};
            height: 10px;
            border-radius: 5px;
            margin: 2px;
        }}
        QScrollBar::handle:horizontal {{
            background: {BG_HOVER};
            border-radius: 5px;
            min-width: 30px;
        }}
    """


def get_dialog_style():
    """Dialog stili"""
    return f"""
        QDialog {{
            background-color: {BG_PRIMARY};
        }}
        QLabel {{
            color: {TEXT_PRIMARY};
        }}
    """


def get_form_label_style():
    """Form label stili"""
    return f"color: {TEXT_MUTED}; font-weight: 500;"


def get_title_style():
    """Baslik stili"""
    return f"color: {TEXT_PRIMARY}; font-size: 18px; font-weight: bold;"


def get_subtitle_style():
    """Alt baslik stili"""
    return f"color: {TEXT_SECONDARY}; font-size: 14px;"


# === STAT CARD RENKLERI ===
STAT_COLORS = {
    "primary": ACCENT,
    "success": SUCCESS,
    "warning": WARNING,
    "error": ERROR,
    "info": INFO,
    "purple": ACCENT_SECONDARY,
}


def get_stat_card_style(color_name="primary"):
    """İstatistik karti stili"""
    color = STAT_COLORS.get(color_name, ACCENT)
    return f"""
        QFrame {{
            background-color: {BG_SECONDARY};
            border: 1px solid {color}40;
            border-radius: 8px;
            border-left: 3px solid {color};
        }}
    """


def get_filter_panel_style():
    """Filtre paneli stili"""
    return f"""
        QFrame {{
            background-color: {BG_SECONDARY};
            border: 1px solid {BORDER};
            border-radius: 8px;
        }}
    """


def get_search_input_style():
    """Arama kutusu stili"""
    return f"""
        QLineEdit {{
            background-color: {BG_TERTIARY};
            border: 1px solid {BORDER};
            border-radius: 4px;
            padding: 8px 12px;
            color: {TEXT_PRIMARY};
        }}
        QLineEdit:focus {{
            border-color: {ACCENT};
        }}
    """


def get_combo_style():
    """Combobox stili"""
    return f"""
        QComboBox {{
            background-color: {BG_TERTIARY};
            border: 1px solid {BORDER};
            border-radius: 4px;
            padding: 8px 12px;
            color: {TEXT_PRIMARY};
            min-width: 120px;
        }}
        QComboBox:focus {{
            border-color: {ACCENT};
        }}
        QComboBox::drop-down {{
            border: none;
            padding-right: 8px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {BG_SECONDARY};
            border: 1px solid {BORDER};
            selection-background-color: {ACCENT};
        }}
    """


def get_action_button_style(color=None):
    """Küçük aksiyon butonu stili (tablo içi)"""
    c = color or ACCENT
    return f"""
        QPushButton {{
            background-color: {c}20;
            border: 1px solid {c}50;
            border-radius: 4px;
            padding: 4px;
        }}
        QPushButton:hover {{
            background-color: {c}40;
        }}
    """


def get_menu_style():
    """Context menu stili"""
    return f"""
        QMenu {{
            background-color: {BG_SECONDARY};
            border: 1px solid {BORDER};
            border-radius: 4px;
            padding: 4px;
        }}
        QMenu::item {{
            padding: 8px 16px;
            border-radius: 4px;
            color: {TEXT_PRIMARY};
        }}
        QMenu::item:selected {{
            background-color: {ACCENT};
        }}
        QMenu::separator {{
            height: 1px;
            background-color: {BORDER};
            margin: 4px 8px;
        }}
    """


def get_module_stat_card(icon="📊", title="", value="0", color=ACCENT):
    """Modül istatistik kartı stili"""
    return f"""
        QFrame {{
            background-color: {color}15;
            border: 1px solid {color}30;
            border-radius: 8px;
        }}
    """


def get_form_input_style():
    """Form input stili"""
    return f"""
        QLineEdit {{
            background-color: {BG_TERTIARY};
            border: 1px solid {BORDER};
            border-radius: 4px;
            padding: 8px 12px;
            color: {TEXT_PRIMARY};
            min-height: 20px;
        }}
        QLineEdit:focus {{
            border-color: {ACCENT};
        }}
        QLineEdit::placeholder {{
            color: {TEXT_MUTED};
        }}
    """


def get_form_spinbox_style():
    """Form spinbox stili"""
    return f"""
        QSpinBox, QDoubleSpinBox {{
            background-color: {BG_TERTIARY};
            border: 1px solid {BORDER};
            border-radius: 4px;
            padding: 8px 12px;
            color: {TEXT_PRIMARY};
            min-width: 120px;
        }}
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: {ACCENT};
        }}
        QSpinBox::up-button, QDoubleSpinBox::up-button,
        QSpinBox::down-button, QDoubleSpinBox::down-button {{
            width: 18px;
            background-color: {BG_HOVER};
            border: none;
        }}
    """


def get_form_textedit_style():
    """Form textedit stili"""
    return f"""
        QTextEdit {{
            background-color: {BG_TERTIARY};
            border: 1px solid {BORDER};
            border-radius: 4px;
            padding: 8px 12px;
            color: {TEXT_PRIMARY};
        }}
        QTextEdit:focus {{
            border-color: {ACCENT};
        }}
    """


def get_form_checkbox_style():
    """Form checkbox stili"""
    return f"""
        QCheckBox {{
            color: {TEXT_PRIMARY};
            spacing: 8px;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 4px;
            border: 1px solid {BORDER};
            background-color: {BG_TERTIARY};
        }}
        QCheckBox::indicator:checked {{
            background-color: {ACCENT};
            border-color: {ACCENT};
        }}
    """


def get_form_frame_style():
    """Form frame stili"""
    return f"""
        QFrame {{
            background-color: {BG_SECONDARY};
            border: 1px solid {BORDER};
            border-radius: 8px;
        }}
    """


def get_form_section_title_style():
    """Form bölüm başlık stili"""
    return f"font-size: 15px; font-weight: bold; color: {TEXT_PRIMARY};"


def get_back_button_style():
    """Geri butonu stili"""
    return f"""
        QPushButton {{
            background-color: transparent;
            border: 1px solid {BORDER};
            border-radius: 4px;
            padding: 8px 16px;
            color: {TEXT_MUTED};
        }}
        QPushButton:hover {{
            background-color: {BG_HOVER};
            color: {TEXT_PRIMARY};
        }}
    """
