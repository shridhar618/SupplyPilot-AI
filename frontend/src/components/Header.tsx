import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FiLogOut, FiMenu, FiLogo } from 'react-icons/fi';
import './Header.css';

const Header = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    // Clear auth tokens
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    // Redirect to login page (we'll create this later)
    navigate('/login');
  };

  return (
    <header className="bg-white border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <FiLogo className="h-8 w-8 text-indigo-600" />
              <span className="ml-2 text-xl font-semibold text-gray-900">
                SupplyPilot AI
              </span>
            </div>
            <div className="hidden md:block">
              <div className="ml-10 flex items-baseline space-x-4">
                <a
                  href="/"
                  className="px-3 py-2 rounded-md text-sm font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-50"
                >
                  Dashboard
                </a>
                <a
                  href="/forecasting"
                  className="px-3 py-2 rounded-md text-sm font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-50"
                >
                  Forecasting
                </a>
                <a
                  href="/inventory"
                  className="px-3 py-2 rounded-md text-sm font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-50"
                >
                  Inventory
                </a>
                <a
                  href="/promotions"
                  className="px-3 py-2 rounded-md text-sm font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-50"
                >
                  Promotions
                </a>
                <a
                  href="/supply-chain"
                  className="px-3 py-2 rounded-md text-sm font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-50"
                >
                  Supply Chain
                </a>
              </div>
            </div>
          </div>
          <div className="hidden md:block">
            <div className="ml-4 flex items-center md:ml-6">
              <button
                type="button"
                onClick={handleLogout}
                className="bg-white rounded-md px-2.5 py-1.5 text-sm font-medium text-gray-500 hover:text-gray-900 focus:outline-none focus:ring-2 focus-ring-offset-2"
              >
                Sign out
                <FiLogOut className="ml-2 h-4 w-4" />
              </button>
            </div>
          </div>
          <div className="-mr-2 flex md:hidden">
            <button
              type="button"
              className="bg-white rounded-md p-2 ripple inline-flex items-center justify-center text-sm font-medium text-gray-500 hover:text-gray-900 hover:bg-gray-50 focus:outline-none focus:ring-2 focus-ring-inset focus-ring-indigo-500"
            >
              <span className="sr-only">Open main menu</span>
              {/* Hamburger icon - using react-icons */}
              <FiMenu className="h-6 w-6" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;