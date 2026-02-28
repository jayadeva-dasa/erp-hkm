import React, { useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { formatIndianCurrency } from '../utils/formatters';

const BalanceSheetCategoryTrends = ({ assets, liabilities, periods, filters }) => {
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedType, setSelectedType] = useState(null); // 'asset' or 'liability'
  const [showModal, setShowModal] = useState(false);

  if (!assets || !liabilities || !periods || periods.length === 0) {
    return <div>No data available</div>;
  }

  // Calculate total assets and liabilities for each period
  const calculateTotals = (categories) => {
    if (!categories || Object.keys(categories).length === 0) return [];
    
    const firstCategory = Object.values(categories)[0];
    if (!firstCategory || !firstCategory.monthly) return [];
    
    return firstCategory.monthly.map((_, idx) => {
      return Object.values(categories).reduce((sum, cat) => {
        return sum + (cat.monthly && cat.monthly[idx] ? cat.monthly[idx].amount : 0);
      }, 0);
    });
  };

  const totalAssetsByPeriod = calculateTotals(assets);
  const totalLiabilitiesByPeriod = calculateTotals(liabilities);

  // Prepare data for category list
  const assetCategories = Object.entries(assets || {}).map(([name, data]) => ({
    name,
    type: 'asset',
    opening: data.monthly && data.monthly.length > 0 ? data.monthly[0].amount : 0,
    closing: data.monthly && data.monthly.length > 0 ? data.monthly[data.monthly.length - 1].amount : 0,
    change: data.monthly && data.monthly.length > 0 
      ? data.monthly[data.monthly.length - 1].amount - data.monthly[0].amount 
      : 0,
    monthly: data.monthly || [],
    accounts: data.accounts || []
  }));

  const liabilityCategories = Object.entries(liabilities || {}).map(([name, data]) => ({
    name,
    type: 'liability',
    opening: data.monthly && data.monthly.length > 0 ? data.monthly[0].amount : 0,
    closing: data.monthly && data.monthly.length > 0 ? data.monthly[data.monthly.length - 1].amount : 0,
    change: data.monthly && data.monthly.length > 0 
      ? data.monthly[data.monthly.length - 1].amount - data.monthly[0].amount 
      : 0,
    monthly: data.monthly || [],
    accounts: data.accounts || []
  }));

  // Chart for selected category
  const getCategoryTrendChart = () => {
    if (!selectedCategory) return null;

    const categoryData = selectedType === 'asset' 
      ? assets[selectedCategory] 
      : liabilities[selectedCategory];

    if (!categoryData || !categoryData.monthly) return null;

    const option = {
      title: {
        text: `${selectedCategory} - Trend Analysis`,
        left: 'center',
        textStyle: { fontSize: 16, fontWeight: 600 }
      },
      tooltip: {
        trigger: 'axis',
        formatter: (params) => {
          let result = `<strong>${params[0].axisValue}</strong><br/>`;
          params.forEach(param => {
            result += `${param.marker} ${param.seriesName}: ${formatIndianCurrency(param.value)}<br/>`;
          });
          return result;
        }
      },
      legend: {
        data: ['Balance'],
        top: 35
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: 80,
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: categoryData.monthly.map(m => m.month),
        axisLabel: { rotate: 45, fontSize: 11 }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: (value) => {
            if (Math.abs(value) >= 10000000) return `₹${(value / 10000000).toFixed(1)}Cr`;
            if (Math.abs(value) >= 100000) return `₹${(value / 100000).toFixed(1)}L`;
            if (Math.abs(value) >= 1000) return `₹${(value / 1000).toFixed(1)}K`;
            return `₹${value}`;
          }
        }
      },
      series: [
        {
          name: 'Balance',
          type: 'line',
          data: categoryData.monthly.map(m => m.amount),
          smooth: true,
          lineStyle: { width: 3 },
          itemStyle: { color: selectedType === 'asset' ? '#667eea' : '#f5576c' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [{
                offset: 0,
                color: selectedType === 'asset' ? 'rgba(102, 126, 234, 0.3)' : 'rgba(245, 87, 108, 0.3)'
              }, {
                offset: 1,
                color: selectedType === 'asset' ? 'rgba(102, 126, 234, 0.05)' : 'rgba(245, 87, 108, 0.05)'
              }]
            }
          }
        }
      ]
    };

    return <ReactECharts option={option} style={{ height: '400px' }} />;
  };

  // Account details table
  const getAccountDetails = () => {
    if (!selectedCategory) return null;

    const categoryData = selectedType === 'asset' 
      ? assets[selectedCategory] 
      : liabilities[selectedCategory];

    if (!categoryData || !categoryData.accounts || categoryData.accounts.length === 0) {
      return <div style={{ padding: '20px', textAlign: 'center', color: '#999' }}>No accounts in this category</div>;
    }

    return (
      <div style={{ marginTop: '20px' }}>
        <h4 style={{ marginBottom: '15px', fontSize: '15px', fontWeight: 600 }}>Account Details</h4>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ background: '#f5f5f5', borderBottom: '2px solid #ddd' }}>
                <th style={{ padding: '10px', textAlign: 'left', fontWeight: 600 }}>Account</th>
                <th style={{ padding: '10px', textAlign: 'right', fontWeight: 600 }}>Opening</th>
                <th style={{ padding: '10px', textAlign: 'right', fontWeight: 600 }}>Closing</th>
                <th style={{ padding: '10px', textAlign: 'right', fontWeight: 600 }}>Change</th>
                <th style={{ padding: '10px', textAlign: 'right', fontWeight: 600 }}>% Change</th>
              </tr>
            </thead>
            <tbody>
              {categoryData.accounts.map((acc, idx) => {
                const opening = acc.monthly && acc.monthly.length > 0 ? acc.monthly[0].amount : 0;
                const closing = acc.monthly && acc.monthly.length > 0 ? acc.monthly[acc.monthly.length - 1].amount : 0;
                const change = closing - opening;
                const percentChange = opening !== 0 ? ((change / Math.abs(opening)) * 100) : 0;

                return (
                  <tr key={idx} style={{ borderBottom: '1px solid #eee' }}>
                    <td style={{ padding: '10px' }}>{acc.account_name || acc.account}</td>
                    <td style={{ padding: '10px', textAlign: 'right' }}>{formatIndianCurrency(opening)}</td>
                    <td style={{ padding: '10px', textAlign: 'right', fontWeight: 600 }}>{formatIndianCurrency(closing)}</td>
                    <td style={{ 
                      padding: '10px', 
                      textAlign: 'right',
                      color: change >= 0 ? '#2e7d32' : '#c62828',
                      fontWeight: 600
                    }}>
                      {change >= 0 ? '+' : ''}{formatIndianCurrency(change)}
                    </td>
                    <td style={{ 
                      padding: '10px', 
                      textAlign: 'right',
                      color: percentChange >= 0 ? '#2e7d32' : '#c62828'
                    }}>
                      {percentChange >= 0 ? '+' : ''}{percentChange.toFixed(1)}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  // Overall Assets & Liabilities Trend Chart
  const getOverallTrendChart = () => {
    if (!periods || periods.length === 0) return null;

    const monthLabels = periods.map(p => p.label);

    const option = {
      title: {
        text: 'Assets & Liabilities Trend',
        left: 'center',
        textStyle: { fontSize: 18, fontWeight: 600 }
      },
      tooltip: {
        trigger: 'axis',
        formatter: (params) => {
          let result = `<strong>${params[0].axisValue}</strong><br/>`;
          params.forEach(param => {
            result += `${param.marker} ${param.seriesName}: ${formatIndianCurrency(param.value)}<br/>`;
          });
          return result;
        }
      },
      legend: {
        data: ['Total Assets', 'Total Liabilities'],
        top: 40
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: 90,
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: monthLabels,
        axisLabel: { rotate: 45, fontSize: 11 }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: (value) => {
            if (Math.abs(value) >= 10000000) return `₹${(value / 10000000).toFixed(1)}Cr`;
            if (Math.abs(value) >= 100000) return `₹${(value / 100000).toFixed(1)}L`;
            if (Math.abs(value) >= 1000) return `₹${(value / 1000).toFixed(1)}K`;
            return `₹${value}`;
          }
        }
      },
      series: [
        {
          name: 'Total Assets',
          type: 'line',
          data: totalAssetsByPeriod,
          smooth: true,
          lineStyle: { width: 3 },
          itemStyle: { color: '#667eea' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [{
                offset: 0,
                color: 'rgba(102, 126, 234, 0.3)'
              }, {
                offset: 1,
                color: 'rgba(102, 126, 234, 0.05)'
              }]
            }
          }
        },
        {
          name: 'Total Liabilities',
          type: 'line',
          data: totalLiabilitiesByPeriod,
          smooth: true,
          lineStyle: { width: 3 },
          itemStyle: { color: '#f5576c' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [{
                offset: 0,
                color: 'rgba(245, 87, 108, 0.3)'
              }, {
                offset: 1,
                color: 'rgba(245, 87, 108, 0.05)'
              }]
            }
          }
        }
      ]
    };

    return <ReactECharts option={option} style={{ height: '450px' }} />;
  };

  // Category-wise trend chart (all categories on one chart)
  const getCategoryWiseTrendChart = (categories, type, title) => {
    if (!categories || Object.keys(categories).length === 0 || !periods) return null;

    const monthLabels = periods.map(p => p.label);
    const categoryNames = Object.keys(categories);
    const colors = type === 'asset' 
      ? ['#667eea', '#764ba2', '#4caf50', '#ff9800', '#9c27b0', '#00bcd4', '#e91e63']
      : ['#f5576c', '#f093fb', '#ff5722', '#ff9800', '#ffc107', '#cddc39', '#8bc34a'];

    const series = categoryNames.map((catName, idx) => ({
      name: catName,
      type: 'line',
      data: categories[catName].monthly ? categories[catName].monthly.map(m => m.amount) : [],
      smooth: true,
      lineStyle: { width: 2 },
      itemStyle: { color: colors[idx % colors.length] }
    }));

    const option = {
      title: {
        text: title,
        left: 'center',
        textStyle: { fontSize: 16, fontWeight: 600 }
      },
      tooltip: {
        trigger: 'axis',
        formatter: (params) => {
          let result = `<strong>${params[0].axisValue}</strong><br/>`;
          params.forEach(param => {
            result += `${param.marker} ${param.seriesName}: ${formatIndianCurrency(param.value)}<br/>`;
          });
          return result;
        }
      },
      legend: {
        data: categoryNames,
        top: 35,
        type: 'scroll',
        textStyle: { fontSize: 11 }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: categoryNames.length > 5 ? 80 : 70,
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: monthLabels,
        axisLabel: { rotate: 45, fontSize: 11 }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: (value) => {
            if (Math.abs(value) >= 10000000) return `₹${(value / 10000000).toFixed(1)}Cr`;
            if (Math.abs(value) >= 100000) return `₹${(value / 100000).toFixed(1)}L`;
            if (Math.abs(value) >= 1000) return `₹${(value / 1000).toFixed(1)}K`;
            return `₹${value}`;
          }
        }
      },
      series: series
    };

    return <ReactECharts option={option} style={{ height: '400px' }} />;
  };

  const renderCategoryList = (categories, type, title, color) => (
    <div className="card" style={{ marginBottom: '20px' }}>
      <div className="card-header" style={{ 
        background: color, 
        color: 'white',
        padding: '20px 25px',
        fontSize: '16px',
        fontWeight: 600
      }}>
        {title}
      </div>
      <div style={{ padding: '15px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ background: '#f5f5f5', borderBottom: '2px solid #ddd' }}>
              <th style={{ padding: '10px', textAlign: 'left', fontWeight: 600 }}>Category</th>
              <th style={{ padding: '10px', textAlign: 'right', fontWeight: 600 }}>Opening Balance</th>
              <th style={{ padding: '10px', textAlign: 'right', fontWeight: 600 }}>Closing Balance</th>
              <th style={{ padding: '10px', textAlign: 'right', fontWeight: 600 }}>Change</th>
              <th style={{ padding: '10px', textAlign: 'right', fontWeight: 600 }}>% Change</th>
              <th style={{ padding: '10px', textAlign: 'center', fontWeight: 600 }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {categories.map((cat, idx) => {
              const percentChange = cat.opening !== 0 ? ((cat.change / Math.abs(cat.opening)) * 100) : 0;
              const isSelected = selectedCategory === cat.name && selectedType === type;

              return (
                <tr 
                  key={idx} 
                  style={{ 
                    borderBottom: '1px solid #eee',
                    background: 'white',
                    transition: 'background 0.2s ease'
                  }}
                  onMouseOver={(e) => e.currentTarget.style.background = '#f5f5f5'}
                  onMouseOut={(e) => e.currentTarget.style.background = 'white'}
                >
                  <td style={{ padding: '10px', fontWeight: isSelected ? 600 : 400 }}>{cat.name}</td>
                  <td style={{ padding: '10px', textAlign: 'right' }}>{formatIndianCurrency(cat.opening)}</td>
                  <td style={{ padding: '10px', textAlign: 'right', fontWeight: 600 }}>{formatIndianCurrency(cat.closing)}</td>
                  <td style={{ 
                    padding: '10px', 
                    textAlign: 'right',
                    color: cat.change >= 0 ? '#2e7d32' : '#c62828',
                    fontWeight: 600
                  }}>
                    {cat.change >= 0 ? '+' : ''}{formatIndianCurrency(cat.change)}
                  </td>
                  <td style={{ 
                    padding: '10px', 
                    textAlign: 'right',
                    color: percentChange >= 0 ? '#2e7d32' : '#c62828'
                  }}>
                    {percentChange >= 0 ? '+' : ''}{percentChange.toFixed(1)}%
                  </td>
                  <td style={{ padding: '10px', textAlign: 'center' }}>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedCategory(cat.name);
                        setSelectedType(type);
                        setShowModal(true);
                      }}
                      style={{
                        padding: '6px 16px',
                        fontSize: '13px',
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontWeight: 500,
                        transition: 'all 0.3s ease'
                      }}
                      onMouseOver={(e) => e.target.style.transform = 'translateY(-2px)'}
                      onMouseOut={(e) => e.target.style.transform = 'translateY(0)'}
                    >
                      📊 View Details
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );

  return (
    <div style={{ marginTop: '30px' }}>
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
          fontSize: '20px',
          fontWeight: '600'
        }}>
          📊 Category-wise Movement Analysis
        </h2>
        <p style={{ 
          color: 'rgba(255,255,255,0.9)', 
          margin: '8px 0 0 0',
          fontSize: '13px'
        }}>
          View overall trends and click on any category to see detailed breakdowns
        </p>
      </div>

      {/* Overall Assets & Liabilities Trend */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <div style={{ padding: '20px' }}>
          {getOverallTrendChart()}
        </div>
      </div>

      {/* Category-wise Trends */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))', gap: '20px', marginBottom: '20px' }}>
        <div className="card">
          <div style={{ padding: '20px' }}>
            {getCategoryWiseTrendChart(assets, 'asset', 'Asset Categories - Monthly Trend')}
          </div>
        </div>
        <div className="card">
          <div style={{ padding: '20px' }}>
            {getCategoryWiseTrendChart(liabilities, 'liability', 'Liability Categories - Monthly Trend')}
          </div>
        </div>
      </div>

      {/* Asset Categories */}
      {renderCategoryList(assetCategories, 'asset', '💰 Asset Categories', 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)')}

      {/* Liability Categories */}
      {renderCategoryList(liabilityCategories, 'liability', '📋 Liability Categories', 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)')}

      {/* Modal for Category Details */}
      {showModal && selectedCategory && (
        <div 
          className="modal-overlay" 
          onClick={() => {
            setShowModal(false);
            setSelectedCategory(null);
            setSelectedType(null);
          }}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '20px'
          }}
        >
          <div 
            className="modal" 
            onClick={(e) => e.stopPropagation()}
            style={{
              background: 'white',
              borderRadius: '12px',
              maxWidth: '1200px',
              width: '100%',
              maxHeight: '90vh',
              overflow: 'auto',
              boxShadow: '0 10px 40px rgba(0, 0, 0, 0.3)'
            }}
          >
            <div style={{ 
              background: selectedType === 'asset' 
                ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' 
                : 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
              color: 'white',
              padding: '20px 30px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderRadius: '12px 12px 0 0'
            }}>
              <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 600 }}>
                📈 {selectedCategory} - Detailed Analysis
              </h3>
              <button
                onClick={() => {
                  setShowModal(false);
                  setSelectedCategory(null);
                  setSelectedType(null);
                }}
                style={{
                  background: 'rgba(255,255,255,0.2)',
                  border: '1px solid white',
                  color: 'white',
                  padding: '8px 16px',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: 600
                }}
              >
                ✕ Close
              </button>
            </div>
            <div style={{ padding: '30px' }}>
              {getCategoryTrendChart()}
              {getAccountDetails()}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BalanceSheetCategoryTrends;

