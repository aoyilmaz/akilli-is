from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QMessageBox
from modules.fixed_assets.services.asset_service import FixedAssetService
from .asset_list import FixedAssetList


class FixedAssetModule(QWidget):
    page_title = "Sabit Kıymetler"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = FixedAssetService()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()

        self.list_page = FixedAssetList()
        self.list_page.add_clicked.connect(self._on_add_clicked)
        self.list_page.edit_clicked.connect(self._on_edit_clicked)
        self.list_page.delete_clicked.connect(self._on_delete_clicked)
        self.list_page.depreciate_clicked.connect(self._on_depreciate_clicked)
        self.list_page.refresh_requested.connect(self.load_data)

        self.stack.addWidget(self.list_page)
        layout.addWidget(self.stack)

        # Load data initially
        self.load_data()

    def load_data(self):
        try:
            assets = self.service.get_all_assets()
            data = [asset.to_dict() for asset in assets]
            self.list_page.load_data(data)
        except Exception as e:
            # QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata oluştu: {e}")
            print(f"Error loading assets: {e}")

    def _on_add_clicked(self):
        from .asset_dialog import FixedAssetDialog

        dialog = FixedAssetDialog(self)
        if dialog.exec():
            data = dialog.get_result()
            if data:
                try:
                    self.service.create_asset(data)
                    self.load_data()
                    QMessageBox.information(
                        self, "Başarılı", "Demirbaş başarıyla eklendi."
                    )
                except Exception as e:
                    QMessageBox.critical(self, "Hata", f"Ekleme hatası: {e}")

    def _on_edit_clicked(self, asset_id: int):
        from .asset_dialog import FixedAssetDialog

        asset = self.service.get_asset(asset_id)
        if not asset:
            return

        dialog = FixedAssetDialog(self, asset.to_dict())
        if dialog.exec():
            data = dialog.get_result()
            if data:
                try:
                    self.service.update_asset(asset_id, data)
                    self.load_data()
                    QMessageBox.information(self, "Başarılı", "Demirbaş güncellendi.")
                except Exception as e:
                    QMessageBox.critical(self, "Hata", f"Güncelleme hatası: {e}")

    def _on_delete_clicked(self, asset_id: int):
        reply = QMessageBox.question(
            self,
            "Onay",
            "Bu demirbaş kartını silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.service.delete_asset(asset_id):
                    self.load_data()
                    QMessageBox.information(self, "Başarılı", "Demirbaş silindi.")
                else:
                    QMessageBox.warning(self, "Hata", "Silinemedi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")

    def _on_depreciate_clicked(self, asset_id: int):
        try:
            from datetime import date

            today = date.today()
            entry = self.service.calculate_depreciation(asset_id, today)

            if entry:
                QMessageBox.information(
                    self, "Başarılı", f"Amortisman hesaplandı: {entry.amount:,.2f} TL"
                )
                self.load_data()
            else:
                QMessageBox.warning(
                    self,
                    "Uyarı",
                    "Amortisman hesaplanamadı (Zaten hesaplanmış veya süre dolmuş olabilir).",
                )
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Hata: {e}")
