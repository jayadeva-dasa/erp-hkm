import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Heading,
  Button,
  VStack,
  HStack,
  useToast,
  Text,
  Badge,
  Spinner,
  FormControl,
  FormLabel,
  Select,
  Divider,
  Card,
  CardBody,
  CardHeader,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  IconButton,
  useColorModeValue,
} from '@chakra-ui/react';
import { FiArrowLeft, FiFilter, FiX } from 'react-icons/fi';
import PageHeader from '../../../components/shared/PageHeader';
import apiClient from '../../../services/apiClient';
import { SearchableSelect, SelectOption } from '../../asset_reco/components/SearchableSelect';

interface AssetMovement {
  name: string;
  asset: string;
  asset_name: string;
  department: string;
  movement_date: string;
  purpose: string;
  from_sub_custodian: string;
  from_location: string;
  to_sub_custodian: string;
  to_location: string;
  remarks: string;
  docstatus: number;
  modified: string;
  modified_by: string;
}

interface GroupedMovement {
  asset: string;
  asset_name: string;
  movements: AssetMovement[];
}

const AssetMovementsHistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [movements, setMovements] = useState<AssetMovement[]>([]);
  const [groupedMovements, setGroupedMovements] = useState<GroupedMovement[]>([]);
  const [selectedAsset, setSelectedAsset] = useState<string>('');
  const [assetOptions, setAssetOptions] = useState<SelectOption[]>([]);
  const [isSearchingAssets, setIsSearchingAssets] = useState(false);
  const assetSearchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const cardBg = useColorModeValue('white', 'gray.800');

  useEffect(() => {
    searchAssets(''); // Load initial assets
  }, []);

  useEffect(() => {
    fetchMovements();
  }, [selectedAsset]);

  useEffect(() => {
    groupMovementsByAsset();
  }, [movements, selectedAsset]);

  const searchAssets = async (searchTerm: string = '') => {
    setIsSearchingAssets(true);
    try {
      const filters: any[] = [['docstatus', '=', 1]];
      const orFilters: any[] = [];
      
      if (searchTerm && searchTerm.trim()) {
        orFilters.push(['name', 'like', `%${searchTerm}%`]);
        orFilters.push(['asset_name', 'like', `%${searchTerm}%`]);
      }
      
      const params: any = {
        fields: JSON.stringify(['name', 'asset_name']),
        filters: JSON.stringify(filters),
        limit_page_length: 100,
        order_by: 'asset_name asc',
      };
      
      if (orFilters.length > 0) {
        params.or_filters = JSON.stringify(orFilters);
      }
      
      const assetsRes = await apiClient.get('/api/resource/HKM Asset', { params });
      const assets = assetsRes.data.data || [];
      const options: SelectOption[] = [
        { value: '', label: 'All Assets' },
        ...assets.map((asset: any) => ({
          value: asset.name,
          label: `${asset.name} - ${asset.asset_name || ''}`,
        })),
      ];
      
      setAssetOptions(options);
    } catch (error: any) {
      console.error('Error searching assets:', error);
      setAssetOptions([{ value: '', label: 'All Assets' }]);
    } finally {
      setIsSearchingAssets(false);
    }
  };

  const handleAssetSearch = (searchTerm: string) => {
    if (assetSearchTimeoutRef.current) {
      clearTimeout(assetSearchTimeoutRef.current);
    }
    
    assetSearchTimeoutRef.current = setTimeout(() => {
      searchAssets(searchTerm);
    }, 300);
  };

  const fetchMovements = async () => {
    try {
      setLoading(true);
      const filters: any[] = [['docstatus', '=', 1]]; // Only submitted movements
      
      if (selectedAsset) {
        filters.push(['asset', '=', selectedAsset]);
      }
      
      const response = await apiClient.get('/api/resource/HKM Asset Movement', {
        params: {
          fields: JSON.stringify([
            'name',
            'asset',
            'asset_name',
            'department',
            'movement_date',
            'purpose',
            'from_sub_custodian',
            'from_location',
            'to_sub_custodian',
            'to_location',
            'remarks',
            'docstatus',
            'modified',
            'modified_by',
          ]),
          filters: JSON.stringify(filters),
          limit_page_length: 1000,
          order_by: 'movement_date desc, modified desc',
        },
      });
      
      setMovements(response.data.data || []);
    } catch (error: any) {
      toast({
        title: 'Error fetching movements',
        description: error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  const groupMovementsByAsset = () => {
    const filtered = selectedAsset
      ? movements.filter(m => m.asset === selectedAsset)
      : movements;

    const grouped: { [key: string]: GroupedMovement } = {};

    filtered.forEach((movement) => {
      if (!grouped[movement.asset]) {
        grouped[movement.asset] = {
          asset: movement.asset,
          asset_name: movement.asset_name || movement.asset,
          movements: [],
        };
      }
      grouped[movement.asset].movements.push(movement);
    });

    // Sort movements within each group by date (newest first)
    Object.values(grouped).forEach((group) => {
      group.movements.sort((a, b) => {
        const dateA = new Date(a.movement_date).getTime();
        const dateB = new Date(b.movement_date).getTime();
        if (dateA !== dateB) return dateB - dateA;
        return new Date(b.modified).getTime() - new Date(a.modified).getTime();
      });
    });

    // Sort groups by asset name
    const sorted = Object.values(grouped).sort((a, b) =>
      a.asset_name.localeCompare(b.asset_name)
    );

    setGroupedMovements(sorted);
  };

  const handleAssetFilterChange = (value: string) => {
    setSelectedAsset(value);
    // Movements will be refetched via useEffect when selectedAsset changes
  };

  const getPurposeColor = (purpose: string) => {
    const colors: Record<string, string> = {
      Transfer: 'blue',
      Issue: 'orange',
      Receipt: 'green',
    };
    return colors[purpose] || 'gray';
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  };

  return (
    <Box minH="100vh" bg="gray.50">
      <PageHeader
        title="Asset Movements History"
        subtitle="View complete history of all asset movements and transfers"
        onBack={() => navigate('/asset-dashboard')}
      />

      <Container maxW="container.xl" py={8}>
        {/* Filter Section */}
        <Card bg={cardBg} mb={6} shadow="md">
          <CardHeader>
            <HStack justify="space-between" align="center">
              <Heading size="md">Filter Movements</Heading>
              <HStack>
                <FiFilter />
                <Text fontSize="sm" color="gray.600">
                  Filter by Asset
                </Text>
              </HStack>
            </HStack>
          </CardHeader>
          <CardBody>
            <FormControl>
              <FormLabel>Select Asset</FormLabel>
              <HStack>
                <Box flex={1}>
                  <SearchableSelect
                    options={assetOptions}
                    value={selectedAsset}
                    onChange={handleAssetFilterChange}
                    onSearch={handleAssetSearch}
                    placeholder="Select asset to filter (or leave empty for all)"
                    isLoading={isSearchingAssets}
                    size="md"
                    emptyMessage="No assets found"
                  />
                </Box>
                {selectedAsset && (
                  <IconButton
                    aria-label="Clear filter"
                    icon={<FiX />}
                    onClick={() => {
                      setSelectedAsset('');
                      fetchMovements();
                    }}
                    variant="outline"
                  />
                )}
              </HStack>
              <Text fontSize="sm" color="gray.600" mt={2}>
                {selectedAsset
                  ? `Showing movements for selected asset only`
                  : `Showing all asset movements`}
              </Text>
            </FormControl>
          </CardBody>
        </Card>

        {/* Movements List */}
        {loading ? (
          <Box textAlign="center" py={10}>
            <Spinner size="xl" color="blue.500" thickness="3px" />
            <Text mt={4} color="gray.600">
              Loading movements...
            </Text>
          </Box>
        ) : groupedMovements.length === 0 ? (
          <Card bg={cardBg} shadow="md">
            <CardBody textAlign="center" py={10}>
              <Text fontSize="lg" color="gray.500">
                No movements found
              </Text>
              <Text fontSize="sm" color="gray.400" mt={2}>
                {selectedAsset
                  ? 'No movements found for the selected asset'
                  : 'No asset movements have been recorded yet'}
              </Text>
            </CardBody>
          </Card>
        ) : (
          <VStack spacing={6} align="stretch">
            {groupedMovements.map((group) => (
              <Card key={group.asset} bg={cardBg} shadow="md">
                <CardHeader bg="blue.50" borderTopRadius="md">
                  <HStack justify="space-between">
                    <VStack align="start" spacing={1}>
                      <Heading size="md" color="blue.700">
                        {group.asset}
                      </Heading>
                      <Text fontSize="sm" color="gray.600">
                        {group.asset_name}
                      </Text>
                    </VStack>
                    <Badge colorScheme="blue" fontSize="md" px={3} py={1}>
                      {group.movements.length} Movement{group.movements.length !== 1 ? 's' : ''}
                    </Badge>
                  </HStack>
                </CardHeader>
                <CardBody>
                  <Box overflowX="auto">
                    <Table variant="simple" size="sm">
                      <Thead>
                        <Tr>
                          <Th>Date</Th>
                          <Th>Purpose</Th>
                          <Th>Department</Th>
                          <Th>From</Th>
                          <Th>To</Th>
                          <Th>Remarks</Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        {group.movements.map((movement) => (
                          <Tr key={movement.name} _hover={{ bg: 'gray.50' }}>
                            <Td fontWeight="medium">
                              {formatDate(movement.movement_date)}
                            </Td>
                            <Td>
                              <Badge colorScheme={getPurposeColor(movement.purpose)}>
                                {movement.purpose}
                              </Badge>
                            </Td>
                            <Td>{movement.department || '-'}</Td>
                            <Td>
                              <VStack align="start" spacing={0}>
                                <Text fontSize="xs" color="gray.600">
                                  Custodian:
                                </Text>
                                <Text fontSize="sm" fontWeight="medium">
                                  {movement.from_sub_custodian || '-'}
                                </Text>
                                <Text fontSize="xs" color="gray.600" mt={1}>
                                  Location:
                                </Text>
                                <Text fontSize="sm">
                                  {movement.from_location || '-'}
                                </Text>
                              </VStack>
                            </Td>
                            <Td>
                              <VStack align="start" spacing={0}>
                                <Text fontSize="xs" color="gray.600">
                                  Custodian:
                                </Text>
                                <Text fontSize="sm" fontWeight="medium" color="green.600">
                                  {movement.to_sub_custodian || '-'}
                                </Text>
                                <Text fontSize="xs" color="gray.600" mt={1}>
                                  Location:
                                </Text>
                                <Text fontSize="sm" color="green.600">
                                  {movement.to_location || '-'}
                                </Text>
                              </VStack>
                            </Td>
                            <Td>
                              <Text fontSize="sm" color="gray.600" noOfLines={2}>
                                {movement.remarks || '-'}
                              </Text>
                            </Td>
                          </Tr>
                        ))}
                      </Tbody>
                    </Table>
                  </Box>
                </CardBody>
              </Card>
            ))}
          </VStack>
        )}

        {/* Back Button */}
        <Box mt={6} textAlign="center">
          <Button
            leftIcon={<FiArrowLeft />}
            variant="outline"
            onClick={() => navigate('/asset-dashboard')}
          >
            Back to Dashboard
          </Button>
        </Box>
      </Container>
    </Box>
  );
};

export default AssetMovementsHistoryPage;

