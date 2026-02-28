// Eagle View Report Page
import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  useToast,
  VStack,
  HStack,
  Heading,
  Text,
} from '@chakra-ui/react';
import { EagleViewFiltersComponent } from '../components/EagleViewFilters';
import { EagleViewTable } from '../components/EagleViewTable';
import { ErrorBoundary } from '../components/ErrorBoundary';
import type { EagleViewFilters, EagleViewRow, EagleViewResponseMetadata } from '../types';
import { eagleViewApi } from '../api/eagleViewApi';
import { loadUserJSON, saveUserJSON } from '../../../utils/storage';

const FILTERS_STORAGE_KEY = 'eagleview_filters';
const EXPANDED_STORAGE_KEY = 'eagleview_expanded_rows';

const EagleViewPage: React.FC = () => {
  const toast = useToast();
  
  // Get current fiscal year dates
  const getCurrentFiscalYear = () => {
    const today = new Date();
    const currentYear = today.getFullYear();
    const currentMonth = today.getMonth() + 1; // JavaScript months are 0-indexed
    
    // Fiscal year starts from April 1st
    if (currentMonth >= 4) {
      // From April to December
      return {
        from: `${currentYear}-04-01`,
        to: `${currentYear + 1}-03-31`,
      };
    } else {
      // From January to March
      return {
        from: `${currentYear - 1}-04-01`,
        to: `${currentYear}-03-31`,
      };
    }
  };

  const fiscalYear = getCurrentFiscalYear();

  // Try to load filters from user-specific localStorage
  const getInitialFilters = (): EagleViewFilters => {
    try {
      // Load user-specific filters
      const saved = loadUserJSON(FILTERS_STORAGE_KEY);
      if (saved) {
        const filters = {
          ...saved,
          // Ensure dates are valid (required for Multi Dimension View and other views)
          from_date: saved.from_date || fiscalYear.from,
          to_date: saved.to_date || fiscalYear.to,
        };
        
        // Ensure Multi Dimension View has required fields
        if (filters.report_view === 'Multi Dimension View') {
          if (!filters.main_dimension) {
            filters.main_dimension = 'Cost Head';
          }
          if (!filters.secondary_dimension) {
            filters.secondary_dimension = 'Cost Center';
          }
          // Ensure dates are set for Multi Dimension View
          if (!filters.from_date) {
            filters.from_date = fiscalYear.from;
          }
          if (!filters.to_date) {
            filters.to_date = fiscalYear.to;
          }
        }
        
        return filters;
      }
    } catch (error) {
      console.error('Failed to load saved filters:', error);
    }
    
    // Default filters
    return {
      report_view: 'Dimension View',
      time_period: 'Cumulative',
      report_type: 'Both Income and Expenses',
      dimension: 'Cost Head',
      dimension_value: [],
      from_date: fiscalYear.from,
      to_date: fiscalYear.to,
      include_adjustment: true,
      include_stock_asset: true,
      include_disabled_dimension: false,
      hide_not_tagged_entries: false,
      exclude_period_closing_entries: true,
      render_as_tree_view: true,
      additional_accounts: [],
      additional_dimensions: [],
    };
  };

  const [filters, setFilters] = useState<EagleViewFilters>(getInitialFilters());
  const [reportData, setReportData] = useState<EagleViewRow[]>([]);
  const [metadata, setMetadata] = useState<EagleViewResponseMetadata | undefined>();
  const [loading, setLoading] = useState(false);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(() => {
    // Load expanded rows from user-specific localStorage
    try {
      const saved = loadUserJSON(EXPANDED_STORAGE_KEY);
      if (saved && Array.isArray(saved)) {
        return new Set(saved);
      }
    } catch (error) {
      console.error('Failed to load expanded rows:', error);
    }
    return new Set<string>();
  });

  // Save filters to user-specific localStorage whenever they change
  useEffect(() => {
    try {
      saveUserJSON(FILTERS_STORAGE_KEY, filters);
    } catch (error) {
      console.error('Failed to save filters:', error);
    }
  }, [filters]);

  // Save expanded rows to user-specific localStorage whenever they change
  useEffect(() => {
    try {
      saveUserJSON(EXPANDED_STORAGE_KEY, Array.from(expandedRows));
    } catch (error) {
      console.error('Failed to save expanded rows:', error);
    }
  }, [expandedRows]);

  // Clear report data when view changes to prevent blank screen
  useEffect(() => {
    // Clear data when switching between views to prevent rendering issues
    setReportData([]);
    setMetadata(undefined);
  }, [filters.report_view]);

  const handleFiltersChange = (newFilters: EagleViewFilters) => {
    // Clear data immediately when view changes to prevent rendering issues
    if (newFilters.report_view !== filters.report_view) {
      setReportData([]);
      setMetadata(undefined);
    }
    setFilters(newFilters);
  };

  const handleExpandedRowsChange = (newExpanded: Set<string>) => {
    setExpandedRows(newExpanded);
  };

  const handleSearch = async () => {
    // Prevent multiple simultaneous requests
    if (loading) {
      return;
    }
    
    try {
      setLoading(true);
      setReportData([]);
      setMetadata(undefined);
      
      console.log('Fetching data with filters:', filters);
      
      // Add timeout to prevent hanging
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Request timeout: The request took too long to complete')), 60000); // 60 second timeout
      });
      
      const response = await Promise.race([
        eagleViewApi.getEagleViewData(filters),
        timeoutPromise
      ]) as any;
      
      console.log('Received response:', response);
      console.log('Response type:', typeof response);
      console.log('Is array:', Array.isArray(response));
      
      // Ensure response has the expected structure
      if (!response) {
        throw new Error('Empty response from server');
      }
      
      // Handle both response formats: { data: [...], metadata: {...} } or just { data: [...] }
      let responseData: any[] = [];
      let responseMetadata: any = undefined;
      
      if (Array.isArray(response)) {
        // Direct array response
        responseData = response;
      } else if (response && typeof response === 'object') {
        // Object response with data and/or metadata
        if (Array.isArray(response.data)) {
          responseData = response.data;
          responseMetadata = response.metadata;
        } else if (response.data && typeof response.data === 'object' && Array.isArray(response.data.data)) {
          // Nested data structure: { data: { data: [...], metadata: {...} } }
          responseData = response.data.data;
          responseMetadata = response.data.metadata || response.metadata;
        } else {
          console.error('Unexpected response structure:', response);
          throw new Error('Invalid response structure: data is not an array');
        }
      } else {
        console.error('Invalid response type:', typeof response, response);
        throw new Error('Invalid response format: expected object or array');
      }
      
      // Ensure data is always an array
      if (!Array.isArray(responseData)) {
        console.error('Invalid data format received:', responseData);
        responseData = []; // Fallback to empty array instead of throwing
      }
      
      console.log('Processed data length:', responseData.length);
      console.log('Processed metadata:', responseMetadata);
      if (responseMetadata) {
        console.log('Metadata has_secondary_dimensions:', responseMetadata.has_secondary_dimensions);
        console.log('Metadata secondary_dimensions count:', responseMetadata.secondary_dimensions?.length || 0);
      }
      
      setReportData(responseData);
      setMetadata(responseMetadata);
      
      toast({
        title: 'Success',
        description: `Loaded ${responseData.length} records`,
        status: 'success',
        duration: 2000,
        isClosable: true,
      });
    } catch (error: any) {
      console.error('Error fetching report data:', error);
      console.error('Error details:', error.response);
      
      // Ensure data is cleared on error
      setReportData([]);
      setMetadata(undefined);
      
      toast({
        title: 'Error',
        description: error.message || 'Failed to fetch report data',
        status: 'error',
        duration: 4000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box minH="100vh" bg="gray.50" position="relative" overflow="visible">
      <Box bg="white" borderBottom="1px" borderColor="gray.200" px={6} py={3} position="relative" zIndex={1} overflow="visible">
        <HStack spacing={3} align="center" flexWrap="nowrap" overflowX="auto" overflowY="visible" position="relative">
          {/* Compact Title */}
          <Box flexShrink={0} whiteSpace="nowrap">
            <Heading size="sm" fontWeight="600" color="gray.700" mb={0}>
              HKM Eagle View
            </Heading>
          </Box>

          {/* Filters in same row */}
          <Box flex="1" minW="0" overflowX="auto" overflowY="visible" position="relative" zIndex={100}>
            <EagleViewFiltersComponent
              filters={filters}
              onFiltersChange={handleFiltersChange}
              onSearch={handleSearch}
              loading={loading}
              compactMode={true}
            />
          </Box>
        </HStack>
      </Box>
      
      <Container maxW="100%" px={6} py={3}>
        <VStack spacing={3} align="stretch">
          {/* Table */}
          <ErrorBoundary>
            <EagleViewTable
              key={`${filters.report_view || 'default'}-${filters.dimension || filters.main_dimension || 'default'}-${filters.secondary_dimension || 'default'}`}
              data={Array.isArray(reportData) ? reportData : []}
              loading={loading}
              reportType={filters.report_type}
              reportView={filters.report_view}
              metadata={metadata}
              expandedRows={expandedRows}
              onExpandedRowsChange={handleExpandedRowsChange}
              onReportTypeChange={(newType) => {
                const updatedFilters = { ...filters, report_type: newType };
                setFilters(updatedFilters);
              }}
              renderAsTreeView={filters.render_as_tree_view ?? true}
              filters={filters}
            />
          </ErrorBoundary>
        </VStack>
      </Container>
    </Box>
  );
};

export default EagleViewPage;

