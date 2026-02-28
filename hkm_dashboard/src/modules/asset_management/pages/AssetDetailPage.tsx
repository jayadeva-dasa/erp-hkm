import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box,
  Container,
  Heading,
  Button,
  VStack,
  HStack,
  Text,
  Badge,
  SimpleGrid,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  useToast,
  Spinner,
  Divider,
  Card,
  CardHeader,
  CardBody,
  Image,
} from '@chakra-ui/react';
import { FiEdit, FiTruck, FiTrash2, FiDollarSign, FiAlertCircle, FiArrowLeft, FiCheck } from 'react-icons/fi';
import PageHeader from '../../../components/shared/PageHeader';
import apiClient from '../../../services/apiClient';

const AssetDetailPage: React.FC = () => {
  const { assetId } = useParams<{ assetId: string }>();
  const navigate = useNavigate();
  const toast = useToast();
  const [asset, setAsset] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [depreciationPage, setDepreciationPage] = useState(1);
  const itemsPerPage = 20;

  useEffect(() => {
    if (assetId) {
      fetchAssetDetails();
      setDepreciationPage(1); // Reset pagination when asset changes
    }
  }, [assetId]);

  const fetchAssetDetails = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get(`/api/resource/HKM Asset/${assetId}`);
      setAsset(response.data.data);
    } catch (error: any) {
      toast({
        title: 'Error fetching asset',
        description: error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
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

  const formatSpecificationValue = (spec: any) => {
    const value = spec.value;
    
    if (!value || value === '') {
      return '-';
    }

    switch (spec.data_type) {
      case 'Checkbox':
        // Checkbox stores "True" or "False" as string
        return value === 'True' || value === true ? 'Yes' : 'No';
      
      case 'Date':
        // Format date string (YYYY-MM-DD) to readable format
        if (value) {
          try {
            const date = new Date(value);
            if (!isNaN(date.getTime())) {
              return date.toLocaleDateString('en-IN', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
              });
            }
          } catch (e) {
            // If date parsing fails, return as is
          }
        }
        return value;
      
      case 'Number':
        // Format number with commas
        const numValue = parseFloat(value);
        if (!isNaN(numValue)) {
          return numValue.toLocaleString('en-IN', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 2
          });
        }
        return value;
      
      case 'Select':
      case 'Text':
      default:
        // For Select and Text, just return the value
        return value;
    }
  };

  const handleSubmitAsset = async () => {
    if (!asset) return;
    
    try {
      // First, get the document
      const docResponse = await apiClient.get(`/api/resource/HKM Asset/${asset.name}`);
      const doc = docResponse.data.data;
      
      // Submit using Frappe's submit method
      await apiClient.post('/api/method/frappe.client.submit', {
        doc: doc,
      });
      
      toast({
        title: 'Asset Submitted!',
        description: `Asset ${asset.name} has been submitted successfully`,
        status: 'success',
        duration: 5000,
      });
      
      // Refresh the asset details
      fetchAssetDetails();
    } catch (error: any) {
      toast({
        title: 'Error submitting asset',
        description: error.response?.data?.message || error.response?.data?.exc || error.message,
        status: 'error',
        duration: 5000,
      });
    }
  };

  if (loading) {
    return (
      <Box minH="100vh" bg="gray.50" display="flex" alignItems="center" justifyContent="center">
        <VStack>
          <Spinner size="xl" color="blue.500" />
          <Text mt={4}>Loading asset details...</Text>
        </VStack>
      </Box>
    );
  }

  if (!asset) {
    return (
      <Box minH="100vh" bg="gray.50">
        <Container maxW="container.md" py={8}>
          <Text fontSize="lg" textAlign="center">Asset not found</Text>
          <Button mt={4} onClick={() => navigate('/asset-dashboard/list')}>
            Back to List
          </Button>
        </Container>
      </Box>
    );
  }

  return (
    <Box minH="100vh" bg="gray.50">
      <PageHeader
        title={`Asset: ${asset.name}`}
        subtitle={asset.asset_name}
        onBack={() => navigate('/asset-dashboard/list')}
      />

      <Container maxW="container.xl" py={8}>
        <VStack spacing={6} align="stretch">
          {/* Quick Actions */}
          <HStack spacing={4} flexWrap="wrap">
            {asset.docstatus === 0 ? (
              <>
                <Button
                  leftIcon={<FiEdit />}
                  colorScheme="blue"
                  onClick={() => window.location.href = `/app/hkm-asset/${asset.name}`}
                >
                  Edit Asset
                </Button>
                <Button
                  leftIcon={<FiCheck />}
                  colorScheme="green"
                  onClick={handleSubmitAsset}
                >
                  Submit Asset
                </Button>
              </>
            ) : (
              <>
                <Button
                  leftIcon={<FiTruck />}
                  colorScheme="purple"
                  onClick={() => navigate('/asset-dashboard/move', { state: { assetId: asset.name } })}
                  isDisabled={['Scrapped', 'Sold', 'Lost'].includes(asset.status)}
                >
                  Move Asset
                </Button>
                <Button
                  leftIcon={<FiTrash2 />}
                  colorScheme="red"
                  onClick={() => navigate('/asset-dashboard/scrap', { state: { assetId: asset.name } })}
                  isDisabled={['Scrapped', 'Sold', 'Lost'].includes(asset.status)}
                >
                  Scrap
                </Button>
                <Button
                  leftIcon={<FiDollarSign />}
                  colorScheme="orange"
                  onClick={() => navigate('/asset-dashboard/sell', { state: { assetId: asset.name } })}
                  isDisabled={['Scrapped', 'Sold', 'Lost'].includes(asset.status)}
                >
                  Sell
                </Button>
                <Button
                  leftIcon={<FiAlertCircle />}
                  colorScheme="yellow"
                  onClick={() => navigate('/asset-dashboard/lost', { state: { assetId: asset.name } })}
                  isDisabled={['Scrapped', 'Sold', 'Lost'].includes(asset.status)}
                >
                  Report Lost
                </Button>
              </>
            )}
            <Button
              leftIcon={<FiEdit />}
              variant="outline"
              onClick={() => window.location.href = `/app/hkm-asset/${asset.name}`}
            >
              Edit in ERPNext
            </Button>
          </HStack>

          {/* Basic Info Card */}
          <Card>
            <CardHeader bg="blue.50">
              <HStack justify="space-between">
                <Heading size="md">Basic Information</Heading>
                <Badge 
                  colorScheme={getStatusColor(asset.docstatus === 0 ? 'Draft' : asset.status)} 
                  fontSize="md" 
                  px={3} 
                  py={1}
                >
                  {asset.docstatus === 0 ? 'Draft' : asset.status}
                </Badge>
              </HStack>
            </CardHeader>
            <CardBody>
              <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
                {asset.image && (
                  <Box gridColumn={{ base: 1, lg: '1 / -1' }}>
                    <Image
                      src={asset.image}
                      alt={asset.asset_name}
                      maxH="200px"
                      objectFit="contain"
                      borderRadius="md"
                    />
                  </Box>
                )}
                <Box>
                  <Text fontWeight="bold" color="gray.600" fontSize="sm">Asset ID</Text>
                  <Text fontSize="lg">{asset.name}</Text>
                </Box>
                <Box>
                  <Text fontWeight="bold" color="gray.600" fontSize="sm">Asset Name</Text>
                  <Text fontSize="lg">{asset.asset_name}</Text>
                </Box>
                <Box>
                  <Text fontWeight="bold" color="gray.600" fontSize="sm">Item Code</Text>
                  <Text fontSize="lg">{asset.item_code}</Text>
                </Box>
                <Box>
                  <Text fontWeight="bold" color="gray.600" fontSize="sm">Category</Text>
                  <Text fontSize="lg">{asset.asset_category}</Text>
                </Box>
                <Box>
                  <Text fontWeight="bold" color="gray.600" fontSize="sm">Company</Text>
                  <Text fontSize="lg">{asset.company}</Text>
                </Box>
                <Box>
                  <Text fontWeight="bold" color="gray.600" fontSize="sm">Department</Text>
                  <Text fontSize="lg">{asset.custodian_department}</Text>
                </Box>
              </SimpleGrid>
            </CardBody>
          </Card>

          {/* Location & Custodian */}
          <Card>
            <CardHeader bg="purple.50">
              <Heading size="md">Current Location & Custodian</Heading>
            </CardHeader>
            <CardBody>
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                <Box>
                  <Text fontWeight="bold" color="gray.600" fontSize="sm">Location</Text>
                  <Text fontSize="lg">{asset.location || '-'}</Text>
                </Box>
                <Box>
                  <Text fontWeight="bold" color="gray.600" fontSize="sm">Current Location</Text>
                  <Text fontSize="lg">{asset.current_location || '-'}</Text>
                </Box>
                <Box>
                  <Text fontWeight="bold" color="gray.600" fontSize="sm">Sub Custodian</Text>
                  <Text fontSize="lg">{asset.sub_custodian || '-'}</Text>
                </Box>
                <Box>
                  <Text fontWeight="bold" color="gray.600" fontSize="sm">Current Sub Custodian</Text>
                  <Text fontSize="lg">{asset.current_sub_custodian || '-'}</Text>
                </Box>
              </SimpleGrid>
            </CardBody>
          </Card>

          {/* Purchase Details */}
          <Card>
            <CardHeader bg="green.50">
              <Heading size="md">Purchase Details</Heading>
            </CardHeader>
            <CardBody>
              <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
                <Box>
                  <Text fontWeight="bold" color="gray.600" fontSize="sm">Purchase Date</Text>
                  <Text fontSize="lg">{asset.purchase_date}</Text>
                </Box>
                <Box>
                  <Text fontWeight="bold" color="gray.600" fontSize="sm">Available for Use Date</Text>
                  <Text fontSize="lg">{asset.available_for_use_date}</Text>
                </Box>
                <Box>
                  <Text fontWeight="bold" color="gray.600" fontSize="sm">Gross Purchase Amount</Text>
                  <Text fontSize="lg" color="green.600" fontWeight="bold">
                    ₹{asset.gross_purchase_amount?.toLocaleString()}
                  </Text>
                </Box>
                <Box>
                  <Text fontWeight="bold" color="gray.600" fontSize="sm">Asset Quantity</Text>
                  <Text fontSize="lg">{asset.asset_quantity}</Text>
                </Box>
                <Box>
                  <Text fontWeight="bold" color="gray.600" fontSize="sm">Purchase Receipt</Text>
                  <Text fontSize="lg">{asset.purchase_receipt || '-'}</Text>
                </Box>
                <Box>
                  <Text fontWeight="bold" color="gray.600" fontSize="sm">Purchase Invoice</Text>
                  <Text fontSize="lg">{asset.purchase_invoice || '-'}</Text>
                </Box>
              </SimpleGrid>
            </CardBody>
          </Card>

          {/* Depreciation Details */}
          {asset.calculate_depreciation && (
            <Card>
              <CardHeader bg="orange.50">
                <Heading size="md">Depreciation Details</Heading>
              </CardHeader>
              <CardBody>
                <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6} mb={6}>
                  <Box>
                    <Text fontWeight="bold" color="gray.600" fontSize="sm">Method</Text>
                    <Text fontSize="lg">{asset.depreciation_method}</Text>
                  </Box>
                  <Box>
                    <Text fontWeight="bold" color="gray.600" fontSize="sm">Frequency (months)</Text>
                    <Text fontSize="lg">{asset.frequency_of_depreciation}</Text>
                  </Box>
                  <Box>
                    <Text fontWeight="bold" color="gray.600" fontSize="sm">Total Depreciations</Text>
                    <Text fontSize="lg">{asset.total_number_of_depreciations}</Text>
                  </Box>
                  <Box>
                    <Text fontWeight="bold" color="gray.600" fontSize="sm">Current Value</Text>
                    <Text fontSize="lg" color="blue.600" fontWeight="bold">
                      ₹{asset.value_after_depreciation?.toLocaleString()}
                    </Text>
                  </Box>
                  <Box>
                    <Text fontWeight="bold" color="gray.600" fontSize="sm">Expected Salvage Value</Text>
                    <Text fontSize="lg">₹{asset.expected_value_after_useful_life?.toLocaleString()}</Text>
                  </Box>
                  <Box>
                    <Text fontWeight="bold" color="gray.600" fontSize="sm">Next Depreciation Date</Text>
                    <Text fontSize="lg">{asset.next_depreciation_date || '-'}</Text>
                  </Box>
                </SimpleGrid>

                {asset.depreciation_schedule && asset.depreciation_schedule.length > 0 && (
                  <>
                    <Divider my={4} />
                    <HStack justify="space-between" mb={4}>
                      <Heading size="sm">Depreciation Schedule</Heading>
                      <Text fontSize="sm" color="gray.600">
                        Total: {asset.depreciation_schedule.length} entries
                      </Text>
                    </HStack>
                    <Box overflowX="auto">
                      <Table variant="simple" size="sm">
                        <Thead>
                          <Tr>
                            <Th>Schedule Date</Th>
                            <Th isNumeric>Depreciation Amount</Th>
                            <Th isNumeric>Accumulated Depreciation</Th>
                            <Th>Journal Entry</Th>
                          </Tr>
                        </Thead>
                        <Tbody>
                          {asset.depreciation_schedule
                            .slice((depreciationPage - 1) * itemsPerPage, depreciationPage * itemsPerPage)
                            .map((schedule: any, index: number) => (
                            <Tr key={index}>
                              <Td>{schedule.schedule_date}</Td>
                              <Td isNumeric>₹{schedule.depreciation_amount?.toLocaleString()}</Td>
                              <Td isNumeric>₹{schedule.accumulated_depreciation_amount?.toLocaleString()}</Td>
                              <Td>{schedule.journal_entry || '-'}</Td>
                            </Tr>
                          ))}
                        </Tbody>
                      </Table>
                    </Box>
                    
                    {/* Pagination Controls */}
                    {asset.depreciation_schedule.length > itemsPerPage && (
                      <HStack justify="space-between" mt={4} pt={4} borderTop="1px" borderColor="gray.200">
                        <Text fontSize="sm" color="gray.600">
                          Showing {(depreciationPage - 1) * itemsPerPage + 1} to{' '}
                          {Math.min(depreciationPage * itemsPerPage, asset.depreciation_schedule.length)} of{' '}
                          {asset.depreciation_schedule.length} entries
                        </Text>
                        <HStack spacing={2}>
                          <Button
                            size="sm"
                            onClick={() => setDepreciationPage(prev => Math.max(1, prev - 1))}
                            isDisabled={depreciationPage === 1}
                            variant="outline"
                          >
                            Previous
                          </Button>
                          <HStack spacing={1}>
                            {Array.from(
                              { 
                                length: Math.min(
                                  5, 
                                  Math.ceil(asset.depreciation_schedule.length / itemsPerPage)
                                ) 
                              }, 
                              (_, i) => {
                                const totalPages = Math.ceil(asset.depreciation_schedule.length / itemsPerPage);
                                let pageNum: number;
                                
                                if (totalPages <= 5) {
                                  pageNum = i + 1;
                                } else if (depreciationPage <= 3) {
                                  pageNum = i + 1;
                                } else if (depreciationPage >= totalPages - 2) {
                                  pageNum = totalPages - 4 + i;
                                } else {
                                  pageNum = depreciationPage - 2 + i;
                                }
                                
                                return (
                                  <Button
                                    key={pageNum}
                                    size="sm"
                                    onClick={() => setDepreciationPage(pageNum)}
                                    colorScheme={depreciationPage === pageNum ? 'blue' : 'gray'}
                                    variant={depreciationPage === pageNum ? 'solid' : 'outline'}
                                    minW="40px"
                                  >
                                    {pageNum}
                                  </Button>
                                );
                              }
                            )}
                          </HStack>
                          <Button
                            size="sm"
                            onClick={() => setDepreciationPage(prev => 
                              Math.min(
                                Math.ceil(asset.depreciation_schedule.length / itemsPerPage), 
                                prev + 1
                              )
                            )}
                            isDisabled={
                              depreciationPage >= Math.ceil(asset.depreciation_schedule.length / itemsPerPage)
                            }
                            variant="outline"
                          >
                            Next
                          </Button>
                        </HStack>
                      </HStack>
                    )}
                  </>
                )}
              </CardBody>
            </Card>
          )}

          {/* Asset Specifications */}
          {asset.asset_specifications && asset.asset_specifications.length > 0 && (
            <Card>
              <CardHeader bg="cyan.50">
                <Heading size="md">Asset Specifications</Heading>
              </CardHeader>
              <CardBody>
                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                  {asset.asset_specifications.map((spec: any, index: number) => {
                    const formattedValue = formatSpecificationValue(spec);
                    const getDataTypeColor = (dataType: string) => {
                      const colors: Record<string, string> = {
                        'Checkbox': 'purple',
                        'Select': 'blue',
                        'Date': 'green',
                        'Number': 'orange',
                        'Text': 'gray',
                      };
                      return colors[dataType] || 'gray';
                    };

                    return (
                      <Box key={index} p={3} bg="gray.50" borderRadius="md" borderLeft="4px" borderColor={`${getDataTypeColor(spec.data_type)}.400`}>
                        <HStack justify="space-between" mb={2}>
                          <Text fontWeight="bold" color="gray.700" fontSize="sm">
                            {spec.specification_name}
                          </Text>
                          <Badge size="sm" colorScheme={getDataTypeColor(spec.data_type)}>
                            {spec.data_type}
                          </Badge>
                        </HStack>
                        {spec.data_type === 'Checkbox' ? (
                          <HStack>
                            <Box
                              w={4}
                              h={4}
                              borderRadius="sm"
                              bg={formattedValue === 'Yes' ? 'green.500' : 'gray.300'}
                              border="2px"
                              borderColor={formattedValue === 'Yes' ? 'green.600' : 'gray.400'}
                            />
                            <Text fontSize="lg" fontWeight="medium" color={formattedValue === 'Yes' ? 'green.700' : 'gray.600'}>
                              {formattedValue}
                            </Text>
                          </HStack>
                        ) : (
                          <Text fontSize="lg" fontWeight="medium" color="gray.800">
                            {formattedValue}
                          </Text>
                        )}
                      </Box>
                    );
                  })}
                </SimpleGrid>
              </CardBody>
            </Card>
          )}

          {/* Remarks */}
          {asset.remarks && (
            <Card>
              <CardHeader bg="gray.50">
                <Heading size="md">Remarks</Heading>
              </CardHeader>
              <CardBody>
                <Text>{asset.remarks}</Text>
              </CardBody>
            </Card>
          )}

          {/* Back Button */}
          <HStack justify="center">
            <Button
              leftIcon={<FiArrowLeft />}
              onClick={() => navigate('/asset-dashboard/list')}
              colorScheme="gray"
              variant="outline"
              size="lg"
            >
              Back to Asset List
            </Button>
          </HStack>
        </VStack>
      </Container>
    </Box>
  );
};

export default AssetDetailPage;


