"""
Unit tests for the Supplier and Purchase Order models in the Supply Chain Resilience Service.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import sys
import os
import uuid
from datetime import datetime, timedelta

# Add the backend directory to the path so we can import the models
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.supply_chain_resilience.main import Base, Supplier, PurchaseOrder, PurchaseOrderItem, SupplierPerformance, SupplyChainRisk

# Setup test database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_create_supplier():
    """Test creating a supplier"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        supplier = Supplier(
            supplier_code="SUP001",
            name="Test Supplier",
            contact_person="John Doe",
            email="john@example.com",
            phone="123-456-7890",
            address="123 Supplier St",
            city="Supplier City",
            state_province="SC",
            country="USA",
            postal_code="12345",
            lead_time_days=7,
            reliability_score=0.95,
            quality_score=0.90,
            on_time_delivery_rate=0.92,
            risk_score=0.15
        )
        db.add(supplier)
        db.commit()
        db.refresh(supplier)

        assert supplier.id is not None
        assert supplier.supplier_code == "SUP001"
        assert supplier.name == "Test Supplier"
        assert supplier.reliability_score == 0.95
        assert supplier.quality_score == 0.90
        assert supplier.on_time_delivery_rate == 0.92
        assert supplier.risk_score == 0.15
        assert supplier.is_active == True
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_supplier_score_validation():
    """Test that supplier scores are validated"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        # Test invalid reliability score (> 1)
        supplier = Supplier(
            supplier_code="SUP002",
            name="Invalid Supplier",
            reliability_score=1.5  # Invalid - should be <= 1
        )
        db.add(supplier)
        with pytest.raises(Exception):  # Should raise validation error
            db.commit()

        db.rollback()

        # Test invalid quality score (< 0)
        supplier.quality_score = -0.1  # Invalid - should be >= 0
        db.add(supplier)
        with pytest.raises(Exception):  # Should raise validation error
            db.commit()
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_supplier_unique_code():
    """Test that supplier code must be unique"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        # Create first supplier
        supplier1 = Supplier(
            supplier_code="SUP003",
            name="First Supplier",
            reliability_score=0.8
        )
        db.add(supplier1)
        db.commit()

        # Try to create second supplier with same code
        supplier2 = Supplier(
            supplier_code="SUP003",  # Same code
            name="Second Supplier",
            reliability_score=0.7
        )
        db.add(supplier2)

        # This should raise an IntegrityError due to unique constraint
        with pytest.raises(IntegrityError):
            db.commit()
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_create_purchase_order():
    """Test creating a purchase order"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        # First create a supplier
        supplier = Supplier(
            supplier_code="SUP004",
            name="PO Test Supplier",
            reliability_score=0.9
        )
        db.add(supplier)
        db.commit()
        db.refresh(supplier)

        # Create purchase order
        po = PurchaseOrder(
            po_number="PO-2024-001",
            supplier_id=supplier.id,
            order_date=datetime.utcnow(),
            expected_delivery_date=datetime.utcnow() + timedelta(days=7),
            status="sent",
            total_amount=1500.00,
            currency="USD"
        )
        db.add(po)
        db.commit()
        db.refresh(po)

        assert po.id is not None
        assert po.po_number == "PO-2024-001"
        assert po.supplier_id == supplier.id
        assert po.status == "sent"
        assert po.total_amount == 1500.00
        assert po.currency == "USD"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_purchase_order_duplicate_number():
    """Test that PO number must be unique"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        # Create a supplier
        supplier = Supplier(
            supplier_code="SUP005",
            name="PO Duplicate Test",
            reliability_score=0.85
        )
        db.add(supplier)
        db.commit()
        db.refresh(supplier)

        # Create first PO
        po1 = PurchaseOrder(
            po_number="PO-DUP-001",
            supplier_id=supplier.id,
            order_date=datetime.utcnow(),
            total_amount=1000.00
        )
        db.add(po1)
        db.commit()

        # Try to create second PO with same number
        po2 = PurchaseOrder(
            po_number="PO-DUP-001",  # Duplicate
            supplier_id=supplier.id,
            order_date=datetime.utcnow(),
            total_amount=500.00
        )
        db.add(po2)

        # This should raise an IntegrityError due to unique constraint
        with pytest.raises(IntegrityError):
            db.commit()
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

if __name__ == "__main__":
    test_create_supplier()
    test_supplier_score_validation()
    test_supplier_unique_code()
    test_create_purchase_order()
    test_purchase_order_duplicate_number()
    print("All supply chain resilience tests passed!")