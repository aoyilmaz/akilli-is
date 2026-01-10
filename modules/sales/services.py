"""
Akıllı İş - Satış Modülü Servisleri
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict
from sqlalchemy import desc, and_, or_
from sqlalchemy.orm import joinedload

from database.base import get_session
from database.models.sales import (
    Customer,
    PriceList,
    PriceListItem,
    PriceListType,
    SalesQuote,
    SalesQuoteItem,
    SalesQuoteStatus,
    SalesOrder,
    SalesOrderItem,
    SalesOrderStatus,
    DeliveryNote,
    DeliveryNoteItem,
    DeliveryNoteStatus,
    Invoice,
    InvoiceItem,
    InvoiceStatus,
)
from database.models.inventory import StockMovementType


class PriceListService:
    """Fiyat listesi servisi"""

    def __init__(self):
        self.session = get_session()

    def get_all(
        self,
        list_type: PriceListType = None,
        active_only: bool = True
    ) -> List[PriceList]:
        """Tüm fiyat listelerini getir"""
        query = self.session.query(PriceList)
        if active_only:
            query = query.filter(PriceList.is_active == True)
        if list_type:
            query = query.filter(PriceList.list_type == list_type)
        return query.order_by(PriceList.priority, PriceList.name).all()

    def get_by_id(self, price_list_id: int) -> Optional[PriceList]:
        """ID ile fiyat listesi getir"""
        return (
            self.session.query(PriceList)
            .options(joinedload(PriceList.items).joinedload(PriceListItem.item))
            .filter(PriceList.id == price_list_id)
            .first()
        )

    def get_by_code(self, code: str) -> Optional[PriceList]:
        """Kod ile fiyat listesi getir"""
        return (
            self.session.query(PriceList)
            .filter(PriceList.code == code)
            .first()
        )

    def get_default(
        self, list_type: PriceListType = PriceListType.SALES
    ) -> Optional[PriceList]:
        """Varsayılan fiyat listesini getir"""
        return (
            self.session.query(PriceList)
            .filter(
                PriceList.is_active == True,
                PriceList.is_default == True,
                PriceList.list_type == list_type
            )
            .first()
        )

    def create(self, items_data: List[Dict] = None, **kwargs) -> PriceList:
        """Yeni fiyat listesi oluştur"""
        price_list = PriceList(**kwargs)

        # Varsayılan olarak işaretleniyorsa diğerlerini kaldır
        if kwargs.get("is_default"):
            self._clear_default(kwargs.get("list_type", PriceListType.SALES))

        self.session.add(price_list)
        self.session.flush()

        # Kalemleri ekle
        if items_data:
            for item_data in items_data:
                item = PriceListItem(
                    price_list_id=price_list.id,
                    **item_data
                )
                self.session.add(item)

        self.session.commit()
        return price_list

    def update(
        self,
        price_list_id: int,
        items_data: List[Dict] = None,
        **kwargs
    ) -> Optional[PriceList]:
        """Fiyat listesi güncelle"""
        price_list = self.get_by_id(price_list_id)
        if not price_list:
            return None

        # Varsayılan olarak işaretleniyorsa diğerlerini kaldır
        if kwargs.get("is_default") and not price_list.is_default:
            self._clear_default(price_list.list_type)

        for key, value in kwargs.items():
            if hasattr(price_list, key):
                setattr(price_list, key, value)

        # Kalemleri güncelle
        if items_data is not None:
            # Mevcut kalemleri temizle
            for item in price_list.items:
                self.session.delete(item)

            # Yeni kalemleri ekle
            for item_data in items_data:
                item = PriceListItem(
                    price_list_id=price_list.id,
                    **item_data
                )
                self.session.add(item)

        self.session.commit()
        return price_list

    def delete(self, price_list_id: int) -> bool:
        """Fiyat listesi sil (soft delete)"""
        price_list = self.get_by_id(price_list_id)
        if price_list:
            price_list.is_active = False
            self.session.commit()
            return True
        return False

    def add_item(
        self,
        price_list_id: int,
        item_id: int,
        unit_price: Decimal,
        min_quantity: Decimal = Decimal("0"),
        discount_rate: Decimal = Decimal("0"),
        notes: str = None
    ) -> Optional[PriceListItem]:
        """Fiyat listesine kalem ekle"""
        price_list = self.get_by_id(price_list_id)
        if not price_list:
            return None

        item = PriceListItem(
            price_list_id=price_list_id,
            item_id=item_id,
            unit_price=unit_price,
            min_quantity=min_quantity,
            discount_rate=discount_rate,
            notes=notes
        )
        self.session.add(item)
        self.session.commit()
        return item

    def remove_item(self, price_list_item_id: int) -> bool:
        """Fiyat listesinden kalem kaldır"""
        item = (
            self.session.query(PriceListItem)
            .filter(PriceListItem.id == price_list_item_id)
            .first()
        )
        if item:
            self.session.delete(item)
            self.session.commit()
            return True
        return False

    def get_price(
        self,
        price_list_id: int,
        item_id: int,
        quantity: Decimal = Decimal("1")
    ) -> Optional[Decimal]:
        """Fiyat listesinden ürün fiyatı getir (miktar bazlı)"""
        items = (
            self.session.query(PriceListItem)
            .filter(
                PriceListItem.price_list_id == price_list_id,
                PriceListItem.item_id == item_id,
                PriceListItem.min_quantity <= quantity
            )
            .order_by(desc(PriceListItem.min_quantity))
            .all()
        )

        if items:
            item = items[0]  # En yüksek min_quantity eşleşmesi
            price = item.unit_price
            if item.discount_rate:
                discount = price * item.discount_rate / 100
                price = price - discount
            return price
        return None

    def get_customer_price(
        self,
        customer_id: int,
        item_id: int,
        quantity: Decimal = Decimal("1")
    ) -> Optional[Decimal]:
        """Müşteriye özel fiyat getir"""
        # Müşterinin fiyat listesini bul
        customer = (
            self.session.query(Customer)
            .filter(Customer.id == customer_id)
            .first()
        )

        if customer and customer.price_list_id:
            price = self.get_price(customer.price_list_id, item_id, quantity)
            if price:
                return price

        # Müşteri fiyat listesi yoksa varsayılan fiyat listesini kontrol et
        default_list = self.get_default(PriceListType.SALES)
        if default_list:
            price = self.get_price(default_list.id, item_id, quantity)
            if price:
                return price

        # Hiç fiyat listesi yoksa stok kartındaki satış fiyatını döndür
        from database.models.inventory import Item
        item = self.session.query(Item).filter(Item.id == item_id).first()
        if item:
            return item.sale_price

        return None

    def generate_code(self) -> str:
        """Fiyat listesi kodu üret"""
        last = (
            self.session.query(PriceList)
            .filter(PriceList.code.like("FL%"))
            .order_by(desc(PriceList.code))
            .first()
        )

        if last:
            try:
                num = int(last.code[2:]) + 1
            except ValueError:
                num = 1
        else:
            num = 1

        return f"FL{num:04d}"

    def _clear_default(self, list_type: PriceListType):
        """Varsayılan fiyat listesi işaretini kaldır"""
        self.session.query(PriceList).filter(
            PriceList.list_type == list_type,
            PriceList.is_default == True
        ).update({"is_default": False})


class CustomerService:
    """Müşteri servisi"""

    def __init__(self):
        self.session = get_session()

    def get_all(self, active_only: bool = True) -> List[Customer]:
        """Tüm müşterileri getir"""
        query = self.session.query(Customer)
        if active_only:
            query = query.filter(Customer.is_active == True)
        return query.order_by(Customer.name).all()

    def get_by_id(self, customer_id: int) -> Optional[Customer]:
        """ID ile müşteri getir"""
        return self.session.query(Customer).filter(Customer.id == customer_id).first()

    def get_by_code(self, code: str) -> Optional[Customer]:
        """Kod ile müşteri getir"""
        return self.session.query(Customer).filter(Customer.code == code).first()

    def search(self, keyword: str, limit: int = 20) -> List[Customer]:
        """Müşteri ara"""
        keyword = f"%{keyword}%"
        return (
            self.session.query(Customer)
            .filter(
                and_(
                    Customer.is_active == True,
                    or_(
                        Customer.code.ilike(keyword),
                        Customer.name.ilike(keyword),
                        Customer.tax_number.ilike(keyword),
                    ),
                )
            )
            .limit(limit)
            .all()
        )

    def create(self, **data) -> Customer:
        """Yeni müşteri oluştur"""
        customer = Customer(**data)
        self.session.add(customer)
        self.session.commit()
        return customer

    def update(self, customer_id: int, **data) -> Optional[Customer]:
        """Müşteri güncelle"""
        customer = self.get_by_id(customer_id)
        if customer:
            for key, value in data.items():
                if hasattr(customer, key):
                    setattr(customer, key, value)
            self.session.commit()
        return customer

    def delete(self, customer_id: int) -> bool:
        """Müşteri sil (soft delete)"""
        customer = self.get_by_id(customer_id)
        if customer:
            customer.is_active = False
            self.session.commit()
            return True
        return False

    def generate_code(self) -> str:
        """Otomatik kod üret"""
        last = self.session.query(Customer).order_by(desc(Customer.id)).first()
        if last and last.code.startswith("MUS"):
            try:
                num = int(last.code[3:]) + 1
            except:
                num = 1
        else:
            num = 1
        return f"MUS{num:04d}"


class SalesQuoteService:
    """Satış teklifi servisi"""

    def __init__(self):
        self.session = get_session()

    def get_all(self, status: SalesQuoteStatus = None, customer_id: int = None) -> List[SalesQuote]:
        """Tüm teklifleri getir"""
        query = self.session.query(SalesQuote).options(
            joinedload(SalesQuote.customer),
            joinedload(SalesQuote.items)
        )
        if status:
            query = query.filter(SalesQuote.status == status)
        if customer_id:
            query = query.filter(SalesQuote.customer_id == customer_id)
        return query.order_by(desc(SalesQuote.quote_date)).all()

    def get_by_id(self, quote_id: int) -> Optional[SalesQuote]:
        """ID ile teklif getir"""
        return (
            self.session.query(SalesQuote)
            .options(
                joinedload(SalesQuote.customer),
                joinedload(SalesQuote.items).joinedload(SalesQuoteItem.item),
                joinedload(SalesQuote.items).joinedload(SalesQuoteItem.unit),
            )
            .filter(SalesQuote.id == quote_id)
            .first()
        )

    def get_pending(self) -> List[SalesQuote]:
        """Gönderilmiş teklifleri getir"""
        return self.get_all(status=SalesQuoteStatus.SENT)

    def get_accepted(self) -> List[SalesQuote]:
        """Kabul edilen (siparişe dönüştürülmemiş) teklifleri getir"""
        return self.get_all(status=SalesQuoteStatus.ACCEPTED)

    def create(self, items_data: List[Dict], **data) -> SalesQuote:
        """Yeni teklif oluştur"""
        data["quote_no"] = self.generate_quote_no()

        quote = SalesQuote(**data)
        self.session.add(quote)
        self.session.flush()

        for item_data in items_data:
            item = SalesQuoteItem(quote_id=quote.id, **item_data)
            item.calculate_line_total()
            self.session.add(item)

        self.session.flush()
        quote.calculate_totals()
        self.session.commit()

        return quote

    def update(self, quote_id: int, items_data: List[Dict] = None, **data) -> Optional[SalesQuote]:
        """Teklif güncelle"""
        quote = self.get_by_id(quote_id)
        if not quote:
            return None

        if quote.status not in [SalesQuoteStatus.DRAFT]:
            raise ValueError("Sadece taslak durumdaki teklifler güncellenebilir")

        for key, value in data.items():
            if hasattr(quote, key):
                setattr(quote, key, value)

        if items_data is not None:
            for item in quote.items:
                self.session.delete(item)

            for item_data in items_data:
                item = SalesQuoteItem(quote_id=quote.id, **item_data)
                item.calculate_line_total()
                self.session.add(item)

            self.session.flush()
            quote.calculate_totals()

        self.session.commit()
        return quote

    def send_to_customer(self, quote_id: int) -> Optional[SalesQuote]:
        """Teklifi müşteriye gönder"""
        quote = self.get_by_id(quote_id)
        if quote and quote.status == SalesQuoteStatus.DRAFT:
            quote.status = SalesQuoteStatus.SENT
            self.session.commit()
        return quote

    def accept(self, quote_id: int) -> Optional[SalesQuote]:
        """Teklifi kabul et"""
        quote = self.get_by_id(quote_id)
        if quote and quote.status == SalesQuoteStatus.SENT:
            quote.status = SalesQuoteStatus.ACCEPTED
            self.session.commit()
        return quote

    def reject(self, quote_id: int, reason: str = None) -> Optional[SalesQuote]:
        """Teklifi reddet"""
        quote = self.get_by_id(quote_id)
        if quote and quote.status == SalesQuoteStatus.SENT:
            quote.status = SalesQuoteStatus.REJECTED
            quote.rejection_reason = reason
            self.session.commit()
        return quote

    def convert_to_order(self, quote_id: int) -> Optional["SalesOrder"]:
        """Teklifi siparişe dönüştür"""
        quote = self.get_by_id(quote_id)
        if not quote or quote.status != SalesQuoteStatus.ACCEPTED:
            raise ValueError("Sadece kabul edilmiş teklifler siparişe dönüştürülebilir")

        # Aynı session'ı kullan
        order_no = SalesOrderService().generate_order_no()

        order = SalesOrder(
            order_no=order_no,
            customer_id=quote.customer_id,
            quote_id=quote.id,
            order_date=date.today(),
            currency=quote.currency,
            exchange_rate=quote.exchange_rate,
            discount_rate=quote.discount_rate,
            notes=quote.notes,
        )
        self.session.add(order)
        self.session.flush()

        for qi in quote.items:
            item = SalesOrderItem(
                order_id=order.id,
                item_id=qi.item_id,
                quantity=qi.quantity,
                unit_id=qi.unit_id,
                unit_price=qi.unit_price,
                discount_rate=qi.discount_rate,
                tax_rate=qi.tax_rate,
                description=qi.description,
            )
            item.calculate_line_total()
            self.session.add(item)

        self.session.flush()
        order.calculate_totals()

        quote.status = SalesQuoteStatus.ORDERED
        self.session.commit()

        return order

    def mark_expired(self) -> int:
        """Süresi dolan teklifleri işaretle"""
        today = date.today()
        count = (
            self.session.query(SalesQuote)
            .filter(
                SalesQuote.status == SalesQuoteStatus.SENT,
                SalesQuote.valid_until < today
            )
            .update({"status": SalesQuoteStatus.EXPIRED})
        )
        self.session.commit()
        return count

    def delete(self, quote_id: int) -> bool:
        """Teklif sil"""
        quote = self.get_by_id(quote_id)
        if quote and quote.status == SalesQuoteStatus.DRAFT:
            self.session.delete(quote)
            self.session.commit()
            return True
        return False

    def generate_quote_no(self) -> str:
        """Teklif numarası üret"""
        today = date.today()
        prefix = f"SQ{today.strftime('%y%m')}"

        last = (
            self.session.query(SalesQuote)
            .filter(SalesQuote.quote_no.like(f"{prefix}%"))
            .order_by(desc(SalesQuote.quote_no))
            .first()
        )

        if last:
            try:
                num = int(last.quote_no[-4:]) + 1
            except:
                num = 1
        else:
            num = 1

        return f"{prefix}{num:04d}"


class SalesOrderService:
    """Satış siparişi servisi"""

    def __init__(self):
        self.session = get_session()

    def get_all(self, status: SalesOrderStatus = None, customer_id: int = None) -> List[SalesOrder]:
        """Tüm siparişleri getir"""
        query = self.session.query(SalesOrder).options(
            joinedload(SalesOrder.customer),
            joinedload(SalesOrder.items)
        )
        if status:
            query = query.filter(SalesOrder.status == status)
        if customer_id:
            query = query.filter(SalesOrder.customer_id == customer_id)
        return query.order_by(desc(SalesOrder.order_date)).all()

    def get_by_id(self, order_id: int) -> Optional[SalesOrder]:
        """ID ile sipariş getir"""
        return (
            self.session.query(SalesOrder)
            .options(
                joinedload(SalesOrder.customer),
                joinedload(SalesOrder.quote),
                joinedload(SalesOrder.items).joinedload(SalesOrderItem.item),
                joinedload(SalesOrder.items).joinedload(SalesOrderItem.unit),
            )
            .filter(SalesOrder.id == order_id)
            .first()
        )

    def get_open_orders(self) -> List[SalesOrder]:
        """Açık siparişleri getir"""
        return (
            self.session.query(SalesOrder)
            .filter(
                SalesOrder.status.in_([
                    SalesOrderStatus.CONFIRMED,
                    SalesOrderStatus.PARTIAL,
                ])
            )
            .order_by(SalesOrder.delivery_date)
            .all()
        )

    def get_ready_for_delivery(self) -> List[SalesOrder]:
        """Sevke hazır siparişleri getir"""
        return self.get_all(status=SalesOrderStatus.CONFIRMED)

    def create(self, items_data: List[Dict], **data) -> SalesOrder:
        """Yeni sipariş oluştur"""
        data["order_no"] = self.generate_order_no()

        order = SalesOrder(**data)
        self.session.add(order)
        self.session.flush()

        for item_data in items_data:
            item = SalesOrderItem(order_id=order.id, **item_data)
            item.calculate_line_total()
            self.session.add(item)

        self.session.flush()
        order.calculate_totals()
        self.session.commit()

        return order

    def create_from_quote(self, quote_id: int) -> SalesOrder:
        """Tekliften sipariş oluştur"""
        quote_service = SalesQuoteService()
        return quote_service.convert_to_order(quote_id)

    def update(self, order_id: int, items_data: List[Dict] = None, **data) -> Optional[SalesOrder]:
        """Sipariş güncelle"""
        order = self.get_by_id(order_id)
        if not order:
            return None

        if order.status not in [SalesOrderStatus.DRAFT]:
            raise ValueError("Sadece taslak durumdaki siparişler güncellenebilir")

        for key, value in data.items():
            if hasattr(order, key):
                setattr(order, key, value)

        if items_data is not None:
            for item in order.items:
                self.session.delete(item)

            for item_data in items_data:
                item = SalesOrderItem(order_id=order.id, **item_data)
                item.calculate_line_total()
                self.session.add(item)

            self.session.flush()
            order.calculate_totals()

        self.session.commit()
        return order

    def confirm(self, order_id: int, skip_credit_check: bool = False) -> Optional[SalesOrder]:
        """Siparişi onayla"""
        order = self.get_by_id(order_id)
        if not order or order.status != SalesOrderStatus.DRAFT:
            return order

        # Müşteri kredi limiti kontrolü
        if not skip_credit_check and order.customer:
            customer = order.customer
            credit_limit = float(customer.credit_limit or 0)

            if credit_limit > 0:
                # Müşterinin açık bakiyesini hesapla
                open_balance = self._get_customer_open_balance(customer.id)
                order_total = float(order.total or 0)

                if open_balance + order_total > credit_limit:
                    raise ValueError(
                        f"Müşteri kredi limiti aşılıyor!\n"
                        f"Kredi Limiti: {credit_limit:,.2f} TL\n"
                        f"Mevcut Bakiye: {open_balance:,.2f} TL\n"
                        f"Sipariş Tutarı: {order_total:,.2f} TL\n"
                        f"Toplam: {open_balance + order_total:,.2f} TL"
                    )

        order.status = SalesOrderStatus.CONFIRMED
        self.session.commit()
        return order

    def _get_customer_open_balance(self, customer_id: int) -> float:
        """Müşterinin açık bakiyesini hesapla"""
        # Onaylı/bekleyen siparişlerin toplamı
        from sqlalchemy import func
        orders_total = (
            self.session.query(func.coalesce(func.sum(SalesOrder.total), 0))
            .filter(
                SalesOrder.customer_id == customer_id,
                SalesOrder.status.in_([
                    SalesOrderStatus.CONFIRMED,
                    SalesOrderStatus.PARTIAL
                ])
            )
            .scalar()
        )

        # Ödenmemiş faturaların bakiyesi
        invoices_balance = (
            self.session.query(func.coalesce(func.sum(Invoice.balance), 0))
            .filter(
                Invoice.customer_id == customer_id,
                Invoice.status.in_([
                    InvoiceStatus.ISSUED,
                    InvoiceStatus.PARTIAL,
                    InvoiceStatus.OVERDUE
                ])
            )
            .scalar()
        )

        return float(orders_total) + float(invoices_balance)

    def cancel(self, order_id: int) -> Optional[SalesOrder]:
        """Sipariş iptal"""
        order = self.get_by_id(order_id)
        if order and order.status in [SalesOrderStatus.DRAFT, SalesOrderStatus.CONFIRMED]:
            order.status = SalesOrderStatus.CANCELLED
            self.session.commit()
        return order

    def close(self, order_id: int) -> Optional[SalesOrder]:
        """Sipariş kapat"""
        order = self.get_by_id(order_id)
        if order and order.status in [SalesOrderStatus.DELIVERED, SalesOrderStatus.PARTIAL]:
            order.status = SalesOrderStatus.CLOSED
            self.session.commit()
        return order

    def update_delivered_quantities(self, order_id: int):
        """Teslim edilen miktarları güncelle ve durumu kontrol et"""
        order = self.get_by_id(order_id)
        if not order:
            return

        all_delivered = True
        any_delivered = False

        for item in order.items:
            if item.delivered_quantity and item.delivered_quantity > 0:
                any_delivered = True
            if not item.is_fully_delivered:
                all_delivered = False

        if all_delivered:
            order.status = SalesOrderStatus.DELIVERED
            order.actual_delivery_date = date.today()
        elif any_delivered:
            order.status = SalesOrderStatus.PARTIAL

        self.session.commit()

    def delete(self, order_id: int) -> bool:
        """Sipariş sil"""
        order = self.get_by_id(order_id)
        if order and order.status == SalesOrderStatus.DRAFT:
            self.session.delete(order)
            self.session.commit()
            return True
        return False

    def generate_order_no(self) -> str:
        """Sipariş numarası üret"""
        today = date.today()
        prefix = f"SO{today.strftime('%y%m')}"

        last = (
            self.session.query(SalesOrder)
            .filter(SalesOrder.order_no.like(f"{prefix}%"))
            .order_by(desc(SalesOrder.order_no))
            .first()
        )

        if last:
            try:
                num = int(last.order_no[-4:]) + 1
            except:
                num = 1
        else:
            num = 1

        return f"{prefix}{num:04d}"


class DeliveryNoteService:
    """Teslimat irsaliyesi servisi"""

    def __init__(self):
        self.session = get_session()

    def get_all(self, status: DeliveryNoteStatus = None, customer_id: int = None) -> List[DeliveryNote]:
        """Tüm irsaliyeleri getir"""
        query = self.session.query(DeliveryNote).options(
            joinedload(DeliveryNote.customer),
            joinedload(DeliveryNote.source_warehouse),
            joinedload(DeliveryNote.items),
        )
        if status:
            query = query.filter(DeliveryNote.status == status)
        if customer_id:
            query = query.filter(DeliveryNote.customer_id == customer_id)
        return query.order_by(desc(DeliveryNote.delivery_date)).all()

    def get_by_id(self, delivery_id: int) -> Optional[DeliveryNote]:
        """ID ile irsaliye getir"""
        return (
            self.session.query(DeliveryNote)
            .options(
                joinedload(DeliveryNote.customer),
                joinedload(DeliveryNote.source_warehouse),
                joinedload(DeliveryNote.sales_order),
                joinedload(DeliveryNote.items).joinedload(DeliveryNoteItem.item),
                joinedload(DeliveryNote.items).joinedload(DeliveryNoteItem.unit),
            )
            .filter(DeliveryNote.id == delivery_id)
            .first()
        )

    def create(self, items_data: List[Dict], **data) -> DeliveryNote:
        """Yeni irsaliye oluştur"""
        data["delivery_no"] = self.generate_delivery_no()

        delivery = DeliveryNote(**data)
        self.session.add(delivery)
        self.session.flush()

        for item_data in items_data:
            item = DeliveryNoteItem(delivery_note_id=delivery.id, **item_data)
            self.session.add(item)

        self.session.commit()
        return delivery

    def update(
        self,
        delivery_id: int,
        items_data: List[Dict] = None,
        **data
    ) -> Optional[DeliveryNote]:
        """İrsaliye güncelle (sadece taslak durumunda)"""
        delivery = self.get_by_id(delivery_id)
        if not delivery:
            return None

        if delivery.status != DeliveryNoteStatus.DRAFT:
            raise ValueError("Sadece taslak irsaliyeler düzenlenebilir")

        # Alanları güncelle
        for key, value in data.items():
            if hasattr(delivery, key) and key not in (
                "id", "delivery_no", "status"
            ):
                setattr(delivery, key, value)

        # Kalemleri güncelle
        if items_data is not None:
            # Mevcut kalemleri sil
            for item in delivery.items:
                self.session.delete(item)

            # Yeni kalemleri ekle
            for item_data in items_data:
                item = DeliveryNoteItem(
                    delivery_note_id=delivery.id, **item_data
                )
                self.session.add(item)

        self.session.commit()
        return delivery

    def create_from_order(self, order_id: int, warehouse_id: int, items_data: List[Dict], **data) -> DeliveryNote:
        """Siparişten irsaliye oluştur"""
        order_service = SalesOrderService()
        order = order_service.get_by_id(order_id)

        if not order:
            raise ValueError("Sipariş bulunamadı")

        if order.status not in [SalesOrderStatus.CONFIRMED, SalesOrderStatus.PARTIAL]:
            raise ValueError("Bu sipariş için irsaliye oluşturulamaz")

        data["sales_order_id"] = order_id
        data["customer_id"] = order.customer_id
        data["source_warehouse_id"] = warehouse_id
        data["shipping_address"] = order.delivery_address

        if "delivery_date" not in data or data["delivery_date"] is None:
            data["delivery_date"] = date.today()

        delivery = self.create(items_data, **data)

        # Sipariş kalemlerini güncelle
        for dn_item in delivery.items:
            if dn_item.so_item_id:
                so_item = self.session.query(SalesOrderItem).get(dn_item.so_item_id)
                if so_item:
                    so_item.delivered_quantity = Decimal(
                        str(so_item.delivered_quantity or 0)
                    ) + Decimal(str(dn_item.quantity or 0))

        # Sipariş durumunu güncelle
        order_service.update_delivered_quantities(order_id)

        return delivery

    def ship(self, delivery_id: int) -> Optional[DeliveryNote]:
        """İrsaliyeyi sevk et"""
        delivery = self.get_by_id(delivery_id)
        if delivery and delivery.status == DeliveryNoteStatus.DRAFT:
            delivery.status = DeliveryNoteStatus.SHIPPED
            self.session.commit()
        return delivery

    def deliver(self, delivery_id: int) -> Optional[DeliveryNote]:
        """Teslimatı tamamla"""
        delivery = self.get_by_id(delivery_id)
        if delivery and delivery.status == DeliveryNoteStatus.SHIPPED:
            delivery.status = DeliveryNoteStatus.DELIVERED
            delivery.actual_delivery_date = date.today()
            self.session.commit()
        return delivery

    def complete(self, delivery_id: int) -> Optional[DeliveryNote]:
        """İrsaliyeyi tamamla ve stok çıkışı yap"""
        delivery = self.get_by_id(delivery_id)
        if not delivery:
            return None

        # Sadece draft veya shipped durumundakiler tamamlanabilir
        if delivery.status not in (
            DeliveryNoteStatus.DRAFT, DeliveryNoteStatus.SHIPPED
        ):
            return None

        try:
            from modules.inventory.services import StockMovementService

            movement_service = StockMovementService()

            for item in delivery.items:
                if item.quantity and item.quantity > 0:
                    movement_service.create_movement(
                        movement_type=StockMovementType.SATIS,
                        item_id=item.item_id,
                        from_warehouse_id=delivery.source_warehouse_id,
                        quantity=float(item.quantity),
                        document_type="delivery_note",
                        document_no=delivery.delivery_no,
                        description=f"Satış İrsaliyesi: {delivery.delivery_no}",
                    )

            delivery.status = DeliveryNoteStatus.DELIVERED
            delivery.actual_delivery_date = date.today()
            self.session.commit()

        except Exception as e:
            self.session.rollback()
            raise e

        return delivery

    def cancel(self, delivery_id: int) -> Optional[DeliveryNote]:
        """İrsaliye iptal"""
        delivery = self.get_by_id(delivery_id)
        if delivery and delivery.status == DeliveryNoteStatus.DRAFT:
            delivery.status = DeliveryNoteStatus.CANCELLED
            self.session.commit()
        return delivery

    def delete(self, delivery_id: int) -> bool:
        """İrsaliye sil"""
        delivery = self.get_by_id(delivery_id)
        if delivery and delivery.status == DeliveryNoteStatus.DRAFT:
            self.session.delete(delivery)
            self.session.commit()
            return True
        return False

    def generate_delivery_no(self) -> str:
        """İrsaliye numarası üret"""
        today = date.today()
        prefix = f"DN{today.strftime('%y%m')}"

        last = (
            self.session.query(DeliveryNote)
            .filter(DeliveryNote.delivery_no.like(f"{prefix}%"))
            .order_by(desc(DeliveryNote.delivery_no))
            .first()
        )

        if last:
            try:
                num = int(last.delivery_no[-4:]) + 1
            except:
                num = 1
        else:
            num = 1

        return f"{prefix}{num:04d}"


class InvoiceService:
    """Fatura servisi"""

    def __init__(self):
        self.session = get_session()

    def get_all(self, status: InvoiceStatus = None, customer_id: int = None) -> List[Invoice]:
        """Tüm faturaları getir"""
        query = self.session.query(Invoice).options(
            joinedload(Invoice.customer),
            joinedload(Invoice.items),
        )
        if status:
            query = query.filter(Invoice.status == status)
        if customer_id:
            query = query.filter(Invoice.customer_id == customer_id)
        return query.order_by(desc(Invoice.invoice_date)).all()

    def get_by_id(self, invoice_id: int) -> Optional[Invoice]:
        """ID ile fatura getir"""
        return (
            self.session.query(Invoice)
            .options(
                joinedload(Invoice.customer),
                joinedload(Invoice.sales_order),
                joinedload(Invoice.delivery_note),
                joinedload(Invoice.items).joinedload(InvoiceItem.item),
                joinedload(Invoice.items).joinedload(InvoiceItem.unit),
            )
            .filter(Invoice.id == invoice_id)
            .first()
        )

    def get_overdue(self) -> List[Invoice]:
        """Vadesi geçmiş faturaları getir"""
        today = date.today()
        return (
            self.session.query(Invoice)
            .filter(
                Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.PARTIAL]),
                Invoice.due_date < today
            )
            .order_by(Invoice.due_date)
            .all()
        )

    def get_unpaid(self) -> List[Invoice]:
        """Ödenmemiş faturaları getir"""
        return (
            self.session.query(Invoice)
            .filter(Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.PARTIAL, InvoiceStatus.OVERDUE]))
            .order_by(Invoice.due_date)
            .all()
        )

    def create(self, items_data: List[Dict], **data) -> Invoice:
        """Yeni fatura oluştur"""
        data["invoice_no"] = self.generate_invoice_no()

        invoice = Invoice(**data)
        self.session.add(invoice)
        self.session.flush()

        for item_data in items_data:
            item = InvoiceItem(invoice_id=invoice.id, **item_data)
            item.calculate_line_total()
            self.session.add(item)

        self.session.flush()
        invoice.calculate_totals()
        self.session.commit()

        return invoice

    def update(
        self,
        invoice_id: int,
        items_data: List[Dict] = None,
        **data
    ) -> Optional[Invoice]:
        """Fatura güncelle (sadece taslak durumunda)"""
        invoice = self.get_by_id(invoice_id)
        if not invoice:
            return None

        if invoice.status != InvoiceStatus.DRAFT:
            raise ValueError("Sadece taslak faturalar düzenlenebilir")

        # Alanları güncelle
        for key, value in data.items():
            if hasattr(invoice, key) and key not in (
                "id", "invoice_no", "status", "paid_amount", "balance"
            ):
                setattr(invoice, key, value)

        # Kalemleri güncelle
        if items_data is not None:
            # Mevcut kalemleri sil
            for item in invoice.items:
                self.session.delete(item)

            # Yeni kalemleri ekle
            for item_data in items_data:
                item = InvoiceItem(invoice_id=invoice.id, **item_data)
                item.calculate_line_total()
                self.session.add(item)

            self.session.flush()
            invoice.calculate_totals()

        self.session.commit()
        return invoice

    def create_from_delivery(self, delivery_id: int, **data) -> Invoice:
        """İrsaliyeden fatura oluştur"""
        delivery_service = DeliveryNoteService()
        delivery = delivery_service.get_by_id(delivery_id)

        if not delivery:
            raise ValueError("İrsaliye bulunamadı")

        # Bu irsaliye için zaten fatura oluşturulmuş mu kontrol et
        existing_invoice = (
            self.session.query(Invoice)
            .filter(
                Invoice.delivery_note_id == delivery_id,
                Invoice.status != InvoiceStatus.CANCELLED
            )
            .first()
        )
        if existing_invoice:
            raise ValueError(
                f"Bu irsaliye için zaten fatura oluşturulmuş: "
                f"{existing_invoice.invoice_no}"
            )

        # Sipariş bilgilerini al
        order = delivery.sales_order

        items_data = []
        for di in delivery.items:
            # Sipariş kaleminden fiyat bilgisi al
            unit_price = 0
            tax_rate = 18
            discount_rate = 0

            if di.so_item_id:
                so_item = self.session.query(SalesOrderItem).get(di.so_item_id)
                if so_item:
                    unit_price = so_item.unit_price
                    tax_rate = so_item.tax_rate
                    discount_rate = so_item.discount_rate
            elif di.item and di.item.sale_price:
                unit_price = di.item.sale_price

            items_data.append({
                "item_id": di.item_id,
                "quantity": di.quantity,
                "unit_id": di.unit_id,
                "unit_price": unit_price,
                "tax_rate": tax_rate,
                "discount_rate": discount_rate,
                "description": di.notes,
            })

        data["customer_id"] = delivery.customer_id
        data["delivery_note_id"] = delivery.id
        data["sales_order_id"] = delivery.sales_order_id

        if "invoice_date" not in data:
            data["invoice_date"] = date.today()

        # Müşteri ödeme vadesini al
        customer = delivery.customer
        if customer and customer.payment_term_days:
            data["due_date"] = date.today()
            from datetime import timedelta
            data["due_date"] = date.today() + timedelta(days=customer.payment_term_days)

        return self.create(items_data, **data)

    def issue(self, invoice_id: int) -> Optional[Invoice]:
        """Faturayı kes"""
        invoice = self.get_by_id(invoice_id)
        if invoice and invoice.status == InvoiceStatus.DRAFT:
            invoice.status = InvoiceStatus.ISSUED
            self.session.commit()

            # Cari hesap hareketi oluştur
            try:
                from modules.finance.services import AccountTransactionService
                transaction_service = AccountTransactionService()
                transaction_service.create_from_invoice(invoice)
            except Exception as e:
                # Finans modülü yüklü değilse veya hata olursa sessizce devam et
                print(f"Cari hesap hareketi oluşturulamadı: {e}")

        return invoice

    def record_payment(self, invoice_id: int, amount: Decimal, method: str = None, notes: str = None) -> Optional[Invoice]:
        """Ödeme kaydet"""
        invoice = self.get_by_id(invoice_id)
        if not invoice or invoice.status in [InvoiceStatus.PAID, InvoiceStatus.CANCELLED]:
            return None

        invoice.paid_amount = Decimal(str(invoice.paid_amount or 0)) + amount
        invoice.balance = Decimal(str(invoice.total or 0)) - invoice.paid_amount

        if invoice.balance <= 0:
            invoice.status = InvoiceStatus.PAID
            invoice.paid_date = date.today()
        else:
            invoice.status = InvoiceStatus.PARTIAL

        if method:
            invoice.payment_method = method
        if notes:
            invoice.payment_notes = notes

        self.session.commit()
        return invoice

    def check_overdue(self) -> int:
        """Vadesi geçmiş faturaları işaretle"""
        today = date.today()
        count = (
            self.session.query(Invoice)
            .filter(
                Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.PARTIAL]),
                Invoice.due_date < today
            )
            .update({"status": InvoiceStatus.OVERDUE})
        )
        self.session.commit()
        return count

    def cancel(self, invoice_id: int) -> Optional[Invoice]:
        """Fatura iptal"""
        invoice = self.get_by_id(invoice_id)
        if invoice and invoice.status == InvoiceStatus.DRAFT:
            invoice.status = InvoiceStatus.CANCELLED
            self.session.commit()
        return invoice

    def delete(self, invoice_id: int) -> bool:
        """Fatura sil"""
        invoice = self.get_by_id(invoice_id)
        if invoice and invoice.status == InvoiceStatus.DRAFT:
            self.session.delete(invoice)
            self.session.commit()
            return True
        return False

    def generate_invoice_no(self) -> str:
        """Fatura numarası üret"""
        today = date.today()
        prefix = f"INV{today.strftime('%y%m')}"

        last = (
            self.session.query(Invoice)
            .filter(Invoice.invoice_no.like(f"{prefix}%"))
            .order_by(desc(Invoice.invoice_no))
            .first()
        )

        if last:
            try:
                num = int(last.invoice_no[-4:]) + 1
            except:
                num = 1
        else:
            num = 1

        return f"{prefix}{num:04d}"
