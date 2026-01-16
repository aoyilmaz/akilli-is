"""
Birim Dönüştürücü - DPI bazlı mm/px/dot dönüşümleri
"""

from typing import Tuple


class UnitConverter:
    """Milimetre, piksel ve nokta (dot) dönüşümlerini yönetir"""

    # DPI Sabitleri
    SCREEN_DPI = 96           # Standart ekran
    THERMAL_DPI_203 = 203     # Zebra 203dpi (GK420, ZD420)
    THERMAL_DPI_300 = 300     # Zebra 300dpi (ZT410, ZT610)
    PDF_POINTS_PER_INCH = 72  # ReportLab point (1 inch = 72 points)

    # 1 inch = 25.4 mm
    MM_PER_INCH = 25.4

    @staticmethod
    def mm_to_px(mm: float, dpi: int = 96) -> float:
        """
        Milimetreyi piksele dönüştürür.

        Args:
            mm: Milimetre değeri
            dpi: Hedef DPI (varsayılan: 96 ekran)

        Returns:
            Piksel değeri

        Örnek:
            >>> UnitConverter.mm_to_px(25.4, 96)
            96.0  # 1 inch = 96px at 96dpi
        """
        return mm * dpi / UnitConverter.MM_PER_INCH

    @staticmethod
    def px_to_mm(px: float, dpi: int = 96) -> float:
        """
        Pikseli milimetreye dönüştürür.

        Args:
            px: Piksel değeri
            dpi: Kaynak DPI

        Returns:
            Milimetre değeri
        """
        return px * UnitConverter.MM_PER_INCH / dpi

    @staticmethod
    def mm_to_dots(mm: float, dpi: int = 203) -> int:
        """
        Milimetreyi yazıcı noktasına (dot) dönüştürür.
        ZPL komutları için yuvarlama yapılır.

        Args:
            mm: Milimetre değeri
            dpi: Yazıcı DPI (203 veya 300)

        Returns:
            Nokta (dot) değeri (int)
        """
        return round(mm * dpi / UnitConverter.MM_PER_INCH)

    @staticmethod
    def dots_to_mm(dots: int, dpi: int = 203) -> float:
        """
        Yazıcı noktasını milimetreye dönüştürür.

        Args:
            dots: Nokta değeri
            dpi: Yazıcı DPI

        Returns:
            Milimetre değeri
        """
        return dots * UnitConverter.MM_PER_INCH / dpi

    @staticmethod
    def mm_to_points(mm: float) -> float:
        """
        Milimetreyi ReportLab point'e dönüştürür.
        PDF çıktısı için kullanılır.

        Args:
            mm: Milimetre değeri

        Returns:
            Point değeri (72 points = 1 inch)
        """
        return mm * UnitConverter.PDF_POINTS_PER_INCH / UnitConverter.MM_PER_INCH

    @staticmethod
    def points_to_mm(points: float) -> float:
        """
        ReportLab point'i milimetreye dönüştürür.

        Args:
            points: Point değeri

        Returns:
            Milimetre değeri
        """
        return points * UnitConverter.MM_PER_INCH / UnitConverter.PDF_POINTS_PER_INCH

    @staticmethod
    def get_scale_factor(source_dpi: int, target_dpi: int) -> float:
        """
        İki DPI arasındaki ölçek faktörünü hesaplar.

        Args:
            source_dpi: Kaynak DPI
            target_dpi: Hedef DPI

        Returns:
            Ölçek faktörü
        """
        return target_dpi / source_dpi

    @classmethod
    def mm_to_screen_px(cls, mm: float) -> float:
        """Milimetreyi ekran pikselene dönüştürür (96 DPI)"""
        return cls.mm_to_px(mm, cls.SCREEN_DPI)

    @classmethod
    def screen_px_to_mm(cls, px: float) -> float:
        """Ekran pikselini milimetreye dönüştürür (96 DPI)"""
        return cls.px_to_mm(px, cls.SCREEN_DPI)

    @classmethod
    def size_mm_to_px(cls, width_mm: float, height_mm: float, dpi: int = 96) -> Tuple[float, float]:
        """
        Boyutları milimetreden piksele dönüştürür.

        Args:
            width_mm: Genişlik (mm)
            height_mm: Yükseklik (mm)
            dpi: Hedef DPI

        Returns:
            (width_px, height_px) tuple
        """
        return (cls.mm_to_px(width_mm, dpi), cls.mm_to_px(height_mm, dpi))

    @classmethod
    def size_px_to_mm(cls, width_px: float, height_px: float, dpi: int = 96) -> Tuple[float, float]:
        """
        Boyutları pikselden milimetreye dönüştürür.

        Args:
            width_px: Genişlik (px)
            height_px: Yükseklik (px)
            dpi: Kaynak DPI

        Returns:
            (width_mm, height_mm) tuple
        """
        return (cls.px_to_mm(width_px, dpi), cls.px_to_mm(height_px, dpi))
