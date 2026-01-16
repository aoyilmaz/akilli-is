from sqlalchemy import text
from database.base import get_session


def fix_schema_phase3():
    """Phase 3 (Operator Panel) schema değişiklikleri"""
    session = get_session()
    try:
        print("Schema düzeltmeleri başlıyor (Phase 3)...")

        # 1. WorkOrderOperation tablosuna last_start_time ekle
        try:
            session.execute(
                text(
                    "ALTER TABLE work_order_operations ADD COLUMN last_start_time TIMESTAMP"
                )
            )
            print("Eklendi: work_order_operations.last_start_time")
        except Exception as e:
            print(
                f"Atlandı (Zaten var olabilir): work_order_operations.last_start_time - {str(e)}"
            )

        session.commit()

        # 2. WorkOrderOperationPersonnel tablosunu oluştur
        # SQLAlchemy create_all kullanmak yerine manuel SQL ile yapalım ki garanti olsun
        try:
            sql = """
            CREATE TABLE IF NOT EXISTS work_order_operation_personnel (
                id SERIAL PRIMARY KEY,
                operation_id INTEGER NOT NULL REFERENCES work_order_operations(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES users(id),
                role VARCHAR(50) DEFAULT 'operator',
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                duration_minutes INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_woopp_op ON work_order_operation_personnel(operation_id);
            CREATE INDEX IF NOT EXISTS idx_woopp_user ON work_order_operation_personnel(user_id);
            """
            session.execute(text(sql))
            print("Oluşturuldu: work_order_operation_personnel tablosu")
        except Exception as e:
            print(
                f"Hata: work_order_operation_personnel tablosu oluşturulamadı - {str(e)}"
            )

        session.commit()
        print("Schema düzeltmeleri tamamlandı.")

    except Exception as e:
        session.rollback()
        print(f"Hata oluştu: {str(e)}")
    finally:
        session.close()


if __name__ == "__main__":
    fix_schema_phase3()
