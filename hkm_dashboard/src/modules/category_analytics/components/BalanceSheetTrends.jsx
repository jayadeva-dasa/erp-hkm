import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

export default function BalanceSheetTrends({ assets, liabilities, periods }) {
  const chartRef = useRef(null);

  useEffect(() => {
    if (!chartRef.current || !periods || !assets) return;

    const chart = echarts.init(chartRef.current);
    
    // Aggregate totals for each period
    const assetTotals = periods.map((period, idx) => {
      return Object.values(assets).reduce((sum, cat) => {
        return sum + (cat.monthly && cat.monthly[idx] ? cat.monthly[idx].amount : 0);
      }, 0) / 10000000;
    });

    const liabilityTotals = periods.map((period, idx) => {
      return Object.values(liabilities).reduce((sum, cat) => {
        return sum + (cat.monthly && cat.monthly[idx] ? cat.monthly[idx].amount : 0);
      }, 0) / 10000000;
    });

    // Calculate net position (Assets - Liabilities)
    const netPositionTotals = assetTotals.map((asset, idx) => asset - liabilityTotals[idx]);

    const option = {
      title: {
        text: 'Assets & Liabilities Trends Over Time',
        left: 'center',
        textStyle: {
          fontSize: 20,
          fontWeight: 600,
          color: '#1a237e'
        }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        },
        formatter: function(params) {
          let result = `<strong>${params[0].axisValue}</strong><br/>`;
          params.forEach(param => {
            result += `${param.marker} ${param.seriesName}: ₹${param.value.toFixed(2)} Cr<br/>`;
          });
          return result;
        }
      },
      legend: {
        data: ['Assets', 'Liabilities', 'Net Position'],
        top: 40,
        textStyle: {
          fontSize: 14
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: 100,
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: periods.map(p => p.label),
        axisLabel: {
          rotate: 45,
          fontSize: 12
        }
      },
      yAxis: {
        type: 'value',
        name: '₹ Crores',
        nameTextStyle: {
          fontSize: 14,
          fontWeight: 600
        },
        axisLabel: {
          formatter: '{value}'
        }
      },
      series: [
        {
          name: 'Assets',
          type: 'line',
          data: assetTotals,
          smooth: true,
          lineStyle: {
            width: 3
          },
          itemStyle: {
            color: '#2196F3'
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(33, 150, 243, 0.3)' },
              { offset: 1, color: 'rgba(33, 150, 243, 0.05)' }
            ])
          }
        },
        {
          name: 'Liabilities',
          type: 'line',
          data: liabilityTotals,
          smooth: true,
          lineStyle: {
            width: 3
          },
          itemStyle: {
            color: '#FF9800'
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(255, 152, 0, 0.3)' },
              { offset: 1, color: 'rgba(255, 152, 0, 0.05)' }
            ])
          }
        },
        {
          name: 'Net Position',
          type: 'line',
          data: netPositionTotals,
          smooth: true,
          lineStyle: {
            width: 3
          },
          itemStyle: {
            color: '#4CAF50'
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(76, 175, 80, 0.3)' },
              { offset: 1, color: 'rgba(76, 175, 80, 0.05)' }
            ])
          }
        }
      ]
    };

    chart.setOption(option);

    // Handle resize
    const handleResize = () => chart.resize();
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.dispose();
    };
  }, [assets, liabilities, periods]);

  return (
    <div className="balance-sheet-trends">
      <div ref={chartRef} style={{ width: '100%', height: '450px', marginTop: '40px' }} />
    </div>
  );
}

