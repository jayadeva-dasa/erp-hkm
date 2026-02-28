// API functions for HKM Pay User Management
import apiClient from '../../../services/apiClient';
import { HKMPUser, HKMPUserFormData, UserAnalytics } from '../types';

// Get all HKMP Users
export const getAllUsers = async (): Promise<HKMPUser[]> => {
  try {
    const response = await apiClient.get(
      '/api/method/hkm.api.hkm_dashboard.hkmp_user.get_all_hkmp_users'
    );
    
    const result = response.data.message || response.data;
    
    if (result.status === 'success' && result.data) {
      return result.data;
    }
    
    throw new Error(result.message || 'Failed to fetch HKMP Users');
  } catch (error: any) {
    console.error('Error fetching HKMP Users:', error);
    throw new Error(
      error.response?.data?.exception || 
      error.message || 
      'Failed to fetch HKMP Users'
    );
  }
};

// Get single HKMP User
export const getUser = async (name: string): Promise<HKMPUser> => {
  try {
    const response = await apiClient.get(
      '/api/method/hkm.api.hkm_dashboard.hkmp_user.get_hkmp_user',
      { params: { name } }
    );
    
    const result = response.data.message || response.data;
    
    if (result.status === 'success' && result.data) {
      return result.data;
    }
    
    throw new Error(result.message || 'Failed to fetch HKMP User');
  } catch (error: any) {
    console.error('Error fetching HKMP User:', error);
    throw new Error(
      error.response?.data?.exception || 
      error.message || 
      'Failed to fetch HKMP User'
    );
  }
};

// Create new HKMP User
export const createUser = async (userData: HKMPUserFormData): Promise<HKMPUser> => {
  try {
    const response = await apiClient.post(
      '/api/method/hkm.api.hkm_dashboard.hkmp_user.create_hkmp_user',
      userData
    );
    
    const result = response.data.message || response.data;
    
    if (result.status === 'success' && result.data) {
      return result.data;
    }
    
    throw new Error(result.message || 'Failed to create HKMP User');
  } catch (error: any) {
    console.error('Error creating HKMP User:', error);
    throw new Error(
      error.response?.data?.exception || 
      error.response?.data?.message ||
      error.message || 
      'Failed to create HKMP User'
    );
  }
};

// Update existing HKMP User
export const updateUser = async (name: string, userData: Partial<HKMPUserFormData>): Promise<HKMPUser> => {
  try {
    const response = await apiClient.post(
      '/api/method/hkm.api.hkm_dashboard.hkmp_user.update_hkmp_user',
      { 
        name,
        user_data: userData 
      }
    );
    
    const result = response.data.message || response.data;
    
    if (result.status === 'success' && result.data) {
      return result.data;
    }
    
    throw new Error(result.message || 'Failed to update HKMP User');
  } catch (error: any) {
    console.error('Error updating HKMP User:', error);
    throw new Error(
      error.response?.data?.exception || 
      error.response?.data?.message ||
      error.message || 
      'Failed to update HKMP User'
    );
  }
};

// Delete HKMP User
export const deleteUser = async (name: string): Promise<void> => {
  try {
    const response = await apiClient.post(
      '/api/method/hkm.api.hkm_dashboard.hkmp_user.delete_hkmp_user',
      { name }
    );
    
    const result = response.data.message || response.data;
    
    if (result.status !== 'success') {
      throw new Error(result.message || 'Failed to delete HKMP User');
    }
  } catch (error: any) {
    console.error('Error deleting HKMP User:', error);
    throw new Error(
      error.response?.data?.exception || 
      error.response?.data?.message ||
      error.message || 
      'Failed to delete HKMP User'
    );
  }
};

// Get all users (for dropdown) with search support
export const getAllSystemUsers = async (
  searchTerm?: string, 
  limit: number = 30
): Promise<Array<{ name: string; full_name: string }>> => {
  try {
    const params: any = { limit };
    if (searchTerm) {
      params.search_term = searchTerm;
    }
    
    const response = await apiClient.get(
      '/api/method/hkm.api.hkm_dashboard.hkmp_user.get_system_users',
      { params }
    );
    
    const result = response.data.message || response.data;
    
    if (result.status === 'success' && result.data) {
      return result.data;
    }
    
    throw new Error(result.message || 'Failed to fetch System Users');
  } catch (error: any) {
    console.error('Error fetching System Users:', error);
    throw new Error(
      error.response?.data?.exception || 
      error.message || 
      'Failed to fetch System Users'
    );
  }
};

// Get all departments
export const getAllDepartments = async (): Promise<Array<{ name: string }>> => {
  try {
    const response = await apiClient.get(
      '/api/method/hkm.api.hkm_dashboard.hkmp_user.get_departments'
    );
    
    const result = response.data.message || response.data;
    
    if (result.status === 'success' && result.data) {
      return result.data;
    }
    
    throw new Error(result.message || 'Failed to fetch Departments');
  } catch (error: any) {
    console.error('Error fetching Departments:', error);
    throw new Error(
      error.response?.data?.exception || 
      error.message || 
      'Failed to fetch Departments'
    );
  }
};

// Get HKMP Entries for a user (user is optional - if null/empty, returns all users' entries)
export const getUserEntries = async (user: string | null | undefined, filters?: any): Promise<any[]> => {
  try {
    const response = await apiClient.post(
      '/api/method/hkm.api.hkm_dashboard.hkmp_user.get_user_entries',
      { 
        user: user || null,
        filters: filters ? JSON.stringify(filters) : null
      }
    );
    
    const result = response.data.message || response.data;
    
    if (result.status === 'success' && result.data) {
      return result.data;
    }
    
    throw new Error(result.message || 'Failed to fetch user entries');
  } catch (error: any) {
    console.error('Error fetching user entries:', error);
    throw new Error(
      error.response?.data?.exception || 
      error.message || 
      'Failed to fetch user entries'
    );
  }
};

// Get user analytics
export const getUserAnalytics = async (user: string, from_date?: string, to_date?: string): Promise<UserAnalytics> => {
  try {
    const response = await apiClient.post(
      '/api/method/hkm.api.hkm_dashboard.hkmp_user.get_user_analytics',
      { 
        user,
        from_date: from_date || null,
        to_date: to_date || null
      }
    );
    
    const result = response.data.message || response.data;
    
    if (result.status === 'success' && result.data) {
      return result.data;
    }
    
    throw new Error(result.message || 'Failed to fetch user analytics');
  } catch (error: any) {
    console.error('Error fetching user analytics:', error);
    throw new Error(
      error.response?.data?.exception || 
      error.message || 
      'Failed to fetch user analytics'
    );
  }
};

// Update entry status (bill_received or is_return)
export const updateEntryStatus = async (entryName: string, field: string, value: number): Promise<void> => {
  try {
    const response = await apiClient.post(
      '/api/method/hkm.api.hkm_dashboard.hkmp_user.update_entry_status',
      { 
        entry_name: entryName,
        field,
        value
      }
    );
    
    const result = response.data.message || response.data;
    
    if (result.status !== 'success') {
      throw new Error(result.message || 'Failed to update entry status');
    }
  } catch (error: any) {
    console.error('Error updating entry status:', error);
    throw new Error(
      error.response?.data?.exception || 
      error.message || 
      'Failed to update entry status'
    );
  }
};

// Show secret PIN for a user
export const showSecretPin = async (docname: string): Promise<string> => {
  try {
    const response = await apiClient.post(
      '/api/method/hkm.hkm_pay.doctype.hkmp_user.hkmp_user.show_secret_pin',
      { docname }
    );
    
    const pin = response.data.message;
    
    if (pin) {
      return pin;
    }
    
    throw new Error('Failed to retrieve secret PIN');
  } catch (error: any) {
    console.error('Error showing secret PIN:', error);
    throw new Error(
      error.response?.data?.exception || 
      error.response?.data?.message ||
      error.message || 
      'Failed to show secret PIN'
    );
  }
};

// Generate/Reset secret PIN for a user
export const generateSecretPin = async (docname: string, desiredPin?: string): Promise<string> => {
  try {
    const response = await apiClient.post(
      '/api/method/hkm.hkm_pay.doctype.hkmp_user.hkmp_user.generate_secret_pin',
      { 
        docname,
        desired_pin: desiredPin || null
      }
    );
    
    const pin = response.data.message;
    
    if (pin) {
      return pin;
    }
    
    throw new Error('Failed to generate secret PIN');
  } catch (error: any) {
    console.error('Error generating secret PIN:', error);
    throw new Error(
      error.response?.data?.exception || 
      error.response?.data?.message ||
      error.message || 
      'Failed to generate secret PIN'
    );
  }
};

// Get companies for a specific user
export const getUserCompanies = async (user: string): Promise<Array<{ company: string }>> => {
  try {
    const response = await apiClient.get(
      '/api/method/hkm.api.hkm_dashboard.hkmp_user.get_companies',
      { params: { user } }
    );
    
    const result = response.data.message || response.data;
    
    if (Array.isArray(result)) {
      return result;
    }
    
    return [];
  } catch (error: any) {
    console.error('Error fetching user companies:', error);
    return [];
  }
};

// Get all companies in the system
export const getAllCompanies = async (): Promise<Array<{ name: string }>> => {
  try {
    const response = await apiClient.get(
      '/api/method/hkm.api.hkm_dashboard.hkmp_user.get_all_companies'
    );
    
    const result = response.data.message || response.data;
    
    if (result.status === 'success' && result.data) {
      return result.data;
    }
    
    throw new Error(result.message || 'Failed to fetch companies');
  } catch (error: any) {
    console.error('Error fetching companies:', error);
    throw new Error(
      error.response?.data?.exception || 
      error.message || 
      'Failed to fetch companies'
    );
  }
};

// Get total spend by bank account
export const getTotalSpendBankAccountWise = async (): Promise<any[]> => {
  try {
    const response = await apiClient.get(
      '/api/method/hkm.api.hkm_dashboard.hkmp_user.get_total_spend_bank_account_wise'
    );
    
    const result = response.data.message || response.data;
    
    if (result.status === 'success' && result.data) {
      return result.data;
    }
    
    throw new Error(result.message || 'Failed to fetch bank account spending data');
  } catch (error: any) {
    console.error('Error fetching bank account spending data:', error);
    throw new Error(
      error.response?.data?.exception || 
      error.message || 
      'Failed to fetch bank account spending data'
    );
  }
};

export const hkmpUserApi = {
  getAllUsers,
  getUser,
  createUser,
  updateUser,
  deleteUser,
  getAllSystemUsers,
  getAllDepartments,
  getUserEntries,
  getUserAnalytics,
  updateEntryStatus,
  showSecretPin,
  generateSecretPin,
  getUserCompanies,
  getAllCompanies,
  getTotalSpendBankAccountWise
};

