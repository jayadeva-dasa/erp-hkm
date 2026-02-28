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

const SellAssetPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const toast = useToast();
  const [loading, setLoading] = useState(false);
  const [assets, setAssets] = useState<any[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [customers, setCustomers] = useState<any[]>([]);
  const [selectedAsset, setSelectedAsset] = useState<any>(null);
  
  const [formData, setFormData] = useState({
    asset: (location.state as any)?.assetId || '',
    department: '',
    customer: '',
    sale_amount: 0,
    sale_date: new Date().toISOString().split('T')[0],
    justification: '',
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
          fields: JSON.stringify(['name', 'asset_name', 'status', 'custodian_department', 'value_after_depreciation']),
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

      const custRes = await apiClient.get('/api/resource/Customer', {
        params: {
          fields: JSON.stringify(['name', 'customer_name']),
          limit_page_length: 50,
        },
      });
      setCustomers(custRes.data.data || []);
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
        sale_amount: response.data.data.value_after_depreciation || 0,
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
    
    if (!formData.asset || !formData.customer || !formData.sale_amount || !formData.justification) {
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
      const response = await apiClient.post('/api/resource/HKM Asset Sale', {
        ...formData,
        naming_series: 'HKM-SALE-.YYYY.-',
        asset_name: selectedAsset?.asset_name,
      });

      toast({
        title: 'Sale Request Created!',
        description: `Sale request ${response.data.data.name} created. Please submit for approval in ERPNext.`,
        status: 'success',
        duration: 5000,
      });

      window.location.href = `/app/hkm-asset-sale/${response.data.data.name}`;
    } catch (error: any) {
      toast({
        title: 'Error creating sale request',
        description: error.response?.data?.message || error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  const profitLoss = selectedAsset && formData.sale_amount
    ? formData.sale_amount - (selectedAsset.value_after_depreciation || 0)
    : 0;

  return (
    <Box minH="100vh" bg="gray.50">
      <PageHeader
        title="Sell Asset"
        subtitle="Record asset sale with customer details and profit/loss"
        onBack={() => navigate('/asset-dashboard')}
      />

      <Container maxW="container.md" py={8}>
        <Box as="form" onSubmit={handleSubmit} bg="white" p={8} borderRadius="xl" shadow="md">
          <VStack spacing={6} align="stretch">
            <Box bg="orange.50" p={4} borderRadius="md" border="1px" borderColor="orange.200">
              <Text color="orange.700" fontWeight="medium">
                💰 Asset sale will create accounting entries for profit/loss calculation.
                This action requires approval.
              </Text>
            </Box>

            <FormControl isRequired>
              <FormLabel>Select Asset to Sell</FormLabel>
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
                    <Text fontWeight="medium">Current Book Value:</Text>
                    <Text fontWeight="bold">₹{selectedAsset.value_after_depreciation?.toLocaleString()}</Text>
                  </HStack>
                  {profitLoss !== 0 && (
                    <HStack>
                      <Text fontWeight="medium">Expected {profitLoss > 0 ? 'Profit' : 'Loss'}:</Text>
                      <Text fontWeight="bold" color={profitLoss > 0 ? 'green.600' : 'red.600'}>
                        ₹{Math.abs(profitLoss).toLocaleString()}
                      </Text>
                    </HStack>
                  )}
                </VStack>
              </Box>
            )}

            <FormControl isRequired>
              <FormLabel>Customer</FormLabel>
              <Select
                value={formData.customer}
                onChange={(e) => setFormData(prev => ({ ...prev, customer: e.target.value }))}
                placeholder="Select customer"
              >
                {customers.map((customer) => (
                  <option key={customer.name} value={customer.name}>
                    {customer.customer_name}
                  </option>
                ))}
              </Select>
            </FormControl>

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
              <FormLabel>Sale Amount (₹)</FormLabel>
              <NumberInput
                value={formData.sale_amount}
                onChange={(_, value) => setFormData(prev => ({ ...prev, sale_amount: value }))}
              >
                <NumberInputField />
              </NumberInput>
              <Text fontSize="sm" color="gray.500">Enter the agreed sale price</Text>
            </FormControl>

            <FormControl isRequired>
              <FormLabel>Sale Date</FormLabel>
              <Input
                type="date"
                value={formData.sale_date}
                onChange={(e) => setFormData(prev => ({ ...prev, sale_date: e.target.value }))}
              />
            </FormControl>

            <FormControl isRequired>
              <FormLabel>Justification</FormLabel>
              <Textarea
                value={formData.justification}
                onChange={(e) => setFormData(prev => ({ ...prev, justification: e.target.value }))}
                placeholder="Enter reason for selling this asset (upgrading, no longer needed, etc.)"
                rows={4}
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
                colorScheme="orange"
                type="submit"
                isLoading={loading}
              >
                Create Sale Request
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

export default SellAssetPage;




