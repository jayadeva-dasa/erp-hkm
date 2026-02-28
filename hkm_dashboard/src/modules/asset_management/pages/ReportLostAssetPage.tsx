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
  Checkbox,
  VStack,
  HStack,
  useToast,
  Text,
  Badge,
} from '@chakra-ui/react';
import { FiSave, FiArrowLeft } from 'react-icons/fi';
import PageHeader from '../../../components/shared/PageHeader';
import apiClient from '../../../services/apiClient';

const ReportLostAssetPage: React.FC = () => {
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
    lost_date: new Date().toISOString().split('T')[0],
    incident_details: '',
    fir_filed: false,
    fir_number: '',
    recovery_possible: false,
    insurance_claim_filed: false,
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
    
    if (!formData.asset || !formData.department || !formData.incident_details) {
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
      const response = await apiClient.post('/api/resource/HKM Asset Lost', {
        ...formData,
        naming_series: 'HKM-LOST-.YYYY.-',
        asset_name: selectedAsset?.asset_name,
        reported_by: window.frappe?.session?.user || '',
      });

      toast({
        title: 'Lost Asset Report Created!',
        description: `Report ${response.data.data.name} created. Please submit for approval in ERPNext.`,
        status: 'success',
        duration: 5000,
      });

      window.location.href = `/app/hkm-asset-lost/${response.data.data.name}`;
    } catch (error: any) {
      toast({
        title: 'Error creating lost asset report',
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
        title="Report Lost Asset"
        subtitle="Report and process lost assets with incident details"
        onBack={() => navigate('/asset-dashboard')}
      />

      <Container maxW="container.md" py={8}>
        <Box as="form" onSubmit={handleSubmit} bg="white" p={8} borderRadius="xl" shadow="md">
          <VStack spacing={6} align="stretch">
            <Box bg="red.50" p={4} borderRadius="md" border="1px" borderColor="red.200">
              <Text color="red.700" fontWeight="medium">
                ⚠️ Critical: Reporting an asset as lost will write off its value.
                Please ensure all recovery attempts have been exhausted. This requires high-level approval.
              </Text>
            </Box>

            <FormControl isRequired>
              <FormLabel>Select Lost Asset</FormLabel>
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
                    <Text fontWeight="medium">Book Value (to be written off):</Text>
                    <Text fontWeight="bold" color="red.600">
                      ₹{selectedAsset.value_after_depreciation?.toLocaleString()}
                    </Text>
                  </HStack>
                  <HStack>
                    <Text fontWeight="medium">Last Known Custodian:</Text>
                    <Text>{selectedAsset.current_sub_custodian || '-'}</Text>
                  </HStack>
                  <HStack>
                    <Text fontWeight="medium">Last Known Location:</Text>
                    <Text>{selectedAsset.current_location || '-'}</Text>
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
              <FormLabel>Date When Loss Was Discovered</FormLabel>
              <Input
                type="date"
                value={formData.lost_date}
                onChange={(e) => setFormData(prev => ({ ...prev, lost_date: e.target.value }))}
              />
            </FormControl>

            <FormControl isRequired>
              <FormLabel>Incident Details</FormLabel>
              <Textarea
                value={formData.incident_details}
                onChange={(e) => setFormData(prev => ({ ...prev, incident_details: e.target.value }))}
                placeholder="Describe the circumstances of the loss (when, where, how it was discovered missing, etc.)"
                rows={6}
              />
            </FormControl>

            <FormControl>
              <Checkbox
                isChecked={formData.fir_filed}
                onChange={(e) => setFormData(prev => ({ ...prev, fir_filed: e.target.checked }))}
              >
                FIR Filed with Police
              </Checkbox>
            </FormControl>

            {formData.fir_filed && (
              <FormControl>
                <FormLabel>FIR Number</FormLabel>
                <Input
                  value={formData.fir_number}
                  onChange={(e) => setFormData(prev => ({ ...prev, fir_number: e.target.value }))}
                  placeholder="Enter FIR number"
                />
              </FormControl>
            )}

            <FormControl>
              <Checkbox
                isChecked={formData.recovery_possible}
                onChange={(e) => setFormData(prev => ({ ...prev, recovery_possible: e.target.checked }))}
              >
                Recovery Possible
              </Checkbox>
              <Text fontSize="sm" color="gray.500" mt={1}>
                Check if there's a reasonable chance of recovering the asset
              </Text>
            </FormControl>

            <FormControl>
              <Checkbox
                isChecked={formData.insurance_claim_filed}
                onChange={(e) => setFormData(prev => ({ ...prev, insurance_claim_filed: e.target.checked }))}
              >
                Insurance Claim Filed
              </Checkbox>
              <Text fontSize="sm" color="gray.500" mt={1}>
                Check if asset was insured and claim has been filed
              </Text>
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
                Create Lost Asset Report
              </Button>
            </HStack>

            <Text fontSize="sm" color="gray.500">
              * After creating, the report will open in ERPNext where you can submit it for management and accounts approval
            </Text>
          </VStack>
        </Box>
      </Container>
    </Box>
  );
};

export default ReportLostAssetPage;




