import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Heading,
  Button,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  HStack,
  Input,
  Select,
  useToast,
  Spinner,
  Text,
  IconButton,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
} from '@chakra-ui/react';
import { FiPlus, FiEdit, FiEye, FiMoreVertical, FiArrowLeft, FiCheck } from 'react-icons/fi';
import PageHeader from '../../../components/shared/PageHeader';
import apiClient from '../../../services/apiClient';

interface Asset {
  name: string;
  asset_name: string;
  item_code: string;
  status: string;
  docstatus: number;
  custodian_department: string;
  current_sub_custodian: string;
  current_location: string;
  gross_purchase_amount: number;
  value_after_depreciation: number;
}

const AssetListPage: React.FC = () => {
  const navigate = useNavigate();
  const toast = useToast();
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    fetchAssets();
  }, []);

  const fetchAssets = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/api/resource/HKM Asset', {
        params: {
          fields: JSON.stringify([
            'name',
            'asset_name',
            'item_code',
            'status',
            'docstatus',
            'custodian_department',
            'current_sub_custodian',
            'current_location',
            'gross_purchase_amount',
            'value_after_depreciation',
          ]),
          // Include both draft (docstatus=0) and submitted (docstatus=1) assets
          filters: JSON.stringify([['docstatus', 'in', [0, 1]]]),
          limit_page_length: 100,
          order_by: 'modified desc',
        },
      });
      setAssets(response.data.data || []);
    } catch (error: any) {
      toast({
        title: 'Error fetching assets',
        description: error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitAsset = async (assetName: string) => {
    try {
      // First, get the document
      const docResponse = await apiClient.get(`/api/resource/HKM Asset/${assetName}`);
      const doc = docResponse.data.data;
      
      // Submit using Frappe's submit method
      await apiClient.post('/api/method/frappe.client.submit', {
        doc: doc,
      });
      
      toast({
        title: 'Asset Submitted!',
        description: `Asset ${assetName} has been submitted successfully`,
        status: 'success',
        duration: 5000,
      });
      
      // Refresh the list
      fetchAssets();
    } catch (error: any) {
      toast({
        title: 'Error submitting asset',
        description: error.response?.data?.message || error.response?.data?.exc || error.message,
        status: 'error',
        duration: 5000,
      });
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      'Draft': 'gray',
      'Available': 'green',
      'Submitted': 'blue',
      'Partially Depreciated': 'yellow',
      'Fully Depreciated': 'orange',
      'Scrapped': 'red',
      'Sold': 'purple',
      'Lost': 'red',
      'Cancelled': 'red',
    };
    return colors[status] || 'gray';
  };

  const filteredAssets = assets.filter((asset) => {
    const matchesSearch =
      !searchQuery ||
      asset.asset_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      asset.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      asset.item_code?.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesStatus = !statusFilter || 
      (statusFilter === 'Draft' ? asset.docstatus === 0 : asset.status === statusFilter);

    return matchesSearch && matchesStatus;
  });

  return (
    <Box minH="100vh" bg="gray.50">
      <PageHeader
        title="All Assets"
        subtitle="Browse and manage all registered assets"
        onBack={() => navigate('/asset-dashboard')}
      />

      <Container maxW="container.xl" py={8}>
        <Box bg="white" p={6} borderRadius="xl" shadow="md">
          {/* Filters */}
          <HStack mb={6} spacing={4}>
            <Input
              placeholder="Search by name, ID, or item..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              maxW="400px"
            />
            <Select
              placeholder="Filter by status"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              maxW="200px"
            >
              <option value="">All Statuses</option>
              <option value="Draft">Draft</option>
              <option value="Available">Available</option>
              <option value="Submitted">Submitted</option>
              <option value="Partially Depreciated">Partially Depreciated</option>
              <option value="Fully Depreciated">Fully Depreciated</option>
              <option value="Scrapped">Scrapped</option>
              <option value="Sold">Sold</option>
              <option value="Lost">Lost</option>
            </Select>
            <Button
              leftIcon={<FiPlus />}
              colorScheme="green"
              onClick={() => navigate('/asset-dashboard/create')}
              ml="auto"
            >
              Create New Asset
            </Button>
          </HStack>

          {/* Table */}
          {loading ? (
            <Box textAlign="center" py={10}>
              <Spinner size="xl" color="blue.500" />
              <Text mt={4}>Loading assets...</Text>
            </Box>
          ) : filteredAssets.length === 0 ? (
            <Box textAlign="center" py={10}>
              <Text fontSize="lg" color="gray.500">
                No assets found
              </Text>
            </Box>
          ) : (
            <Box overflowX="auto">
              <Table variant="simple">
                <Thead bg="gray.50">
                  <Tr>
                    <Th>Asset ID</Th>
                    <Th>Asset Name</Th>
                    <Th>Item Code</Th>
                    <Th>Status</Th>
                    <Th>Department</Th>
                    <Th>Custodian</Th>
                    <Th>Location</Th>
                    <Th isNumeric>Purchase Amount</Th>
                    <Th isNumeric>Current Value</Th>
                    <Th>Actions</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {filteredAssets.map((asset) => (
                    <Tr key={asset.name} _hover={{ bg: 'gray.50' }}>
                      <Td fontWeight="medium">{asset.name}</Td>
                      <Td>{asset.asset_name}</Td>
                      <Td>{asset.item_code}</Td>
                      <Td>
                        <Badge colorScheme={getStatusColor(asset.docstatus === 0 ? 'Draft' : asset.status)}>
                          {asset.docstatus === 0 ? 'Draft' : asset.status}
                        </Badge>
                      </Td>
                      <Td>{asset.custodian_department}</Td>
                      <Td>{asset.current_sub_custodian || '-'}</Td>
                      <Td>{asset.current_location || '-'}</Td>
                      <Td isNumeric>₹{asset.gross_purchase_amount?.toLocaleString()}</Td>
                      <Td isNumeric>₹{asset.value_after_depreciation?.toLocaleString()}</Td>
                      <Td>
                        <Menu>
                          <MenuButton
                            as={IconButton}
                            icon={<FiMoreVertical />}
                            variant="ghost"
                            size="sm"
                          />
                          <MenuList>
                            <MenuItem
                              icon={<FiEye />}
                              onClick={() =>
                                navigate(`/asset-dashboard/detail/${asset.name}`)
                              }
                            >
                              View Details
                            </MenuItem>
                            {asset.docstatus === 0 && (
                              <>
                                <MenuItem
                                  icon={<FiEdit />}
                                  onClick={() =>
                                    navigate(`/asset-dashboard/detail/${asset.name}`)
                                  }
                                >
                                  Edit Asset
                                </MenuItem>
                                <MenuItem
                                  icon={<FiCheck />}
                                  onClick={() => handleSubmitAsset(asset.name)}
                                >
                                  Submit Asset
                                </MenuItem>
                              </>
                            )}
                            {asset.docstatus === 1 && (
                              <MenuItem
                                icon={<FiEdit />}
                                onClick={() =>
                                  navigate(`/asset-dashboard/move`, {
                                    state: { assetId: asset.name },
                                  })
                                }
                              >
                                Move Asset
                              </MenuItem>
                            )}
                          </MenuList>
                        </Menu>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </Box>
          )}

          {/* Summary */}
          <HStack mt={6} spacing={4} justify="space-between">
            <Text color="gray.600">
              Showing {filteredAssets.length} of {assets.length} assets
            </Text>
            <Button
              leftIcon={<FiArrowLeft />}
              variant="outline"
              onClick={() => navigate('/asset-dashboard')}
            >
              Back to Dashboard
            </Button>
          </HStack>
        </Box>
      </Container>
    </Box>
  );
};

export default AssetListPage;



