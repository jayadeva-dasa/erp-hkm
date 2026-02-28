import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Container,
  Heading,
  Button,
  FormControl,
  FormLabel,
  Input,
  Textarea,
  Select,
  VStack,
  HStack,
  useToast,
  Text,
  Badge,
  NumberInput,
  NumberInputField,
} from '@chakra-ui/react';
import { FiSave, FiArrowLeft } from 'react-icons/fi';
import PageHeader from '../../../components/shared/PageHeader';
import apiClient from '../../../services/apiClient';

const ScrapAssetPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const toast = useToast();
  const [loading, setLoading] = useState(false);
  const [assets, setAssets] = useState<any[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [selectedAsset, setSelectedAsset] = useState<any>(null);
  
  const [formData, setFormData] = useState({
    asset: (location.state as any)?.assetId || '',
    department: '',
    scrap_date: new Date().toISOString().split('T')[0],
    scrap_reason: '',
    estimated_scrap_value: 0,
    workflow_state: 'Draft',
  });

  useEffect(() => {
    fetchMasterData();
  }, []);

  useEffect(() => {
    if (formData.asset) {
      fetchAssetDetails(formData.asset);
    }
  }, [formData.asset]);

  const fetchMasterData = async () => {
    try {
      const assetsRes = await apiClient.get('/api/resource/HKM Asset', {
        params: {
          fields: JSON.stringify(['name', 'asset_name', 'status', 'custodian_department']),
          filters: JSON.stringify([['docstatus', '=', 1], ['status', 'not in', ['Scrapped', 'Sold', 'Lost']]]),
          limit_page_length: 100,
        },
      });
      setAssets(assetsRes.data.data || []);

      const deptRes = await apiClient.get('/api/resource/Execution Department', {
        params: {
          fields: JSON.stringify(['name']),
          limit_page_length: 100,
        },
      });
      setDepartments(deptRes.data.data || []);
    } catch (error: any) {
      toast({
        title: 'Error loading data',
        description: error.message,
        status: 'error',
        duration: 5000,
      });
    }
  };

  const fetchAssetDetails = async (assetId: string) => {
    try {
      const response = await apiClient.get(`/api/resource/HKM Asset/${assetId}`);
      setSelectedAsset(response.data.data);
      setFormData(prev => ({
        ...prev,
        department: response.data.data.custodian_department || '',
      }));
    } catch (error: any) {
      toast({
        title: 'Error fetching asset',
        description: error.message,
        status: 'error',
        duration: 5000,
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.asset || !formData.department || !formData.scrap_reason) {
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
      const response = await apiClient.post('/api/resource/HKM Asset Scrap', {
        ...formData,
        naming_series: 'HKM-SCR-.YYYY.-',
        asset_name: selectedAsset?.asset_name,
      });

      toast({
        title: 'Scrap Request Created!',
        description: `Scrap request ${response.data.data.name} created. Please submit for approval in ERPNext.`,
        status: 'success',
        duration: 5000,
      });

      // Open in ERPNext for approval workflow
      window.location.href = `/app/hkm-asset-scrap/${response.data.data.name}`;
    } catch (error: any) {
      toast({
        title: 'Error creating scrap request',
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
        title="Scrap Asset"
        subtitle="Process asset scrapping with approval workflow"
        onBack={() => navigate('/asset-dashboard')}
      />

      <Container maxW="container.md" py={8}>
        <Box as="form" onSubmit={handleSubmit} bg="white" p={8} borderRadius="xl" shadow="md">
          <VStack spacing={6} align="stretch">
            <Box bg="red.50" p={4} borderRadius="md" border="1px" borderColor="red.200">
              <Text color="red.700" fontWeight="medium">
                ⚠️ Warning: Scrapping an asset will remove it from active use and create accounting entries.
                This action requires approval.
              </Text>
            </Box>

            <FormControl isRequired>
              <FormLabel>Select Asset to Scrap</FormLabel>
              <Select
                value={formData.asset}
                onChange={(e) => setFormData(prev => ({ ...prev, asset: e.target.value }))}
                placeholder="Select asset"
              >
                {assets.map((asset) => (
                  <option key={asset.name} value={asset.name}>
                    {asset.name} - {asset.asset_name}
                  </option>
                ))}
              </Select>
            </FormControl>

            {selectedAsset && (
              <Box bg="blue.50" p={4} borderRadius="md">
                <Heading size="sm" mb={2}>Asset Information</Heading>
                <VStack align="stretch" spacing={1}>
                  <HStack>
                    <Text fontWeight="medium">Status:</Text>
                    <Badge colorScheme="blue">{selectedAsset.status}</Badge>
                  </HStack>
                  <HStack>
                    <Text fontWeight="medium">Current Value:</Text>
                    <Text>₹{selectedAsset.value_after_depreciation?.toLocaleString()}</Text>
                  </HStack>
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
              <FormLabel>Scrap Date</FormLabel>
              <Input
                type="date"
                value={formData.scrap_date}
                onChange={(e) => setFormData(prev => ({ ...prev, scrap_date: e.target.value }))}
              />
            </FormControl>

            <FormControl isRequired>
              <FormLabel>Scrap Reason</FormLabel>
              <Textarea
                value={formData.scrap_reason}
                onChange={(e) => setFormData(prev => ({ ...prev, scrap_reason: e.target.value }))}
                placeholder="Enter reason for scrapping this asset (damaged, obsolete, etc.)"
                rows={4}
              />
            </FormControl>

            <FormControl>
              <FormLabel>Estimated Scrap Value (₹)</FormLabel>
              <NumberInput
                value={formData.estimated_scrap_value}
                onChange={(_, value) => setFormData(prev => ({ ...prev, estimated_scrap_value: value }))}
              >
                <NumberInputField />
              </NumberInput>
              <Text fontSize="sm" color="gray.500">Any expected recovery value from scrap</Text>
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
                colorScheme="red"
                type="submit"
                isLoading={loading}
              >
                Create Scrap Request
              </Button>
            </HStack>

            <Text fontSize="sm" color="gray.500">
              * After creating, the request will open in ERPNext where you can submit it for approval workflow
            </Text>
          </VStack>
        </Box>
      </Container>
    </Box>
  );
};

export default ScrapAssetPage;




