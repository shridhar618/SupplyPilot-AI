"""
Promotion & Pricing Service for SupplyPilot AI
Handles promotion management, price optimization, discount calculations, etc.
"""
import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import uuid
import numpy as np
import pandas as pd
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Text, Integer, ForeignKey, Numeric, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pydantic import BaseModel, Field
import warnings
warnings.filterwarnings("ignore")

# Initialize FastAPI app
app = FastAPI(
    title="Promotion & Pricing Service",
    description="Service for managing promotions, pricing, and discount optimization",
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
class Product(Base):
    __tablename__ = "products"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)

class Promotion(Base):
    __tablename__ = "promotions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    promotion_type = Column(String(50), nullable=True)  # discount, bogo, coupon, etc.
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    discount_type = Column(String(20), nullable=True)  # percentage, fixed_amount, etc.
    discount_value = Column(Numeric(precision=5, scale=2), nullable=True)
    max_uses_per_customer = Column(Integer, nullable=True)
    total_uses_limit = Column(Integer, nullable=True)
    current_uses = Column(Integer, default=0)
    target_products = Column(JSONB, nullable=True)  # List of product IDs
    target_locations = Column(JSONB, nullable=True)  # List of location IDs
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class PriceHistory(Base):
    __tablename__ = "price_history"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    effective_date = Column(DateTime, nullable=False)
    price = Column(Numeric(precision=10, scale=2), nullable=False)
    currency = Column(String(3), default='USD')
    price_type = Column(String(20), nullable=True)  # regular, promotion, clearance, etc.
    promotion_id = Column(UUID(as_uuid=True), ForeignKey("promotions.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

# Relationships
Product.price_history = relationship("PriceHistory", backref="product")
Promotion.price_history = relationship("PriceHistory", backref="promotion")

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic Models
class PromotionBase(BaseModel):
    name: str
    description: Optional[str] = None
    promotion_type: str
    start_date: datetime
    end_date: datetime
    discount_type: str
    discount_value: float
    max_uses_per_customer: Optional[int] = None
    total_uses_limit: Optional[int] = None
    target_products: List[str] = []
    target_locations: List[str] = []
    is_active: bool = True

class PromotionCreate(PromotionBase):
    pass

class PromotionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    promotion_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    max_uses_per_customer: Optional[int] = None
    total_uses_limit: Optional[int] = None
    target_products: Optional[List[str]] = None
    target_locations: Optional[List[str]] = None
    is_active: Optional[bool] = None

class PromotionResponse(PromotionBase):
    id: str
    current_uses: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class PriceHistoryBase(BaseModel):
    product_id: str
    effective_date: datetime
    price: float
    currency: str = "USD"
    price_type: str
    promotion_id: Optional[str] = None

class PriceHistoryCreate(PriceHistoryBase):
    pass

class PriceHistoryResponse(PriceHistoryBase):
    id: str
    created_at: datetime

    class Config:
        orm_mode = True

class PromotionEffectivenessRequest(BaseModel):
    promotion_id: str
    start_date: datetime
    end_date: datetime

class PromotionEffectivenessResponse(BaseModel):
    promotion_id: str
    promotion_name: str
    total_sales: float
    total_units_sold: int
    incremental_sales: float
    incremental_units: int
    roi: float
    redemption_rate: float

class PriceOptimizationRequest(BaseModel):
    product_ids: List[str]
    location_ids: List[str]
    objective: str = "maximize_profit"  # or maximize_revenue, maximize_volume
    competitor_prices: Dict[str, float] = {}  # product_id -> price
    price_elasticity: float = -1.5  # Default elasticity
    current_price: float
    cost: float
    min_price: float
    max_price: float

class PriceOptimizationResponse(BaseModel):
    product_id: str
    location_id: Optional[str]
    optimal_price: float
    expected_profit: float
    expected_revenue: float
    expected_volume: float
    confidence: float

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
        "service": "Promotion & Pricing Service",
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

@app.post("/promotions", response_model=PromotionResponse)
async def create_promotion(
    promotion: PromotionCreate,
    db: Session = Depends(get_db)
):
    """Create a new promotion"""
    # Check if promotion with same name and date range exists (optional)
    db_promotion = Promotion(**promotion.dict())
    db.add(db_promotion)
    db.commit()
    db.refresh(db_promotion)
    return db_promotion

@app.get("/promotions", response_model=List[PromotionResponse])
async def get_promotions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None),
    promotion_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get promotions with filtering"""
    query = db.query(Promotion)

    if is_active is not None:
        query = query.filter(Promotion.is_active == is_active)
    if promotion_type:
        query = query.filter(Promotion.promotion_type == promotion_type)

    total = query.count()
    promotions = query.offset(skip).limit(limit).all()
    return promotions

@app.get("/promotions/{promotion_id}", response_model=PromotionResponse)
async def get_promotion(
    promotion_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific promotion by ID"""
    promotion = db.query(Promotion).filter(Promotion.id == promotion_id).first()
    if promotion is None:
        raise HTTPException(status_code=404, detail="Promotion not found")
    return promotion

@app.put("/promotions/{promotion_id}", response_model=PromotionResponse)
async def update_promotion(
    promotion_id: str,
    promotion_update: PromotionUpdate,
    db: Session = Depends(get_db)
):
    """Update a promotion"""
    db_promotion = db.query(Promotion).filter(Promotion.id == promotion_id).first()
    if db_promotion is None:
        raise HTTPException(status_code=404, detail="Promotion not found")

    update_data = promotion_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_promotion, key, value)

    db_promotion.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_promotion)
    return db_promotion

@app.delete("/promotions/{promotion_id}")
async def delete_promotion(
    promotion_id: str,
    db: Session = Depends(get_db)
):
    """Delete a promotion"""
    db_promotion = db.query(Promotion).filter(Promotion.id == promotion_id).first()
    if db_promotion is None:
        raise HTTPException(status_code=404, detail="Promotion not found")

    db.delete(db_promotion)
    db.commit()
    return {"message": "Promotion deleted successfully"}

@app.post("/promotions/{promotion_id}/use")
async def use_promotion(
    promotion_id: str,
    db: Session = Depends(get_db)
):
    """Record usage of a promotion"""
    db_promotion = db.query(Promotion).filter(Promotion.id == promotion_id).first()
    if db_promotion is None:
        raise HTTPException(status_code=404, detail="Promotion not found")

    # Check if promotion is still valid
    now = datetime.utcnow()
    if db_promotion.start_date > now or db_promotion.end_date < now:
        raise HTTPException(status_code=400, detail="Promotion is not active")

    # Check usage limits
    if db_promotion.total_uses_limit and db_promotion.current_uses >= db_promotion.total_uses_limit:
        raise HTTPException(status_code=400, detail="Promotion usage limit exceeded")

    # Increment usage count
    db_promotion.current_uses += 1
    db.commit()
    return {"message": "Promotion usage recorded", "remaining_uses": db_promotion.total_uses_limit - db_promotion.current_uses if db_promotion.total_uses_limit else None}

@app.post("/price-history", response_model=PriceHistoryResponse)
async def create_price_history(
    price_history: PriceHistoryCreate,
    db: Session = Depends(get_db)
):
    """Create a new price history record"""
    # Check if price history for this product and date already exists (optional)
    db_price = PriceHistory(**price_history.dict())
    db.add(db_price)
    db.commit()
    db.refresh(db_price)
    return db_price

@app.get("/price-history", response_model=List[PriceHistoryResponse])
async def get_price_history(
    product_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    price_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get price history with filtering"""
    query = db.query(PriceHistory)

    if product_id:
        query = query.filter(PriceHistory.product_id == product_id)
    if start_date:
        query = query.filter(PriceHistory.effective_date >= start_date)
    if end_date:
        query = query.filter(PriceHistory.effective_date <= end_date)
    if price_type:
        query = query.filter(PriceHistory.price_type == price_type)

    total = query.count()
    price_history = query.order_by(PriceHistory.effective_date.desc()).offset(skip).limit(limit).all()
    return price_history

@app.post("/promotions/effectiveness", response_model=PromotionEffectivenessResponse)
async def calculate_promotion_effectiveness(
    request: PromotionEffectivenessRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate the effectiveness of a promotion
    In a real implementation, this would compare sales during promotion to baseline sales
    """
    # Get the promotion
    promotion = db.query(Promotion).filter(Promotion.id == request.promotion_id).first()
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found")

    # In a real implementation, we would:
    # 1. Get sales data for the promotion period
    # 2. Get sales data for a similar period before/after the promotion (control group)
    # 3. Calculate incremental sales and units
    # 4. Calculate ROI and redemption rate

    # For now, we'll return mock data
    total_sales = np.random.uniform(1000, 10000)
    total_units_sold = np.random.randint(50, 500)
    incremental_sales = np.random.uniform(200, 2000)
    incremental_units = np.random.randint(10, 100)
    roi = incremental_sales / (total_sales * 0.1)  # Assuming 10% of sales is promotion cost
    redemption_rate = min(0.95, incremental_units / total_units_sold) if total_units_sold > 0 else 0

    return PromotionEffectivenessResponse(
        promotion_id=promotion.id,
        promotion_name=promotion.name,
        total_sales=total_sales,
        total_units_sold=total_units_sold,
        incremental_sales=incremental_sales,
        incremental_units=incremental_units,
        roi=roi,
        redemption_rate=redemption_rate
    )

@app.post("/price/optimize", response_model=List[PriceOptimizationResponse])
async def optimize_prices(
    request: PriceOptimizationRequest,
    db: Session = Depends(get_db)
):
    """
    Optimize prices for products based on objective, elasticity, constraints, etc.
    """
    optimizations = []

    for product_id in request.product_ids:
        # Get product info
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            continue

        # For each location (if specified) or just product level
        location_ids = request.location_ids if request.location_ids else [None]

        for location_id in location_ids:
            # In a real implementation, we would:
            # 1. Get current price and cost
            # 2. Get competitor prices for this product/location
            # 3. Get price elasticity of demand (could be estimated or stored)
            # 4. Define objective function (profit, revenue, volume, market share)
            # 5. Use optimization algorithm to find optimal price within min/max constraints

            # For now, we'll use a simple profit maximization model assuming linear demand
            # Profit = (Price - Cost) * Quantity
            # Quantity = a - b * Price (linear demand curve)
            # We can estimate a and b from current price, elasticity, and quantity

            # Mock data for demonstration
            current_price = request.current_price or 50.0
            cost = request.cost or 30.0
            elasticity = request.price_elasticity or -1.5
            min_price = request.min_price or cost * 1.1  # At least 10% above cost
            max_price = request.max_price or current_price * 2.0  # Up to double current price

            # Calculate demand intercept and slope from elasticity at current price
            # Elasticity = (% change in quantity) / (% change in price)
            # For linear demand: Q = a - b*P
            # Elasticity at price P: (dQ/dP) * (P/Q) = -b * (P/Q)
            # So b = -elasticity * (Q/P)
            # We need Q at current price to calculate b
            # Let's assume we know the current quantity sold per month at current price
            current_monthly_quantity = 100.0  # units

            # Calculate slope b
            b = -elasticity * (current_monthly_quantity / current_price)
            # Calculate intercept a: Q = a - b*P => a = Q + b*P
            a = current_monthly_quantity + b * current_price

            # Profit function: Profit = (P - Cost) * (a - b*P)
            # To maximize profit, take derivative and set to zero:
            # d(Profit)/dP = (a - b*P) - b*(P - Cost) = a - b*P - b*P + b*Cost = a - 2*b*P + b*Cost = 0
            # => 2*b*P = a + b*Cost
            # => P = (a + b*Cost) / (2*b)

            optimal_price = (a + b * cost) / (2 * b) if b != 0 else current_price

            # Ensure optimal price is within bounds
            optimal_price = max(min_price, min(max_price, optimal_price))

            # Calculate expected values at optimal price
            expected_quantity = a - b * optimal_price
            expected_quantity = max(0, expected_quantity)  # Quantity can't be negative
            expected_revenue = optimal_price * expected_quantity
            expected_profit = (optimal_price - cost) * expected_quantity

            # Calculate confidence (mock)
            confidence = 0.85  # 85% confidence

            optimizations.append(PriceOptimizationResponse(
                product_id=product_id,
                location_id=location_id,
                optimal_price=optimal_price,
                expected_profit=expected_profit,
                expected_revenue=expected_revenue,
                expected_volume=expected_quantity,
                confidence=confidence
            ))

    return optimizations

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)