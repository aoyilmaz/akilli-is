import sys
import os

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from database.base import get_engine, Base

# Import all models to ensure they are registered with Base
from database.models import *

# Explicitly import CRM to be sure
import database.models.crm


def init_db():
    print("Initializing database tables...")
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")


if __name__ == "__main__":
    init_db()
