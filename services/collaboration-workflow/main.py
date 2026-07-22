"""
Collaboration & Workflow Service for SupplyPilot AI
Handles collaborative forecasting, approval workflows, notifications, and role-based dashboards
"""
import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import uuid
import json
from enum import Enum as PyEnum

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Text, Integer, ForeignKey, Numeric, func, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from pydantic import BaseModel as PydanticBaseModel, Field, validator
import warnings
warnings.filterwarnings("ignore")

# Initialize FastAPI app
app = FastAPI(
    title="Collaboration & Workflow Service",
    description="Service for collaborative forecasting, approval workflows, and notifications",
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

# Enums
class WorkflowStatus(str, PyEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"

class NotificationType(str, PyEnum):
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"
    PUSH = "push"

class AlertSeverity(str, PyEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ApprovalStatus(str, PyEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

# Database Models
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    role = Column(String(50), nullable=True)
    department = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class ForecastCollaboration(Base):
    __tablename__ = "forecast_collaborations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    forecast_id = Column(UUID(as_uuid=True), nullable=False)  # References demand_forecasts.forecast_id
    version = Column(Integer, nullable=False, default=1)
    collaborator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    comments = Column(Text, nullable=True)
    adjustments = Column(JSONB, nullable=True)  # Store adjustments made by collaborator
    status = Column(SQLEnum(WorkflowStatus), default=WorkflowStatus.DRAFT)
    submitted_at = Column(DateTime, nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    collaborator = relationship("User", foreign_keys=[collaborator_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    approver = relationship("User", foreign_keys=[approved_by])

class ApprovalWorkflow(Base):
    __tablename__ = "approval_workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    entity_type = Column(String(50), nullable=False)  # forecast, inventory, promotion, etc.
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    current_step = Column(Integer, default=1)
    total_steps = Column(Integer, default=1)
    status = Column(SQLEnum(WorkflowStatus), default=WorkflowStatus.DRAFT)
    initiated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    initiator = relationship("User", foreign_keys=[initiated_by])
    steps = relationship("ApprovalStep", back_populates="workflow", cascade="all, delete-orphan")

class ApprovalStep(Base):
    __tablename__ = "approval_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("approval_workflows.id"), nullable=False)
    step_number = Column(Integer, nullable=False)
    approver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(SQLEnum(ApprovalStatus), default=ApprovalStatus.PENDING)
    comments = Column(Text, nullable=True)
    actioned_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    workflow = relationship("ApprovalWorkflow", back_populates="steps")
    approver = relationship("User", foreign_keys=[approver_id])

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    subject = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    related_entity_type = Column(String(50), nullable=True)  # forecast, po, etc.
    related_entity_id = Column(UUID(as_uuid=True), nullable=True)
    sent_at = Column(DateTime, server_default=func.now())
    read_at = Column(DateTime, nullable=True)

    # Relationships
    recipient = relationship("User", foreign_keys=[recipient_id])
    sender = relationship("User", foreign_keys=[sender_id])

class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    condition_json = Column(JSONB, nullable=False)  # Rule definition in JSON format
    severity = Column(SQLEnum(AlertSeverity), nullable=False)
    is_active = Column(Boolean, default=True)
    notification_channels = Column(ARRAY(String), nullable=True)  # ["email", "sms", "in_app"]
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("alert_rules.id"), nullable=True)
    triggered_at = Column(DateTime, nullable=False)
    entity_type = Column(String(50), nullable=False)  # product, inventory, forecast, etc.
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    severity = Column(SQLEnum(AlertSeverity), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default='active')  # active, acknowledged, resolved, dismissed
    acknowledged_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Relationships
    rule = relationship("AlertRule", foreign_keys=[rule_id])
    acknowledger = relationship("User", foreign_keys=[acknowledged_by])
    resolver = relationship("User", foreign_keys=[resolved_by])

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic obaseModel):
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    is_active: bool = True

class UserBase(UserBase):
    password_hash is not in the User model for Pydantic; we'll handle it separately
class UserBase(PydanticBaseModel):
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    # password will be handled by the auth service; we don't store it here directly
    pass

class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ForecastCollaborationBase(PydanticBaseModel):
    forecast_id: str
    version: int = 1
    collaborator_id: str
    comments: Optional[str] = None
    adjustments: Optional[Dict[str, Any]] = None
    status: WorkflowStatus = WorkflowStatus.DRAFT

class ForecastCollaborationCreate(ForecastCollaborationBase):
    pass

class ForecastCollaborationUpdate(PydanticBaseModel):
    comments: Optional[str] = None
    adjustments: Optional[Dict[str, Any]] = None
    status: Optional[WorkflowStatus] = None

class ForecastCollaborationResponse(ForecastCollaborationBase):
    id: str
    submitted_at: Optional[datetime]
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ApprovalWorkflowBase(PydanticBaseModel):
    workflow_name: str
    description: Optional[str] = None
    entity_type: str
    entity_id: str
    current_step: int = 1
    total_steps: int = 1
    status: WorkflowStatus = WorkflowStatus.DRAFT
    initiated_by: str

class ApprovalWorkflowCreate(ApprovalWorkflowBase):
    pass

class ApprovalWorkflowUpdate(PydanticBaseModel):
    workflow_name: Optional[str] = None
    description: Optional[str] = None
    current_step: Optional[int] = None
    total_steps: Optional[int] = None
    status: Optional[WorkflowStatus] = None

class ApprovalWorkflowResponse(ApprovalWorkflowBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ApprovalStepBase(PydanticBaseModel):
    workflow_id: str
    step_number: int
    approver_id: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    comments: Optional[str] = None

class ApprovalStepCreate(ApprovalStepBase):
    pass

class ApprovalStepResponse(ApprovalStepBase):
    id: str
    actioned_at: Optional[datetime]
    created_at: datetime

    class Config:
        orm_mode = True

class NotificationBase(PydanticBaseModel):
    recipient_id: str
    sender_id: Optional[str] = None
    notification_type: NotificationType
    subject: str
    message: str
    is_read: bool = False
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[str] = None

class NotificationCreate(NotificationBase):
    pass

class NotificationResponse(NotificationBase):
    id: str
    sent_at: datetime
    read_at: Optional[datetime]

    class Config:
        orm_mode = True

class AlertRuleBase(PydanticBaseModel):
    rule_name: str
    description: Optional[str] = None
    condition_json: Dict[str, Any]
    severity: AlertSeverity
    is_active: bool = True
    notification_channels: Optional[List[str]] = None
    created_by: str

class AlertRuleCreate(AlertRuleBase):
    pass

class AlertRuleUpdate(PydanticBaseModel):
    rule_name: Optional[str] = None
    description: Optional[str] = None
    condition_json: Optional[Dict[str, Any]] = None
    severity: Optional[AlertSeverity] = None
    is_active: Optional[bool] = None
    notification_channels: Optional[List[str]] = None

class AlertRuleResponse(AlertRuleBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class AlertBase(PydanticBaseModel):
    rule_id: Optional[str] = None
    triggered_at: datetime
    entity_type: str
    entity_id: str
    severity: AlertSeverity
    title: str
    description: Optional[str] = None
    status: str = 'active'
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None

class AlertCreate(AlertBase):
    pass

class AlertResponse(AlertBase):
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
def generate_notification_id():
    return str(uuid.uuid4())

# Routes
@app.get("/")
async def root():
    return {
        "service": "Collaboration & Workflow Service",
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

# User Endpoints (simplified - in reality, user management is in its own service)
@app.get("/users", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """Get users with filtering"""
    query = db.query(User)

    if role is not None:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    users = query.offset(skip).limit(limit).all()
    return users

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Forecast Collaboration Endpoints
@app.get("/forecast-collaborations", response_model=List[ForecastCollaborationResponse])
async def get_forecast_collaborations(
    forecast_id: Optional[str] = Query(None),
    collaborator_id: Optional[str] = Query(None),
    status: Optional[WorkflowStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get forecast collaborations with filtering"""
    query = db.query(ForecastCollaboration)

    if forecast_id:
        query = query.filter(ForecastCollaboration.forecast_id == forecast_id)
    if collaborator_id:
        query = query.filter(ForecastCollaboration.collaborator_id == collaborator_id)
    if status:
        query = query.filter(ForecastCollaboration.status == status)

    collaborations = query.offset(skip).limit(limit).all()
    return collaborations

@app.post("/forecast-collaborations", response_model=ForecastCollaborationResponse)
async def create_forecast_collaboration(
    collaboration: ForecastCollaborationCreate,
    db: Session = Depends(get_db)
):
    """Create a new forecast collaboration"""
    # Verify that the collaborator exists
    collaborator = db.query(User).filter(User.id == collaboration.collaborator_id).first()
    if not collaborator:
        raise HTTPException(status_code=404, detail="Collaborator not found")

    db_collaboration = ForecastCollaboration(**collaboration.dict())
    db.add(db_collaboration)
    db.commit()
    db.refresh(db_collaboration)
    return db_collaboration

@app.get("/forecast-collaborations/{collaboration_id}", response_model=ForecastCollaborationResponse)
async def get_forecast_collaboration(
    collaboration_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific forecast collaboration by ID"""
    collaboration = db.query(ForecastCollaboration).filter(ForecastCollaboration.id == collaboration_id).first()
    if collaboration is None:
        raise HTTPException(status_code=404, detail="Forecast collaboration not found")
    return collaboration

@app.put("/forecast-collaborations/{collaboration_id}", response_model=ForecastCollaborationResponse)
async def update_forecast_collaboration(
    collaboration_id: str,
    collaboration_update: ForecastCollaborationUpdate,
    db: Session = Depends(get_db)
):
    """Update a forecast collaboration"""
    db_collaboration = db.query(ForecastCollaboration).filter(ForecastCollaboration.id == collaboration_id).first()
    if db_collaboration is None:
        raise HTTPException(status_code=404, detail="Forecast collaboration not found")

    update_data = collaboration_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_collaboration, key, value)

    db_collaboration.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_collaboration)
    return db_collaboration

@app.post("/forecast-collaborations/{collaboration_id}/submit")
async def submit_forecast_collaboration(
    collaboration_id: str,
    db: Session = Depends(get_db)
):
    """Submit a forecast collaboration for review"""
    collaboration = db.query(ForecastCollaboration).filter(ForecastCollaboration.id == collaboration_id).first()
    if collaboration is None:
        raise HTTPException(status_code=404, detail="Forecast collaboration not found")

    collaboration.status = WorkflowStatus.SUBMITTED
    collaboration.submitted_at = datetime.utcnow()
    db.commit()

    return {"message": "Forecast collaboration submitted for review"}

@app.post("/forecast-collaborations/{collaboration_id}/approve")
async def approve_forecast_collaboration(
    collaboration_id: str,
    approver_id: str,
    db: Session = Depends(get_db)
):
    """Approve a forecast collaboration"""
    collaboration = db.query(ForecastCollaboration).filter(ForecastCollaboration.id == collaboration_id).first()
    if collaboration is None:
        raise HTTPException(status_code=404, detail="Forecast collaboration not found")

    # Verify that the approver exists
    approver = db.query(User).filter(User.id == approver_id).first()
    if not approver:
        raise HTTPException(status_code=404, detail="Approver not found")

    collaboration.status = WorkflowStatus.APPROVED
    collaboration.approved_by = approver_id
    collaboration.approved_at = datetime.utcnow()
    db.commit()

    return {"message": "Forecast collaboration approved"}

@app.post("/forecast-collaborations/{collaboration_id}/reject")
async def reject_forecast_collaboration(
    collaboration_id: str,
    approver_id: str,
    comments: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Reject a forecast collaboration"""
    collaboration = db.query(ForecastCollaboration).filter(ForecastCollaboration.id == collaboration_id).first()
    if collaboration is None:
        raise HTTPException(status_code=404, detail="Forecast collaboration not found")

    # Verify that the approver exists
    approver = db.query(User).filter(User.id == approver_id).first()
    if not approver:
        raise HTTPException(status_code=404, detail="Approver not found")

    collaboration.status = WorkflowStatus.REJECTED
    collaboration.reviewed_by = approver_id
    collaboration.reviewed_at = datetime.utcnow()
    if comments:
        collaboration.comments = comments
    db.commit()

    return {"message": "Forecast collaboration rejected"}

# Approval Workflow Endpoints
@app.get("/approval-workflows", response_model=List[ApprovalWorkflowResponse])
async def get_approval_workflows(
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    status: Optional[WorkflowStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get approval workflows with filtering"""
    query = db.query(ApprovalWorkflow)

    if entity_type:
        query = query.filter(ApprovalWorkflow.entity_type == entity_type)
    if entity_id:
        query = query.filter(ApprovalWorkflow.entity_id == entity_id)
    if status:
        query = query.filter(ApprovalWorkflow.status == status)

    workflows = query.offset(skip).limit(limit).all()
    return workflows

@app.post("/approval-workflows", response_model=ApprovalWorkflowResponse)
async def create_approval_workflow(
    workflow: ApprovalWorkflowCreate,
    db: Session = Depends(get_db)
):
    """Create a new approval workflow"""
    # Verify that the initiator exists
    initiator = db.query(User).filter(User.id == workflow.initiated_by).first()
    if not initiator:
        raise HTTPException(status_code=404, detail="Initiator not found")

    db_workflow = ApprovalWorkflow(**workflow.dict())
    db.add(db_workflow)
    db.commit()
    db.refresh(db_workflow)
    return db_workflow

@app.get("/approval-workflows/{workflow_id}", response_model=ApprovalWorkflowResponse)
async def get_approval_workflow(
    workflow_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific approval workflow by ID"""
    workflow = db.query(ApprovalWorkflow).filter(ApprovalWorkflow.id == workflow_id).first()
    if workflow is None:
        raise HTTPException(status_code=404, detail="Approval workflow not found")
    return workflow

@app.put("/approval-workflows/{workflow_id}", response_model=ApprovalWorkflowResponse)
async def update_approval_workflow(
    workflow_id: str,
    workflow_update: ApprovalWorkflowUpdate,
    db: Session = Depends(get_db)
):
    """Update an approval workflow"""
    db_workflow = db.query(ApprovalWorkflow).filter(ApprovalWorkflow.id == workflow_id).first()
    if db_workflow is None:
        raise HTTPException(status_code=404, detail="Approval workflow not found")

    update_data = workflow_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_workflow, key, value)

    db_workflow.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_workflow)
    return db_workflow

# Approval Step Endpoints
@app.get("/approval-steps", response_model=List[ApprovalStepResponse])
async def get_approval_steps(
    workflow_id: Optional[str] = Query(None),
    approver_id: Optional[str] = Query(None),
    status: Optional[ApprovalStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get approval steps with filtering"""
    query = db.query(ApprovalStep)

    if workflow_id:
        query = query.filter(ApprovalStep.workflow_id == workflow_id)
    if approver_id:
        query = query.filter(ApprovalStep.approver_id == approver_id)
    if status:
        query = query.filter(approval_step.status approver_status
    if status:
        query = query.filter(ApprovalStep.status == status)

    steps = query.offset(skip).limit(limit).all()
    return steps

@app.post("/approval-steps", response_model=ApprovalStepResponse)
async def create_approval_step(
    step: ApprovalStepCreate,
    db: Session = Depends(get_db)
):
    """Create a new approval step"""
    # Verify that the workflow exists
    workflow = db.query(ApprovalWorkflow).filter(ApprovalWorkflow.id == step.workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Verify that the approver exists
    approver = db.query(User).filter(User.id == step.approver_id).first()
    if not approver:
        raise HTTPException(status_code=404, detail="Approver not found")

    db_step = ApprovalStep(**step.dict())
    db.add(db_step)
    db.commit()
    db.refresh(db_step)
    return db_step

@app.post("/approval-steps/{step_id}/approve")
async def approve_approval_step(
    step_id: str,
    approver_comments: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Approve an approval step"""
    step = db.query(ApprovalStep).filter(ApprovalStep.id == step_id).first()
    if step is None:
        raise HTTPException(status_code=404, detail="Approval step not found")

    step.status = ApprovalStatus.APPROVED
    step.actioned_at = datetime.utcnow()
    if approver_comments:
        step.comments = approver_comments
    db.commit()

    # After approving a step, we might want to advance the workflow
    # For simplicity, we'll just return success
    return {"message": "Approval step approved"}

@app.post("/approval-steps/{step_id}/reject")
async def reject_approval_step(
    step_id: str,
    approver_comments: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Reject an approval step"""
    step = db.query(ApprovalStep).filter(ApprovalStep.id == step_id).first()
    if step is None:
        raise HTTPException(status_code=404, detail="Approval step not found")

    step.status = ApprovalStatus.REJECTED
    step.actioned_at = datetime.utcnow()
    if approver_comments:
        step.comments = approver_comments
    db.commit()

    # Update the workflow status to rejected
    workflow = step.workflow
    if workflow:
        workflow.status = WorkflowStatus.REJECTED
        workflow.updated_at = datetime.utcnow()
        db.commit()

    return {"message": "Approval step rejected"}

# Notification Endpoints
@app.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    recipient_id: Optional[str] = Query(None),
    is_read: Optional[bool] = Query(None),
    notification_type: Optional[NotificationType] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get notifications with filtering"""
    query = db.query(Notification)

    if recipient_id:
        query = query.filter(Notification.recipient_id == recipient_id)
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)
    if notification_type:
        query = query.filter(Notification.notification_type == notification_type)

    notifications = query.order_by(Notification.sent_at.desc()).offset(skip).limit(limit).all()
    return notifications

@app.post("/notifications", response_model=NotificationResponse)
async def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db)
):
    """Create a new notification"""
    # Verify that the recipient exists
    recipient = db.query(User).filter(User.id == notification.recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    # Verify that the sender exists if provided
    if notification.sender_id:
        sender = db.query(User).filter(User.id == notification.sender_id).first()
        if not sender:
            raise HTTPException(status_code=404, detail="Sender not found")

    db_notification = Notification(**notification.dict())
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

@app.post("/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    db: Session = Depends(get_db)
):
    """Mark a notification as read"""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.commit()

    return {"message": "Notification marked as read"}

# Alert Rule Endpoints
@app.get("/alert-rules", response_model=List[AlertRuleResponse])
async def get_alert_rules(
    is_active: Optional[bool] = Query(None),
    severity: Optional[AlertSeverity] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get alert rules with filtering"""
    query = db.query(AlertRule)

    if is_active is not None:
        query = query.filter(AlertRule.is_active == is_active)
    if severity:
        query = query.filter(AlertRule.severity == severity)

    rules = query.offset(skip).limit(limit).all()
    return rules

@app.post("/alert-rules", response_model=AlertRuleResponse)
async def create_alert_rule(
    rule: AlertRuleCreate,
    db: Session = Depends(get_db)
):
    """Create a new alert rule"""
    # Verify that the creator exists
    creator = db.query(User).filter(User.id == rule.created_by).first()
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found")

    db_rule = AlertRule(**rule.dict())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule

@app.get("/alert-rules/{rule_id}", response_model=AlertRuleResponse)
async def get_alert_rule(
    rule_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific alert rule by ID"""
    rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if rule is None:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    return rule

@app.put("/alert-rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: str,
    rule_update: AlertRuleUpdate,
    db: Session = Depends(get_db)
):
    """Update an alert rule"""
    db_rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if db_rule is None:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    update_data = rule_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_rule, key, value)

    db_rule.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_rule)
    return db_rule

# Alert Endpoints
@app.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    rule_id: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    severity: Optional[AlertSeverity] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get alerts with filtering"""
    query = db.query(Alert)

    if rule_id:
        query = query.filter(Alert.rule_id == rule_id)
    if entity_type:
        query = query.filter(Alert.entity_type == entity_type)
    if entity_id:
        query = query.filter(Alert.entity_id == entity_id)
    if severity:
        query = query.filter(Alert.severity == severity)
    if status:
        query = query.filter(Alert.status == status)

    alerts = query.order_by(Alert.triggered_at.desc()).offset(skip).limit(limit).all()
    return alerts

@app.post("/alerts", response_model=AlertResponse)
async def create_alert(
    alert: AlertCreate,
    db: Session = Depends(get_db)
):
    """Create a new alert"""
    # If rule_id is provided, verify that the rule exists
    if alert.rule_id:
        rule = db.query(AlertRule).filter(AlertRule.id == alert.rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail="Alert rule not found")

    db_alert = Alert(**alert.dict())
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert

@app.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    acknowledged_by: str,
    db: Session = Depends(get_db)
):
    """Acknowledge an alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Verify that the user exists
    user = db.query(User).filter(User.id == acknowledged_by).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    alert.status = "acknowledged"
    alert.acknowledged_by = acknowledged_by
    alert.acknowledged_at = datetime.utcnow()
    db.commit()

    return {"message": "Alert acknowledged"}

@app.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    resolved_by: str,
    resolution_notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Resolve an alert"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Verify that the user exists
    user = db.query(User).filter(User.id == resolved_by).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    alert.status = "resolved"
    alert.resolved_by = resolved_by
    alert.resolved_at = datetime.utcnow()
    if resolution_notes:
        alert.resolution_notes = resolution_notes
    db.commit()

    return {"message": "Alert resolved"}

# Dashboard Endpoints (for role-based views)
@app.get("/dashboard/executive")
async def get_executive_dashboard(
    db: Session = Depends(get_db)
):
    """Get data for executive dashboard"""
    # In a real implementation, this would aggregate data from various services
    # For now, we'll return placeholder data
    return {
        "total_forecasts": 124,
        "forecast_accuracy": 92.4,
        "total_inventory_value": 2450000,
        "inventory_turnover": 8.2,
        "stockout_incidents": 3,
        "on_time_delivery_rate": 94.2,
        "supplier_quality_score": 4.7,
        "active_alerts": 5,
        "pending_approvals": 12,
        "recent_activities": [
            {
                "id": "act1",
                "type": "forecast_approval",
                "description": "Forecast for Product Q3-2024 approved by Demand Planning Manager",
                "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat()
            },
            {
                "id": "act2",
                "type": "po_creation",
                "description": "New purchase order PO-2024-0847 created for Supplier XYZ Corp",
                "timestamp": (datetime.utcnow() - timedelta(hours=5)).isoformat()
            }
        ]
    }

@app.get("/dashboard/demand-planner")
async def get_demand_planner_dashboard(
    db: Session = Depends(get_db)
):
    """Get data for demand planner dashboard"""
    return {
        "my_forecasts": {
            "draft": 3,
            "submitted": 2,
            "approved": 5
        },
        "collaboration_requests": 4,
        "forecast_accuracy_trend": [
            {"month": "Jan", "accuracy": 89.2},
            {"month": "Feb", "accuracy": 91.5},
            {"month": "Mar", "accuracy": 92.4}
        ],
        "top_products_by_forecast_error": [
            {"product_id": "prod-123", "error_percentage": 15.2},
            {"product_id": "prod-456", "error_percentage": 12.8}
        ]
    }

@app.get("/dashboard/inventory-manager")
async def get_inventory_manager_dashboard(
    db: Session = Depends(get_db)
):
    """Get data for inventory manager dashboard"""
    return {
        "inventory_alerts": {
            "low_stock": 8,
            "overstock": 3,
            "expiring_soon": 2
        },
        "pending_replenishment_orders": 15,
        "inventory_turnover_by_category": [
            {"category": "Electronics", "turnover": 6.5},
            {"category": "Apparel", "turnover": 9.2},
            {"category": "Home Goods", "turnover": 7.8}
        ],
        "upcoming_purchase_orders": [
            {"po_id": "po-789", "supplier": "ABC Supplies", "expected_date": "2024-07-15", "amount": 25000}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)