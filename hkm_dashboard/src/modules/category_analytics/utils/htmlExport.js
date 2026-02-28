/**
 * Frontend-only HTML Export Utility
 * Generates standalone HTML files with embedded data
 */

import { formatIndianCurrency, formatPercent } from './formatters';

/**
 * Generate standalone HTML for comprehensive dashboard
 */
export const generateComprehensiveHTML = (data, company, fromDate, toDate, reportType = null) => {
  const title = reportType === 'balance-sheet' 
    ? 'Balance Sheet Report'
    : reportType === 'pl-report' 
    ? 'P&L Report'
    : 'Financial Dashboard';

  const htmlContent = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${title} - ${company}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f7fa;
            color: #2c3e50;
            padding: 20px;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 20px rgba(0,0,0,0.08);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 32px;
            margin-bottom: 10px;
            font-weight: 600;
        }
        
        .header p {
            font-size: 18px;
            opacity: 0.95;
        }
        
        .meta-info {
            background: #f8f9fa;
            padding: 20px 40px;
            border-bottom: 2px solid #e9ecef;
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 20px;
        }
        
        .meta-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .meta-label {
            font-weight: 600;
            color: #495057;
        }
        
        .meta-value {
            color: #212529;
        }
        
        .content {
            padding: 40px;
        }
        
        .section {
            margin-bottom: 40px;
        }
        
        .section-title {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 20px;
            color: #2c3e50;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }
        
        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            padding: 24px;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        .card-label {
            font-size: 14px;
            color: #6c757d;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .card-value {
            font-size: 28px;
            font-weight: 700;
            color: #212529;
        }
        
        .card-value.positive {
            color: #28a745;
        }
        
        .card-value.negative {
            color: #dc3545;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: white;
            border-radius: 8px;
            overflow: hidden;
        }
        
        thead {
            background: #f8f9fa;
        }
        
        th {
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #495057;
            border-bottom: 2px solid #dee2e6;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        td {
            padding: 12px 15px;
            border-bottom: 1px solid #f0f0f0;
        }
        
        tr:hover {
            background: #f8f9fa;
        }
        
        .amount {
            text-align: right;
            font-weight: 600;
            font-family: 'Courier New', monospace;
        }
        
        .positive-amount {
            color: #28a745;
        }
        
        .negative-amount {
            color: #dc3545;
        }
        
        .subsection {
            margin: 30px 0;
        }
        
        .subsection-title {
            font-size: 20px;
            font-weight: 600;
            color: #495057;
            margin-bottom: 15px;
            padding-left: 10px;
            border-left: 4px solid #667eea;
        }
        
        .footer {
            background: #f8f9fa;
            padding: 20px 40px;
            text-align: center;
            color: #6c757d;
            font-size: 14px;
            border-top: 2px solid #e9ecef;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .badge-success {
            background: #d4edda;
            color: #155724;
        }
        
        .badge-warning {
            background: #fff3cd;
            color: #856404;
        }
        
        .badge-danger {
            background: #f8d7da;
            color: #721c24;
        }
        
        .no-print {
            margin: 20px 0;
        }
        
        @media print {
            .no-print {
                display: none;
            }
            body {
                background: white;
            }
            .container {
                box-shadow: none;
            }
        }
        
        @media (max-width: 768px) {
            .meta-info {
                flex-direction: column;
            }
            .content {
                padding: 20px;
            }
            .summary-cards {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 ${title}</h1>
            <p>${company}</p>
        </div>
        
        <div class="meta-info">
            <div class="meta-item">
                <span class="meta-label">Period:</span>
                <span class="meta-value">${fromDate} to ${toDate}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Generated:</span>
                <span class="meta-value">${new Date().toLocaleString()}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Company:</span>
                <span class="meta-value">${company}</span>
            </div>
        </div>
        
        <div class="content">
            ${generateContentByType(data, reportType)}
        </div>
        
        <div class="footer">
            <p>Generated by HKM Category Analytics Dashboard | ${new Date().toLocaleDateString()}</p>
            <p style="margin-top: 8px; font-size: 12px;">This is a standalone HTML export with embedded data.</p>
        </div>
    </div>
</body>
</html>`;

  return htmlContent;
};

/**
 * Generate content based on report type
 */
const generateContentByType = (data, reportType) => {
  if (reportType === 'balance-sheet') {
    return generateBalanceSheetContent(data);
  } else if (reportType === 'pl-report') {
    return generatePLContent(data);
  } else {
    return generateCombinedContent(data);
  }
};

/**
 * Generate Balance Sheet content
 */
const generateBalanceSheetContent = (data) => {
  const bsData = data?.balance_sheet_data || data;
  const summary = bsData?.summary || {};
  
  return `
    <div class="section">
      <h2 class="section-title">📊 Balance Sheet Summary</h2>
      <div class="summary-cards">
        <div class="card">
          <div class="card-label">Total Assets</div>
          <div class="card-value">${formatIndianCurrency(summary.total_assets || 0)}</div>
        </div>
        <div class="card">
          <div class="card-label">Total Liabilities</div>
          <div class="card-value">${formatIndianCurrency(summary.total_liabilities || 0)}</div>
        </div>
        <div class="card">
          <div class="card-label">Total Equity</div>
          <div class="card-value ${(summary.total_equity || 0) >= 0 ? 'positive' : 'negative'}">${formatIndianCurrency(summary.total_equity || 0)}</div>
        </div>
      </div>
    </div>
    
    ${generateBalanceSheetTable('Assets', bsData?.assets || [])}
    ${generateBalanceSheetTable('Liabilities', bsData?.liabilities || [])}
    ${generateBalanceSheetTable('Equity', bsData?.equity || [])}
  `;
};

/**
 * Generate P&L content
 */
const generatePLContent = (data) => {
  const summary = data?.summary || {};
  
  return `
    <div class="section">
      <h2 class="section-title">📈 P&L Summary</h2>
      <div class="summary-cards">
        <div class="card">
          <div class="card-label">Total Income</div>
          <div class="card-value positive">${formatIndianCurrency(summary.total_income || 0)}</div>
        </div>
        <div class="card">
          <div class="card-label">Total Expenses</div>
          <div class="card-value negative">${formatIndianCurrency(summary.total_expense || 0)}</div>
        </div>
        <div class="card">
          <div class="card-label">Net Income</div>
          <div class="card-value ${(summary.net_income || 0) >= 0 ? 'positive' : 'negative'}">${formatIndianCurrency(summary.net_income || 0)}</div>
        </div>
      </div>
    </div>
    
    ${generateCategoryTable('Income Categories', data?.income_data || {})}
    ${generateCategoryTable('Expense Categories', data?.expense_data || {})}
  `;
};

/**
 * Generate combined content
 */
const generateCombinedContent = (data) => {
  const plSummary = data?.summary || {};
  const bsSummary = data?.balance_sheet_data?.summary || {};
  
  return `
    <div class="section">
      <h2 class="section-title">📊 Financial Overview</h2>
      <div class="summary-cards">
        <div class="card">
          <div class="card-label">Total Income</div>
          <div class="card-value positive">${formatIndianCurrency(plSummary.total_income || 0)}</div>
        </div>
        <div class="card">
          <div class="card-label">Total Expenses</div>
          <div class="card-value negative">${formatIndianCurrency(plSummary.total_expense || 0)}</div>
        </div>
        <div class="card">
          <div class="card-label">Net Income</div>
          <div class="card-value ${(plSummary.net_income || 0) >= 0 ? 'positive' : 'negative'}">${formatIndianCurrency(plSummary.net_income || 0)}</div>
        </div>
        <div class="card">
          <div class="card-label">Total Assets</div>
          <div class="card-value">${formatIndianCurrency(bsSummary.total_assets || 0)}</div>
        </div>
      </div>
    </div>
    
    ${generateCategoryTable('Income Categories', data?.income_data || {})}
    ${generateCategoryTable('Expense Categories', data?.expense_data || {})}
    ${generateBalanceSheetTable('Assets', data?.balance_sheet_data?.assets || [])}
    ${generateBalanceSheetTable('Liabilities', data?.balance_sheet_data?.liabilities || [])}
  `;
};

/**
 * Generate category table (for P&L)
 */
const generateCategoryTable = (title, categoryData) => {
  if (!categoryData || Object.keys(categoryData).length === 0) {
    return `
      <div class="subsection">
        <h3 class="subsection-title">${title}</h3>
        <p style="color: #6c757d; padding: 20px;">No data available</p>
      </div>
    `;
  }
  
  const rows = Object.entries(categoryData).map(([category, data]) => {
    const total = data.monthly?.reduce((sum, m) => sum + (m.amount || 0), 0) || 0;
    return `
      <tr>
        <td>${category}</td>
        <td class="amount">${formatIndianCurrency(total)}</td>
      </tr>
    `;
  }).join('');
  
  return `
    <div class="subsection">
      <h3 class="subsection-title">${title}</h3>
      <table>
        <thead>
          <tr>
            <th>Category</th>
            <th style="text-align: right;">Amount</th>
          </tr>
        </thead>
        <tbody>
          ${rows}
        </tbody>
      </table>
    </div>
  `;
};

/**
 * Generate balance sheet table
 */
const generateBalanceSheetTable = (title, items) => {
  if (!items || items.length === 0) {
    return `
      <div class="subsection">
        <h3 class="subsection-title">${title}</h3>
        <p style="color: #6c757d; padding: 20px;">No data available</p>
      </div>
    `;
  }
  
  const rows = items.map(item => {
    return `
      <tr>
        <td>${item.category || item.account || 'N/A'}</td>
        <td class="amount">${formatIndianCurrency(item.amount || item.value || 0)}</td>
      </tr>
    `;
  }).join('');
  
  const total = items.reduce((sum, item) => sum + (item.amount || item.value || 0), 0);
  
  return `
    <div class="subsection">
      <h3 class="subsection-title">${title}</h3>
      <table>
        <thead>
          <tr>
            <th>Category</th>
            <th style="text-align: right;">Amount</th>
          </tr>
        </thead>
        <tbody>
          ${rows}
          <tr style="font-weight: bold; background: #f8f9fa;">
            <td>Total ${title}</td>
            <td class="amount">${formatIndianCurrency(total)}</td>
          </tr>
        </tbody>
      </table>
    </div>
  `;
};

/**
 * Download HTML file
 */
export const downloadHTMLFile = (htmlContent, filename) => {
  const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};
