import apiClient from '../../../services/apiClient';
import axios from 'axios';

// Create a separate client instance for public requests without CSRF requirement
const publicApiClient = axios.create({
  withCredentials: true
});

const API_BASE = '/api/method/hkm.api.hkm_dashboard.category_analytics.dashboard';
const API_BALANCE_SHEET = '/api/method/hkm.api.hkm_dashboard.category_analytics.balance_sheet';
const API_TRUST_TEMPLATES = '/api/method/hkm.api.hkm_dashboard.category_analytics.trust_templates';

/**
 * Get list of companies
 */
export const getCompanies = async () => {
  try {
    console.log('🔵 [getCompanies] Starting API call...');
    console.log('🔵 [getCompanies] API URL:', `${API_BASE}.get_companies`);
    console.log('🔵 [getCompanies] API_BASE:', API_BASE);
    
    const response = await apiClient.get(`${API_BASE}.get_companies`);
    
    console.log('🟢 [getCompanies] API Response received:', {
      status: response.status,
      statusText: response.statusText,
      data: response.data,
      message: response.data?.message
    });
    
    const companies = response.data.message || [];
    console.log('🟢 [getCompanies] Returning companies:', companies);
    
    return companies;
  } catch (error) {
    console.error('🔴 [getCompanies] Error details:', {
      message: error.message,
      response: error.response,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      config: error.config,
      stack: error.stack
    });
    
    // Return empty array instead of throwing to prevent page crash
    console.warn('🔴 [getCompanies] Returning empty array due to error');
    return [];
  }
};

/**
 * Get complete dashboard data
 */
export const getDashboardData = async (company, fromDate, toDate) => {
  try {
    // Check if this is a public view
    if (typeof window !== 'undefined' && window.is_public_view && window.public_token) {
      return getPublicDashboardData(window.public_token);
    }
    
    const response = await apiClient.post(`${API_BASE}.get_dashboard_data`, {
      company,
      from_date: fromDate,
      to_date: toDate
    });
    return response.data.message;
  } catch (error) {
    console.error('Error fetching dashboard data:', error);
    throw error;
  }
};

/**
 * Get category details for a specific period
 */
export const getCategoryDetails = async (company, fromDate, toDate, category, rootType) => {
  try {
    const response = await apiClient.post(`${API_BASE}.get_category_details`, {
      company,
      from_date: fromDate,
      to_date: toDate,
      category,
      root_type: rootType
    });
    return response.data.message;
  } catch (error) {
    console.error('Error fetching category details:', error);
    throw error;
  }
};

/**
 * Get all categories for a company
 */
export const getAllCategories = async (company) => {
  try {
    const response = await apiClient.post(`${API_BASE}.get_all_categories`, {
      company
    });
    return response.data.message;
  } catch (error) {
    console.error('Error fetching categories:', error);
    throw error;
  }
};

/**
 * Get all accounts for a company and root type
 */
export const getAllAccounts = async (company, rootType) => {
  try {
    const response = await apiClient.post(`${API_BASE}.get_all_accounts`, {
      company,
      root_type: rootType
    });
    return response.data.message;
  } catch (error) {
    console.error('Error fetching accounts:', error);
    throw error;
  }
};

/**
 * Save or update a category
 */
export const saveCategory = async (company, rootType, categoryName, accountsData, oldCategoryName = null, description = '') => {
  try {
    const response = await apiClient.post(`${API_BASE}.save_category`, {
      company,
      root_type: rootType,
      category_name: categoryName,
      accounts_data: JSON.stringify(accountsData),
      old_category_name: oldCategoryName,
      description: description
    });
    return response.data.message;
  } catch (error) {
    console.error('Error saving category:', error);
    throw error;
  }
};

/**
 * Delete a category
 */
export const deleteCategory = async (company, categoryName, rootType) => {
  try {
    const response = await apiClient.post(`${API_BASE}.delete_category`, {
      company,
      category_name: categoryName,
      root_type: rootType
    });
    return response.data.message;
  } catch (error) {
    console.error('Error deleting category:', error);
    throw error;
  }
};

/**
 * Move account between categories
 */
export const moveAccount = async (company, rootType, account, sourceCategory, targetCategory, portion = 100) => {
  try {
    const response = await apiClient.post(`${API_BASE}.move_account`, {
      company,
      root_type: rootType,
      account,
      source_category: sourceCategory,
      target_category: targetCategory,
      portion
    });
    return response.data.message;
  } catch (error) {
    console.error('Error moving account:', error);
    throw error;
  }
};

/**
 * Export to static HTML (Frontend-only implementation)
 * This function is now a placeholder - the actual export is handled by
 * the frontend using data already loaded in the component.
 * See utils/htmlExport.js for the implementation.
 */
export const exportToStaticHTML = async (company, fromDate, toDate, reportType = null) => {
  // This is now handled directly in the component using frontend-only export
  // Keep this function for backwards compatibility
  console.warn('exportToStaticHTML is deprecated. Use frontend-only export from utils/htmlExport.js');
  return { success: true };
};

/**
 * Create a public shareable link
 */
export const createPublicLink = async (company, fromDate, toDate, expiresInDays = 30, reportType = null) => {
  try {
    const response = await apiClient.post(`${API_BASE}.create_public_link`, {
      company,
      from_date: fromDate,
      to_date: toDate,
      expires_in_days: expiresInDays,
      report_type: reportType // 'balance-sheet', 'pl-report', or null for combined
    });
    return response.data.message;
  } catch (error) {
    console.error('Error creating public link:', error);
    throw error;
  }
};

/**
 * Get dashboard data using public token (no authentication required)
 */
export const getPublicDashboardData = async (token) => {
  try {
    console.log('🔧 [Public Mode] Attempting to fetch public dashboard data with token');
    
    // Use the public API client that doesn't require CSRF token
    const response = await publicApiClient.get(`${API_BASE}.get_public_dashboard_data`, {
      params: { token }
    });
    
    console.log('🔧 [Public Mode] Raw response:', response);
    
    const result = response.data.message;
    console.log('🔧 [Public Mode] Processed result:', result);
    return result.data;
  } catch (error) {
    console.error('🔴 Error fetching public dashboard data:', error);
    console.error('🔴 Error details:', {
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      url: error.config?.url,
      method: error.config?.method
    });
    throw error;
  }
};

/**
 * Get all public links
 */
export const getPublicLinks = async (reportType = null) => {
  try {
    const params = reportType ? { report_type: reportType } : {};
    const response = await apiClient.get(`${API_BASE}.get_public_links`, { params });
    // Handle both message and direct response formats
    return response.data.message || response.data || [];
  } catch (error) {
    console.error('Error fetching public links:', error);
    // Return empty array instead of throwing to prevent page crash
    const errorMessage = error?.response?.data?.message || error?.message || 'Unknown error';
    console.error('Public links error details:', errorMessage);
    return [];
  }
};

/**
 * Revoke a public link
 */
export const revokePublicLink = async (token) => {
  try {
    const response = await apiClient.post(`${API_BASE}.revoke_public_link`, {
      token
    });
    return response.data.message;
  } catch (error) {
    console.error('Error revoking public link:', error);
    throw error;
  }
};

// ============================================================================
// BALANCE SHEET & TRUST-SPECIFIC APIs
// ============================================================================

/**
 * Get companies grouped by trust type
 */
export const getCompaniesByTrustType = async () => {
  try {
    const response = await apiClient.get(`${API_BALANCE_SHEET}.get_companies_by_trust_type`);
    return response.data.message || {charitable: [], religious: [], business: [], other: []};
  } catch (error) {
    console.error('Error fetching companies by trust type:', error);
    throw error;
  }
};

/**
 * Get balance sheet data
 */
export const getBalanceSheetData = async (company, fromDate, toDate, periodicity = 'Monthly') => {
  try {
    const response = await apiClient.post(`${API_BALANCE_SHEET}.get_balance_sheet_data`, {
      company,
      from_date: fromDate,
      to_date: toDate,
      periodicity
    });
    return response.data.message;
  } catch (error) {
    console.error('Error fetching balance sheet data:', error);
    throw error;
  }
};

/**
 * Get comprehensive dashboard data (P&L + Balance Sheet + Ratios)
 */
export const getComprehensiveDashboardData = async (company = null, fromDate = null, toDate = null) => {
  try {
    // Check if this is a public view
    if (typeof window !== 'undefined' && window.is_public_view && window.public_token) {
      console.log('🔧 [Public Mode] Fetching public dashboard data with token');
      const publicData = await getPublicDashboardData(window.public_token);
      console.log('🔧 [Public Mode] Public data received:', publicData);
      // Return just the data from public response
      return publicData;
    }
    
    // Authenticated mode - require parameters
    if (!company || !fromDate || !toDate) {
      throw new Error('Company, fromDate, and toDate are required in authenticated mode');
    }
    
    console.log('🔧 [Authenticated Mode] Fetching comprehensive dashboard data:', { company, fromDate, toDate });
    const response = await apiClient.post(`${API_BALANCE_SHEET}.get_comprehensive_dashboard_data`, {
      company,
      from_date: fromDate,
      to_date: toDate
    });
    console.log('🔧 [Authenticated Mode] Data received:', response.data);
    return response.data.message;
  } catch (error) {
    console.error('🔴 Error fetching comprehensive dashboard data:', error);
    console.error('🔴 Error details:', {
      message: error?.message,
      response: error?.response?.data,
      status: error?.response?.status,
      url: `${API_BALANCE_SHEET}.get_comprehensive_dashboard_data`
    });
    throw error;
  }
};

/**
 * Get trust category template
 */
export const getTrustCategoryTemplate = async (trustType) => {
  try {
    const response = await apiClient.post(`${API_TRUST_TEMPLATES}.get_trust_category_template`, {
      trust_type: trustType
    });
    return response.data.message;
  } catch (error) {
    console.error('Error fetching trust category template:', error);
    throw error;
  }
};

/**
 * Setup trust categories for a company
 */
export const setupTrustCategories = async (company, trustType = null) => {
  try {
    const response = await apiClient.post(`${API_TRUST_TEMPLATES}.setup_trust_categories`, {
      company,
      trust_type: trustType
    });
    return response.data.message;
  } catch (error) {
    console.error('Error setting up trust categories:', error);
    throw error;
  }
};

/**
 * Get trust info and setup status
 */
export const getTrustInfo = async (company) => {
  try {
    const response = await apiClient.post(`${API_TRUST_TEMPLATES}.get_trust_info`, {
      company
    });
    return response.data.message;
  } catch (error) {
    console.error('Error fetching trust info:', error);
    throw error;
  }
};

