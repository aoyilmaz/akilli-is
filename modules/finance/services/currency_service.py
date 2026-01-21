import urllib.request
import xml.etree.ElementTree as ET
from decimal import Decimal


from database import get_session
from database.models.common import Currency


class CurrencyService:
    """Para birimi ve döviz kuru işlemleri"""

    def __init__(self):
        self.session = get_session()

    def get_all(self):
        """Aktif para birimlerini getir"""
        return self.session.query(Currency).order_by(Currency.id).all()

    @staticmethod
    def fetch_tcmb_rates() -> dict:
        """
        TCMB üzerinden anlık döviz kurlarını çeker.
        Dönüş formatı: {"USD": Decimal("32.50"), "EUR": ...}
        Hata durumunda None döner.
        """
        url = "https://www.tcmb.gov.tr/kurlar/today.xml"
        try:
            with urllib.request.urlopen(url, timeout=3) as response:
                if response.status != 200:
                    return None

                tree = ET.fromstring(response.read())
                rates = {"TRY": Decimal("1.0")}

                for currency in tree.findall("Currency"):
                    code = currency.get("CurrencyCode")
                    # ForexSelling: Döviz Satış
                    selling = currency.find("ForexSelling").text

                    if selling and code in ["USD", "EUR", "GBP", "CHF", "RUB", "CNY"]:
                        rates[code] = Decimal(selling)

                return rates
        except Exception as e:
            print(f"TCMB Kur Çekme Hatası: {e}")
            return None
