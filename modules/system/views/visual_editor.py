import logging
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsTextItem,
    QMenu,
    QGraphicsSceneContextMenuEvent,
    QInputDialog,
    QColorDialog,
    QFontDialog,
)
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QBrush

logger = logging.getLogger(__name__)

# Sabitler (Milimetreden Piksellere dönüşüm için)
# Ekranda 1mm yaklaşık 3.78px (96 DPI varsayımıyla)
# Ancak baskı hassasiyeti için daha yüksek DPI çalışabiliriz veya scale edebiliriz.
# Kolaylık olması açısından 1mm = 5px diyelim (zoom ile ayarlanır).
MM_TO_PX = 5


class LabelItemMixin:
    """Grafik nesneleri için ortak özellikler"""

    def __init__(self):
        self._item_type = "generic"
        self._data_key = None  # Veritabanı değişkeni (örn: {{ name }})

    def set_data_key(self, key: str):
        self._data_key = key

    def get_data_key(self) -> Optional[str]:
        return self._data_key


class DraggableTextItem(QGraphicsTextItem, LabelItemMixin):
    """Sürüklenebilir Metin Nesnesi"""

    def __init__(self, text="Metin", parent=None):
        super().__init__(text, parent)
        LabelItemMixin.__init__(self)
        self._item_type = "text"
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsFocusable
        )
        self.setDefaultTextColor(QColor("black"))
        # Font varsayılanı
        font = QFont("Arial", 12)
        self.setFont(font)

    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent):
        menu = QMenu()
        edit_action = menu.addAction("Düzenle")
        font_action = menu.addAction("Yazı Tipi")
        color_action = menu.addAction("Renk")
        delete_action = menu.addAction("Sil")

        selected = menu.exec(event.screenPos())

        if selected == edit_action:
            new_text, ok = QInputDialog.getText(
                None, "Metin Düzenle", "Metin:", text=self.toPlainText()
            )
            if ok:
                self.setPlainText(new_text)

        elif selected == font_action:
            ok, font = QFontDialog.getFont(self.font())
            if ok:
                self.setFont(font)

        elif selected == color_action:
            color = QColorDialog.getColor(self.defaultTextColor())
            if color.isValid():
                self.setDefaultTextColor(color)

        elif selected == delete_action:
            if self.scene():
                self.scene().removeItem(self)

    def to_html_style(self):
        """Bu nesnenin HTML stilini (CSS) döndürür"""
        pos = self.pos()
        font = self.font()

        x_mm = pos.x() / MM_TO_PX
        y_mm = pos.y() / MM_TO_PX

        style = f"position: absolute; left: {x_mm:.1f}mm; top: {y_mm:.1f}mm; "
        style += f"font-family: '{font.family()}'; font-size: {font.pointSize()}pt; "
        if font.bold():
            style += "font-weight: bold; "
        if font.italic():
            style += "font-style: italic; "

        color = self.defaultTextColor().name()
        style += f"color: {color}; "

        return style


class BarcodePlaceholderItem(QGraphicsRectItem, LabelItemMixin):
    """Barkod yer tutucu nesnesi"""

    def __init__(self, w=150, h=50, code_key="{{ barcode }}"):
        super().__init__(0, 0, w, h)
        LabelItemMixin.__init__(self)
        self._item_type = "barcode"
        self.set_data_key(code_key)

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsFocusable
        )
        self.setBrush(QBrush(QColor("#eee")))
        self.setPen(QPen(Qt.PenStyle.DashLine))

        # Etiket
        self.text_item = QGraphicsTextItem("BARCODE", self)
        self.text_item.setPos(10, 10)

    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent):
        menu = QMenu()
        resize_action = menu.addAction("Boyutlandır (150x50)")
        delete_action = menu.addAction("Sil")

        selected = menu.exec(event.screenPos())

        if selected == resize_action:
            self.setRect(0, 0, 150, 50)
        elif selected == delete_action:
            if self.scene():
                self.scene().removeItem(self)

    def to_html_style(self):
        pos = self.pos()
        rect = self.rect()

        x_mm = pos.x() / MM_TO_PX
        y_mm = pos.y() / MM_TO_PX
        w_mm = rect.width() / MM_TO_PX
        h_mm = rect.height() / MM_TO_PX  # Resmin yüksekliği

        # Resim olarak render edileceği için img tag
        return f'<img src="{{{{ barcode_path }}}}" style="position: absolute; left: {x_mm:.1f}mm; top: {y_mm:.1f}mm; width: {w_mm:.1f}mm; height: {h_mm:.1f}mm;">'


class LabelGraphicsScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundBrush(QBrush(QColor("white")))
        self.grid_size = 5 * MM_TO_PX  # 5mm grid
        self._page_rect = QRectF(0, 0, 500, 250)

    def set_page_rect(self, rect: QRectF):
        self._page_rect = rect
        self.update()

    def drawBackground(self, painter, rect):
        """Izgara çizimi"""
        super().drawBackground(painter, rect)

        # Grid sadece kağıt (page_rect) içinde görünsün istenirse logic burada değişir.
        # Şimdilik sonsuz grid yerine, page_rect'i baz alalım.

        # Grid sadece page_rect içinde çizilsin
        draw_rect = self._page_rect.intersected(rect)
        if draw_rect.isEmpty():
            return

        left = int(draw_rect.left()) - (int(draw_rect.left()) % int(self.grid_size))
        top = int(draw_rect.top()) - (int(draw_rect.top()) % int(self.grid_size))

        x = left
        while x < draw_rect.right():
            painter.setPen(QPen(QColor(220, 220, 220, 100)))
            painter.drawLine(x, draw_rect.top(), x, draw_rect.bottom())
            x += self.grid_size

        y = top
        while y < draw_rect.bottom():
            painter.setPen(QPen(QColor(220, 220, 220, 100)))
            painter.drawLine(draw_rect.left(), y, draw_rect.right(), y)
            y += self.grid_size


class VisualLabelEditor(QGraphicsView):
    """Görsel Editör Widget'ı"""

    content_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene_obj = LabelGraphicsScene(self)
        self.setScene(self.scene_obj)

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

        # Arka plan rengi (Workspace Gray)
        self.setBackgroundBrush(QBrush(QColor("#e0e0e0")))

        # Kağıt nesnesi
        self.paper_item = None

        # Sahne sınırlarını çiz (Örn: 100x50mm)
        self.setup_canvas(100, 50)

    def setup_canvas(self, w_mm, h_mm):
        """Tuval boyutunu ayarlar ve kağıt görünümü oluşturur"""
        self.scene_obj.clear()

        w_px = w_mm * MM_TO_PX
        h_px = h_mm * MM_TO_PX

        # Sahne boyutu: Biraz marj bırakalım ki gölge görünsün
        margin = 20
        self.scene_obj.setSceneRect(
            -margin, -margin, w_px + 2 * margin, h_px + 2 * margin
        )

        # Kağıt (White Page)
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect

        self.paper_item = QGraphicsRectItem(0, 0, w_px, h_px)
        self.paper_item.setBrush(QBrush(QColor("white")))
        self.paper_item.setPen(QPen(Qt.PenStyle.NoPen))
        self.paper_item.setZValue(-100)  # En altta

        # Gölge Efekti
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 5)
        self.paper_item.setGraphicsEffect(shadow)

        self.scene_obj.addItem(self.paper_item)

        # Grid bilgisini sahneye ver (Çizim kısıtlaması için)
        self.scene_obj.set_page_rect(QRectF(0, 0, w_px, h_px))

        # Merkezle
        # self.centerOn(w_px/2, h_px/2)

    # --- Formatlama Yardımcıları (Toolbar için) ---
    def _get_selected_text_items(self) -> List[DraggableTextItem]:
        return [
            item
            for item in self.scene_obj.selectedItems()
            if isinstance(item, DraggableTextItem)
        ]

    def set_selection_font_family(self, family: str):
        for item in self._get_selected_text_items():
            font = item.font()
            font.setFamily(family)
            item.setFont(font)
        self.content_changed.emit()

    def set_selection_font_size(self, size: int):
        for item in self._get_selected_text_items():
            font = item.font()
            font.setPointSize(size)
            item.setFont(font)
        self.content_changed.emit()

    def toggle_selection_bold(self):
        for item in self._get_selected_text_items():
            font = item.font()
            font.setBold(not font.bold())
            item.setFont(font)
        self.content_changed.emit()

    def toggle_selection_italic(self):
        for item in self._get_selected_text_items():
            font = item.font()
            font.setItalic(not font.italic())
            item.setFont(font)
        self.content_changed.emit()

    def set_selection_alignment(self, align: str):
        # QGraphicsTextItem basitçe HTML/Text tutar. Alignment desteği document().setDefaultTextOption ile olabilir
        # veya HTML sararak. Şimdilik basit tutalım (setTextWidth ve Alignment)
        pass

    def delete_selected_items(self):
        for item in self.scene_obj.selectedItems():
            self.scene_obj.removeItem(item)
        self.content_changed.emit()

    def add_text_item(self, text, x=10, y=10):
        item = DraggableTextItem(text)
        item.setPos(x * MM_TO_PX, y * MM_TO_PX)
        self.scene_obj.addItem(item)
        self.content_changed.emit()

    def add_barcode_item(self, key="{{ barcode }}"):
        item = BarcodePlaceholderItem(code_key=key)
        item.setPos(10 * MM_TO_PX, 30 * MM_TO_PX)
        self.scene_obj.addItem(item)
        self.content_changed.emit()

    def load_from_dict(self, data: Dict[str, Any]):
        """JSON verisinden sahneyi oluşturur"""
        # Sahneyi temizlemek yerine setup_canvas çağırıp kağıdı resetleyelim
        # Ancak setup_canvas clear() çağırıyor zaten.

        w_mm = data.get("width", 100)
        h_mm = data.get("height", 50)
        self.setup_canvas(w_mm, h_mm)

        for item_data in data.get("items", []):
            itype = item_data.get("type", "generic")
            x_mm = item_data.get("x", 0)
            y_mm = item_data.get("y", 0)

            if itype == "text":
                text = item_data.get("text", "Metin")
                item = DraggableTextItem(text)
                item.setPos(x_mm * MM_TO_PX, y_mm * MM_TO_PX)

                # Stil
                font = QFont(
                    item_data.get("font_family", "Arial"),
                    item_data.get("font_size", 12),
                )
                font.setBold(item_data.get("bold", False))
                font.setItalic(item_data.get("italic", False))
                item.setFont(font)

                if "color" in item_data:
                    item.setDefaultTextColor(QColor(item_data["color"]))

                self.scene_obj.addItem(item)

            elif itype == "barcode":
                key = item_data.get("data_key", "{{ barcode }}")
                w = item_data.get("width", 30)
                h = item_data.get("height", 10)

                item = BarcodePlaceholderItem(w * MM_TO_PX, h * MM_TO_PX, key)
                item.setPos(x_mm * MM_TO_PX, y_mm * MM_TO_PX)
                self.scene_obj.addItem(item)

        self.content_changed.emit()

    def to_dict(self) -> Dict[str, Any]:
        """Sahne verisini sözlük (JSON) formatında döndürür"""
        items_data = []

        # Z-Order'a göre sıralı (Alttan üste)
        items = self.scene_obj.items(Qt.SortOrder.AscendingOrder)

        for item in items:
            pos = item.pos()
            x_mm = pos.x() / MM_TO_PX
            y_mm = pos.y() / MM_TO_PX

            item_data = {"x": round(x_mm, 2), "y": round(y_mm, 2)}

            if isinstance(item, DraggableTextItem):
                font = item.font()
                item_data.update(
                    {
                        "type": "text",
                        "text": item.toPlainText(),
                        "font_family": font.family(),
                        "font_size": font.pointSize(),
                        "bold": font.bold(),
                        "italic": font.italic(),
                        "color": item.defaultTextColor().name(),
                    }
                )
            elif isinstance(item, BarcodePlaceholderItem):
                rect = item.rect()
                item_data.update(
                    {
                        "type": "barcode",
                        "width": round(rect.width() / MM_TO_PX, 2),
                        "height": round(rect.height() / MM_TO_PX, 2),
                        "data_key": item.get_data_key(),
                    }
                )

            items_data.append(item_data)

        return {
            "width": self.scene_obj.width() / MM_TO_PX,
            "height": self.scene_obj.height() / MM_TO_PX,
            "items": items_data,
        }

    def render_to_image(self) -> str:
        """Sahneyi resim dosyasına render eder ve yolunu döndürür"""
        import tempfile
        from PyQt6.QtGui import QImage, QPainter
        from PyQt6.QtCore import QSize

        # Sahne boyutu
        rect = self.scene_obj.sceneRect()
        if rect.isEmpty():
            return ""

        image = QImage(rect.size().toSize(), QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.scene_obj.render(painter)
        painter.end()

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            image.save(tmp.name)
            return tmp.name

    def generate_payload(self) -> str:
        """Sahnedeki nesneleri HTML'e dönüştürür"""
        html_parts = []

        # Container (Canvas) - Relative
        # Ancak LabelManager.render_template zaten bir container oluşturuyor.
        # Biz sadece içindeki absolute elementleri döndürelim.

        for item in self.scene_obj.items():
            if isinstance(item, DraggableTextItem):
                style = item.to_html_style()
                content = item.toPlainText()
                # Jinja değişkenlerini düzelt ({{...}} -> {{ ... }}) gerekirse
                html_parts.append(f'<div style="{style}">{content}</div>')

            elif isinstance(item, BarcodePlaceholderItem):
                html_parts.append(item.to_html_style())

        # Ters sıra (Z-Index sorunu olmaması için, GraphicsScene items yığın sırasına göre)
        # Genelde items() top-most first döner. HTML'de son eklenen üsttedir.
        # Bu yüzden listeyi ters çevirelim.
        html_parts.reverse()

        return "\n".join(html_parts)
