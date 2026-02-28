import React, { useState, useEffect } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  VStack,
  HStack,
  FormControl,
  FormLabel,
  Select,
  Input,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Text,
  Spinner,
  Alert,
  AlertIcon,
  Box,
  Divider,
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
} from '@chakra-ui/react';
import { FiDownload, FiCheck, FiX, FiSettings } from 'react-icons/fi';
import { hkmpUserApi } from '../api/hkmpUserApi';
import { HKMPEntry, HKMPEntryFilters, HKMPUser } from '../types';

interface UserEntriesModalProps {
  isOpen: boolean;
  onClose: () => void;
  user?: HKMPUser;
}

const UserEntriesModal: React.FC<UserEntriesModalProps> = ({ isOpen, onClose, user }) => {
  const [entries, setEntries] = useState<HKMPEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [updatingEntry, setUpdatingEntry] = useState<string | null>(null);
  const [selectedUserFilter, setSelectedUserFilter] = useState<string>(user?.user || '');
  const [hkmpUsers, setHkmpUsers] = useState<HKMPUser[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [filters, setFilters] = useState<HKMPEntryFilters>({
    status: '',
    transfer_type: '',
    from_date: '',
    to_date: '',
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
  
  const toast = useToast();
  
  // Fetch HKMP users for dropdown
  useEffect(() => {
    if (isOpen) {
      fetchHkmpUsers();
    }
  }, [isOpen]);
  
  // Clear entries when user changes or modal opens
  useEffect(() => {
    if (isOpen) {
      setEntries([]);
      setFilters({
        status: '',
        transfer_type: '',
        from_date: '',
        to_date: '',
      });
      // Set initial user filter from prop if provided
      if (user?.user) {
        setSelectedUserFilter(user.user);
      } else {
        setSelectedUserFilter('');
      }
    }
  }, [user?.user, isOpen]);
  
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
  
  // Save column visibility to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('hkmp_entries_visible_columns', JSON.stringify(visibleColumns));
  }, [visibleColumns]);
  
  const toggleColumn = (columnKey: string) => {
    setVisibleColumns((prev: any) => ({
      ...prev,
      [columnKey]: !prev[columnKey],
    }));
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
    try {
      setLoading(true);
      
      // Build filters object, removing empty values
      const apiFilters: any = {};
      if (filters.status) apiFilters.status = filters.status;
      if (filters.transfer_type) apiFilters.transfer_type = filters.transfer_type;
      if (filters.from_date) apiFilters.creation = ['>=', filters.from_date];
      if (filters.to_date) {
        if (apiFilters.creation) {
          // If from_date is also set, use between
          apiFilters.creation = ['between', [filters.from_date, filters.to_date]];
        } else {
          apiFilters.creation = ['<=', filters.to_date];
        }
      }
      
      // Use selectedUserFilter - if empty/null, fetch all users' entries
      const userToFetch = selectedUserFilter || null;
      const data = await hkmpUserApi.getUserEntries(userToFetch, apiFilters);
      setEntries(data);
      
      const userLabel = userToFetch 
        ? hkmpUsers.find(u => u.user === userToFetch)?.full_name || userToFetch
        : 'All Users';
      
      toast({
        title: 'Success',
        description: `Found ${data.length} entries${userToFetch ? ` for ${userLabel}` : ' (all users)'}`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
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

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="full" scrollBehavior="inside">
      <ModalOverlay bg="blackAlpha.300" backdropFilter="blur(10px)" />
      <ModalContent 
        minH="100vh" 
        h="100vh" 
        m={0} 
        borderRadius={0}
        containerProps={{ 
          maxW: "100vw",
          maxH: "100vh" 
        }}
      >
        <ModalHeader 
          bg="teal.600" 
          color="white" 
          py={3}
          borderBottom="1px"
          borderColor="teal.700"
        >
          <HStack justify="space-between" align="center">
            <Text fontSize="lg" fontWeight="bold">
              HKMP Entries - {selectedUserFilter 
                ? (hkmpUsers.find(u => u.user === selectedUserFilter)?.full_name || selectedUserFilter)
                : 'All Users'}
            </Text>
            <Text fontSize="xs" fontWeight="normal" color="teal.50">
              Transaction history and filter entries
            </Text>
          </HStack>
        </ModalHeader>
        <ModalCloseButton color="white" />
        
        <ModalBody bg="gray.50" p={3} overflowY="auto">
          <VStack spacing={3} align="stretch" maxW="100%" mx="auto">
            {/* Filters Section */}
            <Box p={3} bg="white" borderRadius="md" shadow="sm" border="1px" borderColor="gray.200">
              <Text fontWeight="bold" fontSize="sm" mb={2} color="teal.700">
                Filters
              </Text>
              <VStack spacing={2}>
                <HStack spacing={2} width="full" flexWrap="wrap">
                  <FormControl maxW="200px">
                    <FormLabel fontSize="xs" mb={1}>User</FormLabel>
                    <Select
                      value={selectedUserFilter}
                      onChange={(e) => setSelectedUserFilter(e.target.value)}
                      size="xs"
                      isLoading={loadingUsers}
                    >
                      <option value="">All Users</option>
                      {hkmpUsers.map((u) => (
                        <option key={u.user} value={u.user}>
                          {u.full_name || u.user}
                        </option>
                      ))}
                    </Select>
                  </FormControl>

                  <FormControl maxW="150px">
                    <FormLabel fontSize="xs" mb={1}>Status</FormLabel>
                    <Select
                      placeholder="All Status"
                      value={filters.status}
                      onChange={(e) =>
                        setFilters({ ...filters, status: e.target.value })
                      }
                      size="xs"
                    >
                      <option value="Pending">Pending</option>
                      <option value="Processing">Processing</option>
                      <option value="Success">Success</option>
                      <option value="Failed">Failed</option>
                    </Select>
                  </FormControl>

                  <FormControl maxW="150px">
                    <FormLabel fontSize="xs" mb={1}>Transfer Type</FormLabel>
                    <Select
                      placeholder="All Types"
                      value={filters.transfer_type}
                      onChange={(e) =>
                        setFilters({ ...filters, transfer_type: e.target.value })
                      }
                      size="xs"
                    >
                      <option value="UPI">UPI</option>
                      <option value="IMPS">IMPS</option>
                      <option value="NEFT">NEFT</option>
                      <option value="RTGS">RTGS</option>
                    </Select>
                  </FormControl>

                  <FormControl maxW="150px">
                    <FormLabel fontSize="xs" mb={1}>From Date</FormLabel>
                    <Input
                      type="date"
                      value={filters.from_date}
                      onChange={(e) =>
                        setFilters({ ...filters, from_date: e.target.value })
                      }
                      size="xs"
                    />
                  </FormControl>

                  <FormControl maxW="150px">
                    <FormLabel fontSize="xs" mb={1}>To Date</FormLabel>
                    <Input
                      type="date"
                      value={filters.to_date}
                      onChange={(e) =>
                        setFilters({ ...filters, to_date: e.target.value })
                      }
                      size="xs"
                    />
                  </FormControl>

                  <Button
                    colorScheme="teal"
                    onClick={handleGetEntries}
                    isLoading={loading}
                    size="xs"
                    mt={4}
                  >
                    Get Entries
                  </Button>
                  <Button
                    variant="ghost"
                    size="xs"
                    mt={4}
                    onClick={() => {
                      setFilters({
                        status: '',
                        transfer_type: '',
                        from_date: '',
                        to_date: '',
                      });
                      setSelectedUserFilter(user?.user || '');
                    }}
                  >
                    Clear Filters
                  </Button>
                  
                  {/* Column Visibility Control */}
                  <Popover placement="bottom-start">
                    <PopoverTrigger>
                      <Button
                        leftIcon={<FiSettings />}
                        variant="outline"
                        size="xs"
                        mt={4}
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
            </Box>

            {/* Summary Section */}
            {entries.length > 0 && (
              <Box p={2} bg="white" borderRadius="md" shadow="sm" border="1px" borderColor="gray.200">
                <HStack justify="space-around" spacing={2} flexWrap="wrap">
                  <VStack align="center" spacing={0}>
                    <Text fontSize="xs" color="gray.600">Total Entries</Text>
                    <Text fontSize="xl" fontWeight="bold" color="blue.600">{entries.length}</Text>
                  </VStack>
                  <Divider orientation="vertical" h="30px" />
                  <VStack align="center" spacing={0}>
                    <Text fontSize="xs" color="gray.600">Total Amount</Text>
                    <Text fontSize="xl" fontWeight="bold" color="blue.600">{formatCurrency(getTotalAmount())}</Text>
                  </VStack>
                  <Divider orientation="vertical" h="30px" />
                  <VStack align="center" spacing={0}>
                    <Text fontSize="xs" color="gray.600">Successful</Text>
                    <Text fontSize="xl" fontWeight="bold" color="green.600">{entries.filter((e) => e.status === 'Success').length}</Text>
                  </VStack>
                  <Divider orientation="vertical" h="30px" />
                  <VStack align="center" spacing={0}>
                    <Text fontSize="xs" color="gray.600">Failed</Text>
                    <Text fontSize="xl" fontWeight="bold" color="red.600">{entries.filter((e) => e.status === 'Failed').length}</Text>
                  </VStack>
                </HStack>
              </Box>
            )}

            {/* Entries Table */}
            {loading ? (
              <Box py={10} textAlign="center" bg="white" borderRadius="md" shadow="sm">
                <Spinner size="lg" color="teal.500" thickness="3px" />
                <Text mt={2} color="gray.600" fontSize="sm">Loading...</Text>
              </Box>
            ) : entries.length === 0 ? (
              <Alert status="info" borderRadius="md" py={3} bg="white" border="1px" borderColor="blue.200">
                <AlertIcon boxSize={4} />
                <Box>
                  <Text fontSize="sm">No entries found. Click "Get Entries" to load transactions.</Text>
                </Box>
              </Alert>
            ) : (
              <Box bg="white" borderRadius="md" shadow="sm" border="1px" borderColor="gray.200" overflow="hidden">
                <Box overflowX="auto" maxH="calc(100vh - 300px)" overflowY="auto">
                  <Table variant="simple" size="sm">
                  <Thead bg="teal.50">
                    <Tr>
                      {visibleColumns.user && <Th py={2} color="teal.700" fontSize="11px" minW="120px">USER</Th>}
                      {visibleColumns.entryId && <Th py={2} color="teal.700" fontSize="11px">ENTRY ID</Th>}
                      {visibleColumns.date && <Th py={2} color="teal.700" fontSize="11px">DATE</Th>}
                      {visibleColumns.status && <Th py={2} color="teal.700" fontSize="11px">STATUS</Th>}
                      {visibleColumns.type && <Th py={2} color="teal.700" fontSize="11px">TYPE</Th>}
                      {visibleColumns.amount && <Th py={2} isNumeric color="teal.700" fontSize="11px">AMOUNT</Th>}
                      {visibleColumns.company && <Th py={2} color="teal.700" fontSize="11px" minW="150px">COMPANY</Th>}
                      {visibleColumns.debitedFrom && <Th py={2} color="teal.700" fontSize="11px" minW="150px">DEBITED FROM</Th>}
                      {visibleColumns.beneficiary && <Th py={2} color="teal.700" fontSize="11px" minW="150px">BENEFICIARY</Th>}
                      {visibleColumns.accountNumber && <Th py={2} color="teal.700" fontSize="11px">ACCOUNT NUMBER</Th>}
                      {visibleColumns.ifscCode && <Th py={2} color="teal.700" fontSize="11px">IFSC CODE</Th>}
                      {visibleColumns.upiId && <Th py={2} color="teal.700" fontSize="11px">UPI ID</Th>}
                      {visibleColumns.mobile && <Th py={2} color="teal.700" fontSize="11px">MOBILE</Th>}
                      {visibleColumns.remarks && <Th py={2} color="teal.700" fontSize="11px">REMARKS</Th>}
                      {visibleColumns.utr && <Th py={2} color="teal.700" fontSize="11px">UTR</Th>}
                      {visibleColumns.bill && <Th py={2} color="teal.700" fontSize="11px" textAlign="center">BILL</Th>}
                      {visibleColumns.return && <Th py={2} color="teal.700" fontSize="11px" textAlign="center">RETURN</Th>}
                    </Tr>
                  </Thead>
                  <Tbody>
                    {entries.map((entry) => (
                      <Tr key={entry.name} _hover={{ bg: 'teal.50' }}>
                        {visibleColumns.user && (
                          <Td py={2} minW="120px">
                            <Text fontSize="xs" fontWeight="medium" color="teal.600">
                              {entry.user_full_name || hkmpUsers.find(u => u.user === entry.user)?.full_name || entry.user}
                            </Text>
                          </Td>
                        )}
                        {visibleColumns.entryId && (
                          <Td py={2}>
                            <Text fontSize="xs" fontFamily="mono">{entry.name}</Text>
                          </Td>
                        )}
                        {visibleColumns.date && (
                          <Td py={2}>
                            <Text fontSize="xs">{formatDate(entry.creation)}</Text>
                          </Td>
                        )}
                        {visibleColumns.status && (
                          <Td py={2}>
                            <Badge colorScheme={getStatusColor(entry.status)} fontSize="10px" px={1.5} py={0.5}>
                              {entry.status}
                            </Badge>
                          </Td>
                        )}
                        {visibleColumns.type && (
                          <Td py={2}>
                            <Badge colorScheme="purple" variant="subtle" fontSize="10px" px={1.5} py={0.5}>
                              {entry.transfer_type}
                            </Badge>
                          </Td>
                        )}
                        {visibleColumns.amount && (
                          <Td py={2} isNumeric fontWeight="semibold" fontSize="xs">
                            {formatCurrency(entry.amount)}
                          </Td>
                        )}
                        {visibleColumns.company && (
                          <Td py={2} minW="150px" whiteSpace="normal">
                            <Text fontSize="xs" title={entry.company || '-'}>{entry.company || '-'}</Text>
                          </Td>
                        )}
                        {visibleColumns.debitedFrom && (
                          <Td py={2} minW="150px" whiteSpace="normal">
                            <Text fontSize="xs" title={entry.debited_from || '-'}>{entry.debited_from || '-'}</Text>
                          </Td>
                        )}
                        {visibleColumns.beneficiary && (
                          <Td py={2} minW="150px" whiteSpace="normal">
                            <Text fontSize="xs" title={entry.beneficiary_name || '-'}>{entry.beneficiary_name || '-'}</Text>
                          </Td>
                        )}
                        {visibleColumns.accountNumber && (
                          <Td py={2}>
                            <Text fontSize="xs" fontFamily="mono">{entry.account_number || '-'}</Text>
                          </Td>
                        )}
                        {visibleColumns.ifscCode && (
                          <Td py={2}>
                            <Text fontSize="xs" fontFamily="mono">{entry.ifsc_code || '-'}</Text>
                          </Td>
                        )}
                        {visibleColumns.upiId && (
                          <Td py={2}>
                            <Text fontSize="xs" fontFamily="mono">{entry.upi_id || '-'}</Text>
                          </Td>
                        )}
                        {visibleColumns.mobile && (
                          <Td py={2}>
                            <Text fontSize="xs">{entry.mobile_number || '-'}</Text>
                          </Td>
                        )}
                        {visibleColumns.remarks && (
                          <Td py={2}>
                            <Text fontSize="xs" noOfLines={1} maxW="200px">{entry.remarks || '-'}</Text>
                          </Td>
                        )}
                        {visibleColumns.utr && (
                          <Td py={2}>
                            <Text fontSize="xs" fontFamily="mono">{entry.utr || '-'}</Text>
                          </Td>
                        )}
                        {visibleColumns.bill && (
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
                        )}
                        {visibleColumns.return && (
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
                        )}
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
                </Box>
              </Box>
            )}
          </VStack>
        </ModalBody>

        <ModalFooter 
          bg="white" 
          borderTop="1px" 
          borderColor="gray.200" 
          py={2}
        >
          <Button 
            colorScheme="teal" 
            size="sm"
            onClick={onClose}
            px={6}
          >
            Close
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default UserEntriesModal;

