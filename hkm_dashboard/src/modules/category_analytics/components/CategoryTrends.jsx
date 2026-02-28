import React, { useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { formatIndianCurrency } from '../utils/formatters';
import { getCategoryDetails } from '../api/categoryAnalyticsApi';
import AccountDetailsModal from './AccountDetailsModal';
import { generateColorPalette } from '../utils/formatters';

const CategoryTrends = ({ data, filters }) => {
  const [activeTab, setActiveTab] = useState('income');
  const [showModal, setShowModal] = useState(false);
  const [modalData, setModalData] = useState(null);
  const [loadingModal, setLoadingModal] = useState(false);

  // Add null checks
  if (!data || !data.income_data || !data.expense_data || !data.periods) {
    return null;
  }

  const handleChartClick = async (params) => {
    if (params.componentType === 'series') {
      const category = params.seriesName;
      const monthIndex = params.dataIndex;
      const monthData = activeTab === 'income' 
        ? data.income_data[category]?.monthly[monthIndex]
        : data.expense_data[category]?.monthly[monthIndex];
      
      if (!monthData) return;
      
      setShowModal(true);
      setLoadingModal(true);
      
      try {
        // Parse the month to get date range
        const monthDate = new Date(monthData.date);
        const fromDate = new Date(monthDate.getFullYear(), monthDate.getMonth(), 1);
        const toDate = new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 0);
        
        const details = await getCategoryDetails(
          filters.company,
          fromDate.toISOString().split('T')[0],
          toDate.toISOString().split('T')[0],
          category,
          activeTab === 'income' ? 'Income' : 'Expense'
        );
        
        // Add month info to modal data
        details.month = monthData.month;
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
    const categoryData = activeTab === 'income' ? data.income_data : data.expense_data;
    const categories = Object.keys(categoryData);
    const colors = generateColorPalette(categories.length);

    const series = categories.map((category, idx) => {
      const monthlyData = categoryData[category].monthly.map(m => Math.round(m.amount));
      
      return {
        name: category,
        type: 'line',
        data: monthlyData,
        smooth: true,
        itemStyle: { color: colors[idx] },
        emphasis: {
          focus: 'series'
        }
      };
    });

    return {
      title: {
        text: `${activeTab === 'income' ? 'Income' : 'Expense'} Category Trends`,
        left: 'center',
        textStyle: {
          fontSize: 18,
          fontWeight: 600
        }
      },
      tooltip: {
        trigger: 'axis',
        formatter: (params) => {
          let result = `<strong>${params[0].axisValue}</strong><br/>`;
          params.forEach(param => {
            result += `${param.marker} ${param.seriesName}: ${formatIndianCurrency(param.value)}<br/>`;
          });
          result += '<br/><em style="color: #999;">Click on a point to see details</em>';
          return result;
        }
      },
      legend: {
        type: 'scroll',
        bottom: 10,
        data: categories
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '80px',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: data.periods,
        axisLabel: {
          rotate: 45
        }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: (value) => formatIndianCurrency(value)
        }
      },
      series: series
    };
  };

  return (
    <>
      <div className="card">
        <div className="card-header">
          Category-wise Monthly Trends
          <div style={{ float: 'right', display: 'flex', gap: '10px' }}>
            <button
              className={`btn ${activeTab === 'income' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab('income')}
              style={{ padding: '6px 15px', fontSize: '13px' }}
            >
              Income
            </button>
            <button
              className={`btn ${activeTab === 'expense' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab('expense')}
              style={{ padding: '6px 15px', fontSize: '13px' }}
            >
              Expense
            </button>
          </div>
        </div>
        <ReactECharts 
          option={getOption()} 
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

export default CategoryTrends;


