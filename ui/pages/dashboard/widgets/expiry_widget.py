"""
Akıllı İş - SKT (Son Kullanma Tarihi) Uyarı Widget'ı

Dashboard'da son kullanma tarihi yaklaşan veya geçmiş stokları gösterir.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from config.styles import COLORS, FONT_FAMILY_QT
from .base import BaseWidget, WidgetConfig


class ExpiryAlertWidget(BaseWidget):
    """
    SKT Uyarı Widget'ı

    Son kullanma tarihi yaklaşan (30 gün içinde) veya geçmiş stokları listeler.
    - Kırmızı: SKT geçmiş
    - Sarı: SKT 7 gün içinde
    - Turuncu: SKT 30 gün içinde
    """

    widget_code = "expiry_alert"
    widget_name = "SKT Uyarıları"
    widget_type = "list"
    widget_description = "Son kullanma tarihi yaklaşan stoklar"
    widget_icon = "calendar-xmark"
    min_size = (2, 2)
    default_size = (2, 2)
    max_size = (4, 4)
    refresh_interval = 300  # 5 dakika

    def __init__(
        self,
        config: Optional[WidgetConfig] = None,
        edit_mode: bool = False,
        parent: Optional[QWidget] = None,
    ):
        self._expiry_items: List[Dict[str, Any]] = []
        super().__init__(config, edit_mode, parent)

    def create_content(self):
        """Widget içeriğini oluşturur"""
        # Başlık bilgi satırı
        self.info_label = QLabel("Yükleniyor...")
        self.info_label.setFont(QFont(FONT_FAMILY_QT, 10))
        self.info_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.content_layout.addWidget(self.info_label)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            """
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
        """
        )

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(4)

        scroll.setWidget(self.scroll_content)
        self.content_layout.addWidget(scroll)

    def refresh_data(self):
        """Veriyi yeniler"""
        self.set_loading(True)

        try:
            self._expiry_items = self._fetch_expiry_data()
            self._update_display()
        except Exception as e:
            self.set_error(str(e))
        finally:
            self.set_loading(False)

    def _fetch_expiry_data(self) -> List[Dict[str, Any]]:
        """SKT yaklaşan stokları veritabanından çeker"""
        try:
            from database.base import get_session
            from database.models.inventory import StockBalance, Item

            session = get_session()
            now = datetime.now()
            future_30 = now + timedelta(days=30)

            # SKT'si 30 gün içinde veya geçmiş olan bakiyeler
            balances = (
                session.query(StockBalance)
                .join(Item)
                .filter(
                    StockBalance.expiry_date.isnot(None),
                    StockBalance.expiry_date <= future_30,
                    StockBalance.quantity > 0,
                )
                .order_by(StockBalance.expiry_date)
                .limit(20)
                .all()
            )

            result = []
            for balance in balances:
                item = balance.item
                warehouse = balance.warehouse

                days_left = (balance.expiry_date - now).days

                result.append(
                    {
                        "item_code": item.code if item else "?",
                        "item_name": item.name if item else "Bilinmiyor",
                        "lot_number": balance.lot_number or "-",
                        "quantity": float(balance.quantity),
                        "warehouse": warehouse.name if warehouse else "-",
                        "expiry_date": balance.expiry_date,
                        "days_left": days_left,
                    }
                )

            session.close()
            return result

        except Exception as e:
            print(f"SKT veri çekme hatası: {e}")
            return []

    def _update_display(self):
        """Görüntüyü günceller"""
        # Eski öğeleri temizle
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self._expiry_items:
            self.info_label.setText("✅ SKT sorunu olan stok yok")
            empty_label = QLabel("Tüm stoklar güvenli aralıkta")
            empty_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(empty_label)
            self.scroll_layout.addStretch()
            return

        # Özet bilgi
        expired_count = sum(1 for item in self._expiry_items if item["days_left"] < 0)
        warning_count = len(self._expiry_items) - expired_count

        if expired_count > 0:
            self.info_label.setText(
                f"⚠️ {expired_count} geçmiş, {warning_count} yaklaşan"
            )
            self.info_label.setStyleSheet(f"color: {COLORS['error']};")
        else:
            self.info_label.setText(f"⚠️ {warning_count} SKT yaklaşan stok")
            self.info_label.setStyleSheet(f"color: {COLORS['warning']};")

        # Öğeleri ekle
        for item in self._expiry_items:
            row = self._create_item_row(item)
            self.scroll_layout.addWidget(row)

        self.scroll_layout.addStretch()

    def _create_item_row(self, item: Dict[str, Any]) -> QFrame:
        """Tek bir stok satırı oluşturur"""
        frame = QFrame()
        frame.setFixedHeight(50)

        days_left = item["days_left"]

        # Renk belirleme
        if days_left < 0:
            # SKT geçmiş - kırmızı
            bg_color = "#7f1d1d"
            border_color = COLORS["error"]
            status_text = f"⛔ {abs(days_left)} gün geçti"
        elif days_left <= 7:
            # 7 gün içinde - sarı
            bg_color = "#713f12"
            border_color = COLORS["warning"]
            status_text = f"⚠️ {days_left} gün kaldı"
        else:
            # 30 gün içinde - turuncu
            bg_color = "#431407"
            border_color = "#f97316"
            status_text = f"📅 {days_left} gün kaldı"

        frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {bg_color};
                border-left: 3px solid {border_color};
                border-radius: 4px;
                padding: 4px;
            }}
        """
        )

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Sol: Ürün bilgisi
        left_layout = QVBoxLayout()
        left_layout.setSpacing(0)

        name_label = QLabel(f"{item['item_code']} - {item['item_name'][:25]}")
        name_label.setFont(QFont(FONT_FAMILY_QT, 10, QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        left_layout.addWidget(name_label)

        detail = f"Lot: {item['lot_number']} | {item['quantity']:.0f} adet"
        detail_label = QLabel(detail)
        detail_label.setFont(QFont(FONT_FAMILY_QT, 9))
        detail_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        left_layout.addWidget(detail_label)

        layout.addLayout(left_layout, stretch=1)

        # Sağ: SKT durumu
        right_layout = QVBoxLayout()
        right_layout.setSpacing(0)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        status_label = QLabel(status_text)
        status_label.setFont(QFont(FONT_FAMILY_QT, 9, QFont.Weight.Bold))
        status_label.setStyleSheet(f"color: {border_color};")
        right_layout.addWidget(status_label)

        expiry_str = item["expiry_date"].strftime("%d.%m.%Y")
        date_label = QLabel(expiry_str)
        date_label.setFont(QFont(FONT_FAMILY_QT, 9))
        date_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        right_layout.addWidget(date_label)

        layout.addLayout(right_layout)

        return frame
