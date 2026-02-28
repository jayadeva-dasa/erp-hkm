import { format as formatDateFns } from 'date-fns';

export const formatCurrency = (value = 0) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value || 0);

export const formatNumber = (value = 0) => new Intl.NumberFormat('en-IN').format(value || 0);

export const formatDate = (value) => {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return formatDateFns(date, 'dd MMM yyyy');
};

export const formatShortNumber = (value = 0) => {
  const abs = Math.abs(value);
  const formatWithUnit = (val, unit) => {
    const formatted = val >= 10 ? Math.round(val).toString() : val.toFixed(1);
    return `${formatted.replace(/\.0$/, '')}${unit}`;
  };

  if (abs >= 10_000_000) {
    return formatWithUnit(value / 10_000_000, 'Cr');
  }
  if (abs >= 100_000) {
    return formatWithUnit(value / 100_000, 'L');
  }
  if (abs >= 1_000) {
    return formatWithUnit(value / 1_000, 'K');
  }
  return formatNumber(value);
};
