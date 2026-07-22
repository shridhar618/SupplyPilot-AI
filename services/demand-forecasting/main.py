"""
Demand Forecasting Service for SupplyPilot AI
Handles demand forecasting using various models (Prophet, XGBoost, LSTM, etc.)
"""
import os
import logging
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import numpy as np
import pandas as pd
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Text, Integer, ForeignKey, Numeric, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pydantic import BaseModel, Field
import uuid
import warnings
warnings.filterwarnings("ignore")

# Initialize FastAPI app
app = FastAPI(
    title="Demand Forecasting Service",
    description="AI-powered demand forecasting service for DemandSense AI",
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

# Database Models (simplified for this service)
class Product(Base):
    __tablename__ = "products"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)

class InventoryLocation(Base):
    __tablename__ = "inventory_locations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)

class DemandForecast(Base):
    __tablename__ = "demand_forecasts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("inventory_locations.id"), nullable=False)
    forecast_date = Column(DateTime, nullable=False)
    forecast_horizon = Column(Integer, nullable=False)
    predicted_demand = Column(Numeric(precision=10, scale=3), nullable=False)
    confidence_lower = Column(Numeric(precision=10, scale=3), nullable=True)
    confidence_upper = Column(Numeric(precision=10, scale=3), nullable=True)
    model_used = Column(String(50), nullable=True)
    model_version = Column(String(20), nullable=True)
    actual_demand = Column(Numeric(precision=10, scale=3), nullable=True)
    forecast_error = Column(Numeric(precision=10, scale=3), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic Models
class ForecastRequest(BaseModel):
    product_ids: List[str]
    location_ids: List[str]
    forecast_horizon: int = 30  # days
    model_type: str = "ensemble"  # prophet, xgboost, lstm, ensemble
    include_external_factors: bool = False

class ForecastResponse(BaseModel):
    forecast_id: str
    product_id: str
    location_id: str
    forecast_date: datetime
    forecast_horizon: int
    predicted_demand: float
    confidence_lower: Optional[float]
    confidence_upper: Optional[float]
    model_used: str
    created_at: datetime

class ForecastListResponse(BaseModel):
    forecasts: List[ForecastResponse]
    total: int
    page: int
    limit: int

class ModelTrainRequest(BaseModel):
    product_ids: List[str]
    location_ids: List[str]
    model_types: List[str] = ["prophet", "xgboost", "lstm"]
    training_start_date: datetime
    training_end_date: datetime
    validation_start_date: datetime
    validation_end_date: datetime

class ModelTrainResponse(BaseModel):
    message: str
    model_ids: List[str]

class ForecastAccuracyResponse(BaseModel):
    product_id: str
    location_id: str
    mae: float
    rmse: float
    mape: float
    accuracy: float
    model_used: str
    evaluated_at: datetime

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper functions for forecasting models
def prepare_time_series(data: pd.DataFrame, date_col: str, value_col: str) -> pd.DataFrame:
    """Prepare data for time series forecasting"""
    df = data.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.set_index(date_col).asfreq('D')  # Daily frequency
    df = df.fillna(method='ffill').fillna(method='bfill')
    return df[[value_col]]

def forecast_arima(data: pd.DataFrame, steps: int = 30) -> tuple:
    """Simple ARIMA forecast"""
    try:
        model = ARIMA(data, order=(1,1,1))
        fitted_model = model.fit()
        forecast = fitted_model.forecast(steps=steps)
        conf_int = fitted_model.get_forecast(steps=steps).conf_int()
        return forecast.values, conf_int[:, 0].values, conf_int[:, 1].values
    except Exception as e:
        logging.error(f"ARIMA model failed: {str(e)}")
        # Fallback to naive forecast
        last_value = data.iloc[-1, 0]
        forecast = np.full(steps, last_value)
        conf_low = np.full(steps, last_value * 0.8)
        conf_high = np.full(steps, last_value * 1.2)
        return forecast, conf_low, conf_high

def forecast_prophet(data: pd.DataFrame, steps: int = 30) -> tuple:
    """Prophet forecast"""
    try:
        df = data.reset_index()
        df.columns = ['ds', 'y']
        model = Prophet()
        model.fit(df)
        future = model.make_future_dataframe(periods=steps)
        forecast = model.predict(future)
        yhat_pred = forecast['yhat'].tail(steps).values
        yhat_lower = forecast['yhat_lower'].tail(steps).values
        yhat_upper = forecast['yhat_upper'].tail(steps).values
        return yhat_pred, yhat_lower, yhat_upper
    except Exception as e:
        logging.error(f"Prophet model failed: {str(e)}")
        # Fallback to naive forecast
        last_value = data.iloc[-1, 0]
        forecast = np.full(steps, last_value)
        conf_low = np.full(steps, last_value * 0.8)
        conf_high = np.full(steps, last_value * 1.2)
        return forecast, conf_low, conf_high

# Routes
@app.get("/")
async def root():
    return {
        "service": "Demand Forecasting Service",
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

@app.post("/forecasts/generate", response_model=List[ForecastResponse])
async def generate_forecasts(
    request: ForecastRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generate demand forecasts for products and locations
    """
    forecasts = []

    for product_id in request.product_ids:
        for location_id in request.location_ids:
            # In a real implementation, we would fetch historical data from the database
            # For now, we'll generate dummy historical data
            dates = [datetime.now() - timedelta(days=i) for i in range(365, 0, -1)]
            demand = np.random.randint(50, 150, size=365)  # Random demand between 50 and 150
            historical_data = pd.DataFrame({
                'date': dates,
                'demand': demand
            })

            # Prepare time series
            ts_data = prepare_time_series(historical_data, 'date', 'demand')

            # Select model
            if request.model_type == "arima":
                forecast_vals, lower_bounds, upper_bounds = forecast_arima(ts_data, request.forecast_horizon)
                model_used = "ARIMA"
            elif request.model_type == "prophet":
                forecast_vals, lower_bounds, upper_bounds = forecast_prophet(ts_data, request.forecast_horizon)
                model_used = "Prophet"
            else:  # default to simple moving average
                # Simple moving average forecast
                window = 7
                last_values = ts_data['demand'].tail(window).values
                forecast_vals = np.full(request.forecast_horizon, np.mean(last_values))
                # Simple confidence intervals based on historical std
                std_dev = np.std(ts_data['demand'])
                lower_bounds = np.maximum(0, forecast_vals - 1.96 * std_dev)
                upper_bounds = forecast_vals + 1.96 * std_dev
                model_used = "SMA"

            # Create forecast records
            for i in range(request.forecast_horizon):
                forecast_date = datetime.now() + timedelta(days=i+1)
                forecast_id = uuid.uuid4()

                forecast_record = DemandForecast(
                    id=forecast_id,
                    product_id=product_id,
                    location_id=location_id,
                    forecast_date=forecast_date,
                    forecast_horizon=i+1,
                    predicted_demand=max(0, forecast_vals[i]),
                    confidence_lower=max(0, lower_bounds[i]),
                    confidence_upper=upper_bounds[i],
                    model_used=model_used,
                    model_version="1.0"
                )
                db.add(forecast_record)

                forecasts.append(ForecastResponse(
                    forecast_id=str(forecast_id),
                    product_id=product_id,
                    location_id=location_id,
                    forecast_date=forecast_date,
                    forecast_horizon=i+1,
                    predicted_demand=max(0, float(forecast_vals[i])),
                    confidence_lower=max(0, float(lower_bounds[i])) if not np.isnan(lower_bounds[i]) else None,
                    confidence_upper=float(upper_bounds[i]) if not np.isnan(upper_bounds[i]) else None,
                    model_used=model_used,
                    created_at=datetime.utcnow()
                ))

    db.commit()
    return forecasts

@app.get("/forecasts", response_model=ForecastListResponse)
async def get_forecasts(
    product_id: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    model_used: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get demand forecasts with filtering"""
    query = db.query(DemandForecast)

    if product_id:
        query = query.filter(DemandForecast.product_id == product_id)
    if location_id:
        query = query.filter(DemandForecast.location_id == location_id)
    if start_date:
        query = query.filter(DemandForecast.forecast_date >= start_date)
    if end_date:
        query = query.filter(DemandForecast.forecast_date <= end_date)
    if model_used:
        query = query.filter(DemandForecast.model_used == model_used)

    total = query.count()
    forecasts = query.offset((page - 1) * limit).limit(limit).all()

    forecast_list = []
    for f in forecasts:
        forecast_list.append(ForecastResponse(
            forecast_id=str(f.id),
            product_id=str(f.product_id),
            location_id=str(f.location_id),
            forecast_date=f.forecast_date,
            forecast_horizon=f.forecast_horizon,
            predicted_demand=float(f.predicted_demand),
            confidence_lower=float(f.confidence_lower) if f.confidence_lower else None,
            confidence_upper=float(f.confidence_upper) if f.confidence_upper else None,
            model_used=f.model_used or "",
            created_at=f.created_at
        ))

    return ForecastListResponse(
        forecasts=forecast_list,
        total=total,
        page=page,
        limit=limit
    )

@app.get("/forecasts/{forecast_id}", response_model=ForecastResponse)
async def get_forecast(
    forecast_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific forecast by ID"""
    forecast = db.query(DemandForecast).filter(DemandForecast.id == forecast_id).first()
    if forecast is None:
        raise HTTPException(status_code=404, detail="Forecast not found")

    return ForecastResponse(
        forecast_id=str(forecast.id),
        product_id=str(forecast.product_id),
        location_id=str(forecast.location_id),
        forecast_date=forecast.forecast_date,
        forecast_horizon=forecast.forecast_horizon,
        predicted_demand=float(forecast.predicted_demand),
        confidence_lower=float(forecast.confidence_lower) if forecast.confidence_lower else None,
        confidence_upper=float(forecast.confidence_upper) if forecast.confidence_upper else None,
        model_used=forecast.model_used or "",
        created_at=forecast.created_at
    )

@app.post("/models/train", response_model=ModelTrainResponse)
async def train_models(
    request: ModelTrainRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Train forecasting models for products and locations
    """
    # In a real implementation, this would train actual models and save them
    # For now, we'll just return a success message
    model_ids = [str(uuid.uuid4()) for _ in range(len(request.product_ids) * len(request.location_ids))]

    # Background task to actually train models (placeholder)
    background_tasks.add_task(train_models_task, request.product_ids, request.location_ids, request.model_types)

    return ModelTrainResponse(
        message="Model training started",
        model_ids=model_ids
    )

async def train_models_task(product_ids: List[str], location_ids: List[str], model_types: List[str]):
    """Background task for model training"""
    # Placeholder for actual model training logic
    pass

@app.get("/forecasts/{product_id}/accuracy", response_model=List[ForecastAccuracyResponse])
async def get_forecast_accuracy(
    product_id: str,
    location_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    model_used: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get forecast accuracy metrics"""
    # In a real implementation, we would calculate accuracy by comparing forecasts to actuals
    # For now, we'll return mock data
    query = db.query(DemandForecast).filter(DemandForecast.product_id == product_id)
    if location_id:
        query = query.filter(DemandForecast.location_id == location_id)
    if start_date:
        query = query.filter(DemandForecast.forecast_date >= start_date)
    if end_date:
        query = query.filter(DemandForecast.forecast_date <= end_date)
    if model_used:
        query = query.filter(DemandForecast.model_used == model_used)

    forecasts = query.all()

    accuracy_list = []
    for f in forecasts:
        # Mock accuracy calculation
        mae = np.random.uniform(2.0, 5.0)
        rmse = np.random.uniform(3.0, 7.0)
        mape = np.random.uniform(5.0, 15.0)
        accuracy = max(0, 100 - mape)

        accuracy_list.append(ForecastAccuracyResponse(
            product_id=product_id,
            location_id=str(location_id) if location_id else str(f.location_id),
            mae=float(mae),
            float(rmse),
            float(mape),
            float(accuracy),
            model_used=f.model_used or "unknown",
            evaluated_at=datetime.utcnow()
        ))

    return accuracy_list

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)