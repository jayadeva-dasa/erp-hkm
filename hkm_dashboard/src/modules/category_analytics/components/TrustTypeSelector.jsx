import React, { useState, useEffect } from 'react';
import { getCompaniesByTrustType } from '../api/categoryAnalyticsApi';
import './TrustTypeSelector.css';

export default function TrustTypeSelector({ onSelect, currentCompany }) {
  const [trustTypes, setTrustTypes] = useState({
    charitable: [],
    religious: [],
    business: [],
    other: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTrustTypes();
  }, []);

  const loadTrustTypes = async () => {
    try {
      setLoading(true);
      const data = await getCompaniesByTrustType();
      setTrustTypes(data);
    } catch (error) {
      console.error('Error loading trust types:', error);
    } finally {
      setLoading(false);
    }
  };

  const TrustCard = ({ type, icon, title, companies, color }) => {
    if (!companies || companies.length === 0) return null;

    return (
      <div className="trust-card" style={{ borderColor: color }}>
        <div className="trust-card-header" style={{ background: color }}>
          <span className="trust-icon">{icon}</span>
          <h3>{title}</h3>
        </div>
        <div className="trust-card-body">
          <p className="trust-count">{companies.length} {companies.length === 1 ? 'Company' : 'Companies'}</p>
          <div className="company-list">
            {companies.map((company) => (
              <button
                key={company.name}
                className={`company-button ${currentCompany === company.name ? 'active' : ''}`}
                onClick={() => onSelect(company.name, type)}
              >
                <span className="company-name">{company.name}</span>
                <span className="company-abbr">{company.abbr}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="trust-selector-loading">
        <div className="loading-spinner"></div>
        <p>Loading trust types...</p>
      </div>
    );
  }

  const hasAnyCompanies = 
    trustTypes.charitable.length > 0 ||
    trustTypes.religious.length > 0 ||
    trustTypes.business.length > 0;

  if (!hasAnyCompanies) {
    return (
      <div className="trust-selector-empty">
        <h3>No Trust Types Configured</h3>
        <p>Please configure trust types for your companies in Company master.</p>
      </div>
    );
  }

  return (
    <div className="trust-type-selector">
      <div className="trust-selector-header">
        <h2>🏛️ Select Trust Type</h2>
        <p>Choose a company to view its financial analytics</p>
      </div>

      <div className="trust-cards-grid">
        <TrustCard
          type="charitable"
          icon="🤲"
          title="Charitable Trust"
          companies={trustTypes.charitable}
          color="#4CAF50"
        />

        <TrustCard
          type="religious"
          icon="🕉️"
          title="Religious Trust"
          companies={trustTypes.religious}
          color="#FF9800"
        />

        <TrustCard
          type="business"
          icon="💼"
          title="Business Trust"
          companies={trustTypes.business}
          color="#2196F3"
        />
      </div>

      {trustTypes.other && trustTypes.other.length > 0 && (
        <div className="other-companies">
          <h4>Other Companies</h4>
          <div className="company-list">
            {trustTypes.other.map((company) => (
              <button
                key={company.name}
                className={`company-button ${currentCompany === company.name ? 'active' : ''}`}
                onClick={() => onSelect(company.name, 'other')}
              >
                <span className="company-name">{company.name}</span>
                <span className="company-abbr">{company.abbr}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="trust-selector-footer">
        <button 
          className="consolidated-view-button"
          onClick={() => onSelect('all', 'consolidated')}
        >
          📊 View Consolidated (All Trusts)
        </button>
      </div>
    </div>
  );
}




