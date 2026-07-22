"""
Inventory Optimization Service for SupplyPilot AI
Handles inventory optimization, reorder points, safety stock calculations
"""
import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import uuid
from enum import Enum as PyEnum

from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Text, Integer, Numeric, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pydantic import BaseModel as PydanticBaseModel, Field
import warnings
warnings.filterwarnings("ignore")

# Initialize FastAPI app
app = FastAPI(
    title="Inventory Optimization Service",
    description="Service for inventory optimization and replenishment planning",
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
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/supplypilot")

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Enums
class OptimizationStrategy(str, PyEnum):
    EOQ = "eoq"  # Economic Order Quantity
    MIN_MAX = "min_max"
    JIT = "jit"  # Just In Time
    SAFETY_STOCK = "safety_stock"

class ReorderStatus(str, PyEnum):
    BELOW_MIN = "below_min"
    ABOVE_MAX = "above_max"
    OPTIMAL = "optimal"
    REORDER_NEEDED = "reorder_needed"

# Database Models
class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku = Column(String(50), unique=True, nullable=False)
    product_id = Column(UUID(as_uuid=True), nullable=False)  # References products table
    location_id = Column(String(50), nullable=False)  # Warehouse/location identifier
    current_stock = Column(Integer, nullable=False, default=0)
    allocated_stock = Column(Integer, nullable=False, default=0)  # Allocated to orders
    available_stock = Column(Integer, nullable=False, default=0)  # Available for sale
    unit_cost = Column(Numeric(10, 2), nullable=False)
    lead_time_days = Column(Integer, nullable=False)
    safety_stock = Column(Integer, nullable=False, default=0)
    reorder_point = Column(Integer, nullable=False)
    max_stock_level = Column(Integer, nullable=False)
    economic_order_quantity = Column(Integer, nullable=False)
    holding_cost_rate = Column(Numeric(5, 4), nullable=False)  # Annual holding cost as % of unit cost
    ordering_cost = Column(Numeric(10, 2), nullable=False)  # Cost per order
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class ReorderRecommendation(Base):
    __tablename__ = "reorder_recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inventory_item_id = Column(UUID(as_uuid=True), ForeignKey("inventory_items.id"), nullable=False)
    recommended_quantity = Column(Integer, nullable=False)
    recommended_order_date = Column(DateTime, nullable=False)
    expected_delivery_date = Column(DateTime, nullable=False)
    total_cost = Column(Numeric(12, 2), nullable=False)
    stockout_risk = Column(Numeric(5, 4), nullable=False)  # Probability of stockout (0-1)
    strategy_used = Column(String(20), nullable=False)
    status = Column(String(20), default='pending')  # pending, approved, ordered, received, cancelled
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    inventory_item = relationship("InventoryItem")

class InventoryOptimization(Base):
    __tablename__ = "inventory_optimizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inventory_item_id = Column(UUID(as_uuid=True), ForeignKey("inventory_items.id"), nullable=False)
    optimization_date = Column(DateTime, nullable=False, server_default=func.now())
    current_stock = Column(Integer, nullable=False)
    projected_daily_demand = Column(Numeric(8, 4), nullable=False)
    lead_time_demand = Column(Numeric(8, 4), nullable=False)
    safety_stock_calculated = Column(Integer, nullable=False)
    reorder_point_calculated = Column(Integer, nullable=False)
    economic_order_quantity_calculated = Column(Integer, nullable=False)
    max_stock_level_calculated = Column(Integer, nullable=False)
    total_annual_cost = Column(Numeric(12, 2), nullable=False)
    optimization_notes = Column(Text, nullable=True)

    # Relationships
    inventory_item = relationship("InventoryItem")

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic Models
class InventoryItemBase(PydanticBaseModel):
    sku: str
    product_id: str
    location_id: str
    current_stock: int = 0
    allocated_stock: int = 0
    available_stock: int = 0
    unit_cost: float
    lead_time_days: int
    safety_stock: int = 0
    reorder_point: int
    max_stock_level: int
    economic_order_quantity: int
    holding_cost_rate: float
    ordering_cost: float
    is_active: bool = True

class InventoryItemCreate(InventoryItemBase):
    pass

class InventoryItemUpdate(PydanticBaseModel):
    current_stock: Optional[int] = None
    allocated_stock: Optional[int] = None
    available_stock: Optional[int] = None
    safety_stock: Optional[int] = None
    reorder_point: Optional[int] = None
    max_stock_level: Optional[int] = None
    economic_order_quantity: Optional[int] = None
    holding_cost_rate: Optional[float] = None
    ordering_cost: Optional[float] = None
    is_active: Optional[bool] = None

class InventoryItemResponse(InventoryItemBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ReorderRecommendationBase(PydanticBaseModel):
    inventory_item_id: str
    recommended_quantity: int
    recommended_order_date: datetime
    expected_delivery_date: datetime
    total_cost: float
    stockout_risk: float
    strategy_used: str
    status: str = 'pending'

class ReorderRecommendationCreate(ReorderRecommendationBase):
    pass

class ReorderRecommendationResponse(ReorderRecommendationBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class InventoryOptimizationBase(PydanticBaseModel):
    inventory_item_id: str
    optimization_date: datetime
    current_stock: int
    projected_daily_demand: float
    lead_time_demand: float
    safety_stock_calculated: int
    reorder_point_calculated: int
    economic_order_quantity_calculated: int
    max_stock_level_calculated: int
    total_annual_cost: float
    optimization_notes: Optional[str] = None

class InventoryOptimizationCreate(InventoryOptimizationBase):
    pass

class InventoryOptimizationResponse(InventoryOptimizationBase):
    id: str

    class Config:
        orm_mode = True

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper functions
def calculate_eoq(annual_demand: float, ordering_cost: float, holding_cost_rate: float, unit_cost: float) -> int:
    """Calculate Economic Order Quantity"""
    if annual_demand <= 0 or ordering_cost <= 0 or holding_cost_rate <= 0 or unit_cost <= 0:
        return 0
    import math
    eoq = math.sqrt((2 * annual_demand * ordering_cost) / (holding_cost_rate * unit_cost))
    return max(1, round(eoq))

def calculate_reorder_point(daily_demand: float, lead_time_days: int, safety_stock: int) -> int:
    """Calculate Reorder Point"""
    return max(0, round((daily_demand * lead_time_days) + safety_stock))

def calculate_max_stock(reorder_point: int, eoq: int) -> int:
    """Calculate Maximum Stock Level"""
    return reorder_point + eoq

# Routes
@app.get("/")
async def root():
    return {
        "service": "Inventory Optimization Service",
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

# Inventory Item Endpoints
@app.get("/inventory-items", response_model=List[InventoryItemResponse])
async def get_inventory_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    location_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """Get inventory items with filtering"""
    query = db.query(InventoryItem)

    if location_id is not None:
        query = query.filter(InventoryItem.location_id == location_id)
    if is_active is not None:
        query = query.filter(InventoryItem.is_active == is_active)

    items = query.offset(skip).limit(limit).all()
    return items

@app.post("/inventory-items", response_model=InventoryItemResponse)
async def create_inventory_item(
    item: InventoryItemCreate,
    db: Session = Depends(get_db)
):
    """Create a new inventory item"""
    # Calculate derived values if not provided
    item_dict = item.dict()
    
    # Calculate economic order quantity if not provided
    if item_dict.get('economic_order_quantity', 0) == 0:
        annual_demand = item_dict.get('current_stock', 0) * 12  # Simplified annual demand
        item_dict['economic_order_quantity'] = calculate_eoq(
            annual_demand,
            item_dict.get('ordering_cost', 0),
            item_dict.get('holding_cost_rate', 0),
            item_dict.get('unit_cost', 0)
        )
    
    # Calculate reorder point if not provided
    if item_dict.get('reorder_point', 0) == 0:
        item_dict['reorder_point'] = calculate_reorder_point(
            item_dict.get('current_stock', 0) / 30,  # Daily demand approximation
            item_dict.get('lead_time_days', 0),
            item_dict.get('safety_stock', 0)
        )
    
    # Calculate max stock level if not provided
    if item_dict.get('max_stock_level', 0) == 0:
        item_dict['max_stock_level'] = calculate_max_stock(
            item_dict.get('reorder_point', 0),
            item_dict.get('economic_order_quantity', 0)
        )
    
    # Calculate available stock
    item_dict['available_stock'] = max(0, item_dict.get('current_stock', 0) - item_dict.get('allocated_stock', 0))
    
    db_item = InventoryItem(**item_dict)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/inventory-items/{item_id}", response_model=InventoryItemResponse)
async def get_inventory_item(
    item_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific inventory item by ID"""
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return item

@app.put("/inventory-items/{item_id}", response_model=InventoryItemResponse)
async def update_inventory_item(
    item_id: str,
    item_update: InventoryItemUpdate,
    db: Session = Depends(get_db)
):
    """Update an inventory item"""
    db_item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    update_data = item_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
    
    # Recalculate derived values if needed
    if 'current_stock' in update_data or 'allocated_stock' in update_data:
        db_item.available_stock = max(0, db_item.current_stock - db_item.allocated_stock)
    
    db_item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_item)
    return db_item

# Reorder Recommendation Endpoints
@app.get("/reorder-recommendations", response_model=List[ReorderRecommendationResponse])
async def get_reorder_recommendations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    inventory_item_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get reorder recommendations with filtering"""
    query = db.query(ReorderRecommendation)

    if inventory_item_id:
        query = query.filter(ReorderRecommendation.inventory_item_id == inventory_item_id)
    if status:
        query = query.filter(ReorderRecommendation.status == status)

    recommendations = query.order_by(ReorderRecommendation.created_at.desc()).offset(skip).limit(limit).all()
    return recommendations

@app.post("/reorder-recommendations", response_model=ReorderRecommendationResponse)
async def create_reorder_recommendation(
    recommendation: ReorderRecommendationCreate,
    db: Session = Depends(get_db)
):
    """Create a new reorder recommendation"""
    # Verify that the inventory item exists
    item = db.query(InventoryItem).filter(InventoryItem.id == recommendation.inventory_item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    db_recommendation = ReorderRecommendation(**recommendation.dict())
    db.add(db_recommendation)
    db.commit()
    db.refresh(db_recommendation)
    return db_recommendation

@app.post("/reorder-recommendations/{recommendation_id}/approve")
async def approve_reorder_recommendation(
    recommendation_id: str,
    db: Session = Depends(get_db)
):
    """Approve a reorder recommendation"""
    recommendation = db.query(ReorderRecommendation).filter(ReorderRecommendation.id == recommendation_id).first()
    if recommendation is None:
        raise HTTPException(status_code=404, detail="Reorder recommendation not found")

    recommendation.status = 'approved'
    db.commit()

    return {"message": "Reorder recommendation approved"}

@app.post("/reorder-recommendations/{recommendation_id}/order")
async def order_reorder_recommendation(
    recommendation_id: str,
    db: Session = Depends(get_db)
):
    """Mark a reorder recommendation as ordered"""
    recommendation = db.query(ReorderRecommendation).filter(ReorderRecommendation.id == recommendation_id).first()
    if recommendation is None:
        raise HTTPException(status_code=404, detail="Reorder recommendation not found")

    recommendation.status = 'ordered'
    db.commit()

    return {"message": "Reorder recommendation marked as ordered"}

# Inventory Optimization Endpoints
@app.get("/optimizations", response_model=List[InventoryOptimizationResponse])
async def get_inventory_optimizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    inventory_item_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get inventory optimizations with filtering"""
    query = db.query(InventoryOptimization)

    if inventory_item_id:
        query = query.filter(InventoryOptimization.inventory_item_id == inventory_item_id)

    optimizations = query.order_by(InventoryOptimization.optimization_date.desc()).offset(skip).limit(limit).all()
    return optimizations

@app.post("/optimizations", response_model=InventoryOptimizationResponse)
async def create_inventory_optimization(
    optimization: InventoryOptimizationCreate,
    db: Session = Depends(get_db)
):
    """Create a new inventory optimization record"""
    # Verify that the inventory item exists
    item = db.query(InventoryItem).filter(InventoryItem.id == optimization.inventory_item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    db_optimization = InventoryOptimization(**optimization.dict())
    db.add(db_optimization)
    db.commit()
    db.refresh(db_optimization)
    return db_optimization

# Dashboard Endpoints
@app.get("/dashboard/inventory-manager")
async def get_inventory_manager_dashboard(
    db: Session = Depends(get_db)
):
    """Get data for inventory manager dashboard"""
    # Get low stock items (below reorder point)
    low_stock_items = db.query(InventoryItem).filter(
        InventoryItem.available_stock <= InventoryItem.reorder_point,
        InventoryItem.is_active == True
    ).count()
    
    # Get overstock items (above max stock)
    overstock_items = db.query(InventoryItem).filter(
        InventoryItem.available_stock >= InventoryItem.max_stock_level,
        InventoryItem.is_active == True
    ).count()
    
    # Get pending recommendations
    pending_recommendations = db.query(ReorderRecommendation).filter(
        ReorderRecommendation.status == 'pending'
    ).count()
    
    # Get total inventory value
    total_inventory_value = db.query(
        func.sum(InventoryItem.available_stock * InventoryItem.unit_cost)
    ).filter(InventoryItem.is_active == True).scalar() or 0
    
    return {
        "low_stock_items": low_stock_items,
        "overstock_items": overstock_items,
        "pending_recommendations": pending_recommendations,
        "total_inventory_value": round(float(total_inventory_value), 2),
        "inventory_turnover": 8.5,  # Placeholder - would be calculated from sales data
        "stockout_incidents": 2,    # Placeholder - would be calculated from historical data
        "recent_recommendations": [
            {
                "id": "rec-001",
                "sku": "SKU-001",
                "recommended_quantity": 100,
                "total_cost": 2500.00,
                "created_at": (datetime.utcnow() - timedelta(hours=2)).isoformat()
            },
            {
                "id": "rec-002", 
                "sku": "SKU-002",
                "recommended_quantity": 50,
                "total_cost": 1200.00,
                "created_at": (datetime.utcnow() - timedelta(hours=5)).isoformat()
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
