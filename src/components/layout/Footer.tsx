import React from 'react';
import './Footer.css';

const Footer = () => {
  return (
    <footer className="bg-gray-50 border-t">
      <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
        <p className="text-center text-sm text-gray-500">
          © {new Date().getFullYear()} SupplyPilot AI. All rights reserved.
        </p>
      </div>
    </footer>
  );
};

export default Footer;