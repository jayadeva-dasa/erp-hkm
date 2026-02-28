import React, { useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { formatIndianCurrency } from '../utils/formatters';
import { getCategoryDetails } from '../api/categoryAnalyticsApi';
import AccountDetailsModal from './AccountDetailsModal';

const CategoryDistribution = ({ data, type, title, filters }) => {
  const [showModal, setShowModal] = useState(false);
  const [modalData, setModalData] = useState(null);
  const [loadingModal, setLoadingModal] = useState(false);

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
          type === 'income' ? 'Income' : 'Expense'
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

  const getOption = () => {
    const pieData = Object.entries(data).map(([category, catData]) => {
      const total = catData.monthly.reduce((sum, m) => sum + m.amount, 0);
      return {
        name: category,
        value: Math.round(total)
      };
    });

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

  return (
    <>
      <div className="card">
        <div className="card-header">{title}</div>
        <ReactECharts 
          option={getOption()} 
          style={{ height: '400px' }}
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

export default CategoryDistribution;


