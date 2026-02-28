// API functions for Eagle View module
import apiClient from '../../../services/apiClient';
import type { EagleViewFilters, DimensionOption, SelectOption, EagleViewRow, EagleViewResponse, ApiResponse } from '../types';

export const eagleViewApi = {
  /**
   * Get all accounting dimensions
   */
  async getAccountingDimensions(): Promise<DimensionOption[]> {
    try {
      const response = await apiClient.get(
        '/api/method/hkm.api.hkm_dashboard.eagle_view.get_accounting_dimensions'
      );

      const result = response.data.message || response.data;
      if (result.status === 'success' && result.data) {
        return result.data;
      }
      throw new Error(result.message || 'Failed to fetch dimensions');
    } catch (error: any) {
      console.error('Error in getAccountingDimensions:', error);
      throw new Error(error.response?.data?.exception || error.message || 'Failed to fetch dimensions');
    }
  },

  /**
   * Get values for a specific dimension
   */
  async getDimensionValues(dimension: string, txt: string = ''): Promise<SelectOption[]> {
    try {
      const response = await apiClient.get(
        '/api/method/hkm.api.hkm_dashboard.eagle_view.get_dimension_values',
        { params: { dimension, txt } }
      );

      const result = response.data.message || response.data;
      if (result.status === 'success' && result.data) {
        return result.data;
      }
      throw new Error(result.message || 'Failed to fetch dimension values');
    } catch (error: any) {
      console.error('Error in getDimensionValues:', error);
      throw new Error(error.response?.data?.exception || error.message || 'Failed to fetch dimension values');
    }
  },

  /**
   * Get accounts list
   */
  async getAccounts(txt: string = ''): Promise<SelectOption[]> {
    try {
      const response = await apiClient.get(
        '/api/method/hkm.api.hkm_dashboard.eagle_view.get_accounts',
        { params: { txt } }
      );

      const result = response.data.message || response.data;
      if (result.status === 'success' && result.data) {
        return result.data;
      }
      throw new Error(result.message || 'Failed to fetch accounts');
    } catch (error: any) {
      console.error('Error in getAccounts:', error);
      throw new Error(error.response?.data?.exception || error.message || 'Failed to fetch accounts');
    }
  },

  /**
   * Get companies list
   */
  async getCompanies(): Promise<SelectOption[]> {
    try {
      const response = await apiClient.get(
        '/api/method/hkm.api.hkm_dashboard.eagle_view.get_companies'
      );

      const result = response.data.message || response.data;
      if (result.status === 'success' && result.data) {
        return result.data;
      }
      throw new Error(result.message || 'Failed to fetch companies');
    } catch (error: any) {
      console.error('Error in getCompanies:', error);
      throw new Error(error.response?.data?.exception || error.message || 'Failed to fetch companies');
    }
  },

  /**
   * Get internal adjustment types
   */
  async getInternalAdjustmentTypes(): Promise<SelectOption[]> {
    try {
      const response = await apiClient.get(
        '/api/method/hkm.api.hkm_dashboard.eagle_view.get_internal_adjustment_types'
      );

      const result = response.data.message || response.data;
      if (result.status === 'success' && result.data) {
        return result.data;
      }
      throw new Error(result.message || 'Failed to fetch adjustment types');
    } catch (error: any) {
      console.error('Error in getInternalAdjustmentTypes:', error);
      throw new Error(error.response?.data?.exception || error.message || 'Failed to fetch adjustment types');
    }
  },

  /**
   * Get Eagle View report data
   */
  async getEagleViewData(filters: EagleViewFilters): Promise<EagleViewResponse> {
    try {
      // Transform filters for backend compatibility
      // Map "Detailed View" to "Voucher View" for backend
      // Handle Account dimension: if Account is selected as dimension, 
      // we still send account field separately (backend expects it)
      const backendFilters: any = { ...filters };
      
      if (filters.report_view === 'Detailed View') {
        backendFilters.report_view = 'Voucher View';
      }
      // Multi Dimension View is already correct, no mapping needed
      
      // For Cumulative Dimension View, don't send from_date and to_date
      // The backend will ignore dates for cumulative reports
      if (filters.report_view === 'Dimension View' && filters.time_period === 'Cumulative') {
        delete backendFilters.from_date;
        delete backendFilters.to_date;
      }
      
      // For Multi Dimension View, keep from_date and to_date (now supports date filtering)
      // Remove time_period as it's not used for Multi Dimension View
      if (filters.report_view === 'Multi Dimension View') {
        delete backendFilters.time_period;
      }
      
      // If Account is selected as dimension, ensure account field is populated
      // The backend will use the account field, not dimension_value for Account
      if (filters.dimension === 'Account' && filters.account && filters.account.length > 0) {
        // Account is already in filters.account, which is what backend expects
        // We can optionally map it to dimension_value if backend needs it
        // For now, keep it as is since backend likely uses account field
      }
      
      // Debug: Log filters being sent to backend
      console.log('=== FRONTEND API DEBUG ===');
      console.log('Filters being sent to backend:', backendFilters);
      console.log('include_adjustment:', backendFilters.include_adjustment);
      console.log('internal_adjustment_type:', backendFilters.internal_adjustment_type);
      console.log('==========================');
      
      const response = await apiClient.post(
        '/api/method/hkm.api.hkm_dashboard.eagle_view.get_eagle_view_data',
        { filters: JSON.stringify(backendFilters) }
      );

      const result = response.data.message || response.data;
      
      console.log('API Response result:', result);
      console.log('Result status:', result.status);
      console.log('Result data type:', typeof result.data);
      console.log('Result data is array:', Array.isArray(result.data));
      
      if (result.status === 'success') {
        let finalData: any[] = [];
        let finalMetadata: any = undefined;
        
        // Check if data is period-wise (has metadata) or cumulative (array)
        if (Array.isArray(result.data)) {
          // Cumulative data - direct array
          console.log('Handling cumulative data (array)');
          finalData = result.data;
          finalMetadata = result.metadata;
        } else if (result.data && typeof result.data === 'object') {
          // Period-wise or multi-dimension data - object with data and metadata
          console.log('Handling period-wise/multi-dimension data (object)');
          console.log('Result.data structure:', result.data);
          
          if (Array.isArray(result.data.data)) {
            // Nested structure: { data: { data: [...], metadata: {...} } }
            finalData = result.data.data;
            finalMetadata = result.data.metadata || result.metadata;
          } else if (Array.isArray(result.data)) {
            // Direct array in data property
            finalData = result.data;
            finalMetadata = result.metadata;
          } else {
            console.warn('Unexpected data structure, defaulting to empty array');
            finalData = [];
            finalMetadata = result.data.metadata || result.metadata;
          }
        } else if (!result.data) {
          // No data but success - return empty array
          console.log('No data in response, returning empty array');
          finalData = [];
          finalMetadata = result.metadata;
        } else {
          console.warn('Unknown data format, defaulting to empty array');
          finalData = [];
          finalMetadata = result.metadata;
        }
        
        // Debug: Log final data structure
        if (finalData && finalData.length > 0) {
          console.log('Final data length:', finalData.length);
          console.log('Sample row keys from final data:', Object.keys(finalData[0]));
        }
        
        return { data: finalData, metadata: finalMetadata };
      }
      
      // Error case
      console.error('API returned error:', result.message);
      throw new Error(result.message || 'Failed to fetch report data');
    } catch (error: any) {
      console.error('Error in getEagleViewData:', error);
      throw new Error(error.response?.data?.exception || error.message || 'Failed to fetch report data');
    }
  },
};

