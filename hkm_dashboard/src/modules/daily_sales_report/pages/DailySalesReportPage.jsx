import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Heading,
  VStack,
  HStack,
  Button,
  Select,
  FormControl,
  FormLabel,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  useColorModeValue,
  Alert,
  AlertIcon,
  Spinner,
  Text,
  Badge,
  Card,
  CardBody,
  CardHeader,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
} from '@chakra-ui/react';
import { getCompanies, getAccounts, getDailySalesReport, getDailySalesReportCash } from '../api/dailySalesReportApi';

const DailySalesReportPage = () => {
  const bgColor = useColorModeValue('white', 'gray.800');
  const [loading, setLoading] = useState(false);
  const [loadingCash, setLoadingCash] = useState(false);
  const [error, setError] = useState(null);
  const [companies, setCompanies] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [reportData, setReportData] = useState([]);
  const [cashReportData, setCashReportData] = useState([]);
  const [activeTab, setActiveTab] = useState(0);

  // Get default date range (last 30 days)
  const getDefaultDateRange = () => {
    const today = new Date();
    const toDate = today.toISOString().split('T')[0];
    const fromDate = new Date(today);
    fromDate.setDate(fromDate.getDate() - 30);
    return {
      fromDate: fromDate.toISOString().split('T')[0],
      toDate: toDate,
    };
  };

  const defaultDates = getDefaultDateRange();
  const [filters, setFilters] = useState({
    company: '',
    account: '',
    fromDate: defaultDates.fromDate,
    toDate: defaultDates.toDate,
  });

  useEffect(() => {
    loadCompanies();
    loadAccounts();
  }, []);

  const loadCompanies = async () => {
    try {
      const companiesList = await getCompanies();
      setCompanies(companiesList || []);
      if (companiesList && companiesList.length > 0) {
        setFilters(prev => ({ ...prev, company: companiesList[0] }));
      }
    } catch (err) {
      console.error('Error loading companies:', err);
      setError('Failed to load companies');
    }
  };

  const loadAccounts = async () => {
    try {
      const accountsList = await getAccounts();
      setAccounts(accountsList || []);
      if (accountsList && accountsList.length > 0) {
        setFilters(prev => ({ ...prev, account: accountsList[0] }));
      }
    } catch (err) {
      console.error('Error loading accounts:', err);
      setError('Failed to load accounts');
    }
  };

  const loadReport = async () => {
    if (!filters.company || !filters.account || !filters.fromDate || !filters.toDate) {
      setError('Please select company, account, and date range');
      return;
    }

    setLoading(true);
    setLoadingCash(true);
    setError(null);

    try {
      // Load both reports in parallel
      const [salesData, cashData] = await Promise.all([
        getDailySalesReport(
          filters.fromDate,
          filters.toDate,
          filters.company,
          filters.account
        ),
        getDailySalesReportCash(
          filters.fromDate,
          filters.toDate,
          filters.company,
          filters.account
        ),
      ]);
      setReportData(salesData || []);
      setCashReportData(cashData || []);
    } catch (err) {
      const errorMessage = err?.response?.data?.message || err?.message || 'Failed to load report';
      setError(errorMessage);
      console.error('Error loading report:', err);
    } finally {
      setLoading(false);
      setLoadingCash(false);
    }
  };

  const handleFilterChange = (name, value) => {
    setFilters(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount || 0);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  // Calculate totals for sales report
  const totals = reportData.reduce(
    (acc, row) => ({
      opening_balance: acc.opening_balance + (row.opening_balance || 0),
      sale_amount: acc.sale_amount + (row.sale_amount || 0),
      cash_adjustment: acc.cash_adjustment + (row.cash_adjustment || 0),
      bank_adjustment: acc.bank_adjustment + (row.bank_adjustment || 0),
      total_adjustments: acc.total_adjustments + (row.total_adjustments || 0),
      closing_balance: acc.closing_balance + (row.closing_balance || 0),
    }),
    {
      opening_balance: 0,
      sale_amount: 0,
      cash_adjustment: 0,
      bank_adjustment: 0,
      total_adjustments: 0,
      closing_balance: 0,
    }
  );

  // Calculate totals for cash report
  const cashTotals = cashReportData.reduce(
    (acc, row) => ({
      opening_balance: acc.opening_balance + (row.opening_balance || 0),
      total_cash_collection: acc.total_cash_collection + (row.total_cash_collection || 0),
      total_cash_adjustment_amount: acc.total_cash_adjustment_amount + (row.total_cash_adjustment_amount || 0),
      difference: acc.difference + (row.difference || 0),
      closing_balance: acc.closing_balance + (row.closing_balance || 0),
    }),
    {
      opening_balance: 0,
      total_cash_collection: 0,
      total_cash_adjustment_amount: 0,
      difference: 0,
      closing_balance: 0,
    }
  );

  return (
    <Box minH="100vh" bg="gray.50" py={8}>
      <Container maxW="container.xl">
        <VStack spacing={6} align="stretch">
          {/* Header */}
          <Box>
            <Heading size="xl" mb={2} color="gray.700">
              Daily Sales Report
            </Heading>
            <Text color="gray.600">
              Track daily sales, adjustments, and balance with opening/closing balance logic
            </Text>
          </Box>

          {/* Filters */}
          <Card bg={bgColor} shadow="md">
            <CardHeader>
              <Heading size="md">Filters</Heading>
            </CardHeader>
            <CardBody>
              <VStack spacing={4}>
                <HStack spacing={4} width="100%" flexWrap="wrap">
                  <FormControl flex="1" minW="200px">
                    <FormLabel>Company</FormLabel>
                    <Select
                      value={filters.company}
                      onChange={(e) => handleFilterChange('company', e.target.value)}
                      placeholder="Select Company"
                    >
                      {companies.map((company, index) => (
                        <option key={index} value={company}>
                          {company}
                        </option>
                      ))}
                    </Select>
                  </FormControl>

                  <FormControl flex="1" minW="200px">
                    <FormLabel>Account</FormLabel>
                    <Select
                      value={filters.account}
                      onChange={(e) => handleFilterChange('account', e.target.value)}
                      placeholder="Select Account"
                    >
                      {accounts.map((account, index) => (
                        <option key={index} value={account}>
                          {account}
                        </option>
                      ))}
                    </Select>
                  </FormControl>

                  <FormControl flex="1" minW="150px">
                    <FormLabel>From Date</FormLabel>
                    <input
                      type="date"
                      value={filters.fromDate}
                      onChange={(e) => handleFilterChange('fromDate', e.target.value)}
                      style={{
                        width: '100%',
                        padding: '8px',
                        border: '1px solid #e2e8f0',
                        borderRadius: '6px',
                      }}
                    />
                  </FormControl>

                  <FormControl flex="1" minW="150px">
                    <FormLabel>To Date</FormLabel>
                    <input
                      type="date"
                      value={filters.toDate}
                      onChange={(e) => handleFilterChange('toDate', e.target.value)}
                      style={{
                        width: '100%',
                        padding: '8px',
                        border: '1px solid #e2e8f0',
                        borderRadius: '6px',
                      }}
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel>&nbsp;</FormLabel>
                    <Button
                      colorScheme="blue"
                      onClick={loadReport}
                      isLoading={loading}
                      loadingText="Loading..."
                    >
                      Load Report
                    </Button>
                  </FormControl>
                </HStack>
              </VStack>
            </CardBody>
          </Card>

          {/* Error Alert */}
          {error && (
            <Alert status="error">
              <AlertIcon />
              {error}
            </Alert>
          )}

          {/* Report Tabs */}
          {loading || loadingCash ? (
            <Box textAlign="center" py={8}>
              <Spinner size="xl" color="blue.500" />
              <Text mt={4}>Loading report data...</Text>
            </Box>
          ) : (reportData.length > 0 || cashReportData.length > 0) ? (
            <Card bg={bgColor} shadow="md">
              <CardBody>
                <Tabs index={activeTab} onChange={setActiveTab}>
                  <TabList>
                    <Tab>Daily Sales Report</Tab>
                    <Tab>Daily Cash Report</Tab>
                  </TabList>

                  <TabPanels>
                    {/* Daily Sales Report Tab */}
                    <TabPanel>
                      {reportData.length > 0 ? (
                        <TableContainer>
                          <Table variant="simple" size="sm">
                            <Thead>
                              <Tr>
                                <Th>Date</Th>
                                <Th isNumeric>Opening Balance</Th>
                                <Th isNumeric>Sale Amount</Th>
                                <Th isNumeric>Cash Adjustment</Th>
                                <Th isNumeric>Bank Adjustment</Th>
                                <Th isNumeric>Total Adjustments</Th>
                                <Th isNumeric>Closing Balance</Th>
                              </Tr>
                            </Thead>
                            <Tbody>
                              {reportData.map((row, index) => (
                                <Tr key={index}>
                                  <Td>{formatDate(row.date)}</Td>
                                  <Td isNumeric>
                                    <Badge
                                      colorScheme={row.opening_balance >= 0 ? 'green' : 'red'}
                                    >
                                      {formatCurrency(row.opening_balance)}
                                    </Badge>
                                  </Td>
                                  <Td isNumeric>
                                    <Text color="blue.600" fontWeight="medium">
                                      {formatCurrency(row.sale_amount)}
                                    </Text>
                                  </Td>
                                  <Td isNumeric>
                                    <Text color="orange.600">
                                      {formatCurrency(row.cash_adjustment)}
                                    </Text>
                                  </Td>
                                  <Td isNumeric>
                                    <Text color="purple.600">
                                      {formatCurrency(row.bank_adjustment)}
                                    </Text>
                                  </Td>
                                  <Td isNumeric>
                                    <Text color="gray.600" fontWeight="medium">
                                      {formatCurrency(row.total_adjustments)}
                                    </Text>
                                  </Td>
                                  <Td isNumeric>
                                    <Badge
                                      colorScheme={row.closing_balance >= 0 ? 'green' : 'red'}
                                      fontSize="sm"
                                      px={2}
                                      py={1}
                                    >
                                      {formatCurrency(row.closing_balance)}
                                    </Badge>
                                  </Td>
                                </Tr>
                              ))}
                              {/* Totals Row */}
                              <Tr bg="gray.100" fontWeight="bold">
                                <Td>
                                  <Text fontWeight="bold">Total</Text>
                                </Td>
                                <Td isNumeric>
                                  <Badge colorScheme="gray">
                                    {formatCurrency(totals.opening_balance)}
                                  </Badge>
                                </Td>
                                <Td isNumeric>
                                  <Text color="blue.700">
                                    {formatCurrency(totals.sale_amount)}
                                  </Text>
                                </Td>
                                <Td isNumeric>
                                  <Text color="orange.700">
                                    {formatCurrency(totals.cash_adjustment)}
                                  </Text>
                                </Td>
                                <Td isNumeric>
                                  <Text color="purple.700">
                                    {formatCurrency(totals.bank_adjustment)}
                                  </Text>
                                </Td>
                                <Td isNumeric>
                                  <Text color="gray.700">
                                    {formatCurrency(totals.total_adjustments)}
                                  </Text>
                                </Td>
                                <Td isNumeric>
                                  <Badge
                                    colorScheme={totals.closing_balance >= 0 ? 'green' : 'red'}
                                    fontSize="md"
                                    px={2}
                                    py={1}
                                  >
                                    {formatCurrency(totals.closing_balance)}
                                  </Badge>
                                </Td>
                              </Tr>
                            </Tbody>
                          </Table>
                        </TableContainer>
                      ) : (
                        <Text textAlign="center" color="gray.500" py={8}>
                          No sales report data available.
                        </Text>
                      )}
                    </TabPanel>

                    {/* Daily Cash Report Tab */}
                    <TabPanel>
                      {cashReportData.length > 0 ? (
                        <TableContainer>
                          <Table variant="simple" size="sm">
                            <Thead>
                              <Tr>
                                <Th>Date</Th>
                                <Th isNumeric>Opening Balance</Th>
                                <Th isNumeric>Cash Collection</Th>
                                <Th isNumeric>Cash Adjustment</Th>
                                <Th isNumeric>Difference</Th>
                                <Th isNumeric>Closing Balance</Th>
                              </Tr>
                            </Thead>
                            <Tbody>
                              {cashReportData.map((row, index) => (
                                <Tr key={index}>
                                  <Td>{formatDate(row.date)}</Td>
                                  <Td isNumeric>
                                    <Badge
                                      colorScheme={row.opening_balance >= 0 ? 'green' : 'red'}
                                    >
                                      {formatCurrency(row.opening_balance)}
                                    </Badge>
                                  </Td>
                                  <Td isNumeric>
                                    <Text color="blue.600" fontWeight="medium">
                                      {formatCurrency(row.total_cash_collection)}
                                    </Text>
                                  </Td>
                                  <Td isNumeric>
                                    <Text color="orange.600">
                                      {formatCurrency(row.total_cash_adjustment_amount)}
                                    </Text>
                                  </Td>
                                  <Td isNumeric>
                                    <Badge
                                      colorScheme={row.difference >= 0 ? 'green' : 'red'}
                                      fontSize="sm"
                                      px={2}
                                      py={1}
                                    >
                                      {formatCurrency(row.difference)}
                                    </Badge>
                                  </Td>
                                  <Td isNumeric>
                                    <Badge
                                      colorScheme={row.closing_balance >= 0 ? 'green' : 'red'}
                                      fontSize="sm"
                                      px={2}
                                      py={1}
                                    >
                                      {formatCurrency(row.closing_balance)}
                                    </Badge>
                                  </Td>
                                </Tr>
                              ))}
                              {/* Totals Row */}
                              <Tr bg="gray.100" fontWeight="bold">
                                <Td>
                                  <Text fontWeight="bold">Total</Text>
                                </Td>
                                <Td isNumeric>
                                  <Badge colorScheme="gray">
                                    {formatCurrency(cashTotals.opening_balance)}
                                  </Badge>
                                </Td>
                                <Td isNumeric>
                                  <Text color="blue.700">
                                    {formatCurrency(cashTotals.total_cash_collection)}
                                  </Text>
                                </Td>
                                <Td isNumeric>
                                  <Text color="orange.700">
                                    {formatCurrency(cashTotals.total_cash_adjustment_amount)}
                                  </Text>
                                </Td>
                                <Td isNumeric>
                                  <Badge
                                    colorScheme={cashTotals.difference >= 0 ? 'green' : 'red'}
                                    fontSize="md"
                                    px={2}
                                    py={1}
                                  >
                                    {formatCurrency(cashTotals.difference)}
                                  </Badge>
                                </Td>
                                <Td isNumeric>
                                  <Badge
                                    colorScheme={cashTotals.closing_balance >= 0 ? 'green' : 'red'}
                                    fontSize="md"
                                    px={2}
                                    py={1}
                                  >
                                    {formatCurrency(cashTotals.closing_balance)}
                                  </Badge>
                                </Td>
                              </Tr>
                            </Tbody>
                          </Table>
                        </TableContainer>
                      ) : (
                        <Text textAlign="center" color="gray.500" py={8}>
                          No cash report data available.
                        </Text>
                      )}
                    </TabPanel>
                  </TabPanels>
                </Tabs>
              </CardBody>
            </Card>
          ) : (
            !loading && !loadingCash && (
              <Card bg={bgColor} shadow="md">
                <CardBody>
                  <Text textAlign="center" color="gray.500" py={8}>
                    No data available. Please select filters and click "Load Report".
                  </Text>
                </CardBody>
              </Card>
            )
          )}
        </VStack>
      </Container>
    </Box>
  );
};

export default DailySalesReportPage;

