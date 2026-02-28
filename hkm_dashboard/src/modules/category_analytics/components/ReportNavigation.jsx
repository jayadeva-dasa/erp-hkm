import React from 'react';
import { Link, useLocation } from 'react-router-dom';

function ReportNavigation() {
  const location = useLocation();

  const navItems = [
    {
      path: '/category-analytics',
      label: 'Dashboard',
      icon: '🏠',
      description: 'Overview and Summary'
    },
    {
      path: '/category-analytics/balance-sheet',
      label: 'Balance Sheet',
      icon: '📊',
      description: 'Assets, Liabilities & Financial Position'
    },
    {
      path: '/category-analytics/pl-report',
      label: 'P&L Report',
      icon: '📈',
      description: 'Income, Expenses & Profitability'
    }
  ];

  return (
    <div style={{
      background: 'white',
      borderRadius: '12px',
      padding: '20px',
      marginBottom: '20px',
      boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
      border: '1px solid #e0e0e0'
    }}>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '15px'
      }}>
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;

          return (
            <Link
              key={item.path}
              to={item.path}
              style={{
                textDecoration: 'none',
                color: 'inherit'
              }}
            >
              <div style={{
                padding: '20px',
                borderRadius: '10px',
                background: isActive
                  ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                  : '#f8f9fa',
                border: isActive ? 'none' : '2px solid #e9ecef',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                textAlign: 'center',
                transform: isActive ? 'translateY(-2px)' : 'translateY(0)',
                boxShadow: isActive
                  ? '0 4px 15px rgba(102, 126, 234, 0.3)'
                  : '0 2px 5px rgba(0,0,0,0.1)',
                ':hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: '0 4px 15px rgba(102, 126, 234, 0.3)'
                }
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.target.style.transform = 'translateY(-2px)';
                  e.target.style.boxShadow = '0 4px 15px rgba(102, 126, 234, 0.3)';
                  e.target.style.borderColor = '#667eea';
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = '0 2px 5px rgba(0,0,0,0.1)';
                  e.target.style.borderColor = '#e9ecef';
                }
              }}
            >
              <div style={{
                fontSize: '32px',
                marginBottom: '10px',
                opacity: isActive ? 1 : 0.7
              }}>
                {item.icon}
              </div>
              <div style={{
                fontSize: '16px',
                fontWeight: '600',
                marginBottom: '5px',
                color: isActive ? 'white' : '#2c3e50'
              }}>
                {item.label}
              </div>
              <div style={{
                fontSize: '12px',
                color: isActive ? 'rgba(255,255,255,0.8)' : '#7f8c8d',
                lineHeight: '1.4'
              }}>
                {item.description}
              </div>
            </div>
          </Link>
          );
        })}
      </div>
    </div>
  );
}

export default ReportNavigation;


