import React from 'react';
import '../pages.css';

const Forecasting = () => {
  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Demand Forecasting</h1>
        <p className="page-description">
          Generate accurate demand forecasts using advanced AI models
        </p>
      </div>

      <div className="content-section">
        <div className="action-buttons">
          <button className="btn btn-primary">Generate New Forecast</button>
          <button className="btn btn-secondary">View Forecast History</button>
        </div>

        <div className="forecast-overview">
          <h2>Forecast Overview</h2>
          <div className="forecast-cards">
            <div className="forecast-card">
              <h3>Product A</h3>
              <p className="forecast-value">1,250 units</p>
              <p className="forecast-period">Next 30 days</p>
              <p className="model-info">Model: Ensemble (Prophet + XGBoost)</p>
            </div>
            <div className="forecast-card">
              <h3>Product B</h3>
              <p className="forecast-value">875 units</p>
              <p className="forecast-period">Next 30 days</p>
              <p className="model-info">Model: LSTM Neural Network</p>
            </div>
            <div className="forecast-card">
              <h3>Product C</h3>
              <p className="forecast-value">2,100 units</p>
              <p className="forecast-period">Next 30 days</p>
              <p className="model-info">Model: ARIMA</p>
            </div>
          </div>
        </div>

        <div className="chart-section">
          <h2>Forecast Visualization</h2>
          <div className="chart-placeholder">
            <p>Interactive forecast charts coming soon...</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Forecasting;