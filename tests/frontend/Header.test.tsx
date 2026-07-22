import React from 'react';
import { render, screen } from '@testing-library/react';
import Header from '../../frontend/src/components/Header';

describe('Header Component', () => {
  it('renders the logo and text', () => {
    render(<Header />);
    const logoElement = screen.getByRole('img', { name: /supplypilot ai/i });
    expect(logoElement).toBeInTheDocument();
    const headingElement = screen.getByText(/supplypilot ai/i);
    expect(headingElement).toBeInTheDocument();
  });

  it('renders the navigation links', () => {
    render(<Header />);
    const dashboardLink = screen.getByRole('link', { name: /dashboard/i });
    expect(dashboardLink).toBeInTheDocument();
    const forecastingLink = screen.getByRole('link', { name: /forecasting/i });
    expect(forecastingLink).toBeInTheDocument();
    // Add more links as needed
  });

  it('renders the sign out button', () => {
    render(<Header />);
    const signOutButton = screen.getByRole('button', { name: /sign out/i });
    expect(signOutButton).toBeInTheDocument();
  });
});