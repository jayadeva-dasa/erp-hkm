import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCompanies, getComprehensiveDashboardData, createPublicLink, getPublicLinks, revokePublicLink } from '../api/categoryAnalyticsApi';
import { getDefaultDateRange } from '../utils/formatters';
import { generateComprehensiveHTML, downloadHTMLFile } from '../utils/htmlExport';
import Filters from '../components/Filters';
import BalanceSheetSummary from '../components/BalanceSheetSummary';
import AssetDistribution from '../components/AssetDistribution';
import LiabilityDistribution from '../components/LiabilityDistribution';
import BalanceSheetCategoryTrends from '../components/BalanceSheetCategoryTrends';
import BalanceSheetTrends from '../components/BalanceSheetTrends';
import CategoryManagement from './CategoryManagement';
import ReportNavigation from '../components/ReportNavigation';
import '../index.css';

function BalanceSheetReport() {
  const navigate = useNavigate();
  const [view, setView] = useState('dashboard'); // 'dashboard', 'manage-categories', or 'manage-links'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [companies, setCompanies] = useState([]);
  const [showPublicLinkModal, setShowPublicLinkModal] = useState(false);
  const [publicLinkData, setPublicLinkData] = useState(null);
  const [isPublicView, setIsPublicView] = useState(false);
  const [publicLinks, setPublicLinks] = useState([]);

  const defaultDates = getDefaultDateRange();
  const [filters, setFilters] = useState({
    company: 'Hare Krishna Movement Jaipur',
    fromDate: defaultDates.fromDate,
    toDate: defaultDates.toDate,
  });

  // Load companies on mount and check if public view
  useEffect(() => {
    // Check if this is a public view by looking for public_token in URL
    // With HashRouter, params are in the hash part: #/route?param=value
    const hash = window.location.hash; // e.g., #/category-analytics/pl-report?public_token=xyz
    const hashParts = hash.split('?');
    const queryString = hashParts.length > 1 ? hashParts[1] : '';
    const urlParams = new URLSearchParams(queryString);
    const publicToken = urlParams.get('public_token');

    console.log('🔵 [BalanceSheet Init] Full hash:', hash);
    console.log('🔵 [BalanceSheet Init] Query string:', queryString);
    console.log('🔵 [BalanceSheet Init] Public token found:', publicToken);

    if (publicToken) {
      // This is a public view
      console.log('🟢 [BalanceSheet] Entering PUBLIC VIEW mode');
      setIsPublicView(true);
      window.public_token = publicToken;
      window.is_public_view = true;
      loadData(); // Auto-load data in public view
    } else {
      // Normal authenticated view
      console.log('🔴 [BalanceSheet] Entering AUTHENTICATED mode');
      loadCompanies();
    }
  }, []);

  const loadCompanies = async () => {
    try {
      const companiesList = await getCompanies();
      setCompanies(companiesList || []);
    } catch (err) {
      console.error('Error loading companies:', err);
    }
  };

  const loadData = async () => {
    // In public view, we don't need filters since they come from the token
    if (!isPublicView && (!filters.company || !filters.fromDate || !filters.toDate)) {
      setError('Please select company and date range');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // In public mode, don't pass parameters - API will get them from token
      // In authenticated mode, pass filters
      const result = isPublicView 
        ? await getComprehensiveDashboardData()
        : await getComprehensiveDashboardData(
            filters.company,
            filters.fromDate,
            filters.toDate
          );
      
      console.log('🟢 [BalanceSheet] Data loaded:', result);
      
      // If this is public view, update filters from the response
      if (isPublicView && result) {
        console.log('🟢 [BalanceSheet] Public view - updating filters from response');
        if (result.company || result.from_date || result.to_date) {
          setFilters({
            company: result.company || 'N/A',
            fromDate: result.from_date || '',
            toDate: result.to_date || '',
          });
        }
      }
      
      setData(result);
    } catch (err) {
      setError(err.message || 'Failed to load data');
      console.error('🔴 [BalanceSheet] Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (name, value) => {
    setFilters(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleCreatePublicLink = async () => {
    if (!filters.company || !filters.fromDate || !filters.toDate) {
      alert('⚠️ Please select company and date range first');
      return;
    }

    try {
      setLoading(true);

      // Create public link with report_type parameter
      // Note: We don't need to load data first - the backend will fetch it using the filters
      const result = await createPublicLink(
        filters.company,
        filters.fromDate,
        filters.toDate,
        30,
        'balance-sheet' // Specify report type
      );
      setPublicLinkData(result);
      setShowPublicLinkModal(true);
    } catch (error) {
      console.error('Failed to create public link:', error);
      alert('❌ Failed to create public link. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const loadPublicLinks = async () => {
    try {
      const links = await getPublicLinks('balance-sheet');
      setPublicLinks(Array.isArray(links) ? links : []);
    } catch (error) {
      console.error('Error loading public links:', error);
      // Set empty array to prevent UI issues
      setPublicLinks([]);
      // Show user-friendly error message
      const errorMsg = error?.response?.data?.message || error?.message || 'Failed to load public links';
      console.error('Public links error:', errorMsg);
    }
  };

  const handleRevokeLink = async (token) => {
    if (!confirm('Are you sure you want to revoke this public link?')) {
      return;
    }

    try {
      await revokePublicLink(token);
      alert('✅ Link revoked successfully');
      loadPublicLinks(); // Reload the list
    } catch (error) {
      console.error('Error revoking link:', error);
      alert('❌ Failed to revoke link');
    }
  };

  const handleExportHTML = async () => {
    if (!filters.company || !filters.fromDate || !filters.toDate) {
      alert('⚠️ Please select company and date range first');
      return;
    }

    if (!data) {
      alert('⚠️ Please load the Balance Sheet data first by clicking "Get Balance Sheet"');
      return;
    }

    try {
      setLoading(true);

      // Generate HTML using frontend-only approach with already loaded data
      const htmlContent = generateComprehensiveHTML(
        data,
        filters.company,
        filters.fromDate,
        filters.toDate,
        'balance-sheet'
      );
      
      // Download the file
      const filename = `HKM_Balance_Sheet_${filters.company.replace(/\s+/g, '_')}_${filters.fromDate}_to_${filters.toDate}.html`;
      downloadHTMLFile(htmlContent, filename);
      
      alert('✅ Balance Sheet HTML export successful!');
    } catch (error) {
      console.error('Export failed:', error);
      alert('❌ Export failed: ' + (error.message || 'Please try again'));
    } finally {
      setLoading(false);
    }
  };

  const handleCopyPublicLink = () => {
    if (publicLinkData && publicLinkData.public_url) {
      navigator.clipboard.writeText(publicLinkData.public_url);
      alert('✅ Link copied to clipboard!');
    }
  };

  const handleCategoryManagementComplete = () => {
    setView('dashboard');
    // Don't auto-reload - let user click "Get Balance Sheet" button when ready
  };

  if (view === 'manage-categories') {
    return (
      <CategoryManagement
        company={filters.company}
        onBack={handleCategoryManagementComplete}
      />
    );
  }

  if (view === 'manage-links') {
    return (
      <div className="container">
        <div className="header">
          <h1 className="header-title">🔗 Manage Balance Sheet Links</h1>
          <p className="header-subtitle">View and manage all your public Balance Sheet links</p>
          <div className="header-actions">
            <button
              className="btn btn-secondary"
              onClick={() => {
                setView('dashboard');
                loadData();
              }}
            >
              ← Back to Balance Sheet
            </button>
          </div>
        </div>

        <div className="card">
          {publicLinks.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '60px 20px', color: '#999' }}>
              <div style={{ fontSize: '48px', marginBottom: '20px' }}>🔗</div>
              <h3>No Public Links Yet</h3>
              <p>Create a public link from the Balance Sheet report to share</p>
            </div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: '#f5f5f5', borderBottom: '2px solid #e0e0e0' }}>
                  <th style={{ padding: '15px', textAlign: 'left' }}>Company</th>
                  <th style={{ padding: '15px', textAlign: 'left' }}>Date Range</th>
                  <th style={{ padding: '15px', textAlign: 'left' }}>Created</th>
                  <th style={{ padding: '15px', textAlign: 'left' }}>Expires</th>
                  <th style={{ padding: '15px', textAlign: 'center' }}>Status</th>
                  <th style={{ padding: '15px', textAlign: 'center' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {publicLinks.map((link) => (
                  <tr key={link.token} style={{ borderBottom: '1px solid #f0f0f0' }}>
                    <td style={{ padding: '12px 15px' }}>{link.company}</td>
                    <td style={{ padding: '12px 15px' }}>
                      {link.from_date} to {link.to_date}
                    </td>
                    <td style={{ padding: '12px 15px', fontSize: '13px', color: '#666' }}>
                      {link.created_at ? new Date(link.created_at).toLocaleDateString() : 'N/A'}
                    </td>
                    <td style={{ padding: '12px 15px', fontSize: '13px', color: '#666' }}>
                      {link.expires_at ? new Date(link.expires_at).toLocaleDateString() : 'N/A'}
                    </td>
                    <td style={{ padding: '12px 15px', textAlign: 'center' }}>
                      <span style={{
                        padding: '4px 12px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        fontWeight: '600',
                        background: link.is_expired ? '#ffcdd2' : '#c8e6c9',
                        color: link.is_expired ? '#c62828' : '#2e7d32'
                      }}>
                        {link.status}
                      </span>
                    </td>
                    <td style={{ padding: '12px 15px', textAlign: 'center' }}>
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(link.public_url);
                          alert('✅ Link copied!');
                        }}
                        style={{
                          padding: '6px 12px',
                          background: '#2196F3',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          marginRight: '8px',
                          fontSize: '13px'
                        }}
                      >
                        📋 Copy
                      </button>
                      <button
                        onClick={() => handleRevokeLink(link.token)}
                        style={{
                          padding: '6px 12px',
                          background: '#f44336',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '13px'
                        }}
                      >
                        🗑️ Revoke
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      {isPublicView && (
        <div style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          padding: '12px 20px',
          textAlign: 'center',
          fontSize: '14px',
          fontWeight: '500',
          marginBottom: '20px',
          borderRadius: '8px'
        }}>
          📊 Public View - Read Only Access
        </div>
      )}

      <div className="header">
        <h1 className="header-title">🎯 HKM Financial Reports</h1>
        <p className="header-subtitle">
          Comprehensive Balance Sheet and P&L analysis with category management
        </p>
      </div>

      {/* Report Navigation */}
      <ReportNavigation />

      <div className="header">
        <h1 className="header-title">📊 Balance Sheet Report</h1>
        <p className="header-subtitle">
          Comprehensive Balance Sheet analysis with Assets, Liabilities & Financial Position
        </p>

        {!isPublicView && (
          <div className="header-actions" style={{ marginTop: '20px' }}>
            <button
              className="btn btn-warning"
              onClick={() => setView('manage-categories')}
              disabled={!filters.company || loading}
            >
              ⚙️ Manage Categories
            </button>
            <button
              className="btn btn-info"
              onClick={() => {
                setView('manage-links');
                loadPublicLinks();
              }}
              disabled={loading}
              style={{
                background: '#00bcd4',
                color: 'white'
              }}
            >
              🔗 Manage Links
            </button>
            <button
              className="btn btn-secondary"
              onClick={handleExportHTML}
              disabled={!filters.company || !filters.fromDate || !filters.toDate || loading}
            >
              📊 Export HTML
            </button>
            <button
              className="btn btn-primary"
              onClick={handleCreatePublicLink}
              disabled={!filters.company || !filters.fromDate || !filters.toDate || loading}
              style={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                border: 'none'
              }}
            >
              🔗 Share Balance Sheet
            </button>
          </div>
        )}
      </div>

      {!isPublicView && (
        <Filters
          filters={filters}
          companies={companies}
          onChange={handleFilterChange}
          onGetReport={loadData}
          loading={loading}
          reportType="balance-sheet"
          buttonText="Get Balance Sheet"
        />
      )}

      {/* Show read-only filter info in public view */}
      {isPublicView && filters.company && (
        <div className="card" style={{ 
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          padding: '20px',
          marginBottom: '20px',
          borderRadius: '8px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '15px', flexWrap: 'wrap' }}>
            <div style={{ flex: '1', minWidth: '200px' }}>
              <div style={{ fontSize: '12px', opacity: 0.9, marginBottom: '5px' }}>Company</div>
              <div style={{ fontSize: '16px', fontWeight: '600' }}>{filters.company}</div>
            </div>
            <div style={{ flex: '1', minWidth: '200px' }}>
              <div style={{ fontSize: '12px', opacity: 0.9, marginBottom: '5px' }}>Date Range</div>
              <div style={{ fontSize: '16px', fontWeight: '600' }}>
                {filters.fromDate} to {filters.toDate}
              </div>
            </div>
          </div>
        </div>
      )}

      {loading && (
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>Loading Balance Sheet data...</p>
        </div>
      )}

      {error && (
        <div className="error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {!data && !loading && !error && (
        <div className="card" style={{ textAlign: 'center', padding: '60px 20px' }}>
          <div style={{ fontSize: '48px', marginBottom: '20px' }}>📊</div>
          <h2 style={{ marginBottom: '10px', color: '#2c3e50' }}>Ready to Generate Balance Sheet</h2>
          <p style={{ color: '#7f8c8d' }}>
            Select your filters above and click "Get Balance Sheet" to view the report.
          </p>
        </div>
      )}

      {!loading && !error && data && data.balance_sheet_data && (
        <div className="balance-sheet-report">
          <div style={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            padding: '20px 30px',
            borderRadius: '12px',
            marginBottom: '20px',
            boxShadow: '0 4px 15px rgba(102, 126, 234, 0.3)'
          }}>
            <h2 style={{
              color: 'white',
              margin: 0,
              fontSize: '24px',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              gap: '10px'
            }}>
              📊 Balance Sheet Analysis
            </h2>
            <p style={{
              color: 'rgba(255,255,255,0.9)',
              margin: '8px 0 0 0',
              fontSize: '14px'
            }}>
              Assets, Liabilities & Financial Position for {filters.company}
            </p>
          </div>

          {/* Balance Sheet Summary Cards */}
          <BalanceSheetSummary
            summary={data.balance_sheet_data.summary || {}}
          />

          {/* Asset and Liability Distribution Pie Charts */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))',
            gap: '20px',
            marginTop: '20px'
          }}>
            <AssetDistribution
              assets={data.balance_sheet_data.assets || {}}
              filters={filters}
            />
            <LiabilityDistribution
              liabilities={data.balance_sheet_data.liabilities || {}}
              filters={filters}
            />
          </div>

          {/* Category-wise Movement Analysis */}
          <BalanceSheetCategoryTrends
            assets={data.balance_sheet_data.assets || {}}
            liabilities={data.balance_sheet_data.liabilities || {}}
            periods={data.balance_sheet_data.periods || []}
            filters={filters}
          />

          {/* Balance Sheet Trends */}
          {data.balance_sheet_data.periods && data.balance_sheet_data.periods.length > 1 && (
            <BalanceSheetTrends
              data={data.balance_sheet_data}
              filters={filters}
            />
          )}

          {/* Financial Ratios */}
          {data.financial_ratios && Object.keys(data.financial_ratios).length > 0 && (
            <div className="card" style={{ marginTop: '20px' }}>
              <div className="card-header">
                📊 Financial Ratios & Indicators
              </div>
              <div style={{ padding: '20px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px' }}>
                {/* Current Ratio */}
                {data.financial_ratios.current_ratio !== null && data.financial_ratios.current_ratio !== undefined && (
                  <div style={{ padding: '15px', background: '#f5f5f5', borderRadius: '8px' }}>
                    <div style={{ fontSize: '12px', color: '#666', marginBottom: '5px' }}>Current Ratio</div>
                    <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#667eea' }}>
                      {data.financial_ratios.current_ratio.toFixed(2)}
                    </div>
                    <div style={{ fontSize: '11px', color: '#999', marginTop: '5px' }}>
                      Current Assets / Current Liabilities
                    </div>
                  </div>
                )}

                {/* Quick Ratio */}
                {data.financial_ratios.quick_ratio !== null && data.financial_ratios.quick_ratio !== undefined && (
                  <div style={{ padding: '15px', background: '#f5f5f5', borderRadius: '8px' }}>
                    <div style={{ fontSize: '12px', color: '#666', marginBottom: '5px' }}>Quick Ratio</div>
                    <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#4caf50' }}>
                      {data.financial_ratios.quick_ratio.toFixed(2)}
                    </div>
                    <div style={{ fontSize: '11px', color: '#999', marginTop: '5px' }}>
                      (Current Assets × 0.8) / Current Liabilities
                    </div>
                  </div>
                )}

                {/* Debt Ratio */}
                {data.financial_ratios.debt_ratio !== null && data.financial_ratios.debt_ratio !== undefined && (
                  <div style={{ padding: '15px', background: '#f5f5f5', borderRadius: '8px' }}>
                    <div style={{ fontSize: '12px', color: '#666', marginBottom: '5px' }}>Debt Ratio</div>
                    <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#f5576c' }}>
                      {(data.financial_ratios.debt_ratio * 100).toFixed(1)}%
                    </div>
                    <div style={{ fontSize: '11px', color: '#999', marginTop: '5px' }}>
                      Total Liabilities / Total Assets
                    </div>
                  </div>
                )}

                {/* Working Capital */}
                {data.financial_ratios.working_capital !== null && data.financial_ratios.working_capital !== undefined && (
                  <div style={{ padding: '15px', background: '#f5f5f5', borderRadius: '8px' }}>
                    <div style={{ fontSize: '12px', color: '#666', marginBottom: '5px' }}>Working Capital</div>
                    <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ff9800' }}>
                      ₹ {(data.financial_ratios.working_capital / 100000).toFixed(2)}L
                    </div>
                    <div style={{ fontSize: '11px', color: '#999', marginTop: '5px' }}>
                      Current Assets - Current Liabilities
                    </div>
                  </div>
                )}

                {/* ROA */}
                {data.financial_ratios.roa !== null && data.financial_ratios.roa !== undefined && (
                  <div style={{ padding: '15px', background: '#f5f5f5', borderRadius: '8px' }}>
                    <div style={{ fontSize: '12px', color: '#666', marginBottom: '5px' }}>Return on Assets (ROA)</div>
                    <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#9c27b0' }}>
                      {data.financial_ratios.roa.toFixed(2)}%
                    </div>
                    <div style={{ fontSize: '11px', color: '#999', marginTop: '5px' }}>
                      Net Income / Total Assets
                    </div>
                  </div>
                )}

                {/* Debt to Equity */}
                {data.financial_ratios.debt_to_equity !== null && data.financial_ratios.debt_to_equity !== undefined && (
                  <div style={{ padding: '15px', background: '#f5f5f5', borderRadius: '8px' }}>
                    <div style={{ fontSize: '12px', color: '#666', marginBottom: '5px' }}>Debt to Equity</div>
                    <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#e91e63' }}>
                      {data.financial_ratios.debt_to_equity.toFixed(2)}
                    </div>
                    <div style={{ fontSize: '11px', color: '#999', marginTop: '5px' }}>
                      Total Liabilities / Total Equity
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Public Link Modal */}
      {showPublicLinkModal && publicLinkData && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 10000,
            backdropFilter: 'blur(5px)'
          }}
          onClick={() => setShowPublicLinkModal(false)}
        >
          <div
            style={{
              background: 'white',
              borderRadius: '12px',
              padding: '30px',
              maxWidth: '600px',
              width: '90%',
              boxShadow: '0 8px 32px rgba(0,0,0,0.3)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 style={{ marginBottom: '20px', color: '#1a237e' }}>
              🔗 Public Balance Sheet Link Created!
            </h2>

            <div style={{ marginBottom: '20px' }}>
              <p style={{ color: '#666', marginBottom: '10px' }}>
                Share this link to give read-only access to this Balance Sheet:
              </p>

              <div style={{
                background: '#f5f5f5',
                padding: '15px',
                borderRadius: '8px',
                border: '1px solid #e0e0e0',
                marginBottom: '15px',
                wordBreak: 'break-all',
                fontFamily: 'monospace',
                fontSize: '14px'
              }}>
                {publicLinkData.public_url}
              </div>

              <div style={{
                display: 'flex',
                gap: '10px',
                marginBottom: '20px'
              }}>
                <button
                  onClick={handleCopyPublicLink}
                  style={{
                    flex: 1,
                    padding: '12px',
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontWeight: '600',
                    fontSize: '14px'
                  }}
                >
                  📋 Copy Link
                </button>
                <button
                  onClick={() => window.open(publicLinkData.public_url, '_blank')}
                  style={{
                    flex: 1,
                    padding: '12px',
                    background: '#2196F3',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontWeight: '600',
                    fontSize: '14px'
                  }}
                >
                  🔍 Preview
                </button>
              </div>
            </div>

            <div style={{
              background: publicLinkData.is_existing ? '#fff3e0' : '#e3f2fd',
              padding: '15px',
              borderRadius: '8px',
              marginBottom: '20px'
            }}>
              <p style={{ margin: 0, fontSize: '13px', color: publicLinkData.is_existing ? '#e65100' : '#1565c0' }}>
                <strong>{publicLinkData.is_existing ? '♻️ Existing Link' : 'ℹ️ New Link Created'}</strong><br/>
                {publicLinkData.is_existing && '• A link for these filters already exists - reusing it<br/>'}
                • This link will expire in {publicLinkData.expires_in_days} days<br/>
                • Anyone with this link can view the Balance Sheet (read-only)<br/>
                • No login required for viewers<br/>
                • Expiry: {new Date(publicLinkData.expires_at).toLocaleString()}<br/>
                • Manage all links via "🔗 Manage Links" button
              </p>
            </div>

            <button
              onClick={() => setShowPublicLinkModal(false)}
              style={{
                width: '100%',
                padding: '12px',
                background: '#f5f5f5',
                border: '1px solid #e0e0e0',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '14px'
              }}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default BalanceSheetReport;