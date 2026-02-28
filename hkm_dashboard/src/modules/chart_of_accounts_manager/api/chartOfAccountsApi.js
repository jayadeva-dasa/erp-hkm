import apiClient from '../../../services/apiClient';

/**
 * Get list of companies
 */
export const getCompanies = async () => {
  try {
    const response = await apiClient.get('/api/resource/Company', {
      params: {
        fields: JSON.stringify(['name', 'abbr', 'default_currency']),
        limit_page_length: 999,
      },
    });
    return response.data.data || [];
  } catch (error) {
    console.error('Error fetching companies:', error);
    throw error;
  }
};

/**
 * Get chart of accounts for a company
 * @param {string} company - Company name
 * @param {number} maxDepth - Maximum depth to expand (optional)
 */
export const getChartOfAccounts = async (company, maxDepth = null) => {
  try {
    const response = await apiClient.post('/api/method/hkm.api.hkm_dashboard.chart_of_accounts.get_chart_of_accounts', {
      company,
      max_depth: maxDepth,
    });
    return response.data.message || [];
  } catch (error) {
    console.error('Error fetching chart of accounts:', error);
    throw error;
  }
};

/**
 * Update account parent (for drag and drop)
 * @param {string} accountName - Account to move
 * @param {string} newParent - New parent account
 * @param {string} company - Company name
 */
export const updateAccountParent = async (accountName, newParent, company) => {
  try {
    const response = await apiClient.post('/api/method/hkm.api.hkm_dashboard.chart_of_accounts.update_account_parent', {
      account_name: accountName,
      new_parent: newParent,
      company,
    });
    return response.data.message || {};
  } catch (error) {
    console.error('Error updating account parent:', error);
    throw error;
  }
};

/**
 * Get account details including balance
 * @param {string} accountName - Account name
 * @param {string} company - Company name
 * @param {string} fromDate - From date for balance calculation
 * @param {string} toDate - To date for balance calculation
 */
export const getAccountDetails = async (accountName, company, fromDate, toDate) => {
  try {
    const response = await apiClient.post('/api/method/hkm.api.hkm_dashboard.chart_of_accounts.get_account_details', {
      account_name: accountName,
      company,
      from_date: fromDate,
      to_date: toDate,
    });
    return response.data.message || {};
  } catch (error) {
    console.error('Error fetching account details:', error);
    throw error;
  }
};

/**
 * Get account balances for multiple accounts
 * @param {Array} accountNames - Array of account names
 * @param {string} company - Company name
 * @param {string} fromDate - From date
 * @param {string} toDate - To date
 */
export const getAccountBalances = async (accountNames, company, fromDate, toDate) => {
  try {
    const response = await apiClient.post('/api/method/hkm.api.hkm_dashboard.chart_of_accounts.get_account_balances', {
      account_names: accountNames,
      company,
      from_date: fromDate,
      to_date: toDate,
    });
    return response.data.message || {};
  } catch (error) {
    console.error('Error fetching account balances:', error);
    throw error;
  }
};

/**
 * Validate if account can be moved to new parent
 * @param {string} accountName - Account to move
 * @param {string} newParent - New parent account
 */
export const validateAccountMove = async (accountName, newParent) => {
  try {
    const response = await apiClient.post('/api/method/hkm.api.hkm_dashboard.chart_of_accounts.validate_account_move', {
      account_name: accountName,
      new_parent: newParent,
    });
    return response.data.message || { valid: false };
  } catch (error) {
    console.error('Error validating account move:', error);
    throw error;
  }
};
