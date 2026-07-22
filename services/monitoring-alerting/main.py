"""
Monitoring & Alerting Service for SupplyPilot AI
Handles system monitoring, metrics collection, and alerting
"""
import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import uuid
import json
from fastapi import FastAPI, Depends, HTTPException, Query, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel as PydanticBaseModel, Field
import random
import asyncio
import time
import warnings
warnings.filterwarnings("ignore")

# Initialize FastAPI app
app = FastAPI(
    title="Monitoring & Alerting Service",
    description="Service for system monitoring, metrics, and alerting",
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

# Pydantic Models
class MetricPoint(PydanticBaseModel):
    timestamp: datetime
    value: float

class MetricSeries(PydanticBaseModel):
    metric_name: str
    labels: Dict[str, str] = {}
    data: List[MetricPoint]

class AlertRule(PydanticBaseModel):
    id: str
    name: str
    condition: str  # e.g., "cpu_usage > 80"
    severity: str   # info, warning, error, critical
    enabled: bool = True
    notification_channels: List[str] = []  # email, slack, etc.
    created_at: datetime
    updated_at: datetime

class Alert(PydanticBaseModel):
    id: str
    rule_id: str
    triggered_at: datetime
    status: str  # firing, resolved, acknowledged
    value: float
    message: str
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None

class Notification(PydanticBaseModel):
    id: str
    alert_id: str
    channel: str  # email, slack, sms, etc.
    sent_at: datetime
    status: str  # sent, failed, delivered
    recipient: str

# In-memory storage for demo
metrics_store = {}
alert_rules = {}
active_alerts = {}
notifications = []

# Background task for generating mock metrics
async def generate_metrics():
    """Background task to generate mock metrics"""
    while True:
        try:
            # Generate some mock system metrics
            timestamp = datetime.utcnow()

            # CPU usage
            cpu_usage = random.uniform(10, 90)
            if "system_cpu_usage" not in metrics_store:
                metrics_store["system_cpu_usage"] = []
            metrics_store["system_cpu_usage"].append({
                "timestamp": timestamp,
                "value": cpu_usage
            })
            # Keep only last 100 points
            if len(metrics_store["system_cpu_usage"]) > 100:
                metrics_store["system_cpu_usage"] = metrics_store["system_cpu_usage"][-100:]

            # Memory usage
            memory_usage = random.uniform(20, 80)
            if "system_memory_usage" not in metrics_store:
                metrics_store["system_memory_usage"] = []
            metrics_store["system_memory_usage"].append({
                "timestamp": timestamp,
                "value": memory_usage
            })
            if len(metrics_store["system_memory_usage"]) > 100:
                metrics_store["system_memory_usage"] = metrics_store["system_memory_usage"][-100:]

            # Request latency
            latency = random.uniform(50, 500)  # ms
            if "api_request_latency" not in metrics_store:
                metrics_store["api_request_latency"] = []
            metrics_store["api_request_latency"].append({
                "timestamp": timestamp,
                "value": latency
            })
            if len(metrics_store["api_request_latency"]) > 100:
                metrics_store["api_request_latency"] = metrics_store["api_request_latency"][-100:]

            # Check alert rules
            await check_alert_rules()

            # Wait for next interval
            await asyncio.sleep(10)  # Generate metrics every 10 seconds
        except Exception as e:
            logging.error(f"Error in metrics generation: {str(e)}")
            await asyncio.sleep(10)

async def check_alert_rules():
    """Check alert rules against current metrics"""
    # Simple rule checking for demo
    for rule_id, rule in alert_rules.items():
        if not rule.get("enabled", True):
            continue

        # Example rule: check CPU usage
        if rule_id == "high_cpu" and "system_cpu_usage" in metrics_store:
            latest = metrics_store["system_cpu_usage"][-1]["value"] if metrics_store["system_cpu_usage"] else 0
            if latest > 80:  # threshold
                # Create alert if not already firing
                alert_key = f"{rule_id}_{int(time.time())}"
                if alert_key not in active_alerts:
                    alert = Alert(
                        id=alert_key,
                        rule_id=rule_id,
                        triggered_at=datetime.utcnow(),
                        status="firing",
                        value=latest,
                        message=f"High CPU usage detected: {latest:.1f}%"
                    )
                    active_alerts[alert_key] = alert
                    # Trigger notification (in background)
                    # In a real system, you would send notifications here

        # Example rule: check memory usage
        if rule_id == "high_memory" and "system_memory_usage" in metrics_store:
            latest = metrics_store["system_memory_usage"][-1]["value"] if metrics_store["system_memory_usage"] else 0
            if latest > 85:
                alert_key = f"{rule_id}_{int(time.time())}"
                if alert_key not in active_alerts:
                    alert = Alert(
                        id=alert_key,
                        rule_id=rule_id,
                        triggered_at=datetime.utcnow(),
                        status="firing",
                        value=latest,
                        message=f"High memory usage detected: {latest:.1f}%"
                    )
                    active_alerts[alert_key] = alert

# Routes
@app.get("/")
async def root():
    return {
        "service": "Monitoring & Alerting Service",
        "version": "0.1.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup"""
    # Initialize some default alert rules
    alert_rules["high_cpu"] = {
        "id": "high_cpu",
        "name": "High CPU Usage",
        "condition": "cpu_usage > 80",
        "severity": "warning",
        "enabled": True,
        "notification_channels": ["email", "slack"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    alert_rules["high_memory"] = {
        "id": "high_memory",
        "name": "High Memory Usage",
        "condition": "memory_usage > 85",
        "severity": "warning",
        "enabled": True,
        "notification_channels": ["email", "slack"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    # Start metrics generation task
    asyncio.create_task(generate_metrics())

@app.get("/metrics", response_model=List[MetricSeries])
async def get_metrics(
    metric_names: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get time series metrics"""
    result = []

    # If specific metrics requested, filter; otherwise return all
    names_to_check = metric_names.split(",") if metric_names else metrics_store.keys()

    for metric_name in names_to_check:
        if metric_name in metrics_store:
            data = metrics_store[metric_name]

            # Filter by time range if provided
            if start_time:
                data = [point for point in data if point["timestamp"] >= start_time]
            if end_time:
                data = [point for point in data if point["timestamp"] <= end_time]

            # Limit results
            if len(data) > limit:
                data = data[-limit:]  # Get most recent points

            # Convert to MetricPoint objects
            points = [MetricPoint(timestamp=point["timestamp"], value=point["value"]) for point in data]

            result.append(MetricSeries(
                metric_name=metric_name,
                data=points
            ))

    return result

@app.get("/alert-rules", response_model=List[AlertRule])
async def get_alert_rules(
    enabled: Optional[bool] = Query(None),
    severity: Optional[str] = Query(None)
):
    """Get alert rules with optional filtering"""
    rules = list(alert_rules.values())

    if enabled is not None:
        rules = [rule for rule in rules if rule.get("enabled", True) == enabled]
    if severity:
        rules = [rule for rule in rules if rule.get("severity") == severity]

    return [AlertRule(**rule) for rule in rules]

@app.post("/alert-rules", response_model=AlertRule)
async def create_alert_rule(rule: AlertRule):
    """Create a new alert rule"""
    rule_dict = rule.dict()
    rule_dict["id"] = str(uuid.uuid4()) if not rule.id else rule.id
    rule_dict["created_at"] = datetime.utcnow()
    rule_dict["updated_at"] = datetime.utcnow()

    alert_rules[rule_dict["id"]] = rule_dict
    return AlertRule(**rule_dict)

@app.get("/alerts", response_model=List[Alert])
async def get_alerts(
    status: Optional[str] = Query(None),
    rule_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get alerts with optional filtering"""
    alerts = list(active_alerts.values())

    if status:
        alerts = [alert for alert in alerts if alert.status == status]
    if rule_id:
        alerts = [alert for alert in alerts if alert.rule_id == rule_id]

    # Sort by most recent first
    alerts.sort(key=lambda x: x.triggered_at, reverse=True)

    return alerts[:limit]

@app.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an active alert"""
    if alert_id not in active_alerts:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert = active_alerts[alert_id]
    alert.status = "acknowledged"
    alert.acknowledged_at = datetime.utcnow()

    return {"message": "Alert acknowledged"}

@app.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve an active alert"""
    if alert_id not in active_alerts:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert = active_alerts[alert_id]
    alert.status = "resolved"
    alert.resolved_at = datetime.utcnow()

    # Move to resolved alerts (in a real system, you might keep history)
    # For demo, we'll just remove from active
    del active_alerts[alert_id]

    return {"message": "Alert resolved"}

@app.get("/notifications", response_model=List[Notification])
async def get_notifications(
    alert_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get notification history"""
    notes = notifications

    if alert_id:
        notes = [n for n in notes if n.alert_id == alert_id]
    if status:
        notes = [n for n in notes if n.status == status]

    # Sort by most recent first
    notes.sort(key=lambda x: x.sent_at, reverse=True)

    return notes[:limit]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8011)