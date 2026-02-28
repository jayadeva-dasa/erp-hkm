// Types for Asset Reco module

export interface AssetRecoItem {
  name: string;
  asset_category: string; // Links to standard ERPNext Asset Category
  company: string | null;
  docstatus: number;
  location: string | null;
  custodian: string | null; // Actually custodian_department (Execution Department)
  custodian_department?: string | null;
  purchased_date: string | null;
  purchased_amount: number | null;
  image_urls: string[];
  secondary_custodian: string | null;
  remarks: string | null;
  availability_status?: 'New' | 'Available' | null;
  asset_id?: string | null;
  asset_name?: string | null;
  specifications?: SpecificationValue[];
}

export interface Specification {
  name: string; // The specification ID (e.g., "RAM Capacity")
  specification_name: string; // Display name
  data_type: 'Text' | 'Number' | 'Select' | 'Date' | 'Checkbox';
  options?: string | null; // For Select type (comma-separated values)
  is_mandatory?: number;
}

export interface SpecificationValue {
  name?: string; // Row ID in child table
  specification: string; // Link to HKM Asset Specification
  specification_name?: string; // Display name (auto-filled)
  data_type?: string; // Data type (auto-filled)
  value: string;
  idx?: number;
}

export interface AvailableAsset {
  asset_id: string;
  asset_name: string;
  purchased_date: string | null;
  purchased_amount: number | null;
  asset_category: string;
}

