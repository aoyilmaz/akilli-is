import sys
import os

# Proje kök dizinini path'e ekle
sys.path.append(os.getcwd())

from database.base import get_session
from database.models.user import User, UserPagePermission
from database.models.hr import Employee
from database.models.production import WorkOrderOperationPersonnel, ProductionDowntime
from database.models.maintenance import MaintenanceRequest, MaintenanceWorkOrder
from sqlalchemy import or_


def delete_all_users_except_admin():
    session = get_session()
    try:
        # Admin olmayan kullanıcıları bul
        users_to_delete = session.query(User).filter(User.username != "admin").all()

        if not users_to_delete:
            print("Silinecek kullanıcı bulunamadı.")
            return

        print(f"{len(users_to_delete)} adet kullanıcı silinecek...")

        user_ids = [u.id for u in users_to_delete]

        # 1. Employee tablosundaki bağlantıları kaldır (user_id = NULL)
        print("Personel bağlantıları kaldırılıyor...")
        session.query(Employee).filter(Employee.user_id.in_(user_ids)).update(
            {Employee.user_id: None}, synchronize_session=False
        )

        # 2. Üretim Modülü referanslarını temizle
        print("Üretim modülü referansları temizleniyor...")
        session.query(WorkOrderOperationPersonnel).filter(
            WorkOrderOperationPersonnel.user_id.in_(user_ids)
        ).update({WorkOrderOperationPersonnel.user_id: None}, synchronize_session=False)

        session.query(ProductionDowntime).filter(
            ProductionDowntime.operator_id.in_(user_ids)
        ).update({ProductionDowntime.operator_id: None}, synchronize_session=False)

        # 3. Bakım Modülü referanslarını temizle
        print("Bakım modülü referansları temizleniyor...")
        session.query(MaintenanceRequest).filter(
            MaintenanceRequest.reported_by_id.in_(user_ids)
        ).update({MaintenanceRequest.reported_by_id: None}, synchronize_session=False)

        session.query(MaintenanceWorkOrder).filter(
            MaintenanceWorkOrder.assigned_to_id.in_(user_ids)
        ).update({MaintenanceWorkOrder.assigned_to_id: None}, synchronize_session=False)

        # 4. İzinleri sil
        print("Kullanıcı izinleri siliniyor...")
        session.query(UserPagePermission).filter(
            UserPagePermission.user_id.in_(user_ids)
        ).delete(synchronize_session=False)

        # 5. Kullanıcıları sil
        print("Kullanıcılar siliniyor...")
        for user in users_to_delete:
            session.delete(user)
            print(f"Silindi: {user.username}")

        session.commit()
        print("İşlem başarıyla tamamlandı.")

    except Exception as e:
        session.rollback()
        print(f"HATA: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    delete_all_users_except_admin()
