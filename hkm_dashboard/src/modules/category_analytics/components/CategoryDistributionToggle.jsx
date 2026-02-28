import React, { useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { formatIndianCurrency } from '../utils/formatters';
import { getCategoryDetails } from '../api/categoryAnalyticsApi';
import AccountDetailsModal from './AccountDetailsModal';

const CategoryDistributionToggle = ({ incomeData, expenseData, filters }) => {
  const [activeTab, setActiveTab] = useState('income');
  const [showModal, setShowModal] = useState(false);
  const [modalData, setModalData] = useState(null);
  const [loadingModal, setLoadingModal] = useState(false);

  // Add null checks
  if (!incomeData || !expenseData) {
    return null;
  }

  const handleChartClick = async (params) => {
    if (params.componentType === 'series') {
      const category = params.name;
      setShowModal(true);
      setLoadingModal(true);
      
      try {
        const details = await getCategoryDetails(
          filters.company,
          filters.fromDate,
          filters.toDate,
          category,
          activeTab === 'income' ? 'Income' : 'Expense'
        );
        setModalData(details);
      } catch (error) {
        console.error('Error loading category details:', error);
        setModalData({ error: 'Failed to load details' });
      } finally {
        setLoadingModal(false);
      }
    }
  };

  const getOption = (data) => {
    const pieData = Object.entries(data).map(([category, catData]) => {
      const total = catData.monthly.reduce((sum, m) => sum + m.amount, 0);
      return {
        name: category,
        value: Math.round(total)
      };
    }).filter(item => item.value > 0);

    return {
      tooltip: {
        trigger: 'item',
        formatter: (params) => {
          return `<strong>${params.name}</strong><br/>
                  ${formatIndianCurrency(params.value)} (${params.percent}%)<br/>
                  <em style="color: #999;">Click to see details</em>`;
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
            formatter: '{b}: {d}%'
          }
        }
      ]
    };
  };

  const currentData = activeTab === 'income' ? incomeData : expenseData;

  return (
    <>
      <div className="card">
        <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>Category Distribution</span>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={() => setActiveTab('income')}
              style={{
                padding: '8px 20px',
                background: activeTab === 'income' ? 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)' : '#f5f5f5',
                color: activeTab === 'income' ? 'white' : '#666',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '14px',
                transition: 'all 0.3s ease'
              }}
            >
              Income
            </button>
            <button
              onClick={() => setActiveTab('expense')}
              style={{
                padding: '8px 20px',
                background: activeTab === 'expense' ? 'linear-gradient(135deg, #ee0979 0%, #ff6a00 100%)' : '#f5f5f5',
                color: activeTab === 'expense' ? 'white' : '#666',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '14px',
                transition: 'all 0.3s ease'
              }}
            >
              Expense
            </button>
          </div>
        </div>
        <ReactECharts 
          option={getOption(currentData)} 
          style={{ height: '500px' }}
          onEvents={{
            click: handleChartClick
          }}
          notMerge={true}
          lazyUpdate={true}
        />
      </div>

      {showModal && (
        <AccountDetailsModal
          data={modalData}
          loading={loadingModal}
          onClose={() => setShowModal(false)}
        />
      )}
    </>
  );
};

export default CategoryDistributionToggle;

