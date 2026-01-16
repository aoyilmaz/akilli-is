import sys
import os

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

print("Attempting to import CRMModule...")
try:
    from modules.crm.views import CRMModule

    print("SUCCESS: CRMModule imported.")
except Exception as e:
    print(f"FAILURE: {type(e).__name__}: {e}")
    import traceback

    traceback.print_exc()
