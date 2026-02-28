import React, { useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { formatIndianCurrency, formatPercent, generateColorPalette } from '../utils/formatters';

const YoYComparison = ({ comparison }) => {
  const [activeTab, setActiveTab] = useState('income');
  
  // Add null checks
  if (!comparison || !comparison.income || !comparison.expense) {
    return null;
  }
  
  const data = activeTab === 'income' ? comparison.income : comparison.expense;
  const categories = Object.keys(data);

  const getChartOption = () => {
    const colors = generateColorPalette(categories.length);
    
    return {
      title: {
        text: `Year-over-Year Comparison - ${activeTab === 'income' ? 'Income' : 'Expense'}`,
        left: 'center',
        textStyle: {
          fontSize: 18,
          fontWeight: 600
        }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        },
        formatter: (params) => {
          const category = params[0].name;
          const catData = data[category];
          return `<strong>${category}</strong><br/>
                  Current Year: ${formatIndianCurrency(catData.current_year)}<br/>
                  Last Year: ${formatIndianCurrency(catData.last_year)}<br/>
                  Change: ${formatIndianCurrency(catData.change)} (${formatPercent(catData.change_percent)})`;
        }
      },
      legend: {
        data: ['Current Year', 'Last Year'],
        bottom: 10
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '60px',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: categories,
        axisLabel: {
          rotate: 45,
          interval: 0
        }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: (value) => formatIndianCurrency(value)
        }
      },
      series: [
        {
          name: 'Current Year',
          type: 'bar',
          data: categories.map(cat => Math.round(data[cat].current_year)),
          itemStyle: {
            color: activeTab === 'income' ? '#11998e' : '#ee0979'
          }
        },
        {
          name: 'Last Year',
          type: 'bar',
          data: categories.map(cat => Math.round(data[cat].last_year)),
          itemStyle: {
            color: '#95a5a6'
          }
        }
      ]
    };
  };

  return (
    <div className="card">
      <div className="card-header">
        Year-over-Year Comparison
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

      <div style={{ padding: '20px', background: '#f9f9f9', borderRadius: '8px', margin: '20px' }}>
        <strong>Period Comparison:</strong>
        <div style={{ marginTop: '10px' }}>
          <div>Current Period: {comparison.period.current.from} to {comparison.period.current.to}</div>
          <div>Last Year: {comparison.period.last_year.from} to {comparison.period.last_year.to}</div>
        </div>
      </div>

      <ReactECharts 
        option={getChartOption()} 
        style={{ height: '400px' }}
        notMerge={true}
        lazyUpdate={true}
      />

      <div style={{ padding: '20px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#f5f5f5', borderBottom: '2px solid #ddd' }}>
              <th style={{ padding: '12px', textAlign: 'left' }}>Category</th>
              <th style={{ padding: '12px', textAlign: 'right' }}>Current Year</th>
              <th style={{ padding: '12px', textAlign: 'right' }}>Last Year</th>
              <th style={{ padding: '12px', textAlign: 'right' }}>Change</th>
              <th style={{ padding: '12px', textAlign: 'center' }}>% Change</th>
            </tr>
          </thead>
          <tbody>
            {categories.map((category, idx) => {
              const catData = data[category];
              const isPositive = catData.change >= 0;
              
              return (
                <tr key={idx} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={{ padding: '12px', fontWeight: 500 }}>
                    {category}
                  </td>
                  <td style={{ padding: '12px', textAlign: 'right' }}>
                    {formatIndianCurrency(catData.current_year)}
                  </td>
                  <td style={{ padding: '12px', textAlign: 'right' }}>
                    {formatIndianCurrency(catData.last_year)}
                  </td>
                  <td style={{ 
                    padding: '12px', 
                    textAlign: 'right',
                    color: isPositive ? '#4CAF50' : '#f44336',
                    fontWeight: 600
                  }}>
                    {isPositive ? '+' : ''}{formatIndianCurrency(catData.change)}
                  </td>
                  <td style={{ padding: '12px', textAlign: 'center' }}>
                    <span style={{
                      padding: '4px 12px',
                      borderRadius: '12px',
                      background: isPositive ? '#e8f5e9' : '#ffebee',
                      color: isPositive ? '#2e7d32' : '#c62828',
                      fontWeight: 600
                    }}>
                      {isPositive ? '↑' : '↓'} {formatPercent(Math.abs(catData.change_percent))}
                    </span>
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

export default YoYComparison;


