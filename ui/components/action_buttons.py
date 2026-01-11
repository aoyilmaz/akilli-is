"""
ui/components/action_buttons.py
İşlem butonları için yardımcı fonksiyonlar - Qt yerleşik simgelerle
"""

from PyQt6.QtWidgets import QPushButton, QStyle, QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize


def create_view_button(parent=None) -> QPushButton:
    """Görüntüle butonu"""
    btn = QPushButton(parent)
    btn.setIcon(
        QApplication.style().standardIcon(
            QStyle.StandardPixmap.SP_FileDialogContentsView
        )
    )
    btn.setIconSize(QSize(16, 16))
    btn.setFixedSize(32, 28)
    btn.setToolTip("Görüntüle")
    return btn


def create_edit_button(parent=None) -> QPushButton:
    """Düzenle butonu"""
    btn = QPushButton(parent)
    btn.setIcon(
        QApplication.style().standardIcon(
            QStyle.StandardPixmap.SP_FileDialogDetailedView
        )
    )
    btn.setIconSize(QSize(16, 16))
    btn.setFixedSize(32, 28)
    btn.setToolTip("Düzenle")
    return btn


def create_delete_button(parent=None) -> QPushButton:
    """Sil butonu"""
    btn = QPushButton(parent)
    btn.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
    btn.setIconSize(QSize(16, 16))
    btn.setFixedSize(32, 28)
    btn.setToolTip("Sil")
    return btn


def create_add_button(parent=None) -> QPushButton:
    """Ekle butonu"""
    btn = QPushButton(parent)
    btn.setIcon(
        QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder)
    )
    btn.setIconSize(QSize(16, 16))
    btn.setFixedSize(32, 28)
    btn.setToolTip("Ekle")
    return btn


def create_save_button(parent=None) -> QPushButton:
    """Kaydet butonu"""
    btn = QPushButton(parent)
    btn.setIcon(
        QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton)
    )
    btn.setIconSize(QSize(16, 16))
    btn.setFixedSize(32, 28)
    btn.setToolTip("Kaydet")
    return btn


def create_cancel_button(parent=None) -> QPushButton:
    """İptal butonu"""
    btn = QPushButton(parent)
    btn.setIcon(
        QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton)
    )
    btn.setIconSize(QSize(16, 16))
    btn.setFixedSize(32, 28)
    btn.setToolTip("İptal")
    return btn


def create_refresh_button(parent=None) -> QPushButton:
    """Yenile butonu"""
    btn = QPushButton(parent)
    btn.setIcon(
        QApplication.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload)
    )
    btn.setIconSize(QSize(16, 16))
    btn.setFixedSize(32, 28)
    btn.setToolTip("Yenile")
    return btn


def create_approve_button(parent=None) -> QPushButton:
    """Onayla butonu"""
    btn = QPushButton(parent)
    btn.setIcon(
        QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
    )
    btn.setIconSize(QSize(16, 16))
    btn.setFixedSize(32, 28)
    btn.setToolTip("Onayla")
    return btn
