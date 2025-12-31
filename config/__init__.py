"""
Akıllı İş - Configuration
"""
from .settings import (
    # Dizinler
    BASE_DIR,
    THEMES_DIR,
    ICONS_DIR,
    DATA_DIR,
    
    # Uygulama
    APP_NAME,
    APP_VERSION,
    APP_DESCRIPTION,
    
    # Veritabanı
    DB_ENGINE,
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
    get_database_url,
    
    # Ayarlar
    DEBUG,
    SECRET_KEY,
    ANTHROPIC_API_KEY,
    AI_MODEL,
    
    # UI
    UI,
    COLORS,
    
    # Dil
    LANGUAGE,
    DATE_FORMAT,
    DATETIME_FORMAT,
    CURRENCY,
    CURRENCY_SYMBOL,
)

__all__ = [
    "BASE_DIR", "THEMES_DIR", "ICONS_DIR", "DATA_DIR",
    "APP_NAME", "APP_VERSION", "APP_DESCRIPTION",
    "DB_ENGINE", "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD",
    "get_database_url",
    "DEBUG", "SECRET_KEY", "ANTHROPIC_API_KEY", "AI_MODEL",
    "UI", "COLORS",
    "LANGUAGE", "DATE_FORMAT", "DATETIME_FORMAT", "CURRENCY", "CURRENCY_SYMBOL",
]
