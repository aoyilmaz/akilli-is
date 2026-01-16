import io
from typing import Optional
import barcode
from barcode.writer import ImageWriter
import qrcode
from PIL import Image


def generate_barcode(data: str, barcode_type: str = "code128") -> Image:
    """
    Verilen veri ile barkod görseli oluşturur.

    Args:
        data (str): Barkodlanacak veri
        barcode_type (str): Barkod tipi (code128, ean13, code39 vb.)

    Returns:
        Image: PIL Image nesnesi veya None
    """
    try:
        # Code128 en yaygın kullanılan tiptir
        barcode_class = barcode.get_barcode_class(barcode_type)

        # Writer ile görsel oluştur (Yazı olmadan, sadece çubuklar için write_text=False)
        writer = ImageWriter()
        my_barcode = barcode_class(data, writer=writer)

        # Bellekte dosya benzeri nesne oluştur
        buffer = io.BytesIO()
        my_barcode.write(
            buffer, options={"write_text": True, "font_size": 10, "text_distance": 5}
        )

        # Buffer'ı başa sar ve PIL Image olarak döndür
        buffer.seek(0)
        return Image.open(buffer)

    except Exception as e:
        print(f"Barkod oluşturma hatası: {e}")
        return None


def generate_qrcode(data: str, box_size=10, border=1) -> Image:
    """
    Verilen veri ile QR kodu oluşturur.

    Args:
        data (str): QR kodlanacak veri

    Returns:
        Image: PIL Image nesnesi
    """
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=box_size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        return img
    except Exception as e:
        print(f"QR kod oluşturma hatası: {e}")
        return None
