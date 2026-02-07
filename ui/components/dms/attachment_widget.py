import os
import shutil
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QMessageBox,
    QMenu,
    QFileDialog,
    QHBoxLayout,
    QPushButton,
)
from PyQt6.QtCore import Qt, QSize, QUrl
from PyQt6.QtGui import QIcon, QDesktopServices, QDragEnterEvent, QDropEvent

from database.base import SessionLocal
from modules.system.services.dms_service import DMSService
from config.icons import ICONS  # Varsayılan ikonlar


class AttachmentWidget(QWidget):
    """
    Dosya ekleme ve listeleme widget'ı.
    Sürükle-Bırak destekler.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.target_table: Optional[str] = None
        self.target_id: Optional[int] = None
        self.current_user_id: Optional[int] = (
            1  # Varsayılan kullanıcı (geliştirme için)
        )

        self.setup_ui()
        self.setAcceptDrops(True)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Başlık ve Butonlar
        header_layout = QHBoxLayout()
        self.title_label = QLabel("Ekli Dosyalar")
        self.title_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        self.add_btn = QPushButton("Dosya Ekle")
        self.add_btn.setIcon(QIcon(ICONS.get("plus", "")))  # Eğer icon yoksa boş geçer
        self.add_btn.clicked.connect(self.open_file_dialog)
        self.add_btn.setFixedSize(100, 25)
        header_layout.addWidget(self.add_btn)

        layout.addLayout(header_layout)

        # Dosya Listesi
        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(24, 24))
        self.list_widget.itemDoubleClicked.connect(self.open_file)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.list_widget)

        # Bilgi Etiketi
        self.info_label = QLabel("Dosyaları buraya sürükleyip bırakabilirsiniz.")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.info_label)

    def set_target(self, table_name: str, record_id: int, user_id: int = 1):
        """Hangi kayıt için çalışacağını ayarlar."""
        self.target_table = table_name
        self.target_id = record_id
        self.current_user_id = user_id
        self.refresh_files()

    def refresh_files(self):
        """Dosya listesini yeniler."""
        if not self.target_table or not self.target_id:
            return

        self.list_widget.clear()

        session = SessionLocal()
        try:
            docs = DMSService.get_documents_for_object(
                session, self.target_table, self.target_id
            )
            for doc in docs:
                item = QListWidgetItem(doc.filename)
                item.setData(Qt.ItemDataRole.UserRole, doc.id)
                item.setData(Qt.ItemDataRole.UserRole + 1, doc.file_path)

                # İkon belirle
                icon_name = "file"
                if doc.extension in [".pdf"]:
                    icon_name = "pdf"  # Varsayılan ikon setinde varsa
                elif doc.extension in [".png", ".jpg", ".jpeg"]:
                    icon_name = "image"

                # Burada ikon setinden ikon çekilmeli, şimdilik varsayılan boş
                # item.setIcon(QIcon(ICONS.get(icon_name, "")))

                # Boyut bilgisi ekle
                size_mb = doc.file_size / (1024 * 1024)
                item.setToolTip(f"Boyut: {size_mb:.2f} MB\nEkleyen: {doc.created_by}")

                self.list_widget.addItem(item)
        except Exception as e:
            print(f"Dosya listeleme hatası: {e}")
        finally:
            session.close()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if not self.target_table or not self.target_id:
            return

        files = [u.toLocalFile() for u in event.mimeData().urls()]
        self.upload_files(files)

    def open_file_dialog(self):
        if not self.target_table or not self.target_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir kayıt seçin.")
            return

        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        if file_dialog.exec():
            filenames = file_dialog.selectedFiles()
            self.upload_files(filenames)

    def upload_files(self, file_paths):
        session = SessionLocal()
        try:
            for file_path in file_paths:
                if not os.path.exists(file_path):
                    continue

                filename = os.path.basename(file_path)

                with open(file_path, "rb") as f:
                    file_bytes = f.read()

                try:
                    DMSService.upload_document(
                        session,
                        file_bytes,
                        filename,
                        self.target_table,
                        self.target_id,
                        self.current_user_id,
                    )
                except ValueError as ve:
                    QMessageBox.warning(self, "Hata", str(ve))
                except Exception as e:
                    QMessageBox.critical(self, "Hata", f"Yükleme hatası: {e}")

            session.commit()
            self.refresh_files()

        except Exception as e:
            session.rollback()
            print(f"Genel yükleme hatası: {e}")
        finally:
            session.close()

    def open_file(self, item):
        file_path = item.data(Qt.ItemDataRole.UserRole + 1)
        if file_path and os.path.exists(file_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(file_path)))
        else:
            QMessageBox.warning(self, "Hata", "Dosya bulunamadı!")

    def show_context_menu(self, position):
        item = self.list_widget.itemAt(position)
        if not item:
            return

        menu = QMenu()
        open_action = menu.addAction("Aç")
        delete_action = menu.addAction("Sil")

        action = menu.exec(self.list_widget.mapToGlobal(position))

        if action == open_action:
            self.open_file(item)
        elif action == delete_action:
            self.delete_file(item)

    def delete_file(self, item):
        reply = QMessageBox.question(
            self,
            "Onay",
            "Bu dosyayı silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            doc_id = item.data(Qt.ItemDataRole.UserRole)
            session = SessionLocal()
            try:
                DMSService.delete_document(session, doc_id, self.current_user_id)
                session.commit()
                self.refresh_files()
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")
            finally:
                session.close()
