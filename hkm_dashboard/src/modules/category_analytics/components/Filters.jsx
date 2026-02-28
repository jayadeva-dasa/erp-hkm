import React from 'react';

const Filters = ({ 
  filters, 
  companies, 
  onChange, 
  onGetReport, 
  loading, 
  activeReport, 
  onReportChange,
  reportType, // 'balance-sheet' or 'pl-report' for standalone reports
  buttonText // Custom button text
}) => {
  return (
    <div className="card">
      <div className="card-header">Filters</div>
      <div className="grid grid-3">
        <div className="form-group">
          <label className="form-label">Company</label>
          <select
            className="form-select"
            value={filters.company || ''}
            onChange={(e) => onChange('company', e.target.value)}
            disabled={loading}
          >
            <option value="">Select Company</option>
            {companies.map((company) => {
              // Handle both string format and object format
              const companyName = typeof company === 'string' ? company : company.name;
              const companyValue = typeof company === 'string' ? company : company.name;
              return (
                <option key={companyValue} value={companyValue}>
                  {companyName}
                </option>
              );
            })}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">From Date</label>
          <input
            type="date"
            className="form-input"
            value={filters.fromDate}
            onChange={(e) => onChange('fromDate', e.target.value)}
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label className="form-label">To Date</label>
          <input
            type="date"
            className="form-input"
            value={filters.toDate}
            onChange={(e) => onChange('toDate', e.target.value)}
            disabled={loading}
          />
        </div>
      </div>

      <div style={{ 
        marginTop: '20px', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        gap: '15px',
        flexWrap: 'wrap'
      }}>
        {/* Get Report Button */}
        <button
          className="btn btn-primary"
          onClick={onGetReport}
          disabled={loading || !filters.company || !filters.fromDate || !filters.toDate}
          style={{ 
            minWidth: '200px', 
            fontSize: '15px', 
            padding: '12px 24px',
            background: reportType === 'balance-sheet' 
              ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
              : reportType === 'pl-report'
              ? 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
              : undefined
          }}
        >
          {loading ? 'Loading...' : (buttonText || '📊 Get Report')}
        </button>
        
        {/* Report Type Toggle Buttons - Only show if onReportChange is provided (combined view) */}
        {onReportChange && (
          <div style={{ 
            display: 'flex', 
            gap: '8px',
            border: '2px solid #e0e0e0',
            borderRadius: '8px',
            padding: '4px',
            background: '#f5f5f5'
          }}>
            <button
              onClick={() => onReportChange('balance-sheet')}
              disabled={loading}
              style={{
                padding: '10px 20px',
                fontSize: '14px',
                fontWeight: '600',
                border: 'none',
                borderRadius: '6px',
                background: activeReport === 'balance-sheet' 
                  ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' 
                  : 'transparent',
                color: activeReport === 'balance-sheet' ? 'white' : '#666',
                cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'all 0.3s ease',
                opacity: loading ? 0.5 : 1
              }}
            >
              📊 Balance Sheet
            </button>
            <button
              onClick={() => onReportChange('pl-report')}
              disabled={loading}
              style={{
                padding: '10px 20px',
                fontSize: '14px',
                fontWeight: '600',
                border: 'none',
                borderRadius: '6px',
                background: activeReport === 'pl-report' 
                  ? 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' 
                  : 'transparent',
                color: activeReport === 'pl-report' ? 'white' : '#666',
                cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'all 0.3s ease',
                opacity: loading ? 0.5 : 1
              }}
            >
              📈 P&L Report
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Filters;


