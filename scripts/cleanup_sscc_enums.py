import sys
import os

# Proje kök dizinini path'e ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.base import get_session
from sqlalchemy import text


def cleanup_enums():
    session = get_session()
    try:
        print("Cleaning up SSCC enums...")
        session.execute(text("DROP TYPE IF EXISTS transportunittype CASCADE"))
        session.execute(text("DROP TYPE IF EXISTS transportunitstatus CASCADE"))
        session.commit()
        print("Enums dropped successfully.")
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    cleanup_enums()
