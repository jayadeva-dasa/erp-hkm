import React from 'react';
import { Link } from 'react-router-dom';
import {
  Box,
  Container,
  Heading,
  Text,
  SimpleGrid,
  Card,
  CardBody,
  CardHeader,
  Icon,
  VStack,
  HStack,
  Badge,
  useColorModeValue,
  Flex,
  Divider,
  Stack,
} from '@chakra-ui/react';
import { FiTrendingUp, FiSearch, FiPieChart, FiPackage, FiUsers, FiBox, FiHome, FiBarChart2, FiDollarSign, FiGitBranch } from 'react-icons/fi';
import { motion } from 'framer-motion';

const MotionCard = motion(Card);

const DashboardCard = ({ title, description, icon, route, color, badge }) => {
  const bgColor = useColorModeValue('white', 'gray.800');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');

  return (
    <MotionCard
      cursor="pointer"
      as={Link}
      to={route}
      bg={bgColor}
      shadow="md"
      borderRadius="xl"
      overflow="hidden"
      transition="all 0.3s"
      _hover={{
        shadow: 'xl',
        transform: 'translateY(-4px)',
        bg: hoverBg,
      }}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      <CardHeader pb={2}>
        <HStack justify="space-between" align="start">
          <Box
            p={3}
            borderRadius="lg"
            bg={`${color}.50`}
            color={`${color}.500`}
          >
            <Icon as={icon} boxSize={8} />
          </Box>
          {badge && (
            <Badge colorScheme={color} fontSize="xs" px={2} py={1} borderRadius="md">
              {badge}
            </Badge>
          )}
        </HStack>
      </CardHeader>
      <CardBody pt={2}>
        <VStack align="start" spacing={2}>
          <Heading size="md" color={`${color}.600`}>
            {title}
          </Heading>
          <Text fontSize="sm" color="gray.600" noOfLines={2}>
            {description}
          </Text>
        </VStack>
      </CardBody>
    </MotionCard>
  );
};

const HomePage = () => {
  const headerBg = useColorModeValue('white', 'gray.800');
  const frappeSession = typeof window !== 'undefined' ? window?.frappe?.session : undefined;
  const userFullName = frappeSession?.user_fullname || 'System User';
  const userEmail = frappeSession?.user || '';

  const dashboardItems = [
    {
      title: 'Eagle View',
      description: 'Comprehensive financial reporting with multi-dimensional analysis. View income, expenses, and net profit by Cost Head, Cost Center, or Project.',
      icon: FiPieChart,
      route: '/eagle-view',
      color: 'purple',
      badge: 'Finance',
    },
    {
      title: 'Donation Insights',
      description: 'Full Dhananjaya donation analytics, trends, breakdowns and geo insights – now embedded here.',
      icon: FiTrendingUp,
      route: '/donation-insights',
      color: 'blue',
      badge: 'Analytics',
    },
    {
      title: 'Donor Search',
      description: 'Search aggregate identities, drill into profiles, and jump to ERPNext records in one click.',
      icon: FiSearch,
      route: '/donor-search',
      color: 'green',
      badge: 'Operations',
    },
    {
      title: 'Asset Reco',
      description: 'Asset reconciliation and management module for tracking and reconciling assets.',
      icon: FiPackage,
      route: '/asset-reco',
      color: 'orange',
      badge: 'Assets',
    },
    {
      title: 'HKM Pay User Management',
      description: 'Manage HKMP Users - view, create, edit, and delete user accounts with transaction and advance limits.',
      icon: FiUsers,
      route: '/hkm-pay-user-management',
      color: 'teal',
      badge: 'HKM Pay',
    },
    {
      title: 'Asset Dashboard',
      description: 'Complete asset lifecycle management - create, track, move, depreciate, and dispose assets with full accounting.',
      icon: FiBox,
      route: '/asset-dashboard',
      color: 'pink',
      badge: 'Assets',
    },
    {
      title: 'S3 File Search',
      description: 'Search and browse all files stored in the S3 bucket. View, download, and manage cloud storage files.',
      icon: FiSearch,
      route: '/s3-file-search',
      color: 'cyan',
      badge: 'Storage',
    },
    {
      title: 'Guest House Management',
      description: 'View room availability, booking status, and manage guest house operations. Check room availability by date and floor.',
      icon: FiHome,
      route: '/guest-house',
      color: 'indigo',
      badge: 'Operations',
    },
    {
      title: 'Category Analytics',
      description: 'Comprehensive financial analysis dashboard with balance sheet, income/expense trends, category management, and year-over-year comparisons.',
      icon: FiBarChart2,
      route: '/category-analytics',
      color: 'purple',
      badge: 'Finance',
    },
    {
      title: 'Daily Sales Report',
      description: 'Track daily sales, cash/bank adjustments, and balance with opening/closing balance logic. View day-wise sales and adjustment details.',
      icon: FiDollarSign,
      route: '/daily-sales-report',
      color: 'green',
      badge: 'Sales',
    },
    {
      title: 'Chart of Accounts Manager',
      description: 'Interactive drag-and-drop chart of accounts management. Easily reorganize account hierarchy, view balances, and manage account structure.',
      icon: FiGitBranch,
      route: '/chart-of-accounts',
      color: 'teal',
      badge: 'Finance',
    },
  ];

  return (
    <Box minH="100vh" bg="gray.50">
      {/* Header */}
      <Box bg={headerBg} shadow="sm" mb={8}>
        <Container maxW="container.xl" py={8}>
          <Flex justify="space-between" align="start" mb={4}>
            <HStack spacing={4}>
              <Text fontSize="4xl" fontWeight="bold">
                🙏
              </Text>
              <VStack align="start" spacing={0}>
                <Heading size="2xl" bgGradient="linear(to-r, orange.400, orange.600)" bgClip="text">
                  Hare Krishna Movement
                </Heading>
                <Text fontSize="xl" color="gray.600" fontWeight="medium">
                  Jaipur - Unified Dashboard
                </Text>
              </VStack>
            </HStack>
            <Stack spacing={0} align="flex-end">
              <Text fontSize="sm" color="gray.500">
                Logged in as
              </Text>
              <Text fontWeight="bold" color="gray.700">
                {userFullName}
              </Text>
              {userEmail ? (
                <Text fontSize="sm" color="gray.500">
                  {userEmail}
                </Text>
              ) : null}
            </Stack>
          </Flex>
          <Divider mb={4} />
            <Text fontSize="md" color="gray.600">
              Access all your reports, analytics, and insights from one centralized location
            </Text>
        </Container>
      </Box>

      {/* Dashboard Cards */}
      <Container maxW="container.xl" pb={12}>
        <VStack spacing={8} align="stretch">
          <Box>
            <Heading size="lg" mb={2} color="gray.700">
              Quick Access
            </Heading>
            <Text color="gray.600">
              Select a module to get started
            </Text>
          </Box>

          <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
            {dashboardItems.map((item, index) => (
              <DashboardCard key={index} {...item} />
            ))}
          </SimpleGrid>

          {/* Stats Section */}
          <Box mt={8} p={6} bg="white" borderRadius="xl" shadow="md">
            <Heading size="md" mb={4} color="gray.700">
              Dashboard Statistics
            </Heading>
            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
              <Box>
                <Text fontSize="3xl" fontWeight="bold" color="blue.500">
                  11
                </Text>
                <Text color="gray.600" fontSize="sm">
                  Integrated Modules
                </Text>
              </Box>
              <Box>
                <Text fontSize="3xl" fontWeight="bold" color="green.500">
                  Active
                </Text>
                <Text color="gray.600" fontSize="sm">
                  System Status
                </Text>
              </Box>
            </SimpleGrid>
          </Box>
        </VStack>
      </Container>
    </Box>
  );
};

export default HomePage;

