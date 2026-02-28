import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCompanies, getComprehensiveDashboardData, createPublicLink, getPublicLinks, revokePublicLink } from '../api/categoryAnalyticsApi';
import { getDefaultDateRange } from '../utils/formatters';
import { generateComprehensiveHTML, downloadHTMLFile } from '../utils/htmlExport';
import Filters from '../components/Filters';
import SummaryCards from '../components/SummaryCards';
import TrendChart from '../components/TrendChart';
import CategoryDistributionToggle from '../components/CategoryDistributionToggle';
import CategoryTrends from '../components/CategoryTrends';
import VolatilityAnalysis from '../components/VolatilityAnalysis';
import YoYComparison from '../components/YoYComparison';
import CategoryManagement from './CategoryManagement';
import ReportNavigation from '../components/ReportNavigation';
import '../index.css';

function PLReport() {
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

    console.log('🔵 [PLReport Init] Full hash:', hash);
    console.log('🔵 [PLReport Init] Query string:', queryString);
    console.log('🔵 [PLReport Init] Public token found:', publicToken);

    if (publicToken) {
      // This is a public view
      console.log('🟢 [PLReport] Entering PUBLIC VIEW mode');
      setIsPublicView(true);
      window.public_token = publicToken;
      window.is_public_view = true;
      loadData(); // Auto-load data in public view
    } else {
      // Normal authenticated view
      console.log('🔴 [PLReport] Entering AUTHENTICATED mode');
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
      
      console.log('🟢 [PLReport] Data loaded:', result);
      
      // If this is public view, update filters from the response
      if (isPublicView && result) {
        console.log('🟢 [PLReport] Public view - updating filters from response');
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
      console.error('🔴 [PLReport] Error loading data:', err);
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
        'pl-report' // Specify report type
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
      const links = await getPublicLinks('pl-report');
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
      alert('⚠️ Please load the P&L data first by clicking "Get P&L"');
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
        'pl-report'
      );
      
      // Download the file
      const filename = `HKM_PL_Report_${filters.company.replace(/\s+/g, '_')}_${filters.fromDate}_to_${filters.toDate}.html`;
      downloadHTMLFile(htmlContent, filename);
      
      alert('✅ P&L HTML export successful!');
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
    // Don't auto-reload - let user click "Get P&L" button when ready
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
          <h1 className="header-title">🔗 Manage P&L Links</h1>
          <p className="header-subtitle">View and manage all your public P&L report links</p>
          <div className="header-actions">
            <button
              className="btn btn-secondary"
              onClick={() => {
                setView('dashboard');
                loadData();
              }}
            >
              ← Back to P&L Report
            </button>
          </div>
        </div>

        <div className="card">
          {publicLinks.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '60px 20px', color: '#999' }}>
              <div style={{ fontSize: '48px', marginBottom: '20px' }}>🔗</div>
              <h3>No Public Links Yet</h3>
              <p>Create a public link from the P&L report to share</p>
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
          background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
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
        <h1 className="header-title">📈 Profit & Loss Report</h1>
        <p className="header-subtitle">
          Comprehensive P&L analysis with Income, Expenses & Profitability
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
                background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                border: 'none'
              }}
            >
              🔗 Share P&L
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
          reportType="pl-report"
          buttonText="Get P&L Report"
        />
      )}

      {/* Show read-only filter info in public view */}
      {isPublicView && filters.company && (
        <div className="card" style={{ 
          background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
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
          <p>Loading P&L data...</p>
        </div>
      )}

      {error && (
        <div className="error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {!data && !loading && !error && (
        <div className="card" style={{ textAlign: 'center', padding: '60px 20px' }}>
          <div style={{ fontSize: '48px', marginBottom: '20px' }}>📈</div>
          <h2 style={{ marginBottom: '10px', color: '#2c3e50' }}>Ready to Generate P&L Report</h2>
          <p style={{ color: '#7f8c8d' }}>
            Select your filters above and click "Get P&L Report" to view the analysis.
          </p>
        </div>
      )}

      {!loading && !error && data && (
        <div className="pl-report">
          <div style={{
            background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
            padding: '20px 30px',
            borderRadius: '12px',
            marginBottom: '20px',
            boxShadow: '0 4px 15px rgba(245, 87, 108, 0.3)'
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
              📈 Profit & Loss Analysis
            </h2>
            <p style={{
              color: 'rgba(255,255,255,0.9)',
              margin: '8px 0 0 0',
              fontSize: '14px'
            }}>
              Income, Expenses & Profitability for {filters.company}
            </p>
          </div>

          <SummaryCards summary={data.summary} />

          <TrendChart
            data={data}
            filters={filters}
          />

          <CategoryDistributionToggle
            incomeData={data.income_data}
            expenseData={data.expense_data}
            filters={filters}
          />

          <CategoryTrends
            data={data}
            filters={filters}
          />

          <VolatilityAnalysis
            incomeStats={data.income_stats}
            expenseStats={data.expense_stats}
          />

          <YoYComparison
            comparison={data.yoy_comparison}
          />
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
              🔗 Public P&L Link Created!
            </h2>

            <div style={{ marginBottom: '20px' }}>
              <p style={{ color: '#666', marginBottom: '10px' }}>
                Share this link to give read-only access to this P&L Report:
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
                    background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
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
                • Anyone with this link can view the P&L Report (read-only)<br/>
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

export default PLReport;