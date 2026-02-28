// S3 File Search API

import type { S3SearchFilters, S3SearchResponse, S3Stats } from '../types';

const API_BASE = '/api/method/hkm.cursor.s3_file_search';

export const s3FileSearchApi = {
  /**
   * Search files in S3 bucket
   */
  async searchFiles(filters: S3SearchFilters = {}): Promise<S3SearchResponse> {
    try {
      const params = new URLSearchParams();
      
      if (filters.search_term) params.append('search_term', filters.search_term);
      if (filters.file_type) params.append('file_type', filters.file_type);
      if (filters.size_min !== undefined) params.append('size_min', filters.size_min.toString());
      if (filters.size_max !== undefined) params.append('size_max', filters.size_max.toString());
      if (filters.date_from) params.append('date_from', filters.date_from);
      if (filters.date_to) params.append('date_to', filters.date_to);
      if (filters.folder_path) params.append('folder_path', filters.folder_path);

      const response = await fetch(`${API_BASE}.search_s3_files?${params.toString()}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Frappe-CSRF-Token': (window as any).frappe?.csrf_token || '',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.message;
    } catch (error) {
      console.error('Error searching S3 files:', error);
      throw error;
    }
  },

  /**
   * Get S3 bucket statistics
   */
  async getStats(): Promise<S3Stats> {
    try {
      const response = await fetch(`${API_BASE}.get_s3_stats`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Frappe-CSRF-Token': (window as any).frappe?.csrf_token || '',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.message;
    } catch (error) {
      console.error('Error getting S3 stats:', error);
      throw error;
    }
  },

  /**
   * Download file from S3
   */
  downloadFile(fileKey: string, fileName: string): void {
    const url = `/api/method/hkm.cursor.s3_file_search.download_s3_file?file_key=${encodeURIComponent(fileKey)}`;
    const link = document.createElement('a');
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  },

  /**
   * Get file preview URL
   */
  getPreviewUrl(fileKey: string): string {
    return `/api/method/hkm.cursor.s3_file_search.get_s3_file_url?file_key=${encodeURIComponent(fileKey)}`;
  },
};

