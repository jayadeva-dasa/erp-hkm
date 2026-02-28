import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
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
  IconButton,
  useToast,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  FormControl,
  FormLabel,
  Input,
  Select,
  VStack,
  HStack,
  Badge,
  Spinner,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  useColorModeValue,
  Card,
  CardBody,
  Flex,
  InputGroup,
  InputLeftElement,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Divider,
  SimpleGrid,
  Checkbox,
  CheckboxGroup,
  Wrap,
  WrapItem,
  InputRightElement,
  Icon,
} from '@chakra-ui/react';
import { FiArrowLeft, FiEdit2, FiTrash2, FiPlus, FiSearch, FiUser, FiFileText, FiBarChart2, FiEye, FiRefreshCw, FiCopy, FiChevronUp, FiChevronDown } from 'react-icons/fi';
import { hkmpUserApi } from '../api/hkmpUserApi';
import { HKMPUser, HKMPUserFormData } from '../types';
import UserAnalyticsDashboard from '../components/UserAnalyticsDashboard';
import SearchableUserSelect from '../components/SearchableUserSelect';

// Define sort directions
type SortDirection = 'asc' | 'desc' | null;

// Define sort field type
type SortField = keyof HKMPUser | null;

const HKMPayUserManagementPage: React.FC = () => {
  const navigate = useNavigate();
  const [users, setUsers] = useState<HKMPUser[]>([]);
  const [filteredUsers, setFilteredUsers] = useState<HKMPUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [departments, setDepartments] = useState<Array<{ name: string }>>([]);
  const [companies, setCompanies] = useState<Array<{ name: string }>>([]);
  const [selectedCompanies, setSelectedCompanies] = useState<string[]>([]);
  const [selectedUser, setSelectedUser] = useState<HKMPUser | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formResetKey, setFormResetKey] = useState(0);
  const [formData, setFormData] = useState<HKMPUserFormData>({
    user: '',
    full_name: '',
    department: '',
    per_transaction_limit: 20000,
    advance_limit: 20000,
    daily_limit: 20000,
    active_company: [],
    enabled: 1,
  });

  // Sorting state
  const [sortField, setSortField] = useState<SortField>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);

  const toast = useToast();
  const { isOpen, onOpen, onClose } = useDisclosure();
  const {
    isOpen: isDeleteOpen,
    onOpen: onDeleteOpen,
    onClose: onDeleteClose,
  } = useDisclosure();
  const [selectedUserForAnalytics, setSelectedUserForAnalytics] = useState<HKMPUser | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [secretPin, setSecretPin] = useState<string>('');
  const [pinAction, setPinAction] = useState<'show' | 'reset'>('show');
  const {
    isOpen: isPinModalOpen,
    onOpen: onPinModalOpen,
    onClose: onPinModalClose,
  } = useDisclosure();
  const [customPin, setCustomPin] = useState<string>('');
  const {
    isOpen: isCustomPinModalOpen,
    onOpen: onCustomPinModalOpen,
    onClose: onCustomPinModalClose,
  } = useDisclosure();
  const [bankAccountSpending, setBankAccountSpending] = useState<any[]>([]);

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  // Fetch users on mount
  useEffect(() => {
    fetchUsers();
    fetchDepartments();
    fetchAllCompanies();
    fetchBankAccountSpending();
  }, []);

  // Filter users based on search term
  useEffect(() => {
    let result = [...users];
    
    if (searchTerm) {
      result = result.filter(
        (user) =>
          user.user?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          user.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          user.department?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    // Apply sorting if a sort field is selected
    if (sortField && sortDirection) {
      result.sort((a, b) => {
        const aValue = a[sortField];
        const bValue = b[sortField];
        
        // Handle undefined/null values
        if (aValue == null && bValue == null) return 0;
        if (aValue == null) return sortDirection === 'asc' ? -1 : 1;
        if (bValue == null) return sortDirection === 'asc' ? 1 : -1;
        
        // Handle different data types
        if (typeof aValue === 'string' && typeof bValue === 'string') {
          const comparison = aValue.localeCompare(bValue);
          return sortDirection === 'asc' ? comparison : -comparison;
        }
        
        if (typeof aValue === 'number' && typeof bValue === 'number') {
          const comparison = aValue - bValue;
          return sortDirection === 'asc' ? comparison : -comparison;
        }
        
        // Convert to string for other types
        const comparison = String(aValue).localeCompare(String(bValue));
        return sortDirection === 'asc' ? comparison : -comparison;
      });
    }
    
    setFilteredUsers(result);
  }, [searchTerm, users, sortField, sortDirection]);

  // Handle sorting
  const handleSort = (field: SortField) => {
    if (field === sortField) {
      // Toggle direction if clicking the same field
      if (sortDirection === 'asc') {
        setSortDirection('desc');
      } else if (sortDirection === 'desc') {
        setSortDirection(null);
        setSortField(null);
      } else {
        setSortDirection('asc');
      }
    } else {
      // Set new field and default to ascending
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // Get sort indicator for a column
  const getSortIndicator = (field: SortField) => {
    if (field !== sortField || sortDirection === null) {
      return null;
    }
    return sortDirection === 'asc' ? <FiChevronUp /> : <FiChevronDown />;
  };

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const data = await hkmpUserApi.getAllUsers();
      setUsers(data);
      setFilteredUsers(data);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to fetch users',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchDepartments = async () => {
    try {
      const data = await hkmpUserApi.getAllDepartments();
      setDepartments(data);
    } catch (error) {
      console.error('Error fetching departments:', error);
    }
  };

  const fetchAllCompanies = async () => {
    try {
      const data = await hkmpUserApi.getAllCompanies();
      setCompanies(data);
    } catch (error) {
      console.error('Error fetching companies:', error);
    }
  };

  const fetchBankAccountSpending = async () => {
    try {
      const data = await hkmpUserApi.getTotalSpendBankAccountWise();
      setBankAccountSpending(data);
    } catch (error) {
      console.error('Error fetching bank account spending:', error);
    }
  };

  const handleCreateNew = async () => {
    setSelectedUser(null);
    setFormData({
      user: '',
      full_name: '',
      department: '',
      per_transaction_limit: 20000,
      advance_limit: 20000,
      daily_limit: 20000,
      active_company: [],
      enabled: 1,
    });
    setSelectedCompanies([]);
    onOpen();
  };

  const handleModalClose = () => {
    // Reset form data when modal closes
    setSelectedUser(null);
    setFormData({
      user: '',
      full_name: '',
      department: '',
      per_transaction_limit: 20000,
      advance_limit: 20000,
      daily_limit: 20000,
      active_company: [],
      enabled: 1,
    });
    setSelectedCompanies([]);
    // Increment key to force SearchableUserSelect to remount and clear its internal state
    setFormResetKey(prev => prev + 1);
    onClose();
  };

  const handleEdit = async (user: HKMPUser) => {
    setSelectedUser(user);
    setFormData({
      user: user.user,
      full_name: user.full_name || '',
      department: user.department || '',
      per_transaction_limit: user.per_transaction_limit,
      advance_limit: user.advance_limit,
      daily_limit: user.daily_limit,
      active_company: user.active_company || [],
      enabled: user.enabled || 1,
    });
    
    // Fetch existing companies for the user
    try {
      const userCompanies = await hkmpUserApi.getUserCompanies(user.user);
      const companyNames = userCompanies.map(c => c.company);
      setSelectedCompanies(companyNames);
    } catch (error) {
      console.error('Error fetching user companies:', error);
      setSelectedCompanies([]);
    }
    
    onOpen();
  };

  const handleDelete = (user: HKMPUser) => {
    setSelectedUser(user);
    onDeleteOpen();
  };

  const handleViewEntries = (user: HKMPUser) => {
    navigate(`/hkm-pay-user-management/entries/${user.user}`);
  };

  const handleViewAnalytics = (user: HKMPUser) => {
    setSelectedUserForAnalytics(user);
    setActiveTab(1); // Switch to analytics tab
  };

  const handleSubmit = async () => {
    if (!formData.user) {
      toast({
        title: 'Validation Error',
        description: 'Please select a user',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    if (formData.per_transaction_limit <= 0 || formData.advance_limit <= 0 || formData.daily_limit <= 0) {
      toast({
        title: 'Validation Error',
        description: 'All limit fields must be greater than 0',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    if (!formData.full_name || !formData.department) {
      toast({
        title: 'Validation Error',
        description: 'Please fill in all required fields',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    try {
      setIsSubmitting(true);
      
      // Prepare active_company data from selected companies
      const activeCompanyData = selectedCompanies.map(company => ({ company }));
      
      if (selectedUser) {
        // Update existing user
        await hkmpUserApi.updateUser(selectedUser.name, {
          full_name: formData.full_name,
          department: formData.department,
          per_transaction_limit: formData.per_transaction_limit,
          advance_limit: formData.advance_limit,
          daily_limit: formData.daily_limit,
          active_company: activeCompanyData,
          enabled: formData.enabled,
        });
        toast({
          title: 'Success',
          description: 'HKMP User updated successfully',
          status: 'success',
          duration: 3000,
          isClosable: true,
        });
      } else {
        // Create new user
        const userData = {
          ...formData,
          active_company: activeCompanyData,
        };
        await hkmpUserApi.createUser(userData);
        toast({
          title: 'Success',
          description: 'HKMP User created successfully',
          status: 'success',
          duration: 3000,
          isClosable: true,
        });
      }
      handleModalClose();
      fetchUsers();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to save user',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const confirmDelete = async () => {
    if (!selectedUser) return;

    try {
      setIsSubmitting(true);
      await hkmpUserApi.deleteUser(selectedUser.name);
      toast({
        title: 'Success',
        description: 'HKMP User deleted successfully',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      onDeleteClose();
      fetchUsers();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete user',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleShowPin = async (user: HKMPUser) => {
    try {
      setIsSubmitting(true);
      const pin = await hkmpUserApi.showSecretPin(user.name);
      setSecretPin(pin);
      setPinAction('show');
      setSelectedUser(user);
      onPinModalOpen();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to show secret PIN',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResetPin = async (user: HKMPUser) => {
    try {
      setIsSubmitting(true);
      const pin = await hkmpUserApi.generateSecretPin(user.name);
      setSecretPin(pin);
      setPinAction('reset');
      setSelectedUser(user);
      onPinModalOpen();
      fetchUsers();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to generate secret PIN',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResetPinWithCustom = async (user: HKMPUser) => {
    try {
      setIsSubmitting(true);
      // Call the API with the custom PIN
      const pin = await hkmpUserApi.generateSecretPin(user.name, customPin);
      setSecretPin(pin);
      setPinAction('reset');
      setSelectedUser(user);
      onPinModalOpen();
      fetchUsers();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to generate secret PIN',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCopyPin = () => {
    navigator.clipboard.writeText(secretPin);
    toast({
      title: 'Copied!',
      description: 'PIN copied to clipboard',
      status: 'success',
      duration: 2000,
      isClosable: true,
    });
  };

  const handleOpenCustomPinModal = (user: HKMPUser) => {
    setSelectedUser(user);
    setCustomPin(''); // Reset custom PIN when opening modal
    onCustomPinModalOpen();
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <Box minH="100vh" bg="gray.50">
      {/* Header */}
      <Box bg={bgColor} shadow="sm" mb={4}>
        <Container maxW="container.xl" py={3}>
          <HStack spacing={3} mb={0}>
            <IconButton
              as={Link}
              to="/"
              icon={<FiArrowLeft />}
              aria-label="Back to dashboard"
              variant="ghost"
              size="md"
            />
            <Box flex="1">
              <Heading size="lg" color="teal.600">
                HKM Pay User Management
              </Heading>
              <Text color="gray.600" mt={0} fontSize="sm">
                Manage HKMP Users - View, Create, Edit, and Delete
              </Text>
            </Box>
            <Button
              leftIcon={<FiPlus />}
              colorScheme="teal"
              onClick={handleCreateNew}
              size="md"
            >
              Create New User
            </Button>
          </HStack>
        </Container>
      </Box>

      {/* Main Content */}
      <Container maxW="container.xl" pb={8}>
        <Tabs index={activeTab} onChange={setActiveTab} colorScheme="teal" size="sm">
          <TabList>
            <Tab py={2}>
              <HStack spacing={2}>
                <Box as={FiUser} boxSize={4} />
                <Text fontSize="sm">User Management</Text>
              </HStack>
            </Tab>
            <Tab py={2} isDisabled={!selectedUserForAnalytics}>
              <HStack spacing={2}>
                <Box as={FiBarChart2} boxSize={4} />
                <Text fontSize="sm">
                  Analytics
                  {selectedUserForAnalytics && (
                    <Badge ml={2} colorScheme="teal" fontSize="xs">
                      {selectedUserForAnalytics.user}
                    </Badge>
                  )}
                </Text>
              </HStack>
            </Tab>
          </TabList>

          <TabPanels>
            {/* Tab 1: User Management */}
            <TabPanel p={0} pt={3}>
              <Card>
                <CardBody py={3}>
                  {/* Bank Account Spending Summary - Compact Layout */}
                  {bankAccountSpending.length > 0 && (
                    <Card mb={4}>
                      <CardBody py={2}>
                        <Heading size="sm" mb={2} color="teal.600">
                          Current Month Spending by Bank Account
                        </Heading>
                        
                        {/* Group data by debited_from */}
                        {(() => {
                          const groupedData = bankAccountSpending.reduce((acc: any, item: any) => {
                            const key = item.debited_from || 'Unknown';
                            if (!acc[key]) {
                              acc[key] = [];
                            }
                            acc[key].push(item);
                            return acc;
                          }, {});
                          
                          return Object.entries(groupedData).map(([debitedFrom, companies]: [string, any]) => (
                            <Box key={debitedFrom} mb={3}>
                              {/* Debited From Title */}
                              <Box 
                                bg="teal.50" 
                                p={2} 
                                borderRadius="md" 
                                mb={2}
                                borderLeftWidth="3px"
                                borderLeftColor="teal.500"
                              >
                                <Heading size="xs" color="teal.700">
                                  {debitedFrom}
                                </Heading>
                              </Box>
                              
                              {/* Company Cards */}
                              <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={3}>
                                {companies.map((item: any, idx: number) => (
                                  <Card 
                                    key={idx} 
                                    boxShadow="sm" 
                                    borderWidth="1px" 
                                    borderColor="gray.200"
                                    _hover={{ boxShadow: "md" }}
                                    transition="all 0.2s"
                                  >
                                    <CardBody p={3}>
                                      <VStack align="stretch" spacing={2}>
                                        <Box>
                                          <Text fontSize="10px" color="gray.500" fontWeight="medium" mb={0.5}>
                                            COMPANY
                                          </Text>
                                          <Text fontSize="xs" fontWeight="semibold" color="gray.700" noOfLines={1}>
                                            {item.company || 'Unknown'}
                                          </Text>
                                        </Box>
                                        
                                        <Divider />
                                        
                                        <Box>
                                          <Text fontSize="10px" color="gray.500" fontWeight="medium" mb={0.5}>
                                            CURRENT MONTH SPEND
                                          </Text>
                                          <Text fontSize="sm" fontWeight="bold" color="teal.600">
                                            {formatCurrency(item.current_month_spending ? Number(item.current_month_spending) : 0)}
                                          </Text>
                                        </Box>
                                        
                                        <Box>
                                          <Text fontSize="10px" color="gray.500" fontWeight="medium" mb={0.5}>
                                            AVG DAILY SPEND
                                          </Text>
                                          <Text fontSize="sm" fontWeight="bold" color="purple.600">
                                            {formatCurrency(item.average_daily_spending ? Number(item.average_daily_spending) : 0)}
                                          </Text>
                                        </Box>
                                        
                                        <Box>
                                          <Text fontSize="10px" color="gray.500" fontWeight="medium" mb={0.5}>
                                            TOTAL SPEND
                                          </Text>
                                          <Text fontSize="sm" fontWeight="bold" color="blue.600">
                                            {formatCurrency(item.total_spending ? Number(item.total_spending) : 0)}
                                          </Text>
                                        </Box>
                                      </VStack>
                                    </CardBody>
                                  </Card>
                                ))}
                              </SimpleGrid>
                            </Box>
                          ));
                        })()}
                      </CardBody>
                    </Card>
                  )}

                  {/* Search Bar */}
                  <Flex mb={3} gap={3} align="center">
                    <InputGroup maxW="400px" size="sm">
                      <InputLeftElement pointerEvents="none" h="32px">
                        <FiSearch color="gray.300" size={14} />
                      </InputLeftElement>
                      <Input
                        placeholder="Search by user, name, or department..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        fontSize="sm"
                      />
                    </InputGroup>
                    <Text color="gray.600" fontSize="xs">
                      Total Users: <Badge colorScheme="teal" fontSize="xs">{filteredUsers.length}</Badge>
                    </Text>
                  </Flex>

                  {/* Loading State */}
                  {loading ? (
                    <Flex justify="center" align="center" py={10}>
                      <VStack spacing={2}>
                        <Spinner size="lg" color="teal.500" thickness="3px" />
                        <Text color="gray.600" fontSize="sm">Loading users...</Text>
                      </VStack>
                    </Flex>
                  ) : filteredUsers.length === 0 ? (
                    <Alert
                      status="info"
                      variant="subtle"
                      flexDirection="column"
                      alignItems="center"
                      justifyContent="center"
                      textAlign="center"
                      height="150px"
                      borderRadius="md"
                    >
                      <AlertIcon boxSize="32px" mr={0} />
                      <AlertTitle mt={3} mb={1} fontSize="md">
                        No users found
                      </AlertTitle>
                      <AlertDescription maxWidth="sm" fontSize="sm">
                        {searchTerm
                          ? 'No users match your search criteria. Try a different search term.'
                          : 'No HKMP Users exist yet. Click "Create New User" to add one.'}
                      </AlertDescription>
                    </Alert>
                  ) : (
                    /* Users Table */
                    <Box overflowX="auto">
                      <Table variant="simple" size="sm">
                        <Thead bg="gray.50">
                          <Tr>
                            <Th py={2} fontSize="xs" cursor="pointer" onClick={() => handleSort('full_name')}>
                              <HStack spacing={1}>
                                <Text>Full Name</Text>
                                <Icon as={() => getSortIndicator('full_name')} boxSize={3} />
                              </HStack>
                            </Th>
                            <Th py={2} isNumeric fontSize="xs" cursor="pointer" onClick={() => handleSort('advance_limit')}>
                              <HStack spacing={1} justifyContent="flex-end">
                                <Text>Advance Limit</Text>
                                <Icon as={() => getSortIndicator('advance_limit')} boxSize={3} />
                              </HStack>
                            </Th>
                            <Th py={2} isNumeric fontSize="xs" cursor="pointer" onClick={() => handleSort('available_amt')}>
                              <HStack spacing={1} justifyContent="flex-end">
                                <Text>Available Amount</Text>
                                <Icon as={() => getSortIndicator('available_amt')} boxSize={3} />
                              </HStack>
                            </Th>
                            <Th py={2} isNumeric fontSize="xs" cursor="pointer" onClick={() => handleSort('current_day_spending')}>
                              <HStack spacing={1} justifyContent="flex-end">
                                <Text>Current Day Spending</Text>
                                <Icon as={() => getSortIndicator('current_day_spending')} boxSize={3} />
                              </HStack>
                            </Th>
                            <Th py={2} isNumeric fontSize="xs" cursor="pointer" onClick={() => handleSort('current_month_spending')}>
                              <HStack spacing={1} justifyContent="flex-end">
                                <Text>Current Month Spending</Text>
                                <Icon as={() => getSortIndicator('current_month_spending')} boxSize={3} />
                              </HStack>
                            </Th>
                            <Th py={2} isNumeric fontSize="xs" cursor="pointer" onClick={() => handleSort('total_spending')}>
                              <HStack spacing={1} justifyContent="flex-end">
                                <Text>Total Spending</Text>
                                <Icon as={() => getSortIndicator('total_spending')} boxSize={3} />
                              </HStack>
                            </Th>
                            <Th py={2} fontSize="xs" cursor="pointer" onClick={() => handleSort('enabled')}>
                              <HStack spacing={1}>
                                <Text>Status</Text>
                                <Icon as={() => getSortIndicator('enabled')} boxSize={3} />
                              </HStack>
                            </Th>
                            <Th py={2} fontSize="xs">Actions</Th>
                          </Tr>
                        </Thead>
                        <Tbody>
                          {filteredUsers.map((user) => (
                            <Tr key={user.name} _hover={{ bg: 'gray.50' }}>

                              <Td py={2} fontSize="sm">
                                <Text
                                  as="button"
                                  color="teal.600"
                                  fontWeight="medium"
                                  _hover={{ textDecoration: 'underline', color: 'teal.700' }}
                                  cursor="pointer"
                                  onClick={() => handleViewEntries(user)}
                                  title="Click to view all entries"
                                >
                                  {user.full_name || '-'}
                                </Text>
                              </Td>

                              <Td py={2} isNumeric fontWeight="medium" fontSize="sm">
                                {formatCurrency(user.advance_limit)}
                              </Td>
                              <Td py={2} isNumeric>
                                <Badge
                                  colorScheme={
                                    (user.available_amt || 0) > 0 ? 'green' : 'red'
                                  }
                                  fontSize="xs"
                                  px={2}
                                  py={0.5}
                                >
                                  {formatCurrency(user.available_amt || 0)}
                                </Badge>
                              </Td>
                              <Td py={2} isNumeric fontWeight="medium" fontSize="sm">
                                <Badge
                                  colorScheme="orange"
                                  fontSize="xs"
                                  px={2}
                                  py={0.5}
                                >
                                  {formatCurrency(user.current_day_spending || 0)}
                                </Badge>
                              </Td>
                              <Td py={2} isNumeric fontWeight="medium" fontSize="sm">
                                <Badge
                                  colorScheme="blue"
                                  fontSize="xs"
                                  px={2}
                                  py={0.5}
                                >
                                  {formatCurrency(user.current_month_spending || 0)}
                                </Badge>
                              </Td>
                              <Td py={2} isNumeric fontWeight="medium" fontSize="sm">
                                <Badge
                                  colorScheme="teal"
                                  fontSize="xs"
                                  px={2}
                                  py={0.5}
                                >
                                  {formatCurrency(user.total_spending || 0)}
                                </Badge>
                              </Td>
                              <Td py={2}>
                                <Badge
                                  colorScheme={user.enabled ? 'green' : 'red'}
                                  fontSize="xs"
                                  px={2}
                                  py={0.5}
                                >
                                  {user.enabled ? 'Enabled' : 'Disabled'}
                                </Badge>
                              </Td>
                              <Td py={2}>
                                <HStack spacing={1}>
                                  <IconButton
                                    icon={<FiBarChart2 />}
                                    aria-label="View analytics"
                                    size="xs"
                                    colorScheme="purple"
                                    variant="ghost"
                                    onClick={() => handleViewAnalytics(user)}
                                    title="View Analytics"
                                  />
                                  <IconButton
                                    icon={<FiEye />}
                                    aria-label="Show PIN"
                                    size="xs"
                                    colorScheme="cyan"
                                    variant="ghost"
                                    onClick={() => handleShowPin(user)}
                                    title="Show Secret PIN"
                                  />
                                  <IconButton
                                    icon={<FiRefreshCw />}
                                    aria-label="Reset PIN"
                                    size="xs"
                                    colorScheme="orange"
                                    variant="ghost"
                                    onClick={() => handleOpenCustomPinModal(user)}
                                    title="Reset Secret PIN"
                                  />
                                  <IconButton
                                    icon={<FiEdit2 />}
                                    aria-label="Edit user"
                                    size="xs"
                                    colorScheme="blue"
                                    variant="ghost"
                                    onClick={() => handleEdit(user)}
                                    title="Edit User"
                                  />
                                  <IconButton
                                    icon={<FiTrash2 />}
                                    aria-label="Delete user"
                                    size="xs"
                                    colorScheme="red"
                                    variant="ghost"
                                    onClick={() => handleDelete(user)}
                                    title="Delete User"
                                  />
                                </HStack>
                              </Td>
                            </Tr>
                          ))}
                        </Tbody>
                      </Table>
                    </Box>
                  )}
                </CardBody>
              </Card>
            </TabPanel>

            {/* Tab 2: Analytics Dashboard */}
            <TabPanel p={0} pt={3}>
              {selectedUserForAnalytics ? (
                <Box>
                  <Card mb={3}>
                    <CardBody py={2}>
                      <HStack justify="space-between">
                        <VStack align="start" spacing={0}>
                          <Text fontSize="xs" color="gray.600">
                            Analytics for
                          </Text>
                          <Heading size="sm" color="teal.600">
                            {selectedUserForAnalytics.full_name || selectedUserForAnalytics.user}
                          </Heading>
                        </VStack>
                        <Button
                          size="xs"
                          variant="outline"
                          onClick={() => setActiveTab(0)}
                        >
                          Back to List
                        </Button>
                      </HStack>
                    </CardBody>
                  </Card>
                  <UserAnalyticsDashboard user={selectedUserForAnalytics} />
                </Box>
              ) : (
                <Alert status="info" py={3}>
                  <AlertIcon boxSize={4} />
                  <Text fontSize="sm">Please select a user from the User Management tab to view analytics.</Text>
                </Alert>
              )}
            </TabPanel>
          </TabPanels>
        </Tabs>
      </Container>

      {/* Create/Edit Modal */}
      <Modal isOpen={isOpen} onClose={handleModalClose} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            {selectedUser ? 'Edit HKMP User' : 'Create New HKMP User'}
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4}>
              <SearchableUserSelect
                key={`user-select-${formResetKey}`}
                value={formData.user}
                onChange={(value, user) => setFormData({
                  ...formData,
                  user: value,
                  full_name: user?.full_name || ''
                })}
                isDisabled={!!selectedUser}
                isRequired={true}
                label="User"
                placeholder="Search and select user..."
              />

              <FormControl>
                <FormLabel>Full Name</FormLabel>
                <Input
                  placeholder="Enter full name"
                  value={formData.full_name}
                  onChange={(e) =>
                    setFormData({ ...formData, full_name: e.target.value })
                  }
                />
              </FormControl>

              <FormControl>
                <FormLabel>Department</FormLabel>
                <Select
                  placeholder="Select department"
                  value={formData.department}
                  onChange={(e) =>
                    setFormData({ ...formData, department: e.target.value })
                  }
                >
                  {departments.map((department) => (
                    <option key={department.name} value={department.name}>
                      {department.name}
                    </option>
                  ))}
                </Select>
              </FormControl>

              <FormControl>
                <FormLabel>Active Companies</FormLabel>
                <Box
                  border="1px"
                  borderColor={borderColor}
                  borderRadius="md"
                  p={3}
                  maxH="200px"
                  overflowY="auto"
                >
                  <CheckboxGroup
                    value={selectedCompanies}
                    onChange={(values) => {
                      const companyNames = values as string[];
                      setSelectedCompanies(companyNames);
                    }}
                  >
                    <Wrap spacing={3}>
                      {companies.map((company) => (
                        <WrapItem key={company.name}>
                          <Checkbox value={company.name}>
                            {company.name}
                          </Checkbox>
                        </WrapItem>
                      ))}
                    </Wrap>
                  </CheckboxGroup>
                  {companies.length === 0 && (
                    <Text fontSize="sm" color="gray.500">
                      No companies available
                    </Text>
                  )}
                </Box>
                <Text fontSize="xs" color="gray.500" mt={1}>
                  Select one or more companies for this user
                </Text>
              </FormControl>
              
              <FormControl>
                <FormLabel>Status</FormLabel>
                <Checkbox
                  isChecked={formData.enabled === 1}
                  onChange={(e) =>
                    setFormData({ ...formData, enabled: e.target.checked ? 1 : 0 })
                  }
                >
                  Enabled
                </Checkbox>
                <Text fontSize="xs" color="gray.500" mt={1}>
                  Enable or disable this user's access to HKM Pay
                </Text>
              </FormControl>

              <FormControl isRequired>
                <FormLabel>Per Transaction Limit (₹)</FormLabel>
                <Input
                  type="number"
                  placeholder="Enter per transaction limit"
                  value={formData.per_transaction_limit || ''}
                  onChange={(e) => {
                    const value = e.target.value;
                    // Allow empty string for clearing, convert to 0
                    const numValue = value === '' ? 0 : parseFloat(value);
                    setFormData({
                      ...formData,
                      per_transaction_limit: isNaN(numValue) ? 0 : numValue,
                    });
                  }}
                />
              </FormControl>

              <FormControl isRequired>
                <FormLabel>Daily Limit (₹)</FormLabel>
                <Input
                  type="number"
                  placeholder="Enter daily limit"
                  value={formData.daily_limit || ''}
                  onChange={(e) => {
                    const value = e.target.value;
                    const numValue = value === '' ? 0 : parseFloat(value);
                    setFormData({
                      ...formData,
                      daily_limit: isNaN(numValue) ? 0 : numValue,
                    });
                  }}
                />
              </FormControl>

              <FormControl isRequired>
                <FormLabel>Advance Limit (₹)</FormLabel>
                <Input
                  type="number"
                  placeholder="Enter advance limit"
                  value={formData.advance_limit || ''}
                  onChange={(e) => {
                    const value = e.target.value;
                    const numValue = value === '' ? 0 : parseFloat(value);
                    setFormData({
                      ...formData,
                      advance_limit: isNaN(numValue) ? 0 : numValue,
                    });
                  }}
                />
              </FormControl>
            </VStack>
          </ModalBody>

          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button
              colorScheme="teal"
              onClick={handleSubmit}
              isLoading={isSubmitting}
            >
              {selectedUser ? 'Update' : 'Create'}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal isOpen={isDeleteOpen} onClose={onDeleteClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Confirm Delete</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Text>
              Are you sure you want to delete user{' '}
              <strong>{selectedUser?.user}</strong>? This action cannot be
              undone.
            </Text>
          </ModalBody>

          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onDeleteClose}>
              Cancel
            </Button>
            <Button
              colorScheme="red"
              onClick={confirmDelete}
              isLoading={isSubmitting}
            >
              Delete
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* PIN Display Modal */}
      <Modal isOpen={isPinModalOpen} onClose={onPinModalClose} size="md" isCentered>
        <ModalOverlay backdropFilter="blur(4px)" />
        <ModalContent>
          <ModalHeader>
            <HStack spacing={2}>
              <Box as={pinAction === 'show' ? FiEye : FiRefreshCw} color="teal.500" />
              <Text>
                {pinAction === 'show' ? 'Current Secret PIN' : 'New Secret PIN Generated'}
              </Text>
            </HStack>
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4} align="stretch">
              {selectedUser && (
                <Box bg="gray.50" p={3} borderRadius="md">
                  <Text fontSize="sm" color="gray.600" mb={1}>
                    User
                  </Text>
                  <Text fontWeight="bold" color="teal.600">
                    {selectedUser.full_name || selectedUser.user}
                  </Text>
                  <Text fontSize="xs" color="gray.500">
                    {selectedUser.user}
                  </Text>
                </Box>
              )}

              <Box
                bg={pinAction === 'show' ? 'blue.50' : 'green.50'}
                p={6}
                borderRadius="lg"
                textAlign="center"
                border="2px"
                borderColor={pinAction === 'show' ? 'blue.200' : 'green.200'}
              >
                <Text fontSize="xs" color="gray.600" mb={2} textTransform="uppercase" fontWeight="medium">
                  Secret PIN
                </Text>
                <Text
                  fontSize="4xl"
                  fontWeight="bold"
                  color={pinAction === 'show' ? 'blue.600' : 'green.600'}
                  letterSpacing="widest"
                  fontFamily="monospace"
                >
                  {secretPin}
                </Text>
              </Box>

              {pinAction === 'reset' && (
                <Alert status="warning" borderRadius="md" fontSize="sm">
                  <AlertIcon boxSize={4} />
                  <Box>
                    <AlertTitle fontSize="sm" mb={1}>PIN has been reset!</AlertTitle>
                    <AlertDescription fontSize="xs">
                      Make sure to save this PIN securely. The user will need this PIN to access the system.
                    </AlertDescription>
                  </Box>
                </Alert>
              )}

              {pinAction === 'show' && (
                <Alert status="info" borderRadius="md" fontSize="sm">
                  <AlertIcon boxSize={4} />
                  <AlertDescription fontSize="xs">
                    Keep this PIN confidential. Do not share it over unsecured channels.
                  </AlertDescription>
                </Alert>
              )}
            </VStack>
          </ModalBody>

          <ModalFooter>
            <Button
              leftIcon={<FiCopy />}
              variant="outline"
              colorScheme="teal"
              mr={3}
              onClick={handleCopyPin}
              size="sm"
            >
              Copy PIN
            </Button>
            <Button onClick={onPinModalClose} colorScheme="teal" size="sm">
              Close
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
      
      {/* Custom PIN Modal */}
      <Modal isOpen={isCustomPinModalOpen} onClose={onCustomPinModalClose} size="md" isCentered>
        <ModalOverlay backdropFilter="blur(4px)" />
        <ModalContent>
          <ModalHeader>
            <HStack spacing={2}>
              <Box as={FiRefreshCw} color="orange.500" />
              <Text>Reset Secret PIN</Text>
            </HStack>
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4} align="stretch">
              {selectedUser && (
                <Box bg="gray.50" p={3} borderRadius="md">
                  <Text fontSize="sm" color="gray.600" mb={1}>
                    User
                  </Text>
                  <Text fontWeight="bold" color="teal.600">
                    {selectedUser.full_name || selectedUser.user}
                  </Text>
                  <Text fontSize="xs" color="gray.500">
                    {selectedUser.user}
                  </Text>
                </Box>
              )}
              
              <Alert status="warning" borderRadius="md" fontSize="sm">
                <AlertIcon boxSize={4} />
                <Box>
                  <AlertTitle fontSize="sm" mb={1}>Security Notice</AlertTitle>
                  <AlertDescription fontSize="xs">
                    Please ensure the PIN is secure and only shared with the intended user through secure channels.
                  </AlertDescription>
                </Box>
              </Alert>
              
              <FormControl>
                <FormLabel>Custom 4-Digit PIN</FormLabel>
                <InputGroup>
                  <Input
                    type="password"
                    placeholder="Enter 4-digit PIN"
                    value={customPin}
                    onChange={(e) => {
                      const value = e.target.value.replace(/\D/g, '').slice(0, 4);
                      setCustomPin(value);
                    }}
                    maxLength={4}
                  />
                  <InputRightElement width="4.5rem">
                    <Button 
                      h="1.75rem" 
                      size="sm"
                      onClick={() => setCustomPin('')}
                    >
                      Clear
                    </Button>
                  </InputRightElement>
                </InputGroup>
                <Text fontSize="xs" color="gray.500" mt={1}>
                  Enter a custom 4-digit PIN or leave blank for auto-generation
                </Text>
              </FormControl>
            </VStack>
          </ModalBody>

          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onCustomPinModalClose}>
              Cancel
            </Button>
            <Button
              colorScheme="orange"
              onClick={() => {
                if (!selectedUser) {
                  toast({
                    title: 'Error',
                    description: 'No user selected',
                    status: 'error',
                    duration: 3000,
                    isClosable: true,
                  });
                  return;
                }
                
                if (customPin && (customPin.length !== 4 || !/^\d+$/.test(customPin))) {
                  toast({
                    title: 'Invalid PIN',
                    description: 'Please enter a valid 4-digit PIN or leave blank for auto-generation',
                    status: 'warning',
                    duration: 3000,
                    isClosable: true,
                  });
                  return;
                }
                handleResetPinWithCustom(selectedUser);
                onCustomPinModalClose();
                setCustomPin(''); // Reset the custom PIN after use
              }}
              isLoading={isSubmitting}
            >
              Reset PIN
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default HKMPayUserManagementPage;