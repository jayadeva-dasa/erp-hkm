import React from 'react';
import './BalanceSheetSummary.css';

export default function BalanceSheetSummary({ summary }) {
  if (!summary) return null;

  const formatCrores = (value) => {
    const numValue = parseFloat(value) || 0;
    return (numValue / 10000000).toFixed(2);
  };

  const getChangeIcon = (value) => {
    if (value > 0) return '↗';
    if (value < 0) return '↘';
    return '→';
  };

  // Safely extract values with defaults
  const totalAssets = parseFloat(summary.total_assets) || 0;
  const totalLiabilities = parseFloat(summary.total_liabilities) || 0;
  const currentAssets = parseFloat(summary.current_assets) || 0;
  const fixedAssets = parseFloat(summary.fixed_assets) || 0;
  const currentLiabilities = parseFloat(summary.current_liabilities) || 0;
  const longTermLiabilities = parseFloat(summary.long_term_liabilities) || 0;
  const workingCapital = parseFloat(summary.working_capital) || 0;
  
  const netPosition = totalAssets - totalLiabilities;

  return (
    <div className="bs-summary-cards">
      <div className="bs-summary-card assets-card">
        <div className="card-icon">💰</div>
        <div className="card-label">Total Assets</div>
        <div className="card-value">
          ₹ {formatCrores(totalAssets)} Cr
        </div>
        <div className="card-breakdown">
          <span>Current: ₹{formatCrores(currentAssets)} Cr</span>
          <span>Fixed: ₹{formatCrores(fixedAssets)} Cr</span>
        </div>
      </div>
      
      <div className="bs-summary-card liabilities-card">
        <div className="card-icon">💳</div>
        <div className="card-label">Total Liabilities</div>
        <div className="card-value">
          ₹ {formatCrores(totalLiabilities)} Cr
        </div>
        <div className="card-breakdown">
          <span>Current: ₹{formatCrores(currentLiabilities)} Cr</span>
          <span>Long-term: ₹{formatCrores(longTermLiabilities)} Cr</span>
        </div>
      </div>
      
      <div className="bs-summary-card net-position-card">
        <div className="card-icon">💎</div>
        <div className="card-label">Net Position</div>
        <div className="card-value" style={{ color: netPosition >= 0 ? '#4CAF50' : '#f44336' }}>
          {getChangeIcon(netPosition)} ₹ {formatCrores(Math.abs(netPosition))} Cr
        </div>
        <div className="card-note">
          Assets - Liabilities
        </div>
      </div>
      
      <div className="bs-summary-card working-capital-card">
        <div className="card-icon">📊</div>
        <div className="card-label">Working Capital</div>
        <div className="card-value" style={{ color: workingCapital >= 0 ? '#4CAF50' : '#f44336' }}>
          {getChangeIcon(workingCapital)} ₹ {formatCrores(Math.abs(workingCapital))} Cr
        </div>
        <div className="card-note">
          Current Assets - Current Liabilities
        </div>
      </div>
    </div>
  );
}

