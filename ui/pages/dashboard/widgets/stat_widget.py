"""
Akıllı İş - StatWidget

İstatistik gösterge widget'ı. Sayısal değerleri kart formatında gösterir.
"""

from typing import Optional, Callable, Any
from decimal import Decimal

from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from config.styles import COLORS, FONT_FAMILY_QT
from .base import BaseWidget, WidgetConfig


class StatWidget(BaseWidget):
    """
    İstatistik gösterge widget'ı

    Tek bir sayısal değeri büyük fontla gösterir.
    Opsiyonel olarak değişim yüzdesi ve ikon gösterebilir.
    """

    widget_code = "stat_generic"
    widget_name = "İstatistik"
    widget_type = "stat"
    widget_description = "Sayısal değer göstergesi"
    widget_icon = "chart-simple"
    min_size = (1, 1)
    default_size = (1, 1)
    max_size = (2, 1)
    refresh_interval = 300  # 5 dakika

    def __init__(
        self,
        config: Optional[WidgetConfig] = None,
        edit_mode: bool = False,
        parent: Optional[QWidget] = None,
        # Özel parametreler
        value_getter: Optional[Callable[[], Any]] = None,
        value_formatter: Optional[Callable[[Any], str]] = None,
        trend_getter: Optional[Callable[[], float]] = None,
    ):
        self._value_getter = value_getter
        self._value_formatter = value_formatter or str
        self._trend_getter = trend_getter
        self._current_value = None
        self._current_trend = None

        super().__init__(config, edit_mode, parent)

    def create_content(self):
        """Widget içeriğini oluşturur"""
        # Değer
        self.value_label = QLabel("--")
        self.value_label.setFont(QFont(FONT_FAMILY_QT, 28, QFont.Weight.Bold))
        self.value_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.value_label)

        # Trend (opsiyonel)
        self.trend_label = QLabel("")
        self.trend_label.setFont(QFont(FONT_FAMILY_QT, 11))
        self.trend_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.trend_label.setVisible(False)
        self.content_layout.addWidget(self.trend_label)

        # Açıklama (config'den)
        self.description_label = QLabel("")
        self.description_label.setFont(QFont(FONT_FAMILY_QT, 10))
        self.description_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.description_label.setWordWrap(True)
        self.content_layout.addWidget(self.description_label)

        self.content_layout.addStretch()

    def refresh_data(self):
        """Veriyi yeniler"""
        self.set_loading(True)

        try:
            if self._value_getter:
                self._current_value = self._value_getter()
                formatted_value = self._value_formatter(self._current_value)
                self.value_label.setText(formatted_value)

            if self._trend_getter:
                self._current_trend = self._trend_getter()
                self._update_trend()

            # Config'den açıklama
            description = self._config.config.get("description", "")
            self.description_label.setText(description)

        except Exception as e:
            print(f"StatWidget veri yenileme hatası: {e}")
            self.value_label.setText("Hata")
        finally:
            self.set_loading(False)

    def _update_trend(self):
        """Trend göstergesini günceller"""
        if self._current_trend is None:
            self.trend_label.setVisible(False)
            return

        self.trend_label.setVisible(True)

        if self._current_trend > 0:
            self.trend_label.setText(f"↑ %{self._current_trend:.1f}")
            self.trend_label.setStyleSheet(f"color: {COLORS['success']};")
        elif self._current_trend < 0:
            self.trend_label.setText(f"↓ %{abs(self._current_trend):.1f}")
            self.trend_label.setStyleSheet(f"color: {COLORS['danger']};")
        else:
            self.trend_label.setText("→ %0")
            self.trend_label.setStyleSheet(f"color: {COLORS['text_secondary']};")

    def set_value(self, value: Any, trend: Optional[float] = None):
        """Değeri manuel olarak ayarlar"""
        self._current_value = value
        self._current_trend = trend

        formatted_value = self._value_formatter(value)
        self.value_label.setText(formatted_value)

        if trend is not None:
            self._update_trend()


# Özelleştirilmiş StatWidget'lar


class SalesTodayWidget(StatWidget):
    """Bugünkü satışlar widget'ı"""

    widget_code = "stat_sales_today"
    widget_name = "Bugünkü Satışlar"
    widget_description = "Günlük satış toplamı"
    widget_icon = "shopping-cart"
    required_permission = "sales.view"

    def __init__(self, config=None, edit_mode=False, parent=None):
        super().__init__(
            config=config,
            edit_mode=edit_mode,
            parent=parent,
            value_formatter=lambda v: f"₺{v:,.2f}" if v else "₺0",
        )

    def refresh_data(self):
        """Satış verilerini çeker"""
        self.set_loading(True)
        try:
            from database.base import get_session
            from database.models.sales import Invoice
            from sqlalchemy import func
            from datetime import date

            session = get_session()
            try:
                total = session.query(func.sum(Invoice.total)).filter(
                    func.date(Invoice.created_at) == date.today(), Invoice.is_active
                ).scalar() or Decimal("0")

                self.set_value(float(total))
                self.description_label.setText("Bugünkü toplam satış")
            finally:
                session.close()
        except Exception as e:
            print(f"SalesTodayWidget hatası: {e}")
            self.value_label.setText("--")
        finally:
            self.set_loading(False)


class PendingOrdersWidget(StatWidget):
    """Bekleyen siparişler widget'ı"""

    widget_code = "stat_pending_orders"
    widget_name = "Bekleyen Siparişler"
    widget_description = "Onay bekleyen sipariş sayısı"
    widget_icon = "clock"
    required_permission = "sales.view"

    def __init__(self, config=None, edit_mode=False, parent=None):
        super().__init__(
            config=config,
            edit_mode=edit_mode,
            parent=parent,
            value_formatter=lambda v: str(v) if v else "0",
        )

    def refresh_data(self):
        """Bekleyen sipariş verilerini çeker"""
        self.set_loading(True)
        try:
            from database.base import get_session
            from database.models.sales import SalesOrder, SalesOrderStatus

            session = get_session()
            try:
                count = (
                    session.query(SalesOrder)
                    .filter(
                        SalesOrder.status == SalesOrderStatus.DRAFT,
                        SalesOrder.is_active,
                    )
                    .count()
                )

                self.set_value(count)
                self.description_label.setText("Taslak sipariş")
            finally:
                session.close()
        except Exception as e:
            print(f"PendingOrdersWidget hatası: {e}")
            self.value_label.setText("--")
        finally:
            self.set_loading(False)


class LowStockWidget(StatWidget):
    """Düşük stok uyarısı widget'ı"""

    widget_code = "stat_low_stock"
    widget_name = "Stok Uyarıları"
    widget_description = "Kritik seviyedeki stok sayısı"
    widget_icon = "exclamation-triangle"
    required_permission = "inventory.view"

    def __init__(self, config=None, edit_mode=False, parent=None):
        super().__init__(
            config=config,
            edit_mode=edit_mode,
            parent=parent,
            value_formatter=lambda v: str(v) if v else "0",
        )

    def refresh_data(self):
        """Düşük stok verilerini çeker"""
        self.set_loading(True)
        try:
            from database.base import get_session
            from database.models.inventory import Item, StockBalance
            from sqlalchemy import func

            session = get_session()
            try:
                # Minimum stok seviyesinin altında olanları say
                count = (
                    session.query(Item)
                    .filter(Item.is_active, Item.min_stock > 0)
                    .join(StockBalance, Item.id == StockBalance.item_id, isouter=True)
                    .group_by(Item.id)
                    .having(
                        func.coalesce(func.sum(StockBalance.quantity), 0)
                        < Item.min_stock
                    )
                    .count()
                )

                self.set_value(count)
                self.description_label.setText("Kritik stok seviyesi")

                # Renk değiştir
                if count > 0:
                    self.value_label.setStyleSheet(f"color: {COLORS['danger']};")
                else:
                    self.value_label.setStyleSheet(f"color: {COLORS['success']};")
            finally:
                session.close()
        except Exception as e:
            print(f"LowStockWidget hatası: {e}")
            self.value_label.setText("--")
        finally:
            self.set_loading(False)


class OpenWorkOrdersWidget(StatWidget):
    """Açık iş emirleri widget'ı"""

    widget_code = "stat_open_work_orders"
    widget_name = "Açık İş Emirleri"
    widget_description = "Devam eden iş emri sayısı"
    widget_icon = "cogs"
    required_permission = "production.view"

    def __init__(self, config=None, edit_mode=False, parent=None):
        super().__init__(
            config=config,
            edit_mode=edit_mode,
            parent=parent,
            value_formatter=lambda v: str(v) if v else "0",
        )

    def refresh_data(self):
        """Açık iş emri verilerini çeker"""
        self.set_loading(True)
        try:
            from database.base import get_session
            from database.models.production import WorkOrder, WorkOrderStatus

            session = get_session()
            try:
                count = (
                    session.query(WorkOrder)
                    .filter(
                        WorkOrder.status.in_(
                            [
                                WorkOrderStatus.DRAFT,
                                WorkOrderStatus.PLANNED,
                                WorkOrderStatus.IN_PROGRESS,
                            ]
                        ),
                        WorkOrder.is_active,
                    )
                    .count()
                )

                self.set_value(count)
                self.description_label.setText("Devam eden iş emri")
            finally:
                session.close()
        except Exception as e:
            print(f"OpenWorkOrdersWidget hatası: {e}")
            self.value_label.setText("--")
        finally:
            self.set_loading(False)


class TodayWarehouseEntryWidget(StatWidget):
    """Bugün depoya giren malzeme widget'ı"""

    widget_code = "stat_warehouse_entry"
    widget_name = "Depoya Giriş"
    widget_description = "Bugün depoya giren malzeme sayısı"
    widget_icon = "arrow-down"
    required_permission = "inventory.view"

    def __init__(self, config=None, edit_mode=False, parent=None):
        super().__init__(
            config=config,
            edit_mode=edit_mode,
            parent=parent,
            value_formatter=lambda v: str(v) if v else "0",
        )

    def refresh_data(self):
        """Bugün depoya giren malzemeleri çeker"""
        self.set_loading(True)
        try:
            from database.base import get_session
            from database.models.inventory import StockMovement, MovementType
            from sqlalchemy import func
            from datetime import date

            session = get_session()
            try:
                count = (
                    session.query(StockMovement)
                    .filter(
                        func.date(StockMovement.created_at) == date.today(),
                        StockMovement.movement_type == MovementType.IN,
                        StockMovement.is_active,
                    )
                    .count()
                )

                self.set_value(count)
                self.description_label.setText("Bugün giren hareket")
            finally:
                session.close()
        except Exception as e:
            print(f"TodayWarehouseEntryWidget hatası: {e}")
            self.value_label.setText("--")
        finally:
            self.set_loading(False)


class TodayWarehouseExitWidget(StatWidget):
    """Bugün depodan çıkan malzeme widget'ı"""

    widget_code = "stat_warehouse_exit"
    widget_name = "Depodan Çıkış"
    widget_description = "Bugün depodan çıkan malzeme sayısı"
    widget_icon = "arrow-up"
    required_permission = "inventory.view"

    def __init__(self, config=None, edit_mode=False, parent=None):
        super().__init__(
            config=config,
            edit_mode=edit_mode,
            parent=parent,
            value_formatter=lambda v: str(v) if v else "0",
        )

    def refresh_data(self):
        """Bugün depodan çıkan malzemeleri çeker"""
        self.set_loading(True)
        try:
            from database.base import get_session
            from database.models.inventory import StockMovement, MovementType
            from sqlalchemy import func
            from datetime import date

            session = get_session()
            try:
                count = (
                    session.query(StockMovement)
                    .filter(
                        func.date(StockMovement.created_at) == date.today(),
                        StockMovement.movement_type == MovementType.OUT,
                        StockMovement.is_active,
                    )
                    .count()
                )

                self.set_value(count)
                self.description_label.setText("Bugün çıkan hareket")
            finally:
                session.close()
        except Exception as e:
            print(f"TodayWarehouseExitWidget hatası: {e}")
            self.value_label.setText("--")
        finally:
            self.set_loading(False)


class TodayPurchasesWidget(StatWidget):
    """Bugünkü satınalmalar widget'ı"""

    widget_code = "stat_today_purchases"
    widget_name = "Bugünkü Satınalmalar"
    widget_description = "Bugün yapılan satınalma tutarı"
    widget_icon = "shopping-bag"
    required_permission = "purchasing.view"

    def __init__(self, config=None, edit_mode=False, parent=None):
        super().__init__(
            config=config,
            edit_mode=edit_mode,
            parent=parent,
            value_formatter=lambda v: f"₺{v:,.2f}" if v else "₺0",
        )

    def refresh_data(self):
        """Bugünkü satınalma verilerini çeker"""
        self.set_loading(True)
        try:
            from database.base import get_session
            from database.models.purchasing import PurchaseOrder, PurchaseOrderStatus
            from sqlalchemy import func
            from datetime import date

            session = get_session()
            try:
                total = session.query(func.sum(PurchaseOrder.total)).filter(
                    func.date(PurchaseOrder.created_at) == date.today(),
                    PurchaseOrder.is_active,
                ).scalar() or Decimal("0")

                self.set_value(float(total))
                self.description_label.setText("Bugünkü satınalma tutarı")
            finally:
                session.close()
        except Exception as e:
            print(f"TodayPurchasesWidget hatası: {e}")
            self.value_label.setText("--")
        finally:
            self.set_loading(False)


class PendingPurchaseOrdersWidget(StatWidget):
    """Bekleyen satınalma siparişleri widget'ı"""

    widget_code = "stat_pending_purchases"
    widget_name = "Bekleyen Satınalmalar"
    widget_description = "Onay bekleyen satınalma sipariş sayısı"
    widget_icon = "hourglass"
    required_permission = "purchasing.view"

    def __init__(self, config=None, edit_mode=False, parent=None):
        super().__init__(
            config=config,
            edit_mode=edit_mode,
            parent=parent,
            value_formatter=lambda v: str(v) if v else "0",
        )

    def refresh_data(self):
        """Bekleyen satınalma sipariş verilerini çeker"""
        self.set_loading(True)
        try:
            from database.base import get_session
            from database.models.purchasing import PurchaseOrder, PurchaseOrderStatus

            session = get_session()
            try:
                count = (
                    session.query(PurchaseOrder)
                    .filter(
                        PurchaseOrder.status == PurchaseOrderStatus.PENDING,
                        PurchaseOrder.is_active,
                    )
                    .count()
                )

                self.set_value(count)
                self.description_label.setText("Onay bekleyen sipariş")
            finally:
                session.close()
        except Exception as e:
            print(f"PendingPurchaseOrdersWidget hatası: {e}")
            self.value_label.setText("--")
        finally:
            self.set_loading(False)


class TodayShipmentsWidget(StatWidget):
    """Bugünkü sevkiyatlar widget'ı"""

    widget_code = "stat_today_shipments"
    widget_name = "Bugünkü Sevkiyatlar"
    widget_description = "Bugün yapılan sevkiyat sayısı"
    widget_icon = "truck"
    required_permission = "sales.view"

    def __init__(self, config=None, edit_mode=False, parent=None):
        super().__init__(
            config=config,
            edit_mode=edit_mode,
            parent=parent,
            value_formatter=lambda v: str(v) if v else "0",
        )

    def refresh_data(self):
        """Bugünkü sevkiyat verilerini çeker"""
        self.set_loading(True)
        try:
            from database.base import get_session
            from database.models.sales import Shipment
            from sqlalchemy import func
            from datetime import date

            session = get_session()
            try:
                count = (
                    session.query(Shipment)
                    .filter(
                        func.date(Shipment.ship_date) == date.today(),
                        Shipment.is_active,
                    )
                    .count()
                )

                self.set_value(count)
                self.description_label.setText("Bugün yapılan sevkiyat")
            finally:
                session.close()
        except Exception as e:
            print(f"TodayShipmentsWidget hatası: {e}")
            self.value_label.setText("--")
        finally:
            self.set_loading(False)


class PendingShipmentsWidget(StatWidget):
    """Bekleyen sevkiyatlar widget'ı"""

    widget_code = "stat_pending_shipments"
    widget_name = "Bekleyen Sevkiyatlar"
    widget_description = "Sevk edilmemiş sipariş sayısı"
    widget_icon = "box"
    required_permission = "sales.view"

    def __init__(self, config=None, edit_mode=False, parent=None):
        super().__init__(
            config=config,
            edit_mode=edit_mode,
            parent=parent,
            value_formatter=lambda v: str(v) if v else "0",
        )

    def refresh_data(self):
        """Bekleyen sevkiyat verilerini çeker"""
        self.set_loading(True)
        try:
            from database.base import get_session
            from database.models.sales import SalesOrder, SalesOrderStatus

            session = get_session()
            try:
                # Onaylanmış ama sevk edilmemiş siparişler
                count = (
                    session.query(SalesOrder)
                    .filter(
                        SalesOrder.status == SalesOrderStatus.APPROVED,
                        SalesOrder.is_active,
                    )
                    .count()
                )

                self.set_value(count)
                self.description_label.setText("Sevk bekleyen sipariş")

                if count > 0:
                    self.value_label.setStyleSheet(f"color: {COLORS['warning']};")
                else:
                    self.value_label.setStyleSheet(f"color: {COLORS['text_primary']};")
            finally:
                session.close()
        except Exception as e:
            print(f"PendingShipmentsWidget hatası: {e}")
            self.value_label.setText("--")
        finally:
            self.set_loading(False)


class TodayProductionWidget(StatWidget):
    """Bugünkü üretim widget'ı"""

    widget_code = "stat_today_production"
    widget_name = "Bugünkü Üretim"
    widget_description = "Bugün tamamlanan iş emri sayısı"
    widget_icon = "industry"
    required_permission = "production.view"

    def __init__(self, config=None, edit_mode=False, parent=None):
        super().__init__(
            config=config,
            edit_mode=edit_mode,
            parent=parent,
            value_formatter=lambda v: str(v) if v else "0",
        )

    def refresh_data(self):
        """Bugünkü üretim verilerini çeker"""
        self.set_loading(True)
        try:
            from database.base import get_session
            from database.models.production import WorkOrder, WorkOrderStatus
            from sqlalchemy import func
            from datetime import date

            session = get_session()
            try:
                count = (
                    session.query(WorkOrder)
                    .filter(
                        func.date(WorkOrder.actual_end_date) == date.today(),
                        WorkOrder.status == WorkOrderStatus.COMPLETED,
                        WorkOrder.is_active,
                    )
                    .count()
                )

                self.set_value(count)
                self.description_label.setText("Bugün tamamlanan iş emri")
            finally:
                session.close()
        except Exception as e:
            print(f"TodayProductionWidget hatası: {e}")
            self.value_label.setText("--")
        finally:
            self.set_loading(False)


class ActiveCustomersWidget(StatWidget):
    """Aktif müşteriler widget'ı"""

    widget_code = "stat_active_customers"
    widget_name = "Aktif Müşteriler"
    widget_description = "Sistemdeki aktif müşteri sayısı"
    widget_icon = "users"
    required_permission = "sales.view"

    def __init__(self, config=None, edit_mode=False, parent=None):
        super().__init__(
            config=config,
            edit_mode=edit_mode,
            parent=parent,
            value_formatter=lambda v: str(v) if v else "0",
        )

    def refresh_data(self):
        """Aktif müşteri verilerini çeker"""
        self.set_loading(True)
        try:
            from database.base import get_session
            from database.models.common import Contact, ContactType

            session = get_session()
            try:
                count = (
                    session.query(Contact)
                    .filter(
                        Contact.contact_type == ContactType.CUSTOMER,
                        Contact.is_active,
                    )
                    .count()
                )

                self.set_value(count)
                self.description_label.setText("Toplam aktif müşteri")
            finally:
                session.close()
        except Exception as e:
            print(f"ActiveCustomersWidget hatası: {e}")
            self.value_label.setText("--")
        finally:
            self.set_loading(False)


class ActiveSuppliersWidget(StatWidget):
    """Aktif tedarikçiler widget'ı"""

    widget_code = "stat_active_suppliers"
    widget_name = "Aktif Tedarikçiler"
    widget_description = "Sistemdeki aktif tedarikçi sayısı"
    widget_icon = "building"
    required_permission = "purchasing.view"

    def __init__(self, config=None, edit_mode=False, parent=None):
        super().__init__(
            config=config,
            edit_mode=edit_mode,
            parent=parent,
            value_formatter=lambda v: str(v) if v else "0",
        )

    def refresh_data(self):
        """Aktif tedarikçi verilerini çeker"""
        self.set_loading(True)
        try:
            from database.base import get_session
            from database.models.common import Contact, ContactType

            session = get_session()
            try:
                count = (
                    session.query(Contact)
                    .filter(
                        Contact.contact_type == ContactType.SUPPLIER,
                        Contact.is_active,
                    )
                    .count()
                )

                self.set_value(count)
                self.description_label.setText("Toplam aktif tedarikçi")
            finally:
                session.close()
        except Exception as e:
            print(f"ActiveSuppliersWidget hatası: {e}")
            self.value_label.setText("--")
        finally:
            self.set_loading(False)


class TotalStockValueWidget(StatWidget):
    """Toplam stok değeri widget'ı"""

    widget_code = "stat_total_stock_value"
    widget_name = "Stok Değeri"
    widget_description = "Toplam stok değeri"
    widget_icon = "coins"
    required_permission = "inventory.view"

    def __init__(self, config=None, edit_mode=False, parent=None):
        super().__init__(
            config=config,
            edit_mode=edit_mode,
            parent=parent,
            value_formatter=lambda v: f"₺{v:,.0f}" if v else "₺0",
        )

    def refresh_data(self):
        """Toplam stok değerini çeker"""
        self.set_loading(True)
        try:
            from database.base import get_session
            from database.models.inventory import Item, StockBalance
            from sqlalchemy import func

            session = get_session()
            try:
                total = session.query(
                    func.sum(StockBalance.quantity * Item.purchase_price)
                ).join(Item, StockBalance.item_id == Item.id).filter(
                    StockBalance.is_active, Item.is_active
                ).scalar() or Decimal(
                    "0"
                )

                self.set_value(float(total))
                self.description_label.setText("Envanter değeri")
            finally:
                session.close()
        except Exception as e:
            print(f"TotalStockValueWidget hatası: {e}")
            self.value_label.setText("--")
        finally:
            self.set_loading(False)
