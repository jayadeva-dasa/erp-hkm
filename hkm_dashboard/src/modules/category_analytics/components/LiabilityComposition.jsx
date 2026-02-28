import React from 'react';
import './Composition.css';

export default function LiabilityComposition({ liabilities, totalLiabilities }) {
  const formatAmount = (value) => {
    return (value / 10000000).toFixed(2);
  };

  if (!liabilities || Object.keys(liabilities).length === 0) {
    return <div className="composition-empty">No liability data available</div>;
  }

  return (
    <div className="composition-list">
      {Object.entries(liabilities).map(([category, catData]) => {
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
                ₹ {formatAmount(catData.total)} Cr
              </div>
            </div>
            
            {catData.accounts && catData.accounts.length > 0 && (
              <div className="item-details">
                <div className="item-accounts-count">
                  {catData.accounts.length} {catData.accounts.length === 1 ? 'account' : 'accounts'}
                </div>
                
                <div className="item-accounts-list">
                  {catData.accounts.slice(0, 3).map((acc, idx) => (
                    <div key={idx} className="account-item">
                      <span className="account-name">{acc.account_name}</span>
                      <span className="account-amount">
                        ₹ {formatAmount(acc.amount)} Cr
                        {acc.portion < 100 && ` (${acc.portion}%)`}
                      </span>
                    </div>
                  ))}
                  {catData.accounts.length > 3 && (
                    <div className="account-more">
                      +{catData.accounts.length - 3} more accounts
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        );
      })}
      
      <div className="composition-total">
        <div className="total-label">Total Liabilities</div>
        <div className="total-value">
          ₹ {formatAmount(totalLiabilities)} Cr
        </div>
      </div>
    </div>
  );
}

