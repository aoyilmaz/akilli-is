import os
import sys
from abc import ABC, abstractmethod
from typing import List, Any, Dict

# Çıktı formatları için kütüphaneler
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import openpyxl

from PyQt6.QtWidgets import QMenu, QFileDialog, QMessageBox, QTableWidget
from PyQt6.QtGui import QAction


class ExportStrategy(ABC):
    """Dışa aktarma stratejisi arayüzü"""

    @abstractmethod
    def export(self, data: Any, filename: str, **kwargs):
        pass


class ExcelExportStrategy(ExportStrategy):
    """Excel'e aktarma stratejisi"""

    def export(self, data: Any, filename: str, **kwargs):
        # Data bir liste ise DataFrame'e çevir
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise ValueError(
                "Desteklenmeyen veri formatı (Liste veya DataFrame gerekli)"
            )

        # Excel'e kaydet
        df.to_excel(filename, index=False, engine="openpyxl")


class PDFListExportStrategy(ExportStrategy):
    """Basit PDF Listesi çıkarma stratejisi (ReportLab)"""

    def export(self, data: Any, filename: str, **kwargs):
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4

        # Türkçe font desteği (Eğer font dosyası varsa. Yoksa standart)
        # pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
        # c.setFont("Arial", 12)

        y = height - 50
        c.drawString(50, y, "Rapor Çıktısı")
        y -= 30

        # Basit satır yazdırma (Geliştirilebilir: Table kullanımı)
        if isinstance(data, list):
            for row in data:
                text = str(row)
                c.drawString(50, y, text[:100])  # Çok uzun satırları kes
                y -= 15
                if y < 50:
                    c.showPage()
                    y = height - 50

        c.save()


class ExportManager:
    """Dışa aktarma işlemlerini yöneten merkezi sınıf"""

    @staticmethod
    def create_export_menu(parent_widget, export_callback=None):
        """
        Bir butona eklemek için hazır Export menüsü oluşturur.

        Args:
            parent_widget: Menünün ekleneceği widget (genellikle butonun olduğu pencere)
            export_callback: Veri sağlayan fonksiyon. (format -> data) şeklinde çalışmalı.
        """
        menu = QMenu(parent_widget)

        # Excel
        action_excel = QAction("📊 Excel Olarak Kaydet", parent_widget)
        action_excel.triggered.connect(
            lambda: ExportManager._handle_export(
                parent_widget, "excel", export_callback
            )
        )
        menu.addAction(action_excel)

        # PDF
        action_pdf = QAction("📄 PDF Olarak Kaydet", parent_widget)
        action_pdf.triggered.connect(
            lambda: ExportManager._handle_export(parent_widget, "pdf", export_callback)
        )
        menu.addAction(action_pdf)

        return menu

    @staticmethod
    def _handle_export(parent, format_type, data_provider):
        if not data_provider:
            return

        try:
            # Veriyi al
            data = data_provider()
            if data is None or len(data) == 0:
                QMessageBox.warning(parent, "Uyarı", "Dışa aktarılacak veri yok!")
                return

            # Dosya kaydetme diyaloğu
            file_filter = ""
            default_ext = ""

            if format_type == "excel":
                file_filter = "Excel Dosyası (*.xlsx)"
                default_ext = ".xlsx"
            elif format_type == "pdf":
                file_filter = "PDF Dosyası (*.pdf)"
                default_ext = ".pdf"

            file_name, _ = QFileDialog.getSaveFileName(
                parent,
                "Dosyayı Kaydet",
                os.path.expanduser(f"~/Desktop/export{default_ext}"),
                file_filter,
            )

            if not file_name:
                return

            # Strateji seç ve uygula
            strategy = None
            if format_type == "excel":
                strategy = ExcelExportStrategy()
            elif format_type == "pdf":
                strategy = PDFListExportStrategy()

            if strategy:
                strategy.export(data, file_name)
                QMessageBox.information(
                    parent, "Başarılı", "Dosya başarıyla kaydedildi."
                )

                # Dosyayı otomatik aç (Opsiyonel - MacOS/Windows uyumlu)
                if sys.platform == "darwin":
                    os.system(f'open "{file_name}"')
                elif sys.platform == "win32":
                    os.startfile(file_name)

        except Exception as e:
            QMessageBox.critical(parent, "Hata", f"Dışa aktarma hatası:\n{str(e)}")

    @staticmethod
    def extract_data_from_table(
        table_widget: QTableWidget, include_headers=True
    ) -> List[Dict]:
        """QTableWidget'tan veriyi dict listesi olarak çeker"""
        data = []
        headers = []

        # Başlıkları al
        for col in range(table_widget.columnCount()):
            item = table_widget.horizontalHeaderItem(col)
            headers.append(item.text() if item else f"Kolon {col}")

        # Satırları al
        for row in range(table_widget.rowCount()):
            row_data = {}
            # Gizli satırları atla
            if table_widget.isRowHidden(row):
                continue

            for col in range(table_widget.columnCount()):
                item = table_widget.item(row, col)
                # Widget varsa (örn: buton) atla veya özel işlem yap
                val = item.text() if item else ""

                if include_headers:
                    row_data[headers[col]] = val
                else:
                    # Liste listesi istenirse farklı yapı kurulabilir
                    pass
            data.append(row_data)

        return data
