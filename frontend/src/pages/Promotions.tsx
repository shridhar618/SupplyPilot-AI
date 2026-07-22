import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './pages.css';

const Promotions = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    type: 'percentage',
    startDate: '',
    endDate: '',
    discountValue: ''
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // In a real app, this would submit to an API
    alert(`Promotion "${formData.name}" created successfully!`);
    resetForm();
    navigate('/promotions');
  };

  const resetForm = () => {
    setFormData({
      name: '',
      type: 'percentage',
      startDate: '',
      endDate: '',
      discountValue: ''
    });
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Promotion Management</h1>
        <p className="page-description">
          Create, manage, and analyze promotional campaigns to drive sales
        </p>
      </div>

      <div className="content-section">
        <div className="action-buttons">
          <button className="btn btn-primary" onClick={() => navigate('/promotions/create')}>
            Create New Promotion
          </button>
          <button className="btn btn-secondary" onClick={() => navigate('/promotions/calendar')}>
            View Promotion Calendar
          </button>
        </div>

        <div className="promotions-overview">
          <h2>Active Promotions</h2>
          <div className="promotions-stats">
            <div className="stat-item">
              <h3>Active Promotions</h3>
              <p className="stat-value">8</p>
            </div>
            <div className="stat-item">
              <h3>Upcoming Promotions</h3>
              <p className="stat-value">3</p>
            </div>
            <div className="stat-item">
              <h3>Avg. Lift</h3>
              <p className="stat-value">23%</p>
            </div>
            <div className="stat-item">
              <h3>Total Redemptions</h3>
              <p className="stat-value">12,450</p>
            </div>
          </div>
        </div>

        <div className="promotions-list">
          <h2>Recent Promotions</h2>
          <div className="promotion-card">
            <div className="promotion-header">
              <h3>Summer Clearance Sale</h3>
              <span className="status active">Active</span>
            </div>
            <div className="promotion-details">
              <p><strong>Type:</strong> Percentage Discount</p>
              <p><strong>Discount:</strong> 25% off</p>
              <p><strong>Duration:</strong> Jun 15 - Jul 15</p>
              <p><strong>Target Products:</strong> Summer Apparel (45 SKUs)</p>
            </div>
            <div className="promotion-metrics">
              <div className="metric">
                <h4>Sales Lift</h4>
                <p>+34%</p>
              </div>
              <div className="metric">
                <h4>Units Sold</h4>
                <p>2,840</p>
              </div>
              <div className="metric">
                <h4>Redemption Rate</h4>
                <p>78%</p>
              </div>
            </div>
            <div className="promotion-actions">
              <button className="btn btn-sm btn-outline" onClick={() => navigate('/promotions/summer-clearance')}>
                View Details
              </button>
              <button className="btn btn-sm btn-outline" onClick={() => alert('Ending promotion early...')}>
                End Early
              </button>
              <button className="btn btn-sm btn-outline" onClick={() => navigate('/promotions/summer-clearance/duplicate')}>
                Duplicate
              </button>
            </div>
          </div>

          <div className="promotion-card">
            <div className="promotion-header">
              <h3>Back-to-School Bundle</h3>
              <span className="status scheduled">Scheduled</span>
            </div>
            <div className="promotion-details">
              <p><strong>Type:</strong> Bundle Deal</p>
              <p><strong>Offer:</strong> Buy 2, Get 1 Free</p>
              <p><strong>Duration:</strong> Aug 1 - Sep 15</p>
              <p><strong>Target Products:</strong> School Supplies (78 SKUs)</p>
            </div>
            <div className="promotion-metrics">
              <div className="metric">
                <h4>Expected Lift</h4>
                <p>+45%</p>
              </div>
              <div className="metric">
                <h4>Launch Date</h4>
                <p>Aug 1, 2024</p>
              </div>
            </div>
            <div className="promotion-actions">
              <button className="btn btn-sm btn-outline" onClick={() => navigate('/promotions/back-to-school')}>
                View Details
              </button>
              <button className="btn btn-sm btn-outline" onClick={() => navigate('/promotions/back-to-school/edit')}>
                Edit
              </button>
              <button className="btn btn-sm btn-outline" onClick={() => alert('Promotion cancelled')}>
                Cancel
              </button>
            </div>
          </div>
        </div>

        <div className="create-promotion-section">
          <h2>Create New Promotion</h2>
          <form className="promotion-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="promo-name">Promotion Name:</label>
              <input
                type="text"
                id="promo-name"
                name="name"
                className="form-input"
                placeholder="Enter promotion name"
                value={formData.name}
                onChange={handleChange}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="promo-type">Promotion Type:</label>
              <select
                id="promo-type"
                name="type"
                className="form-select"
                value={formData.type}
                onChange={handleChange}
                required
              >
                <option value="percentage">Percentage Discount</option>
                <option value="fixed">Fixed Amount Discount</option>
                <option value="bogo">Buy One Get One</option>
                <option value="bundle">Bundle Deal</option>
                <option value="coupon">Coupon Code</option>
              </select>
            </div>
            <div className="form-group">
              <label htmlFor="start-date">Start Date:</label>
              <input
                type="date"
                id="start-date"
                name="startDate"
                className="form-input"
                value={formData.startDate}
                onChange={handleChange}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="end-date">End Date:</label>
              <input
                type="date"
                id="end-date"
                name="endDate"
                className="form-input"
                value={formData.endDate}
                onChange={handleChange}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="discount-value">Discount Value:</label>
              <input
                type="number"
                id="discount-value"
                name="discountValue"
                className="form-input"
                placeholder="Enter discount value"
                value={formData.discountValue}
                onChange={handleChange}
                required
              />
            </div>
            <div className="form-actions">
              <button type="button" className="btn btn-outline" onClick={resetForm}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary">
                Create Promotion
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Promotions;