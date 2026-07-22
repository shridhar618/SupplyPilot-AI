import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import Forecasting from './pages/Forecasting';
import Inventory from './pages/Inventory';
import Promotions from './pages/Promotions';
import SupplyChain from './pages/SupplyChain';
import './App.css';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-white text-gray-900">
        <Routes>
          <Route path="/" element={<Layout><Dashboard /></Layout>} />
          <Route path="/forecasting" element={<Layout><Forecasting /></Layout>} />
          <Route path="/inventory" element={<Layout><Inventory /></Layout>} />
          <Route path="/promotions" element={<Layout><Promotions /></Layout>} />
          <Route path="/supply-chain" element={<Layout><SupplyChain /></Layout>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;