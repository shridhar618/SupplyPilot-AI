import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import sys
import os

# Add the backend directory to the path so we can import the models
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.product_catalog.main import Base, Product, ProductCategory, ProductAttribute
from passlib.context import CryptPwdContext

# Setup test database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_create_product_category():
    """Test creating a product category"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        category = ProductCategory(
            name="Electronics",
            description="Electronic devices and gadgets",
            level=1,
            sort_order=1,
            is_active=True
        )
        db.add(category)
        db.commit()
        db.refresh(category)

        assert category.id is not None
        assert category.name == "Electronics"
        assert category.description == "Electronic devices and gadgets"
        assert category.level == 1
        assert category.is_active == True
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_create_product():
    """Test creating a product"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        # First create a category
        category = ProductCategory(
            name="Electronics",
            level=1,
            is_active=True
        )
        db.add(category)
        db.commit()
        db.refresh(category)

        # Then create a product
        product = Product(
            sku="PHONE-001",
            name="Smartphone XYZ",
            description="Latest smartphone model",
            category_id=category.id,
            brand="TechBrand",
            unit_of_measure="units",
            weight=0.2,
            is_active=True
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        assert product.id is not None
        assert product.sku == "PHONE-001"
        assert product.name == "Smartphone XYZ"
        assert product.category_id == category.id
        assert product.brand == "TechBrand"
        assert product.is_active == True
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_create_product_attribute():
    """Test creating a product attribute"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        # Create category and product first
        category = ProductCategory(name="Electronics", level=1, is_active=True)
        db.add(category)
        db.commit()
        db.refresh(category)

        product = Product(
            sku="PHONE-001",
            name="Smartphone XYZ",
            category_id=category.id,
            is_active=True
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        # Create attribute
        attribute = ProductAttribute(
            product_id=product.id,
            name="Color",
            value="Black",
            attribute_type="color"
        )
        db.add(attribute)
        db.commit()
        db.refresh(attribute)

        assert attribute.id is not None
        assert attribute.product_id == product.id
        assert attribute.name == "Color"
        assert attribute.value == "Black"
        assert attribute.attribute_type == "color"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

if __name__ == "__main__":
    test_create_product_category()
    test_create_product()
    test_create_product_attribute()
    print("All tests passed!")