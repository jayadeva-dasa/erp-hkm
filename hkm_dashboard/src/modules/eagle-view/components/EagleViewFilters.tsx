// Eagle View Filters Component
import React, { useState, useEffect } from 'react';
import {
  Box,
  SimpleGrid,
  FormControl,
  FormLabel,
  Select,
  Input,
  Checkbox,
  Button,
  VStack,
  HStack,
  useToast,
  Text,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  IconButton,
  ButtonGroup,
} from '@chakra-ui/react';
import { SettingsIcon, AddIcon } from '@chakra-ui/icons';
import type { EagleViewFilters, DimensionOption, SelectOption } from '../types';
import { eagleViewApi } from '../api/eagleViewApi';
import { SearchableMultiSelect } from './SearchableMultiSelect';

interface EagleViewFiltersProps {
  filters: EagleViewFilters;
  onFiltersChange: (filters: EagleViewFilters) => void;
  onSearch: () => void;
  loading?: boolean;
  compactMode?: boolean;
}

export const EagleViewFiltersComponent: React.FC<EagleViewFiltersProps> = ({
  filters,
  onFiltersChange,
  onSearch,
  loading = false,
  compactMode = false,
}) => {
  const toast = useToast();
  const { isOpen, onOpen, onClose } = useDisclosure();
  const { isOpen: isAdditionalOpen, onOpen: onAdditionalOpen, onClose: onAdditionalClose } = useDisclosure();
  const [dimensions, setDimensions] = useState<DimensionOption[]>([]);
  const [dimensionValues, setDimensionValues] = useState<SelectOption[]>([]);
  const [companies, setCompanies] = useState<SelectOption[]>([]);
  const [accounts, setAccounts] = useState<SelectOption[]>([]);
  const [adjustmentTypes, setAdjustmentTypes] = useState<SelectOption[]>([]);
  // Store dimension values for additional dimensions
  const [additionalDimensionValues, setAdditionalDimensionValues] = useState<Record<string, SelectOption[]>>({});
  const [isLoadingAccounts, setIsLoadingAccounts] = useState(false);
  // Multi-dimension view specific state
  const [mainDimensionValues, setMainDimensionValues] = useState<SelectOption[]>([]);
  const [secondaryDimensionValues, setSecondaryDimensionValues] = useState<SelectOption[]>([]);

  // Load initial data
  useEffect(() => {
    loadInitialData();
  }, []);

  // Load dimension values when dimension changes (skip for Account)
  useEffect(() => {
    if (filters.dimension && filters.dimension !== 'Account') {
      loadDimensionValues(filters.dimension);
    } else if (filters.dimension === 'Account') {
      // Always load accounts when Account dimension is selected
      if (accounts.length === 0) {
        loadAccounts();
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.dimension]);

  // Load main dimension values when main_dimension changes (for Multi Dimension View)
  useEffect(() => {
    if (filters.report_view === 'Multi Dimension View' && filters.main_dimension) {
      if (filters.main_dimension === 'Account') {
        // For Account dimension, use accounts
        if (accounts.length > 0) {
          // Map accounts to main dimension values format
          setMainDimensionValues(accounts.map(acc => ({ value: acc.value, label: acc.label })));
        } else {
          // Load accounts if not already loaded
          loadAccounts().then(() => {
            // After loading, set main dimension values
            // This will be handled by the accounts state update
          });
        }
      } else {
        // For other dimensions, load dimension values
        loadMainDimensionValues(filters.main_dimension);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.main_dimension, filters.report_view]);

  // Update main dimension values when accounts change (for Account main dimension)
  useEffect(() => {
    if (filters.report_view === 'Multi Dimension View' && 
        filters.main_dimension === 'Account' && 
        accounts.length > 0) {
      // Map accounts to main dimension values format
      setMainDimensionValues(accounts.map(acc => ({ value: acc.value, label: acc.label })));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accounts, filters.main_dimension, filters.report_view]);

  // Load secondary dimension values when secondary_dimension changes (for Multi Dimension View)
  useEffect(() => {
    if (filters.report_view === 'Multi Dimension View' && filters.secondary_dimension) {
      if (filters.secondary_dimension === 'Account') {
        // For Account dimension, use accounts
        console.log('Account selected as secondary dimension, accounts.length:', accounts.length);
        if (accounts.length > 0) {
          // Map accounts to secondary dimension values format
          const mappedAccounts = accounts.map(acc => ({ value: acc.value, label: acc.label }));
          console.log('Setting secondaryDimensionValues from accounts:', mappedAccounts.length, 'accounts');
          setSecondaryDimensionValues(mappedAccounts);
        } else {
          // Load accounts if not already loaded
          console.log('Accounts not loaded yet, loading accounts...');
          loadAccounts().then((loadedAccounts) => {
            console.log('Accounts loaded:', loadedAccounts.length, 'accounts');
            // Map accounts to secondary dimension values format
            const mappedAccounts = loadedAccounts.map((acc: SelectOption) => ({ value: acc.value, label: acc.label }));
            setSecondaryDimensionValues(mappedAccounts);
          }).catch((error) => {
            console.error('Error loading accounts:', error);
          });
        }
      } else {
        // For other dimensions, load dimension values
        loadSecondaryDimensionValues(filters.secondary_dimension);
      }
    } else {
      // Clear secondary dimension values when not in Multi Dimension View or no secondary dimension selected
      setSecondaryDimensionValues([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.secondary_dimension, filters.report_view]);

  // Update secondary dimension values when accounts change (for Account secondary dimension)
  useEffect(() => {
    if (filters.report_view === 'Multi Dimension View' && 
        filters.secondary_dimension === 'Account' && 
        accounts.length > 0) {
      // Map accounts to secondary dimension values format
      const mappedAccounts = accounts.map(acc => ({ value: acc.value, label: acc.label }));
      console.log('Updating secondaryDimensionValues from accounts state change:', mappedAccounts.length, 'accounts');
      setSecondaryDimensionValues(mappedAccounts);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accounts, filters.secondary_dimension, filters.report_view]);

  // Load accounts when modal opens (for additional accounts filter)
  useEffect(() => {
    if (isOpen && accounts.length === 0) {
      loadAccounts();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  const loadInitialData = async () => {
    try {
      const [dimsData, companiesData, adjustTypesData, accountsData] = await Promise.all([
        eagleViewApi.getAccountingDimensions(),
        eagleViewApi.getCompanies(),
        eagleViewApi.getInternalAdjustmentTypes(),
        eagleViewApi.getAccounts(), // Load accounts on initial load
      ]);
      
      // Add Account as a dimension option (frontend only)
      const dimensionsWithAccount = [
        ...dimsData,
        { value: 'Account', label: 'Account', fieldname: 'account' }
      ];
      
      setDimensions(dimensionsWithAccount);
      setCompanies([{ value: '', label: 'All Companies' }, ...companiesData]);
      setAdjustmentTypes(adjustTypesData);
      setAccounts(accountsData); // Set accounts on initial load
    } catch (error: any) {
      console.error('Error in loadInitialData:', error);
      toast({
        title: 'Error',
        description: error?.message || 'Failed to load filter options',
        status: 'error',
        duration: 4000,
      });
    }
  };

  const loadDimensionValues = async (dimension: string, search: string = '') => {
    try {
      const values = await eagleViewApi.getDimensionValues(dimension, search);
      setDimensionValues(values);
      return values;
    } catch (error: any) {
      console.error('Error loading dimension values:', error);
      toast({
        title: 'Error',
        description: error?.message || 'Failed to load dimension values',
        status: 'error',
        duration: 3000,
      });
      return [];
    }
  };

  const loadMainDimensionValues = async (dimension: string, search: string = '') => {
    try {
      const values = await eagleViewApi.getDimensionValues(dimension, search);
      setMainDimensionValues(values);
      return values;
    } catch (error: any) {
      console.error('Error loading main dimension values:', error);
      toast({
        title: 'Error',
        description: error?.message || 'Failed to load main dimension values',
        status: 'error',
        duration: 3000,
      });
      return [];
    }
  };

  const loadSecondaryDimensionValues = async (dimension: string, search: string = '') => {
    try {
      const values = await eagleViewApi.getDimensionValues(dimension, search);
      setSecondaryDimensionValues(values);
      return values;
    } catch (error: any) {
      console.error('Error loading secondary dimension values:', error);
      toast({
        title: 'Error',
        description: error?.message || 'Failed to load secondary dimension values',
        status: 'error',
        duration: 3000,
      });
      return [];
    }
  };

  // Handle dimension search with optimized debounce
  const dimensionSearchTimeoutRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);
  const handleDimensionSearch = React.useCallback((searchTerm: string) => {
    if (dimensionSearchTimeoutRef.current) {
      clearTimeout(dimensionSearchTimeoutRef.current);
    }
    
    // If empty search, load all values immediately
    if (!searchTerm.trim()) {
      if (filters.dimension && filters.dimension !== 'Account') {
        loadDimensionValues(filters.dimension, '');
      }
      return;
    }
    
    const debounceTime = searchTerm.length <= 2 ? 500 : 200;
    
    dimensionSearchTimeoutRef.current = setTimeout(() => {
      if (filters.dimension && filters.dimension !== 'Account') {
        loadDimensionValues(filters.dimension, searchTerm);
      }
    }, debounceTime);
  }, [filters.dimension]);

  // Handle main dimension search with optimized debounce
  const mainDimensionSearchTimeoutRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);
  const handleMainDimensionSearch = React.useCallback((searchTerm: string) => {
    if (mainDimensionSearchTimeoutRef.current) {
      clearTimeout(mainDimensionSearchTimeoutRef.current);
    }
    
    // If empty search, load all values immediately
    if (!searchTerm.trim()) {
      if (filters.main_dimension) {
        loadMainDimensionValues(filters.main_dimension, '');
      }
      return;
    }
    
    const debounceTime = searchTerm.length <= 2 ? 500 : 200;
    
    mainDimensionSearchTimeoutRef.current = setTimeout(() => {
      if (filters.main_dimension) {
        loadMainDimensionValues(filters.main_dimension, searchTerm);
      }
    }, debounceTime);
  }, [filters.main_dimension]);

  // Handle secondary dimension search with optimized debounce (except Account which has its own handler)
  const secondaryDimensionSearchTimeoutRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);
  const handleSecondaryDimensionSearch = React.useCallback((searchTerm: string) => {
    if (secondaryDimensionSearchTimeoutRef.current) {
      clearTimeout(secondaryDimensionSearchTimeoutRef.current);
    }
    
    // Skip if Account (has its own handler)
    if (filters.secondary_dimension === 'Account') {
      return;
    }
    
    // If empty search, load all values immediately
    if (!searchTerm.trim()) {
      if (filters.secondary_dimension) {
        loadSecondaryDimensionValues(filters.secondary_dimension, '');
      }
      return;
    }
    
    const debounceTime = searchTerm.length <= 2 ? 500 : 200;
    
    secondaryDimensionSearchTimeoutRef.current = setTimeout(() => {
      if (filters.secondary_dimension) {
        loadSecondaryDimensionValues(filters.secondary_dimension, searchTerm);
      }
    }, debounceTime);
  }, [filters.secondary_dimension]);

  const loadDimensionValuesForAdditional = async (dimension: string, index: number, search: string = '') => {
    try {
      const values = await eagleViewApi.getDimensionValues(dimension, search);
      setAdditionalDimensionValues(prev => ({
        ...prev,
        [`${dimension}_${index}`]: values
      }));
      return values;
    } catch (error: any) {
      console.error('Error loading dimension values for additional filter:', error);
      toast({
        title: 'Error',
        description: error?.message || 'Failed to load dimension values',
        status: 'error',
        duration: 3000,
      });
      return [];
    }
  };

  // Handle additional dimension search with optimized debounce
  const additionalDimensionSearchTimeoutRefs = React.useRef<Record<string, ReturnType<typeof setTimeout> | null>>({});
  const handleAdditionalDimensionSearch = React.useCallback((dimension: string, index: number, searchTerm: string) => {
    const key = `${dimension}_${index}`;
    if (additionalDimensionSearchTimeoutRefs.current[key]) {
      clearTimeout(additionalDimensionSearchTimeoutRefs.current[key]!);
    }
    
    // If empty search, load all values immediately
    if (!searchTerm.trim()) {
      loadDimensionValuesForAdditional(dimension, index, '');
      return;
    }
    
    const debounceTime = searchTerm.length <= 2 ? 500 : 200;
    
    additionalDimensionSearchTimeoutRefs.current[key] = setTimeout(() => {
      loadDimensionValuesForAdditional(dimension, index, searchTerm);
    }, debounceTime);
  }, []);

  const loadAccounts = async (search: string = ''): Promise<SelectOption[]> => {
    try {
      setIsLoadingAccounts(true);
      const accountsData = await eagleViewApi.getAccounts(search);
      // Always replace accounts - backend already filters by search term
      // This ensures we get the correct filtered results
      setAccounts(accountsData);
      return accountsData;
    } catch (error) {
      console.error('Error loading accounts:', error);
      return [];
    } finally {
      setIsLoadingAccounts(false);
    }
  };

  // Handle account search with optimized debounce
  const searchTimeoutRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);
  const handleAccountSearch = React.useCallback((searchTerm: string) => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    
    // If empty search, load all accounts immediately
    if (!searchTerm.trim()) {
      loadAccounts('');
      return;
    }
    
    // If search term is very short (1-2 chars), wait longer to avoid too many requests
    // If longer, search faster for better UX
    const debounceTime = searchTerm.length <= 2 ? 500 : 200;
    
    searchTimeoutRef.current = setTimeout(() => {
      loadAccounts(searchTerm);
    }, debounceTime);
  }, []);

  // Handle secondary account search with optimized debounce (for Account secondary dimension)
  const secondaryAccountSearchTimeoutRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);
  const handleSecondaryAccountSearch = React.useCallback((searchTerm: string) => {
    if (secondaryAccountSearchTimeoutRef.current) {
      clearTimeout(secondaryAccountSearchTimeoutRef.current);
    }
    
    // Optimized debounce: shorter for longer search terms
    const debounceTime = searchTerm.length <= 2 ? 400 : 150;
    
    secondaryAccountSearchTimeoutRef.current = setTimeout(async () => {
      try {
        // If search term is empty, reload all accounts (or use already loaded accounts)
        if (!searchTerm.trim()) {
          // If we already have accounts loaded, use them (don't reload)
          if (accounts.length > 0) {
            const mappedAccounts = accounts.map(acc => ({ value: acc.value, label: acc.label }));
            setSecondaryDimensionValues(mappedAccounts);
          } else {
            // Load all accounts if not already loaded
            const allAccounts = await loadAccounts('');
            const mappedAccounts = allAccounts.map(acc => ({ value: acc.value, label: acc.label }));
            setSecondaryDimensionValues(mappedAccounts);
          }
        } else {
          // Search for accounts matching the term
          const searchedAccounts = await loadAccounts(searchTerm);
          // Update secondary dimension values with searched accounts
          if (filters.secondary_dimension === 'Account') {
            const mappedAccounts = searchedAccounts.map(acc => ({ value: acc.value, label: acc.label }));
            setSecondaryDimensionValues(mappedAccounts);
          }
        }
      } catch (error) {
        console.error('Error searching accounts for secondary dimension:', error);
      }
    }, debounceTime);
  }, [filters.secondary_dimension, accounts]);

  const handleFilterChange = (key: keyof EagleViewFilters, value: any) => {
    const newFilters = { ...filters, [key]: value };
    
    // Handle dependent filters
    if (key === 'report_view') {
      if (value === 'Detailed View') {
        newFilters.report_type = 'Both Income and Expenses';
        newFilters.hide_not_tagged_entries = true;
      } else if (value === 'Dimension View') {
        newFilters.report_type = 'Both Income and Expenses';
        newFilters.hide_not_tagged_entries = false;
      } else if (value === 'Multi Dimension View') {
        // Multi Dimension View doesn't use report_type, but set defaults
        newFilters.hide_not_tagged_entries = false;
        // Initialize main and secondary dimensions if not set
        if (!newFilters.main_dimension) {
          newFilters.main_dimension = 'Cost Head';
        }
        if (!newFilters.secondary_dimension) {
          newFilters.secondary_dimension = 'Cost Center';
        }
      }
    }
    
    if (key === 'include_adjustment' && !value) {
      newFilters.internal_adjustment_type = [];
    }
    
    // When dimension changes, clear dimension_value and account selection
    if (key === 'dimension') {
      newFilters.dimension_value = [];
      if (value === 'Account') {
        // Load accounts when Account dimension is selected
        loadAccounts();
        // Clear account selection when switching to Account dimension
        newFilters.account = [];
      } else {
        // Clear account selection when switching away from Account dimension
        newFilters.account = [];
      }
    }

    // When main_dimension changes, clear main_dimension_value
    if (key === 'main_dimension') {
      newFilters.main_dimension_value = [];
    }

    // When secondary_dimension changes, clear secondary_dimension_value
    if (key === 'secondary_dimension') {
      newFilters.secondary_dimension_value = [];
    }
    
    onFiltersChange(newFilters);
  };

  const getReportTypeOptions = () => {
    if (filters.report_view === 'Detailed View') {
      return ['Detailed Income', 'Detailed Expense'];
    }
    return ['Both Income and Expenses', 'Only Incomes', 'Only Expense', 'Net Profit'];
  };

  if (compactMode) {
    return (
      <Box width="100%" position="relative" zIndex={100} overflow="visible">
        <HStack spacing={2} align="center" flexWrap="nowrap" width="100%" overflow="visible" position="relative">
          {/* Report View - First Step */}
          <FormControl minW="120px">
            <Select
              size="sm"
              value={filters.report_view}
              onChange={(e) => handleFilterChange('report_view', e.target.value)}
            >
              <option value="Dimension View">Dimension View</option>
              <option value="Detailed View">Detailed View</option>
              <option value="Multi Dimension View">Multi Dimension View</option>
            </Select>
          </FormControl>

          {/* Multi Dimension View - Main Dimension */}
          {filters.report_view === 'Multi Dimension View' ? (
            <>
              <FormControl minW="140px">
                <Select
                  size="sm"
                  value={filters.main_dimension || 'Cost Head'}
                  onChange={(e) => handleFilterChange('main_dimension', e.target.value)}
                >
                  {dimensions.map((dim) => (
                    <option key={dim.value} value={dim.value}>
                      {dim.label} (Main)
                    </option>
                  ))}
                </Select>
              </FormControl>
              <Box minW="180px" position="relative" zIndex={10} overflow="visible">
                <SearchableMultiSelect
                  options={mainDimensionValues}
                  value={filters.main_dimension_value || []}
                  onChange={(selected) => handleFilterChange('main_dimension_value', selected)}
                  placeholder="Select main dimension values..."
                  onSearch={handleMainDimensionSearch}
                />
              </Box>
              <FormControl minW="140px">
                <Select
                  size="sm"
                  value={filters.secondary_dimension || 'Cost Center'}
                  onChange={(e) => handleFilterChange('secondary_dimension', e.target.value)}
                >
                  {dimensions.map((dim) => (
                    <option key={dim.value} value={dim.value}>
                      {dim.label} (Secondary)
                    </option>
                  ))}
                </Select>
              </FormControl>
              <Box minW="180px" position="relative" zIndex={10} overflow="visible">
                <SearchableMultiSelect
                  options={secondaryDimensionValues}
                  value={filters.secondary_dimension_value || []}
                  onChange={(selected) => handleFilterChange('secondary_dimension_value', selected)}
                  placeholder="Select secondary dimension values..."
                  onSearch={filters.secondary_dimension === 'Account' ? handleSecondaryAccountSearch : handleSecondaryDimensionSearch}
                  isLoading={filters.secondary_dimension === 'Account' && isLoadingAccounts}
                />
              </Box>
            </>
          ) : (
            <>
              {/* Select Dimension - Second Step */}
              <FormControl minW="140px">
                <Select
                  size="sm"
                  value={filters.dimension}
                  onChange={(e) => handleFilterChange('dimension', e.target.value)}
                >
                  {dimensions.map((dim) => (
                    <option key={dim.value} value={dim.value}>
                      {dim.label}
                    </option>
                  ))}
                </Select>
              </FormControl>

              {/* Time Period */}
              {filters.report_view !== 'Detailed View' && (
            <FormControl minW="120px">
              <Select
                size="sm"
                value={filters.time_period}
                onChange={(e) => handleFilterChange('time_period', e.target.value)}
              >
                <option value="Cumulative">Cumulative</option>
                <option value="Day Wise">Day Wise</option>
                <option value="Week Wise">Week Wise</option>
                <option value="Month Wise">Month Wise</option>
                <option value="Quarter Wise">Quarter Wise</option>
              </Select>
            </FormControl>
          )}

          {/* Dimension Values or Account - Multiselect */}
          {filters.dimension === 'Account' ? (
            <Box minW="180px" position="relative" zIndex={10} overflow="visible">
              <SearchableMultiSelect
                options={accounts}
                value={filters.account || []}
                onChange={(selected) => handleFilterChange('account', selected)}
                placeholder="Select accounts..."
                onSearch={handleAccountSearch}
                isLoading={isLoadingAccounts}
              />
            </Box>
          ) : (
            <Box minW="180px" position="relative" zIndex={10} overflow="visible">
              <SearchableMultiSelect
                options={dimensionValues}
                value={filters.dimension_value || []}
                onChange={(selected) => handleFilterChange('dimension_value', selected)}
                placeholder="Select dimension values..."
                onSearch={filters.dimension !== 'Account' ? handleDimensionSearch : undefined}
              />
            </Box>
          )}
            </>
          )}

          {/* Additional Accounts & Dimensions Button */}
          <IconButton
            aria-label="Additional Accounts & Dimensions"
            icon={<AddIcon />}
            size="sm"
            variant="outline"
            onClick={onAdditionalOpen}
            flexShrink={0}
            colorScheme="blue"
          />

          {/* Additional Filters Button */}
          <IconButton
            aria-label="Additional Filters"
            icon={<SettingsIcon />}
            size="sm"
            variant="outline"
            onClick={onOpen}
            flexShrink={0}
          />

          {/* Get Report Button */}
          <Button
            colorScheme="blue"
            size="sm"
            onClick={onSearch}
            isLoading={loading}
            loadingText="Loading..."
            flexShrink={0}
            whiteSpace="nowrap"
          >
            Get Report
          </Button>
        </HStack>

        {/* Additional Filters Modal */}
        <Modal isOpen={isOpen} onClose={onClose} size="xl" blockScrollOnMount={false}>
        <ModalOverlay />
        <ModalContent maxH="90vh" overflow="hidden" display="flex" flexDirection="column">
          <ModalHeader>Additional Filters</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6} overflowY="auto" flex="1">
            <VStack spacing={4} align="stretch">
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                {/* Company */}
                <FormControl>
                  <FormLabel fontSize="sm">Company</FormLabel>
                  <Select
                    size="sm"
                    value={filters.company || ''}
                    onChange={(e) => handleFilterChange('company', e.target.value)}
                  >
                    {companies.map((comp) => (
                      <option key={comp.value} value={comp.value}>
                        {comp.label}
                      </option>
                    ))}
                  </Select>
                </FormControl>

                {/* From Date - Hide only for Cumulative Dimension View */}
                {!(filters.report_view === 'Dimension View' && filters.time_period === 'Cumulative') && (
                  <FormControl>
                    <FormLabel fontSize="sm">From Date</FormLabel>
                    <Input
                      type="date"
                      size="sm"
                      value={filters.from_date}
                      onChange={(e) => handleFilterChange('from_date', e.target.value)}
                    />
                  </FormControl>
                )}

                {/* To Date - Hide only for Cumulative Dimension View */}
                {!(filters.report_view === 'Dimension View' && filters.time_period === 'Cumulative') && (
                  <FormControl>
                    <FormLabel fontSize="sm">To Date</FormLabel>
                    <Input
                      type="date"
                      size="sm"
                      value={filters.to_date}
                      onChange={(e) => handleFilterChange('to_date', e.target.value)}
                    />
                  </FormControl>
                )}
              </SimpleGrid>

              {/* Checkboxes */}
              <VStack spacing={3} align="stretch">
                <Checkbox
                  isChecked={filters.exclude_period_closing_entries}
                  onChange={(e) => handleFilterChange('exclude_period_closing_entries', e.target.checked)}
                >
                  <Text fontSize="sm">Exclude Period Closing Entries</Text>
                </Checkbox>

                <Checkbox
                  isChecked={filters.render_as_tree_view}
                  onChange={(e) => handleFilterChange('render_as_tree_view', e.target.checked)}
                >
                  <Text fontSize="sm">Render as Tree View</Text>
                </Checkbox>

                <Checkbox
                  isChecked={filters.include_stock_asset}
                  onChange={(e) => handleFilterChange('include_stock_asset', e.target.checked)}
                >
                  <Text fontSize="sm">Include Stock & Asset Expenses</Text>
                </Checkbox>

                {(filters.report_view === 'Dimension View' || filters.report_view === 'Multi Dimension View') && (
                  <Checkbox
                    isChecked={filters.include_disabled_dimension}
                    onChange={(e) => handleFilterChange('include_disabled_dimension', e.target.checked)}
                  >
                    <Text fontSize="sm">Include Disabled Dimension</Text>
                  </Checkbox>
                )}

                <FormControl>
                  <Checkbox
                    isChecked={filters.include_adjustment}
                    onChange={(e) => handleFilterChange('include_adjustment', e.target.checked)}
                  >
                    <Text fontSize="sm">Include Adjustment</Text>
                  </Checkbox>
                  
                  {/* Internal Adjustment Type dropdown - only show if Include Adjustment is checked */}
                  {filters.include_adjustment && (
                    <Box mt={2}>
                      <SearchableMultiSelect
                        options={adjustmentTypes}
                        value={filters.internal_adjustment_type || []}
                        onChange={(selected) => handleFilterChange('internal_adjustment_type', selected)}
                        placeholder="Internal Adjustment Type"
                      />
                    </Box>
                  )}
                </FormControl>
              </VStack>

              {/* Modal Action Buttons */}
              <HStack justify="flex-end" mt={4}>
                <Button variant="ghost" onClick={onClose}>
                  Cancel
                </Button>
                <Button colorScheme="blue" onClick={onClose}>
                  Apply Filters
                </Button>
              </HStack>
            </VStack>
          </ModalBody>
        </ModalContent>
      </Modal>

      {/* Additional Accounts & Dimensions Modal */}
      <Modal isOpen={isAdditionalOpen} onClose={onAdditionalClose} size="xl" blockScrollOnMount={false}>
        <ModalOverlay />
        <ModalContent maxH="90vh" overflow="hidden" display="flex" flexDirection="column">
          <ModalHeader>Additional Accounts & Dimensions</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6} overflowY="auto" flex="1">
            <VStack spacing={4} align="stretch">
              {/* Additional Accounts Filter */}
              <FormControl>
                <FormLabel fontSize="sm">Additional Accounts (Optional)</FormLabel>
                <SearchableMultiSelect
                  options={accounts}
                  value={filters.additional_accounts || []}
                  onChange={(selected) => handleFilterChange('additional_accounts', selected)}
                  placeholder="Select additional accounts..."
                  onOpen={() => {
                    // Ensure accounts are loaded when dropdown opens
                    if (accounts.length === 0) {
                      loadAccounts();
                    }
                  }}
                  onSearch={handleAccountSearch}
                  isLoading={isLoadingAccounts}
                />
                <Text fontSize="xs" color="gray.500" mt={1}>
                  Filter by multiple accounts in addition to main dimension filter
                </Text>
              </FormControl>

              {/* Additional Dimensions Filter */}
              <FormControl>
                <FormLabel fontSize="sm">Additional Dimensions (Optional)</FormLabel>
                <VStack spacing={3} align="stretch">
                  {(filters.additional_dimensions || []).map((dimFilter, index) => (
                    <Box key={index} p={3} border="1px" borderColor="gray.200" borderRadius="md">
                      <HStack spacing={2} mb={2}>
                        <Select
                          size="sm"
                          flex={1}
                          value={dimFilter.dimension}
                          onChange={(e) => {
                            const updated = [...(filters.additional_dimensions || [])];
                            updated[index] = { ...updated[index], dimension: e.target.value, values: [] };
                            handleFilterChange('additional_dimensions', updated);
                            // Load dimension values when dimension changes
                            if (e.target.value && e.target.value !== 'Account') {
                              loadDimensionValuesForAdditional(e.target.value, index);
                            }
                          }}
                        >
                          <option value="">Select Dimension</option>
                          {dimensions
                            .filter(d => d.value !== filters.dimension) // Exclude main dimension
                            .map((dim) => (
                              <option key={dim.value} value={dim.value}>
                                {dim.label}
                              </option>
                            ))}
                        </Select>
                        <Button
                          size="sm"
                          colorScheme="red"
                          variant="ghost"
                          onClick={() => {
                            const updated = (filters.additional_dimensions || []).filter((_, i) => i !== index);
                            handleFilterChange('additional_dimensions', updated);
                          }}
                        >
                          Remove
                        </Button>
                      </HStack>
                      {dimFilter.dimension && (
                        <Box>
                          {dimFilter.dimension === 'Account' ? (
                            <SearchableMultiSelect
                              options={accounts}
                              value={dimFilter.values}
                              onChange={(selected) => {
                                const updated = [...(filters.additional_dimensions || [])];
                                updated[index] = { ...updated[index], values: selected };
                                handleFilterChange('additional_dimensions', updated);
                              }}
                              placeholder="Select accounts..."
                              onSearch={handleAccountSearch}
                              isLoading={isLoadingAccounts}
                            />
                          ) : (
                            <SearchableMultiSelect
                              options={additionalDimensionValues[`${dimFilter.dimension}_${index}`] || []}
                              value={dimFilter.values}
                              onChange={(selected) => {
                                const updated = [...(filters.additional_dimensions || [])];
                                updated[index] = { ...updated[index], values: selected };
                                handleFilterChange('additional_dimensions', updated);
                              }}
                              placeholder="Select dimension values..."
                              onSearch={(searchTerm) => handleAdditionalDimensionSearch(dimFilter.dimension, index, searchTerm)}
                              onOpen={() => {
                                // Load values when dropdown opens if not already loaded
                                if (!additionalDimensionValues[`${dimFilter.dimension}_${index}`]) {
                                  loadDimensionValuesForAdditional(dimFilter.dimension, index);
                                }
                              }}
                            />
                          )}
                        </Box>
                      )}
                    </Box>
                  ))}
                  <Button
                    size="sm"
                    colorScheme="blue"
                    variant="outline"
                    leftIcon={<AddIcon />}
                    onClick={() => {
                      const updated = [...(filters.additional_dimensions || []), { dimension: '', values: [] }];
                      handleFilterChange('additional_dimensions', updated);
                    }}
                  >
                    Add Dimension Filter
                  </Button>
                </VStack>
                <Text fontSize="xs" color="gray.500" mt={2}>
                  Add multiple dimension filters for advanced filtering
                </Text>
              </FormControl>
            </VStack>
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  );
  }

  // Non-compact mode (original layout) - kept for backward compatibility
  return (
    <Box bg="white" p={6} borderRadius="lg" boxShadow="sm" mb={4}>
      <VStack spacing={4} align="stretch">
        <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4}>
          {/* Report View - First Step */}
          <FormControl>
            <FormLabel fontSize="sm">Report View</FormLabel>
            <Select
              size="sm"
              value={filters.report_view}
              onChange={(e) => handleFilterChange('report_view', e.target.value)}
            >
              <option value="Dimension View">Dimension View</option>
              <option value="Detailed View">Detailed View</option>
              <option value="Multi Dimension View">Multi Dimension View</option>
            </Select>
          </FormControl>

          {/* Multi Dimension View - Main Dimension */}
          {filters.report_view === 'Multi Dimension View' ? (
            <>
              <FormControl>
                <FormLabel fontSize="sm">Main Dimension (Rows)</FormLabel>
                <Select
                  size="sm"
                  value={filters.main_dimension || 'Cost Head'}
                  onChange={(e) => handleFilterChange('main_dimension', e.target.value)}
                >
                  {dimensions.map((dim) => (
                    <option key={dim.value} value={dim.value}>
                      {dim.label}
                    </option>
                  ))}
                </Select>
              </FormControl>
              <FormControl>
                <FormLabel fontSize="sm">Main Dimension Values</FormLabel>
                <SearchableMultiSelect
                  options={mainDimensionValues}
                  value={filters.main_dimension_value || []}
                  onChange={(selected) => handleFilterChange('main_dimension_value', selected)}
                  placeholder="Select main dimension values..."
                />
              </FormControl>
              <FormControl>
                <FormLabel fontSize="sm">Secondary Dimension (Columns)</FormLabel>
                <Select
                  size="sm"
                  value={filters.secondary_dimension || 'Cost Center'}
                  onChange={(e) => handleFilterChange('secondary_dimension', e.target.value)}
                >
                  {dimensions.map((dim) => (
                    <option key={dim.value} value={dim.value}>
                      {dim.label}
                    </option>
                  ))}
                </Select>
              </FormControl>
              <FormControl>
                <FormLabel fontSize="sm">Secondary Dimension Values</FormLabel>
                <SearchableMultiSelect
                  options={secondaryDimensionValues}
                  value={filters.secondary_dimension_value || []}
                  onChange={(selected) => handleFilterChange('secondary_dimension_value', selected)}
                  placeholder="Select secondary dimension values..."
                  onSearch={filters.secondary_dimension === 'Account' ? handleSecondaryAccountSearch : handleSecondaryDimensionSearch}
                  isLoading={filters.secondary_dimension === 'Account' && isLoadingAccounts}
                />
              </FormControl>
            </>
          ) : (
            <>
              {/* Select Dimension - Second Step */}
              <FormControl>
                <FormLabel fontSize="sm">Select Dimension</FormLabel>
                <Select
                  size="sm"
                  value={filters.dimension}
                  onChange={(e) => handleFilterChange('dimension', e.target.value)}
                >
                  {dimensions.map((dim) => (
                    <option key={dim.value} value={dim.value}>
                      {dim.label}
                    </option>
                  ))}
                </Select>
              </FormControl>

              {/* Time Period */}
              {filters.report_view !== 'Detailed View' && (
                <FormControl>
                  <FormLabel fontSize="sm">Time Period</FormLabel>
                  <Select
                    size="sm"
                    value={filters.time_period}
                    onChange={(e) => handleFilterChange('time_period', e.target.value)}
                  >
                    <option value="Cumulative">Cumulative</option>
                    <option value="Day Wise">Day Wise</option>
                    <option value="Week Wise">Week Wise</option>
                    <option value="Month Wise">Month Wise</option>
                    <option value="Quarter Wise">Quarter Wise</option>
                  </Select>
                </FormControl>
              )}

              {/* Report Type */}
              <FormControl>
                <FormLabel fontSize="sm">Report Type</FormLabel>
                <Select
                  size="sm"
                  value={filters.report_type}
                  onChange={(e) => handleFilterChange('report_type', e.target.value)}
                >
                  {getReportTypeOptions().map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </Select>
              </FormControl>

              {/* Dimension Values or Account - Multiselect */}
              {filters.dimension === 'Account' ? (
            <FormControl>
              <FormLabel fontSize="sm">Select Value</FormLabel>
              <Box onClick={() => { if (accounts.length === 0) loadAccounts(); }}>
                <SearchableMultiSelect
                  options={accounts}
                  value={filters.account || []}
                  onChange={(selected) => handleFilterChange('account', selected)}
                  placeholder="Select accounts..."
                  onSearch={handleAccountSearch}
                  isLoading={isLoadingAccounts}
                />
              </Box>
            </FormControl>
          ) : (
            <FormControl>
              <FormLabel fontSize="sm">Select Value</FormLabel>
              <SearchableMultiSelect
                options={dimensionValues}
                value={filters.dimension_value}
                onChange={(selected) => handleFilterChange('dimension_value', selected)}
                placeholder="Select dimension values..."
              />
            </FormControl>
          )}

          {/* Additional Filters Button */}
          <FormControl>
            <FormLabel fontSize="sm">&nbsp;</FormLabel>
            <IconButton
              aria-label="Additional Filters"
              icon={<SettingsIcon />}
              size="sm"
              variant="outline"
              onClick={onOpen}
              width="100%"
            />
          </FormControl>
            </>
          )}
        </SimpleGrid>

        {/* Action Button */}
        <HStack justify="flex-end">
          <Button
            colorScheme="blue"
            size="md"
            onClick={onSearch}
            isLoading={loading}
            loadingText="Loading..."
          >
            Get Report
          </Button>
        </HStack>
      </VStack>

      {/* Additional Filters Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Additional Filters</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <VStack spacing={4} align="stretch">
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                {/* Company */}
                <FormControl>
                  <FormLabel fontSize="sm">Company</FormLabel>
                  <Select
                    size="sm"
                    value={filters.company || ''}
                    onChange={(e) => handleFilterChange('company', e.target.value)}
                  >
                    {companies.map((comp) => (
                      <option key={comp.value} value={comp.value}>
                        {comp.label}
                      </option>
                    ))}
                  </Select>
                </FormControl>

                {/* From Date - Hide only for Cumulative Dimension View */}
                {!(filters.report_view === 'Dimension View' && filters.time_period === 'Cumulative') && (
                  <FormControl>
                    <FormLabel fontSize="sm">From Date</FormLabel>
                    <Input
                      type="date"
                      size="sm"
                      value={filters.from_date}
                      onChange={(e) => handleFilterChange('from_date', e.target.value)}
                    />
                  </FormControl>
                )}

                {/* To Date - Hide only for Cumulative Dimension View */}
                {!(filters.report_view === 'Dimension View' && filters.time_period === 'Cumulative') && (
                  <FormControl>
                    <FormLabel fontSize="sm">To Date</FormLabel>
                    <Input
                      type="date"
                      size="sm"
                      value={filters.to_date}
                      onChange={(e) => handleFilterChange('to_date', e.target.value)}
                    />
                  </FormControl>
                )}
              </SimpleGrid>

              {/* Checkboxes */}
              <VStack spacing={3} align="stretch">
                <Checkbox
                  isChecked={filters.exclude_period_closing_entries}
                  onChange={(e) => handleFilterChange('exclude_period_closing_entries', e.target.checked)}
                >
                  <Text fontSize="sm">Exclude Period Closing Entries</Text>
                </Checkbox>

                <Checkbox
                  isChecked={filters.render_as_tree_view}
                  onChange={(e) => handleFilterChange('render_as_tree_view', e.target.checked)}
                >
                  <Text fontSize="sm">Render as Tree View</Text>
                </Checkbox>

                <Checkbox
                  isChecked={filters.include_stock_asset}
                  onChange={(e) => handleFilterChange('include_stock_asset', e.target.checked)}
                >
                  <Text fontSize="sm">Include Stock & Asset Expenses</Text>
                </Checkbox>

                {(filters.report_view === 'Dimension View' || filters.report_view === 'Multi Dimension View') && (
                  <Checkbox
                    isChecked={filters.include_disabled_dimension}
                    onChange={(e) => handleFilterChange('include_disabled_dimension', e.target.checked)}
                  >
                    <Text fontSize="sm">Include Disabled Dimension</Text>
                  </Checkbox>
                )}

                <FormControl>
                  <Checkbox
                    isChecked={filters.include_adjustment}
                    onChange={(e) => handleFilterChange('include_adjustment', e.target.checked)}
                  >
                    <Text fontSize="sm">Include Adjustment</Text>
                  </Checkbox>
                  
                  {/* Internal Adjustment Type dropdown - only show if Include Adjustment is checked */}
                  {filters.include_adjustment && (
                    <Box mt={2}>
                      <SearchableMultiSelect
                        options={adjustmentTypes}
                        value={filters.internal_adjustment_type || []}
                        onChange={(selected) => handleFilterChange('internal_adjustment_type', selected)}
                        placeholder="Internal Adjustment Type"
                      />
                    </Box>
                  )}
                </FormControl>
              </VStack>

              {/* Modal Action Buttons */}
              <HStack justify="flex-end" mt={4}>
                <Button variant="ghost" onClick={onClose}>
                  Cancel
                </Button>
                <Button colorScheme="blue" onClick={onClose}>
                  Apply Filters
                </Button>
              </HStack>
            </VStack>
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  );
};

