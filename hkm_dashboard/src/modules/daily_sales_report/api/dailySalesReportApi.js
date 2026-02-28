import apiClient from '../../../services/apiClient';

const API_BASE = '/api/method/hkm.api.hkm_dashboard.daily_sales_report';

/**
 * Get list of companies for sales report
 */
export const getCompanies = async () => {
  try {
    const response = await apiClient.get(`${API_BASE}.company_list_for_sales_report`);
    return response.data.message || [];
  } catch (error) {
    console.error('Error fetching companies:', error);
    return [];
  }
};

/**
 * Get list of accounts for sales report
 */
export const getAccounts = async () => {
  try {
    const response = await apiClient.get(`${API_BASE}.account_list_for_sales_report`);
    return response.data.message || [];
  } catch (error) {
    console.error('Error fetching accounts:', error);
    return [];
  }
};

/**
 * Get daily sales report data
 */
export const getDailySalesReport = async (fromDate, toDate, company, account) => {
  try {
    const response = await apiClient.post(`${API_BASE}.get_daily_sales_report`, {
      from_date: fromDate,
      to_date: toDate,
      company: company,
      account: account,
    });
    return response.data.message || [];
  } catch (error) {
    console.error('Error fetching daily sales report:', error);
    throw error;
  }
};

/**
 * Get daily sales report cash data
 */
export const getDailySalesReportCash = async (fromDate, toDate, company, account) => {
  try {
    const response = await apiClient.post(`${API_BASE}.get_daily_sales_report_cash`, {
      from_date: fromDate,
      to_date: toDate,
      company: company,
      account: account,
    });
    return response.data.message || [];
  } catch (error) {
    console.error('Error fetching daily sales report cash:', error);
    throw error;
  }
};

