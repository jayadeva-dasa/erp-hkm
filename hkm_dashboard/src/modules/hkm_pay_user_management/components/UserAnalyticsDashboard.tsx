import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Heading,
  Text,
  SimpleGrid,
  Card,
  CardBody,
  VStack,
  HStack,
  Button,
  FormControl,
  FormLabel,
  Input,
  Select,
  Spinner,
  Alert,
  AlertIcon,
  Badge,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Divider,
  useToast,
  useColorModeValue,
  Flex,
} from '@chakra-ui/react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { FiRefreshCw, FiTrendingUp, FiDollarSign, FiCheckCircle, FiXCircle } from 'react-icons/fi';
import { format, subDays, subMonths } from 'date-fns';
import { hkmpUserApi } from '../api/hkmpUserApi';
import { HKMPUser, UserAnalytics } from '../types';

interface UserAnalyticsDashboardProps {
  user: HKMPUser;
}

const COLORS = {
  Success: '#38A169',
  Failed: '#E53E3E',
  Pending: '#ECC94B',
  Processing: '#3182CE',
  UPI: '#805AD5',
  IMPS: '#DD6B20',
  NEFT: '#38B2AC',
  RTGS: '#D53F8C',
};

const UserAnalyticsDashboard: React.FC<UserAnalyticsDashboardProps> = ({ user }) => {
  const [analytics, setAnalytics] = useState<UserAnalytics | null>(null);
  const [loading, setLoading] = useState(false);
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const toast = useToast();
  
  const bgColor = useColorModeValue('white', 'gray.800');
  const cardBg = useColorModeValue('white', 'gray.700');

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const data = await hkmpUserApi.getUserAnalytics(user.user, fromDate, toDate);
      setAnalytics(data);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to fetch analytics',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [user.user]);

  const handleQuickFilter = (days: number) => {
    const today = new Date();
    const from = subDays(today, days);
    setFromDate(format(from, 'yyyy-MM-dd'));
    setToDate(format(today, 'yyyy-MM-dd'));
  };

  const handleQuickFilterMonths = (months: number) => {
    const today = new Date();
    const from = subMonths(today, months);
    setFromDate(format(from, 'yyyy-MM-dd'));
    setToDate(format(today, 'yyyy-MM-dd'));
  };

  const handleClearFilters = () => {
    setFromDate('');
    setToDate('');
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return format(new Date(dateString), 'MMM dd');
  };

  if (loading && !analytics) {
    return (
      <Flex justify="center" align="center" minH="400px">
        <VStack spacing={4}>
          <Spinner size="xl" color="teal.500" thickness="4px" />
          <Text color="gray.600">Loading analytics...</Text>
        </VStack>
      </Flex>
    );
  }

  if (!analytics) {
    return (
      <Alert status="info">
        <AlertIcon />
        No analytics data available.
      </Alert>
    );
  }

  return (
    <Box>
      {/* Date Filters */}
      <Card mb={6} bg={cardBg}>
        <CardBody>
          <VStack spacing={4} align="stretch">
            <Heading size="sm" color="teal.600">
              Analytics Period
            </Heading>
            
            <HStack spacing={4} flexWrap="wrap">
              <Button size="sm" onClick={() => handleQuickFilter(7)} variant="outline" colorScheme="teal">
                Last 7 Days
              </Button>
              <Button size="sm" onClick={() => handleQuickFilter(30)} variant="outline" colorScheme="teal">
                Last 30 Days
              </Button>
              <Button size="sm" onClick={() => handleQuickFilterMonths(3)} variant="outline" colorScheme="teal">
                Last 3 Months
              </Button>
              <Button size="sm" onClick={() => handleQuickFilterMonths(6)} variant="outline" colorScheme="teal">
                Last 6 Months
              </Button>
              <Button size="sm" onClick={handleClearFilters} variant="outline">
                All Time
              </Button>
            </HStack>

            <HStack spacing={4} flexWrap="wrap">
              <FormControl maxW="200px">
                <FormLabel fontSize="sm">From Date</FormLabel>
                <Input
                  type="date"
                  size="sm"
                  value={fromDate}
                  onChange={(e) => setFromDate(e.target.value)}
                />
              </FormControl>
              <FormControl maxW="200px">
                <FormLabel fontSize="sm">To Date</FormLabel>
                <Input
                  type="date"
                  size="sm"
                  value={toDate}
                  onChange={(e) => setToDate(e.target.value)}
                />
              </FormControl>
              <Button
                leftIcon={<FiRefreshCw />}
                colorScheme="teal"
                size="sm"
                onClick={fetchAnalytics}
                isLoading={loading}
                mt={6}
              >
                Refresh
              </Button>
            </HStack>
          </VStack>
        </CardBody>
      </Card>

      {/* Summary Stats */}
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={4} mb={6}>
        <Card bg={cardBg}>
          <CardBody>
            <Stat>
              <StatLabel>Total Transactions</StatLabel>
              <StatNumber color="blue.600">{analytics.total_transactions}</StatNumber>
              <StatHelpText>
                <HStack spacing={2}>
                  <Box as={FiCheckCircle} color="green.500" />
                  <Text>{analytics.success_count} successful</Text>
                </HStack>
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card bg={cardBg}>
          <CardBody>
            <Stat>
              <StatLabel>Total Amount</StatLabel>
              <StatNumber color="green.600">
                {formatCurrency(analytics.total_amount)}
              </StatNumber>
              <StatHelpText>
                Avg: {formatCurrency(analytics.average_transaction)}
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card bg={cardBg}>
          <CardBody>
            <Stat>
              <StatLabel>Success Rate</StatLabel>
              <StatNumber color="teal.600">
                {analytics.success_rate.toFixed(1)}%
              </StatNumber>
              <StatHelpText>
                <HStack spacing={2}>
                  <Box as={FiXCircle} color="red.500" />
                  <Text>{analytics.failed_count} failed</Text>
                </HStack>
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card bg={cardBg}>
          <CardBody>
            <Stat>
              <StatLabel>Pending Amount</StatLabel>
              <StatNumber color="yellow.600">
                {formatCurrency(analytics.pending_amount)}
              </StatNumber>
              <StatHelpText>Bills: {analytics.bills_received}/{analytics.bills_received + analytics.bills_pending}</StatHelpText>
            </Stat>
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Additional Stats Cards */}
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={4} mb={6}>
        <Card bg={cardBg}>
          <CardBody>
            <VStack align="start" spacing={2}>
              <Text fontSize="sm" color="gray.600">Highest Transaction</Text>
              <Text fontSize="2xl" fontWeight="bold" color="green.600">
                {formatCurrency(analytics.highest_transaction)}
              </Text>
            </VStack>
          </CardBody>
        </Card>

        <Card bg={cardBg}>
          <CardBody>
            <VStack align="start" spacing={2}>
              <Text fontSize="sm" color="gray.600">Most Used Method</Text>
              <Badge colorScheme="purple" fontSize="lg" p={2}>
                {analytics.most_used_method || 'N/A'}
              </Badge>
            </VStack>
          </CardBody>
        </Card>

        <Card bg={cardBg}>
          <CardBody>
            <VStack align="start" spacing={2}>
              <Text fontSize="sm" color="gray.600">Bills Received</Text>
              <HStack spacing={2}>
                <Text fontSize="2xl" fontWeight="bold" color="green.600">
                  {analytics.bills_received}
                </Text>
                <Text fontSize="sm" color="gray.500">
                  / {analytics.bills_received + analytics.bills_pending}
                </Text>
              </HStack>
              <Text fontSize="xs" color="gray.500">
                {analytics.bills_pending} pending
              </Text>
            </VStack>
          </CardBody>
        </Card>

        <Card bg={cardBg}>
          <CardBody>
            <VStack align="start" spacing={2}>
              <Text fontSize="sm" color="gray.600">Returns</Text>
              <Text fontSize="2xl" fontWeight="bold" color="orange.600">
                {analytics.returns}
              </Text>
            </VStack>
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Charts Section */}
      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6} mb={6}>
        {/* Transaction Trends */}
        <Card bg={cardBg}>
          <CardBody>
            <Heading size="sm" mb={4} color="teal.600">
              Transaction Trends
            </Heading>
            {analytics.transaction_trends.length > 0 ? (
              <Box h="300px">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={analytics.transaction_trends}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="date"
                      tickFormatter={formatDate}
                      fontSize={11}
                    />
                    <YAxis yAxisId="left" fontSize={11} />
                    <YAxis yAxisId="right" orientation="right" fontSize={11} />
                    <Tooltip
                      formatter={(value: any, name: string) =>
                        name === 'amount' ? formatCurrency(value) : value
                      }
                      labelFormatter={(label) => format(new Date(label), 'MMM dd, yyyy')}
                    />
                    <Legend />
                    <Line
                      yAxisId="left"
                      type="monotone"
                      dataKey="count"
                      stroke="#3182CE"
                      strokeWidth={2}
                      name="Transactions"
                    />
                    <Line
                      yAxisId="right"
                      type="monotone"
                      dataKey="amount"
                      stroke="#38A169"
                      strokeWidth={2}
                      name="Amount (₹)"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            ) : (
              <Text color="gray.500" textAlign="center" py={10}>
                No trend data available
              </Text>
            )}
          </CardBody>
        </Card>

        {/* Status Breakdown */}
        <Card bg={cardBg}>
          <CardBody>
            <Heading size="sm" mb={4} color="teal.600">
              Status Distribution
            </Heading>
            {analytics.status_breakdown.length > 0 ? (
              <Box h="300px">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={analytics.status_breakdown}
                      dataKey="count"
                      nameKey="status"
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      label={(entry) => `${entry.status} (${entry.count})`}
                    >
                      {analytics.status_breakdown.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={COLORS[entry.status as keyof typeof COLORS] || '#718096'}
                        />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value: any, name: string, props: any) =>
                        `${value} (${formatCurrency(props.payload.amount)})`
                      }
                    />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
            ) : (
              <Text color="gray.500" textAlign="center" py={10}>
                No status data available
              </Text>
            )}
          </CardBody>
        </Card>

        {/* Payment Method Breakdown */}
        <Card bg={cardBg}>
          <CardBody>
            <Heading size="sm" mb={4} color="teal.600">
              Payment Methods
            </Heading>
            {analytics.transfer_type_breakdown.length > 0 ? (
              <Box h="300px">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={analytics.transfer_type_breakdown}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="type" fontSize={11} />
                    <YAxis fontSize={11} />
                    <Tooltip
                      formatter={(value: any) => formatCurrency(value)}
                    />
                    <Legend />
                    <Bar dataKey="amount" fill="#805AD5" name="Amount (₹)">
                      {analytics.transfer_type_breakdown.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={COLORS[entry.type as keyof typeof COLORS] || '#805AD5'}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            ) : (
              <Text color="gray.500" textAlign="center" py={10}>
                No payment method data available
              </Text>
            )}
          </CardBody>
        </Card>

        {/* Status by Amount */}
        <Card bg={cardBg}>
          <CardBody>
            <Heading size="sm" mb={4} color="teal.600">
              Amount by Status
            </Heading>
            {analytics.status_breakdown.length > 0 ? (
              <Box h="300px">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={analytics.status_breakdown}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="status" fontSize={11} />
                    <YAxis fontSize={11} tickFormatter={(value) => `₹${(value / 1000).toFixed(0)}k`} />
                    <Tooltip
                      formatter={(value: any) => formatCurrency(value)}
                    />
                    <Legend />
                    <Bar dataKey="amount" name="Amount (₹)">
                      {analytics.status_breakdown.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={COLORS[entry.status as keyof typeof COLORS] || '#718096'}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            ) : (
              <Text color="gray.500" textAlign="center" py={10}>
                No data available
              </Text>
            )}
          </CardBody>
        </Card>
      </SimpleGrid>
    </Box>
  );
};

export default UserAnalyticsDashboard;

