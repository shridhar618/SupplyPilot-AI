"""
Supply Chain Resilience Service for SupplyPilot AI
Handles supplier management, purchase orders, risk assessment, and supply chain monitoring
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
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Text, Integer, ForeignKey, Numeric, func, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pydantic import BaseModel, Field, validator
import warnings
warnings.filterwarnings("ignore")

# Initialize FastAPI app
app = FastAPI(
    title="Supply Chain Resilience Service",
    description="Service for managing suppliers, purchase orders, and supply chain risk",
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
class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_code = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    contact_person = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    city = String(100)
    state_province = String(100)
    country = String(100)
    postal_code = String(20)
    lead_time_days = Integer()
    reliability_score = Numeric(precision=3, scale=2)  # 0.00 to 1.00
    quality_score = Numeric(precision=3, scale=2)
    on_time_delivery_rate = Numeric(precision=3, scale=2)
    risk_score = Numeric(precision=3, scale=2)  # 0.00 to 1.00 (lower is better)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")
    performance_records = relationship("SupplierPerformance", back_populates="supplier")

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_number = Column(String(50), unique=True, nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=True)
    location_id = Column(UUID(as_uuid=True), nullable=True)  # References inventory_locations
    order_date = Column(DateTime, nullable=False)
    expected_delivery_date = Column(DateTime, nullable=True)
    actual_delivery_date = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=True)  # draft, sent, acknowledged, partially_received, received, cancelled, delayed
    total_amount = Column(Numeric(precision=12, scale=2), nullable=False)
    currency = Column(String(3), default='USD')
    notes = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=True)  # References users
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    supplier = relationship("Supplier", back_populates="purchase_orders")
    items = relationship("PurchaseOrderItem", back_populates="po", cascade="all, delete-orphan")

class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), nullable=False)  # References products
    quantity_ordered = Column(Integer, nullable=False)
    quantity_received = Column(Integer, default=0)
    unit_price = Column(Numeric(precision=10, scale=2), nullable=False)
    line_total = Column(Numeric(precision=12, scale=2), nullable=False)
    received_date = Column(DateTime, nullable=True)

    # Relationships
    po = relationship("PurchaseOrder", back_populates="items")

class SupplierPerformance(Base):
    __tablename__ = "supplier_performance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    evaluation_period_start = Column(DateTime, nullable=False)
    evaluation_period_end = Column(DateTime, nullable=False)
    on_time_delivery_rate = Numeric(precision=3, scale=2)
    quality_defect_rate = Numeric(precision=3, scale=2)
    average_lead_time = Numeric(precision=5, scale=2)
    total_spend = Numeric(precision=12, scale=2)
    order_count = Integer()
    risk_score = Numeric(precision=3, scale=2)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    supplier = relationship("Supplier", back_populates="performance_records")

class SupplyChainRisk(Base):
    __tablename__ = "supply_chain_risks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    risk_id = Column(String(50), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    risk_type = Column(String(50), nullable=True)  # supplier, geopolitical, natural_disaster, economic, etc.
    severity = Column(String(20), nullable=True)  # low, medium, high, critical
    probability = Column(Numeric(precision=3, scale=2))  # 0.00 to 1.00
    impact_score = Column(Numeric(precision=3, scale=2))  # 0.00 to 1.00
    risk_score = Column(Numeric(precision=3, scale=2))  # probability * impact
    affected_suppliers = Column(JSONB, nullable=True)  # List of supplier IDs
    affected_materials = Column(JSONB, nullable=True)  # List of material/product IDs
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    mitigation_plan = Column(Text, nullable=True)
    status = Column(String(20), default='active')  # active, mitigated, resolved, monitored
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic Models
class SupplierBase(BaseModel):
    supplier_code: str
    name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    lead_time_days: Optional[int] = None
    reliability_score: Optional[float] = None
    quality_score: Optional[float] = None
    on_time_delivery_rate: Optional[float] = None
    risk_score: Optional[float] = None
    is_active: bool = True

class SupplierCreate(SupplierBase):
    @validator('reliability_score', 'quality_score', 'on_time_delivery_rate', 'risk_score')
    def validate_scores(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError('Score must be between 0 and 1')
        return v

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    lead_time_days: Optional[int] = None
    reliability_score: Optional[float] = None
    quality_score: Optional[float] = None
    on_time_delivery_rate: Optional[float] = None
    risk_score: Optional[float] = None
    is_active: Optional[bool] = None

    @validator('reliability_score', 'quality_score', 'on_time_delivery_rate', 'risk_score')
    def validate_scores(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError('Score must be between 0 and 1')
        return v

class SupplierResponse(SupplierBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class PurchaseOrderBase(BaseModel):
    po_number: str
    supplier_id: Optional[str] = None
    location_id: Optional[str] = None
    order_date: datetime
    expected_delivery_date: Optional[datetime] = None
    status: str = "draft"
    total_amount: float
    currency: str = "USD"
    notes: Optional[str] = None
    created_by: Optional[str] = None

class PurchaseOrderCreate(PurchaseOrderBase):
    pass

class PurchaseOrderUpdate(BaseModel):
    po_number: Optional[str] = None
    supplier_id: Optional[str] = None
    location_id: Optional[str] = None
    order_date: Optional[datetime] = None
    expected_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    status: Optional[str] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = None
    notes: Optional[str] = None
    created_by: Optional[str] = None

class PurchaseOrderResponse(PurchaseOrderBase):
    id: str
    actual_delivery_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class PurchaseOrderItemBase(BaseModel):
    product_id: str
    quantity_ordered: int
    quantity_received: int = 0
    unit_price: float
    line_total: float
    received_date: Optional[datetime] = None

class PurchaseOrderItemCreate(PurchaseOrderItemBase):
    pass

class PurchaseOrderItemResponse(PurchaseOrderItemBase):
    id: str
    po_id: str

    class Config:
        orm_mode = True

class SupplierPerformanceBase(BaseModel):
    supplier_id: str
    evaluation_period_start: datetime
    evaluation_period_end: datetime
    on_time_delivery_rate: float
    quality_defect_rate: float
    average_lead_time: float
    total_spend: float
    order_count: int
    risk_score: float

class SupplierPerformanceCreate(SupplierPerformanceBase):
    @validator('on_time_delivery_rate', 'quality_defect_rate', 'risk_score')
    def validate_rates(cls, v):
        if v < 0 or v > 1:
            raise ValueError('Rate must be between 0 and 1')
        return v

class SupplierPerformanceResponse(SupplierPerformanceBase):
    id: str
    created_at: datetime

    class Config:
        orm_mode = True

class SupplyChainRiskBase(BaseModel):
    risk_id: str
    title: str
    description: Optional[str] = None
    risk_type: Optional[str] = None
    severity: Optional[str] = None
    probability: float
    impact_score: float
    risk_score: float
    affected_suppliers: Optional[List[str]] = None
    affected_materials: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    mitigation_plan: Optional[str] = None
    status: str = "active"

class SupplyChainRiskCreate(SupplyChainRiskBase):
    @validator('probability', 'impact_score', 'risk_score')
    def validate_scores(cls, v):
        if v < 0 or v > 1:
            raise ValueError('Score must be between 0 and 1')
        return v

class SupplyChainRiskResponse(SupplyChainRiskBase):
    id: str
    created_at: datetime
    updated_at: datetime

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
        "service": "Supply Chain Resilience Service",
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

# Supplier Endpoints
@app.get("/suppliers", response_model=List[SupplierResponse])
async def get_suppliers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None),
    country: Optional[str] = Query(None),
    min_reliability_score: Optional[float] = Query(None),
    db: Session = Depends(get_db)
):
    """Get suppliers with filtering"""
    query = db.query(Supplier)

    if is_active is not None:
        query = query.filter(Supplier.is_active == is_active)
    if country:
        query = query.filter(Supplier.country == country)
    if min_reliability_score is not None:
        query = query.filter(Supplier.reliability_score >= min_reliability_score)

    total = query.count()
    suppliers = query.offset(skip).limit(limit).all()
    return suppliers

@app.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific supplier by ID"""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier

@app.post("/suppliers", response_model=SupplierResponse)
async def create_supplier(
    supplier: SupplierCreate,
    db: Session = Depends(get_db)
):
    """Create a new supplier"""
    # Check if supplier with same code already exists
    existing_supplier = db.query(Supplier).filter(Supplier.supplier_code == supplier.supplier_code).first()
    if existing_supplier:
        raise HTTPException(status_code=400, detail="Supplier with this code already exists")

    db_supplier = Supplier(**supplier.dict())
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier

@app.put("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: str,
    supplier_update: SupplierUpdate,
    db: Session = Depends(get_db)
):
    """Update a supplier"""
    db_supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if db_supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")

    update_data = supplier_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_supplier, key, value)

    db_supplier.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_supplier)
    return db_supplier

@app.delete("/suppliers/{supplier_id}")
async def delete_supplier(
    supplier_id: str,
    db: Session = Depends(get_db)
):
    """Delete a supplier (soft delete)"""
    db_supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if db_supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")

    # Soft delete - set inactive
    db_supplier.is_active = False
    db_supplier.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Supplier deactivated successfully"}

# Purchase Order Endpoints
@app.get("/purchase-orders", response_model=List[PurchaseOrderResponse])
async def get_purchase_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    supplier_id: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    order_date_from: Optional[datetime] = Query(None),
    order_date_to: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Get purchase orders with filtering"""
    query = db.query(PurchaseOrder)

    if supplier_id:
        query = query.filter(PurchaseOrder.supplier_id == supplier_id)
    if location_id:
        query = query.filter(PurchaseOrder.location_id == location_id)
    if status:
        query = query.filter(PurchaseOrder.status == status)
    if order_date_from:
        query = query.filter(PurchaseOrder.order_date >= order_date_from)
    if order_date_to:
        query = query.filter(PurchaseOrder.order_date <= order_date_to)

    total = query.count()
    purchase_orders = query.order_by(PurchaseOrder.order_date.desc()).offset(skip).limit(limit).all()
    return purchase_orders

@app.get("/purchase-orders/{po_id}", response_model=PurchaseOrderResponse)
async def get_purchase_order(
    po_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific purchase order by ID"""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if po is None:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po

@app.post("/purchase-orders", response_model=PurchaseOrderResponse)
async def create_purchase_order(
    po: PurchaseOrderCreate,
    db: Session = Depends(get_db)
):
    """Create a new purchase order"""
    # Check if PO number already exists
    existing_po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po.po_number).first()
    if existing_po:
        raise HTTPException(status_code=400, detail="Purchase order with this number already exists")

    db_po = PurchaseOrder(**po.dict())
    db.add(db_po)
    db.commit()
    db.refresh(db_po)
    return db_po

@app.put("/purchase-orders/{po_id}", response_model=PurchaseOrderResponse)
async def update_purchase_order(
    po_id: str,
    po_update: PurchaseOrderUpdate,
    db: Session = Depends(get_db)
):
    """Update a purchase order"""
    db_po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if db_po is None:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    update_data = po_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_po, key, value)

    db_po.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_po)
    return db_po

@app.post("/purchase-orders/{po_id}/receive")
async def receive_purchase_order(
    po_id: str,
    items: List[PurchaseOrderItemBase],
    db: Session = Depends(get_db)
):
    """Receive items for a purchase order"""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if po is None:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    # Update PO status if all items received
    all_received = True
    for item_data in items:
        # Find or create PO item
        po_item = db.query(PurchaseOrderItem).filter(
            PurchaseOrderItem.po_id == po_id,
            PurchaseOrderItem.product_id == item_data.product_id
        ).first()

        if not po_item:
            # Create new PO item
            po_item = PurchaseOrderItem(
                po_id=po_id,
                product_id=item_data.product_id,
                quantity_ordered=item_data.quantity_ordered,
                quantity_received=item_data.quantity_received,
                unit_price=item_data.unit_price,
                line_total=item_data.line_total,
                received_date=item_data.received_date
            )
            db.add(po_item)
        else:
            # Update existing PO item
            po_item.quantity_received = item_data.quantity_received
            po_item.received_date = item_data.received_date
            if po_item.quantity_received < po_item.quantity_ordered:
                all_received = False

    # Update PO status
    if all_received:
        po.status = "received"
        po.actual_delivery_date = datetime.utcnow()
    else:
        po.status = "partially_received"

    po.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Purchase order items received successfully"}

# Supplier Performance Endpoints
@app.get("/suppliers/{supplier_id}/performance", response_model=List[SupplierPerformanceResponse])
async def get_supplier_performance(
    supplier_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Get performance history for a supplier"""
    query = db.query(SupplierPerformance).filter(SupplierPerformance.supplier_id == supplier_id)

    if start_date:
        query = query.filter(SupplierPerformance.evaluation_period_start >= start_date)
    if end_date:
        query = query.filter(SupplierPerformance.evaluation_period_end <= end_date)

    performances = query.order_by(SupplierPerformance.evaluation_period_start.desc()).all()
    return performances

@app.post("/suppliers/performance", response_model=SupplierPerformanceResponse)
async def create_supplier_performance(
    performance: SupplierPerformanceCreate,
    db: Session = Depends(get_db)
):
    """Create a new supplier performance record"""
    # Verify supplier exists
    supplier = db.query(Supplier).filter(Supplier.id == performance.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    db_performance = SupplierPerformance(**performance.dict())
    db.add(db_performance)
    db.commit()
    db.refresh(db_performance)
    return db_performance

# Supply Chain Risk Endpoints
@app.get("/risks", response_model=List[SupplyChainRiskResponse])
async def get_supply_chain_risks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    risk_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get supply chain risks with filtering"""
    query = db.query(SupplyChainRisk)

    if risk_type:
        query = query.filter(SupplyChainRisk.risk_type == risk_type)
    if severity:
        query = query.filter(SupplyChainRisk.severity == severity)
    if status:
        query = query.filter(SupplyChainRisk.status == status)

    total = query.count()
    risks = query.offset(skip).limit(limit).all()
    return risks

@app.get("/risks/{risk_id}", response_model=SupplyChainRiskResponse)
async def get_supply_chain_risk(
    risk_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific supply chain risk by ID"""
    risk = db.query(SupplyChainRisk).filter(SupplyChainRisk.id == risk_id).first()
    if risk is None:
        raise HTTPException(status_code=404, detail="Supply chain risk not found")
    return risk

@app.post("/risks", response_model=SupplyChainRiskResponse)
async def create_supply_chain_risk(
    risk: SupplyChainRiskCreate,
    db: Session = Depends(get_db)
):
    """Create a new supply chain risk"""
    # Check if risk with same ID already exists
    existing_risk = db.query(SupplyChainRisk).filter(SupplyChainRisk.risk_id == risk.risk_id).first()
    if existing_risk:
        raise HTTPException(status_code=400, detail="Risk with this ID already exists")

    db_risk = SupplyChainRisk(**risk.dict())
    db.add(db_risk)
    db.commit()
    db.refresh(db_risk)
    return db_risk

@app.put("/risks/{risk_id}", response_model=SupplyChainRiskResponse)
async def update_supply_chain_risk(
    risk_id: str,
    risk_update: SupplyChainRiskBase,
    db: Session = Depends(get_db)
):
    """Update a supply chain risk"""
    db_risk = db.query(SupplyChainRisk).filter(SupplyChainRisk.id == risk_id).first()
    if db_risk is None:
        raise HTTPException(status_code=404, detail="Supply chain risk not found")

    update_data = risk_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_risk, key, value)

    db_risk.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_risk)
    return db_risk

# Analytics and Reporting Endpoints
@app.get("/analytics/supplier-performance-summary")
async def get_supplier_performance_summary(
    db: Session = Depends(get_db)
):
    """Get summary of supplier performance metrics"""
    # Get average scores across all active suppliers
    suppliers = db.query(Supplier).filter(Supplier.is_active == True).all()

    if not suppliers:
        return {
            "total_suppliers": 0,
            "avg_reliability_score": 0,
            "avg_quality_score": 0,
            "avg_on_time_delivery_rate": 0,
            "avg_risk_score": 0
        }

    total_suppliers = len(suppliers)
    avg_reliability = sum(float(s.reliability_score or 0) for s in suppliers) / total_suppliers
    avg_quality = sum(float(s.quality_score or 0) for s in suppliers) / total_suppliers
    avg_otd = sum(float(s.on_time_delivery_rate or 0) for s in suppliers) / total_suppliers
    avg_risk = sum(float(s.risk_score or 0) for s in suppliers) / total_suppliers

    return {
        "total_suppliers": total_suppliers,
        "avg_reliability_score": round(avg_reliability, 3),
        "avg_quality_score": round(avg_quality, 3),
        "avg_on_time_delivery_rate": round(avg_otd, 3),
        "avg_risk_score": round(avg_risk, 3)
    }

@app.get("/analytics/purchase-order-stats")
async def get_purchase_order_stats(
    days: int = Query(30, ge=1),
    db: Session = Depends(get_db)
):
    """Get purchase order statistics for the last N days"""
    from_date = datetime.utcnow() - timedelta(days=days)

    # Get POs from the last N days
    pos = db.query(PurchaseOrder).filter(PurchaseOrder.order_date >= from_date).all()

    total_pos = len(pos)
    pending_pos = len([po for po in pos if po.status in ["draft", "sent", "acknowledged", "partially_received"]])
    completed_pos = len([po for po in pos if po.status == "received"])
    cancelled_pos = len([po for po in pos if po.status == "cancelled"])
    delayed_pos = len([po for po in pos if po.status == "delayed"])

    # Calculate on-time delivery rate for completed POs with actual delivery date
    completed_with_delivery = [po for po in pos if po.status == "received" and po.actual_delivery_date and po.expected_delivery_date]
    on_time_deliveries = len([po for po in completed_with_delivery
                             if po.actual_delivery_date <= po.expected_delivery_date])
    on_time_rate = (on_time_deliveries / len(completed_with_delivery) * 100) if completed_with_delivery else 0

    # Calculate total value
    total_value = sum(float(po.total_amount) for po in pos)

    return {
        "period_days": days,
        "total_purchase_orders": total_pos,
        "pending_orders": pending_pos,
        "completed_orders": completed_pos,
        "cancelled_orders": cancelled_pos,
        "delayed_orders": delayed_pos,
        "on_time_delivery_rate": round(on_time_rate, 2),
        "total_value": round(total_value, 2)
    }

# Alerts and Notifications (placeholder for integration with alerting system)
@app.get("/alerts/supply-chain")
async def get_supply_chain_alerts(
    db: Session = Depends(get_db)
):
    """Get supply chain alerts based on risk scores and performance metrics"""
    alerts = []

    # Check for high-risk suppliers
    high_risk_suppliers = db.query(Supplier).filter(
        Supplier.is_active == True,
        Supplier.risk_score > 0.7
    ).all()

    for supplier in high_risk_suppliers:
        alerts.append({
            "id": str(uuid.uuid4()),
            "type": "high_risk_supplier",
            "severity": "high",
            "title": f"High Risk Supplier: {supplier.name}",
            "description": f"Supplier {supplier.name} has a risk score of {supplier.risk_score:.2f} which exceeds the threshold of 0.7",
            "supplier_id": str(supplier.id),
            "supplier_name": supplier.name,
            "timestamp": datetime.utcnow().isoformat()
        })

    # Check for suppliers with declining performance
    # In a real implementation, we would compare recent performance to historical averages
    # For now, we'll skip this to keep it simple

    # Check for active supply chain risks
    active_risks = db.query(SupplyChainRisk).filter(
        SupplyChainRisk.status == "active",
        SupplyChainRisk.risk_score > 0.5
    ).all()

    for risk in active_risks:
        alerts.append({
            "id": str(uuid.uuid4()),
            "type": "supply_chain_risk",
            "severity": "high" if risk.risk_score > 0.7 else "medium",
            "title": f"Active Supply Chain Risk: {risk.title}",
            "description": risk.description or f"Risk {risk.risk_id} has a score of {risk.risk_score:.2f}",
            "risk_id": str(risk.id),
            "risk_title": risk.title,
            "timestamp": datetime.utcnow().isoformat()
        })

    return alerts

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)