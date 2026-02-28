// API functions for Asset Reco module
import apiClient from '../../../services/apiClient';
import type { AssetRecoItem, Specification, AvailableAsset, SpecificationValue } from '../types';

export const assetRecoApi = {
  /**
   * Get all companies for the dropdown filter
   */
  async getCompanies(): Promise<string[]> {
    try {
      const response = await apiClient.get(
        '/api/method/hkm.api.asset_reco.get_companies'
      );

      const result = response.data.message || response.data;
      
      // Handle direct array response
      if (Array.isArray(result)) {
        return result;
      }
      
      // Handle wrapped response
      if (result && Array.isArray(result.data)) {
        return result.data;
      }
      
      return [];
    } catch (error: any) {
      console.error('Error in getCompanies:', error);
      return [];
    }
  },

  /**
   * Get all asset reco documents with optional filters
   * NOTE: sub_category field does not exist in HKM Assets Reco
   */
  async getAssetReco(filters?: {
    company?: string;
    asset_category?: string;
    purchased_date_from?: string;
    purchased_date_to?: string;
    custodian?: string;
    secondary_custodian?: string;
  }): Promise<AssetRecoItem[]> {
    try {
      const params = new URLSearchParams();
      
      if (filters?.company) {
        params.append('company', filters.company);
      }
      if (filters?.asset_category) {
        params.append('asset_category', filters.asset_category);
      }
      if (filters?.purchased_date_from) {
        params.append('purchased_date_from', filters.purchased_date_from);
      }
      if (filters?.purchased_date_to) {
        params.append('purchased_date_to', filters.purchased_date_to);
      }
      if (filters?.custodian) {
        params.append('custodian', filters.custodian);
      }
      if (filters?.secondary_custodian) {
        params.append('secondary_custodian', filters.secondary_custodian);
      }
      
      const queryString = params.toString();
      const url = queryString 
        ? `/api/method/hkm.api.asset_reco.get_asset_reco_list?${queryString}`
        : '/api/method/hkm.api.asset_reco.get_asset_reco_list';
      
      const response = await apiClient.get(url);

      const result = response.data.message || response.data;
      
      // Handle direct array response or wrapped response
      if (Array.isArray(result)) {
        return result;
      }
      
      if (result && Array.isArray(result.data)) {
        return result.data;
      }
      
      throw new Error('Unexpected response format from server');
    } catch (error: any) {
      console.error('Error in getAssetReco:', error);
      throw new Error(
        error.response?.data?.exception || 
        error.message || 
        'Failed to fetch asset reco data'
      );
    }
  },

  /**
   * Submit an asset reco document
   */
  async submitAssetReco(name: string): Promise<void> {
    try {
      const response = await apiClient.post(
        '/api/method/hkm.api.asset_reco.submit_asset_reco',
        { name }
      );

      const result = response.data.message || response.data;
      
      if (result && result.exc_type) {
        throw new Error(result.exc || 'Failed to submit asset reco');
      }
    } catch (error: any) {
      console.error('Error in submitAssetReco:', error);
      throw new Error(
        error.response?.data?.exception || 
        error.response?.data?.message ||
        error.message || 
        'Failed to submit asset reco'
      );
    }
  },

  /**
   * Edit asset reco document fields
   * Allowed fields: location, purchased_date, purchased_amount, secondary_custodian, remarks
   * NOTE: sub_category, model_number, brand fields do not exist in HKM Assets Reco
   */
  async editAssetReco(updates: Array<{ name: string; fieldname: string; value: any }>): Promise<void> {
    try {
      const response = await apiClient.post(
        '/api/method/hkm.api.asset_reco.edit_asset_reco',
        { dict_data: updates }
      );

      const result = response.data.message || response.data;
      
      if (result && result.exc_type) {
        throw new Error(result.exc || 'Failed to update asset reco');
      }
    } catch (error: any) {
      console.error('Error in editAssetReco:', error);
      throw new Error(
        error.response?.data?.exception || 
        error.response?.data?.message ||
        error.message || 
        'Failed to update asset reco'
      );
    }
  },

  /**
   * Get sub categories for a given category
   * NOTE: Sub-category field does not exist in HKM Assets Reco.
   * Keeping for API compatibility but always returns empty array.
   */
  async getSubCategory(category: string): Promise<string[]> {
    // Sub-category not used in HKM Assets Reco
    return [];
  },

  /**
   * Get users for secondary custodian dropdown
   */
  async getUsers(searchTerm: string = ''): Promise<Array<{ email: string; full_name: string }>> {
    try {
      const url = searchTerm
        ? `/api/method/hkm.api.asset_reco.get_users?search_term=${encodeURIComponent(searchTerm)}`
        : '/api/method/hkm.api.asset_reco.get_users';

      const response = await apiClient.get(url);

      const result = response.data.message || response.data;
      
      // Handle direct array response
      if (Array.isArray(result)) {
        return result;
      }
      
      // Handle wrapped response
      if (result && Array.isArray(result.data)) {
        return result.data;
      }
      
      return [];
    } catch (error: any) {
      console.error('Error in getUsers:', error);
      return [];
    }
  },

  /**
   * Get all custodians (users assigned to assets)
   */
  async getCustodians(): Promise<string[]> {
    try {
      const response = await apiClient.get(
        '/api/method/hkm.api.asset_reco.get_custodians'
      );

      const result = response.data.message || response.data;
      
      // Handle direct array response
      if (Array.isArray(result)) {
        return result;
      }
      
      // Handle wrapped response
      if (result && Array.isArray(result.data)) {
        return result.data;
      }
      
      return [];
    } catch (error: any) {
      console.error('Error in getCustodians:', error);
      return [];
    }
  },

  /**
   * Get all sub categories for filter dropdown
   * NOTE: Sub-category field does not exist in HKM Assets Reco.
   * Keeping for API compatibility but always returns empty array.
   */
  async getAllSubCategories(): Promise<string[]> {
    // Sub-category not used in HKM Assets Reco
    return [];
  },

  /**
   * Get single asset reco document with specifications
   */
  async getAssetRecoById(id: string): Promise<AssetRecoItem> {
    try {
      const response = await apiClient.get(
        `/api/method/hkm.api.asset_reco.get_asset_reco?id=${encodeURIComponent(id)}`
      );

      const result = response.data.message || response.data;
      
      if (!result) {
        throw new Error('Asset not found');
      }
      
      return result;
    } catch (error: any) {
      console.error('Error in getAssetRecoById:', error);
      throw new Error(
        error.response?.data?.exception || 
        error.message || 
        'Failed to fetch asset reco'
      );
    }
  },

  /**
   * Get asset categories available to the user
   */
  async getAssetCategories(): Promise<string[]> {
    try {
      const response = await apiClient.get(
        '/api/method/hkm.api.asset_reco.get_asset_categories'
      );

      const result = response.data.message || response.data;
      
      if (Array.isArray(result)) {
        return result;
      }
      
      return [];
    } catch (error: any) {
      console.error('Error in getAssetCategories:', error);
      return [];
    }
  },

  /**
   * Get specifications for a given asset category
   */
  async getAssetSpecifications(mainCategory: string): Promise<Specification[]> {
    try {
      if (!mainCategory) {
        return [];
      }

      const response = await apiClient.get(
        `/api/method/hkm.api.asset_reco.get_asset_specifications?main_category=${encodeURIComponent(mainCategory)}`
      );

      const result = response.data.message || response.data;
      
      if (Array.isArray(result)) {
        return result;
      }
      
      return [];
    } catch (error: any) {
      console.error('Error in getAssetSpecifications:', error);
      return [];
    }
  },

  /**
   * Get available custom specifications (non-mandatory) for a category
   */
  async getAvailableCustomSpecs(mainCategory: string): Promise<Specification[]> {
    try {
      if (!mainCategory) {
        return [];
      }

      const response = await apiClient.get(
        `/api/method/hkm.api.asset_reco.get_available_custom_specs?main_category=${encodeURIComponent(mainCategory)}`
      );

      const result = response.data.message || response.data;
      
      if (Array.isArray(result)) {
        return result;
      }
      
      return [];
    } catch (error: any) {
      console.error('Error in getAvailableCustomSpecs:', error);
      return [];
    }
  },

  /**
   * Search for available assets (for autocomplete)
   */
  async searchAvailableAssets(params: { 
    assetId?: string; 
    assetName?: string;
  }): Promise<AvailableAsset[]> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.assetId) {
        queryParams.append('asset_id', params.assetId);
      }
      if (params.assetName) {
        queryParams.append('asset_name', params.assetName);
      }

      const queryString = queryParams.toString();
      const url = queryString
        ? `/api/method/hkm.api.asset_reco.search_available_assets?${queryString}`
        : '/api/method/hkm.api.asset_reco.search_available_assets';

      const response = await apiClient.get(url);

      const result = response.data.message || response.data;
      
      if (Array.isArray(result)) {
        return result;
      }
      
      return [];
    } catch (error: any) {
      console.error('Error in searchAvailableAssets:', error);
      return [];
    }
  },

  /**
   * Save asset reco with specifications
   */
  async saveAssetRecoWithSpecs(params: {
    name: string;
    purchased_date?: string;
    purchased_amount?: number;
    location?: string;
    remarks?: string;
    secondary_custodian?: string;
    availability_status?: 'New' | 'Available';
    asset_id?: string;
    asset_name?: string;
    asset_category?: string;
    sub_category?: string;
    model_number?: string;
    brand?: string;
    specifications?: SpecificationValue[];
  }): Promise<void> {
    try {
      const response = await apiClient.post(
        '/api/method/hkm.api.asset_reco.save_asset_reco_with_specs',
        params
      );

      const result = response.data.message || response.data;
      
      if (result && result.exc_type) {
        throw new Error(result.exc || 'Failed to save asset reco');
      }
    } catch (error: any) {
      console.error('Error in saveAssetRecoWithSpecs:', error);
      throw new Error(
        error.response?.data?.exception || 
        error.response?.data?.message ||
        error.message || 
        'Failed to save asset reco'
      );
    }
  },
};

