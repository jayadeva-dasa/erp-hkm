import React, { useState } from 'react';
import { 
  formatIndianCurrency, 
  formatPercent,
  getVolatilityBadgeClass,
  getTrendBadgeClass,
  getTrendIcon
} from '../utils/formatters';

const VolatilityAnalysis = ({ incomeStats, expenseStats }) => {
  const [activeTab, setActiveTab] = useState('income');
  
  // Add null checks
  if (!incomeStats || !expenseStats) {
    return null;
  }
  
  const stats = activeTab === 'income' ? incomeStats : expenseStats;
  const categories = Object.keys(stats).sort((a, b) => {
    // Sort by volatility: volatile > moderate > stable
    const volatilityOrder = { 'volatile': 0, 'moderate': 1, 'stable': 2 };
    return volatilityOrder[stats[a].volatility] - volatilityOrder[stats[b].volatility];
  });

  return (
    <div className="card">
      <div className="card-header">
        Volatility & Trend Analysis
        <div style={{ float: 'right', display: 'flex', gap: '10px' }}>
          <button
            className={`btn ${activeTab === 'income' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('income')}
            style={{ padding: '6px 15px', fontSize: '13px' }}
          >
            Income
          </button>
          <button
            className={`btn ${activeTab === 'expense' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('expense')}
            style={{ padding: '6px 15px', fontSize: '13px' }}
          >
            Expense
          </button>
        </div>
      </div>

      <div style={{ padding: '20px' }}>
        <div style={{ marginBottom: '20px', color: '#7f8c8d' }}>
          <strong>Legend:</strong>
          <span className="badge badge-stable" style={{ marginLeft: '10px' }}>Stable (CV &lt; 15%)</span>
          <span className="badge badge-moderate" style={{ marginLeft: '10px' }}>Moderate (CV 15-30%)</span>
          <span className="badge badge-volatile" style={{ marginLeft: '10px' }}>Volatile (CV &gt; 30%)</span>
        </div>

        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#f5f5f5', borderBottom: '2px solid #ddd' }}>
              <th style={{ padding: '12px', textAlign: 'left' }}>Category</th>
              <th style={{ padding: '12px', textAlign: 'right' }}>Average</th>
              <th style={{ padding: '12px', textAlign: 'center' }}>Volatility</th>
              <th style={{ padding: '12px', textAlign: 'center' }}>CV</th>
              <th style={{ padding: '12px', textAlign: 'center' }}>Trend</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Recent Changes</th>
            </tr>
          </thead>
          <tbody>
            {categories.map((category, idx) => {
              const stat = stats[category];
              const recentChanges = stat.month_over_month.slice(-3); // Last 3 months
              
              return (
                <tr key={idx} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={{ padding: '12px', fontWeight: 500 }}>
                    {category}
                  </td>
                  <td style={{ padding: '12px', textAlign: 'right' }}>
                    {formatIndianCurrency(stat.mean)}
                  </td>
                  <td style={{ padding: '12px', textAlign: 'center' }}>
                    <span className={`badge ${getVolatilityBadgeClass(stat.volatility)}`}>
                      {stat.volatility}
                    </span>
                  </td>
                  <td style={{ padding: '12px', textAlign: 'center' }}>
                    {formatPercent(stat.cv)}
                  </td>
                  <td style={{ padding: '12px', textAlign: 'center' }}>
                    <span className={`badge ${getTrendBadgeClass(stat.trend)}`}>
                      {getTrendIcon(stat.trend)} {stat.trend}
                    </span>
                  </td>
                  <td style={{ padding: '12px' }}>
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                      {recentChanges.map((change, i) => (
                        <div 
                          key={i}
                          className="tooltip"
                          data-tooltip={`${change.month}: ${formatIndianCurrency(change.change_amount)}`}
                          style={{
                            padding: '4px 8px',
                            borderRadius: '4px',
                            fontSize: '11px',
                            background: change.change_percent >= 0 ? '#e8f5e9' : '#ffebee',
                            color: change.change_percent >= 0 ? '#2e7d32' : '#c62828'
                          }}
                        >
                          {change.change_percent >= 0 ? '↑' : '↓'} {formatPercent(Math.abs(change.change_percent))}
                        </div>
                      ))}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        <div style={{ marginTop: '20px', padding: '15px', background: '#f5f5f5', borderRadius: '8px' }}>
          <strong>💡 Insights:</strong>
          <ul style={{ marginTop: '10px', marginLeft: '20px' }}>
            <li>
              <strong>Volatile categories</strong> show high fluctuation and may need closer monitoring
            </li>
            <li>
              <strong>Stable categories</strong> have predictable patterns and are easier to budget
            </li>
            <li>
              <strong>Increasing trends</strong> indicate growing income/expenses over time
            </li>
            <li>
              <strong>Recent changes</strong> show month-over-month percentage changes for the last 3 months
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default VolatilityAnalysis;


