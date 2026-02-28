// TypeScript types for HKM Pay User Management
export interface HKMActiveCompany {
  company: string;
}

export interface HKMPUser {
  name: string;
  user: string;
  full_name?: string;
  department?: string;
  per_transaction_limit: number;
  daily_limit: number;
  advance_limit: number;
  available_amt?: number;
  available_daily_limit?: number;
  current_day_spending?: number;
  current_month_spending?: number;
  total_spending?: number;
  active_company?: HKMActiveCompany[];
  enabled: number;
  creation?: string;
  modified?: string;
  owner?: string;
  modified_by?: string;
}

export interface HKMPUserFormData {
  user: string;
  full_name?: string;
  department?: string;
  per_transaction_limit: number;
  advance_limit: number;
  daily_limit: number;
  active_company?: HKMActiveCompany[];
  enabled: number;
}

export interface HKMPEntry {
  name: string;
  user: string;
  user_full_name?: string;
  status: 'Pending' | 'Processing' | 'Success' | 'Failed';
  transfer_type: 'UPI' | 'IMPS' | 'NEFT' | 'RTGS';
  amount: number;
  beneficiary_name?: string;
  utr?: string;
  remarks: string;
  bill_received: number;
  is_return: number;
  debited_from?: string;
  company?: string;
  bank_account?: string;
  account_number?: string;
  ifsc_code?: string;
  upi_id?: string;
  mobile_number?: number;
  creation: string;
  modified: string;
  docstatus: number;
}

export interface HKMPEntryFilters {
  status?: string;
  transfer_type?: string;
  from_date?: string;
  to_date?: string;
  company?: string;
  debited_from?: string;
  bill_received?: number;
  is_return?: number;
}

export interface TransactionTrend {
  date: string;
  count: number;
  amount: number;
}

export interface StatusBreakdown {
  status: string;
  count: number;
  amount: number;
}

export interface PaymentMethodBreakdown {
  type: string;
  count: number;
  amount: number;
}

export interface UserAnalytics {
  total_transactions: number;
  total_amount: number;
  average_transaction: number;
  success_rate: number;
  status_breakdown: StatusBreakdown[];
  transfer_type_breakdown: PaymentMethodBreakdown[];
  transaction_trends: TransactionTrend[];
  highest_transaction: number;
  lowest_transaction: number;
  bills_received: number;
  bills_pending: number;
  returns: number;
  most_used_method?: string;
  pending_amount: number;
  success_count: number;
  failed_count: number;
}

