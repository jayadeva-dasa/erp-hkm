import React from 'react';
import { formatIndianCurrency } from '../utils/formatters';

const SummaryCards = ({ summary }) => {
  // Add null check
  if (!summary) {
    return null;
  }

  return (
    <div className="grid grid-3">
      <div className="card" style={{
        background: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
        color: 'white',
        textAlign: 'center'
      }}>
        <h3 style={{ fontSize: '14px', opacity: 0.9, marginBottom: '10px', textTransform: 'uppercase' }}>
          Total Income
        </h3>
        <div style={{ fontSize: '32px', fontWeight: 'bold' }}>
          {formatIndianCurrency(summary.total_income || 0)}
        </div>
      </div>

      <div className="card" style={{
        background: 'linear-gradient(135deg, #ee0979 0%, #ff6a00 100%)',
        color: 'white',
        textAlign: 'center'
      }}>
        <h3 style={{ fontSize: '14px', opacity: 0.9, marginBottom: '10px', textTransform: 'uppercase' }}>
          Total Expenses
        </h3>
        <div style={{ fontSize: '32px', fontWeight: 'bold' }}>
          {formatIndianCurrency(summary.total_expense || 0)}
        </div>
      </div>

      <div className="card" style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        textAlign: 'center'
      }}>
        <h3 style={{ fontSize: '14px', opacity: 0.9, marginBottom: '10px', textTransform: 'uppercase' }}>
          Net Income
        </h3>
        <div style={{ fontSize: '32px', fontWeight: 'bold' }}>
          {formatIndianCurrency(summary.net_income || 0)}
        </div>
      </div>
    </div>
  );
};

export default SummaryCards;


