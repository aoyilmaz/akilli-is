"""
Akıllı İş ERP - Tema Yönetimi
PyERP Pro + One Dark Pro + Material Ocean + Dark
"""

from dataclasses import dataclass
from typing import Dict
from enum import Enum


class ThemeType(Enum):
    """Tema türleri"""
    PYERP_PRO = "pyerp_pro"
    ONE_DARK_PRO = "one_dark_pro"
    DARK = "dark"
    MATERIAL_OCEAN = "material_ocean"


@dataclass
class Theme:
    """Tema tanımı"""
    name: str
    display_name: str
    
    # Ana renkler
    bg_primary: str
    bg_secondary: str
    bg_tertiary: str
    bg_hover: str
    bg_selected: str
    
    # Kenar çizgileri
    border: str
    border_light: str
    
    # Metin renkleri
    text_primary: str
    text_secondary: str
    text_muted: str
    text_accent: str
    
    # Accent renkler
    accent_primary: str
    accent_secondary: str
    accent_gradient_start: str
    accent_gradient_end: str
    
    # Durum renkleri
    success: str
    warning: str
    error: str
    info: str
    
    # Özel renkler
    sidebar_bg: str
    header_bg: str
    card_bg: str
    input_bg: str
    
    # Font
    font_family: str
    font_size: int
    font_size_small: int
    font_size_large: int
    font_size_title: int
    
    # Border radius
    radius_small: int
    radius_medium: int
    radius_large: int


# === PYERP PRO TEMA (Prototype'tan) ===
PYERP_PRO_THEME = Theme(
    name="pyerp_pro",
    display_name="PyERP Pro",
    
    # slate-950, slate-900, slate-800
    bg_primary="#020617",      # slate-950
    bg_secondary="#0f172a",    # slate-900
    bg_tertiary="#1e293b",     # slate-800
    bg_hover="#334155",        # slate-700
    bg_selected="#475569",     # slate-600
    
    # Borders
    border="#1e293b",          # slate-800
    border_light="#334155",    # slate-700
    
    # Text - slate tones
    text_primary="#f8fafc",    # slate-50
    text_secondary="#e2e8f0",  # slate-200
    text_muted="#64748b",      # slate-500
    text_accent="#818cf8",     # indigo-400
    
    # Accent - indigo to purple gradient
    accent_primary="#6366f1",  # indigo-500
    accent_secondary="#a855f7", # purple-500
    accent_gradient_start="#6366f1",
    accent_gradient_end="#a855f7",
    
    # Status colors
    success="#34d399",         # emerald-400
    warning="#fbbf24",         # amber-400
    error="#f87171",           # red-400
    info="#38bdf8",            # sky-400
    
    # Special areas
    sidebar_bg="#0f172a",      # slate-900
    header_bg="#020617",       # slate-950 with opacity
    card_bg="#0f172a",         # slate-900/50
    input_bg="#0f172a",        # slate-900
    
    # Font - SF Pro / System
    font_family="SF Pro Display, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Arial",
    font_size=14,
    font_size_small=12,
    font_size_large=16,
    font_size_title=24,
    
    # Rounded corners - more rounded
    radius_small=8,
    radius_medium=12,
    radius_large=16,
)


# === ONE DARK PRO TEMA ===
ONE_DARK_PRO_THEME = Theme(
    name="one_dark_pro",
    display_name="One Dark Pro",
    
    bg_primary="#282c34",
    bg_secondary="#21252b",
    bg_tertiary="#2c313a",
    bg_hover="#3a3f4b",
    bg_selected="#3e4451",
    
    border="#3a3f4b",
    border_light="#4b5263",
    
    text_primary="#abb2bf",
    text_secondary="#9da5b4",
    text_muted="#5c6370",
    text_accent="#61afef",
    
    accent_primary="#61afef",
    accent_secondary="#c678dd",
    accent_gradient_start="#61afef",
    accent_gradient_end="#c678dd",
    
    success="#98c379",
    warning="#e5c07b",
    error="#e06c75",
    info="#56b6c2",
    
    sidebar_bg="#21252b",
    header_bg="#282c34",
    card_bg="#2c313a",
    input_bg="#1d2025",
    
    font_family="SF Pro Display, -apple-system, BlinkMacSystemFont, Segoe UI, Arial",
    font_size=13,
    font_size_small=11,
    font_size_large=15,
    font_size_title=22,
    
    radius_small=6,
    radius_medium=8,
    radius_large=12,
)


# === DARK TEMA (Orijinal) ===
DARK_THEME = Theme(
    name="dark",
    display_name="Dark",
    
    bg_primary="#0f172a",
    bg_secondary="#1e293b",
    bg_tertiary="#334155",
    bg_hover="#3b4963",
    bg_selected="#4f5d7a",
    
    border="#334155",
    border_light="#475569",
    
    text_primary="#f8fafc",
    text_secondary="#e2e8f0",
    text_muted="#94a3b8",
    text_accent="#818cf8",
    
    accent_primary="#6366f1",
    accent_secondary="#a855f7",
    accent_gradient_start="#6366f1",
    accent_gradient_end="#a855f7",
    
    success="#10b981",
    warning="#f59e0b",
    error="#ef4444",
    info="#3b82f6",
    
    sidebar_bg="#1e293b",
    header_bg="#0f172a",
    card_bg="#1e293b",
    input_bg="#1e293b",
    
    font_family="Arial",
    font_size=14,
    font_size_small=12,
    font_size_large=16,
    font_size_title=24,
    
    radius_small=8,
    radius_medium=12,
    radius_large=16,
)


# === MATERIAL OCEAN TEMA ===
MATERIAL_OCEAN_THEME = Theme(
    name="material_ocean",
    display_name="Material Ocean",
    
    bg_primary="#0F111A",
    bg_secondary="#1A1C25",
    bg_tertiary="#2B2F40",
    bg_hover="#363a4f",
    bg_selected="#414560",
    
    border="#1F2233",
    border_light="#2B2F40",
    
    text_primary="#EEFFFF",
    text_secondary="#B0BEC5",
    text_muted="#546E7A",
    text_accent="#82AAFF",
    
    accent_primary="#82AAFF",
    accent_secondary="#C792EA",
    accent_gradient_start="#82AAFF",
    accent_gradient_end="#C792EA",
    
    success="#C3E88D",
    warning="#FFCB6B",
    error="#FF5370",
    info="#89DDFF",
    
    sidebar_bg="#0F111A",
    header_bg="#0F111A",
    card_bg="#1A1C25",
    input_bg="#1A1C25",
    
    font_family="Arial",
    font_size=14,
    font_size_small=12,
    font_size_large=16,
    font_size_title=24,
    
    radius_small=6,
    radius_medium=10,
    radius_large=14,
)


# Tema koleksiyonu - PyERP Pro varsayılan
THEMES: Dict[str, Theme] = {
    "pyerp_pro": PYERP_PRO_THEME,
    "one_dark_pro": ONE_DARK_PRO_THEME,
    "dark": DARK_THEME,
    "material_ocean": MATERIAL_OCEAN_THEME,
}


class ThemeManager:
    """Tema yöneticisi"""
    
    _instance = None
    _current_theme: Theme = PYERP_PRO_THEME  # Varsayılan PyERP Pro
    _callbacks = []
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_theme(cls) -> Theme:
        return cls._current_theme
    
    @classmethod
    def set_theme(cls, theme_name: str):
        if theme_name in THEMES:
            cls._current_theme = THEMES[theme_name]
            cls._notify_callbacks()
    
    @classmethod
    def get_available_themes(cls) -> Dict[str, str]:
        return {name: theme.display_name for name, theme in THEMES.items()}
    
    @classmethod
    def register_callback(cls, callback):
        if callback not in cls._callbacks:
            cls._callbacks.append(callback)
    
    @classmethod
    def _notify_callbacks(cls):
        for callback in cls._callbacks:
            try:
                callback(cls._current_theme)
            except:
                pass
    
    @classmethod
    def get_stylesheet(cls) -> str:
        t = cls._current_theme
        return f"""
            QWidget {{
                background-color: {t.bg_primary};
                color: {t.text_primary};
                font-family: {t.font_family};
                font-size: {t.font_size}px;
            }}
            
            QScrollBar:vertical {{
                background: {t.bg_secondary};
                width: 8px;
                border-radius: 4px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {t.bg_tertiary};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {t.border_light};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar:horizontal {{
                background: {t.bg_secondary};
                height: 8px;
                border-radius: 4px;
                margin: 2px;
            }}
            QScrollBar::handle:horizontal {{
                background: {t.bg_tertiary};
                border-radius: 4px;
                min-width: 30px;
            }}
            
            QMenu {{
                background-color: {t.bg_secondary};
                border: 1px solid {t.border};
                border-radius: {t.radius_small}px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 8px 24px;
                border-radius: 4px;
                color: {t.text_primary};
            }}
            QMenu::item:selected {{
                background-color: {t.bg_hover};
            }}
            
            QToolTip {{
                background-color: {t.bg_secondary};
                color: {t.text_primary};
                border: 1px solid {t.border};
                border-radius: 6px;
                padding: 8px 12px;
            }}
            
            QMessageBox {{
                background-color: {t.bg_primary};
            }}
            QMessageBox QLabel {{
                color: {t.text_primary};
            }}
            QMessageBox QPushButton {{
                background-color: {t.bg_secondary};
                border: 1px solid {t.border};
                border-radius: {t.radius_small}px;
                padding: 8px 20px;
                min-width: 80px;
                color: {t.text_primary};
            }}
            QMessageBox QPushButton:hover {{
                background-color: {t.bg_hover};
            }}
        """


def get_theme() -> Theme:
    return ThemeManager.get_theme()


def get_colors() -> dict:
    t = get_theme()
    return {
        "primary": t.accent_primary,
        "secondary": t.accent_secondary,
        "success": t.success,
        "warning": t.warning,
        "error": t.error,
        "info": t.info,
        "bg_dark": t.bg_primary,
        "bg_medium": t.bg_secondary,
        "bg_light": t.bg_tertiary,
        "text": t.text_primary,
        "text_secondary": t.text_secondary,
        "text_muted": t.text_muted,
        "border": t.border,
    }
