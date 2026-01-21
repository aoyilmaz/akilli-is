import sys
import os
from pathlib import Path
from decimal import Decimal
from sqlalchemy import text
from datetime import datetime

# Add root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from database.base import get_session, get_engine
from database.models.production import (
    BillOfMaterials,
    BOMLine,
    WorkOrder,
    WorkOrderStatus,
)
from database.models.inventory import Item, Unit
from modules.production.services.base import WorkOrderService


def check_and_migrate():
    session = get_session()
    engine = get_engine()
    print(f"Database Engine: {engine.name}")

    try:
        # Check if column exists by trying to select it
        try:
            session.execute(text("SELECT is_percentage FROM bom_lines LIMIT 1"))
            print("✓ 'is_percentage' column already exists.")
        except Exception:
            print("! 'is_percentage' column missing. Adding it...")
            session.rollback()
            # Add column
            if engine.name == "sqlite":
                session.execute(
                    text(
                        "ALTER TABLE bom_lines ADD COLUMN is_percentage BOOLEAN DEFAULT 0"
                    )
                )
            else:
                session.execute(
                    text(
                        "ALTER TABLE bom_lines ADD COLUMN is_percentage BOOLEAN DEFAULT FALSE"
                    )
                )
            session.commit()
            print("✓ Column added successfully.")

    except Exception as e:
        print(f"Migration Error: {e}")
        session.rollback()
    finally:
        session.close()


def test_calculation():
    session = get_session()
    engine = get_engine()
    try:
        # Debug Enum Values if Postgres
        if engine.name != "sqlite":
            try:
                result = session.execute(
                    text("SELECT enum_range(NULL::workorderstatus)")
                ).scalar()
                print(f"Valid WorkOrderStatus values in DB: {result}")
            except Exception as e:
                print(f"Could not fetch enum values: {e}")

        # 1. Create Test Item (Product)
        product = session.query(Item).filter_by(code="TEST_PROD_PCT").first()
        if not product:
            product = Item(
                code="TEST_PROD_PCT",
                name="Test Yüzdelik Mamul",
                net_weight=Decimal("10.00"),  # 10 KG Net Weight
                unit_id=1,  # Adet assumed
            )
            session.add(product)
            session.commit()

        # 2. Create Raw Material
        raw_mat = session.query(Item).filter_by(code="TEST_RAW_PCT").first()
        if not raw_mat:
            raw_mat = Item(
                code="TEST_RAW_PCT", name="Test Hammadde", unit_id=2  # KG assumed
            )
            session.add(raw_mat)
            session.commit()

        # 3. Create BOM
        bom = session.query(BillOfMaterials).filter_by(code="BOM_TEST_PCT").first()
        if bom:
            # Delete associated WO first?
            # Cascades should handle it but safer to clean manually if not
            pass
            session.delete(bom)
            session.commit()

        bom = BillOfMaterials(
            code="BOM_TEST_PCT",
            name="Test Percentage BOM",
            item_id=product.id,
            base_quantity=Decimal("1"),
            unit_id=1,
        )
        session.add(bom)
        session.commit()

        # Add Line: 50%
        line = BOMLine(
            bom_id=bom.id,
            item_id=raw_mat.id,
            quantity=Decimal("50"),
            is_percentage=True,
            unit_id=2,
        )
        session.add(line)
        session.commit()

        # 4. Create Work Order
        wo_service = WorkOrderService()

        # Clean existing
        try:
            session.execute(
                text("DELETE FROM work_orders WHERE order_no = 'WO_TEST_PCT_001'")
            )
            session.commit()
        except Exception as e:
            print(f"Cleanup warning: {e}")
            session.rollback()

        wo = WorkOrder(
            order_no="WO_TEST_PCT_001",
            item_id=product.id,
            bom_id=bom.id,
            planned_quantity=Decimal("10"),
            status=WorkOrderStatus.DRAFT,
        )
        session.add(wo)
        session.commit()

        # 5. Run Calculation Logic
        print("Running calculation...")
        wo_service.session = session
        wo_service._create_lines_from_bom(wo, bom.id, wo.planned_quantity)
        session.commit()

        # 6. Verify
        # Expected:
        # Planned Qty: 10
        # Unit Net Weight: 10kg
        # Total Net Weight: 100kg
        # Line Percentage: 50%
        # Required Qty: 50% of 100kg = 50kg.

        # Refresh WO
        session.refresh(wo)
        if not wo.lines:
            print("✗ TEST FAILED: No lines created.")
            return

        wo_line = wo.lines[0]
        print(f"Required Quantity: {wo_line.required_quantity}")

        expected = Decimal("50.00")
        if abs(wo_line.required_quantity - expected) < Decimal("0.01"):
            print("✓ TEST PASSED: Calculation is correct.")
        else:
            print(
                f"✗ TEST FAILED: Expected {expected}, got {wo_line.required_quantity}"
            )

        # Cleanup
        session.execute(
            text("DELETE FROM work_orders WHERE order_no = 'WO_TEST_PCT_001'")
        )
        session.delete(bom)
        # Keep items for re-run convenience or delete them
        session.commit()

    except Exception as e:
        print(f"Test Error: {e}")
        import traceback

        traceback.print_exc()
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    check_and_migrate()
    test_calculation()
