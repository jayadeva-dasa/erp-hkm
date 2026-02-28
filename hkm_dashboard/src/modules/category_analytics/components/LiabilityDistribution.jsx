import React, { useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { formatIndianCurrency } from '../utils/formatters';

const LiabilityDistribution = ({ liabilities, filters }) => {
  const [showModal, setShowModal] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState(null);

  const handleChartClick = (params) => {
    if (params.componentType === 'series') {
      const categoryName = params.name;
      const categoryData = liabilities[categoryName];
      
      setSelectedCategory({
        name: categoryName,
        data: categoryData
      });
      setShowModal(true);
    }
  };

  const getOption = () => {
    const pieData = Object.entries(liabilities).map(([category, catData]) => {
      return {
        name: category,
        value: Math.abs(Math.round(catData.total || 0))
      };
    }).filter(item => item.value > 0); // Only show categories with values

    // Color scheme for liabilities (warmer colors)
    const colors = [
      '#f5576c', '#f093fb', '#ff5722', '#ff9800', 
      '#ffc107', '#cddc39', '#8bc34a', '#e91e63',
      '#9c27b0', '#673ab7', '#3f51b5', '#2196f3'
    ];

    return {
      color: colors,
      tooltip: {
        trigger: 'item',
        formatter: (params) => {
          return `<strong>${params.name}</strong><br/>
                  ${formatIndianCurrency(params.value)} (${params.percent}%)<br/>
                  <em style="color: #999;">Click to see accounts</em>`;
        }
      },
      legend: {
        orient: 'vertical',
        right: 10,
        top: 'center',
        type: 'scroll',
        formatter: (name) => {
          const item = pieData.find(d => d.name === name);
          return `${name}: ${formatIndianCurrency(item.value)}`;
        },
        textStyle: {
          fontSize: 12
        }
      },
      series: [
        {
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['40%', '50%'],
          data: pieData,
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          },
          label: {
            formatter: '{b}: {d}%',
            fontSize: 11
          }
        }
      ]
    };
  };

  return (
    <>
      <div className="card">
        <div className="card-header">
          💳 Liability Distribution
        </div>
        <ReactECharts 
          option={getOption()} 
          style={{ height: '450px' }}
          onEvents={{
            click: handleChartClick
          }}
          notMerge={true}
          lazyUpdate={true}
        />
      </div>

      {/* Modal for Account Details */}
      {showModal && selectedCategory && (
        <div 
          className="modal-overlay" 
          onClick={() => setShowModal(false)}
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
              maxWidth: '900px',
              width: '100%',
              maxHeight: '80vh',
              overflow: 'auto',
              boxShadow: '0 10px 40px rgba(0, 0, 0, 0.3)'
            }}
          >
            <div style={{ 
              background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
              color: 'white',
              padding: '20px 30px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderRadius: '12px 12px 0 0'
            }}>
              <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 600 }}>
                💳 {selectedCategory.name}
              </h3>
              <button
                onClick={() => setShowModal(false)}
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
              <div style={{ 
                background: '#f5f5f5', 
                padding: '15px 20px', 
                borderRadius: '8px',
                marginBottom: '20px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <span style={{ fontSize: '14px', color: '#666' }}>Total Amount:</span>
                <span style={{ fontSize: '24px', fontWeight: 'bold', color: '#f5576c' }}>
                  {formatIndianCurrency(selectedCategory.data.total)}
                </span>
              </div>

              <div style={{ marginBottom: '15px', color: '#666', fontSize: '14px' }}>
                {selectedCategory.data.accounts?.length || 0} account(s)
              </div>

              {selectedCategory.data.accounts && selectedCategory.data.accounts.length > 0 ? (
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ background: '#f5f5f5', borderBottom: '2px solid #ddd' }}>
                      <th style={{ padding: '12px', textAlign: 'left', fontSize: '13px', fontWeight: 600 }}>
                        Account Name
                      </th>
                      <th style={{ padding: '12px', textAlign: 'right', fontSize: '13px', fontWeight: 600 }}>
                        Amount
                      </th>
                      <th style={{ padding: '12px', textAlign: 'center', fontSize: '13px', fontWeight: 600 }}>
                        Allocation
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedCategory.data.accounts.map((account, idx) => (
                      <tr 
                        key={idx}
                        style={{ 
                          borderBottom: '1px solid #eee',
                          transition: 'background 0.2s'
                        }}
                        onMouseOver={(e) => e.currentTarget.style.background = '#f9f9f9'}
                        onMouseOut={(e) => e.currentTarget.style.background = 'white'}
                      >
                        <td style={{ padding: '12px', fontSize: '13px' }}>
                          {account.account_name || account.account}
                        </td>
                        <td style={{ padding: '12px', textAlign: 'right', fontSize: '13px', fontWeight: 500 }}>
                          {formatIndianCurrency(account.amount)}
                        </td>
                        <td style={{ padding: '12px', textAlign: 'center', fontSize: '12px' }}>
                          <span style={{ 
                            background: '#ffebee', 
                            color: '#c62828', 
                            padding: '4px 10px', 
                            borderRadius: '12px',
                            fontWeight: 500
                          }}>
                            {account.portion}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div style={{ 
                  textAlign: 'center', 
                  padding: '40px', 
                  color: '#999',
                  fontSize: '14px'
                }}>
                  No accounts in this category
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default LiabilityDistribution;

