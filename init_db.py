#!/usr/bin/env python3
"""
Akıllı İş - Veritabanı Başlatma Scripti
Tabloları oluşturur ve varsayılan verileri ekler.
"""

import sys
from pathlib import Path

# Proje kökünü path'e ekle
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from database import init_database, get_session
from database.models import User, Role
import bcrypt


def create_admin_user():
    """Varsayılan admin kullanıcısı oluştur"""
    session = get_session()
    
    try:
        # Admin var mı kontrol et
        admin = session.query(User).filter(User.username == 'admin').first()
        if admin:
            print("ℹ Admin kullanıcısı zaten mevcut")
            return
        
        # Admin rolünü bul
        admin_role = session.query(Role).filter(Role.code == 'ADMIN').first()
        
        # Şifreyi hashle
        password = "admin123"  # Varsayılan şifre
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Admin kullanıcısı oluştur
        admin = User(
            username='admin',
            email='admin@akilliis.local',
            password_hash=password_hash,
            first_name='Sistem',
            last_name='Yöneticisi',
            is_superuser=True,
            is_verified=True,
        )
        
        if admin_role:
            admin.roles.append(admin_role)
        
        session.add(admin)
        session.commit()
        
        print("✓ Admin kullanıcısı oluşturuldu")
        print(f"  Kullanıcı adı: admin")
        print(f"  Şifre: {password}")
        print("  ⚠ Lütfen şifreyi değiştirin!")
        
    except Exception as e:
        session.rollback()
        print(f"✗ Admin oluşturma hatası: {e}")
    finally:
        session.close()


def main():
    """Ana fonksiyon"""
    print("=" * 50)
    print("Akıllı İş - Veritabanı Başlatılıyor")
    print("=" * 50)
    print()
    
    # Tabloları oluştur
    print("[1/2] Tablolar oluşturuluyor...")
    init_database()
    
    # Admin kullanıcısı oluştur
    print("\n[2/2] Admin kullanıcısı oluşturuluyor...")
    create_admin_user()
    
    print()
    print("=" * 50)
    print("✓ Veritabanı başarıyla hazırlandı!")
    print("=" * 50)


if __name__ == "__main__":
    main()
