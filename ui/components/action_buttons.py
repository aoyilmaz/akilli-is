"""
ui/components/action_buttons.py
İşlem butonları için yardımcı fonksiyonlar - Phosphor Icons ve Modern UI
"""

from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import QSize, Qt
import qtawesome as qta

from config.icons import ICONS
from config.styles import COLORS


# Standart Buton Boyutu
BTN_SIZE = QSize(32, 28)
ICON_SIZE = QSize(16, 16)


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Hex kodu RGBA string'ine çevirir."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 6:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"rgba({r}, {g}, {b}, {alpha})"
    return hex_color


def _apply_action_style(
    btn: QPushButton, color_name: str, tooltip: str, icon_name: str
):
    """
    Butona standart stil ve ikon uygular.
    """
    color = COLORS.get(color_name, COLORS["primary"])
    bg_hover = hex_to_rgba(color, 0.4)  # %40 opacity bg
    border_hover = color  # Tam opak border

    # Ikon oluştur
    btn.setIcon(qta.icon(icon_name, color=color))
    btn.setIconSize(ICON_SIZE)
    btn.setFixedSize(BTN_SIZE)
    btn.setToolTip(tooltip)

    # UX & A11y improvements
    btn.setAccessibleName(tooltip)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)

    # Stil uygula
    btn.setStyleSheet(
        f"""
        QPushButton {{
            background-color: transparent !important;
            border: none !important;
            border-radius: 4px !important;
            padding: 2px !important;
        }}
        QPushButton:hover {{
            background-color: {bg_hover} !important;
            border: 1px solid {border_hover} !important;
        }}
        QPushButton:pressed {{
            background-color: {hex_to_rgba(color, 0.6)} !important;
        }}
    """
    )


def create_view_button(parent=None) -> QPushButton:
    """Görüntüle butonu (Nötr/Gri)"""
    btn = QPushButton(parent)
    _apply_action_style(btn, "text_secondary", "Görüntüle", ICONS.EYE)
    return btn


def create_edit_button(parent=None) -> QPushButton:
    """Düzenle butonu (Mavi/Primary)"""
    btn = QPushButton(parent)
    _apply_action_style(btn, "primary", "Düzenle", ICONS.EDIT)
    return btn


def create_delete_button(parent=None) -> QPushButton:
    """Sil butonu (Kırmızı/Danger)"""
    btn = QPushButton(parent)
    _apply_action_style(btn, "danger", "Sil", ICONS.DELETE)
    return btn


def create_add_button(parent=None, text=None) -> QPushButton:
    """
    Ekle butonu (Yeşil/Success)
    Not: Bu genelde tablo içinde değil, sayfa başlığında kullanılır.
    Eğer text verilirse ikon+metin olur, yoksa sadece ikon.
    """
    btn = QPushButton(parent)
    if text:
        btn.setText(text)

    # Başlık butonu stili biraz farklı olabilir ama tutarlılık için aynı fonk kullanıyoruz
    _apply_action_style(btn, "success", "Yeni Ekle", ICONS.PLUS)

    if text:
        # Metin varsa genişlik serbest olmalı
        btn.setFixedWidth(None)
        btn.setMinimumWidth(80)

    return btn


def create_save_button(parent=None) -> QPushButton:
    """Kaydet butonu (Info/Mavi)"""
    btn = QPushButton(parent)
    _apply_action_style(btn, "info", "Kaydet", ICONS.SAVE)
    return btn


def create_cancel_button(parent=None) -> QPushButton:
    """İptal butonu (Warning/Koyu)"""
    btn = QPushButton(parent)
    _apply_action_style(btn, "text_muted", "İptal", ICONS.CANCEL)
    return btn


def create_refresh_button(parent=None) -> QPushButton:
    """Yenile butonu"""
    btn = QPushButton(parent)
    _apply_action_style(btn, "primary", "Yenile", ICONS.REFRESH)
    return btn


def create_approve_button(parent=None) -> QPushButton:
    """Onayla butonu (Yeşil)"""
    btn = QPushButton(parent)
    _apply_action_style(btn, "success", "Onayla", ICONS.CHECK)
    return btn


def create_custom_button(
    parent=None, icon_name=None, tooltip="", color_name="primary"
) -> QPushButton:
    """Özel aksiyon butonu oluşturucu"""
    btn = QPushButton(parent)
    icon = icon_name or ICONS.STAR  # Fallback
    _apply_action_style(btn, color_name, tooltip, icon)
    return btn
