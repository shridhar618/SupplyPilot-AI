"""
Product Catalog Service for SupplyPilot AI
Handles product information, categories, and attributes
"""
import os
import logging
from typing import List, Optional
from uuid import uuid4
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Text, Integer, ForeignKey, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pydantic import BaseModel, Field

# Initialize FastAPI app
app = FastAPI(
    title="SupplyPilot AI - Product Catalog Service",
    description="Service for managing product information, categories, and attributes",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/demandsense")

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class ProductCategory(Base):
    __tablename__ = "product_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("product_categories.id"), nullable=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    level = Column(Integer, nullable=False)  # 1=top level, 2=subcategory, etc.
    sort_order = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    children = relationship("ProductCategory", back_populates="parent")
    parent = relationship("ProductCategory", back_populates="children", remote_side=[id])
    products = relationship("Product", back_populates="category")

    __table_args__ = (
        Index('idx_category_name', 'name'),
        Index('idx_category_level', 'level'),
    )

class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    sku = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("product_categories.id"), nullable=True)
    brand = Column(String(100), nullable=True)
    unit_of_measure = Column(String(20), nullable=True)
    weight = Column(Numeric(precision=10, scale=3), nullable=True)
    dimensions = Column(JSONB, nullable=True)  # {length: float, width: float, height: float, unit: 'cm'}
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category = relationship("ProductCategory", back_populates="products")
    attributes = relationship("ProductAttribute", back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_product_sku', 'sku'),
        Index('idx_product_name', 'name'),
        Index('idx_product_category', 'category_id'),
    )

class ProductAttribute(Base):
    __tablename__ = "product_attributes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    name = Column(String(100), nullable=False)
    value = Column(String(255), nullable=True)
    attribute_type = Column(String(50), nullable=True)  # color, size, material, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="attributes")

    __table_args__ = (
        Index('idx_attribute_product', 'product_id'),
        Index('idx_attribute_name', 'name'),
    )

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic Models
class ProductCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    level: int
    sort_order: Optional[int] = None
    is_active: bool = True

class ProductCategoryCreate(ProductCategoryBase):
    pass

class ProductCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None
    level: Optional[int] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

class ProductCategoryResponse(ProductCategoryBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ProductBase(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    category_id: Optional[str] = None
    brand: Optional[str] = None
    unit_of_measure: Optional[str] = None
    weight: Optional[float] = None
    dimensions: Optional[dict] = None
    is_active: bool = True

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    brand: Optional[str] = None
    unit_of_measure: Optional[str] = None
    weight: Optional[float] = None
    dimensions: Optional[dict] = None
    is_active: Optional[bool] = None

class ProductResponse(ProductBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ProductAttributeBase(BaseModel):
    name: str
    value: Optional[str] = None
    attribute_type: Optional[str] = None

class ProductAttributeCreate(ProductAttributeBase):
    pass

class ProductAttributeUpdate(BaseModel):
    name: Optional[str] = None
    value: Optional[str] = None
    attribute_type: Optional[str] = None

class ProductAttributeResponse(ProductAttributeBase):
    id: str
    product_id: str
    created_at: datetime

    class Config:
        orm_mode = True

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Routes
@app.get("/")
async def root():
    return {
        "service": "Product Catalog Service",
        "version": "0.1.0",
        "status": "running"
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Check database connection
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# Product Category Endpoints
@app.get("/categories", response_model=List[ProductCategoryResponse])
async def read_categories(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get list of product categories"""
    query = db.query(ProductCategory)
    if is_active is not None:
        query = query.filter(ProductCategory.is_active == is_active)

    categories = query.offset(skip).limit(limit).all()
    return categories

@app.get("/categories/{category_id}", response_model=ProductCategoryResponse)
async def read_category(
    category_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific category by ID"""
    category = db.query(ProductCategory).filter(ProductCategory.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@app.post("/categories", response_model=ProductCategoryResponse)
async def create_category(
    category: ProductCategoryCreate,
    db: Session = Depends(get_db)
):
    """Create a new product category"""
    # Check if category with same name and parent already exists (optional)
    db_category = ProductCategory(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@app.put("/categories/{category_id}", response_model=ProductCategoryResponse)
async def update_category(
    category_id: str,
    category_update: ProductCategoryUpdate,
    db: Session = Depends(get_db)
):
    """Update a product category"""
    db_category = db.query(ProductCategory).filter(ProductCategory.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    update_data = category_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)

    db_category.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_category)
    return db_category

@app.delete("/categories/{category_id}")
async def delete_category(
    category_id: str,
    db: Session = Depends(get_db)
):
    """Delete a product category (soft delete)"""
    db_category = db.query(ProductCategory).filter(ProductCategory.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    # Soft delete
    db_category.is_active = False
    db_category.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Category deactivated successfully"}

# Product Endpoints
@app.get("/products", response_model=List[ProductResponse])
async def read_products(
    skip: int = 0,
    limit: int = 100,
    sku: Optional[str] = None,
    name: Optional[str] = None,
    category_id: Optional[str] = None,
    brand: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get list of products with filtering"""
    query = db.query(Product)

    if sku:
        query = query.filter(Product.sku.ilike(f"%{sku}%"))
    if name:
        query = query.filter(Product.name.ilike(f"%{name}%"))
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if brand:
        query = query.filter(Product.brand.ilike(f"%{brand}%"))
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)

    products = query.offset(skip).limit(limit).all()
    return products

@app.get("/products/{product_id}", response_model=ProductResponse)
async def read_product(
    product_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific product by ID"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.post("/products", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
):
    """Create a new product"""
    # Check if SKU already exists
    db_product = db.query(Product).filter(Product.sku == product.sku).first()
    if db_product:
        raise HTTPException(status_code=400, detail="Product with this SKU already exists")

    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_update: ProductUpdate,
    db: Session = Depends(get_db)
):
    """Update a product"""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = product_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)

    db_product.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_product)
    return db_product

@app.delete("/products/{product_id}")
async def delete_product(
    product_id: str,
    db: Session = Depends(get_db)
):
    """Delete a product (soft delete)"""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    # Soft delete
    db_product.is_active = False
    db_product.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Product deactivated successfully"}

# Product Attribute Endpoints
@app.get("/products/{product_id}/attributes", response_model=List[ProductAttributeResponse])
async def read_product_attributes(
    product_id: str,
    db: Session = Depends(get_db)
):
    """Get attributes for a product"""
    # Verify product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    attributes = db.query(ProductAttribute).filter(ProductAttribute.product_id == product_id).all()
    return attributes

@app.post("/products/{product_id}/attributes", response_model=ProductAttributeResponse)
async def create_product_attribute(
    product_id: str,
    attribute: ProductAttributeCreate,
    db: Session = Depends(get_db)
):
    """Add attribute to a product"""
    # Verify product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    # Create attribute
    db_attribute = ProductAttribute(
        product_id=product_id,
        **attribute.dict()
    )
    db.add(db_attribute)
    db.commit()
    db.refresh(db_attribute)
    return db_attribute

@app.put("/products/{product_id}/attributes/{attribute_id}", response_model=ProductAttributeResponse)
async def update_product_attribute(
    product_id: str,
    attribute_id: str,
    attribute_update: ProductAttributeUpdate,
    db: Session = Depends(get_db)
):
    """Update a product attribute"""
    # Verify product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    # Get attribute
    db_attribute = db.query(ProductAttribute).filter(
        ProductAttribute.id == attribute_id,
        ProductAttribute.product_id == product_id
    ).first()
    if db_attribute is None:
        raise HTTPException(status_code=404, detail="Attribute not found")

    # Update attribute
    update_data = attribute_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_attribute, field, value)

    db.commit()
    db.refresh(db_attribute)
    return db_attribute

@app.delete("/products/{product_id}/attributes/{attribute_id}")
async def delete_product_attribute(
    product_id: str,
    attribute_id: str,
    db: Session = Depends(get_db)
):
    """Delete a product attribute"""
    # Verify product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    # Get attribute
    db_attribute = db.query(ProductAttribute).filter(
        ProductAttribute.id == attribute_id,
        ProductAttribute.product_id == product_id
    ).first()
    if db_attribute is None:
        raise HTTPException(status_code=404, detail="Attribute not found")

    # Delete attribute
    db.delete(db_attribute)
    db.commit()

    return {"message": "Attribute deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)