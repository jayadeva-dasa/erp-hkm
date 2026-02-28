/**
 * Format number in Indian numbering system (Lakhs, Crores)
 */
export const formatIndianCurrency = (num) => {
  if (num === null || num === undefined) return '₹0';
  
  const absNum = Math.abs(num);
  const sign = num < 0 ? '-' : '';
  
  if (absNum >= 10000000) {
    return `${sign}₹${(absNum / 10000000).toFixed(2)}Cr`;
  } else if (absNum >= 100000) {
    return `${sign}₹${(absNum / 100000).toFixed(2)}L`;
  } else if (absNum >= 1000) {
    return `${sign}₹${(absNum / 1000).toFixed(2)}K`;
  } else {
    return `${sign}₹${absNum.toFixed(2)}`;
  }
};

/**
 * Format number with Indian comma separation
 */
export const formatIndianNumber = (num) => {
  if (num === null || num === undefined) return '0';
  
  const rounded = Math.round(num);
  const absNum = Math.abs(rounded);
  const sign = rounded < 0 ? '-' : '';
  
  const numStr = absNum.toString();
  
  if (numStr.length <= 3) {
    return sign + numStr;
  }
  
  const lastThree = numStr.slice(-3);
  const remaining = numStr.slice(0, -3);
  
  const formatted = remaining.replace(/\B(?=(\d{2})+(?!\d))/g, ',') + ',' + lastThree;
  
  return sign + formatted;
};

/**
 * Format percentage
 */
export const formatPercent = (num, decimals = 1) => {
  if (num === null || num === undefined) return '0%';
  return `${num.toFixed(decimals)}%`;
};

/**
 * Format date to readable format
 */
export const formatDate = (dateStr) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-IN', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric' 
  });
};

/**
 * Get default date range (current month)
 */
export const getDefaultDateRange = () => {
  const today = new Date();
  const year = today.getFullYear();
  const month = today.getMonth();
  
  // First day of current month
  const fromDate = new Date(year, month, 1);
  
  // Last day of current month
  const toDate = new Date(year, month + 1, 0);
  
  return {
    fromDate: fromDate.toISOString().split('T')[0],
    toDate: toDate.toISOString().split('T')[0]
  };
};

/**
 * Get financial year date range
 */
export const getFinancialYearRange = () => {
  const today = new Date();
  const currentYear = today.getFullYear();
  const currentMonth = today.getMonth(); // 0-11
  
  // If we're in Jan-Mar, financial year started last year
  // If we're in Apr-Dec, financial year started this year
  const fyStartYear = currentMonth < 3 ? currentYear - 1 : currentYear;
  
  return {
    fromDate: `${fyStartYear}-04-01`,
    toDate: today.toISOString().split('T')[0]
  };
};

/**
 * Get volatility color based on classification
 */
export const getVolatilityColor = (volatility) => {
  switch (volatility) {
    case 'stable':
      return '#4CAF50';
    case 'moderate':
      return '#FF9800';
    case 'volatile':
      return '#f44336';
    default:
      return '#9E9E9E';
  }
};

/**
 * Get trend color based on direction
 */
export const getTrendColor = (trend) => {
  switch (trend) {
    case 'increasing':
      return '#2196F3';
    case 'decreasing':
      return '#E91E63';
    case 'stable':
      return '#4CAF50';
    default:
      return '#9E9E9E';
  }
};

/**
 * Get trend icon based on direction
 */
export const getTrendIcon = (trend) => {
  switch (trend) {
    case 'increasing':
      return '📈';
    case 'decreasing':
      return '📉';
    case 'stable':
      return '➡️';
    default:
      return '—';
  }
};

/**
 * Get volatility badge class
 */
export const getVolatilityBadgeClass = (volatility) => {
  switch (volatility) {
    case 'stable':
      return 'badge-stable';
    case 'moderate':
      return 'badge-moderate';
    case 'volatile':
      return 'badge-volatile';
    default:
      return '';
  }
};

/**
 * Get trend badge class
 */
export const getTrendBadgeClass = (trend) => {
  switch (trend) {
    case 'increasing':
      return 'badge-increasing';
    case 'decreasing':
      return 'badge-decreasing';
    case 'stable':
      return 'badge-stable';
    default:
      return '';
  }
};

/**
 * Calculate percentage change
 */
export const calculatePercentChange = (current, previous) => {
  if (previous === 0) return current > 0 ? 100 : 0;
  return ((current - previous) / Math.abs(previous)) * 100;
};

/**
 * Generate color palette for charts
 */
export const generateColorPalette = (count) => {
  const baseColors = [
    '#2196F3', '#4CAF50', '#FF9800', '#E91E63', '#9C27B0',
    '#00BCD4', '#8BC34A', '#FFC107', '#F44336', '#3F51B5',
    '#009688', '#CDDC39', '#FF5722', '#673AB7', '#03A9F4'
  ];
  
  if (count <= baseColors.length) {
    return baseColors.slice(0, count);
  }
  
  // Generate additional colors if needed
  const colors = [...baseColors];
  while (colors.length < count) {
    const hue = (colors.length * 137.5) % 360;
    colors.push(`hsl(${hue}, 70%, 50%)`);
  }
  
  return colors;
};


