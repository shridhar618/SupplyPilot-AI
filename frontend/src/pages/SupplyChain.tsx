import React from 'react';
import './pages.css';

const SupplyChain = () => {
  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Supply Chain Management</h1>
        <p className="page-description">
          Monitor and optimize your end-to-end supply chain operations
        </p>
      </div>

      <div className="content-section">
        <div className="action-buttons">
          <button className="btn btn-primary">Add New Supplier</button>
          <button className="btn btn-secondary">View Purchase Orders</button>
        </div>

        <div className="supply-chain-overview">
          <h2>Supply Chain Health</h2>
          <div className="sc-metrics">
            <div className="metric-card">
              <h3>On-Time Delivery Rate</h3>
              <p className="metric-value">94.2%</p>
              <p className="change-indicator positive">+1.8% vs last month</p>
            </div>
            <div className="metric-card">
              <h3>Average Lead Time</h3>
              <p className="metric-value">12.4 days</p>
              <p className="change-indicator negative">+0.8 days vs last month</p>
            </div>
            <div className="metric-card">
              <h3>Supplier Quality Score</h3>
              <p className="metric-value">4.7/5</p>
              <p className="change-indicator stable">±0.1 vs last quarter</p>
            </div>
            <div className="metric-card">
              <h3>Purchase Order Accuracy</h3>
              <p className="metric-value">98.6%</p>
              <p className="change-indicator positive">+0.3% vs last month</p>
            </div>
          </div>
        </div>

        <div className="suppliers-section">
          <h2>Supplier Performance</h2>
          <div className="suppliers-table">
            <div className="table-header">
              <div className="th">Supplier</div>
              <div className="th">On-Time Delivery</div>
              <div className="th">Quality Score</div>
              <div className="th">Lead Time (days)</div>
              <div className="th">Risk Level</div>
              <div className="th">Actions</div>
            </div>
            <div className="table-row">
              <div className="td">ABC Supplies Inc.</div>
              <div className="td">98%</div>
              <div className="td">4.8/5</div>
              <div className="td">7</div>
              <div className="td status low">Low</div>
              <div className="td actions">
                <button className="btn btn-sm btn-outline">View</button>
                <button className="btn btn-sm btn-outline">Contact</button>
              </div>
            </div>
            <div className="table-row">
              <div className="td">XYZ Manufacturing</div>
              <div className="td">85%</div>
              <div className="td">4.2/5</div>
              <div className="td">14</div>
              <div className="td status medium">Medium</div>
              <div className="td actions">
                <button className="btn btn-sm btn-outline">View</button>
                <button className="btn btn-sm btn-outline">Contact</button>
              </div>
            </div>
            <div className="table-row">
              <div className="td">Global Logistics Corp</div>
              <div className="td">92%</div>
              <div className="td">4.5/5</div>
              <div className="td">5</div>
              <div className="td status low">Low</div>
              <div className="td actions">
                <button className="btn btn-sm btn-outline">View</button>
                <button className="btn btn-sm btn-outline">Contact</button>
              </div>
            </div>
          </div>
        </div>

        <div className="purchase-orders-section">
          <h2>Recent Purchase Orders</h2>
          <div className="po-table">
            <div className="table-header">
              <div className="th">PO Number</div>
              <div className="th">Supplier</div>
              <div className="th">Order Date</div>
              <div className="th">Expected Delivery</div>
              <div className="th">Status</div>
              <div className="th">Value</div>
              <div className="th">Actions</div>
            </div>
            <div className="table-row">
              <div className="td">PO-2024-0845</div>
              <div className="td">ABC Supplies Inc.</div>
              <div className="td">Jun 10, 2024</div>
              <div className="td">Jun 20, 2024</div>
              <div className="td status delivered">Delivered</div>
              <div className="td">$12,450.00</div>
              <div className="td actions">
                <button className="btn btn-sm btn-outline">View</button>
                <button className="btn btn-sm btn-outline">Reorder</button>
              </div>
            </div>
            <div className="table-row">
              <div className="td">PO-2024-0846</div>
              <div className="td">XYZ Manufacturing</div>
              <div className="td">Jun 12, 2024</div>
              <div className="td">Jun 26, 2024</div>
              <div className="td status in-transit">In Transit</div>
              <div className="td">$8,920.00</div>
              <div className="td actions">
                <button className="btn btn-sm btn-outline">View</button>
                <button className="btn btn-sm btn-outline">Track</button>
              </div>
            </div>
            <div className="table-row">
              <div className="td">PO-2024-0847</div>
              <div className="td">Global Logistics Corp</div>
              <div className="td">Jun 15, 2024</div>
              <div className="td">Jun 22, 2024</div>
              <div className="td status processing">Processing</div>
              <div className="td">$15,780.00</div>
              <div className="td actions">
                <button className="btn btn-sm btn-outline">View</button>
                <button className="btn btn-sm btn-outline">Edit</button>
              </div>
            </div>
          </div>
        </div>

        <div className="logistics-section">
          <h2>Logistics & Transportation</h2>
          <div className="logistics-map">
            <p>Interactive shipment tracking map coming soon...</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SupplyChain;
