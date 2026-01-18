"""
Akıllı İş - TCMB API Servisi

Türkiye Cumhuriyet Merkez Bankası döviz kurları API entegrasyonu.
"""

import xml.etree.ElementTree as ET
from typing import Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import threading

import requests


@dataclass
class CurrencyRate:
    """Döviz kuru bilgisi"""
    code: str           # USD, EUR, GBP
    name: str           # Amerikan Doları, Euro, İngiliz Sterlini
    buying: float       # Alış kuru
    selling: float      # Satış kuru
    effective_buying: float   # Efektif alış
    effective_selling: float  # Efektif satış
    change: float       # Değişim yüzdesi (önceki güne göre)


class TCMBService:
    """
    TCMB Döviz Kurları Servisi

    Merkez Bankası'nın günlük döviz kurlarını çeker ve önbelleğe alır.

    Kullanım:
        rates = TCMBService.get_rates()
        usd = rates.get("USD")
        print(f"Dolar: {usd.selling}")
    """

    # TCMB XML URL
    BASE_URL = "https://www.tcmb.gov.tr/kurlar/today.xml"

    # Önbellek
    _cache: Dict[str, CurrencyRate] = {}
    _cache_time: Optional[datetime] = None
    _cache_duration = timedelta(hours=1)  # 1 saat
    _lock = threading.Lock()

    # İzlenecek para birimleri
    TRACKED_CURRENCIES = ["USD", "EUR", "GBP", "CHF", "JPY", "SAR", "AUD", "CAD"]

    @classmethod
    def get_rates(cls, force_refresh: bool = False) -> Dict[str, CurrencyRate]:
        """
        Güncel döviz kurlarını döner

        Args:
            force_refresh: Önbelleği atla ve yeniden çek

        Returns:
            Dict[currency_code, CurrencyRate]
        """
        with cls._lock:
            # Önbellek kontrolü
            if not force_refresh and cls._is_cache_valid():
                return cls._cache.copy()

            # TCMB'den çek
            try:
                cls._fetch_rates()
            except Exception as e:
                print(f"TCMB kur çekme hatası: {e}")
                # Önbellekte veri varsa onu döndür
                if cls._cache:
                    return cls._cache.copy()
                return {}

            return cls._cache.copy()

    @classmethod
    def get_rate(cls, currency_code: str) -> Optional[CurrencyRate]:
        """
        Tek bir döviz kurunu döner

        Args:
            currency_code: Para birimi kodu (USD, EUR, vb.)

        Returns:
            CurrencyRate veya None
        """
        rates = cls.get_rates()
        return rates.get(currency_code.upper())

    @classmethod
    def _is_cache_valid(cls) -> bool:
        """Önbellek geçerli mi kontrol eder"""
        if not cls._cache or not cls._cache_time:
            return False

        return datetime.now() - cls._cache_time < cls._cache_duration

    @classmethod
    def _fetch_rates(cls):
        """TCMB'den kurları çeker"""
        try:
            response = requests.get(cls.BASE_URL, timeout=10)
            response.raise_for_status()

            # XML parse
            root = ET.fromstring(response.content)

            new_cache = {}

            for currency in root.findall(".//Currency"):
                code = currency.get("Kod")

                if code not in cls.TRACKED_CURRENCIES:
                    continue

                name = currency.findtext("Isim") or code

                # Değerleri al (boş olabilir)
                def safe_float(text):
                    try:
                        return float(text.replace(",", ".")) if text else 0.0
                    except:
                        return 0.0

                forex_buying = safe_float(currency.findtext("ForexBuying"))
                forex_selling = safe_float(currency.findtext("ForexSelling"))
                effective_buying = safe_float(currency.findtext("BanknoteBuying"))
                effective_selling = safe_float(currency.findtext("BanknoteSelling"))

                # Değişim hesapla (önceki kapanışa göre)
                change = 0.0
                # Not: TCMB XML'inde değişim yok, gerekirse önceki günün verisiyle karşılaştırılabilir

                new_cache[code] = CurrencyRate(
                    code=code,
                    name=name,
                    buying=forex_buying,
                    selling=forex_selling,
                    effective_buying=effective_buying,
                    effective_selling=effective_selling,
                    change=change
                )

            cls._cache = new_cache
            cls._cache_time = datetime.now()

        except requests.RequestException as e:
            print(f"TCMB istek hatası: {e}")
            raise
        except ET.ParseError as e:
            print(f"TCMB XML parse hatası: {e}")
            raise

    @classmethod
    def clear_cache(cls):
        """Önbelleği temizler"""
        with cls._lock:
            cls._cache = {}
            cls._cache_time = None

    @classmethod
    def get_last_update(cls) -> Optional[datetime]:
        """Son güncelleme zamanını döner"""
        return cls._cache_time
