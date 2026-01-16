"""
RenderStrategy - Render stratejisi temel sınıfı
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

from ..items.base import LabelItem, LabelSize
from ..unit_converter import UnitConverter


@dataclass
class RenderContext:
    """Render bağlamı - dinamik veri bağlama için"""
    data: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = "") -> Any:
        """Değer alır, yoksa default döner"""
        # Nested key desteği (örn: "product.name")
        keys = key.split(".")
        value = self.data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value if value is not None else default

    def resolve(self, template: str) -> str:
        """
        {key} formatındaki şablonu çözümler.

        Örnek:
            "{Urun_Adi} - {SKT}" -> "Elma - 2026-12-31"
        """
        result = template
        # Basit {key} formatı
        for key, value in self.data.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result


@dataclass
class RenderOutput:
    """Render çıktısı"""
    success: bool
    data: Any = None  # bytes, str, QPixmap vb.
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class RenderStrategy(ABC):
    """
    Render stratejisi abstract base class.

    Alt sınıflar:
    - ScreenRenderer: Ekran önizleme (QPixmap)
    - PDFRenderer: ReportLab vektörel PDF
    - ZPLRenderer: Zebra ZPL II komutları
    """

    def __init__(self, dpi: int = 96):
        self._dpi = dpi

    @property
    def dpi(self) -> int:
        return self._dpi

    @dpi.setter
    def dpi(self, value: int):
        self._dpi = value

    @property
    @abstractmethod
    def name(self) -> str:
        """Renderer adı"""
        pass

    @property
    @abstractmethod
    def output_type(self) -> str:
        """Çıktı türü (örn: 'pixmap', 'pdf', 'zpl')"""
        pass

    @abstractmethod
    def render(
        self,
        items: List[LabelItem],
        label_size: LabelSize,
        context: Optional[RenderContext] = None
    ) -> RenderOutput:
        """
        Elemanları render eder.

        Args:
            items: Render edilecek elemanlar
            label_size: Etiket boyutu
            context: Veri bağlama bağlamı

        Returns:
            RenderOutput
        """
        pass

    def save_to_file(
        self,
        items: List[LabelItem],
        label_size: LabelSize,
        file_path: Union[str, Path],
        context: Optional[RenderContext] = None
    ) -> RenderOutput:
        """
        Render edip dosyaya kaydeder.

        Alt sınıflar override edebilir.
        """
        output = self.render(items, label_size, context)
        if not output.success:
            return output

        try:
            path = Path(file_path)
            if isinstance(output.data, bytes):
                path.write_bytes(output.data)
            elif isinstance(output.data, str):
                path.write_text(output.data, encoding="utf-8")
            else:
                return RenderOutput(
                    success=False,
                    error=f"Desteklenmeyen çıktı türü: {type(output.data)}"
                )

            return RenderOutput(
                success=True,
                data=str(path),
                metadata={"file_path": str(path), **output.metadata}
            )
        except Exception as e:
            return RenderOutput(success=False, error=str(e))

    def _mm_to_units(self, mm: float) -> float:
        """mm'i renderer birimine çevirir (varsayılan: piksel)"""
        return UnitConverter.mm_to_px(mm, self._dpi)

    def _resolve_item_data(
        self,
        item: LabelItem,
        context: Optional[RenderContext]
    ) -> str:
        """Item verisini bağlamla çözümler"""
        if context and item.data_key:
            return context.resolve(item.data_key)
        return ""
