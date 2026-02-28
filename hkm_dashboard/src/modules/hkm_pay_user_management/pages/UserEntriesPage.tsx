import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Box,
  Container,
  Heading,
  Text,
  Button,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Spinner,
  Alert,
  AlertIcon,
  VStack,
  HStack,
  FormControl,
  FormLabel,
  Select,
  Input,
  useToast,
  Checkbox,
  IconButton,
  Popover,
  PopoverTrigger,
  PopoverContent,
  PopoverHeader,
  PopoverBody,
  PopoverArrow,
  PopoverCloseButton,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Card,
  CardBody,
  Divider,
  useColorModeValue,
} from '@chakra-ui/react';
import { FiArrowLeft, FiDownload, FiCheck, FiX, FiSettings, FiFileText, FiMove } from 'react-icons/fi';
import { hkmpUserApi } from '../api/hkmpUserApi';
import { HKMPEntry, HKMPEntryFilters, HKMPUser } from '../types';

// Helper function to get current month's first and last day
const getCurrentMonthDates = () => {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth();
  
  // First day of current month
  const fromDate = new Date(year, month, 1);
  // Last day of current month
  const toDate = new Date(year, month + 1, 0);
  
  // Format as YYYY-MM-DD
  const formatDate = (date: Date) => {
    return date.toISOString().split('T')[0];
  };
  
  return {
    from_date: formatDate(fromDate),
    to_date: formatDate(toDate),
  };
};

const UserEntriesPage: React.FC = () => {
  const { userId } = useParams<{ userId: string }>();
  const navigate = useNavigate();
  const [user, setUser] = useState<HKMPUser | null>(null);
  const [entries, setEntries] = useState<HKMPEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [userLoading, setUserLoading] = useState(true);
  const [updatingEntry, setUpdatingEntry] = useState<string | null>(null);
  const [selectedUserFilter, setSelectedUserFilter] = useState<string>(userId || '');
  const [hkmpUsers, setHkmpUsers] = useState<HKMPUser[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  
  // Initialize with current month dates
  const currentMonthDates = getCurrentMonthDates();
  const [filters, setFilters] = useState<HKMPEntryFilters>({
    status: '',
    transfer_type: '',
    from_date: currentMonthDates.from_date,
    to_date: currentMonthDates.to_date,
    company: '',
    debited_from: '',
    bill_received: undefined,
    is_return: undefined,
  });
  const [companies, setCompanies] = useState<Array<{ name: string }>>([]);
  const [debitedFromOptions, setDebitedFromOptions] = useState<string[]>([]);
  
  // Local filters state (client-side filtering)
  const [localFilters, setLocalFilters] = useState({
    amount: '',
    remarks: '',
    utr: '',
    date: '',
  });
  
  // Column order state with localStorage persistence
  const defaultColumnOrder = [
    'user',
    'entryId',
    'date',
    'status',
    'type',
    'amount',
    'company',
    'debitedFrom',
    'beneficiary',
    'accountNumber',
    'ifscCode',
    'upiId',
    'mobile',
    'remarks',
    'utr',
    'bill',
    'return',
  ];

  const [columnOrder, setColumnOrder] = useState<string[]>(() => {
    const saved = localStorage.getItem('hkmp_entries_column_order');
    if (saved) {
      const parsed = JSON.parse(saved);
      // Ensure 'user' is in columnOrder if it's missing (for backward compatibility)
      if (!parsed.includes('user')) {
        return ['user', ...parsed];
      }
      return parsed;
    }
    return defaultColumnOrder;
  });

  // Column visibility state with localStorage persistence
  const [visibleColumns, setVisibleColumns] = useState(() => {
    const saved = localStorage.getItem('hkmp_entries_visible_columns');
    const defaultVisibility = {
      user: true, // Always show user column with full name
      entryId: true,
      date: true,
      status: true,
      type: true,
      amount: true,
      company: true,
      debitedFrom: true,
      beneficiary: true,
      accountNumber: true,
      ifscCode: true,
      upiId: true,
      mobile: true,
      remarks: true,
      utr: true,
      bill: true,
      return: true,
    };
    if (saved) {
      const parsed = JSON.parse(saved);
      // Ensure 'user' key exists in parsed object and default to true
      if (!('user' in parsed)) {
        parsed.user = true;
      }
      return parsed;
    }
    return defaultVisibility;
  });

  // Ensure user column is always in columnOrder
  useEffect(() => {
    if (!columnOrder.includes('user')) {
      setColumnOrder((prev: string[]) => ['user', ...prev]);
    }
  }, [columnOrder]);

  // Drag and drop state
  const [draggedColumn, setDraggedColumn] = useState<string | null>(null);
  const [dragOverColumn, setDragOverColumn] = useState<string | null>(null);
  
  // Column width state with localStorage persistence
  const defaultColumnWidths: { [key: string]: number } = {
    user: 150,
    entryId: 120,
    date: 180,
    status: 100,
    type: 100,
    amount: 120,
    company: 200,
    debitedFrom: 200,
    beneficiary: 150,
    accountNumber: 150,
    ifscCode: 120,
    upiId: 180,
    mobile: 120,
    remarks: 200,
    utr: 150,
    bill: 80,
    return: 80,
  };

  const [columnWidths, setColumnWidths] = useState<{ [key: string]: number }>(() => {
    const saved = localStorage.getItem('hkmp_entries_column_widths');
    return saved ? JSON.parse(saved) : defaultColumnWidths;
  });

  // Column resize state
  const [resizingColumn, setResizingColumn] = useState<string | null>(null);
  const [resizeStartX, setResizeStartX] = useState(0);
  const [resizeStartWidth, setResizeStartWidth] = useState(0);
  
  // Popover state for column visibility
  const [isPopoverOpen, setIsPopoverOpen] = useState(false);
  
  // Table height ref for preserving height
  const tableHeightRef = useRef<number>(0);
  
  const toast = useToast();
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  
  // Fetch user details and options on mount
  useEffect(() => {
    fetchHkmpUsers();
    if (userId) {
      fetchUserDetails();
      fetchCompanies();
      setSelectedUserFilter(userId);
    } else {
      fetchCompanies();
    }
  }, [userId]);
  
  const fetchHkmpUsers = async () => {
    try {
      setLoadingUsers(true);
      const users = await hkmpUserApi.getAllUsers();
      setHkmpUsers(users);
    } catch (error: any) {
      console.error('Error fetching HKMP users:', error);
      toast({
        title: 'Warning',
        description: 'Failed to load user list for filter',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setLoadingUsers(false);
    }
  };
  
  // Fetch debited_from options after user filter is set
  useEffect(() => {
    if (selectedUserFilter) {
      fetchDebitedFromOptions();
    }
  }, [selectedUserFilter]);
  
  // Track if initial load has been done
  const [hasInitialLoaded, setHasInitialLoaded] = useState(false);
  
  // Helper function to fetch entries
  const fetchEntriesWithFilters = useCallback(async () => {
    // Validate required dates before fetching
    if (!filters.from_date || !filters.to_date) {
      return;
    }
    
    // Empty string means "All Users" which is valid, so we proceed with fetch
    // selectedUserFilter can be empty string (All Users) or a specific user
    
    try {
      setLoading(true);
      
      // Build filters object, removing empty values
      const apiFilters: any = {};
      if (filters.status) apiFilters.status = filters.status;
      if (filters.transfer_type) apiFilters.transfer_type = filters.transfer_type;
      if (filters.company) apiFilters.company = filters.company;
      if (filters.debited_from) apiFilters.debited_from = filters.debited_from;
      if (filters.bill_received !== undefined && filters.bill_received !== null) {
        apiFilters.bill_received = filters.bill_received;
      }
      if (filters.is_return !== undefined && filters.is_return !== null) {
        apiFilters.is_return = filters.is_return;
      }
      
      // Dates are mandatory, always include them
      if (filters.from_date && filters.to_date) {
        apiFilters.creation = ['between', [filters.from_date, filters.to_date]];
      } else if (filters.from_date) {
        apiFilters.creation = ['>=', filters.from_date];
      } else if (filters.to_date) {
        apiFilters.creation = ['<=', filters.to_date];
      }
      
      // Use selectedUserFilter - if empty, fetch all users' entries
      const userToFetch = selectedUserFilter || null;
      const data = await hkmpUserApi.getUserEntries(userToFetch, apiFilters);
      setEntries(data);
      
      // Update user state if a specific user is selected
      if (selectedUserFilter && !user) {
        const foundUser = hkmpUsers.find(u => u.user === selectedUserFilter);
        if (foundUser) {
          setUser(foundUser);
        }
      }
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to fetch entries',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  }, [
    selectedUserFilter,
    filters.status,
    filters.transfer_type,
    filters.from_date,
    filters.to_date,
    filters.company,
    filters.debited_from,
    filters.bill_received,
    filters.is_return,
    user,
    hkmpUsers,
    toast,
  ]);
  
  // Initial load when user filter and dates are set
  useEffect(() => {
    // selectedUserFilter can be empty string (All Users) or a specific user
    // Both are valid, so we check if dates are set and initial load hasn't happened
    if (filters.from_date && filters.to_date && !hasInitialLoaded) {
      fetchEntriesWithFilters();
      setHasInitialLoaded(true);
    }
  }, [selectedUserFilter, filters.from_date, filters.to_date, hasInitialLoaded, fetchEntriesWithFilters]);
  
  // Automatically fetch entries when filters change (after initial load)
  useEffect(() => {
    // Don't fetch if initial load hasn't happened yet or dates are missing
    if (!hasInitialLoaded) return;
    
    // Validate required dates before fetching
    if (!filters.from_date || !filters.to_date) {
      return;
    }
    
    // Debounce filter changes to avoid too many API calls
    const timeoutId = setTimeout(() => {
      fetchEntriesWithFilters();
    }, 300); // 300ms debounce
    
    return () => clearTimeout(timeoutId);
  }, [selectedUserFilter, hasInitialLoaded, fetchEntriesWithFilters, filters.from_date, filters.to_date]);
  
  // Fetch debited_from options when entries are loaded (update if new entries have new debited_from values)
  useEffect(() => {
    if (entries.length > 0) {
      const uniqueDebitedFrom = Array.from(
        new Set(entries.map(e => e.debited_from).filter(Boolean))
      ).sort();
      setDebitedFromOptions(prev => {
        const combined = Array.from(new Set([...prev, ...uniqueDebitedFrom])).sort();
        return combined;
      });
    }
  }, [entries]);
  
  // Save column visibility to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('hkmp_entries_visible_columns', JSON.stringify(visibleColumns));
  }, [visibleColumns]);
  
  // Store table height on mount and when entries load
  useEffect(() => {
    if (entries.length > 0) {
      const card = document.querySelector('[data-table-card]') as HTMLElement;
      if (card && card.offsetHeight > 0 && !tableHeightRef.current) {
        tableHeightRef.current = card.offsetHeight;
      }
    }
  }, [entries.length]);
  
  // Preserve table height when columns change or popover opens
  useEffect(() => {
    const preserveHeight = () => {
      const card = document.querySelector('[data-table-card]') as HTMLElement;
      const tableContainer = document.querySelector('[data-table-container]') as HTMLElement;
      if (card && tableContainer) {
        // Get current height or calculate it
        let targetHeight = tableHeightRef.current;
        
        if (!targetHeight || targetHeight < 400) {
          // Calculate available height based on viewport
          const viewportHeight = window.innerHeight;
          const headerHeight = 80;
          const filtersHeight = 120;
          targetHeight = Math.max(400, viewportHeight - headerHeight - filtersHeight - 100);
          tableHeightRef.current = targetHeight;
        }
        
        // Lock the height to prevent shrinking
        card.style.height = `${targetHeight}px`;
        card.style.minHeight = `${targetHeight}px`;
        card.style.maxHeight = `${targetHeight}px`;
        tableContainer.style.minHeight = `${targetHeight - 20}px`;
      }
    };
    
    // Preserve height immediately and after a short delay
    preserveHeight();
    const timeoutId = setTimeout(preserveHeight, 50);
    return () => clearTimeout(timeoutId);
  }, [visibleColumns, isPopoverOpen, entries.length]);
  
  // Store table height before popover opens
  const handlePopoverOpen = () => {
    const card = document.querySelector('[data-table-card]') as HTMLElement;
    if (card && card.offsetHeight > 0) {
      tableHeightRef.current = card.offsetHeight;
      // Lock height immediately
      card.style.height = `${card.offsetHeight}px`;
      card.style.minHeight = `${card.offsetHeight}px`;
      card.style.maxHeight = `${card.offsetHeight}px`;
    }
    setIsPopoverOpen(true);
  };
  
  const handlePopoverClose = () => {
    setIsPopoverOpen(false);
  };

  // Save column order to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('hkmp_entries_column_order', JSON.stringify(columnOrder));
  }, [columnOrder]);

  // Save column widths to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('hkmp_entries_column_widths', JSON.stringify(columnWidths));
  }, [columnWidths]);

  // Drag and drop handlers
  const handleDragStart = (columnKey: string) => {
    setDraggedColumn(columnKey);
  };

  const handleDragOver = (e: React.DragEvent, columnKey: string) => {
    e.preventDefault();
    if (draggedColumn && draggedColumn !== columnKey) {
      setDragOverColumn(columnKey);
    }
  };

  const handleDragLeave = () => {
    setDragOverColumn(null);
  };

  const handleDrop = (e: React.DragEvent, targetColumn: string) => {
    e.preventDefault();
    if (!draggedColumn || draggedColumn === targetColumn) {
      setDraggedColumn(null);
      setDragOverColumn(null);
      return;
    }

    const newOrder = [...columnOrder];
    const draggedIndex = newOrder.indexOf(draggedColumn);
    const targetIndex = newOrder.indexOf(targetColumn);

    newOrder.splice(draggedIndex, 1);
    newOrder.splice(targetIndex, 0, draggedColumn);

    setColumnOrder(newOrder);
    setDraggedColumn(null);
    setDragOverColumn(null);

    toast({
      title: 'Column Reordered',
      description: `Moved ${draggedColumn} column`,
      status: 'success',
      duration: 2000,
      isClosable: true,
    });
  };

  const resetColumnOrder = () => {
    setColumnOrder(defaultColumnOrder);
    toast({
      title: 'Column Order Reset',
      description: 'Columns restored to default order',
      status: 'info',
      duration: 2000,
      isClosable: true,
    });
  };

  // Column resize handlers
  const handleResizeStart = (e: React.MouseEvent, columnKey: string) => {
    e.preventDefault();
    e.stopPropagation();
    setResizingColumn(columnKey);
    setResizeStartX(e.clientX);
    setResizeStartWidth(columnWidths[columnKey] || defaultColumnWidths[columnKey] || 150);
  };

  useEffect(() => {
    const handleResizeMove = (e: MouseEvent) => {
      if (!resizingColumn) return;
      
      const diff = e.clientX - resizeStartX;
      const newWidth = Math.max(50, resizeStartWidth + diff); // Minimum width of 50px
      
      setColumnWidths((prev) => ({
        ...prev,
        [resizingColumn]: newWidth,
      }));
    };

    const handleResizeEnd = () => {
      setResizingColumn(null);
    };

    if (resizingColumn) {
      document.addEventListener('mousemove', handleResizeMove);
      document.addEventListener('mouseup', handleResizeEnd);
      
      return () => {
        document.removeEventListener('mousemove', handleResizeMove);
        document.removeEventListener('mouseup', handleResizeEnd);
      };
    }
  }, [resizingColumn, resizeStartX, resizeStartWidth]);

  const resetColumnWidths = () => {
    setColumnWidths(defaultColumnWidths);
    toast({
      title: 'Column Widths Reset',
      description: 'Column widths restored to default',
      status: 'info',
      duration: 2000,
      isClosable: true,
    });
  };

  // Column configuration
  const columnConfig: { [key: string]: { label: string; renderHeader?: (columnKey: string) => React.ReactNode; renderCell: (entry: HKMPEntry) => React.ReactNode; props?: any } } = {
    user: {
      label: 'USER',
      renderCell: (entry) => (
        <Td py={2} minW="120px">
          <Text fontSize="xs" fontWeight="medium" color="teal.600">
            {entry.user_full_name || hkmpUsers.find(u => u.user === entry.user)?.full_name || entry.user}
          </Text>
        </Td>
      ),
    },
    entryId: {
      label: 'ENTRY ID',
      renderCell: (entry) => (
        <Td py={2}>
          <Text fontSize="xs" fontFamily="mono">{entry.name}</Text>
        </Td>
      ),
    },
    date: {
      label: 'DATE',
      renderCell: (entry) => (
        <Td py={2}>
          <Text fontSize="xs">{formatDate(entry.creation)}</Text>
        </Td>
      ),
    },
    status: {
      label: 'STATUS',
      renderCell: (entry) => (
        <Td py={2}>
          <Badge colorScheme={getStatusColor(entry.status)} fontSize="10px" px={1.5} py={0.5}>
            {entry.status}
          </Badge>
        </Td>
      ),
    },
    type: {
      label: 'TYPE',
      renderCell: (entry) => (
        <Td py={2}>
          <Badge colorScheme="purple" variant="subtle" fontSize="10px" px={1.5} py={0.5}>
            {entry.transfer_type}
          </Badge>
        </Td>
      ),
    },
    amount: {
      label: 'AMOUNT',
      renderCell: (entry) => (
        <Td py={2} isNumeric fontWeight="semibold" fontSize="xs">
          {formatCurrency(entry.amount)}
        </Td>
      ),
      props: { isNumeric: true },
    },
    company: {
      label: 'COMPANY',
      renderCell: (entry) => (
        <Td py={2} whiteSpace="normal">
          <Text fontSize="xs" title={entry.company || '-'}>{entry.company || '-'}</Text>
        </Td>
      ),
    },
    debitedFrom: {
      label: 'DEBITED FROM',
      renderCell: (entry) => (
        <Td py={2} whiteSpace="normal">
          <Text fontSize="xs" title={entry.debited_from || '-'}>{entry.debited_from || '-'}</Text>
        </Td>
      ),
    },
    beneficiary: {
      label: 'BENEFICIARY',
      renderCell: (entry) => (
        <Td py={2} whiteSpace="normal">
          <Text fontSize="xs" title={entry.beneficiary_name || '-'}>{entry.beneficiary_name || '-'}</Text>
        </Td>
      ),
    },
    accountNumber: {
      label: 'ACCOUNT NUMBER',
      renderCell: (entry) => (
        <Td py={2}>
          <Text fontSize="xs" fontFamily="mono">{entry.account_number || '-'}</Text>
        </Td>
      ),
    },
    ifscCode: {
      label: 'IFSC CODE',
      renderCell: (entry) => (
        <Td py={2}>
          <Text fontSize="xs" fontFamily="mono">{entry.ifsc_code || '-'}</Text>
        </Td>
      ),
    },
    upiId: {
      label: 'UPI ID',
      renderCell: (entry) => (
        <Td py={2}>
          <Text fontSize="xs" fontFamily="mono">{entry.upi_id || '-'}</Text>
        </Td>
      ),
    },
    mobile: {
      label: 'MOBILE',
      renderCell: (entry) => (
        <Td py={2}>
          <Text fontSize="xs">{entry.mobile_number || '-'}</Text>
        </Td>
      ),
    },
    remarks: {
      label: 'REMARKS',
      renderCell: (entry) => (
        <Td py={2}>
          <Text fontSize="xs" noOfLines={1} maxW="200px">{entry.remarks || '-'}</Text>
        </Td>
      ),
    },
    utr: {
      label: 'UTR',
      renderCell: (entry) => (
        <Td py={2}>
          <Text fontSize="xs" fontFamily="mono">{entry.utr || '-'}</Text>
        </Td>
      ),
    },
    bill: {
      label: 'BILL',
      renderCell: (entry) => (
        <Td py={2} textAlign="center">
          <Checkbox
            isChecked={entry.bill_received === 1}
            onChange={() => handleUpdateStatus(entry.name, 'bill_received', entry.bill_received)}
            isDisabled={updatingEntry === entry.name}
            colorScheme="green"
            size="md"
            sx={{
              '& .chakra-checkbox__control': {
                borderWidth: '2px',
                borderColor: 'gray.300',
                _checked: {
                  borderColor: 'green.500',
                  bg: 'green.500',
                },
                _hover: {
                  borderColor: 'green.400',
                },
                _disabled: {
                  opacity: 0.6,
                },
              },
            }}
          />
        </Td>
      ),
      props: { textAlign: 'center' },
    },
    return: {
      label: 'RETURN',
      renderCell: (entry) => (
        <Td py={2} textAlign="center">
          <Checkbox
            isChecked={entry.is_return === 1}
            onChange={() => handleUpdateStatus(entry.name, 'is_return', entry.is_return)}
            isDisabled={updatingEntry === entry.name}
            colorScheme="orange"
            size="md"
            sx={{
              '& .chakra-checkbox__control': {
                borderWidth: '2px',
                borderColor: 'gray.300',
                _checked: {
                  borderColor: 'orange.500',
                  bg: 'orange.500',
                },
                _hover: {
                  borderColor: 'orange.400',
                },
                _disabled: {
                  opacity: 0.6,
                },
              },
            }}
          />
        </Td>
      ),
      props: { textAlign: 'center' },
    },
  };
  
  const fetchUserDetails = async () => {
    try {
      setUserLoading(true);
      const allUsers = await hkmpUserApi.getAllUsers();
      const foundUser = allUsers.find(u => u.user === userId || u.name === userId);
      if (foundUser) {
        setUser(foundUser);
      } else {
        toast({
          title: 'Error',
          description: 'User not found',
          status: 'error',
          duration: 5000,
          isClosable: true,
        });
        navigate('/hkm-pay-user-management');
      }
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to fetch user details',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
      navigate('/hkm-pay-user-management');
    } finally {
      setUserLoading(false);
    }
  };
  
  const fetchCompanies = async () => {
    try {
      const data = await hkmpUserApi.getAllCompanies();
      setCompanies(data);
    } catch (error) {
      console.error('Error fetching companies:', error);
    }
  };
  
  const fetchDebitedFromOptions = async () => {
    if (!selectedUserFilter) return;
    
    try {
      // Fetch all entries for the user (without filters) to get unique debited_from values
      const allEntries = await hkmpUserApi.getUserEntries(selectedUserFilter, {});
      const uniqueDebitedFrom = Array.from(
        new Set(allEntries.map((e: HKMPEntry) => e.debited_from).filter(Boolean))
      ).sort();
      setDebitedFromOptions(uniqueDebitedFrom);
    } catch (error) {
      console.error('Error fetching debited_from options:', error);
    }
  };
  
  const toggleColumn = (columnKey: string) => {
    setVisibleColumns((prev: any) => {
      const newColumns = {
        ...prev,
        [columnKey]: !prev[columnKey],
      };
      // Force layout recalculation on small screens
      setTimeout(() => {
        window.dispatchEvent(new Event('resize'));
      }, 100);
      return newColumns;
    });
  };
  
  const showAllColumns = () => {
    const allVisible = {
      user: !selectedUserFilter, // Show user column if no user filter
      entryId: true,
      date: true,
      status: true,
      type: true,
      amount: true,
      company: true,
      debitedFrom: true,
      beneficiary: true,
      accountNumber: true,
      ifscCode: true,
      upiId: true,
      mobile: true,
      remarks: true,
      utr: true,
      bill: true,
      return: true,
    };
    setVisibleColumns(allVisible);
  };
  
  const hideAllOptionalColumns = () => {
    setVisibleColumns({
      user: !selectedUserFilter, // Show user column if no user filter
      entryId: true,
      date: true,
      status: true,
      type: false,
      amount: true,
      company: true,
      debitedFrom: true,
      beneficiary: false,
      accountNumber: false,
      ifscCode: false,
      upiId: false,
      mobile: false,
      remarks: false,
      utr: false,
      bill: true,
      return: true,
    });
  };

  const handleGetEntries = async () => {
    // Validate required dates
    if (!filters.from_date || !filters.to_date) {
      toast({
        title: 'Validation Error',
        description: 'From Date and To Date are required',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }
    
    // Empty string means "All Users" which is valid, so no need to validate user filter
    // Use the same fetch function (entries will be updated automatically)
    await fetchEntriesWithFilters();
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };
  
  const formatDateForExport = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };
  
  const exportToCSV = () => {
    if (filteredEntries.length === 0) {
      toast({
        title: 'No Data',
        description: 'No filtered entries to export. Please adjust filters or load entries first.',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }
    
    // Define CSV headers based on visible columns in column order
    const headers: string[] = [];
    const headerMap: { [key: string]: string } = {
      user: 'User',
      entryId: 'Entry ID',
      date: 'Date',
      status: 'Status',
      type: 'Transfer Type',
      amount: 'Amount',
      company: 'Company',
      debitedFrom: 'Debited From',
      beneficiary: 'Beneficiary',
      accountNumber: 'Account Number',
      ifscCode: 'IFSC Code',
      upiId: 'UPI ID',
      mobile: 'Mobile',
      remarks: 'Remarks',
      utr: 'UTR',
      bill: 'Bill Received',
      return: 'Is Return',
    };
    
    // Build headers in column order
    columnOrder.forEach(key => {
      if (visibleColumns[key] && headerMap[key]) {
        headers.push(headerMap[key]);
      }
    });
    
    // Build CSV rows
    const csvRows = [headers.join(',')];
    
    const getCellValue = (columnKey: string, entry: HKMPEntry): string => {
      switch (columnKey) {
        case 'user': return `"${entry.user_full_name || hkmpUsers.find(u => u.user === entry.user)?.full_name || entry.user}"`;
        case 'entryId': return `"${entry.name || ''}"`;
        case 'date': return `"${formatDateForExport(entry.creation)}"`;
        case 'status': return `"${entry.status || ''}"`;
        case 'type': return `"${entry.transfer_type || ''}"`;
        case 'amount': return String(entry.amount || 0);
        case 'company': return `"${entry.company || ''}"`;
        case 'debitedFrom': return `"${entry.debited_from || ''}"`;
        case 'beneficiary': return `"${entry.beneficiary_name || ''}"`;
        case 'accountNumber': return `"${entry.account_number || ''}"`;
        case 'ifscCode': return `"${entry.ifsc_code || ''}"`;
        case 'upiId': return `"${entry.upi_id || ''}"`;
        case 'mobile': return String(entry.mobile_number || '');
        case 'remarks': return `"${(entry.remarks || '').replace(/"/g, '""')}"`;
        case 'utr': return `"${entry.utr || ''}"`;
        case 'bill': return entry.bill_received === 1 ? 'Yes' : 'No';
        case 'return': return entry.is_return === 1 ? 'Yes' : 'No';
        default: return '';
      }
    };
    
    filteredEntries.forEach(entry => {
      const row: string[] = [];
      columnOrder.forEach(key => {
        if (visibleColumns[key]) {
          row.push(getCellValue(key, entry));
        }
      });
      csvRows.push(row.join(','));
    });
    
    // Create and download CSV
    const csvContent = csvRows.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `HKMP_Entries_${selectedUserFilter || 'all_users'}_${filters.from_date}_to_${filters.to_date}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    toast({
      title: 'Export Successful',
      description: `Exported ${filteredEntries.length} entries to CSV`,
      status: 'success',
      duration: 3000,
      isClosable: true,
    });
  };
  
  const exportToExcel = () => {
    if (filteredEntries.length === 0) {
      toast({
        title: 'No Data',
        description: 'No filtered entries to export. Please adjust filters or load entries first.',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }
    
    // Define headers based on visible columns in column order
    const headers: string[] = [];
    const headerMap: { [key: string]: string } = {
      user: 'User',
      entryId: 'Entry ID',
      date: 'Date',
      status: 'Status',
      type: 'Transfer Type',
      amount: 'Amount',
      company: 'Company',
      debitedFrom: 'Debited From',
      beneficiary: 'Beneficiary',
      accountNumber: 'Account Number',
      ifscCode: 'IFSC Code',
      upiId: 'UPI ID',
      mobile: 'Mobile',
      remarks: 'Remarks',
      utr: 'UTR',
      bill: 'Bill Received',
      return: 'Is Return',
    };
    
    // Build headers in column order
    columnOrder.forEach(key => {
      if (visibleColumns[key] && headerMap[key]) {
        headers.push(headerMap[key]);
      }
    });
    
    const getExcelCellValue = (columnKey: string, entry: HKMPEntry): string => {
      switch (columnKey) {
        case 'user': return entry.user_full_name || hkmpUsers.find(u => u.user === entry.user)?.full_name || entry.user;
        case 'entryId': return entry.name || '';
        case 'date': return formatDateForExport(entry.creation);
        case 'status': return entry.status || '';
        case 'type': return entry.transfer_type || '';
        case 'amount': return `<td class="number">${formatCurrency(entry.amount || 0)}</td>`;
        case 'company': return entry.company || '';
        case 'debitedFrom': return entry.debited_from || '';
        case 'beneficiary': return entry.beneficiary_name || '';
        case 'accountNumber': return entry.account_number || '';
        case 'ifscCode': return entry.ifsc_code || '';
        case 'upiId': return entry.upi_id || '';
        case 'mobile': return String(entry.mobile_number || '');
        case 'remarks': return (entry.remarks || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        case 'utr': return entry.utr || '';
        case 'bill': return entry.bill_received === 1 ? 'Yes' : 'No';
        case 'return': return entry.is_return === 1 ? 'Yes' : 'No';
        default: return '';
      }
    };
    
    // Build HTML table for Excel
    let htmlContent = `
      <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
      <head>
        <meta charset="utf-8">
        <!--[if gte mso 9]>
        <xml>
          <x:ExcelWorkbook>
            <x:ExcelWorksheets>
              <x:ExcelWorksheet>
                <x:Name>HKMP Entries</x:Name>
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
          th { background-color: #2d3748; color: white; padding: 8px; text-align: left; font-weight: bold; border: 1px solid #ddd; }
          td { padding: 6px 8px; border: 1px solid #ddd; }
          .number { text-align: right; }
        </style>
      </head>
      <body>
        <h2>HKMP Entries - ${selectedUserFilter ? (hkmpUsers.find(u => u.user === selectedUserFilter)?.full_name || selectedUserFilter) : 'All Users'}</h2>
        <p><strong>Period:</strong> ${filters.from_date} to ${filters.to_date}</p>
        <p><strong>Total Entries:</strong> ${filteredEntries.length} | <strong>Total Amount:</strong> ${formatCurrency(filteredEntries.reduce((sum, entry) => sum + (entry.amount || 0), 0))}</p>
        <table>
          <thead>
            <tr>
              ${headers.map(h => `<th>${h}</th>`).join('')}
            </tr>
          </thead>
          <tbody>
    `;
    
    filteredEntries.forEach(entry => {
      htmlContent += '<tr>';
      columnOrder.forEach(key => {
        if (visibleColumns[key]) {
          const value = getExcelCellValue(key, entry);
          if (key === 'amount') {
            htmlContent += value;
          } else {
            htmlContent += `<td>${value}</td>`;
          }
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
    
    // Create and download Excel file
    const blob = new Blob([htmlContent], { type: 'application/vnd.ms-excel' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `HKMP_Entries_${selectedUserFilter || 'all_users'}_${filters.from_date}_to_${filters.to_date}.xls`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    toast({
      title: 'Export Successful',
      description: `Exported ${filteredEntries.length} entries to Excel`,
      status: 'success',
      duration: 3000,
      isClosable: true,
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Success':
        return 'green';
      case 'Failed':
        return 'red';
      case 'Processing':
        return 'blue';
      case 'Pending':
        return 'yellow';
      default:
        return 'gray';
    }
  };

  const getTotalAmount = () => {
    return entries.reduce((sum, entry) => sum + (entry.amount || 0), 0);
  };

  // Filter entries based on local filters
  const getFilteredEntries = () => {
    // If all filters are empty, return all entries
    const hasActiveFilters = localFilters.amount.trim() || 
                            localFilters.remarks.trim() || 
                            localFilters.utr.trim() || 
                            localFilters.date.trim();
    
    if (!hasActiveFilters) {
      return entries;
    }

    return entries.filter((entry) => {
      // Filter by amount (like operation - partial match)
      if (localFilters.amount.trim()) {
        const filterAmountStr = localFilters.amount.replace(/[₹,\s]/g, '').trim();
        if (filterAmountStr) {
          const entryAmountStr = String(entry.amount || 0);
          if (!entryAmountStr.includes(filterAmountStr)) {
            return false;
          }
        }
      }

      // Filter by remarks (case-insensitive partial match - like operation)
      if (localFilters.remarks.trim()) {
        const remarks = (entry.remarks || '').toLowerCase();
        const filterRemarks = localFilters.remarks.trim().toLowerCase();
        if (!remarks.includes(filterRemarks)) {
          return false;
        }
      }

      // Filter by UTR (case-insensitive partial match - like operation)
      if (localFilters.utr.trim()) {
        const utr = (entry.utr || '').toLowerCase();
        const filterUtr = localFilters.utr.trim().toLowerCase();
        if (!utr.includes(filterUtr)) {
          return false;
        }
      }

      // Filter by date (only date part, not time)
      if (localFilters.date.trim()) {
        try {
          const entryDate = new Date(entry.creation).toISOString().split('T')[0];
          const filterDate = localFilters.date.trim();
          if (entryDate !== filterDate) {
            return false;
          }
        } catch (e) {
          // If date parsing fails, don't filter this entry
          return true;
        }
      }

      return true;
    });
  };

  const filteredEntries = getFilteredEntries();

  const handleUpdateStatus = async (entryName: string, field: 'bill_received' | 'is_return', currentValue: number) => {
    try {
      setUpdatingEntry(entryName);
      const newValue = currentValue === 1 ? 0 : 1;
      
      await hkmpUserApi.updateEntryStatus(entryName, field, newValue);
      
      // Update local state
      setEntries(prevEntries => 
        prevEntries.map(entry => 
          entry.name === entryName 
            ? { ...entry, [field]: newValue }
            : entry
        )
      );
      
      toast({
        title: 'Success',
        description: `${field === 'bill_received' ? 'Bill status' : 'Return status'} updated successfully`,
        status: 'success',
        duration: 2000,
        isClosable: true,
      });
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to update status',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setUpdatingEntry(null);
    }
  };

  if (userLoading && userId) {
    return (
      <Box minH="100vh" bg="gray.50" display="flex" alignItems="center" justifyContent="center">
        <VStack spacing={4}>
          <Spinner size="xl" color="teal.500" thickness="4px" />
          <Text color="gray.600">Loading user details...</Text>
        </VStack>
      </Box>
    );
  }

  return (
    <Box h="100vh" bg="gray.50" display="flex" flexDirection="column" overflow="hidden">
      {/* Header */}
      <Box bg={bgColor} shadow="sm" flexShrink={0}>
        <Container maxW="100%" px={4} py={2}>
          <HStack spacing={3}>
            <IconButton
              as={Link}
              to="/hkm-pay-user-management"
              icon={<FiArrowLeft />}
              aria-label="Back to user management"
              variant="ghost"
              size="md"
            />
            <Box flex="1">
              <Heading size="md" color="teal.600">
                HKMP Entries - {selectedUserFilter 
                  ? (hkmpUsers.find(u => u.user === selectedUserFilter)?.full_name || selectedUserFilter)
                  : 'All Users'}
              </Heading>
              <Text color="gray.600" mt={0} fontSize="xs">
                Transaction history and filter entries
              </Text>
            </Box>
          </HStack>
        </Container>
      </Box>

      {/* Main Content */}
      <Container maxW="100%" px={4} py={2} flex="1" display="flex" flexDirection="column" minH={0} overflow="hidden">
        <VStack spacing={2} align="stretch" flex="1" minH={0} overflow="hidden">
          {/* Filters Section */}
          <Card flexShrink={0}>
            <CardBody p={3}>
              <Text fontWeight="bold" fontSize="xs" mb={2} color="teal.700">
                Filters
              </Text>
              <VStack spacing={1.5}>
                <HStack spacing={2} width="full" flexWrap="wrap">
                  <FormControl maxW="200px">
                    <FormLabel fontSize="2xs" mb={0.5}>User</FormLabel>
                    <Select
                      value={selectedUserFilter}
                      onChange={(e) => {
                        setSelectedUserFilter(e.target.value);
                        setHasInitialLoaded(false);
                        if (e.target.value) {
                          const foundUser = hkmpUsers.find(u => u.user === e.target.value);
                          if (foundUser) {
                            setUser(foundUser);
                          }
                        } else {
                          setUser(null);
                        }
                      }}
                      size="sm"
                    >
                      <option value="">All Users</option>
                      {loadingUsers ? (
                        <option disabled>Loading...</option>
                      ) : (
                        hkmpUsers.map((u) => (
                          <option key={u.user} value={u.user}>
                            {u.full_name || u.user}
                          </option>
                        ))
                      )}
                    </Select>
                  </FormControl>

                  <FormControl maxW="140px">
                    <FormLabel fontSize="2xs" mb={0.5}>Status</FormLabel>
                    <Select
                      placeholder="All Status"
                      value={filters.status}
                      onChange={(e) =>
                        setFilters({ ...filters, status: e.target.value })
                      }
                      size="sm"
                    >
                      <option value="Pending">Pending</option>
                      <option value="Processing">Processing</option>
                      <option value="Success">Success</option>
                      <option value="Failed">Failed</option>
                    </Select>
                  </FormControl>

                  <FormControl maxW="140px">
                    <FormLabel fontSize="2xs" mb={0.5}>Transfer Type</FormLabel>
                    <Select
                      placeholder="All Types"
                      value={filters.transfer_type}
                      onChange={(e) =>
                        setFilters({ ...filters, transfer_type: e.target.value })
                      }
                      size="sm"
                    >
                      <option value="UPI">UPI</option>
                      <option value="IMPS">IMPS</option>
                      <option value="NEFT">NEFT</option>
                      <option value="RTGS">RTGS</option>
                    </Select>
                  </FormControl>

                  <FormControl maxW="140px" isRequired>
                    <FormLabel fontSize="2xs" mb={0.5}>From Date</FormLabel>
                    <Input
                      type="date"
                      value={filters.from_date}
                      onChange={(e) =>
                        setFilters({ ...filters, from_date: e.target.value })
                      }
                      size="sm"
                      required
                    />
                  </FormControl>

                  <FormControl maxW="140px" isRequired>
                    <FormLabel fontSize="2xs" mb={0.5}>To Date</FormLabel>
                    <Input
                      type="date"
                      value={filters.to_date}
                      onChange={(e) =>
                        setFilters({ ...filters, to_date: e.target.value })
                      }
                      size="sm"
                      required
                    />
                  </FormControl>

                  <FormControl maxW="140px">
                    <FormLabel fontSize="2xs" mb={0.5}>Company</FormLabel>
                    <Select
                      placeholder="All Companies"
                      value={filters.company}
                      onChange={(e) =>
                        setFilters({ ...filters, company: e.target.value })
                      }
                      size="sm"
                    >
                      {companies.map((company) => (
                        <option key={company.name} value={company.name}>
                          {company.name}
                        </option>
                      ))}
                    </Select>
                  </FormControl>

                  <FormControl maxW="140px">
                    <FormLabel fontSize="2xs" mb={0.5}>Debited From</FormLabel>
                    <Select
                      placeholder="All Accounts"
                      value={filters.debited_from}
                      onChange={(e) =>
                        setFilters({ ...filters, debited_from: e.target.value })
                      }
                      size="sm"
                    >
                      {debitedFromOptions.map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </Select>
                  </FormControl>

                  <FormControl maxW="140px">
                    <FormLabel fontSize="2xs" mb={0.5}>Bill Received</FormLabel>
                    <Select
                      value={filters.bill_received === undefined ? '' : filters.bill_received === 1 ? '1' : '0'}
                      onChange={(e) =>
                        setFilters({ 
                          ...filters, 
                          bill_received: e.target.value === '' ? undefined : e.target.value === '1' ? 1 : 0 
                        })
                      }
                      size="sm"
                    >
                      <option value="">All</option>
                      <option value="1">Yes</option>
                      <option value="0">No</option>
                    </Select>
                  </FormControl>

                  <FormControl maxW="140px">
                    <FormLabel fontSize="2xs" mb={0.5}>Is Return</FormLabel>
                    <Select
                      value={filters.is_return === undefined ? '' : filters.is_return === 1 ? '1' : '0'}
                      onChange={(e) =>
                        setFilters({ 
                          ...filters, 
                          is_return: e.target.value === '' ? undefined : e.target.value === '1' ? 1 : 0 
                        })
                      }
                      size="sm"
                    >
                      <option value="">All</option>
                      <option value="1">Yes</option>
                      <option value="0">No</option>
                    </Select>
                  </FormControl>

                  <Button
                    colorScheme="teal"
                    onClick={handleGetEntries}
                    isLoading={loading}
                    size="xs"
                    height="28px"
                  >
                    Get Entries
                  </Button>
                  <Button
                    variant="ghost"
                    size="xs"
                    height="28px"
                    onClick={() => {
                      const currentMonthDates = getCurrentMonthDates();
                      setFilters({
                        status: '',
                        transfer_type: '',
                        from_date: currentMonthDates.from_date,
                        to_date: currentMonthDates.to_date,
                        company: '',
                        debited_from: '',
                        bill_received: undefined,
                        is_return: undefined,
                      });
                      setSelectedUserFilter(userId || '');
                      if (userId) {
                        const foundUser = hkmpUsers.find(u => u.user === userId);
                        if (foundUser) {
                          setUser(foundUser);
                        }
                      } else {
                        setUser(null);
                      }
                    }}
                  >
                    Clear Filters
                  </Button>
                  
                  {/* Export Menu */}
                  <Menu>
                    <MenuButton
                      as={Button}
                      leftIcon={<FiDownload />}
                      variant="outline"
                      size="xs"
                      height="28px"
                      colorScheme="teal"
                      isDisabled={entries.length === 0}
                    >
                      Export
                    </MenuButton>
                    <MenuList>
                      <MenuItem icon={<FiFileText />} onClick={exportToCSV}>
                        Export to CSV
                      </MenuItem>
                      <MenuItem icon={<FiFileText />} onClick={exportToExcel}>
                        Export to Excel
                      </MenuItem>
                    </MenuList>
                  </Menu>
                  
                  {/* Column Visibility Control */}
                  <Popover 
                    placement="bottom-start"
                    isOpen={isPopoverOpen}
                    onOpen={handlePopoverOpen}
                    onClose={handlePopoverClose}
                    closeOnBlur={true}
                    isLazy
                  >
                    <PopoverTrigger>
                      <Button
                        leftIcon={<FiSettings />}
                        variant="outline"
                        size="xs"
                        height="28px"
                        colorScheme="gray"
                      >
                        Columns
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent width="300px">
                      <PopoverArrow />
                      <PopoverCloseButton />
                      <PopoverHeader fontWeight="bold" fontSize="sm">
                        Show/Hide Columns
                      </PopoverHeader>
                      <PopoverBody>
                        <VStack align="stretch" spacing={2}>
                          <HStack justify="space-between" mb={2}>
                            <Button size="xs" onClick={showAllColumns} colorScheme="teal" variant="ghost">
                              Show All
                            </Button>
                            <Button size="xs" onClick={hideAllOptionalColumns} colorScheme="gray" variant="ghost">
                              Show Essential
                            </Button>
                          </HStack>
                          <HStack justify="space-between" mb={2}>
                            <Button 
                              size="xs" 
                              onClick={resetColumnOrder} 
                              colorScheme="blue" 
                              variant="ghost"
                              leftIcon={<FiMove />}
                              flex="1"
                            >
                              Reset Order
                            </Button>
                            <Button 
                              size="xs" 
                              onClick={resetColumnWidths} 
                              colorScheme="purple" 
                              variant="ghost"
                              flex="1"
                            >
                              Reset Widths
                            </Button>
                          </HStack>
                          <Divider mb={2} />
                          <Text fontSize="xs" color="gray.600" mb={2}>
                            Drag column headers to reorder | Drag right edge to resize
                          </Text>
                          <Divider />
                          <Checkbox
                            isChecked={visibleColumns.user}
                            onChange={() => toggleColumn('user')}
                            size="sm"
                          >
                            User
                          </Checkbox>
                          <Checkbox
                            isChecked={visibleColumns.entryId}
                            onChange={() => toggleColumn('entryId')}
                            size="sm"
                          >
                            Entry ID
                          </Checkbox>
                          <Checkbox
                            isChecked={visibleColumns.date}
                            onChange={() => toggleColumn('date')}
                            size="sm"
                          >
                            Date
                          </Checkbox>
                          <Checkbox
                            isChecked={visibleColumns.status}
                            onChange={() => toggleColumn('status')}
                            size="sm"
                          >
                            Status
                          </Checkbox>
                          <Checkbox
                            isChecked={visibleColumns.type}
                            onChange={() => toggleColumn('type')}
                            size="sm"
                          >
                            Type
                          </Checkbox>
                          <Checkbox
                            isChecked={visibleColumns.amount}
                            onChange={() => toggleColumn('amount')}
                            size="sm"
                          >
                            Amount
                          </Checkbox>
                          <Checkbox
                            isChecked={visibleColumns.company}
                            onChange={() => toggleColumn('company')}
                            size="sm"
                          >
                            Company
                          </Checkbox>
                          <Checkbox
                            isChecked={visibleColumns.debitedFrom}
                            onChange={() => toggleColumn('debitedFrom')}
                            size="sm"
                          >
                            Debited From
                          </Checkbox>
                          <Checkbox
                            isChecked={visibleColumns.beneficiary}
                            onChange={() => toggleColumn('beneficiary')}
                            size="sm"
                          >
                            Beneficiary
                          </Checkbox>
                          <Checkbox
                            isChecked={visibleColumns.accountNumber}
                            onChange={() => toggleColumn('accountNumber')}
                            size="sm"
                          >
                            Account Number
                          </Checkbox>
                          <Checkbox
                            isChecked={visibleColumns.ifscCode}
                            onChange={() => toggleColumn('ifscCode')}
                            size="sm"
                          >
                            IFSC Code
                          </Checkbox>
                          <Checkbox
                            isChecked={visibleColumns.upiId}
                            onChange={() => toggleColumn('upiId')}
                            size="sm"
                          >
                            UPI ID
                          </Checkbox>
                          <Checkbox
                            isChecked={visibleColumns.mobile}
                            onChange={() => toggleColumn('mobile')}
                            size="sm"
                          >
                            Mobile
                          </Checkbox>
                          <Checkbox
                            isChecked={visibleColumns.remarks}
                            onChange={() => toggleColumn('remarks')}
                            size="sm"
                          >
                            Remarks
                          </Checkbox>
                          <Checkbox
                            isChecked={visibleColumns.utr}
                            onChange={() => toggleColumn('utr')}
                            size="sm"
                          >
                            UTR
                          </Checkbox>
                          <Checkbox
                            isChecked={visibleColumns.bill}
                            onChange={() => toggleColumn('bill')}
                            size="sm"
                          >
                            Bill
                          </Checkbox>
                          <Checkbox
                            isChecked={visibleColumns.return}
                            onChange={() => toggleColumn('return')}
                            size="sm"
                          >
                            Return
                          </Checkbox>
                        </VStack>
                      </PopoverBody>
                    </PopoverContent>
                  </Popover>
                </HStack>
              </VStack>
            </CardBody>
          </Card>

          {/* Summary Section */}
          {entries.length > 0 && (
            <Card flexShrink={0}>
              <CardBody py={2} px={3}>
                <HStack justify="space-around" spacing={2} flexWrap="wrap">
                  <VStack align="center" spacing={0}>
                    <Text fontSize="2xs" color="gray.600">Total Entries</Text>
                    <Text fontSize="lg" fontWeight="bold" color="blue.600">{filteredEntries.length}</Text>
                  </VStack>
                  <Divider orientation="vertical" h="25px" />
                  <VStack align="center" spacing={0}>
                    <Text fontSize="2xs" color="gray.600">Total Amount</Text>
                    <Text fontSize="lg" fontWeight="bold" color="blue.600">{formatCurrency(filteredEntries.reduce((sum, entry) => sum + (entry.amount || 0), 0))}</Text>
                  </VStack>
                  <Divider orientation="vertical" h="25px" />
                  <VStack align="center" spacing={0}>
                    <Text fontSize="2xs" color="gray.600">Successful</Text>
                    <Text fontSize="lg" fontWeight="bold" color="green.600">{filteredEntries.filter((e) => e.status === 'Success').length}</Text>
                  </VStack>
                  <Divider orientation="vertical" h="25px" />
                  <VStack align="center" spacing={0}>
                    <Text fontSize="2xs" color="gray.600">Failed</Text>
                    <Text fontSize="lg" fontWeight="bold" color="red.600">{filteredEntries.filter((e) => e.status === 'Failed').length}</Text>
                  </VStack>
                </HStack>
              </CardBody>
            </Card>
          )}

          {/* Entries Table */}
          {loading ? (
            <Card flexShrink={0}>
              <CardBody>
                <Box py={10} textAlign="center">
                  <Spinner size="lg" color="teal.500" thickness="3px" />
                  <Text mt={2} color="gray.600" fontSize="sm">Loading...</Text>
                </Box>
              </CardBody>
            </Card>
          ) : entries.length === 0 ? (
            <Card flexShrink={0}>
              <CardBody>
                <Alert status="info" borderRadius="md" py={3}>
                  <AlertIcon boxSize={4} />
                  <Box>
                    <Text fontSize="sm">No entries found. Click "Get Entries" to load transactions.</Text>
                  </Box>
                </Alert>
              </CardBody>
            </Card>
          ) : (
            <Card flex="1" display="flex" flexDirection="column" minH="400px" overflow="hidden" w="100%" data-table-card>
              <CardBody p={0} flex="1" display="flex" flexDirection="column" minH="400px" overflow="hidden" w="100%">
                <Box 
                  data-table-container
                  overflowX="auto" 
                  overflowY="auto" 
                  flex="1"
                  minH="400px"
                  position="relative"
                  w="100%"
                  css={{
                    '&::-webkit-scrollbar': {
                      width: '10px',
                      height: '10px',
                    },
                    '&::-webkit-scrollbar-track': {
                      background: '#f1f1f1',
                      borderRadius: '5px',
                    },
                    '&::-webkit-scrollbar-thumb': {
                      background: '#888',
                      borderRadius: '5px',
                    },
                    '&::-webkit-scrollbar-thumb:hover': {
                      background: '#555',
                    },
                  }}
                >
                  <Table variant="simple" size="sm" w="100%" minW="max-content">
                    <Thead 
                      bg="teal.50" 
                      boxShadow="sm"
                    >
                      <Tr>
                        {columnOrder.map((columnKey) => {
                          if (!visibleColumns[columnKey] || !columnConfig[columnKey]) return null;
                          const config = columnConfig[columnKey];
                          const width = columnWidths[columnKey] || defaultColumnWidths[columnKey] || 150;
                          return (
                            <Th
                              key={columnKey}
                              py={2}
                              color="teal.700"
                              fontSize="11px"
                              width={`${width}px`}
                              minW={`${width}px`}
                              {...config.props}
                              draggable
                              onDragStart={() => handleDragStart(columnKey)}
                              onDragOver={(e) => handleDragOver(e, columnKey)}
                              onDragLeave={handleDragLeave}
                              onDrop={(e) => handleDrop(e, columnKey)}
                              cursor="move"
                              userSelect="none"
                              bg={dragOverColumn === columnKey ? 'teal.100' : draggedColumn === columnKey ? 'teal.200' : 'teal.50'}
                              transition="background-color 0.2s"
                              position="relative"
                            >
                              <HStack spacing={1} align="center" justify={config.props?.textAlign === 'center' ? 'center' : config.props?.isNumeric ? 'flex-end' : 'flex-start'}>
                                <FiMove size={10} opacity={0.5} />
                                <Text flex="1">{config.label}</Text>
                              </HStack>
                              <Box
                                position="absolute"
                                right={0}
                                top={0}
                                bottom={0}
                                width="6px"
                                cursor="col-resize"
                                bg={resizingColumn === columnKey ? 'teal.500' : 'gray.300'}
                                opacity={resizingColumn === columnKey ? 1 : 0.6}
                                _hover={{ bg: 'teal.400', opacity: 1 }}
                                onMouseDown={(e) => handleResizeStart(e, columnKey)}
                                zIndex={10}
                                transition="all 0.2s"
                                title="Drag to resize column"
                                borderRight="2px solid"
                                borderColor={resizingColumn === columnKey ? 'teal.600' : 'gray.400'}
                              />
                            </Th>
                          );
                        })}
                      </Tr>
                      {/* Filter Row */}
                      <Tr bg="gray.100">
                        {columnOrder.map((columnKey) => {
                          if (!visibleColumns[columnKey] || !columnConfig[columnKey]) return null;
                          const width = columnWidths[columnKey] || defaultColumnWidths[columnKey] || 150;
                          
                          // Render filter input only for amount, remarks, utr, and date columns
                          if (columnKey === 'amount') {
                            return (
                              <Th key={`filter-${columnKey}`} py={1} px={2} width={`${width}px`} minW={`${width}px`}>
                                <Input
                                  size="xs"
                                  placeholder="Filter amount"
                                  value={localFilters.amount}
                                  onChange={(e) => setLocalFilters({ ...localFilters, amount: e.target.value })}
                                  bg="white"
                                  fontSize="10px"
                                  height="24px"
                                />
                              </Th>
                            );
                          } else if (columnKey === 'remarks') {
                            return (
                              <Th key={`filter-${columnKey}`} py={1} px={2} width={`${width}px`} minW={`${width}px`}>
                                <Input
                                  size="xs"
                                  placeholder="Filter remarks"
                                  value={localFilters.remarks}
                                  onChange={(e) => setLocalFilters({ ...localFilters, remarks: e.target.value })}
                                  bg="white"
                                  fontSize="10px"
                                  height="24px"
                                />
                              </Th>
                            );
                          } else if (columnKey === 'utr') {
                            return (
                              <Th key={`filter-${columnKey}`} py={1} px={2} width={`${width}px`} minW={`${width}px`}>
                                <Input
                                  size="xs"
                                  placeholder="Filter UTR"
                                  value={localFilters.utr}
                                  onChange={(e) => setLocalFilters({ ...localFilters, utr: e.target.value })}
                                  bg="white"
                                  fontSize="10px"
                                  height="24px"
                                />
                              </Th>
                            );
                          } else if (columnKey === 'date') {
                            return (
                              <Th key={`filter-${columnKey}`} py={1} px={2} width={`${width}px`} minW={`${width}px`}>
                                <Input
                                  type="date"
                                  size="xs"
                                  placeholder="Filter date"
                                  value={localFilters.date}
                                  onChange={(e) => setLocalFilters({ ...localFilters, date: e.target.value })}
                                  bg="white"
                                  fontSize="10px"
                                  height="24px"
                                />
                              </Th>
                            );
                          } else {
                            return <Th key={`filter-${columnKey}`} py={1} px={2} width={`${width}px`} minW={`${width}px`} />;
                          }
                        })}
                      </Tr>
                    </Thead>
                    <Tbody>
                      {filteredEntries.map((entry) => {
                        // Determine row background color based on bill_received and is_return
                        let rowBg = 'transparent';
                        let hoverBg = 'teal.50';
                        
                        if (entry.bill_received === 1 && entry.is_return === 1) {
                          // Both checked - use a combined color (light yellow-green)
                          rowBg = 'yellow.50';
                          hoverBg = 'yellow.100';
                        } else if (entry.bill_received === 1) {
                          // Bill checked - use light green
                          rowBg = 'green.50';
                          hoverBg = 'green.100';
                        } else if (entry.is_return === 1) {
                          // Return checked - use light orange
                          rowBg = 'orange.50';
                          hoverBg = 'orange.100';
                        }
                        
                        return (
                          <Tr 
                            key={entry.name} 
                            bg={rowBg}
                            _hover={{ bg: hoverBg }}
                            transition="background-color 0.2s"
                          >
                            {columnOrder.map((columnKey) => {
                              if (!visibleColumns[columnKey] || !columnConfig[columnKey]) return null;
                              const width = columnWidths[columnKey] || defaultColumnWidths[columnKey] || 150;
                              const cell = columnConfig[columnKey].renderCell(entry);
                              // Clone the cell and add width prop
                              return (
                                <React.Fragment key={columnKey}>
                                  {React.cloneElement(cell as React.ReactElement, {
                                    width: `${width}px`,
                                    minW: `${width}px`,
                                  })}
                                </React.Fragment>
                              );
                            })}
                          </Tr>
                        );
                      })}
                    </Tbody>
                  </Table>
                </Box>
              </CardBody>
            </Card>
          )}
        </VStack>
      </Container>
    </Box>
  );
};

export default UserEntriesPage;

