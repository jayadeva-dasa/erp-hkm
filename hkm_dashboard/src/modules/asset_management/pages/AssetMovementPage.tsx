import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Container,
  Heading,
  Button,
  FormControl,
  FormLabel,
  Input,
  Select,
  VStack,
  HStack,
  useToast,
  Text,
  Badge,
  Tag,
  TagLabel,
  TagCloseButton,
  Wrap,
  WrapItem,
} from '@chakra-ui/react';
import { FiSave, FiArrowLeft } from 'react-icons/fi';
import PageHeader from '../../../components/shared/PageHeader';
import apiClient from '../../../services/apiClient';
import { SearchableSelect, SelectOption } from '../../asset_reco/components/SearchableSelect';

interface SelectedAsset {
  id: string;
  name: string;
  asset_name: string;
  status?: string;
  current_sub_custodian?: string;
  current_location?: string;
}

const AssetMovementPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const toast = useToast();
  const [loading, setLoading] = useState(false);
  const [assetOptions, setAssetOptions] = useState<SelectOption[]>([]);
  const [isSearchingAssets, setIsSearchingAssets] = useState(false);
  const [selectedAssets, setSelectedAssets] = useState<SelectedAsset[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const assetSearchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  
  const [formData, setFormData] = useState({
    department: '',
    to_sub_custodian: '',
    to_location: '',
    movement_date: new Date().toISOString().split('T')[0],
    purpose: 'Transfer',
    remarks: '',
  });

  // Initialize with asset from location state if provided
  useEffect(() => {
    const assetId = (location.state as any)?.assetId;
    if (assetId) {
      fetchAssetDetails(assetId).then((asset) => {
        if (asset) {
          setSelectedAssets([asset]);
        }
      });
    }
  }, []);

  useEffect(() => {
    fetchDepartments();
    searchAssets(''); // Load initial assets
  }, []);

  const fetchDepartments = async () => {
    try {
      const deptRes = await apiClient.get('/api/resource/Execution Department', {
        params: {
          fields: JSON.stringify(['name']),
          limit_page_length: 100,
        },
      });
      setDepartments(deptRes.data.data || []);
    } catch (error: any) {
      toast({
        title: 'Error loading departments',
        description: error.message,
        status: 'error',
        duration: 5000,
      });
    }
  };

  const searchAssets = async (searchTerm: string = '') => {
    setIsSearchingAssets(true);
    try {
      const filters: any[] = [
        ['docstatus', '=', 1],
        ['status', 'in', ['Available', 'Submitted', 'Partially Depreciated']]
      ];
      const orFilters: any[] = [];
      
      // Add search filter if search term is provided
      if (searchTerm && searchTerm.trim()) {
        orFilters.push(['name', 'like', `%${searchTerm}%`]);
        orFilters.push(['asset_name', 'like', `%${searchTerm}%`]);
      }
      
      const params: any = {
        fields: JSON.stringify(['name', 'asset_name', 'status', 'current_sub_custodian', 'current_location']),
        filters: JSON.stringify(filters),
        limit_page_length: 50,
        order_by: 'asset_name asc',
      };
      
      // Add or_filters if we have a search term
      if (orFilters.length > 0) {
        params.or_filters = JSON.stringify(orFilters);
      }
      
      const assetsRes = await apiClient.get('/api/resource/HKM Asset', { params });
      
      const assets = assetsRes.data.data || [];
      const options: SelectOption[] = assets
        .filter((asset: any) => !selectedAssets.find(sa => sa.id === asset.name))
        .map((asset: any) => ({
          value: asset.name,
          label: `${asset.name} - ${asset.asset_name || ''}`,
        }));
      
      setAssetOptions(options);
    } catch (error: any) {
      console.error('Error searching assets:', error);
      toast({
        title: 'Error searching assets',
        description: error.message,
        status: 'error',
        duration: 3000,
      });
      setAssetOptions([]);
    } finally {
      setIsSearchingAssets(false);
    }
  };

  const handleAssetSearch = (searchTerm: string) => {
    // Clear previous timeout
    if (assetSearchTimeoutRef.current) {
      clearTimeout(assetSearchTimeoutRef.current);
    }
    
    // Debounce search - wait 300ms after user stops typing
    assetSearchTimeoutRef.current = setTimeout(() => {
      searchAssets(searchTerm);
    }, 300);
  };

  const handleAssetSelect = async (assetId: string) => {
    // Check if asset is already selected
    if (selectedAssets.find(sa => sa.id === assetId)) {
      toast({
        title: 'Asset already selected',
        description: 'This asset is already in the list',
        status: 'warning',
        duration: 3000,
      });
      return;
    }

    try {
      const asset = await fetchAssetDetails(assetId);
      if (asset) {
        setSelectedAssets(prev => [...prev, asset]);
        // Auto-fill department from first asset if not set
        if (!formData.department && asset.current_sub_custodian) {
          // Try to get department from asset
          const assetDoc = await apiClient.get(`/api/resource/HKM Asset/${assetId}`);
          if (assetDoc.data.data.custodian_department) {
            setFormData(prev => ({
              ...prev,
              department: assetDoc.data.data.custodian_department,
            }));
          }
        }
        // Refresh asset options to remove selected asset
        searchAssets('');
      }
    } catch (error: any) {
      toast({
        title: 'Error fetching asset',
        description: error.message,
        status: 'error',
        duration: 5000,
      });
    }
  };

  const handleRemoveAsset = (assetId: string) => {
    setSelectedAssets(prev => prev.filter(sa => sa.id !== assetId));
    // Refresh asset options
    searchAssets('');
  };

  const fetchAssetDetails = async (assetId: string): Promise<SelectedAsset | null> => {
    try {
      const response = await apiClient.get(`/api/resource/HKM Asset/${assetId}`);
      const asset = response.data.data;
      return {
        id: asset.name,
        name: asset.name,
        asset_name: asset.asset_name || '',
        status: asset.status,
        current_sub_custodian: asset.current_sub_custodian,
        current_location: asset.current_location,
      };
    } catch (error: any) {
      toast({
        title: 'Error fetching asset',
        description: error.message,
        status: 'error',
        duration: 5000,
      });
      return null;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (selectedAssets.length === 0) {
      toast({
        title: 'Validation Error',
        description: 'Please select at least one asset',
        status: 'error',
        duration: 3000,
      });
      return;
    }

    if (!formData.department || !formData.to_sub_custodian || !formData.to_location) {
      toast({
        title: 'Validation Error',
        description: 'Please fill all required fields',
        status: 'error',
        duration: 3000,
      });
      return;
    }

    setLoading(true);
    try {
      const createdMovements: string[] = [];
      const errors: string[] = [];

      // Create movement for each selected asset
      for (const asset of selectedAssets) {
        try {
          const response = await apiClient.post('/api/resource/HKM Asset Movement', {
            asset: asset.id,
            department: formData.department,
            to_sub_custodian: formData.to_sub_custodian,
            to_location: formData.to_location,
            movement_date: formData.movement_date,
            purpose: formData.purpose,
            remarks: formData.remarks,
            naming_series: 'HKM-ASS-MOV-.YYYY.-',
          });

          // Get the document first
          const docResponse = await apiClient.get(`/api/resource/HKM Asset Movement/${response.data.data.name}`);
          const doc = docResponse.data.data;

          // Submit the document using Frappe's submit method
          await apiClient.post('/api/method/frappe.client.submit', {
            doc: doc,
          });

          createdMovements.push(response.data.data.name);
        } catch (error: any) {
          errors.push(`${asset.name}: ${error.response?.data?.message || error.message}`);
        }
      }

      if (createdMovements.length > 0) {
        toast({
          title: 'Assets Moved!',
          description: `Successfully created ${createdMovements.length} movement(s)${errors.length > 0 ? ` (${errors.length} error(s))` : ''}`,
          status: errors.length > 0 ? 'warning' : 'success',
          duration: 5000,
        });
        navigate('/asset-dashboard/list');
      } else {
        toast({
          title: 'Error creating movements',
          description: errors.join('; '),
          status: 'error',
          duration: 5000,
        });
      }
    } catch (error: any) {
      toast({
        title: 'Error creating movement',
        description: error.response?.data?.message || error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box minH="100vh" bg="gray.50">
      <PageHeader
        title="Asset Movement"
        subtitle="Transfer asset to new location or custodian"
        onBack={() => navigate('/asset-dashboard')}
      />

      <Container maxW="container.md" py={8}>
        <Box as="form" onSubmit={handleSubmit} bg="white" p={8} borderRadius="xl" shadow="md">
          <VStack spacing={6} align="stretch">
            <FormControl isRequired>
              <FormLabel>Select Asset(s)</FormLabel>
              <SearchableSelect
                options={assetOptions}
                value=""
                onChange={handleAssetSelect}
                onSearch={handleAssetSearch}
                placeholder="Search and select assets to move..."
                isLoading={isSearchingAssets}
                size="md"
                emptyMessage="No assets found. Try a different search term."
              />
              <Text fontSize="sm" color="gray.600" mt={2}>
                You can select multiple assets. Each asset will have its own movement document.
              </Text>
            </FormControl>

            {selectedAssets.length > 0 && (
              <Box>
                <FormLabel mb={2}>Selected Assets ({selectedAssets.length})</FormLabel>
                <Wrap spacing={2}>
                  {selectedAssets.map((asset) => (
                    <WrapItem key={asset.id}>
                      <Tag
                        size="lg"
                        borderRadius="full"
                        variant="solid"
                        colorScheme="blue"
                        px={3}
                        py={2}
                      >
                        <TagLabel>
                          {asset.name} - {asset.asset_name}
                        </TagLabel>
                        <TagCloseButton onClick={() => handleRemoveAsset(asset.id)} />
                      </Tag>
                    </WrapItem>
                  ))}
                </Wrap>
              </Box>
            )}

            {selectedAssets.length > 0 && (
              <Box bg="blue.50" p={4} borderRadius="md">
                <Heading size="sm" mb={2}>Selected Assets Information</Heading>
                <VStack align="stretch" spacing={2} maxH="200px" overflowY="auto">
                  {selectedAssets.map((asset) => (
                    <Box key={asset.id} bg="white" p={3} borderRadius="md" borderWidth="1px" borderColor="blue.200">
                      <Text fontWeight="bold" fontSize="sm" mb={1}>
                        {asset.name} - {asset.asset_name}
                      </Text>
                      <HStack spacing={4} fontSize="xs">
                        <HStack>
                          <Text fontWeight="medium">Status:</Text>
                          <Badge colorScheme="blue" size="sm">{asset.status || 'N/A'}</Badge>
                        </HStack>
                        <HStack>
                          <Text fontWeight="medium">Custodian:</Text>
                          <Text>{asset.current_sub_custodian || '-'}</Text>
                        </HStack>
                        <HStack>
                          <Text fontWeight="medium">Location:</Text>
                          <Text>{asset.current_location || '-'}</Text>
                        </HStack>
                      </HStack>
                    </Box>
                  ))}
                </VStack>
              </Box>
            )}

            <FormControl isRequired>
              <FormLabel>Department</FormLabel>
              <Select
                value={formData.department}
                onChange={(e) => setFormData(prev => ({ ...prev, department: e.target.value }))}
                placeholder="Select department"
              >
                {departments.map((dept) => (
                  <option key={dept.name} value={dept.name}>
                    {dept.name}
                  </option>
                ))}
              </Select>
            </FormControl>

            <FormControl isRequired>
              <FormLabel>To Sub-Custodian</FormLabel>
              <Input
                value={formData.to_sub_custodian}
                onChange={(e) => setFormData(prev => ({ ...prev, to_sub_custodian: e.target.value }))}
                placeholder="Enter new custodian name"
              />
            </FormControl>

            <FormControl isRequired>
              <FormLabel>To Location</FormLabel>
              <Input
                value={formData.to_location}
                onChange={(e) => setFormData(prev => ({ ...prev, to_location: e.target.value }))}
                placeholder="Enter new location"
              />
            </FormControl>

            <FormControl isRequired>
              <FormLabel>Movement Date</FormLabel>
              <Input
                type="date"
                value={formData.movement_date}
                onChange={(e) => setFormData(prev => ({ ...prev, movement_date: e.target.value }))}
              />
            </FormControl>

            <FormControl isRequired>
              <FormLabel>Purpose</FormLabel>
              <Select
                value={formData.purpose}
                onChange={(e) => setFormData(prev => ({ ...prev, purpose: e.target.value }))}
              >
                <option value="Transfer">Transfer</option>
                <option value="Issue">Issue</option>
                <option value="Receipt">Receipt</option>
              </Select>
            </FormControl>

            <FormControl>
              <FormLabel>Remarks</FormLabel>
              <Input
                value={formData.remarks}
                onChange={(e) => setFormData(prev => ({ ...prev, remarks: e.target.value }))}
                placeholder="Any additional notes..."
              />
            </FormControl>

            <HStack spacing={4} justify="flex-end">
              <Button
                leftIcon={<FiArrowLeft />}
                variant="outline"
                onClick={() => navigate('/asset-dashboard')}
              >
                Cancel
              </Button>
              <Button
                leftIcon={<FiSave />}
                colorScheme="purple"
                type="submit"
                isLoading={loading}
              >
                Submit Movement
              </Button>
            </HStack>
          </VStack>
        </Box>
      </Container>
    </Box>
  );
};

export default AssetMovementPage;



