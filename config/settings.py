"""
Akıllı İş ERP - Uygulama Ayarları
"""
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Uygulama ayarları"""
    
    # Uygulama Bilgileri
    APP_NAME: str = "Akıllı İş"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Kurumsal Kaynak Planlama Sistemi"
    
    # Veritabanı Ayarları
    DB_HOST: str = Field(default="localhost", env="DB_HOST")
    DB_PORT: int = Field(default=3306, env="DB_PORT")
    DB_NAME: str = Field(default="akilli_is", env="DB_NAME")
    DB_USER: str = Field(default="root", env="DB_USER")
    DB_PASSWORD: str = Field(default="", env="DB_PASSWORD")
    
    # Uygulama Ayarları
    DEBUG: bool = Field(default=True, env="DEBUG")
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    
    # AI Asistan
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    AI_MODEL: str = "claude-sonnet-4-20250514"
    
    # Dosya Yolları
    BASE_DIR: Path = Path(__file__).parent.parent
    ASSETS_DIR: Path = BASE_DIR / "assets"
    REPORTS_DIR: Path = BASE_DIR / "reports" / "templates"
    EXPORTS_DIR: Path = BASE_DIR / "exports" / "output"
    
    # Tema Ayarları
    THEME: str = "dark"  # "dark" veya "light"
    ACCENT_COLOR: str = "#6366f1"  # Indigo
    
    # Dil Ayarları
    LANGUAGE: str = "tr"
    DATE_FORMAT: str = "%d.%m.%Y"
    DATETIME_FORMAT: str = "%d.%m.%Y %H:%M"
    CURRENCY: str = "TRY"
    CURRENCY_SYMBOL: str = "₺"
    
    @property
    def database_url(self) -> str:
        """SQLAlchemy veritabanı URL'si"""
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
