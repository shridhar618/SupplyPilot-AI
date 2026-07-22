"""
Explainable AI Service for SupplyPilot AI
Provides model explainability using SHAP and other techniques
"""
import os
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid
import numpy as np
import pandas as pd
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel as PydanticBaseModel, Field
import shap
import warnings
warnings.filterwarnings("ignore")

# Initialize FastAPI app
app = FastAPI(
    title="Explainable AI Service",
    description="Service for model explainability and interpretation",
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
class ExplainabilityRequest(PydanticBaseModel):
    model_type: str  # e.g., "xgboost", "random_forest", "neural_network"
    features: List[str]
    sample_data: List[List[float]]  # 2D array: [sample, features]
    feature_names: Optional[List[str]] = None
    explanation_type: str = "shap"  # shap, lime, etc.

class ExplainabilityResponse(PydanticBaseModel):
    explanation_id: str
    feature_importance: Dict[str, float]
    shap_values: Optional[List[List[float]]] = None
    expected_value: Optional[float] = None
    explanation_text: str
    created_at: datetime

# In-memory storage for demo (in production, use a database or cache)
explanation_cache = {}

# Routes
@app.get("/")
async def root():
    return {
        "service": "Explainable AI Service",
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

@app.post("/explain", response_model=ExplainabilityResponse)
async def explain_model(
    request: ExplainabilityRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate explanations for model predictions
    """
    explanation_id = str(uuid.uuid4())

    try:
        # Convert input data
        data = np.array(request.sample_data)
        feature_names = request.feature_names or request.features

        # For demonstration, we'll create a simple mock model
        # In a real implementation, you would load a trained model

        # Mock explanation based on SHAP (simplified)
        if request.explanation_type == "shap":
            # Generate mock SHAP values
            shap_values = np.random.uniform(-1, 1, size=(len(request.sample_data), len(feature_names))).tolist()
            expected_value = float(np.mean(data))
            feature_importance = {}
            for i, fname in enumerate(feature_names):
                # Mean absolute SHAP value as feature importance
                importance = np.mean(np.abs([shap_values[j][i] for j in range(len(shap_values))]))
                feature_importance[fname] = float(importance)

            explanation_text = f"SHAP explanation for {request.model_type} model. " \
                             f"Top feature: {max(feature_importance, key=feature_importance.get)} " \
                             f"with importance {max(feature_importance.values()):.3f}"
        else:
            # Fallback to simple feature importance
            shap_values = None
            expected_value = None
            # Random feature importance for demo
            importances = np.random.uniform(0, 1, size=len(feature_names))
            importances = importances / importances.sum()
            feature_importance = {fname: float(imp) for fname, imp in zip(feature_names, importances)}
            explanation_text = f"Feature importance explanation for {request.model_type} model."

        # Cache the explanation
        explanation_cache[explanation_id] = {
            "feature_importance": feature_importance,
            "shap_values": shap_values,
            "expected_value": expected_value,
            "explanation_text": explanation_text,
            "created_at": datetime.utcnow()
        }

        return ExplainabilityResponse(
            explanation_id=explanation_id,
            feature_importance=feature_importance,
            shap_values=shap_values,
            expected_value=expected_value,
            explanation_text=explanation_text,
            created_at=datetime.utcnow()
        )

    except Exception as e:
        logging.error(f"Error generating explanation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate explanation: {str(e)}")

@app.get("/explain/{explanation_id}", response_model=ExplainabilityResponse)
async def get_explanation(explanation_id: str):
    """Retrieve a previously generated explanation"""
    if explanation_id not in explanation_cache:
        raise HTTPException(status_code=404, detail="Explanation not found")

    cached = explanation_cache[explanation_id]
    return ExplainabilityResponse(
        explanation_id=explanation_id,
        feature_importance=cached["feature_importance"],
        shap_values=cached["shap_values"],
        expected_value=cached["expected_value"],
        explanation_text=cached["explanation_text"],
        created_at=cached["created_at"]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)