import sys
import os

sys.path.append(os.getcwd())
import enum
from database.models.production import BOMType
from database.base import get_session
from sqlalchemy import text

print(f"BOMType: {BOMType}")
print(f"BOMType members: {list(BOMType)}")
print(f"BOMType.STANDARD.value: {BOMType.STANDARD.value}")
try:
    print(f"BOMType('standard'): {BOMType('standard')}")
except Exception as e:
    print(f"Error mapping 'standard': {e}")

session = get_session()
try:
    res = session.execute(text("SELECT bom_type FROM bill_of_materials")).fetchall()
    print(f"DB Values: {res}")
except Exception as e:
    print(f"DB Error: {e}")
finally:
    session.close()
