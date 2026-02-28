// S3 File Search Types

export interface S3File {
  key: string;
  file_name: string;
  size: number;
  size_formatted: string;
  last_modified: string;
  last_modified_formatted: string;
  url: string;
  file_type: string;
  folder_path: string;
}

export interface S3SearchFilters {
  search_term?: string;
  file_type?: string;
  size_min?: number;
  size_max?: number;
  date_from?: string;
  date_to?: string;
  folder_path?: string;
}

export interface S3SearchResponse {
  success: boolean;
  files: S3File[];
  total_count: number;
  filtered_count: number;
  search_term?: string;
  error?: string;
}

export interface S3Stats {
  total_files: number;
  total_size: number;
  total_size_formatted: string;
  file_types: Record<string, number>;
}

