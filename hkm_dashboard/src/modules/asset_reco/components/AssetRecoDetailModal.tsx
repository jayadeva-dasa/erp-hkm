// Asset Reco Detail Modal with Specifications Support
import React, { useState, useEffect, useCallback } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  FormControl,
  FormLabel,
  Input,
  VStack,
  HStack,
  Text,
  Select,
  NumberInput,
  NumberInputField,
  useToast,
  Box,
  Badge,
  Divider,
  IconButton,
  Checkbox,
  Spinner,
  Tooltip,
  Icon,
  RadioGroup,
  Radio,
  Stack,
  InputGroup,
  InputLeftElement,
} from '@chakra-ui/react';
import { 
  FiPlus, 
  FiX, 
  FiCalendar, 
  FiSearch,
  FiCheckCircle,
} from 'react-icons/fi';
import { assetRecoApi } from '../api/assetRecoApi';
import type { 
  AssetRecoItem, 
  Specification, 
  SpecificationValue,
  AvailableAsset,
} from '../types';
import { SearchableSelect, type SelectOption } from './SearchableSelect';

interface AssetRecoDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  assetId: string;
  onSave: () => Promise<void>;
  users: SelectOption[];
  onUserSearch: (searchTerm: string) => void;
  loadingUsers: boolean;
}

// ============ ADD SPECIFICATION DIALOG (Chakra UI Modal) ============
interface AddSpecDialogProps {
  isOpen: boolean;
  onClose: () => void;
  availableSpecs: Specification[];
  onAdd: (spec: Specification, value: string) => void;
}

const AddSpecificationDialog: React.FC<AddSpecDialogProps> = ({
  isOpen,
  onClose,
  availableSpecs,
  onAdd,
}) => {
  const [selectedSpec, setSelectedSpec] = useState<Specification | null>(null);
  const [tempValue, setTempValue] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState('');

  const filteredSpecs = availableSpecs.filter((spec) =>
    spec.specification_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleSelectSpec = (spec: Specification) => {
    setSelectedSpec(spec);
    setTempValue('');
  };

  const handleAdd = () => {
    if (selectedSpec && tempValue) {
      onAdd(selectedSpec, tempValue);
      handleReset();
    }
  };

  const handleReset = () => {
    setSelectedSpec(null);
    setTempValue('');
    setSearchTerm('');
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleReset} size="md" isCentered>
      <ModalOverlay bg="blackAlpha.600" backdropFilter="blur(5px)" />
      <ModalContent>
        <ModalHeader bg="purple.500" color="white" borderTopRadius="md">
          Add Custom Specification
        </ModalHeader>
        <ModalCloseButton color="white" />

        <ModalBody py={4}>
          <VStack spacing={4} align="stretch">
            {/* Search Input */}
            <InputGroup>
              <InputLeftElement>
                <Icon as={FiSearch} color="gray.400" />
              </InputLeftElement>
              <Input
                placeholder="Search specifications..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </InputGroup>

            {/* Selected Spec Display */}
            {selectedSpec && (
              <Box bg="green.50" p={3} borderRadius="md" borderWidth="1px" borderColor="green.200">
                <HStack justify="space-between">
                  <HStack>
                    <Icon as={FiCheckCircle} color="green.500" />
                    <Text fontWeight="medium">{selectedSpec.specification_name}</Text>
                    <Badge colorScheme="green">{selectedSpec.data_type}</Badge>
                  </HStack>
                  <IconButton
                    aria-label="Deselect"
                    icon={<FiX />}
                    size="xs"
                    variant="ghost"
                    onClick={() => {
                      setSelectedSpec(null);
                      setTempValue('');
                    }}
                  />
                </HStack>
              </Box>
            )}

            {/* Spec List */}
            {!selectedSpec && (
              <Box maxH="200px" overflowY="auto" borderWidth="1px" borderRadius="md" p={2}>
                {filteredSpecs.length > 0 ? (
                  <VStack spacing={1} align="stretch">
                    {filteredSpecs.map((spec) => (
                      <Box
                        key={spec.name}
                        p={2}
                        borderRadius="md"
                        cursor="pointer"
                        _hover={{ bg: 'blue.50' }}
                        onClick={() => handleSelectSpec(spec)}
                      >
                        <HStack justify="space-between">
                          <Text fontSize="sm">{spec.specification_name}</Text>
                          <Badge colorScheme="blue" fontSize="xs">
                            {spec.data_type}
                          </Badge>
                        </HStack>
                      </Box>
                    ))}
                  </VStack>
                ) : (
                  <Text fontSize="sm" color="gray.500" textAlign="center" py={4}>
                    No specifications found
                  </Text>
                )}
              </Box>
            )}

            {/* Value Input */}
            {selectedSpec && (
              <FormControl>
                <FormLabel fontSize="sm">Value</FormLabel>
                {selectedSpec.data_type === 'Text' || selectedSpec.data_type === 'Number' ? (
                  <Input
                    type={selectedSpec.data_type === 'Number' ? 'number' : 'text'}
                    value={tempValue}
                    onChange={(e) => setTempValue(e.target.value)}
                    placeholder={`Enter ${selectedSpec.data_type.toLowerCase()}`}
                    autoFocus
                  />
                ) : selectedSpec.data_type === 'Select' ? (
                  <Select
                    value={tempValue}
                    onChange={(e) => setTempValue(e.target.value)}
                    placeholder="Select option"
                  >
                    {selectedSpec.options?.split(',').map((option) => (
                      <option key={option.trim()} value={option.trim()}>
                        {option.trim()}
                      </option>
                    ))}
                  </Select>
                ) : selectedSpec.data_type === 'Date' ? (
                  <Input
                    type="date"
                    value={tempValue}
                    onChange={(e) => setTempValue(e.target.value)}
                  />
                ) : selectedSpec.data_type === 'Checkbox' ? (
                  <Checkbox
                    isChecked={tempValue === '1'}
                    onChange={(e) => setTempValue(e.target.checked ? '1' : '0')}
                  >
                    Enabled
                  </Checkbox>
                ) : null}
              </FormControl>
            )}
          </VStack>
        </ModalBody>

        <ModalFooter bg="gray.50" borderBottomRadius="md">
          <HStack spacing={3}>
            <Button variant="ghost" onClick={handleReset}>
              Cancel
            </Button>
            <Button
              colorScheme="purple"
              onClick={handleAdd}
              isDisabled={!selectedSpec || !tempValue}
            >
              Add
            </Button>
          </HStack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export const AssetRecoDetailModal: React.FC<AssetRecoDetailModalProps> = ({
  isOpen,
  onClose,
  assetId,
  onSave,
  users,
  onUserSearch,
  loadingUsers,
}) => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [asset, setAsset] = useState<AssetRecoItem | null>(null);
  const [specifications, setSpecifications] = useState<Specification[]>([]);
  const [customSpecs, setCustomSpecs] = useState<Specification[]>([]);
  const [specValues, setSpecValues] = useState<Record<string, string>>({});
  const [customSpecValues, setCustomSpecValues] = useState<SpecificationValue[]>([]);
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [availabilityStatus, setAvailabilityStatus] = useState<'New' | 'Available'>('New');
  const [searchResults, setSearchResults] = useState<AvailableAsset[]>([]);
  const [searchingAssets, setSearchingAssets] = useState(false);
  const [searchDebounceTimer, setSearchDebounceTimer] = useState<ReturnType<typeof setTimeout> | null>(null);
  const [showAddSpecDialog, setShowAddSpecDialog] = useState(false);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [loadingCategories, setLoadingCategories] = useState(false);
  const [specMetadataMap, setSpecMetadataMap] = useState<Record<string, Specification>>({});
  const toast = useToast();

  // Load categories on mount
  useEffect(() => {
    if (isOpen) {
      loadCategories();
    }
  }, [isOpen]);

  // Load asset data
  useEffect(() => {
    if (isOpen && assetId) {
      loadAssetData();
    }
  }, [isOpen, assetId]);

  const loadCategories = async () => {
    try {
      setLoadingCategories(true);
      const cats = await assetRecoApi.getAssetCategories();
      setCategories(cats);
    } catch (error: any) {
      console.error('Error loading categories:', error);
    } finally {
      setLoadingCategories(false);
    }
  };

  const loadAssetData = async () => {
    try {
      setLoading(true);
      const data = await assetRecoApi.getAssetRecoById(assetId);
      setAsset(data);
      
      // Initialize form data
      setFormData({
        location: data.location || '',
        purchased_date: data.purchased_date || '',
        purchased_amount: data.purchased_amount || 0,
        secondary_custodian: data.secondary_custodian || '',
        remarks: data.remarks || '',
        asset_id: data.asset_id || '',
        asset_name: data.asset_name || '',
      });

      setAvailabilityStatus(data.availability_status || 'New');

      // Set selected category
      setSelectedCategory(data.asset_category || '');

      // Load specifications for category
      if (data.asset_category) {
        await loadSpecifications(data.asset_category);
      }

      // Initialize spec values from loaded data
      if (data.specifications && data.specifications.length > 0) {
        // Load all specs metadata for the category to identify mandatory vs custom
        const allCategorySpecs = await assetRecoApi.getAssetSpecifications(data.asset_category);
        
        const values: Record<string, string> = {};
        const customValues: SpecificationValue[] = [];
        
        data.specifications.forEach((spec) => {
          // Find if this spec is mandatory
          const specMetadata = allCategorySpecs.find(s => s.name === spec.specification);
          
          if (specMetadata && specMetadata.is_mandatory === 1) {
            // Mandatory spec - store in specValues
            values[spec.specification] = spec.value;
          } else if (specMetadata) {
            // Custom spec - store in customSpecValues with metadata
            customValues.push({
              specification: spec.specification,
              specification_name: spec.specification_name || specMetadata.specification_name,
              data_type: spec.data_type || specMetadata.data_type,
              value: spec.value,
            });
          }
        });
        
        setSpecValues(values);
        setCustomSpecValues(customValues);
      }
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to load asset data',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const loadSpecifications = async (category: string) => {
    try {
      const allSpecs = await assetRecoApi.getAssetSpecifications(category);
      
      // Filter ONLY mandatory specs for main section
      const mandatorySpecs = allSpecs.filter(spec => spec.is_mandatory === 1);
      setSpecifications(mandatorySpecs);
      
      // Build metadata map for ALL specs (for lookup)
      const metadataMap: Record<string, Specification> = {};
      allSpecs.forEach(spec => {
        metadataMap[spec.name] = spec;
      });
      setSpecMetadataMap(metadataMap);
    } catch (error: any) {
      console.error('Error loading specifications:', error);
    }
  };


  const handleFieldChange = (fieldname: string, value: any) => {
    setFormData((prev) => ({
      ...prev,
      [fieldname]: value,
    }));
  };

  // Handle category change - reload specifications (like Flutter)
  const handleCategoryChange = async (newCategory: string) => {
    if (newCategory === selectedCategory) return;

    setSelectedCategory(newCategory);

    // Clear all custom specifications (like Flutter does)
    setCustomSpecs([]);
    setCustomSpecValues([]);

    // Clear specification values
    setSpecValues({});

    // Load specifications for new category
    if (newCategory) {
      await loadSpecifications(newCategory);
    } else {
      setSpecifications([]);
    }

    toast({
      title: 'Category Changed',
      description: 'Specifications reloaded for new category. Please re-enter values.',
      status: 'info',
      duration: 3000,
      isClosable: true,
    });
  };

  const handleSpecValueChange = (specification: string, value: string) => {
    setSpecValues((prev) => ({
      ...prev,
      [specification]: value,
    }));
  };

  const handleAssetSearch = useCallback((query: string) => {
    if (searchDebounceTimer) {
      clearTimeout(searchDebounceTimer);
    }

    if (!query || query.length < 2) {
      setSearchResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        setSearchingAssets(true);
        const results = await assetRecoApi.searchAvailableAssets({ assetId: query });
        setSearchResults(results);
      } catch (error: any) {
        console.error('Error searching assets:', error);
      } finally {
        setSearchingAssets(false);
      }
    }, 500);

    setSearchDebounceTimer(timer);
  }, [searchDebounceTimer]);

  const handleAssetSelect = (selectedAsset: AvailableAsset) => {
    setFormData((prev) => ({
      ...prev,
      asset_id: selectedAsset.asset_id,
      asset_name: selectedAsset.asset_name,
      purchased_date: selectedAsset.purchased_date || '',
      purchased_amount: selectedAsset.purchased_amount || 0,
    }));
    setSearchResults([]);
  };

  const loadAvailableCustomSpecs = async () => {
    if (!asset?.asset_category) return;
    
    try {
      const specs = await assetRecoApi.getAvailableCustomSpecs(asset.asset_category);
      
      // Filter out already added specs
      const existingSpecNames = [
        ...specifications.map(s => s.name),
        ...customSpecValues.map(s => s.specification),
      ];
      const availableSpecs = specs.filter(
        s => !existingSpecNames.includes(s.name)
      );
      
      setCustomSpecs(availableSpecs);
      setShowAddSpecDialog(true);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: 'Failed to load custom specifications',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const handleAddCustomSpec = (spec: Specification, value: string) => {
    setCustomSpecValues((prev) => [
      ...prev,
      {
        specification: spec.name, // Use spec.name as the ID
        specification_name: spec.specification_name,
        data_type: spec.data_type, // Store data_type
        value,
      },
    ]);
    
    // Store metadata for this spec
    setSpecMetadataMap((prev) => ({
      ...prev,
      [spec.name]: spec,
    }));
    
    // Remove from available custom specs
    setCustomSpecs((prev) => prev.filter(s => s.name !== spec.name));
  };

  const handleRemoveCustomSpec = (specification: string) => {
    setCustomSpecValues((prev) =>
      prev.filter((spec) => spec.specification !== specification)
    );
  };

  const handleSave = async () => {
    if (!asset) return;

    try {
      setSaving(true);

      // Collect all specifications
      const allSpecs: SpecificationValue[] = [];
      
      // Add mandatory specs
      specifications.forEach((spec) => {
        const value = specValues[spec.name] || (spec.data_type === 'Checkbox' ? '0' : '');
        allSpecs.push({
          specification: spec.name, // Use spec.name as the ID
          value,
        });
      });

      // Add custom specs
      customSpecValues.forEach((spec) => {
        allSpecs.push(spec);
      });

      await assetRecoApi.saveAssetRecoWithSpecs({
        name: asset.name,
        asset_category: selectedCategory, // Include selected category
        ...formData,
        availability_status: availabilityStatus,
        specifications: allSpecs,
      });

      toast({
        title: 'Success',
        description: 'Asset saved successfully',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });

      await onSave();
      onClose();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to save asset',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setSaving(false);
    }
  };

  const renderSpecificationField = (spec: Specification) => {
    const value = specValues[spec.name] || '';
    
    return (
      <FormControl key={spec.name}>
        <FormLabel fontSize="sm" fontWeight="semibold">
          {spec.specification_name}
          {spec.is_mandatory === 1 && (
            <Text as="span" color="red.500" ml={1}>
              *
            </Text>
          )}
        </FormLabel>
        
        {spec.data_type === 'Text' || spec.data_type === 'Number' ? (
          <Input
            type={spec.data_type === 'Number' ? 'number' : 'text'}
            value={value}
            onChange={(e) => handleSpecValueChange(spec.name, e.target.value)}
            placeholder={`Enter ${spec.data_type.toLowerCase()}`}
            size="sm"
            isReadOnly={isReadOnly}
          />
        ) : spec.data_type === 'Select' ? (
          <Select
            value={value}
            onChange={(e) => handleSpecValueChange(spec.name, e.target.value)}
            placeholder="Select option"
            size="sm"
            isDisabled={isReadOnly}
          >
            {spec.options?.split(',').map((option) => (
              <option key={option.trim()} value={option.trim()}>
                {option.trim()}
              </option>
            ))}
          </Select>
        ) : spec.data_type === 'Date' ? (
          <Input
            type="date"
            value={value}
            onChange={(e) => handleSpecValueChange(spec.name, e.target.value)}
            size="sm"
            isReadOnly={isReadOnly}
          />
        ) : spec.data_type === 'Checkbox' ? (
          <Checkbox
            isChecked={value === '1'}
            onChange={(e) => handleSpecValueChange(spec.name, e.target.checked ? '1' : '0')}
            isDisabled={isReadOnly}
          >
            Enable
          </Checkbox>
        ) : null}
      </FormControl>
    );
  };

  // Render custom spec field with proper data type handling
  const renderCustomSpecField = (spec: SpecificationValue, specMetadata: Specification | null) => {
    const handleChange = (value: string) => {
      setCustomSpecValues((prev) =>
        prev.map((s) =>
          s.specification === spec.specification
            ? { ...s, value }
            : s
        )
      );
    };

    // Get data type and options from metadata
    const dataType = specMetadata?.data_type || 'Text';
    const options = specMetadata?.options || '';

    return (
      <FormControl flex={1}>
        <FormLabel fontSize="sm" fontWeight="semibold">
          {spec.specification_name || spec.specification}
        </FormLabel>
        
        {dataType === 'Text' || dataType === 'Number' ? (
          <Input
            type={dataType === 'Number' ? 'number' : 'text'}
            value={spec.value || ''}
            onChange={(e) => handleChange(e.target.value)}
            placeholder={`Enter ${dataType.toLowerCase()}`}
            size="sm"
            isReadOnly={isReadOnly}
          />
        ) : dataType === 'Select' ? (
          <Select
            value={spec.value || ''}
            onChange={(e) => handleChange(e.target.value)}
            placeholder="Select option"
            size="sm"
            isDisabled={isReadOnly}
          >
            {options.split(',').map((option) => (
              <option key={option.trim()} value={option.trim()}>
                {option.trim()}
              </option>
            ))}
          </Select>
        ) : dataType === 'Date' ? (
          <Input
            type="date"
            value={spec.value || ''}
            onChange={(e) => handleChange(e.target.value)}
            size="sm"
            isReadOnly={isReadOnly}
          />
        ) : dataType === 'Checkbox' ? (
          <Checkbox
            isChecked={spec.value === '1'}
            onChange={(e) => handleChange(e.target.checked ? '1' : '0')}
            isDisabled={isReadOnly}
          >
            Enable
          </Checkbox>
        ) : (
          <Input
            value={spec.value || ''}
            onChange={(e) => handleChange(e.target.value)}
            size="sm"
            isReadOnly={isReadOnly}
          />
        )}
      </FormControl>
    );
  };

  if (!asset) return null;

  const isReadOnly = asset.docstatus === 1;

  return (
    <>
      <Modal isOpen={isOpen} onClose={onClose} size="4xl" scrollBehavior="inside">
        <ModalOverlay bg="blackAlpha.600" backdropFilter="blur(5px)" />
        <ModalContent maxH="90vh">
          <ModalHeader bg="blue.500" color="white" borderTopRadius="md">
            <HStack justify="space-between">
              <VStack align="start" spacing={1}>
                <Text fontSize="lg" fontWeight="bold">Asset Details</Text>
                <Text fontSize="sm" fontWeight="normal" opacity={0.9}>
                  {asset.name} - {asset.asset_category}
                </Text>
              </VStack>
              {isReadOnly && (
                <Badge colorScheme="green" fontSize="md" px={3} py={1}>
                  Submitted
                </Badge>
              )}
            </HStack>
          </ModalHeader>
          <ModalCloseButton color="white" />

          <ModalBody py={6}>
            {loading ? (
              <Box textAlign="center" py={8}>
                <Spinner size="xl" color="blue.500" thickness="3px" />
                <Text mt={3} color="gray.600">
                  Loading asset data...
                </Text>
              </Box>
            ) : (
              <VStack spacing={6} align="stretch">
                {/* Submitted Banner */}
                {isReadOnly && (
                  <Box bg="green.50" borderWidth="1px" borderColor="green.200" borderRadius="md" p={4}>
                    <HStack>
                      <Icon as={FiCheckCircle} color="green.500" boxSize={5} />
                      <Box>
                        <Text fontWeight="bold" color="green.700">Submitted</Text>
                        <Text fontSize="sm" color="green.600">
                          This asset has been submitted. Only images can be modified.
                        </Text>
                      </Box>
                    </HStack>
                  </Box>
                )}

                {/* Basic Information */}
                <Box>
                  <Text fontSize="md" fontWeight="bold" mb={3} color="blue.600">
                    Basic Information
                  </Text>
                  <VStack spacing={4} align="stretch">
                    <HStack spacing={4}>
                      <FormControl flex={1}>
                        <FormLabel fontSize="sm" fontWeight="semibold">
                          Company
                        </FormLabel>
                        <Input
                          value={asset.company || ''}
                          isReadOnly
                          bg="gray.100"
                          size="sm"
                        />
                      </FormControl>

                      <FormControl flex={1} isRequired>
                        <FormLabel fontSize="sm" fontWeight="semibold">
                          Asset Category *
                        </FormLabel>
                        <Select
                          value={selectedCategory}
                          onChange={(e) => handleCategoryChange(e.target.value)}
                          placeholder={loadingCategories ? 'Loading...' : 'Select category'}
                          isDisabled={loadingCategories || isReadOnly}
                          size="sm"
                          bg={isReadOnly ? 'gray.100' : 'white'}
                        >
                          {categories.map((cat) => (
                            <option key={cat} value={cat}>
                              {cat}
                            </option>
                          ))}
                        </Select>
                      </FormControl>
                    </HStack>

                    <FormControl>
                      <FormLabel fontSize="sm" fontWeight="semibold">
                        Custodian Department
                      </FormLabel>
                      <Input
                        value={asset.custodian_department || asset.custodian || ''}
                        isReadOnly
                        bg="gray.100"
                        size="sm"
                      />
                    </FormControl>

                    {/* Availability Status */}
                    {!isReadOnly && (
                      <FormControl>
                        <FormLabel fontSize="sm" fontWeight="semibold">
                          Availability Status
                        </FormLabel>
                        <RadioGroup
                          value={availabilityStatus}
                          onChange={(value) => setAvailabilityStatus(value as 'New' | 'Available')}
                        >
                          <Stack direction="row" spacing={4}>
                            <Radio value="New">New</Radio>
                            <Radio value="Available">Available</Radio>
                          </Stack>
                        </RadioGroup>
                      </FormControl>
                    )}

                    {/* Asset Name (editable for both New and Available when draft; read-only when submitted) */}
                    <FormControl>
                      <FormLabel fontSize="sm" fontWeight="semibold">
                        Asset Name
                      </FormLabel>
                      <Input
                        value={formData.asset_name || ''}
                        onChange={(e) => handleFieldChange('asset_name', e.target.value)}
                        placeholder="Enter asset name"
                        size="sm"
                        isReadOnly={isReadOnly}
                        bg={isReadOnly ? 'gray.100' : 'white'}
                      />
                    </FormControl>

                    {/* Asset ID Search (only for Available status) */}
                    {availabilityStatus === 'Available' && !isReadOnly && (
                      <Box>
                        <FormControl>
                          <FormLabel fontSize="sm" fontWeight="semibold">
                            Asset ID
                          </FormLabel>
                          <InputGroup>
                            <InputLeftElement>
                              {searchingAssets ? (
                                <Spinner size="sm" color="blue.500" />
                              ) : (
                                <Icon as={FiSearch} color="gray.400" />
                              )}
                            </InputLeftElement>
                            <Input
                              value={formData.asset_id || ''}
                              onChange={(e) => {
                                handleFieldChange('asset_id', e.target.value);
                                handleAssetSearch(e.target.value);
                              }}
                              placeholder="Search asset ID..."
                              size="sm"
                            />
                          </InputGroup>
                        </FormControl>

                        {/* Search Results */}
                        {searchResults.length > 0 && (
                          <Box
                            mt={2}
                            maxH="200px"
                            overflowY="auto"
                            borderWidth="1px"
                            borderRadius="md"
                            bg="white"
                            shadow="md"
                          >
                            {searchResults.map((result) => (
                              <Box
                                key={result.asset_id}
                                p={3}
                                cursor="pointer"
                                _hover={{ bg: 'blue.50' }}
                                onClick={() => handleAssetSelect(result)}
                                borderBottomWidth="1px"
                              >
                                <Text fontWeight="medium" fontSize="sm">
                                  {result.asset_id}
                                </Text>
                                <Text fontSize="xs" color="gray.600">
                                  {result.asset_name} - ₹{result.purchased_amount}
                                </Text>
                              </Box>
                            ))}
                          </Box>
                        )}
                      </Box>
                    )}
                  </VStack>
                </Box>

                <Divider />

                {/* Specifications */}
                {specifications.length > 0 && (
                  <Box>
                    <HStack justify="space-between" mb={3}>
                      <Text fontSize="md" fontWeight="bold" color="blue.600">
                        Specifications
                      </Text>
                      {!isReadOnly && (
                        <Button
                          size="xs"
                          colorScheme="purple"
                          leftIcon={<FiPlus />}
                          onClick={loadAvailableCustomSpecs}
                        >
                          Add Custom Spec
                        </Button>
                      )}
                    </HStack>
                    
                    <VStack spacing={3} align="stretch">
                      {specifications.map((spec) => renderSpecificationField(spec))}
                      
                      {/* Custom Specifications (Non-Mandatory, User Added) */}
                      {customSpecValues.map((spec) => (
                        <HStack key={spec.specification} spacing={2}>
                          {renderCustomSpecField(spec, specMetadataMap[spec.specification] || null)}
                          {!isReadOnly && (
                            <Tooltip label="Remove specification">
                              <IconButton
                                aria-label="Remove"
                                icon={<FiX />}
                                size="sm"
                                colorScheme="red"
                                variant="ghost"
                                mt={8}
                                onClick={() => handleRemoveCustomSpec(spec.specification)}
                              />
                            </Tooltip>
                          )}
                        </HStack>
                      ))}
                    </VStack>
                  </Box>
                )}

                <Divider />

                {/* Additional Information */}
                <Box>
                  <Text fontSize="md" fontWeight="bold" mb={3} color="blue.600">
                    Additional Information
                  </Text>
                  <VStack spacing={4} align="stretch">
                    <FormControl>
                      <FormLabel fontSize="sm" fontWeight="semibold">
                        Location
                      </FormLabel>
                      <Input
                        value={formData.location || ''}
                        onChange={(e) => handleFieldChange('location', e.target.value)}
                        placeholder="Enter location"
                        size="sm"
                        isReadOnly={isReadOnly}
                      />
                    </FormControl>

                    <HStack spacing={4}>
                      <FormControl flex={1}>
                        <FormLabel fontSize="sm" fontWeight="semibold">
                          Purchased Date
                        </FormLabel>
                        <Input
                          type="date"
                          value={formData.purchased_date || ''}
                          onChange={(e) => handleFieldChange('purchased_date', e.target.value)}
                          size="sm"
                          isReadOnly
                          bg="gray.100"
                        />
                      </FormControl>

                      <FormControl flex={1}>
                        <FormLabel fontSize="sm" fontWeight="semibold">
                          Purchased Amount
                        </FormLabel>
                        <NumberInput
                          value={formData.purchased_amount || 0}
                          onChange={(_, value) => handleFieldChange('purchased_amount', value)}
                          min={0}
                          precision={2}
                          size="sm"
                          isReadOnly={isReadOnly}
                        >
                          <NumberInputField bg={isReadOnly ? 'gray.100' : 'white'} />
                        </NumberInput>
                      </FormControl>
                    </HStack>

                    <FormControl>
                      <FormLabel fontSize="sm" fontWeight="semibold">
                        Secondary Custodian
                      </FormLabel>
                      <SearchableSelect
                        size="sm"
                        options={users}
                        value={formData.secondary_custodian || ''}
                        onChange={(value) => handleFieldChange('secondary_custodian', value)}
                        placeholder="Select user..."
                        onSearch={onUserSearch}
                        isLoading={loadingUsers}
                        isDisabled={isReadOnly}
                      />
                    </FormControl>

                    <FormControl>
                      <FormLabel fontSize="sm" fontWeight="semibold">
                        Remarks
                      </FormLabel>
                      <Input
                        value={formData.remarks || ''}
                        onChange={(e) => handleFieldChange('remarks', e.target.value)}
                        placeholder="Add remarks..."
                        size="sm"
                        isReadOnly={isReadOnly}
                      />
                    </FormControl>
                  </VStack>
                </Box>
              </VStack>
            )}
          </ModalBody>

          <ModalFooter bg="gray.50" borderBottomRadius="md">
            <HStack spacing={3}>
              <Button variant="ghost" onClick={onClose} isDisabled={saving}>
                {isReadOnly ? 'Close' : 'Cancel'}
              </Button>
              {!isReadOnly && (
                <Button
                  colorScheme="blue"
                  onClick={handleSave}
                  isLoading={saving}
                  loadingText="Saving..."
                >
                  Save Changes
                </Button>
              )}
            </HStack>
          </ModalFooter>
        </ModalContent>
      </Modal>

      <AddSpecificationDialog
        isOpen={showAddSpecDialog}
        onClose={() => setShowAddSpecDialog(false)}
        availableSpecs={customSpecs}
        onAdd={handleAddCustomSpec}
      />
    </>
  );
};

