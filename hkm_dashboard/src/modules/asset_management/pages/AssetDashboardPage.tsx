import React from 'react';
import { useNavigate } from 'react-router-dom';
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
  Button,
  useColorModeValue,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Divider,
  Badge,
} from '@chakra-ui/react';
import {
  FiPlus,
  FiPackage,
  FiTruck,
  FiTrash2,
  FiDollarSign,
  FiAlertCircle,
  FiList,
  FiPieChart,
  FiTrendingUp,
  FiArrowLeft,
} from 'react-icons/fi';
import { motion } from 'framer-motion';
import PageHeader from '../../../components/shared/PageHeader';

const MotionCard = motion(Card);

interface ActionCardProps {
  title: string;
  description: string;
  icon: any;
  onClick: () => void;
  color: string;
  badge?: string;
}

const ActionCard: React.FC<ActionCardProps> = ({
  title,
  description,
  icon,
  onClick,
  color,
  badge,
}) => {
  const bgColor = useColorModeValue('white', 'gray.800');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');

  return (
    <MotionCard
      cursor="pointer"
      onClick={onClick}
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
          <Box p={3} borderRadius="lg" bg={`${color}.50`} color={`${color}.500`}>
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

const AssetDashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const bgColor = useColorModeValue('white', 'gray.800');

  const assetActions = [
    {
      title: 'Create New Asset',
      description: 'Register a new asset with purchase details, depreciation settings, and specifications.',
      icon: FiPlus,
      onClick: () => navigate('/asset-dashboard/create'),
      color: 'green',
      badge: 'New',
    },
    {
      title: 'View All Assets',
      description: 'Browse and manage all registered assets. View status, location, and custodian details.',
      icon: FiPackage,
      onClick: () => navigate('/asset-dashboard/list'),
      color: 'blue',
      badge: 'List',
    },
    {
      title: 'Asset Movement',
      description: 'Transfer assets between locations and custodians. Track movement history.',
      icon: FiTruck,
      onClick: () => navigate('/asset-dashboard/move'),
      color: 'purple',
      badge: 'Transfer',
    },
    {
      title: 'Scrap Asset',
      description: 'Process asset scrapping with approval workflow and accounting entries.',
      icon: FiTrash2,
      onClick: () => navigate('/asset-dashboard/scrap'),
      color: 'red',
      badge: 'Dispose',
    },
    {
      title: 'Sell Asset',
      description: 'Record asset sale transactions with customer details and profit/loss calculation.',
      icon: FiDollarSign,
      onClick: () => navigate('/asset-dashboard/sell'),
      color: 'orange',
      badge: 'Sale',
    },
    {
      title: 'Report Lost Asset',
      description: 'Report and process lost assets with FIR details and insurance claims.',
      icon: FiAlertCircle,
      onClick: () => navigate('/asset-dashboard/lost'),
      color: 'yellow',
      badge: 'Lost',
    },
    {
      title: 'Asset Movements',
      description: 'View complete history of all asset movements and transfers.',
      icon: FiList,
      onClick: () => navigate('/asset-dashboard/movements'),
      color: 'teal',
      badge: 'History',
    },
    {
      title: 'Asset Specifications',
      description: 'Manage asset specification templates for different categories.',
      icon: FiPieChart,
      onClick: () => navigate('/asset-dashboard/specifications'),
      color: 'cyan',
      badge: 'Config',
    },
  ];

  const quickStats = [
    {
      label: 'Total Assets',
      value: '--',
      helpText: 'All registered assets',
      color: 'blue',
    },
    {
      label: 'Available',
      value: '--',
      helpText: 'Ready for use',
      color: 'green',
    },
    {
      label: 'In Movement',
      value: '--',
      helpText: 'Being transferred',
      color: 'purple',
    },
    {
      label: 'Disposed',
      value: '--',
      helpText: 'Scrapped/Sold/Lost',
      color: 'red',
    },
  ];

  return (
    <Box minH="100vh" bg="gray.50">
      <PageHeader
        title="Asset Management Dashboard"
        subtitle="Manage your organization's assets - create, track, move, and dispose"
        onBack={() => navigate('/')}
      />

      <Container maxW="container.xl" py={8}>
        <VStack spacing={8} align="stretch">
          {/* Quick Stats */}
          <Box bg={bgColor} p={6} borderRadius="xl" shadow="md">
            <Heading size="md" mb={6} color="gray.700">
              Asset Overview
            </Heading>
            <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6}>
              {quickStats.map((stat, index) => (
                <Box key={index}>
                  <Stat>
                    <StatLabel color="gray.600" fontSize="sm">
                      {stat.label}
                    </StatLabel>
                    <StatNumber fontSize="3xl" color={`${stat.color}.500`}>
                      {stat.value}
                    </StatNumber>
                    <StatHelpText fontSize="xs" color="gray.500">
                      {stat.helpText}
                    </StatHelpText>
                  </Stat>
                </Box>
              ))}
            </SimpleGrid>
          </Box>

          <Divider />

          {/* Action Cards */}
          <Box>
            <Heading size="lg" mb={2} color="gray.700">
              Quick Actions
            </Heading>
            <Text color="gray.600" mb={6}>
              Select an action to perform on assets
            </Text>

            <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
              {assetActions.map((action, index) => (
                <ActionCard key={index} {...action} />
              ))}
            </SimpleGrid>
          </Box>

          {/* Info Section */}
          <Box bg="blue.50" p={6} borderRadius="xl" border="1px" borderColor="blue.200">
            <HStack spacing={4} align="start">
              <Icon as={FiTrendingUp} boxSize={6} color="blue.500" mt={1} />
              <VStack align="start" spacing={2}>
                <Heading size="sm" color="blue.700">
                  Asset Management Features
                </Heading>
                <Text fontSize="sm" color="blue.600">
                  • <strong>Complete Lifecycle:</strong> Track assets from purchase to disposal
                  <br />
                  • <strong>Depreciation:</strong> Automated SLM depreciation with journal entries
                  <br />
                  • <strong>Movement Tracking:</strong> Full history of location and custodian changes
                  <br />
                  • <strong>Disposal Workflows:</strong> Approval-based scrap, sale, and loss processes
                  <br />
                  • <strong>Accounting Integration:</strong> Automatic GL entries for all transactions
                  <br />
                  • <strong>Dynamic Specifications:</strong> Category-specific technical details
                </Text>
              </VStack>
            </HStack>
          </Box>

          {/* Back Button */}
          <HStack justify="center">
            <Button
              leftIcon={<FiArrowLeft />}
              onClick={() => navigate('/')}
              colorScheme="gray"
              variant="outline"
              size="lg"
            >
              Back to Dashboard
            </Button>
          </HStack>
        </VStack>
      </Container>
    </Box>
  );
};

export default AssetDashboardPage;

