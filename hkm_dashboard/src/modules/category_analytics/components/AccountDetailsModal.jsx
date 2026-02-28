import React from 'react';
import { formatIndianCurrency, formatIndianNumber } from '../utils/formatters';

const AccountDetailsModal = ({ data, loading, onClose }) => {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()} style={{ minWidth: '600px' }}>
        <div className="modal-header">
          <h2 className="modal-title">
            {data?.category || 'Category Details'}
          </h2>
          <span className="modal-close" onClick={onClose}>&times;</span>
        </div>

        <div className="modal-body">
          {loading && (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <div className="loading-spinner"></div>
              <p>Loading account details...</p>
            </div>
          )}

          {!loading && data?.error && (
            <div className="error">
              {data.error}
            </div>
          )}

          {!loading && !data?.error && data?.accounts && (
            <>
              <div style={{ marginBottom: '20px', color: '#7f8c8d' }}>
                <strong>{data.count}</strong> account(s) in this category
              </div>

              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: '#f5f5f5', borderBottom: '2px solid #ddd' }}>
                    <th style={{ padding: '12px', textAlign: 'left' }}>#</th>
                    <th style={{ padding: '12px', textAlign: 'left' }}>Account</th>
                    <th style={{ padding: '12px', textAlign: 'right' }}>Portion</th>
                    <th style={{ padding: '12px', textAlign: 'right' }}>Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {data.accounts.map((acc, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid #eee' }}>
                      <td style={{ padding: '10px' }}>{idx + 1}</td>
                      <td style={{ padding: '10px' }}>
                        <div style={{ fontWeight: 500 }}>{acc.account_name || acc.account}</div>
                        {acc.account_name && (
                          <div style={{ fontSize: '12px', color: '#999' }}>{acc.account}</div>
                        )}
                      </td>
                      <td style={{ padding: '10px', textAlign: 'right' }}>
                        {acc.portion}%
                        {acc.portion < 100 && (
                          <span style={{ color: '#FF9800', marginLeft: '5px' }}>⚠️</span>
                        )}
                      </td>
                      <td style={{ padding: '10px', textAlign: 'right', fontWeight: 600 }}>
                        ₹{formatIndianNumber(acc.amount)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div style={{
                marginTop: '20px',
                padding: '15px',
                background: '#f5f5f5',
                borderRadius: '8px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <strong>Total:</strong>
                <strong style={{ fontSize: '18px', color: '#2196F3' }}>
                  {formatIndianCurrency(data.total)}
                </strong>
              </div>
            </>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default AccountDetailsModal;


