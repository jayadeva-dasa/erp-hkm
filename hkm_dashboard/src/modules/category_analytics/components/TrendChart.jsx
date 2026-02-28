import React from 'react';
import ReactECharts from 'echarts-for-react';
import { formatIndianCurrency } from '../utils/formatters';

const TrendChart = ({ data, filters }) => {
  // Add null checks
  if (!data || !data.periods || !data.income_data || !data.expense_data) {
    return null;
  }

  const getOption = () => {
    const periods = data.periods;
    
    // Calculate totals per period
    const incomeByPeriod = periods.map((_, idx) => {
      let total = 0;
      Object.values(data.income_data).forEach(cat => {
        if (cat.monthly[idx]) total += cat.monthly[idx].amount;
      });
      return Math.round(total);
    });
    
    const expenseByPeriod = periods.map((_, idx) => {
      let total = 0;
      Object.values(data.expense_data).forEach(cat => {
        if (cat.monthly[idx]) total += cat.monthly[idx].amount;
      });
      return Math.round(total);
    });
    
    const netIncomeByPeriod = incomeByPeriod.map((inc, idx) => inc - expenseByPeriod[idx]);
    
    return {
      title: {
        text: 'Income & Expense Trends',
        left: 'center',
        textStyle: {
          fontSize: 18,
          fontWeight: 600
        }
      },
      tooltip: {
        trigger: 'axis',
        formatter: (params) => {
          let result = `<strong>${params[0].name}</strong><br/>`;
          params.forEach(param => {
            result += `${param.marker} ${param.seriesName}: ${formatIndianCurrency(param.value)}<br/>`;
          });
          return result;
        }
      },
      legend: {
        data: ['Income', 'Expense', 'Net Income'],
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
        data: periods,
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
      series: [
        {
          name: 'Income',
          type: 'line',
          data: incomeByPeriod,
          smooth: true,
          itemStyle: { color: '#11998e' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(17, 153, 142, 0.3)' },
                { offset: 1, color: 'rgba(17, 153, 142, 0.05)' }
              ]
            }
          }
        },
        {
          name: 'Expense',
          type: 'line',
          data: expenseByPeriod,
          smooth: true,
          itemStyle: { color: '#ee0979' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(238, 9, 121, 0.3)' },
                { offset: 1, color: 'rgba(238, 9, 121, 0.05)' }
              ]
            }
          }
        },
        {
          name: 'Net Income',
          type: 'line',
          data: netIncomeByPeriod,
          smooth: true,
          itemStyle: { color: '#667eea' },
          lineStyle: {
            width: 3,
            type: 'dashed'
          }
        }
      ]
    };
  };

  return (
    <div className="card">
      <ReactECharts 
        option={getOption()} 
        style={{ height: '400px' }}
        notMerge={true}
        lazyUpdate={true}
      />
    </div>
  );
};

export default TrendChart;


