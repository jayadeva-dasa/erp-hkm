import React, { useState, useEffect } from 'react';
import { getBalanceSheetData } from '../api/categoryAnalyticsApi';
import BalanceSheetSummary from './BalanceSheetSummary';
import AssetComposition from './AssetComposition';
import LiabilityComposition from './LiabilityComposition';
import BalanceSheetTrends from './BalanceSheetTrends';
import './BalanceSheetView.css';

export default function BalanceSheetView({ company, fromDate, toDate }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (company && fromDate && toDate) {
      loadBalanceSheetData();
    }
  }, [company, fromDate, toDate]);

  const loadBalanceSheetData = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await getBalanceSheetData(company, fromDate, toDate);
      setData(result);
    } catch (err) {
      setError(err.message || 'Failed to load balance sheet data');
      console.error('Error loading balance sheet:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="balance-sheet-loading">
        <div className="loading-spinner"></div>
        <p>Loading balance sheet data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="balance-sheet-error">
        <strong>Error:</strong> {error}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="balance-sheet-empty">
        <div style={{ fontSize: '48px', marginBottom: '20px' }}>📊</div>
        <h2>Select Filters to View Balance Sheet</h2>
        <p>Choose company and date range to view financial position</p>
      </div>
    );
  }

  return (
    <div className="balance-sheet-view">
      <div className="balance-sheet-header">
        <h1>📊 Balance Sheet Analysis</h1>
        <p className="balance-sheet-subtitle">
          Financial Position as of {toDate}
        </p>
      </div>

      {/* Summary Cards */}
      <BalanceSheetSummary summary={data.summary} />

      {/* Visual Balance Sheet */}
      <div className="visual-balance-sheet">
        <div className="balance-sheet-side assets-side">
          <div className="side-header">
            <h2>ASSETS</h2>
            <div className="side-total">
              ₹ {(data.summary.total_assets / 10000000).toFixed(2)} Cr
            </div>
          </div>
          <AssetComposition assets={data.assets} />
        </div>

        <div className="balance-sheet-divider">
          <div className="equals-sign">=</div>
        </div>

        <div className="balance-sheet-side liabilities-side">
          <div className="side-header">
            <h2>LIABILITIES</h2>
            <div className="side-total">
              ₹ {(data.summary.total_liabilities / 10000000).toFixed(2)} Cr
            </div>
          </div>
          <LiabilityComposition 
            liabilities={data.liabilities}
            totalLiabilities={data.summary.total_liabilities}
          />
        </div>
      </div>

      {/* Trends */}
      <BalanceSheetTrends 
        assets={data.assets}
        liabilities={data.liabilities}
        periods={data.period_list}
      />
    </div>
  );
}

