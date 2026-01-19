"""
Akıllı İş - Hava Durumu API Servisi

wttr.in ücretsiz hava durumu API entegrasyonu.
"""

from typing import Optional, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass
import threading

import requests
import urllib3

# SSL uyarılarını bastır
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@dataclass
class WeatherData:
    """Hava durumu bilgisi"""

    city: str
    condition: str  # Açık, Bulutlu, Yağmurlu, vb.
    condition_icon: str  # Emoji veya ikon kodu
    temperature: int  # Celsius
    feels_like: int  # Hissedilen sıcaklık
    humidity: int  # Nem yüzdesi
    wind_speed: int  # Rüzgar hızı (km/s)
    wind_direction: str  # Rüzgar yönü
    updated_at: datetime


class WeatherService:
    """
    Hava Durumu Servisi (wttr.in)

    Ücretsiz, API key gerektirmeyen hava durumu servisi.

    Kullanım:
        weather = WeatherService.get_weather("Istanbul")
        print(f"{weather.city}: {weather.temperature}°C, {weather.condition}")
    """

    BASE_URL = "https://wttr.in"

    # Önbellek (şehir bazlı)
    _cache: Dict[str, WeatherData] = {}
    _cache_duration = timedelta(minutes=30)  # 30 dakika
    _lock = threading.Lock()

    # Hava durumu kod eşlemeleri
    CONDITION_MAP = {
        "113": ("Açık", "☀️"),
        "116": ("Parçalı Bulutlu", "⛅"),
        "119": ("Bulutlu", "☁️"),
        "122": ("Kapalı", "☁️"),
        "143": ("Sisli", "🌫️"),
        "176": ("Sağanak Yağışlı", "🌧️"),
        "179": ("Kar Yağışlı", "🌨️"),
        "182": ("Sulu Kar", "🌨️"),
        "185": ("Dondurucu Çisenti", "🌨️"),
        "200": ("Gök Gürültülü", "⛈️"),
        "227": ("Kar Fırtınası", "❄️"),
        "230": ("Tipi", "❄️"),
        "248": ("Sis", "🌫️"),
        "260": ("Yoğun Sis", "🌫️"),
        "263": ("Çisenti", "🌧️"),
        "266": ("Hafif Yağmur", "🌧️"),
        "281": ("Dondurucu Yağmur", "🌧️"),
        "284": ("Şiddetli Dondurucu Yağmur", "🌧️"),
        "293": ("Hafif Yağmur", "🌧️"),
        "296": ("Yağmur", "🌧️"),
        "299": ("Orta Şiddetli Yağmur", "🌧️"),
        "302": ("Şiddetli Yağmur", "🌧️"),
        "305": ("Kuvvetli Yağmur", "🌧️"),
        "308": ("Çok Kuvvetli Yağmur", "🌧️"),
        "311": ("Hafif Dondurucu Yağmur", "🌧️"),
        "314": ("Orta Dondurucu Yağmur", "🌧️"),
        "317": ("Hafif Sulu Kar", "🌨️"),
        "320": ("Orta Sulu Kar", "🌨️"),
        "323": ("Hafif Kar", "🌨️"),
        "326": ("Kar", "🌨️"),
        "329": ("Orta Kar", "🌨️"),
        "332": ("Yoğun Kar", "🌨️"),
        "335": ("Şiddetli Kar", "🌨️"),
        "338": ("Çok Yoğun Kar", "🌨️"),
        "350": ("Dolu", "🌨️"),
        "353": ("Hafif Sağanak", "🌧️"),
        "356": ("Orta Sağanak", "🌧️"),
        "359": ("Kuvvetli Sağanak", "🌧️"),
        "362": ("Hafif Sulu Kar Sağanağı", "🌨️"),
        "365": ("Orta Sulu Kar Sağanağı", "🌨️"),
        "368": ("Hafif Kar Sağanağı", "🌨️"),
        "371": ("Orta Kar Sağanağı", "🌨️"),
        "374": ("Hafif Dolu", "🌨️"),
        "377": ("Orta Dolu", "🌨️"),
        "386": ("Gök Gürültülü Sağanak", "⛈️"),
        "389": ("Şiddetli Gök Gürültülü Sağanak", "⛈️"),
        "392": ("Gök Gürültülü Kar", "⛈️"),
        "395": ("Şiddetli Kar Fırtınası", "❄️"),
    }

    # Türkçe şehir adı eşlemeleri
    CITY_MAP = {
        "istanbul": "Istanbul",
        "ankara": "Ankara",
        "izmir": "Izmir",
        "bursa": "Bursa",
        "antalya": "Antalya",
        "adana": "Adana",
        "konya": "Konya",
        "gaziantep": "Gaziantep",
        "mersin": "Mersin",
        "kayseri": "Kayseri",
    }

    @classmethod
    def get_weather(
        cls, city: str = "Istanbul", force_refresh: bool = False
    ) -> Optional[WeatherData]:
        """
        Şehir için hava durumu bilgisi döner

        Args:
            city: Şehir adı
            force_refresh: Önbelleği atla

        Returns:
            WeatherData veya None
        """
        # Şehir adını normalize et
        city_key = city.lower().strip()
        city_query = cls.CITY_MAP.get(city_key, city)

        with cls._lock:
            # Önbellek kontrolü
            if not force_refresh and city_key in cls._cache:
                cached = cls._cache[city_key]
                if datetime.now() - cached.updated_at < cls._cache_duration:
                    return cached

            # API'den çek
            try:
                weather_data = cls._fetch_weather(city_query)
                if weather_data:
                    cls._cache[city_key] = weather_data
                    return weather_data
            except Exception as e:
                print(f"Hava durumu çekme hatası ({city}): {e}")

            # Önbellekte varsa onu döndür
            return cls._cache.get(city_key)

    @classmethod
    def _fetch_weather(cls, city: str) -> Optional[WeatherData]:
        """API'den hava durumu çeker"""
        try:
            # wttr.in JSON formatı
            url = f"{cls.BASE_URL}/{city}?format=j1"

            response = requests.get(
                url,
                timeout=3,
                headers={"User-Agent": "AkilliIs-ERP/1.0"},
                verify=False,
            )
            response.raise_for_status()

            data = response.json()

            # Mevcut hava durumu
            current = data.get("current_condition", [{}])[0]

            # Hava durumu kodu
            weather_code = current.get("weatherCode", "113")
            condition, icon = cls.CONDITION_MAP.get(weather_code, ("Bilinmiyor", "❓"))

            return WeatherData(
                city=city,
                condition=condition,
                condition_icon=icon,
                temperature=int(current.get("temp_C", 0)),
                feels_like=int(current.get("FeelsLikeC", 0)),
                humidity=int(current.get("humidity", 0)),
                wind_speed=int(current.get("windspeedKmph", 0)),
                wind_direction=current.get("winddir16Point", ""),
                updated_at=datetime.now(),
            )

        except requests.RequestException as e:
            print(f"Hava durumu istek hatası: {e}")
            raise
        except (KeyError, ValueError, IndexError) as e:
            print(f"Hava durumu parse hatası: {e}")
            raise

    @classmethod
    def clear_cache(cls, city: Optional[str] = None):
        """
        Önbelleği temizler

        Args:
            city: Belirli şehir için temizle, None ise tümünü temizle
        """
        with cls._lock:
            if city:
                cls._cache.pop(city.lower().strip(), None)
            else:
                cls._cache = {}

    @classmethod
    def get_supported_cities(cls) -> list:
        """Desteklenen Türkiye şehirlerini döner"""
        return list(cls.CITY_MAP.keys())
