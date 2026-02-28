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
  Input,
  Select,
  Checkbox,
  Textarea,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  IconButton,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  useColorModeValue,
  Card,
  CardBody,
  CardHeader,
  Divider,
} from '@chakra-ui/react';
import { FiArrowLeft, FiPlus, FiEdit, FiTrash2, FiX } from 'react-icons/fi';
import PageHeader from '../../../components/shared/PageHeader';
import apiClient from '../../../services/apiClient';
import { SearchableSelect, SelectOption } from '../../asset_reco/components/SearchableSelect';

interface AssetSpecification {
  name: string;
  specification_name: string;
  asset_category: string;
  data_type: 'Text' | 'Number' | 'Select' | 'Date' | 'Checkbox';
  options?: string;
  is_mandatory: boolean;
  description?: string;
}

const AssetSpecificationsPage: React.FC = () => {
  const navigate = useNavigate();
  const toast = useToast();
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [loading, setLoading] = useState(true);
  const [specifications, setSpecifications] = useState<AssetSpecification[]>([]);
  const [assetCategories, setAssetCategories] = useState<SelectOption[]>([]);
  const [isSearchingCategories, setIsSearchingCategories] = useState(false);
  const [editingSpec, setEditingSpec] = useState<AssetSpecification | null>(null);
  const categorySearchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const cardBg = useColorModeValue('white', 'gray.800');

  const [formData, setFormData] = useState({
    specification_name: '',
    asset_category: '',
    data_type: 'Text' as AssetSpecification['data_type'],
    options: '',
    is_mandatory: false,
    description: '',
  });
  const [optionFields, setOptionFields] = useState<string[]>(['']);

  useEffect(() => {
    fetchSpecifications();
    searchAssetCategories('');
  }, []);

  const searchAssetCategories = async (searchTerm: string = '') => {
    setIsSearchingCategories(true);
    try {
      const filters: any[] = [];
      const orFilters: any[] = [];
      
      if (searchTerm && searchTerm.trim()) {
        orFilters.push(['name', 'like', `%${searchTerm}%`]);
      }
      
      const params: any = {
        fields: JSON.stringify(['name']),
        filters: filters.length > 0 ? JSON.stringify(filters) : undefined,
        limit_page_length: 100,
        order_by: 'name asc',
      };
      
      if (orFilters.length > 0) {
        params.or_filters = JSON.stringify(orFilters);
      }
      
      const catRes = await apiClient.get('/api/resource/Asset Category', { params });
      const categories = catRes.data.data || [];
      const options: SelectOption[] = categories.map((cat: any) => ({
        value: cat.name,
        label: cat.name,
      }));
      
      setAssetCategories(options);
    } catch (error: any) {
      console.error('Error searching asset categories:', error);
      setAssetCategories([]);
    } finally {
      setIsSearchingCategories(false);
    }
  };

  const handleCategorySearch = (searchTerm: string) => {
    if (categorySearchTimeoutRef.current) {
      clearTimeout(categorySearchTimeoutRef.current);
    }
    
    categorySearchTimeoutRef.current = setTimeout(() => {
      searchAssetCategories(searchTerm);
    }, 300);
  };

  const fetchSpecifications = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/api/resource/HKM Asset Specification', {
        params: {
          fields: JSON.stringify([
            'name',
            'specification_name',
            'asset_category',
            'data_type',
            'options',
            'is_mandatory',
            'description',
          ]),
          limit_page_length: 1000,
          order_by: 'asset_category asc, specification_name asc',
        },
      });
      setSpecifications(response.data.data || []);
    } catch (error: any) {
      toast({
        title: 'Error fetching specifications',
        description: error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleOpenCreate = () => {
    setEditingSpec(null);
    setFormData({
      specification_name: '',
      asset_category: '',
      data_type: 'Text',
      options: '',
      is_mandatory: false,
      description: '',
    });
    setOptionFields(['']);
    onOpen();
  };

  const handleOpenEdit = (spec: AssetSpecification) => {
    setEditingSpec(spec);
    setFormData({
      specification_name: spec.specification_name,
      asset_category: spec.asset_category,
      data_type: spec.data_type,
      options: spec.options || '',
      is_mandatory: spec.is_mandatory || false,
      description: spec.description || '',
    });
    // Split comma-separated options into array
    if (spec.data_type === 'Select' && spec.options) {
      const options = spec.options.split(',').map(opt => opt.trim()).filter(opt => opt);
      setOptionFields(options.length > 0 ? options : ['']);
    } else {
      setOptionFields(['']);
    }
    onOpen();
  };

  const handleAddOption = () => {
    setOptionFields([...optionFields, '']);
  };

  const handleRemoveOption = (index: number) => {
    if (optionFields.length > 1) {
      const newFields = optionFields.filter((_, i) => i !== index);
      setOptionFields(newFields);
    }
  };

  const handleOptionChange = (index: number, value: string) => {
    const newFields = [...optionFields];
    newFields[index] = value;
    setOptionFields(newFields);
  };

  const handleSubmit = async () => {
    // Validation
    if (!formData.specification_name.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Specification name is required',
        status: 'error',
        duration: 3000,
      });
      return;
    }

    if (!formData.asset_category) {
      toast({
        title: 'Validation Error',
        description: 'Asset category is required',
        status: 'error',
        duration: 3000,
      });
      return;
    }

    if (formData.data_type === 'Select') {
      const validOptions = optionFields.filter(opt => opt.trim());
      if (validOptions.length === 0) {
        toast({
          title: 'Validation Error',
          description: 'At least one option is required for Select data type',
          status: 'error',
          duration: 3000,
        });
        return;
      }
    }

    try {
      const payload: any = {
        specification_name: formData.specification_name.trim(),
        asset_category: formData.asset_category,
        data_type: formData.data_type,
        is_mandatory: formData.is_mandatory ? 1 : 0,
        description: formData.description.trim() || '',
      };

      if (formData.data_type === 'Select') {
        // Combine all non-empty options with commas
        const validOptions = optionFields.filter(opt => opt.trim());
        payload.options = validOptions.map(opt => opt.trim()).join(', ');
      }

      if (editingSpec) {
        // Update existing
        await apiClient.put(`/api/resource/HKM Asset Specification/${editingSpec.name}`, payload);
        toast({
          title: 'Specification Updated',
          description: 'Asset specification has been updated successfully',
          status: 'success',
          duration: 5000,
        });
      } else {
        // Create new
        await apiClient.post('/api/resource/HKM Asset Specification', payload);
        toast({
          title: 'Specification Created',
          description: 'Asset specification has been created successfully',
          status: 'success',
          duration: 5000,
        });
      }

      onClose();
      fetchSpecifications();
    } catch (error: any) {
      toast({
        title: editingSpec ? 'Error updating specification' : 'Error creating specification',
        description: error.response?.data?.message || error.message,
        status: 'error',
        duration: 5000,
      });
    }
  };

  const handleDelete = async (spec: AssetSpecification) => {
    if (!window.confirm(`Are you sure you want to delete "${spec.specification_name}"?`)) {
      return;
    }

    try {
      await apiClient.delete(`/api/resource/HKM Asset Specification/${spec.name}`);
      toast({
        title: 'Specification Deleted',
        description: 'Asset specification has been deleted successfully',
        status: 'success',
        duration: 5000,
      });
      fetchSpecifications();
    } catch (error: any) {
      toast({
        title: 'Error deleting specification',
        description: error.response?.data?.message || error.message,
        status: 'error',
        duration: 5000,
      });
    }
  };

  const getDataTypeColor = (dataType: string) => {
    const colors: Record<string, string> = {
      Text: 'blue',
      Number: 'green',
      Select: 'purple',
      Date: 'orange',
      Checkbox: 'pink',
    };
    return colors[dataType] || 'gray';
  };

  // Group specifications by asset category
  const groupedSpecs = specifications.reduce((acc, spec) => {
    const category = spec.asset_category || 'Uncategorized';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(spec);
    return acc;
  }, {} as Record<string, AssetSpecification[]>);

  return (
    <Box minH="100vh" bg="gray.50">
      <PageHeader
        title="Asset Specifications"
        subtitle="Manage asset specification templates for different categories"
        onBack={() => navigate('/asset-dashboard')}
      />

      <Container maxW="container.xl" py={8}>
        {/* Action Bar */}
        <Card bg={cardBg} mb={6} shadow="md">
          <CardBody>
            <HStack justify="space-between">
              <Heading size="md">Specifications</Heading>
              <Button
                leftIcon={<FiPlus />}
                colorScheme="green"
                onClick={handleOpenCreate}
              >
                Create Specification
              </Button>
            </HStack>
          </CardBody>
        </Card>

        {/* Specifications List */}
        {loading ? (
          <Box textAlign="center" py={10}>
            <Spinner size="xl" color="blue.500" thickness="3px" />
            <Text mt={4} color="gray.600">
              Loading specifications...
            </Text>
          </Box>
        ) : specifications.length === 0 ? (
          <Card bg={cardBg} shadow="md">
            <CardBody textAlign="center" py={10}>
              <Text fontSize="lg" color="gray.500">
                No specifications found
              </Text>
              <Text fontSize="sm" color="gray.400" mt={2}>
                Create your first asset specification to get started
              </Text>
              <Button
                leftIcon={<FiPlus />}
                colorScheme="green"
                mt={4}
                onClick={handleOpenCreate}
              >
                Create Specification
              </Button>
            </CardBody>
          </Card>
        ) : (
          <VStack spacing={6} align="stretch">
            {Object.entries(groupedSpecs).map(([category, specs]) => (
              <Card key={category} bg={cardBg} shadow="md">
                <CardHeader bg="blue.50" borderTopRadius="md">
                  <HStack justify="space-between">
                    <Heading size="md" color="blue.700">
                      {category}
                    </Heading>
                    <Badge colorScheme="blue" fontSize="md" px={3} py={1}>
                      {specs.length} Specification{specs.length !== 1 ? 's' : ''}
                    </Badge>
                  </HStack>
                </CardHeader>
                <CardBody>
                  <Box overflowX="auto">
                    <Table variant="simple" size="sm">
                      <Thead>
                        <Tr>
                          <Th>Specification Name</Th>
                          <Th>Data Type</Th>
                          <Th>Options</Th>
                          <Th>Mandatory</Th>
                          <Th>Description</Th>
                          <Th>Actions</Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        {specs.map((spec) => (
                          <Tr key={spec.name} _hover={{ bg: 'gray.50' }}>
                            <Td fontWeight="medium">{spec.specification_name}</Td>
                            <Td>
                              <Badge colorScheme={getDataTypeColor(spec.data_type)}>
                                {spec.data_type}
                              </Badge>
                            </Td>
                            <Td>
                              <Text fontSize="sm" color="gray.600" noOfLines={2}>
                                {spec.data_type === 'Select' ? spec.options || '-' : '-'}
                              </Text>
                            </Td>
                            <Td>
                              {spec.is_mandatory ? (
                                <Badge colorScheme="red">Required</Badge>
                              ) : (
                                <Badge colorScheme="gray">Optional</Badge>
                              )}
                            </Td>
                            <Td>
                              <Text fontSize="sm" color="gray.600" noOfLines={2}>
                                {spec.description || '-'}
                              </Text>
                            </Td>
                            <Td>
                              <HStack spacing={2}>
                                <IconButton
                                  aria-label="Edit specification"
                                  icon={<FiEdit />}
                                  size="sm"
                                  colorScheme="blue"
                                  variant="ghost"
                                  onClick={() => handleOpenEdit(spec)}
                                />
                                <IconButton
                                  aria-label="Delete specification"
                                  icon={<FiTrash2 />}
                                  size="sm"
                                  colorScheme="red"
                                  variant="ghost"
                                  onClick={() => handleDelete(spec)}
                                />
                              </HStack>
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

        {/* Create/Edit Modal */}
        <Modal isOpen={isOpen} onClose={onClose} size="xl">
          <ModalOverlay />
          <ModalContent>
            <ModalHeader>
              {editingSpec ? 'Edit Specification' : 'Create Specification'}
            </ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              <VStack spacing={4} align="stretch">
                <FormControl isRequired>
                  <FormLabel>Specification Name</FormLabel>
                  <Input
                    value={formData.specification_name}
                    onChange={(e) =>
                      setFormData({ ...formData, specification_name: e.target.value })
                    }
                    placeholder="e.g., Serial Number, Model, Warranty Period"
                  />
                </FormControl>

                <FormControl isRequired>
                  <FormLabel>Asset Category</FormLabel>
                  <SearchableSelect
                    options={assetCategories}
                    value={formData.asset_category}
                    onChange={(value) =>
                      setFormData({ ...formData, asset_category: value })
                    }
                    onSearch={handleCategorySearch}
                    placeholder="Search and select asset category"
                    isLoading={isSearchingCategories}
                    size="md"
                    emptyMessage="No asset categories found"
                  />
                </FormControl>

                <FormControl isRequired>
                  <FormLabel>Data Type</FormLabel>
                  <Select
                    value={formData.data_type}
                    onChange={(e) => {
                      const newDataType = e.target.value as AssetSpecification['data_type'];
                      setFormData({
                        ...formData,
                        data_type: newDataType,
                      });
                      // Reset options when changing data type
                      if (newDataType !== 'Select') {
                        setOptionFields(['']);
                      } else if (optionFields.length === 0 || (optionFields.length === 1 && !optionFields[0])) {
                        setOptionFields(['']);
                      }
                    }}
                  >
                    <option value="Text">Text</option>
                    <option value="Number">Number</option>
                    <option value="Select">Select</option>
                    <option value="Date">Date</option>
                    <option value="Checkbox">Checkbox</option>
                  </Select>
                </FormControl>

                {formData.data_type === 'Select' && (
                  <FormControl isRequired>
                    <FormLabel>Options</FormLabel>
                    <VStack spacing={2} align="stretch">
                      {optionFields.map((option, index) => (
                        <HStack key={index} spacing={2}>
                          <Input
                            value={option}
                            onChange={(e) => handleOptionChange(index, e.target.value)}
                            placeholder={`Option ${index + 1}`}
                            flex={1}
                          />
                          {optionFields.length > 1 && (
                            <IconButton
                              aria-label="Remove option"
                              icon={<FiX />}
                              size="sm"
                              colorScheme="red"
                              variant="ghost"
                              onClick={() => handleRemoveOption(index)}
                            />
                          )}
                        </HStack>
                      ))}
                      <Button
                        leftIcon={<FiPlus />}
                        size="sm"
                        variant="outline"
                        colorScheme="blue"
                        onClick={handleAddOption}
                        width="fit-content"
                      >
                        Add Option
                      </Button>
                    </VStack>
                    <Text fontSize="xs" color="gray.500" mt={2}>
                      Add multiple options. They will be combined automatically.
                    </Text>
                  </FormControl>
                )}

                <FormControl>
                  <Checkbox
                    isChecked={formData.is_mandatory}
                    onChange={(e) =>
                      setFormData({ ...formData, is_mandatory: e.target.checked })
                    }
                  >
                    Is Mandatory
                  </Checkbox>
                  <Text fontSize="sm" color="gray.600" mt={1}>
                    If checked, this specification must be filled when creating assets
                  </Text>
                </FormControl>

                <FormControl>
                  <FormLabel>Description</FormLabel>
                  <Textarea
                    value={formData.description}
                    onChange={(e) =>
                      setFormData({ ...formData, description: e.target.value })
                    }
                    placeholder="Optional description for this specification"
                    rows={3}
                  />
                </FormControl>
              </VStack>
            </ModalBody>

            <ModalFooter>
              <Button variant="ghost" mr={3} onClick={onClose}>
                Cancel
              </Button>
              <Button colorScheme="blue" onClick={handleSubmit}>
                {editingSpec ? 'Update' : 'Create'}
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>

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

export default AssetSpecificationsPage;

