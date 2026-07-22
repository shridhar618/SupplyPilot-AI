import React from 'react';
import '../pages.css';

const Dashboard = () => {
  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-description">
          Overview of key metrics and insights for your supply chain operations
        </p>
      </div>

      <div className="content-section">
        <div className="welcome-message">
          <h2>Welcome to SupplyPilot AI</h2>
          <p>
            Your AI-powered decision intelligence platform for demand forecasting and supply chain optimization.
            Use the navigation menu to explore different modules.
          </p>
        </div>

        {/* In a real implementation, this would show charts, metrics, etc. */}
        <div className="placeholder-content">
          <div className="placeholder-item">
            <h3>Forecast Accuracy</h3>
            <p>View your demand forecast accuracy metrics</p>
          </div>
          <div className="placeholder-item">
            <h3>Inventory Levels</h3>
            <p>Monitor stock levels across all locations</p>
          </div>
          <div className="placeholder-item">
            <h3>Promotion Performance</h3>
            <p>Analyze the effectiveness of your promotions</p>
          </div>
          <div className="placeholder-item">
            <h3>Supply Chain Risks</h3>
            <p>Identify and mitigate potential disruptions</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;