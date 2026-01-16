import os
import tempfile
import sys
from typing import List, Dict, Any

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtGui import QTextDocument
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtCore import QSizeF

from utils.barcode_utils import generate_barcode
from database import SessionLocal
from database.models.common import LabelTemplate


class LabelManager:
    """Etiket yazdırma işlemlerini yöneten sınıf"""

    @staticmethod
    def render_template(
        content: str, item_data: Dict[str, Any], width_mm=100, height_mm=50
    ) -> str:
        """
        Şablon içeriğini verilen veri ile render eder ve HTML döndürür.
        Barkod üretimi de burada yapılır.
        """
        # Barkod üretimi
        if "barkod" in item_data or "code" in item_data or "barcode" in item_data:
            code_val = (
                item_data.get("barkod")
                or item_data.get("code")
                or item_data.get("barcode")
            )
            if code_val and "barcode_path" not in item_data:
                barcode_img = generate_barcode(code_val)
                if barcode_img:
                    with tempfile.NamedTemporaryFile(
                        suffix=".png", delete=False
                    ) as tmp:
                        barcode_img.save(tmp.name)
                        item_data["barcode_path"] = tmp.name

        # Render işlemi
        rendered = content
        for k, v in item_data.items():
            rendered = rendered.replace(f"{{{{ {k} }}}}", str(v))
            rendered = rendered.replace(f"{{{{{k}}}}}", str(v))

        # Container style
        style = (
            f"width: {width_mm}mm; "
            f"height: {height_mm}mm; "
            "border: 1px dashed #ccc; "
            "padding: 5px; "
            "box-sizing: border-box; "
            "overflow: hidden; "
            "page-break-inside: avoid; "
            "position: relative;"
        )

        return f'<div style="{style}">{rendered}</div>'

    @staticmethod
    def clean_temp_files(items: List[Dict[str, Any]]):
        """Geçici dosyaları temizler"""
        for item in items:
            if "barcode_path" in item and os.path.exists(item["barcode_path"]):
                try:
                    os.unlink(item["barcode_path"])
                except:
                    pass

    @staticmethod
    def print_from_template(parent, template_code: str, items: List[Dict[str, Any]]):
        """Veritabanındaki şablona göre etiket basar."""
        import json

        session = SessionLocal()
        try:
            template = (
                session.query(LabelTemplate).filter_by(code=template_code).first()
            )
            if not template:
                QMessageBox.warning(
                    parent, "Hata", f"Şablon bulunamadı: {template_code}"
                )
                return

            if not items:
                return

            file_name, _ = QFileDialog.getSaveFileName(
                parent,
                f"{template.name} Kaydet",
                os.path.expanduser(f"~/Desktop/{template.code}.pdf"),
                "PDF Dosyası (*.pdf)",
            )

            if not file_name:
                return

            # Şablon tipini kontrol et (JSON/Visual)
            is_visual = False
            visual_data = {}
            try:
                if template.content.strip().startswith("{"):
                    visual_data = json.loads(template.content)
                    is_visual = True
            except:
                pass

            if is_visual:
                # --- REPORTLAB İLE GÖRSEL BASKI ---
                try:
                    LabelManager.render_visual_pdf(
                        file_name,
                        visual_data,
                        items,
                        template.width_mm or 100,
                        template.height_mm or 50,
                    )

                    if sys.platform == "darwin":
                        os.system(f'open "{file_name}"')
                    elif sys.platform == "win32":
                        os.startfile(file_name)

                except Exception as e:
                    QMessageBox.critical(parent, "Hata", f"PDF Hatası: {e}")

            else:
                # --- MEVCUT HTML BASKI (FALLBACK) ---
                printer = QPrinter(QPrinter.PrinterMode.HighResolution)
                printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
                printer.setOutputFileName(file_name)

                # HTML Oluşturma
                full_html = "<html><head><style>body { margin: 0; padding: 0; }</style></head><body>"
                full_html += '<div style="display: flex; flex-wrap: wrap;">'

                w = template.width_mm if template.width_mm else 100
                h = template.height_mm if template.height_mm else 50

                for item in items:
                    try:
                        full_html += LabelManager.render_template(
                            template.content, item, w, h
                        )
                    except Exception as render_err:
                        print(f"Render error: {render_err}")
                        continue

                full_html += "</div></body></html>"

                doc = QTextDocument()
                doc.setHtml(full_html)
                doc.setPageSize(QSizeF(210, 297))  # A4
                doc.print(printer)

                LabelManager.clean_temp_files(items)

                if sys.platform == "darwin":
                    os.system(f'open "{file_name}"')
                elif sys.platform == "win32":
                    os.startfile(file_name)

        except Exception as e:
            QMessageBox.critical(parent, "Hata", f"Yazdırma hatası: {e}")
        finally:
            session.close()

    @staticmethod
    def render_visual_pdf(
        file_name: str,
        visual_data: Dict[str, Any],
        items: List[Dict[str, Any]],
        width_mm: int,
        height_mm: int,
    ):
        """
        JSON tabanlı görsel veriyi ReportLab ile PDF'e basar.
        DB'den bağımsız çalışabilir.
        """
        c = canvas.Canvas(file_name, pagesize=A4)
        page_w, page_h = A4

        lbl_w_mm = width_mm
        lbl_h_mm = height_mm
        lbl_w = lbl_w_mm * mm
        lbl_h = lbl_h_mm * mm

        # Sayfadaki konumlar
        current_x = 10 * mm
        current_y = page_h - 10 * mm - lbl_h

        cols = int((page_w - 20 * mm) / lbl_w)
        if cols < 1:
            cols = 1

        col_idx = 0

        for item_data in items:
            # Etiket çerçevesi
            c.setLineWidth(0.5)
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.rect(current_x, current_y, lbl_w, lbl_h)
            c.setStrokeColorRGB(0, 0, 0)  # Reset

            # Öğeleri çiz
            for v_item in visual_data.get("items", []):
                vx = v_item.get("x", 0) * mm
                vy = v_item.get("y", 0) * mm

                item_type = v_item.get("type")

                if item_type == "text":
                    text = v_item.get("text", "")
                    # Değişken değişimi
                    for k, v in item_data.items():
                        text = text.replace(f"{{{{ {k} }}}}", str(v))
                        text = text.replace(f"{{{{{k}}}}}", str(v))

                    font_family = v_item.get("font_family", "Helvetica")
                    font_size = v_item.get("font_size", 12)

                    c.setFont("Helvetica", font_size)
                    if v_item.get("bold"):
                        c.setFont("Helvetica-Bold", font_size)
                    # Italic support via oblique if needed

                    # Y koordinatı düzeltmesi
                    draw_y = lbl_h - vy - font_size

                    c.setFillColor(v_item.get("color", "black"))
                    c.drawString(current_x + vx, current_y + draw_y, text)

                elif item_type == "barcode":
                    key = v_item.get("data_key", "{{ barcode }}")
                    key = key.replace("{{ ", "").replace(" }}", "")
                    code_val = item_data.get(key)

                    bw = v_item.get("width", 30) * mm
                    bh = v_item.get("height", 10) * mm

                    if code_val:
                        barcode_img = generate_barcode(str(code_val))
                        if barcode_img:
                            with tempfile.NamedTemporaryFile(
                                suffix=".png", delete=False
                            ) as tmp:
                                barcode_img.save(tmp.name)
                                draw_y = lbl_h - vy - bh
                                c.drawImage(
                                    tmp.name,
                                    current_x + vx,
                                    current_y + draw_y,
                                    width=bw,
                                    height=bh,
                                )
                                os.unlink(tmp.name)

            # Konum güncelle
            col_idx += 1
            if col_idx >= cols:
                col_idx = 0
                current_x = 10 * mm
                current_y -= lbl_h + 5 * mm
            else:
                current_x += lbl_w + 5 * mm

            # Sayfa sonu
            if current_y < 10 * mm:
                c.showPage()
                current_y = page_h - 10 * mm - lbl_h
                current_x = 10 * mm
                col_idx = 0

        c.save()

    @staticmethod
    def print_product_labels(parent, items: List[Dict]):
        """
        Seçili ürünler için etiket PDF'i oluşturur.

        Args:
            items: Etiket basılacak ürünlerin listesi (Code, Name, Price vb. içermeli)
        """
        if not items:
            QMessageBox.warning(parent, "Uyarı", "Etiket basılacak ürün seçilmedi!")
            return

        try:
            file_name, _ = QFileDialog.getSaveFileName(
                parent,
                "Etiketleri Kaydet",
                os.path.expanduser("~/Desktop/etiketler.pdf"),
                "PDF Dosyası (*.pdf)",
            )

            if not file_name:
                return

            c = canvas.Canvas(file_name, pagesize=A4)
            width, height = A4

            # Etiket ayarları (Örn: 3 sütunlu, 40mm yükseklik)
            margin_x = 10 * mm
            margin_y = 10 * mm
            col_width = (width - 2 * margin_x) / 3
            row_height = 40 * mm

            x = margin_x
            y = height - margin_y - row_height

            for item in items:
                # Çerçeve çiz
                c.rect(x, y, col_width - 2 * mm, row_height - 2 * mm)

                # Ürün Adı (Kısa)
                name = item.get("Stok Adı", "Ürün")[:20]
                c.setFont("Helvetica-Bold", 10)
                c.drawString(x + 5 * mm, y + row_height - 10 * mm, name)

                # Fiyat
                price = item.get("Satış Fiyatı", "")
                c.setFont("Helvetica", 12)
                c.drawString(x + 5 * mm, y + row_height - 15 * mm, f"{price}")

                # Barkod (Code128)
                code = item.get("Kod", "0000")
                if code:
                    barcode_img = generate_barcode(code)
                    if barcode_img:
                        # Geçici dosyaya kaydet ve PDF'e ekle
                        with tempfile.NamedTemporaryFile(
                            suffix=".png", delete=False
                        ) as tmp:
                            barcode_img.save(tmp.name)
                            # Görüntüyü boyutlandırıp ekle
                            c.drawImage(
                                tmp.name,
                                x + 5 * mm,
                                y + 5 * mm,
                                width=40 * mm,
                                height=15 * mm,
                            )
                            os.unlink(tmp.name)

                # Konum güncelleme
                x += col_width
                if x > width - margin_x - col_width:
                    x = margin_x
                    y -= row_height

                # Sayfa sonu kontrolü
                if y < margin_y:
                    c.showPage()
                    y = height - margin_y - row_height

            c.save()

            QMessageBox.information(parent, "Başarılı", "Etiketler oluşturuldu.")

            # Dosyayı aç
            if sys.platform == "darwin":
                os.system(f'open "{file_name}"')
            elif sys.platform == "win32":
                os.startfile(file_name)

        except Exception as e:
            QMessageBox.critical(parent, "Hata", f"Etiket oluşturma hatası:\n{str(e)}")

    @staticmethod
    def print_work_order_labels(parent, items: List[Dict]):
        """
        Seçili iş emirleri için refakatçi etiketi oluşturur.
        """
        if not items:
            QMessageBox.warning(parent, "Uyarı", "Etiket basılacak iş emri seçilmedi!")
            return

        try:
            file_name, _ = QFileDialog.getSaveFileName(
                parent,
                "İş Emri Etiketlerini Kaydet",
                os.path.expanduser("~/Desktop/uretim_etiketleri.pdf"),
                "PDF Dosyası (*.pdf)",
            )

            if not file_name:
                return

            c = canvas.Canvas(file_name, pagesize=A4)
            width, height = A4

            # Etiket ayarları (Daha büyük etiket: 2 sütunlu, 70mm yükseklik)
            margin_x = 10 * mm
            margin_y = 10 * mm
            col_width = (width - 2 * margin_x) / 2
            row_height = 70 * mm

            x = margin_x
            y = height - margin_y - row_height

            for item in items:
                # Çerçeve çiz
                c.rect(x, y, col_width - 5 * mm, row_height - 5 * mm)

                # Başlık: İş Emri
                c.setFont("Helvetica-Bold", 14)
                c.drawString(
                    x + 5 * mm, y + row_height - 10 * mm, "İŞ EMRİ / REFAKATÇİ KARTI"
                )

                # WO No
                wo_no = item.get("İş Emri No", "")
                c.setFont("Helvetica-Bold", 12)
                c.drawString(x + 5 * mm, y + row_height - 20 * mm, f"No: {wo_no}")

                # Ürün
                product = item.get("Mamul", "Ürün")[:30]
                c.setFont("Helvetica", 10)
                c.drawString(x + 5 * mm, y + row_height - 30 * mm, f"Ürün: {product}")

                # Miktar ve Tarih
                qty = item.get("Miktar", "")
                date_val = item.get("Planlanan Bitiş", "")
                c.drawString(x + 5 * mm, y + row_height - 40 * mm, f"Miktar: {qty}")
                c.drawString(x + 5 * mm, y + row_height - 45 * mm, f"Tarih: {date_val}")

                # Barkod (WO No)
                if wo_no:
                    barcode_img = generate_barcode(wo_no)
                    if barcode_img:
                        with tempfile.NamedTemporaryFile(
                            suffix=".png", delete=False
                        ) as tmp:
                            barcode_img.save(tmp.name)
                            c.drawImage(
                                tmp.name,
                                x + 5 * mm,
                                y + 5 * mm,
                                width=50 * mm,
                                height=20 * mm,
                            )
                            os.unlink(tmp.name)

                # Konum güncelleme
                x += col_width
                if x > width - margin_x - col_width:
                    x = margin_x
                    y -= row_height

                # Sayfa sonu kontrolü
                if y < margin_y:
                    c.showPage()
                    y = height - margin_y - row_height

            c.save()

            QMessageBox.information(
                parent, "Başarılı", "İş emri etiketleri oluşturuldu."
            )

            if sys.platform == "darwin":
                os.system(f'open "{file_name}"')
            elif sys.platform == "win32":
                os.startfile(file_name)

        except Exception as e:
            QMessageBox.critical(parent, "Hata", f"Etiket oluşturma hatası:\n{str(e)}")
