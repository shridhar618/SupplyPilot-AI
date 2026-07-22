"""
Unit tests for the Inventory Level and Optimization models in the Inventory Optimization Service.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import sys
import os

# Add the backend directory to the path so we can import the models
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.inventory_optimization.main import Base, InventoryLevel, InventoryOptimization
import uuid

# Setup test database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_create_inventory_level():
    """Test creating an inventory level"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        inventory_level = InventoryLevel(
            product_id=uuid.uuid4(),
            location_id=uuid.uuid4(),
            quantity_on_hand=100,
            quantity_allocated=20,
            quantity_on_order=50,
            safety_stock=30,
            reorder_point=70
        )
        db.add(inventory_level)
        db.commit()
        db.refresh(inventory_level)

        assert inventory_level.id is not None
        assert inventory_level.quantity_on_hand == 100
        assert inventory_level.quantity_allocated == 20
        assert inventory_level.quantity_on_order == 50
        assert inventory_level.quantity_available == 80  # 100 - 20
        assert inventory_level.safety_stock == 30
        assert inventory_level.reorder_point == 70
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_inventory_level_unique_constraint():
    """Test that inventory level for same product and location is unique"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        product_id = uuid.uuid4()
        location_id = uuid.uuid4()

        # Create first inventory level
        inv1 = InventoryLevel(
            product_id=product_id,
            location_id=location_id,
            quantity_on_hand=100,
            quantity_allocated=0,
            quantity_on_order=0
        )
        db.add(inv1)
        db.commit()

        # Try to create second inventory level for same product and location
        inv2 = InventoryLevel(
            product_id=product_id,
            location_id=location_id,
            quantity_on_hand=50,
            quantity_allocated=0,
            quantity_on_order=0
        )
        db.add(inv2)

        # This should raise an IntegrityError due to unique constraint
        with pytest.raises(IntegrityError):
            db.commit()
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_create_inventory_optimization():
    """Test creating an inventory optimization record"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        optimization = InventoryOptimization(
            product_id=uuid.uuid4(),
            location_id=uuid.uuid4(),
            optimization_date=datetime.datetime.utcnow(),
            recommended_order_quantity=50,
            recommended_order_date=datetime.datetime.utcnow() + datetime.timedelta(days=1),
            expected_stockout_date=datetime.datetime.utcnow() + datetime.timedelta(days=10),
            total_cost=125.50,
            service_level=0.95,
            safety_stock=20,
            reorder_point=80
        )
        db.add(optimization)
        db.commit()
        db.refresh(optimization)

        assert optimization.id is not None
        assert optimization.recommended_order_quantity == 50
        assert optimization.total_cost == 125.50
        assert optimization.service_level == 0.95
        assert optimization.safety_stock == 20
        assert optimization.reorder_point == 80
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

if __name__ == "__main__":
    test_create_inventory_level()
    test_inventory_level_unique_constraint()
    test_create_inventory_optimization()
    print("All tests passed!")