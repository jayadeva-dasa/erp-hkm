import apiClient from '../../../services/apiClient';

// API endpoint for profit loss analysis
const PROFIT_LOSS_ANALYSIS_ENDPOINT =
  '/api/method/hkm.api.hkm_dashboard.profit_loss_analysis.get_profit_loss_analysis';

/**
 * Fetch profit loss analysis data
 * @param {Object} payload - The filter parameters
 * @param {string} payload.view_type - View type (dimension or detailed)
 * @param {string} payload.dimension - Primary dimension for analysis
 * @param {string} payload.analysis_type - Analysis type (cumulative or period_specific)
 * @param {string} payload.from_date - Start date for analysis (only for period_specific)
 * @param {string} payload.to_date - End date for analysis (only for period_specific)
 * @param {string} payload.period_type - Period type (only for period_specific)
 * @param {Array} payload.companies - Array of selected companies
 * @returns {Promise} API response with profit loss data
 */
export const fetchProfitLossAnalysis = async (payload) => {
  try {
    // Send payload as filters parameter for Frappe API
    const params = new URLSearchParams();
    params.append('filters', JSON.stringify(payload));

    const response = await apiClient.get(`${PROFIT_LOSS_ANALYSIS_ENDPOINT}?${params.toString()}`);
    return response;
  } catch (error) {
    console.error('Error fetching profit loss analysis:', error);
    throw error;
  }
};

/**
 * Get expected payload type for TypeScript
 * @typedef {Object} ProfitLossPayload
 * @property {string} view_type - View type (dimension or detailed)
 * @property {string} dimension - Primary dimension for analysis
 * @property {string} analysis_type - Analysis type (cumulative or period_specific)
 * @property {string} from_date - Start date for analysis (only for period_specific)
 * @property {string} to_date - End date for analysis (only for period_specific)
 * @property {string} period_type - Period type (only for period_specific)
 * @property {Array} companies - Array of selected companies
 */

/**
 * Export profit loss analysis data to Excel
 * @param {Object} payload - The filter parameters
 * @returns {Promise} Excel file download
 */
export const exportProfitLossAnalysisExcel = async (payload) => {
  try {
    const response = await apiClient.post(
      '/api/method/hkm.api.hkm_dashboard.profit_loss_analysis.export_excel',
      payload,
      { responseType: 'blob' }
    );
    return response;
  } catch (error) {
    console.error('Error exporting profit loss analysis to Excel:', error);
    throw error;
  }
};

/**
 * Export profit loss analysis data to PDF
 * @param {Object} payload - The filter parameters
 * @returns {Promise} PDF file download
 */
export const exportProfitLossAnalysisPdf = async (payload) => {
  try {
    const response = await apiClient.post(
      '/api/method/hkm.api.hkm_dashboard.profit_loss_analysis.export_pdf',
      payload,
      { responseType: 'blob' }
    );
    return response;
  } catch (error) {
    console.error('Error exporting profit loss analysis to PDF:', error);
    throw error;
  }
};

/**
 * Get available dimensions and their filter options
 * @returns {Promise} Available dimensions and filters
 */
export const getAvailableDimensions = async () => {
  try {
    const response = await apiClient.get(
      '/api/method/hkm.api.hkm_dashboard.profit_loss_analysis.get_dimensions'
    );
    return response;
  } catch (error) {
    console.error('Error fetching available dimensions:', error);
    throw error;
  }
};
