import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useNavigate } from 'react-router-dom';
import './pages.css';

// Mock data for metrics
const metricsData = [
  { name: 'Forecast Accuracy', value: '92%', change: '+2.3%', isPositive: true, path: '/forecasting' },
  { name: 'Inventory Turnover', value: '8.2', change: '+0.5', isPositive: true, path: '/inventory' },
  { name: 'Stockout Incidents', value: '3', change: '-1.2', isPositive: true, path: '/inventory' }, // Lower is better
  { name: 'Sales Trend', value: '$452K', change: '+5.1%', isPositive: true, path: '/forecasting' },
];

// Mock data for forecast accuracy chart (last 6 months)
const forecastData = [
  { month: 'Jan', accuracy: 88 },
  { month: 'Feb', accuracy: 90 },
  { month: 'Mar', accuracy: 85 },
  { month: 'Apr', accuracy: 92 },
  { month: 'May', accuracy: 94 },
  { month: 'Jun', accuracy: 92 },
];

// Mock data for inventory levels (by category)
const inventoryData = [
  { name: 'Electronics', value: 450 },
  { name: 'Apparel', value: 320 },
  { name: 'Home Goods', value: 210 },
  { name: 'Sports', value: 180 },
];

const Dashboard = () => {
  const navigate = useNavigate();

  const handleNavigate = (path: string) => {
    navigate(path);
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-description">
          Overview of key metrics and insights for your supply chain operations
          Use the navigation menu to explore different modules.
        </p>
      </div>

      <div className="content-section">
        {/* Action Buttons */}
        <div className="action-buttons">
          <button className="btn btn-primary" onClick={() => handleNavigate('/forecasting')}>
            Generate New Forecast
          </button>
          <button className="btn btn-secondary" onClick={() => handleNavigate('/inventory')}>
            View Inventory Levels
          </button>
        </div>

        {/* Metrics Cards */}
        <div className="metrics-grid">
          {metricsData.map((metric, index) => (
            <div
              key={index}
              className="metric-card"
              onClick={() => handleNavigate(metric.path)}
              style={{ cursor: 'pointer' }}
            >
              <h3>{metric.name}</h3>
              <p className="metric-value">{metric.value}</p>
              <p className={`change-indicator ${metric.isPositive ? 'positive' : 'negative'}`}>
                {metric.change}
              </p>
            </div>
          ))}
        </div>

        {/* Charts Section */}
        <div className="forecast-overview">
          <h2>Forecast Accuracy Trend</h2>
          <div className="chart-section">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={forecastData}>
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="accuracy" fill="#4299e1" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="supply-chain-overview">
          <h2>Inventory Levels by Category</h2>
          <div className="chart-section">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={inventoryData}>
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="value" fill="#38a169" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;