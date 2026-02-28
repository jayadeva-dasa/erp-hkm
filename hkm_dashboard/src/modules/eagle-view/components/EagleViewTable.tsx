// Eagle View Table Component
import React, { useState, useMemo } from 'react';
import {
  Box,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Input,
  InputGroup,
  InputLeftElement,
  Icon,
  Text,
  Spinner,
  Center,
  IconButton,
  Button,
  HStack,
  VStack,
  Flex,
  Badge,
  useDisclosure,
  ButtonGroup,
  Tooltip,
  Checkbox,
  Select,
} from '@chakra-ui/react';
import { SearchIcon, ChevronRightIcon, ChevronDownIcon, DownloadIcon, AttachmentIcon, ArrowUpIcon, ArrowDownIcon } from '@chakra-ui/icons';
import type { EagleViewRow, EagleViewResponseMetadata } from '../types';
import { FileViewerModal } from './FileViewerModal';
import { VoucherViewerModal } from './VoucherViewerModal';
import { CellDetailModal } from './CellDetailModal';

interface EagleViewTableProps {
  data: EagleViewRow[];
  loading?: boolean;
  reportType: string;
  reportView: string;
  metadata?: EagleViewResponseMetadata;
  expandedRows?: Set<string>;
  onExpandedRowsChange?: (expanded: Set<string>) => void;
  onReportTypeChange?: (reportType: string) => void;
  renderAsTreeView?: boolean;
  filters?: any; // Current filters from parent
}

export const EagleViewTable: React.FC<EagleViewTableProps> = ({
  data,
  loading = false,
  reportType,
  reportView,
  metadata,
  expandedRows: controlledExpandedRows,
  onExpandedRowsChange,
  onReportTypeChange,
  renderAsTreeView = true,
  filters,
}) => {
  // Ensure data is always an array
  const safeData = Array.isArray(data) ? data : [];
  
  const [searchTerm, setSearchTerm] = useState('');
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [selectedAttachments, setSelectedAttachments] = useState<any[]>([]);
  const [selectedVoucherNo, setSelectedVoucherNo] = useState('');
  
  // For VoucherViewerModal
  const { isOpen: isVoucherModalOpen, onOpen: onVoucherModalOpen, onClose: onVoucherModalClose } = useDisclosure();
  const [selectedVoucherIndex, setSelectedVoucherIndex] = useState(0);
  
  // For CellDetailModal (Multi Dimension View drill-down)
  const { isOpen: isCellDetailModalOpen, onOpen: onCellDetailModalOpen, onClose: onCellDetailModalClose } = useDisclosure();
  const [selectedMainDimValue, setSelectedMainDimValue] = useState<string | null>(null);
  const [selectedSecondaryDimValue, setSelectedSecondaryDimValue] = useState<string | null>(null);
  const [selectedColumnType, setSelectedColumnType] = useState<'inc' | 'exp' | 'net' | 'both' | null>(null);
  
  // Pagination state (for Detailed View and Multi Dimension View with many rows)
  const [currentPage, setCurrentPage] = useState(1);
  const recordsPerPage = reportView === 'Detailed View' ? 15 : 50; // More rows per page for dimension views
  
  // State to hide columns with all zero values (for Multi Dimension View)
  const [hideZeroColumns, setHideZeroColumns] = useState(false);
  
  // State to hide rows with all zero values
  const [hideEmptyRows, setHideEmptyRows] = useState(false);
  
  // State for sorting (for Multi Dimension View)
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  
  // State for sorting by disabled status
  const [sortByDisabled, setSortByDisabled] = useState<'none' | 'disabled_first' | 'disabled_last'>('none');
  
  // Auto-expand root level items (indent = 0) by default
  const getDefaultExpandedRows = () => {
    const expanded = new Set<string>();
    safeData.forEach((row) => {
      if (row && ((row.indent === 0 || !row.indent) && row.is_group)) {
        expanded.add(row.name);
      }
    });
    return expanded;
  };
  
  // Use controlled or local state for expanded rows
  const [localExpandedRows, setLocalExpandedRows] = useState<Set<string>>(() => getDefaultExpandedRows());
  const expandedRows = controlledExpandedRows || localExpandedRows;
  const setExpandedRows = onExpandedRowsChange || setLocalExpandedRows;

  // Reset expanded rows when data changes (only if not using controlled state)
  React.useEffect(() => {
    if (!controlledExpandedRows) {
      setLocalExpandedRows(getDefaultExpandedRows());
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [safeData, controlledExpandedRows]);

  // Toggle row expansion
  const toggleRow = (rowName: string) => {
    const newSet = new Set(expandedRows);
    if (newSet.has(rowName)) {
      newSet.delete(rowName);
    } else {
      newSet.add(rowName);
    }
    setExpandedRows(newSet);
  };

  // Expand all rows (show all children)
  const expandAll = () => {
    const allExpandableRows = new Set<string>();
    buildTreeStructure.forEach((row) => {
      if (row.hasChildren) {
        allExpandableRows.add(row.name);
      }
    });
    setExpandedRows(allExpandableRows);
  };

  // Collapse all rows (show only parents)
  const collapseAll = () => {
    setExpandedRows(new Set());
  };

  // Build hierarchical structure by analyzing indent levels (only for Dimension View)
  const buildTreeStructure = useMemo(() => {
    // If no data, return empty array
    if (!safeData || safeData.length === 0) {
      return [];
    }

    // Tree structure only for Dimension View and Multi Dimension View
    if (reportView !== 'Dimension View' && reportView !== 'Multi Dimension View') {
      // For Detailed View, ensure data has the correct structure
      // If data has 'name' but not 'dimension_value', it's from Dimension View - return empty
      if (safeData.length > 0 && safeData[0] && safeData[0].name && !safeData[0].dimension_value && !safeData[0].voucher_no) {
        return [];
      }
      return safeData.map(row => ({ ...row, hasChildren: false }));
    }

    // For Dimension View, ensure data has the correct structure
    // If data has 'voucher_no' or 'dimension_value', it's from Detailed View - return empty
    if (safeData.length > 0 && safeData[0] && (safeData[0].voucher_no || (safeData[0].dimension_value && !safeData[0].name))) {
      return [];
    }

    // Optimize: Use a single pass with a stack to build parent relationships
    const enhancedData: EagleViewRow[] = [];
    const parentStack: Array<{ name: string; indent: number }> = [];
    
    safeData.forEach((row, index) => {
      if (!row) return; // Skip invalid rows
      
      const currentIndent = row.indent || 0;
      
      // Pop stack until we find the parent (indent level less than current)
      while (parentStack.length > 0 && parentStack[parentStack.length - 1].indent >= currentIndent) {
        parentStack.pop();
      }
      
      // Get parent from stack top
      const parent = parentStack.length > 0 ? parentStack[parentStack.length - 1].name : null;
      
      // Check if this row has children by looking ahead (only check next few rows for performance)
      let hasChildren = row.is_group === 1;
      if (!hasChildren && index < safeData.length - 1 && safeData[index + 1]) {
        const nextIndent = safeData[index + 1].indent || 0;
        hasChildren = nextIndent > currentIndent;
      }
      
      enhancedData.push({
        ...row,
        parent,
        hasChildren,
      });
      
      // Push current row to stack if it's a group
      if (hasChildren) {
        parentStack.push({ name: row.name, indent: currentIndent });
      }
    });
    
    return enhancedData;
  }, [safeData, reportView]);

  // Filter tree for display based on expanded state (only for Dimension View and Multi Dimension View)
  const displayData = useMemo(() => {
    // For Multi Dimension View, also apply tree filtering
    if (reportView === 'Multi Dimension View') {
      const result: EagleViewRow[] = [];
      
      buildTreeStructure.forEach((row, index) => {
        // Check if any parent in the chain is collapsed
        let shouldShow = true;
        let checkIndent = row.indent || 0;
        
        if (checkIndent > 0) {
          // Look back to find all parents in the hierarchy chain
          for (let i = index - 1; i >= 0; i--) {
            const prevRow = buildTreeStructure[i];
            const prevIndent = prevRow.indent || 0;
            
            // Check if this is the immediate parent of our current check level
            if (prevIndent === checkIndent - 1) {
              // This is a direct parent at the level we're checking
              if (!expandedRows.has(prevRow.name)) {
                shouldShow = false;
                break;
              }
              // Move up to check the next level
              checkIndent = prevIndent;
              
              // If we've reached the root level, we're done
              if (checkIndent === 0) break;
            }
          }
        }
        
        if (shouldShow) {
          result.push(row);
        }
      });
      
      return result;
    }
    
    // No tree filtering for non-dimension views
    if (reportView !== 'Dimension View') {
      return buildTreeStructure;
    }

    const result: EagleViewRow[] = [];
    
    buildTreeStructure.forEach((row, index) => {
      // Check if any parent in the chain is collapsed
      let shouldShow = true;
      let checkIndent = row.indent || 0;
      
      if (checkIndent > 0) {
        // Look back to find all parents in the hierarchy chain
        for (let i = index - 1; i >= 0; i--) {
          const prevRow = buildTreeStructure[i];
          const prevIndent = prevRow.indent || 0;
          
          // Check if this is the immediate parent of our current check level
          if (prevIndent === checkIndent - 1) {
            // This is a direct parent at the level we're checking
            if (!expandedRows.has(prevRow.name)) {
              shouldShow = false;
              break;
            }
            // Move up to check the next level
            checkIndent = prevIndent;
            
            // If we've reached the root level, we're done
            if (checkIndent === 0) break;
          }
        }
      }
      
      if (shouldShow) {
        result.push(row);
      }
    });
    
    return result;
  }, [buildTreeStructure, expandedRows, reportView]);

  // Check if a row has all zero values
  const isRowEmpty = (row: EagleViewRow): boolean => {
    // Skip non-numeric metadata fields
    const skipKeys = new Set([
      'name', 'indent', 'is_group', 'lft', 'rgt', 'parent', 'hasChildren',
      'account', 'posting_date', 'company', 'voucher_type', 'voucher_no',
      'dimension_value', 'account_head', 'root_type', 'remarks', 'attachments',
      'voucher_no_link', '_adjustment_keys'
    ]);
    
    // Check all numeric columns in the row
    for (const [key, value] of Object.entries(row)) {
      // Skip metadata fields
      if (skipKeys.has(key)) {
        continue;
      }
      
      // Check if field is amount-related (ends with _inc, _exp, _net, or starts with total_)
      if (
        key.endsWith('_inc') ||
        key.endsWith('_exp') ||
        key.endsWith('_net') ||
        key.startsWith('total_') ||
        key === 'amount'
      ) {
        // For _both columns, check both _inc and _exp
        if (key.endsWith('_both')) {
          const incKey = key.replace('_both', '_inc');
          const expKey = key.replace('_both', '_exp');
          const incValue = (row[incKey] as number) || 0;
          const expValue = (row[expKey] as number) || 0;
          if (incValue !== 0 || expValue !== 0) {
            return false; // Row has at least one non-zero value
          }
        } else {
          // For regular columns, check the value directly
          const numValue = typeof value === 'number' ? value : parseFloat(String(value));
          if (!isNaN(numValue) && numValue !== 0) {
            return false; // Row has at least one non-zero value
          }
        }
      }
    }
    
    return true; // Row is empty (all values are zero)
  };

  // Filter data based on search term and report type (for Detailed View)
  const filteredData = useMemo(() => {
    let data = displayData;
    
    // For Detailed View, filter by root_type based on report type toggle
    if (reportView === 'Detailed View') {
      if (reportType === 'Detailed Income') {
        data = displayData.filter((row) => (row as any).root_type === 'Income');
      } else if (reportType === 'Detailed Expense') {
        data = displayData.filter((row) => (row as any).root_type === 'Expense');
      }
      // If "Both Income and Expenses" or any other value, show all data (already fetched)
    }
    
    // Apply search filter
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      data = data.filter((row) =>
        row.name?.toLowerCase().includes(searchLower) ||
        (row as any).account_head?.toLowerCase().includes(searchLower) ||
        (row as any).voucher_no?.toLowerCase().includes(searchLower) ||
        (row as any).voucher_type?.toLowerCase().includes(searchLower)
      );
    }
    
    // Filter out empty rows if hideEmptyRows is enabled
    if (hideEmptyRows) {
      data = data.filter((row) => !isRowEmpty(row));
    }
    
    return data;
  }, [displayData, searchTerm, reportView, reportType, hideEmptyRows]);

  // Check if there are any disabled items in the data
  const hasDisabledItems = useMemo(() => {
    return safeData.some(row => row.disabled === 1);
  }, [safeData]);

  // Apply sorting (for Multi Dimension View and disabled status)
  const sortedData = useMemo(() => {
    const dataToSort = [...filteredData];
    
    // Apply combined sorting: disabled status first (if enabled), then column sort (if applicable)
    return dataToSort.sort((a, b) => {
      // First, sort by disabled status if enabled
      if (sortByDisabled !== 'none') {
        const aDisabled = (a.disabled === 1) ? 1 : 0;
        const bDisabled = (b.disabled === 1) ? 1 : 0;
        
        if (aDisabled !== bDisabled) {
          // Items have different disabled status, sort by disabled status
          if (sortByDisabled === 'disabled_first') {
            // Disabled items first
            return bDisabled - aDisabled;
          } else {
            // Disabled items last
            return aDisabled - bDisabled;
          }
        }
        // If disabled status is the same, continue to next sort criteria
      }
      
      // Then, apply column sorting for Multi Dimension View
      if (reportView === 'Multi Dimension View' && sortColumn) {
        let aValue: number = 0;
        let bValue: number = 0;

        // Handle _both columns - sum of income and expense
        if (sortColumn.endsWith('_both')) {
          const incKey = sortColumn.replace('_both', '_inc');
          const expKey = sortColumn.replace('_both', '_exp');
          const aInc = (a[incKey] as number) || 0;
          const aExp = (a[expKey] as number) || 0;
          const bInc = (b[incKey] as number) || 0;
          const bExp = (b[expKey] as number) || 0;
          aValue = aInc - aExp; // Net value
          bValue = bInc - bExp; // Net value
        } else {
          // Handle regular columns (_inc, _exp, _net)
          aValue = (a[sortColumn] as number) || 0;
          bValue = (b[sortColumn] as number) || 0;
        }

        if (aValue !== bValue) {
          if (sortDirection === 'asc') {
            return aValue - bValue;
          } else {
            return bValue - aValue;
          }
        }
        // If values are equal, maintain original order
      }
      
      // If no sorting criteria applies or values are equal, maintain original order
      return 0;
    });
  }, [filteredData, sortColumn, sortDirection, reportView, sortByDisabled]);

  // Pagination calculations (for Detailed View and Multi Dimension View with many rows)
  const totalRecords = sortedData.length;
  const shouldPaginate = reportView === 'Detailed View' || 
                         (reportView === 'Multi Dimension View' && filteredData.length > 100);
  const totalPages = shouldPaginate ? Math.ceil(totalRecords / recordsPerPage) : 1;
  const startIndex = shouldPaginate ? (currentPage - 1) * recordsPerPage : 0;
  const endIndex = shouldPaginate ? startIndex + recordsPerPage : totalRecords;
  // Paginate for Detailed View and Multi Dimension View (if more than 100 rows)
  const paginatedData = (reportView === 'Detailed View' || 
                         (reportView === 'Multi Dimension View' && sortedData.length > 100))
    ? sortedData.slice(startIndex, endIndex)
    : sortedData;

  // Reset to page 1 when filters change
  React.useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, reportType, reportView, sortColumn, sortDirection]);
  
  // Reset sorting when view changes
  React.useEffect(() => {
    setSortColumn(null);
    setSortDirection('desc');
    // Keep sortByDisabled as it applies to all views
  }, [reportView]);
  
  // Handle column header click for sorting (Multi Dimension View only)
  const handleSort = (columnKey: string) => {
    if (reportView !== 'Multi Dimension View') return;
    
    if (sortColumn === columnKey) {
      // Toggle sort direction
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      // Set new sort column with default descending
      setSortColumn(columnKey);
      setSortDirection('desc');
    }
  };

  // Reset search term when view changes
  React.useEffect(() => {
    setSearchTerm('');
  }, [reportView]);
  
  // Reset hideZeroColumns when view changes (only applicable to Multi Dimension View)
  React.useEffect(() => {
    if (reportView !== 'Multi Dimension View') {
      setHideZeroColumns(false);
    }
  }, [reportView]);
  
  // Reset hideEmptyRows when view changes
  React.useEffect(() => {
    setHideEmptyRows(false);
  }, [reportView]);

  // Format currency - rounded to no decimals
  // For Multi Dimension View, show nothing (blank) when value is 0
  const formatCurrency = (value: number | undefined, showZero: boolean = true) => {
    if (value === undefined || value === null) {
      return showZero ? '₹ 0' : '';
    }
    const roundedValue = Math.round(value);
    if (roundedValue === 0 && !showZero) {
      return ''; // Show nothing for zero values in Multi Dimension View
    }
    return `₹ ${roundedValue.toLocaleString('en-IN')}`;
  };

  // Get adjustment type breakdown for a row
  // Memoize adjustment breakdown to avoid recalculating for every cell
  // columnKey: optional column key to filter adjustments (for Multi Dimension View)
  const getAdjustmentBreakdown = React.useCallback((row: EagleViewRow, type: 'inc' | 'exp', columnKey?: string) => {
    const adjustments: Array<{ name: string; value: number }> = [];
    
    // Get list of secondary dimension keys to exclude (for Multi Dimension View)
    // These are the base columns like "folk_main_inc", "folk_main_exp", "folk_main_net"
    // Adjustment columns will be like "folk_main_manual_inc" which won't match these exact keys
    const secondaryDimKeys = new Set<string>();
    if (metadata?.has_secondary_dimensions && metadata?.secondary_dimensions) {
      metadata.secondary_dimensions.forEach((secDim: any) => {
        if (secDim && secDim.key) {
          secondaryDimKeys.add(`${secDim.key}_inc`);
          secondaryDimKeys.add(`${secDim.key}_exp`);
          secondaryDimKeys.add(`${secDim.key}_net`);
        }
      });
    }
    
    // For Multi Dimension View, extract the column prefix from columnKey
    // e.g., if columnKey is "folk_main_inc", the prefix is "folk_main_"
    let columnPrefix = '';
    if (reportView === 'Multi Dimension View' && columnKey) {
      // Remove the suffix (_inc, _exp, _net) to get the base column key
      const baseKey = columnKey.replace(/_(inc|exp|net)$/, '');
      columnPrefix = baseKey + '_';
    }
    
    // Get list of period keys to exclude (for period-wise views)
    const periodKeys = new Set<string>();
    if (metadata?.has_periods && metadata?.periods) {
      metadata.periods.forEach((period: any) => {
        if (period && period.key) {
          periodKeys.add(`${period.key}_inc`);
          periodKeys.add(`${period.key}_exp`);
          periodKeys.add(`${period.key}_net`);
          periodKeys.add(`${period.key}_both`);
        }
      });
    }
    
    // Cache the keys to avoid repeated Object.keys() calls
    const rowKeys = Object.keys(row);
    const suffix = `_${type}`;
    
    // Find all adjustment keys in the row (optimized)
    for (let i = 0; i < rowKeys.length; i++) {
      const key = rowKeys[i];
      if (key.endsWith(suffix) && !key.startsWith('total_')) {
        // Exclude secondary dimension base columns (Multi Dimension View)
        // These are exact matches like "folk_main_inc", "folk_main_exp", "folk_main_net"
        if (secondaryDimKeys.has(key)) {
          continue;
        }
        // Exclude period columns (period-wise views)
        if (periodKeys.has(key)) {
          continue;
        }
        // Exclude columns with dashes (period keys like "2024-01_inc")
        if (key.includes('-')) {
          continue;
        }
        
        // For Multi Dimension View, only include adjustments for the current column
        if (columnPrefix && !key.startsWith(columnPrefix)) {
          continue;
        }
        
        const value = row[key] as number;
        if (value && value !== 0) {
          let adjType = key.slice(0, -suffix.length);
          
          // For Multi Dimension View, adjustment columns are like "folk_main_manual_inc"
          // where "folk_main" is the secondary dimension key and "manual" is the adjustment type
          // We need to extract just the adjustment type part
          if (reportView === 'Multi Dimension View' && metadata?.has_secondary_dimensions) {
            // Check if key starts with any secondary dimension key
            for (const secDimKey of secondaryDimKeys) {
              const baseKey = secDimKey.slice(0, -suffix.length); // Remove "_inc" or "_exp" to get base like "folk_main"
              if (adjType.startsWith(baseKey + '_')) {
                // Extract the adjustment type part after the secondary dimension key
                adjType = adjType.substring(baseKey.length + 1); // +1 to skip the underscore
                break;
              }
            }
          }
          
          // Convert snake_case to Title Case for display
          const displayName = adjType
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
          adjustments.push({ name: displayName, value });
        }
      }
    }
    
    return adjustments;
  }, [reportView, metadata]);

  // Format adjustment breakdown as JSX with colored amounts
  // vertical: if true, display adjustments vertically (for Multi Dimension View)
  const renderAdjustmentBreakdown = (adjustments: Array<{ name: string; value: number }>, type: 'inc' | 'exp', vertical: boolean = false) => {
    if (adjustments.length === 0) return null;
    
    // Color: green for income adjustments, red for expense adjustments
    const amountColor = type === 'inc' ? 'green.600' : 'red.600';
    
    if (vertical) {
      // Vertical layout for Multi Dimension View - saves space
      return (
        <VStack spacing={0.5} align="flex-start" mt={1}>
          {adjustments.map((adj, index) => {
            const amount = Math.round(adj.value || 0).toLocaleString('en-IN');
            return (
              <Text key={index} fontSize="xs" color="gray.700" lineHeight="1.2">
                <Text as="span" fontWeight="500" color="gray.800">{adj.name}</Text>
                {' : '}
                <Text as="span" color={amountColor} fontWeight="600">{amount}</Text>
              </Text>
            );
          })}
        </VStack>
      );
    }
    
    // Horizontal layout for other views
    return (
      <Text as="span" fontSize="xs" color="gray.700">
        {'('}
        {adjustments.map((adj, index) => {
          const amount = Math.round(adj.value || 0).toLocaleString('en-IN');
          return (
            <Text as="span" key={index}>
              {index > 0 && ', '}
              <Text as="span" fontWeight="500" color="gray.800">{adj.name}</Text>
              {' : '}
              <Text as="span" color={amountColor} fontWeight="600">{amount}</Text>
            </Text>
          );
        })}
        {')'}
      </Text>
    );
  };

  // Get all unique adjustment type column names from data (for debugging/metadata)
  const getAdjustmentTypeColumns = useMemo(() => {
    const adjColumns = new Set<string>();
    
    safeData.forEach(row => {
      if (!row) return;
      Object.keys(row).forEach(key => {
        if ((key.endsWith('_inc') || key.endsWith('_exp')) && 
            !key.startsWith('total_') && 
            !key.includes('-') && // Exclude period keys like "2024-01_inc"
            row[key] !== undefined) {
          adjColumns.add(key);
        }
      });
    });
    
    const columns = Array.from(adjColumns).sort();
    
    // Debug: Uncomment to see adjustment type columns being received from backend
    // console.log('Adjustment type columns found:', columns);
    
    return columns;
  }, [safeData]);

  // Export to Excel (HTML table format that Excel can open)
  const exportToExcel = () => {
    // IMPORTANT: Export ALL filtered and sorted rows, not just the paginated/visible ones
    // Using sortedData (all filtered and sorted rows) instead of paginatedData (current page only)
    const dataToExport = sortedData;
    
    // Create HTML table content that Excel can open natively
    let htmlContent = `
      <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
      <head>
        <meta charset="utf-8">
        <!--[if gte mso 9]>
        <xml>
          <x:ExcelWorkbook>
            <x:ExcelWorksheets>
              <x:ExcelWorksheet>
                <x:Name>Eagle View Report</x:Name>
                <x:WorksheetOptions>
                  <x:DisplayGridlines/>
                </x:WorksheetOptions>
              </x:ExcelWorksheet>
            </x:ExcelWorksheets>
          </x:ExcelWorkbook>
        </xml>
        <![endif]-->
        <style>
          table { border-collapse: collapse; width: 100%; }
          th { background-color: #4a5568; color: white; padding: 8px; text-align: left; font-weight: bold; border: 1px solid #ddd; }
          td { padding: 6px 8px; border: 1px solid #ddd; white-space: pre; }
          .number { text-align: right; }
          .group { font-weight: bold; background-color: #f7fafc; }
        </style>
      </head>
      <body>
        <table>
          <thead>
            <tr>
              ${columns.map(col => `<th>${col.label}</th>`).join('')}
            </tr>
          </thead>
          <tbody>
    `;
    
    // Add data rows with tree structure and formatting - ALL filtered rows
    dataToExport.forEach((row) => {
      const isGroup = reportView === 'Dimension View' && row.is_group;
      htmlContent += `<tr class="${isGroup ? 'group' : ''}">`;
      
      columns.forEach((col, colIndex) => {
        let cellValue = row[col.key];
        let cellClass = col.isNumeric ? 'number' : '';
        
        // Format numeric values - round to no decimals
        if (col.isNumeric && typeof cellValue === 'number') {
          cellValue = Math.round(cellValue).toLocaleString('en-IN');
          
          // Add adjustment breakdown for income/expense columns
          if (col.key.includes('_inc')) {
            const adjustments = getAdjustmentBreakdown(row, 'inc');
            if (adjustments.length > 0) {
              const adjText = ' (' + adjustments
                .map(adj => {
                  const amount = Math.round(adj.value || 0).toLocaleString('en-IN');
                  return `${adj.name} : ${amount}`;
                })
                .join(', ') + ')';
              cellValue += adjText;
            }
          } else if (col.key.includes('_exp')) {
            const adjustments = getAdjustmentBreakdown(row, 'exp');
            if (adjustments.length > 0) {
              const adjText = ' (' + adjustments
                .map(adj => {
                  const amount = Math.round(adj.value || 0).toLocaleString('en-IN');
                  return `${adj.name} : ${amount}`;
                })
                .join(', ') + ')';
              cellValue += adjText;
            }
          }
        } else if (cellValue === undefined || cellValue === null) {
          cellValue = '-';
        } else {
          // Escape HTML entities for text
          cellValue = String(cellValue).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        }
        
        // Add indentation for first column in Dimension View and Multi Dimension View
        if (colIndex === 0 && (reportView === 'Dimension View' || reportView === 'Multi Dimension View') && row.indent) {
          const indentSpaces = '&nbsp;&nbsp;'.repeat(row.indent); // Non-breaking spaces for Excel indentation
          htmlContent += `<td class="${cellClass}">${indentSpaces}${cellValue}</td>`;
        } else {
          htmlContent += `<td class="${cellClass}">${cellValue}</td>`;
        }
      });
      
      htmlContent += '</tr>';
    });
    
    htmlContent += `
          </tbody>
        </table>
      </body>
      </html>
    `;
    
    // Create blob and download as .xls (Excel will open it)
    const blob = new Blob([htmlContent], { type: 'application/vnd.ms-excel' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `eagle_view_report_${new Date().toISOString().split('T')[0]}.xls`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Handle attachment click - for non-voucher views
  const handleAttachmentClick = (attachments: any[], voucherNo: string) => {
    if (attachments && attachments.length > 0) {
      setSelectedAttachments(attachments);
      setSelectedVoucherNo(voucherNo);
      onOpen();
    }
  };

  // Handle voucher click - for voucher view (opens enhanced modal)
  const handleVoucherClick = (index: number) => {
    setSelectedVoucherIndex(index);
    onVoucherModalOpen();
  };

  // Prepare voucher data for VoucherViewerModal (use full filtered data, not paginated)
  const voucherData = useMemo(() => {
    if (reportView !== 'Detailed View') return [];
    
    return filteredData.map(row => ({
      voucher_no: row.voucher_no,
      voucher_type: row.voucher_type,
      posting_date: row.posting_date,
      company: row.company,
      attachments: row.attachments || [],
    }));
  }, [filteredData, reportView]);
  
  // Handle voucher click - adjust index for pagination
  const handleVoucherClickWithPagination = (index: number) => {
    // Convert paginated index to full filtered data index
    const actualIndex = reportView === 'Detailed View' ? startIndex + index : index;
    setSelectedVoucherIndex(actualIndex);
    onVoucherModalOpen();
  };

  // Handle cell click in Multi Dimension View (drill-down to detailed entries)
  const handleCellClick = (row: EagleViewRow, columnKey: string) => {
    if (reportView !== 'Multi Dimension View') return;
    
    // Get main dimension value from row
    const mainDimValue = row.name;
    if (!mainDimValue) return;
    
    // Extract secondary dimension value from column key
    // Column keys are like: "brahmachari_ashram_general_inc", "brahmachari_ashram_general_exp", "brahmachari_ashram_general_both", etc.
    // We need to extract the secondary dimension value and type
    let secondaryDimValue: string | null = null;
    let columnType: 'inc' | 'exp' | 'net' | 'both' | null = null;
    
    // Determine column type from key
    if (columnKey.endsWith('_both')) {
      columnType = 'both';
      secondaryDimValue = columnKey.replace('_both', '');
    } else if (columnKey.endsWith('_inc')) {
      columnType = 'inc';
      secondaryDimValue = columnKey.replace('_inc', '');
    } else if (columnKey.endsWith('_exp')) {
      columnType = 'exp';
      secondaryDimValue = columnKey.replace('_exp', '');
    } else if (columnKey.endsWith('_net')) {
      columnType = 'net';
      secondaryDimValue = columnKey.replace('_net', '');
    }
    
    if (!secondaryDimValue) return;
    
    // Find the secondary dimension label from metadata
    let actualSecondaryDimValue: string | null = null;
    if (metadata?.has_secondary_dimensions && metadata?.secondary_dimensions) {
      const secDim = metadata.secondary_dimensions.find((dim: any) => dim.key === secondaryDimValue);
      if (secDim && secDim.value) {
        actualSecondaryDimValue = secDim.value;
      }
    }
    
    if (!actualSecondaryDimValue) {
      // Fallback: convert snake_case to Title Case
      actualSecondaryDimValue = secondaryDimValue
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
    }
    
    // Debug logging
    console.log('Cell clicked:', {
      mainDimValue,
      actualSecondaryDimValue,
      columnType,
      columnKey,
    });
    
    // Set state and open modal
    setSelectedMainDimValue(mainDimValue);
    setSelectedSecondaryDimValue(actualSecondaryDimValue);
    setSelectedColumnType(columnType);
    onCellDetailModalOpen();
  };

  // Validate data structure matches the current view
  const isDataStructureValid = useMemo(() => {
    if (!safeData || safeData.length === 0) {
      return true; // Empty data is valid
    }
    
    const firstRow = safeData[0];
    if (!firstRow) {
      return false; // Invalid row
    }
    
    if (reportView === 'Detailed View') {
      // Detailed View should have voucher_no, posting_date, etc.
      // If it has 'name' but no 'voucher_no', it's Dimension View data
      return !!(firstRow.voucher_no || firstRow.posting_date || firstRow.dimension_value);
    } else if (reportView === 'Multi Dimension View') {
      // Multi Dimension View should have 'name' and secondary dimension columns (e.g., cost_center_inc, cost_center_exp, cost_center_net)
      // If it has 'voucher_no', it's Detailed View data
      return !!(firstRow.name && !firstRow.voucher_no);
    } else {
      // Dimension View should have 'name' and possibly 'indent', 'is_group'
      // If it has 'voucher_no', it's Detailed View data
      return !!(firstRow.name && !firstRow.voucher_no);
    }
  }, [safeData, reportView]);

  // Check if a column has all zero values (for Multi Dimension View)
  const isColumnAllZeros = useMemo(() => {
    if (reportView !== 'Multi Dimension View' || !hideZeroColumns) {
      return new Set<string>(); // Return empty set if not applicable
    }
    
    const zeroColumns = new Set<string>();
    
    // Check each column in the data
    if (safeData && safeData.length > 0) {
      // Get all possible column keys from the first row
      const firstRow = safeData[0];
      if (firstRow) {
        // Collect all column keys that might exist
        const allKeys = new Set<string>();
        Object.keys(firstRow).forEach((key) => {
          // Skip non-numeric columns
          if (key === 'name' || key === 'indent' || key === 'is_group' || key === 'lft' || key === 'rgt' || key === 'parent' || key === 'hasChildren') {
            return;
          }
          allKeys.add(key);
          
          // For _inc and _exp columns, also add the corresponding _both key
          if (key.endsWith('_inc')) {
            allKeys.add(key.replace('_inc', '_both'));
          } else if (key.endsWith('_exp')) {
            allKeys.add(key.replace('_exp', '_both'));
          }
        });
        
        // Check each column key
        allKeys.forEach((key) => {
          // Check if this column has all zero values
          let allZeros = true;
          
          for (let i = 0; i < safeData.length; i++) {
            const row = safeData[i];
            if (!row) continue;
            
            // For _both columns, check both _inc and _exp
            if (key.endsWith('_both')) {
              const incKey = key.replace('_both', '_inc');
              const expKey = key.replace('_both', '_exp');
              const incValue = (row[incKey] as number) || 0;
              const expValue = (row[expKey] as number) || 0;
              if (incValue !== 0 || expValue !== 0) {
                allZeros = false;
                break;
              }
            } else {
              // For regular columns (_inc, _exp, _net), check the value directly
              const value = row[key];
              if (value !== null && value !== undefined) {
                const numValue = typeof value === 'number' ? value : parseFloat(String(value));
                if (!isNaN(numValue) && numValue !== 0) {
                  allZeros = false;
                  break;
                }
              }
            }
          }
          
          if (allZeros) {
            zeroColumns.add(key);
          }
        });
      }
    }
    
    return zeroColumns;
  }, [safeData, hideZeroColumns, reportView]);

  // Get columns based on report view, type and metadata (memoized for performance)
  const columns = useMemo(() => {
    try {
      const cols: Array<{ key: string; label: string; isPeriod?: boolean; isNumeric?: boolean; isBoth?: boolean }> = [];

      // Different column structures for different views
      if (reportView === 'Detailed View') {
        cols.push(
        { key: 'posting_date', label: 'Date' },
        { key: 'company', label: 'Company' },
        { key: 'voucher_type', label: 'Voucher Type' },
        { key: 'voucher_no', label: 'Voucher No' },
        { key: 'dimension_value', label: 'Dimension Value' },
        { key: 'account_head', label: 'Account' },
        { key: 'root_type', label: 'Type' },
        { key: 'amount', label: 'Amount', isNumeric: true },
        { key: 'remarks', label: 'Remarks' },
        { key: 'attachments', label: 'Attachments' }
        );
    } else if (reportView === 'Multi Dimension View') {
      // Multi Dimension View - main dimension as rows, secondary dimension as columns
      cols.push({ key: 'name', label: 'Dimension Value' });

      // Check if we have secondary dimension columns from metadata
      if (metadata && metadata.has_secondary_dimensions && Array.isArray(metadata.secondary_dimensions) && metadata.secondary_dimensions.length > 0) {
        console.log('Using metadata.secondary_dimensions:', metadata.secondary_dimensions.length, 'dimensions');
        // Generate dynamic columns for each secondary dimension based on report type
        metadata.secondary_dimensions.forEach((secDim: any) => {
          if (secDim && secDim.key) {
            if (reportType === 'Both Income and Expenses') {
              // Show single column with both income and expense (stacked vertically)
              cols.push(
                { key: `${secDim.key}_both`, label: `${secDim.label || secDim.key}`, isPeriod: true, isNumeric: true, isBoth: true }
              );
            } else if (reportType === 'Only Incomes') {
              // Show only income column
              cols.push(
                { key: `${secDim.key}_inc`, label: `${secDim.label || secDim.key} (Income)`, isPeriod: true, isNumeric: true }
              );
            } else if (reportType === 'Only Expense') {
              // Show only expense column
              cols.push(
                { key: `${secDim.key}_exp`, label: `${secDim.label || secDim.key} (Expense)`, isPeriod: true, isNumeric: true }
              );
            } else if (reportType === 'Net Profit') {
              // Show only net column
              cols.push(
                { key: `${secDim.key}_net`, label: `${secDim.label || secDim.key} (Net)`, isPeriod: true, isNumeric: true }
              );
            }
          }
        });
      } else if (safeData && safeData.length > 0 && safeData[0]) {
        // Fallback: Extract secondary dimension columns from data if metadata is missing
        // Limit processing to prevent performance issues with large datasets
        try {
          const firstRow = safeData[0];
          const secondaryDimKeys = new Set<string>();
          const allKeys = Object.keys(firstRow);
          
          // Limit to first 1000 keys to prevent performance issues
          // In practice, metadata should always be provided, so this is just a safety fallback
          const keysToProcess = allKeys.slice(0, 1000);
          
          // Find all columns that match the pattern: {key}_inc, {key}_exp, {key}_net
          keysToProcess.forEach(key => {
            if (key.endsWith('_inc') || key.endsWith('_exp') || key.endsWith('_net')) {
              const baseKey = key.replace(/_(inc|exp|net)$/, '');
              if (baseKey !== 'total' && baseKey !== 'name' && !baseKey.startsWith('_')) {
                secondaryDimKeys.add(baseKey);
              }
            }
          });
          
          // Limit to first 100 secondary dimensions to prevent UI issues
          const sortedKeys = Array.from(secondaryDimKeys).sort().slice(0, 100);
          
          // Generate columns for each detected secondary dimension based on report type
          sortedKeys.forEach(secKey => {
            // Convert key back to label (e.g., 'cost_center' -> 'Cost Center')
            const label = secKey.split('_').map(word => 
              word.charAt(0).toUpperCase() + word.slice(1)
            ).join(' ');
            
            if (reportType === 'Both Income and Expenses') {
              // Show single column with both income and expense (stacked vertically)
              cols.push(
                { key: `${secKey}_both`, label: label, isPeriod: true, isNumeric: true, isBoth: true }
              );
            } else if (reportType === 'Only Incomes') {
              // Show only income column
              cols.push(
                { key: `${secKey}_inc`, label: `${label} (Income)`, isPeriod: true, isNumeric: true }
              );
            } else if (reportType === 'Only Expense') {
              // Show only expense column
              cols.push(
                { key: `${secKey}_exp`, label: `${label} (Expense)`, isPeriod: true, isNumeric: true }
              );
            } else if (reportType === 'Net Profit') {
              // Show only net column
              cols.push(
                { key: `${secKey}_net`, label: `${label} (Net)`, isPeriod: true, isNumeric: true }
              );
            }
          });
        } catch (error) {
          console.error('Error extracting columns from data:', error);
          // If extraction fails, just show the name column
          // Metadata should be provided by backend to avoid this
        }
      }
      
      // Filter out zero columns if hideZeroColumns is enabled (for Multi Dimension View)
      if (hideZeroColumns) {
        return cols.filter(col => !isColumnAllZeros.has(col.key));
      }
    } else if (reportView === 'Account View') {
      // Account View
      cols.push({ key: 'account', label: 'Account' });
      
      // Check if we have period-wise data
      if (metadata?.has_periods && metadata?.periods) {
        // Generate dynamic columns for each period
        metadata.periods.forEach((period) => {
          if (reportType === 'Both Income and Expenses') {
            cols.push({ key: `${period.key}_both`, label: period.label, isPeriod: true, isNumeric: true, isBoth: true });
          } else if (reportType === 'Only Incomes') {
            cols.push({ key: `${period.key}_inc`, label: `${period.label} (Income)`, isPeriod: true, isNumeric: true });
          } else if (reportType === 'Only Expense') {
            cols.push({ key: `${period.key}_exp`, label: `${period.label} (Expense)`, isPeriod: true, isNumeric: true });
          } else if (reportType === 'Net Profit') {
            cols.push({ key: `${period.key}_net`, label: `${period.label} (Net)`, isPeriod: true, isNumeric: true });
          }
        });
      } else {
        // Cumulative columns
        if (reportType === 'Both Income and Expenses') {
          cols.push(
            { key: 'total_both', label: 'Income / Expense', isNumeric: true, isBoth: true }
          );
        } else if (reportType === 'Only Incomes') {
          cols.push({ key: 'total_inc', label: 'Total Income', isNumeric: true });
        } else if (reportType === 'Only Expense') {
          cols.push({ key: 'total_exp', label: 'Total Expense', isNumeric: true });
        } else if (reportType === 'Net Profit') {
          cols.push({ key: 'total_net', label: 'Total Net Profit', isNumeric: true });
        }
      }
    } else {
      // Dimension View
      cols.push({ key: 'name', label: 'Dimension Value' });

      // Check if we have period-wise data
      if (metadata?.has_periods && metadata?.periods) {
        // Generate dynamic columns for each period
        metadata.periods.forEach((period) => {
          if (reportType === 'Both Income and Expenses') {
            cols.push({ key: `${period.key}_both`, label: period.label, isPeriod: true, isNumeric: true, isBoth: true });
          } else if (reportType === 'Only Incomes') {
            cols.push({ key: `${period.key}_inc`, label: `${period.label} (Income)`, isPeriod: true, isNumeric: true });
          } else if (reportType === 'Only Expense') {
            cols.push({ key: `${period.key}_exp`, label: `${period.label} (Expense)`, isPeriod: true, isNumeric: true });
          } else if (reportType === 'Net Profit') {
            cols.push({ key: `${period.key}_net`, label: `${period.label} (Net)`, isPeriod: true, isNumeric: true });
          }
        });
      } else {
        // Cumulative columns
        if (reportType === 'Both Income and Expenses') {
          cols.push(
            { key: 'total_both', label: 'Income / Expense', isNumeric: true, isBoth: true }
          );
        } else if (reportType === 'Only Incomes') {
          cols.push({ key: 'total_inc', label: 'Total Income', isNumeric: true });
        } else if (reportType === 'Only Expense') {
          cols.push({ key: 'total_exp', label: 'Total Expense', isNumeric: true });
        } else if (reportType === 'Net Profit') {
          cols.push({ key: 'total_net', label: 'Total Net Profit', isNumeric: true });
        }
      }
    }

    return cols;
    } catch (error) {
      console.error('Error generating columns:', error);
      // Return minimal columns on error
      return [
        { key: 'name', label: 'Dimension Value' },
        { key: 'error', label: 'Error loading columns' }
      ];
    }
  }, [reportView, reportType, metadata, safeData, hideZeroColumns, isColumnAllZeros]);

  // If data structure doesn't match view, show "No data found" instead of trying to render
  if (!isDataStructureValid && safeData.length > 0) {
    return (
      <Box bg="white" borderRadius="lg" boxShadow="sm" overflow="hidden">
        <Flex p={4} borderBottom="1px" borderColor="gray.200" justify="space-between" align="center" gap={4}>
          <InputGroup size="md" maxW="400px">
            <InputLeftElement pointerEvents="none">
              <Icon as={SearchIcon} color="gray.400" />
            </InputLeftElement>
            <Input
              placeholder="Search in table..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              isDisabled
            />
          </InputGroup>
        </Flex>
        <Box p={6}>
          <Center h="200px">
            <Text color="gray.500">No data found. Please click "Get Report" to load data.</Text>
          </Center>
        </Box>
      </Box>
    );
  }

  return (
    <Box bg="white" borderRadius="lg" boxShadow="sm" overflow="hidden">
      {/* Search Box, Report Type Toggle, and Export Button */}
      <Flex p={4} borderBottom="1px" borderColor="gray.200" justify="space-between" align="center" gap={4}>
        <InputGroup size="md" maxW="400px">
          <InputLeftElement pointerEvents="none">
            <Icon as={SearchIcon} color="gray.400" />
          </InputLeftElement>
          <Input
            placeholder="Search in table..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </InputGroup>
        
        <HStack spacing={2} align="center">
          {/* Collapse/Expand All Buttons (only for Dimension View and Multi Dimension View when renderAsTreeView is true) */}
          {(reportView === 'Dimension View' || reportView === 'Multi Dimension View') && renderAsTreeView && (
            <ButtonGroup size="sm" isAttached variant="outline">
              <Button
                onClick={expandAll}
                variant="outline"
                colorScheme="blue"
              >
                Expand All
              </Button>
              <Button
                onClick={collapseAll}
                variant="outline"
                colorScheme="blue"
              >
                Collapse All
              </Button>
            </ButtonGroup>
          )}
          
          {/* Hide Zero Columns Checkbox (for Multi Dimension View) */}
          {reportView === 'Multi Dimension View' && (
            <Checkbox
              size="sm"
              isChecked={hideZeroColumns}
              onChange={(e) => setHideZeroColumns(e.target.checked)}
              colorScheme="blue"
            >
              <Text fontSize="xs" color="gray.700">
                Hide Zero Columns
              </Text>
            </Checkbox>
          )}
          
          {/* Hide Empty Rows Checkbox */}
          {(reportView === 'Dimension View' || reportView === 'Multi Dimension View' || reportView === 'Account View') && (
            <Checkbox
              size="sm"
              isChecked={hideEmptyRows}
              onChange={(e) => setHideEmptyRows(e.target.checked)}
              colorScheme="blue"
            >
              <Text fontSize="xs" color="gray.700">
                Hide Empty Rows
              </Text>
            </Checkbox>
          )}
          
          {/* Sort by Disabled Status (show if there are disabled items in the data) */}
          {(reportView === 'Dimension View' || reportView === 'Multi Dimension View' || reportView === 'Account View') && hasDisabledItems && (
            <Select
              size="sm"
              value={sortByDisabled}
              onChange={(e) => setSortByDisabled(e.target.value as 'none' | 'disabled_first' | 'disabled_last')}
              maxW="180px"
              fontSize="xs"
            >
              <option value="none">Sort: Default</option>
              <option value="disabled_first">Sort: Disabled First</option>
              <option value="disabled_last">Sort: Disabled Last</option>
            </Select>
          )}
          
          {/* Report Type Toggle Buttons */}
          {onReportTypeChange && (
            <ButtonGroup size="sm" isAttached variant="outline">
              {(reportView === 'Dimension View' || reportView === 'Multi Dimension View') ? (
                <>
                  <Button
                    colorScheme={reportType === 'Both Income and Expenses' ? 'blue' : 'gray'}
                    variant={reportType === 'Both Income and Expenses' ? 'solid' : 'outline'}
                    onClick={() => onReportTypeChange('Both Income and Expenses')}
                  >
                    Both
                  </Button>
                  <Button
                    colorScheme={reportType === 'Only Incomes' ? 'blue' : 'gray'}
                    variant={reportType === 'Only Incomes' ? 'solid' : 'outline'}
                    onClick={() => onReportTypeChange('Only Incomes')}
                  >
                    Income
                  </Button>
                  <Button
                    colorScheme={reportType === 'Only Expense' ? 'blue' : 'gray'}
                    variant={reportType === 'Only Expense' ? 'solid' : 'outline'}
                    onClick={() => onReportTypeChange('Only Expense')}
                  >
                    Expense
                  </Button>
                  <Button
                    colorScheme={reportType === 'Net Profit' ? 'blue' : 'gray'}
                    variant={reportType === 'Net Profit' ? 'solid' : 'outline'}
                    onClick={() => onReportTypeChange('Net Profit')}
                  >
                    Profit
                  </Button>
                </>
              ) : (
                <>
                  <Button
                    colorScheme={reportType === 'Both Income and Expenses' ? 'blue' : 'gray'}
                    variant={reportType === 'Both Income and Expenses' ? 'solid' : 'outline'}
                    onClick={() => onReportTypeChange('Both Income and Expenses')}
                  >
                    Both
                  </Button>
                  <Button
                    colorScheme={reportType === 'Detailed Income' ? 'blue' : 'gray'}
                    variant={reportType === 'Detailed Income' ? 'solid' : 'outline'}
                    onClick={() => onReportTypeChange('Detailed Income')}
                  >
                    Income
                  </Button>
                  <Button
                    colorScheme={reportType === 'Detailed Expense' ? 'blue' : 'gray'}
                    variant={reportType === 'Detailed Expense' ? 'solid' : 'outline'}
                    onClick={() => onReportTypeChange('Detailed Expense')}
                  >
                    Expense
                  </Button>
                </>
              )}
            </ButtonGroup>
          )}
          
          <Button
            leftIcon={<DownloadIcon />}
            colorScheme="green"
            size="sm"
            onClick={exportToExcel}
            isDisabled={sortedData.length === 0}
          >
            Export to Excel
          </Button>
        </HStack>
      </Flex>

      {/* Table */}
      <Box 
        overflowX="auto" 
        position="relative"
        maxH={
          reportView === 'Detailed View' 
            ? 'calc(100vh - 300px)' 
            : reportView === 'Multi Dimension View' 
            ? 'calc(100vh - 250px)' 
            : 'none'
        }
        overflowY={
          reportView === 'Detailed View' || reportView === 'Multi Dimension View' 
            ? 'auto' 
            : 'visible'
        }
      >
        <Table variant="simple" size="sm">
          <Thead bg="gray.50" position="sticky" top={0} zIndex={20}>
            <Tr>
              {columns.map((col, colIndex) => {
                const isSortable = reportView === 'Multi Dimension View' && colIndex > 0 && col.isNumeric;
                const isSorted = sortColumn === col.key;
                
                return (
                  <Th 
                    key={col.key} 
                    textTransform="none" 
                    fontSize="sm" 
                    fontWeight="600"
                    minW={colIndex === 0 ? '250px' : '150px'}
                    position={colIndex === 0 ? 'sticky' : 'sticky'}
                    left={colIndex === 0 ? 0 : 'auto'}
                    top={0}
                    bg={colIndex === 0 ? 'gray.50' : 'gray.50'}
                    zIndex={colIndex === 0 ? 21 : 20}
                    borderRight={colIndex === 0 ? '2px solid' : 'none'}
                    borderRightColor={colIndex === 0 ? 'gray.300' : 'transparent'}
                    boxShadow={colIndex === 0 ? '2px 0 4px rgba(0,0,0,0.1)' : 'none'}
                    cursor={isSortable ? 'pointer' : 'default'}
                    onClick={isSortable ? () => handleSort(col.key) : undefined}
                    _hover={isSortable ? { bg: 'gray.100' } : {}}
                    userSelect="none"
                  >
                    <Flex alignItems="center" justifyContent={colIndex === 0 ? 'flex-start' : 'flex-end'} gap={1}>
                      {colIndex === 0 ? (
                        <Text>{col.label}</Text>
                      ) : (
                        <>
                          <Text textAlign="right">{col.label}</Text>
                          {isSortable && (
                            <Box ml={1}>
                              {isSorted ? (
                                sortDirection === 'asc' ? (
                                  <ArrowUpIcon boxSize={3} color="blue.500" />
                                ) : (
                                  <ArrowDownIcon boxSize={3} color="blue.500" />
                                )
                              ) : (
                                <Box opacity={0.3}>
                                  <ArrowUpIcon boxSize={3} />
                                </Box>
                              )}
                            </Box>
                          )}
                        </>
                      )}
                    </Flex>
                  </Th>
                );
              })}
            </Tr>
          </Thead>
          <Tbody>
            {paginatedData.length === 0 ? (
              <Tr>
                <Td colSpan={columns.length} textAlign="center" py={8}>
                  <Text color="gray.500">No data found</Text>
                </Td>
              </Tr>
            ) : (
              paginatedData.map((row, index) => {
                const hasChildren = row.hasChildren || false;
                const isExpanded = expandedRows.has(row.name);
                const isFirstColumn = reportView === 'Dimension View' ? 'name' : columns[0].key;
                
                return (
                  <Tr key={`${row.name || row.name}-${index}`} _hover={{ bg: 'gray.50' }}>
                    {columns.map((col, colIndex) => {
                      // For Multi Dimension View, make numeric cells clickable
                      const isClickableCell = reportView === 'Multi Dimension View' && col.isNumeric && colIndex > 0;
                      
                      // Check if cell has a value
                      let hasValue = false;
                      if (isClickableCell) {
                        if (col.key.endsWith('_both')) {
                          // For _both columns, check if either _inc or _exp has a value
                          const incKey = col.key.replace('_both', '_inc');
                          const expKey = col.key.replace('_both', '_exp');
                          const incValue = row[incKey];
                          const expValue = row[expKey];
                          hasValue = (incValue !== undefined && incValue !== null && incValue !== 0) ||
                                     (expValue !== undefined && expValue !== null && expValue !== 0);
                        } else {
                          // For other columns, check the value directly
                          hasValue = row[col.key] !== undefined && row[col.key] !== null && row[col.key] !== 0;
                        }
                      }
                      
                      return (
                      <Td 
                        key={col.key}
                        minW={colIndex === 0 ? '250px' : '150px'}
                        maxW={col.isNumeric ? '200px' : 'auto'}
                        whiteSpace={col.isNumeric ? 'nowrap' : 'normal'}
                        position={colIndex === 0 ? 'sticky' : 'relative'}
                        left={colIndex === 0 ? 0 : 'auto'}
                        bg={colIndex === 0 ? 'white' : 'transparent'}
                        zIndex={colIndex === 0 ? 10 : 'auto'}
                        borderRight={colIndex === 0 ? '2px solid' : 'none'}
                        borderRightColor={colIndex === 0 ? 'gray.200' : 'transparent'}
                        boxShadow={colIndex === 0 ? '2px 0 4px rgba(0,0,0,0.1)' : 'none'}
                        cursor={hasValue ? 'pointer' : 'default'}
                        onClick={hasValue ? () => handleCellClick(row, col.key) : undefined}
                        _hover={hasValue ? { 
                          bg: 'blue.50', 
                          transform: 'scale(1.02)',
                          transition: 'all 0.15s ease-in-out',
                          boxShadow: 'md'
                        } : {}}
                        transition="all 0.15s ease-in-out"
                      >
                        {colIndex === 0 && (reportView === 'Dimension View' || reportView === 'Multi Dimension View' || reportView === 'Account View') ? (
                          <Flex 
                            alignItems="center"
                            pl={row.indent ? `${row.indent * 20}px` : '0'}
                          >
                            {/* Only show expansion icons if renderAsTreeView is true, or if it's Dimension View (always show) */}
                            {hasChildren && (reportView === 'Dimension View' || (reportView === 'Multi Dimension View' && renderAsTreeView)) ? (
                              <IconButton
                                aria-label={isExpanded ? 'Collapse' : 'Expand'}
                                icon={isExpanded ? <ChevronDownIcon /> : <ChevronRightIcon />}
                                size="xs"
                                variant="ghost"
                                onClick={() => toggleRow(reportView === 'Account View' ? row.account : row.name)}
                                mr={2}
                                minW="24px"
                              />
                            ) : (
                              <Box minW="32px" />
                            )}
                            <HStack spacing={2} align="center">
                              <Text
                                fontWeight={row.is_group ? '600' : '400'}
                                color={row.is_group ? 'gray.700' : 'gray.600'}
                              >
                                {row[col.key]}
                              </Text>
                              {row.disabled === 1 && (
                                <Badge
                                  colorScheme="gray"
                                  fontSize="xs"
                                  variant="subtle"
                                  title={reportView === 'Account View' ? "This account is disabled" : "This dimension is disabled"}
                                >
                                  Disabled
                                </Badge>
                              )}
                            </HStack>
                          </Flex>
                        ) : col.key === 'voucher_no' && reportView === 'Detailed View' ? (
                          <Button
                            variant="link"
                            colorScheme="blue"
                            size="sm"
                            fontWeight="500"
                            onClick={() => handleVoucherClickWithPagination(index)}
                          >
                            {row.voucher_no}
                          </Button>
                        ) : col.key === 'root_type' && reportView === 'Detailed View' ? (
                          <Badge
                            colorScheme={row.root_type === 'Income' ? 'green' : 'red'}
                            fontSize="xs"
                          >
                            {row.root_type}
                          </Badge>
                        ) : col.key === 'amount' && reportView === 'Detailed View' ? (
                          <Text
                            fontWeight="500"
                            color={row.root_type === 'Income' ? 'green.600' : 'red.600'}
                            fontSize="sm"
                          >
                            {formatCurrency(row.amount as number)}
                          </Text>
                        ) : col.key === 'attachments' && reportView === 'Detailed View' ? (
                          <Box>
                            {row.attachments && row.attachments.length > 0 ? (
                              <HStack 
                                spacing={1} 
                                cursor="pointer"
                                onClick={() => handleVoucherClickWithPagination(index)}
                                _hover={{ opacity: 0.7 }}
                                transition="opacity 0.2s"
                              >
                                <AttachmentIcon color="blue.500" />
                                <Badge colorScheme="blue">
                                  {row.attachments.length}
                                </Badge>
                              </HStack>
                            ) : (
                              <Text color="gray.400" fontSize="sm">-</Text>
                            )}
                          </Box>
                        ) : (col.key === 'total_both' || (col.key.endsWith('_both') && reportType === 'Both Income and Expenses')) ? (
                          <VStack spacing={1} align="flex-end">
                            {(() => {
                              const incKey = col.key.replace('_both', '_inc');
                              const expKey = col.key.replace('_both', '_exp');
                              const incValue = (row[incKey] || 0) as number;
                              const expValue = (row[expKey] || 0) as number;
                              // For Multi Dimension View, pass the column key to filter adjustments
                              const incAdjustments = getAdjustmentBreakdown(row, 'inc', reportView === 'Multi Dimension View' ? incKey : undefined);
                              const expAdjustments = getAdjustmentBreakdown(row, 'exp', reportView === 'Multi Dimension View' ? expKey : undefined);
                              
                              const showZero = reportView !== 'Multi Dimension View';
                              const incFormatted = formatCurrency(incValue, showZero);
                              const expFormatted = formatCurrency(expValue, showZero);
                              
                              // Check if we have any content to show
                              const hasIncContent = incFormatted || incAdjustments.length > 0;
                              const hasExpContent = expFormatted || expAdjustments.length > 0;
                              
                              // For Multi Dimension View, if no content, show empty space to maintain alignment
                              if (reportView === 'Multi Dimension View' && !hasIncContent && !hasExpContent) {
                                return <Box minH="48px" w="100%" />; // Empty box to maintain cell height and alignment
                              }
                              
                              // For Multi Dimension View, use bordered containers to group values
                              if (reportView === 'Multi Dimension View') {
                                return (
                                  <VStack spacing={1.5} align="stretch" w="100%" minH="48px" justify="center">
                                    {hasIncContent ? (
                                      <Box
                                        border="1px solid"
                                        borderColor="green.200"
                                        borderRadius="md"
                                        bg="green.50"
                                        px={2}
                                        py={1}
                                        minH="22px"
                                        display="flex"
                                        alignItems="center"
                                        justifyContent="flex-end"
                                      >
                                        <Flex alignItems="center" justifyContent="flex-end" gap={1} flexWrap="wrap">
                                          {incFormatted && (
                                            <Text
                                              fontWeight={row.is_group && reportView === 'Dimension View' ? '600' : '500'}
                                              color="green.700"
                                              fontSize="sm"
                                            >
                                              {incFormatted}
                                            </Text>
                                          )}
                                          {renderAdjustmentBreakdown(incAdjustments, 'inc', true)}
                                        </Flex>
                                      </Box>
                                    ) : (
                                      <Box minH="22px" /> // Empty space for income row to maintain alignment
                                    )}
                                    {hasExpContent ? (
                                      <Box
                                        border="1px solid"
                                        borderColor="red.200"
                                        borderRadius="md"
                                        bg="red.50"
                                        px={2}
                                        py={1}
                                        minH="22px"
                                        display="flex"
                                        alignItems="center"
                                        justifyContent="flex-end"
                                      >
                                        <Flex alignItems="center" justifyContent="flex-end" gap={1} flexWrap="wrap">
                                          {expFormatted && (
                                            <Text
                                              fontWeight={row.is_group && reportView === 'Dimension View' ? '600' : '500'}
                                              color="red.700"
                                              fontSize="sm"
                                            >
                                              {expFormatted}
                                            </Text>
                                          )}
                                          {renderAdjustmentBreakdown(expAdjustments, 'exp', true)}
                                        </Flex>
                                      </Box>
                                    ) : (
                                      <Box minH="22px" /> // Empty space for expense row to maintain alignment
                                    )}
                                  </VStack>
                                );
                              }
                              
                              // For other views, use original layout
                              return (
                                <VStack spacing={1} align="flex-end">
                                  {hasIncContent ? (
                                    <Flex alignItems="center" justifyContent="flex-end" gap={1}>
                                      {incFormatted && (
                                        <Text
                                          fontWeight={row.is_group && reportView === 'Dimension View' ? '600' : '400'}
                                          color="green.600"
                                          fontSize="sm"
                                        >
                                          {incFormatted}
                                        </Text>
                                      )}
                                      {renderAdjustmentBreakdown(incAdjustments, 'inc', false)}
                                    </Flex>
                                  ) : (
                                    <Box minH="16px" /> // Empty space for income row to maintain alignment
                                  )}
                                  {hasExpContent ? (
                                    <Flex alignItems="center" justifyContent="flex-end" gap={1}>
                                      {expFormatted && (
                                        <Text
                                          fontWeight={row.is_group && reportView === 'Dimension View' ? '600' : '400'}
                                          color="red.600"
                                          fontSize="sm"
                                        >
                                          {expFormatted}
                                        </Text>
                                      )}
                                      {renderAdjustmentBreakdown(expAdjustments, 'exp', false)}
                                    </Flex>
                                  ) : (
                                    <Box minH="16px" /> // Empty space for expense row to maintain alignment
                                  )}
                                </VStack>
                              );
                            })()}
                          </VStack>
                        ) : (
                          (() => {
                            // Determine color based on report type
                            let textColor = row.is_group && reportView === 'Dimension View' ? 'gray.700' : 'gray.600';
                            
                            if (col.isNumeric) {
                              if (reportType === 'Only Incomes' || col.key.includes('_inc')) {
                                textColor = 'green.600';
                              } else if (reportType === 'Only Expense' || col.key.includes('_exp')) {
                                textColor = 'red.600';
                              } else if (reportType === 'Net Profit' || col.key.includes('_net')) {
                                // For profit/loss, determine value first
                                let value: number;
                                if (col.key === 'total_net' && (row.total_net === undefined || row.total_net === null)) {
                                  const totalInc = row.total_inc || 0;
                                  const totalExp = row.total_exp || 0;
                                  value = totalInc - totalExp;
                                } else if (col.key.endsWith('_net') && (row[col.key] === undefined || row[col.key] === null)) {
                                  const incKey = col.key.replace('_net', '_inc');
                                  const expKey = col.key.replace('_net', '_exp');
                                  const incValue = row[incKey] || 0;
                                  const expValue = row[expKey] || 0;
                                  value = incValue - expValue;
                                } else {
                                  value = (row[col.key] as number) || 0;
                                }
                                // Green for profit (positive), red for loss (negative)
                                textColor = value >= 0 ? 'green.600' : 'red.600';
                              }
                            }

                                return (
                                  <Text
                                    fontWeight={row.is_group && reportView === 'Dimension View' ? '600' : '400'}
                                    color={textColor}
                                    fontSize="sm"
                                  >
                                    {col.isNumeric ? (() => {
                                      let formattedValue = '';
                                      let adjustments: Array<{ name: string; value: number }> = [];
                                      let adjustmentType: 'inc' | 'exp' | null = null;
                                      
                                      // For Multi Dimension View, don't show zero values
                                      const showZero = reportView !== 'Multi Dimension View';
                                      
                                      // Calculate total_net if it doesn't exist and we're showing Net Profit
                                      if (col.key === 'total_net' && (row.total_net === undefined || row.total_net === null)) {
                                        const totalInc = row.total_inc || 0;
                                        const totalExp = row.total_exp || 0;
                                        formattedValue = formatCurrency(totalInc - totalExp, showZero);
                                      }
                                      // For period-wise net values, calculate if not present
                                      else if (col.key.endsWith('_net') && (row[col.key] === undefined || row[col.key] === null)) {
                                        const incKey = col.key.replace('_net', '_inc');
                                        const expKey = col.key.replace('_net', '_exp');
                                        const incValue = row[incKey] || 0;
                                        const expValue = row[expKey] || 0;
                                        formattedValue = formatCurrency(incValue - expValue, showZero);
                                      }
                                      // Show adjustment breakdown for income columns
                                      else if (col.key.includes('_inc')) {
                                        formattedValue = formatCurrency(row[col.key] as number, showZero);
                                        adjustments = getAdjustmentBreakdown(row, 'inc', reportView === 'Multi Dimension View' ? col.key : undefined);
                                        adjustmentType = 'inc';
                                      }
                                      // Show adjustment breakdown for expense columns
                                      else if (col.key.includes('_exp')) {
                                        formattedValue = formatCurrency(row[col.key] as number, showZero);
                                        adjustments = getAdjustmentBreakdown(row, 'exp', reportView === 'Multi Dimension View' ? col.key : undefined);
                                        adjustmentType = 'exp';
                                      }
                                      else {
                                        formattedValue = formatCurrency(row[col.key] as number, showZero);
                                      }
                                      
                                      // For Multi Dimension View, if value is empty and no adjustments, show empty space to maintain alignment
                                      if (!formattedValue && reportView === 'Multi Dimension View' && adjustments.length === 0) {
                                        return <Box minH="48px" w="100%" />; // Empty box to maintain cell height and alignment
                                      }
                                      
                                      // For Multi Dimension View, use bordered container to group value and adjustments
                                      if (reportView === 'Multi Dimension View' && (formattedValue || adjustments.length > 0)) {
                                        // Determine border color and text color based on column type
                                        let borderColor = 'gray.200';
                                        let bgColor = 'gray.50';
                                        let cellTextColor = 'gray.700';
                                        
                                        if (col.key.includes('_inc') || reportType === 'Only Incomes') {
                                          borderColor = 'green.200';
                                          bgColor = 'green.50';
                                          cellTextColor = 'green.700';
                                        } else if (col.key.includes('_exp') || reportType === 'Only Expense') {
                                          borderColor = 'red.200';
                                          bgColor = 'red.50';
                                          cellTextColor = 'red.700';
                                        } else if (col.key.includes('_net') || reportType === 'Net Profit') {
                                          // For net, use color based on value
                                          let numValue = 0;
                                          if (col.key === 'total_net' && (row.total_net === undefined || row.total_net === null)) {
                                            const totalInc = row.total_inc || 0;
                                            const totalExp = row.total_exp || 0;
                                            numValue = totalInc - totalExp;
                                          } else if (col.key.endsWith('_net') && (row[col.key] === undefined || row[col.key] === null)) {
                                            const incKey = col.key.replace('_net', '_inc');
                                            const expKey = col.key.replace('_net', '_exp');
                                            const incValue = row[incKey] || 0;
                                            const expValue = row[expKey] || 0;
                                            numValue = incValue - expValue;
                                          } else {
                                            numValue = typeof row[col.key] === 'number' ? row[col.key] : parseFloat(String(row[col.key] || 0));
                                          }
                                          borderColor = numValue >= 0 ? 'green.200' : 'red.200';
                                          bgColor = numValue >= 0 ? 'green.50' : 'red.50';
                                          cellTextColor = numValue >= 0 ? 'green.700' : 'red.700';
                                        }
                                        
                                        return (
                                          <Box
                                            border="1px solid"
                                            borderColor={borderColor}
                                            borderRadius="md"
                                            bg={bgColor}
                                            px={2}
                                            py={1.5}
                                            minH="48px"
                                            display="flex"
                                            alignItems="center"
                                            justifyContent="flex-end"
                                            w="100%"
                                          >
                                            <Flex alignItems="center" justifyContent="flex-end" gap={1} flexWrap="wrap">
                                              {formattedValue && (
                                                <Text
                                                  fontWeight={row.is_group && reportView === 'Dimension View' ? '600' : '500'}
                                                  color={cellTextColor}
                                                  fontSize="sm"
                                                >
                                                  {formattedValue}
                                                </Text>
                                              )}
                                              {adjustmentType && adjustments.length > 0 && renderAdjustmentBreakdown(adjustments, adjustmentType, true)}
                                            </Flex>
                                          </Box>
                                        );
                                      }
                                      
                                      // For other views, use original layout
                                      return (
                                        <Flex alignItems="center" gap={1}>
                                          {formattedValue || (reportView === 'Multi Dimension View' ? '' : '₹ 0')}
                                          {adjustmentType && adjustments.length > 0 && renderAdjustmentBreakdown(adjustments, adjustmentType, false)}
                                        </Flex>
                                      );
                                    })() : (row[col.key] || '-')}
                                  </Text>
                                );
                          })()
                        )}
                      </Td>
                    );
                    })}
                  </Tr>
                );
              })
            )}
          </Tbody>
        </Table>
      </Box>

      {/* Footer with Pagination */}
      {filteredData.length > 0 && (
        <Box p={3} borderTop="1px" borderColor="gray.200" bg="gray.50">
          <Flex justify="space-between" align="center" flexWrap="wrap" gap={3}>
            <Text fontSize="sm" color="gray.600">
              {reportView === 'Detailed View' ? (
                <>
                  Showing {startIndex + 1} to {Math.min(endIndex, totalRecords)} of {totalRecords} records
                </>
              ) : (
                <>
                  Showing {sortedData.length} of {safeData.length} records
                </>
              )}
            </Text>
            
            {/* Pagination Controls (for Detailed View and Multi Dimension View with many rows) */}
            {shouldPaginate && totalPages > 1 && (
              <HStack spacing={2}>
                <Button
                  size="sm"
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  isDisabled={currentPage === 1}
                  variant="outline"
                >
                  Previous
                </Button>
                
                <HStack spacing={1}>
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (currentPage <= 3) {
                      pageNum = i + 1;
                    } else if (currentPage >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = currentPage - 2 + i;
                    }
                    
                    return (
                      <Button
                        key={pageNum}
                        size="sm"
                        onClick={() => setCurrentPage(pageNum)}
                        colorScheme={currentPage === pageNum ? 'blue' : 'gray'}
                        variant={currentPage === pageNum ? 'solid' : 'outline'}
                        minW="40px"
                      >
                        {pageNum}
                      </Button>
                    );
                  })}
                </HStack>
                
                <Button
                  size="sm"
                  onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                  isDisabled={currentPage === totalPages}
                  variant="outline"
                >
                  Next
                </Button>
                
                <Text fontSize="sm" color="gray.600" ml={2}>
                  Page {currentPage} of {totalPages}
                </Text>
              </HStack>
            )}
          </Flex>
        </Box>
      )}

      {/* File Viewer Modal */}
      <FileViewerModal
        isOpen={isOpen}
        onClose={onClose}
        attachments={selectedAttachments}
        voucherNo={selectedVoucherNo}
      />

      {/* Voucher Viewer Modal (for Detailed View) */}
      {reportView === 'Detailed View' && (
        <VoucherViewerModal
          isOpen={isVoucherModalOpen}
          onClose={onVoucherModalClose}
          vouchers={voucherData}
          initialIndex={selectedVoucherIndex}
        />
      )}

      {/* Cell Detail Modal (for Multi Dimension View drill-down) */}
      {reportView === 'Multi Dimension View' && metadata && filters && (
        <CellDetailModal
          isOpen={isCellDetailModalOpen}
          onClose={onCellDetailModalClose}
          mainDimensionValue={selectedMainDimValue}
          secondaryDimensionValue={selectedSecondaryDimValue}
          columnType={selectedColumnType}
          baseFilters={{
            report_view: 'Multi Dimension View',
            hide_not_tagged_entries: true,
            main_dimension: filters.main_dimension || metadata.main_dimension || 'Cost Head',
            secondary_dimension: filters.secondary_dimension || metadata.secondary_dimension || 'Cost Center',
            from_date: filters.from_date || metadata.from_date || '',
            to_date: filters.to_date || metadata.to_date || '',
            report_type: reportType,
            include_adjustment: filters.include_adjustment ?? true,
            include_stock_asset:true,
            include_disabled_dimension: filters.include_disabled_dimension ?? false,
            exclude_period_closing_entries: filters.exclude_period_closing_entries ?? true,
            render_as_tree_view: renderAsTreeView,
            dimension: filters.main_dimension || metadata.main_dimension || 'Cost Head',
            dimension_value: [],
            time_period: 'Cumulative',
            additional_accounts: filters.additional_accounts || [],
            additional_dimensions: filters.additional_dimensions || [],
            company: filters.company,
            internal_adjustment_type: filters.internal_adjustment_type,
          }}
          mainDimensionLabel={metadata.main_dimension_label || metadata.main_dimension || 'Main Dimension'}
          secondaryDimensionLabel={metadata.secondary_dimension_label || metadata.secondary_dimension || 'Secondary Dimension'}
        />
      )}
    </Box>
  );
};

