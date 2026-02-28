// TypeScript types for Eagle View module

export interface EagleViewFilters {
  company?: string;
  report_view: 'Dimension View' | 'Detailed View' | 'Multi Dimension View';
  time_period: 'Cumulative' | 'Day Wise' | 'Week Wise' | 'Month Wise' | 'Quarter Wise';
  report_type: string;
  dimension: string;
  dimension_value: string[];
  account?: string[];
  from_date: string;
  to_date: string;
  include_adjustment: boolean;
  internal_adjustment_type?: string[];
  include_stock_asset: boolean;
  include_disabled_dimension: boolean;
  hide_not_tagged_entries: boolean;
  exclude_period_closing_entries: boolean;
  render_as_tree_view: boolean;
  // Additional filters for multiple dimensions and accounts
  additional_accounts?: string[];
  additional_dimensions?: Array<{
    dimension: string;
    values: string[];
  }>;
  // Multi Dimension View specific filters
  main_dimension?: string;
  main_dimension_value?: string[];
  secondary_dimension?: string;
  secondary_dimension_value?: string[];
}

export interface DimensionOption {
  value: string;
  label: string;
  fieldname: string;
}

export interface SelectOption {
  value: string;
  label: string;
}

export interface EagleViewRow {
  name: string;
  total_inc?: number;
  total_exp?: number;
  total_net?: number;
  indent?: number;
  is_group?: number;
  disabled?: number; // 1 if disabled, 0 if enabled (only present when include_disabled_dimension is true)
  children?: EagleViewRow[];
  // Dynamic keys for adjustment types (e.g., manual_inc, manual_exp, auto_transfer_inc, etc.)
  // Dynamic keys for period-wise data (e.g., 2024-01_inc, 2024-01_exp, etc.)
  [key: string]: any;
}

export interface PeriodColumn {
  key: string;
  label: string;
}

export interface SecondaryDimensionColumn {
  key: string;
  label: string;
  value: string;
}

export interface EagleViewResponseMetadata {
  periods?: PeriodColumn[];
  has_periods?: boolean;
  secondary_dimensions?: SecondaryDimensionColumn[];
  has_secondary_dimensions?: boolean;
  main_dimension?: string;
  main_dimension_label?: string;
  secondary_dimension?: string;
  secondary_dimension_label?: string;
  from_date?: string;
  to_date?: string;
}

export interface EagleViewResponse {
  data: EagleViewRow[];
  metadata?: EagleViewResponseMetadata;
}

export interface ApiResponse<T> {
  status: 'success' | 'error';
  data?: T;
  message?: string;
}

