"""
Akıllı İş ERP - Uygulama Ayarları
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Temel dizinler
BASE_DIR = Path(__file__).resolve().parent.parent
THEMES_DIR = BASE_DIR / "ui" / "themes"
ICONS_DIR = BASE_DIR / "ui" / "resources" / "icons"
DATA_DIR = BASE_DIR / "data"

# Data klasörünü oluştur
DATA_DIR.mkdir(exist_ok=True)

# Uygulama bilgileri
APP_NAME = "Akıllı İş"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Kurumsal Kaynak Planlama Sistemi"

# Veritabanı ayarları
DB_ENGINE = os.getenv("DB_ENGINE", "postgresql")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "akilli_is")
DB_USER = os.getenv("DB_USER", "akilli_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "akilli123")


def get_database_url() -> str:
    """Veritabanı bağlantı URL'i"""
    if DB_ENGINE == "postgresql":
        return f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    elif DB_ENGINE == "sqlite":
        db_path = DATA_DIR / "akilliis.db"
        return f"sqlite:///{db_path}"
    elif DB_ENGINE == "mysql":
        return f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    else:
        raise ValueError(f"Desteklenmeyen veritabanı: {DB_ENGINE}")


# Uygulama ayarları
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")

# AI Asistan
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
AI_MODEL = "claude-sonnet-4-20250514"

# UI Ayarları
UI = {
    "THEME": os.getenv("UI_THEME", "dark"),
    "LANGUAGE": os.getenv("UI_LANGUAGE", "tr"),
    "FONT_FAMILY": "Helvetica Neue",
    "FONT_SIZE": 13,
    "WINDOW_WIDTH": 1400,
    "WINDOW_HEIGHT": 900,
    "SIDEBAR_WIDTH": 260,
    "SIDEBAR_COLLAPSED_WIDTH": 70,
}

# Renk paleti
COLORS = {
    # Primary
    "primary": "#6366f1",
    "primary_light": "#818cf8",
    "primary_dark": "#4f46e5",
    # Secondary
    "secondary": "#8b5cf6",
    "secondary_light": "#a78bfa",
    "secondary_dark": "#7c3aed",
    # Accent
    "accent": "#a855f7",
    # Status
    "success": "#10b981",
    "warning": "#f59e0b",
    "error": "#ef4444",
    "info": "#3b82f6",
    # Dark theme
    "dark_bg": "#0f172a",
    "dark_surface": "#1e293b",
    "dark_border": "#334155",
    "dark_text": "#f8fafc",
    "dark_text_secondary": "#94a3b8",
    # Light theme
    "light_bg": "#f8fafc",
    "light_surface": "#ffffff",
    "light_border": "#e2e8f0",
    "light_text": "#0f172a",
    "light_text_secondary": "#64748b",
}

# Dil ayarları
LANGUAGE = "tr"
DATE_FORMAT = "%d.%m.%Y"
DATETIME_FORMAT = "%d.%m.%Y %H:%M"
CURRENCY = "TRY"
CURRENCY_SYMBOL = "₺"
