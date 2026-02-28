import React from 'react';
import './Composition.css';

export default function AssetComposition({ assets }) {
  if (!assets || Object.keys(assets).length === 0) {
    return <div className="composition-empty">No asset data available</div>;
  }

  const formatAmount = (value) => {
    return (value / 10000000).toFixed(2);
  };

  return (
    <div className="composition-list">
      {Object.entries(assets).map(([category, data]) => {
        const isUncategorized = category === 'Uncategorized';
        
        return (
          <div 
            key={category} 
            className={`composition-item ${isUncategorized ? 'uncategorized' : ''}`}
          >
            <div className="item-header">
              <div className="item-name">
                {isUncategorized && '⚠️ '}
                {category}
              </div>
              <div className="item-value">
                ₹ {formatAmount(data.total)} Cr
              </div>
            </div>
            
            {data.accounts && data.accounts.length > 0 && (
              <div className="item-details">
                <div className="item-accounts-count">
                  {data.accounts.length} {data.accounts.length === 1 ? 'account' : 'accounts'}
                </div>
                
                <div className="item-accounts-list">
                  {data.accounts.slice(0, 3).map((acc, idx) => (
                    <div key={idx} className="account-item">
                      <span className="account-name">{acc.account_name}</span>
                      <span className="account-amount">
                        ₹ {formatAmount(acc.amount)} Cr
                        {acc.portion < 100 && ` (${acc.portion}%)`}
                      </span>
                    </div>
                  ))}
                  {data.accounts.length > 3 && (
                    <div className="account-more">
                      +{data.accounts.length - 3} more accounts
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}




