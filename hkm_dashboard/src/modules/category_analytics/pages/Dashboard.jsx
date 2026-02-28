import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCompanies, getComprehensiveDashboardData, createPublicLink, getPublicLinks, revokePublicLink } from '../api/categoryAnalyticsApi';
import { getDefaultDateRange } from '../utils/formatters';
import { generateComprehensiveHTML, downloadHTMLFile } from '../utils/htmlExport';
import Filters from '../components/Filters';
import SummaryCards from '../components/SummaryCards';
import BalanceSheetSummary from '../components/BalanceSheetSummary';
import AssetDistribution from '../components/AssetDistribution';
import LiabilityDistribution from '../components/LiabilityDistribution';
import CategoryManagement from './CategoryManagement';
import ReportNavigation from '../components/ReportNavigation';
import '../index.css';

function Dashboard() {
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
  const [isLoadingData, setIsLoadingData] = useState(false); // Prevent concurrent loads

  const defaultDates = getDefaultDateRange();
  const [filters, setFilters] = useState({
    company: 'Hare Krishna Movement Jaipur',
    fromDate: defaultDates.fromDate,
    toDate: defaultDates.toDate,
  });

  // Load companies on mount and check if public view
  useEffect(() => {
    // Check if this is a public view
    const urlParams = new URLSearchParams(window.location.search);
    const publicToken = urlParams.get('public_token');

    if (publicToken) {
      // This is a public view
      setIsPublicView(true);
      window.public_token = publicToken;
      window.is_public_view = true;
      loadData(); // Auto-load data in public view
    } else if (typeof window !== 'undefined' && window.is_public_view) {
      setIsPublicView(true);
      loadData(); // Auto-load data in public view
    } else {
      loadCompanies();
    }
  }, []);

  const loadCompanies = async () => {
    console.log('🟡 [Dashboard] loadCompanies called');
    try {
      console.log('🟡 [Dashboard] Calling getCompanies API...');
      const companiesList = await getCompanies();
      console.log('🟡 [Dashboard] Companies received:', companiesList);
      
      setCompanies(companiesList || []);
      console.log('🟡 [Dashboard] Companies state updated');
      
      // Validate default company exists in the list
      if (filters.company && companiesList && companiesList.length > 0) {
        console.log('🟡 [Dashboard] Validating default company:', filters.company);
        const companyExists = companiesList.some(
          company => (typeof company === 'string' ? company : company.name) === filters.company
        );
        console.log('🟡 [Dashboard] Company exists:', companyExists);
        
        if (!companyExists) {
          // Reset company if default doesn't exist
          console.warn('🟡 [Dashboard] Default company not found, resetting');
          setFilters(prev => ({ ...prev, company: '' }));
          setError('Default company not found. Please select a company.');
        }
      } else {
        console.log('🟡 [Dashboard] No companies or no default company to validate');
      }
    } catch (err) {
      console.error('🔴 [Dashboard] Error in loadCompanies:', err);
      const errorMsg = err?.response?.data?.message || err?.message || 'Failed to load companies list';
      console.error('🔴 [Dashboard] Error message:', errorMsg);
      setError(errorMsg);
      // Don't block the UI - set empty array so user can still see the page
      setCompanies([]);
    }
  };

  const loadData = async () => {
    // Prevent concurrent loads
    if (isLoadingData) {
      console.log('Data load already in progress, skipping...');
      return;
    }

    // In public view, we don't need filters since they come from the token
    if (!isPublicView && (!filters.company || !filters.fromDate || !filters.toDate)) {
      setError('Please select company and date range');
      setLoading(false);
      return;
    }

    setIsLoadingData(true);
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
      
      console.log('🟢 [Dashboard] Data loaded:', result);
      
      // If this is public view, update filters from the response
      if (isPublicView && result) {
        console.log('🟢 [Dashboard] Public view - updating filters from response');
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
      const errorMessage = err?.response?.data?.message || err?.message || 'Failed to load data';
      setError(errorMessage);
      console.error('🔴 [Dashboard] Error loading data:', err);
      // Log full error details for debugging
      if (err?.response) {
        console.error('🔴 [Dashboard] API Error Response:', err.response);
      }
    } finally {
      // Always clear loading state, even if there's an error
      setIsLoadingData(false);
      setLoading(false);
    }
  };

  const handleFilterChange = (name, value) => {
    setFilters(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleExportHTML = async () => {
    if (!filters.company || !filters.fromDate || !filters.toDate) {
      alert('⚠️ Please select company and date range first');
      return;
    }

    if (!data) {
      alert('⚠️ Please load the dashboard data first by clicking "Get Dashboard"');
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
        null // Combined report
      );
      
      // Download the file
      const filename = `hkm.api.hkm_dashboard_${filters.company.replace(/\s+/g, '_')}_${filters.fromDate}_to_${filters.toDate}.html`;
      downloadHTMLFile(htmlContent, filename);
      
      alert('✅ Export successful!');
    } catch (error) {
      console.error('Export failed:', error);
      alert('❌ Export failed: ' + (error.message || 'Please try again'));
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePublicLink = async () => {
    if (!filters.company || !filters.fromDate || !filters.toDate) {
      alert('⚠️ Please select company and date range first');
      return;
    }

    try {
      setLoading(true);

      // Create public link - backend will fetch the data using filters
      const result = await createPublicLink(filters.company, filters.fromDate, filters.toDate, 30);
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
      const links = await getPublicLinks();
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

  const handleCopyPublicLink = () => {
    if (publicLinkData && publicLinkData.public_url) {
      navigator.clipboard.writeText(publicLinkData.public_url);
      alert('✅ Link copied to clipboard!');
    }
  };

  const handleCategoryManagementComplete = () => {
    setView('dashboard');
    loadData(); // Reload data with updated categories
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
          <h1 className="header-title">🔗 Manage Public Links</h1>
          <p className="header-subtitle">View and manage all your public dashboard links</p>
          <div className="header-actions">
            <button
              className="btn btn-secondary"
              onClick={() => {
                setView('dashboard');
                loadData();
              }}
            >
              ← Back to Dashboard
            </button>
          </div>
        </div>

        <div className="card">
          {publicLinks.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '60px 20px', color: '#999' }}>
              <div style={{ fontSize: '48px', marginBottom: '20px' }}>🔗</div>
              <h3>No Public Links Yet</h3>
              <p>Create a public link from the dashboard to share your reports</p>
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
      <div className="header">
        <h1 className="header-title">🎯 HKM Category Analytics</h1>
        <p className="header-subtitle">
          Comprehensive financial analysis with category management and volatility tracking
        </p>
        {!isPublicView && (
          <div className="header-actions">
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
              🔗 Share
            </button>
          </div>
        )}
      </div>

      {/* Report Navigation */}
      <ReportNavigation />

      {!isPublicView && (
        <Filters
          filters={filters}
          companies={companies}
          onChange={handleFilterChange}
          onGetReport={loadData}
          loading={loading}
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
          <p>Loading financial data...</p>
        </div>
      )}

      {error && (
        <div className="error" style={{
          padding: '20px',
          margin: '20px',
          background: '#ffebee',
          border: '2px solid #f44336',
          borderRadius: '8px',
          color: '#c62828'
        }}>
          <strong style={{ fontSize: '18px', display: 'block', marginBottom: '10px' }}>⚠️ Error:</strong>
          <div style={{ fontSize: '14px', lineHeight: '1.6' }}>{error}</div>
          <button
            onClick={() => {
              setError(null);
              console.clear();
            }}
            style={{
              marginTop: '10px',
              padding: '8px 16px',
              background: '#f44336',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Dismiss
          </button>
        </div>
      )}

      {!data && !loading && !error && (
        <div className="card" style={{ textAlign: 'center', padding: '60px 20px' }}>
          <div style={{ fontSize: '48px', marginBottom: '20px' }}>📊</div>
          <h2 style={{ marginBottom: '10px', color: '#2c3e50' }}>Ready to Generate Report</h2>
          <p style={{ color: '#7f8c8d' }}>
            Select your filters above and click "Get Report" to view the category analytics.
          </p>
        </div>
      )}

      {!loading && !error && data && (
        <>
          {/* Dashboard Overview */}
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
              📊 Financial Overview
            </h2>
            <p style={{
              color: 'rgba(255,255,255,0.9)',
              margin: '8px 0 0 0',
              fontSize: '14px'
            }}>
              Summary of key financial metrics for {filters.company}
            </p>
          </div>

          {/* Key Summary Cards */}
          {data.summary && <SummaryCards summary={data.summary} />}

          {/* Balance Sheet Overview */}
          {data.balance_sheet_data && data.balance_sheet_data.summary && (
            <div style={{ marginTop: '20px' }}>
              <BalanceSheetSummary summary={data.balance_sheet_data.summary} />
            </div>
          )}

          {/* Asset and Liability Overview */}
          {data.balance_sheet_data && (
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
          )}

          {/* Navigation to Detailed Reports */}
          <div style={{ marginTop: '30px', textAlign: 'center' }}>
            <div style={{
              background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
              padding: '30px',
              borderRadius: '12px',
              border: '1px solid #e0e6ed'
            }}>
              <h3 style={{ marginBottom: '15px', color: '#2c3e50' }}>
                📈 Access Detailed Reports
              </h3>
              <p style={{ color: '#7f8c8d', marginBottom: '20px' }}>
                Get comprehensive analysis with charts, trends, and insights
              </p>
              <div style={{
                display: 'flex',
                gap: '15px',
                justifyContent: 'center',
                flexWrap: 'wrap'
              }}>
                <button
                  onClick={() => navigate('/category-analytics/balance-sheet')}
                  style={{
                    padding: '12px 24px',
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontWeight: '600',
                    fontSize: '14px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                >
                  📊 Balance Sheet Report
                </button>
                <button
                  onClick={() => navigate('/category-analytics/pl-report')}
                  style={{
                    padding: '12px 24px',
                    background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontWeight: '600',
                    fontSize: '14px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                >
                  📈 P&L Report
                </button>
              </div>
            </div>
          </div>
        </>
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
              🔗 Public Link Created Successfully!
            </h2>

            <div style={{ marginBottom: '20px' }}>
              <p style={{ color: '#666', marginBottom: '10px' }}>
                Share this link with anyone to give them read-only access to this dashboard:
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
              background: '#e3f2fd',
              padding: '15px',
              borderRadius: '8px',
              marginBottom: '20px'
            }}>
              <p style={{ margin: 0, fontSize: '13px', color: '#1565c0' }}>
                <strong>ℹ️ Important:</strong><br/>
                • This link will expire in {publicLinkData.expires_in_days} days<br/>
                • Anyone with this link can view the dashboard (read-only)<br/>
                • No login required for viewers<br/>
                • Expiry: {new Date(publicLinkData.expires_at).toLocaleString()}
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

export default Dashboard;
