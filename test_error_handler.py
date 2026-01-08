"""
Test ErrorHandler - Örnek hata kayıtları oluştur
"""

from database.base import get_session
from database.models.user import User
from modules.development import ErrorHandler

# Mock user oluştur
session = get_session()
user = session.query(User).filter(User.username == 'admin').first()

if user:
    ErrorHandler.set_current_user(user)
    print(f"✓ User set: {user.username}")
else:
    print("✗ Admin user not found!")
    exit(1)

# Test hataları oluştur
print("\n" + "="*50)
print("TEST HATALARI OLUŞTURULUYOR")
print("="*50 + "\n")

# 1. Critical Error
try:
    raise ValueError("Critical database connection error!")
except Exception as e:
    ErrorHandler.handle_error(
        e,
        module='inventory',
        screen='WarehouseModule',
        function='connect_database',
        severity='critical',
        show_message=False
    )
    print("✓ Critical error kaydedildi")

# 2. Normal Error
try:
    raise KeyError("Item not found in inventory")
except Exception as e:
    ErrorHandler.handle_error(
        e,
        module='inventory',
        screen='ItemModule',
        function='get_item',
        severity='error',
        show_message=False
    )
    print("✓ Error kaydedildi")

# 3. Warning
try:
    raise Warning("Stock level is low")
except Exception as e:
    ErrorHandler.handle_error(
        e,
        module='inventory',
        screen='StockModule',
        function='check_stock_level',
        severity='warning',
        show_message=False
    )
    print("✓ Warning kaydedildi")

# 4. Info
try:
    raise Exception("User logged in successfully")
except Exception as e:
    ErrorHandler.handle_error(
        e,
        module='system',
        screen='LoginModule',
        function='login',
        severity='info',
        show_message=False
    )
    print("✓ Info kaydedildi")

# 5. Production Error
try:
    raise RuntimeError("Work order failed to complete")
except Exception as e:
    ErrorHandler.handle_error(
        e,
        module='production',
        screen='WorkOrderModule',
        function='complete_order',
        severity='error',
        show_message=False
    )
    print("✓ Production error kaydedildi")

# 6. Purchasing Error
try:
    raise ConnectionError("Supplier API connection timeout")
except Exception as e:
    ErrorHandler.handle_error(
        e,
        module='purchasing',
        screen='SupplierModule',
        function='sync_suppliers',
        severity='error',
        show_message=False
    )
    print("✓ Purchasing error kaydedildi")

session.close()

print("\n" + "="*50)
print("TEST TAMAMLANDI!")
print("="*50)
print("\nUygulamayı açıp 'Geliştirme > Hata Kayıtları' ekranını kontrol edin.")
print("6 adet test hatası görmelisiniz.\n")
