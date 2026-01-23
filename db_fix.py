from sqlalchemy import text
from database.base import get_session


def fix_db():
    session = get_session()
    try:
        print("Checking/Adding overhead_rate to work_stations...")
        try:
            session.execute(
                text(
                    "ALTER TABLE work_stations ADD COLUMN overhead_rate NUMERIC(18, 4) DEFAULT 0"
                )
            )
            session.commit()
            print("✅ overhead_rate added.")
        except Exception:
            print("⚠️ overhead_rate might already exist or error.")
            session.rollback()

        print("Adding bom_type to bill_of_materials...")
        try:
            session.execute(
                text(
                    "ALTER TABLE bill_of_materials ADD COLUMN bom_type VARCHAR(20) DEFAULT 'STANDARD' NOT NULL"
                )
            )
            session.commit()
            print("✅ bom_type added.")
        except Exception as e:
            print(f"⚠️ bom_type error (maybe exists): {e}")
            session.rollback()

        print("Adding columns to work_orders...")
        columns_to_add = [
            ("batch_number", "VARCHAR(100)"),
            ("production_notes", "TEXT"),
            ("quality_notes", "TEXT"),
            ("shipping_notes", "TEXT"),
            ("qc_approved_quantity", "NUMERIC(18, 4) DEFAULT 0"),
            ("qc_rejected_quantity", "NUMERIC(18, 4) DEFAULT 0"),
            ("qc_notes", "TEXT"),
            ("qc_checked_by", "INTEGER"),
            ("qc_checked_at", "TIMESTAMP"),
        ]

        for col_name, col_type in columns_to_add:
            try:
                session.execute(
                    text(f"ALTER TABLE work_orders ADD COLUMN {col_name} {col_type}")
                )
                session.commit()
                print(f"✅ work_orders.{col_name} added.")
            except Exception:
                print(f"⚠️ work_orders.{col_name} maybe exists.")
                session.rollback()

        print("Normalizing bom_type values to UPPERCASE...")
        try:
            session.execute(text("UPDATE bill_of_materials SET bom_type = 'STANDARD'"))
            session.commit()
            print("✅ bom_type normalized to STANDARD.")
        except Exception as e:
            print(f"⚠️ BOM update error: {e}")
            session.rollback()

    except Exception as e:
        print(f"❌ General Error: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    fix_db()
