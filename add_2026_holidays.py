"""
2026 Yılı Türkiye Resmi Tatillerini Veritabanına Ekle
"""

from datetime import date
from database import get_session
from modules.production.calendar_services import HolidayService


# 2026 Türkiye Resmi Tatilleri
HOLIDAYS_2026 = [
    # Yılbaşı
    (date(2026, 1, 1), "Yılbaşı", False),
    # Ulusal Egemenlik ve Çocuk Bayramı
    (date(2026, 4, 23), "Ulusal Egemenlik ve Çocuk Bayramı", False),
    # Emek ve Dayanışma Günü
    (date(2026, 5, 1), "Emek ve Dayanışma Günü", False),
    # Atatürk'ü Anma, Gençlik ve Spor Bayramı
    (date(2026, 5, 19), "Atatürk'ü Anma, Gençlik ve Spor Bayramı", False),
    # Ramazan Bayramı (2026 tahmini: 19-21 Mart)
    (date(2026, 3, 19), "Ramazan Bayramı Arifesi", True),  # Yarım gün
    (date(2026, 3, 20), "Ramazan Bayramı 1. Gün", False),
    (date(2026, 3, 21), "Ramazan Bayramı 2. Gün", False),
    (date(2026, 3, 22), "Ramazan Bayramı 3. Gün", False),
    # Kurban Bayramı (2026 tahmini: 26-29 Mayıs)
    (date(2026, 5, 26), "Kurban Bayramı Arifesi", True),  # Yarım gün
    (date(2026, 5, 27), "Kurban Bayramı 1. Gün", False),
    (date(2026, 5, 28), "Kurban Bayramı 2. Gün", False),
    (date(2026, 5, 29), "Kurban Bayramı 3. Gün", False),
    (date(2026, 5, 30), "Kurban Bayramı 4. Gün", False),
    # Demokrasi ve Milli Birlik Günü
    (date(2026, 7, 15), "Demokrasi ve Milli Birlik Günü", False),
    # Zafer Bayramı
    (date(2026, 8, 30), "Zafer Bayramı", False),
    # Cumhuriyet Bayramı
    (date(2026, 10, 28), "Cumhuriyet Bayramı Arifesi", True),  # Yarım gün
    (date(2026, 10, 29), "Cumhuriyet Bayramı", False),
]


def add_holidays():
    """Tatilleri veritabanına ekle"""
    session = get_session()

    try:
        service = HolidayService()
        service.session = session

        added = 0
        skipped = 0

        for holiday_date, name, is_half_day in HOLIDAYS_2026:
            # Zaten var mı kontrol et
            existing = service.get_by_date(holiday_date)
            if existing:
                print(f"⏭ Zaten var: {holiday_date} - {name}")
                skipped += 1
                continue

            # Ekle
            service.create(
                holiday_date=holiday_date,
                name=name,
                is_half_day=is_half_day,
                applies_to_all=True,
            )
            print(f"✓ Eklendi: {holiday_date} - {name}")
            added += 1

        session.commit()
        print(f"\n{'='*50}")
        print(f"Toplam: {added} tatil eklendi, {skipped} zaten vardı")

    except Exception as e:
        session.rollback()
        print(f"Hata: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    print("2026 Türkiye Resmi Tatilleri Ekleniyor...")
    print("=" * 50)
    add_holidays()
