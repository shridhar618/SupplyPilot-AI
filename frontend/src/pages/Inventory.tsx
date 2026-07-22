import React from 'react';
import '../pages.css';

const Inventory = () => {
  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Inventory Management</h1>
        <p className="page-description">
          Optimize inventory levels across all locations with intelligent recommendations
        </p>
      </div>

      <div className="content-section">
        <div className="action-buttons">
          <button className="btn btn-primary">Run Optimization</button>
          <button className="btn btn-secondary">View Inventory Levels</button>
        </div>

        <div className="inventory-summary">
          <h2>Inventory Summary</h2>
          <div className="summary-cards">
            <div className="summary-card">
              <h3>Total Items in Stock</h3>
              <p className="summary-value">15,420</p>
              <p className="change-indicator positive">+2.3% vs last week</p>
            </div>
            <div className="summary-card">
              <h3>Items Below Reorder Point</h3>
              <p className="summary-value">24</p>
              <p className="change-indicator negative">+5 vs yesterday</p>
            </div>
            <div className="summary-card">
              <h3>Excess Inventory Value</h3>
              <p className="summary-value">$8,450</p>
              <p className="change-indicator negative">-12% vs last month</p>
            </div>
            <div className="summary-card">
              <h3>Inventory Turnover</h3>
              <p className="summary-value">8.2x</p>
              <p className="change-indicator positive">+0.5 vs last quarter</p>
            </div>
          </div>
        </div>

        <div className="recommendations-section">
          <h2>Optimization Recommendations</h2>
          <div className="recommendations-list">
            <div className="recommendation-item">
              <div className="recommendation-header">
                <h3>Product XYZ-123 - Warehouse A</h3>
                <span className="priority high">High Priority</span>
              </div>
              <p className="recommendation-description">
                Current stock: 12 units | Recommended order: 85 units
              </p>
              <p className="recommendation-reason">
                Based on demand forecast (avg 8.2 units/day) and 7-day lead time
              </p>
              <div className="recommendation-actions">
                <button className="btn btn-sm btn-outline">Create PO</button>
                <button className="btn btn-sm btn-outline">View Details</button>
              </div>
            </div>
            <div className="recommendation-item">
              <div className="recommendation-header">
                <h3>Product ABC-456 - Warehouse B</h3>
                <span className="priority medium">Medium Priority</span>
              </div>
              <p className="recommendation-description">
                Current stock: 210 units | Recommended action: Hold
              </p>
              <p className="recommendation-reason">
                Sufficient stock for next 18 days based on current demand
              </p>
              <div className="recommendation-actions">
                <button className="btn btn-sm btn-outline">Create PO</button>
                <button className="btn btn-sm btn-outline">View Details</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Inventory;